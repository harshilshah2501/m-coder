"""
Sandbox Executor — M3.2 orchestrator integration.

Provides the bridge between the LoopController and SandboxRunner.
Handles the CONF_APPROVED → CODE_EXECUTION → SANDBOX_RESULT flow.

Architecture principle:
    CONF → authorize
    CODE → execute (sandboxed)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from runtime.sandbox.sandbox_errors import (
    SandboxError,
    SandboxExecutionError,
    SandboxPolicyViolation,
    SandboxTimeout,
)
from runtime.sandbox.sandbox_ledger import SandboxLedgerEmitter, SandboxLedgerEntry
from runtime.sandbox.sandbox_ledger_store import (
    EVENT_BLOCKED,
    EVENT_EXECUTED,
    LedgerStoreError,
    SandboxLedgerStore,
)
from runtime.sandbox.sandbox_driver import LocalProcessSandboxDriver, SandboxDriver
from runtime.sandbox.sandbox_policy import SandboxPolicy
from runtime.sandbox.sandbox_result import GovernedExecutionResult, SandboxResult


@dataclass
class SandboxAction:
    """
    A requested sandbox action from the orchestrator.
    
    Represents a CODE phase action that has been authorized through CONF.
    
    Attributes:
        task_id: Task identifier for ledger linkage (used as request_id when absent).
        command: Command to execute.
        working_dir: Working directory for execution.
        request_id: Optional; defaults to task_id for unified contract.
        plan_hash: Optional plan hash for linkage.
        sandbox_id: Optional sandbox identifier.
        timeout_seconds: Optional timeout override.
        env: Optional environment variables.
        metadata: Optional metadata for audit.
    """

    task_id: str
    command: list[str]
    working_dir: Path | str
    request_id: str = ""
    plan_hash: str = ""
    sandbox_id: str = ""
    timeout_seconds: int | None = None
    env: dict[str, str] | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "command": self.command,
            "working_dir": str(self.working_dir),
            "request_id": self.request_id or self.task_id,
            "plan_hash": self.plan_hash,
            "sandbox_id": self.sandbox_id,
            "timeout_seconds": self.timeout_seconds,
            "env": self.env,
            "metadata": self.metadata,
        }


@dataclass
class SandboxExecutionResult:
    """
    Result from sandbox execution with ledger linkage.
    
    Wraps SandboxResult with orchestrator context.
    Prefer GovernedExecutionResult for unified REFUSED/BLOCKED/EXECUTED contract.
    
    Attributes:
        success: Whether execution succeeded.
        result: The underlying SandboxResult.
        ledger_entry: The emitted ledger entry.
        action: The original action request.
    """

    success: bool
    result: SandboxResult
    ledger_entry: SandboxLedgerEntry
    action: SandboxAction

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "result": self.result.to_dict(),
            "ledger_entry": self.ledger_entry.to_dict(),
            "action": self.action.to_dict(),
        }


def _truncate_summary(text: str, max_len: int = 2000) -> str:
    """Truncate for stdout_summary/stderr_summary."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n...[truncated]"


def _stable_ledger_id(
    prefix: str,
    request_id: str,
    plan_hash: str,
    sandbox_id: str,
    outcome_type: str,
    command_canonical: str,
) -> str:
    """Deterministic ledger row id from structured fields (no id() or process-specific hash)."""
    payload = {
        "request_id": request_id,
        "plan_hash": plan_hash,
        "sandbox_id": sandbox_id,
        "outcome_type": outcome_type,
        "command": command_canonical,
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    h = hashlib.sha256(canonical).hexdigest()[:16]
    return f"{prefix}-{request_id}-{h}"


def _ledger_payload_with_identity(
    base_payload: dict[str, Any],
    action: SandboxAction,
    backend_name: str | None = None,
) -> dict[str, Any]:
    """
    Merge identity from action.metadata into payload for ledger rows.
    When metadata contains canonical_hash, the ledger row MUST include it (M4.1 invariant).
    """
    out = dict(base_payload)
    if not action.metadata:
        if backend_name is not None:
            out["backend"] = backend_name
        return out
    if action.metadata.get("canonical_hash") is not None:
        out["canonical_hash"] = action.metadata["canonical_hash"]
    if action.metadata.get("intent_id") is not None:
        out["intent_id"] = action.metadata["intent_id"]
    if action.metadata.get("request_id") is not None:
        out["request_id"] = action.metadata["request_id"]
    if action.metadata.get("plan_hash") is not None:
        out["plan_hash"] = action.metadata["plan_hash"]
    if backend_name is not None:
        out["backend"] = backend_name
    if action.metadata.get("execution_surface") is not None:
        out["execution_surface"] = action.metadata["execution_surface"]
    return out


class SandboxExecutor:
    """
    Orchestrator integration for sandbox execution.
    
    Returns GovernedExecutionResult for all three outcomes (refused handled by controller):
    BLOCKED = policy disallows; EXECUTED = command ran (success or failure).
    When ledger_store is provided, all outcomes are persisted.
    """

    def __init__(
        self,
        policy: SandboxPolicy | None = None,
        ledger_emitter: SandboxLedgerEmitter | None = None,
        ledger_store: SandboxLedgerStore | None = None,
        execution_callback: Callable[[GovernedExecutionResult], None] | None = None,
        driver: SandboxDriver | None = None,
    ):
        """
        Initialize sandbox executor.

        Args:
            policy: Execution policy. If None, uses default policy.
            ledger_emitter: Ledger emitter for in-memory entries. If None, creates new.
            ledger_store: Optional persistent store; when set, blocked/executed rows are appended.
            execution_callback: Optional callback invoked with GovernedExecutionResult.
            driver: Sandbox execution backend. If None, uses LocalProcessSandboxDriver(policy).
        """
        self.policy = policy or SandboxPolicy()
        self._driver: SandboxDriver = driver if driver is not None else LocalProcessSandboxDriver(policy=self.policy)
        self.ledger_emitter = ledger_emitter or SandboxLedgerEmitter()
        self.ledger_store = ledger_store
        self.execution_callback = execution_callback
        self._execution_history: list[GovernedExecutionResult] = []

    def execute_sandbox_action(
        self,
        action: SandboxAction,
    ) -> GovernedExecutionResult:
        """
        Execute a sandbox action. Returns unified GovernedExecutionResult.
        BLOCKED when policy disallows or when canonical_hash is missing (only
        CanonicalExecutionIntent-derived actions may run). EXECUTED when command runs.
        Persists to ledger_store when provided.
        """
        req_id = action.request_id or action.task_id
        plan_hash = action.plan_hash or ""
        sandbox_id = action.sandbox_id or action.task_id

        # Only CanonicalExecutionIntent-derived actions may run (canonical_hash in metadata)
        if not action.metadata or not action.metadata.get("canonical_hash"):
            blocked_result = GovernedExecutionResult(
                outcome_type="blocked",
                request_id=req_id,
                plan_hash=plan_hash,
                sandbox_id=sandbox_id,
                success=False,
                final_status="blocked",
                blocked_reason="Execution refused: only CanonicalExecutionIntent-derived actions may run; canonical_hash is missing.",
                policy_violation_type="missing_canonical_identity",
                commands_blocked=[],
                ledger_row_id="",
            )
            if self.ledger_store:
                cmd_canonical = " ".join(action.command) if action.command else ""
                lid = _stable_ledger_id("blocked", req_id, plan_hash, sandbox_id, "missing_canonical_hash", cmd_canonical)
                self.ledger_store.append(
                    ledger_row_id=lid,
                    event_type=EVENT_BLOCKED,
                    outcome_type="blocked",
                    request_id=req_id,
                    plan_hash=plan_hash,
                    sandbox_id=sandbox_id,
                    payload=_ledger_payload_with_identity(blocked_result.to_dict(), action),
                )
                blocked_result.ledger_row_id = lid
            self._execution_history.append(blocked_result)
            if self.execution_callback:
                self.execution_callback(blocked_result)
            return blocked_result

        # Run command via driver; policy violation → BLOCKED (command does not run)
        try:
            result = self._driver.run(
                command=action.command,
                working_dir=action.working_dir,
                timeout_seconds=action.timeout_seconds,
                env=action.env,
            )
        except SandboxPolicyViolation as e:
            blocked_result = GovernedExecutionResult(
                outcome_type="blocked",
                request_id=req_id,
                plan_hash=plan_hash,
                sandbox_id=sandbox_id,
                success=False,
                final_status="blocked",
                blocked_reason=e.reason,
                policy_violation_type="command_or_path",
                commands_blocked=[" ".join(e.command)] if e.command else [],
                ledger_row_id="",
            )
            if self.ledger_store:
                cmd_canonical = " ".join(e.command) if e.command else ""
                lid = _stable_ledger_id("blocked", req_id, plan_hash, sandbox_id, "blocked", cmd_canonical)
                self.ledger_store.append(
                    ledger_row_id=lid,
                    event_type=EVENT_BLOCKED,
                    outcome_type="blocked",
                    request_id=req_id,
                    plan_hash=plan_hash,
                    sandbox_id=sandbox_id,
                    payload=_ledger_payload_with_identity(blocked_result.to_dict(), action),
                )
                blocked_result.ledger_row_id = lid
            self._execution_history.append(blocked_result)
            if self.execution_callback:
                self.execution_callback(blocked_result)
            return blocked_result
        except (SandboxTimeout, SandboxExecutionError) as e:
            cmd_str = getattr(e, "command", action.command)
            cmd_display = " ".join(cmd_str) if isinstance(cmd_str, list) else str(cmd_str)
            executed_result = GovernedExecutionResult(
                outcome_type="executed",
                request_id=req_id,
                plan_hash=plan_hash,
                sandbox_id=sandbox_id,
                success=False,
                final_status="executed_failed",
                stderr_summary=_truncate_summary(str(e)),
                commands_executed=[cmd_display],
                ledger_row_id="",
            )
            if self.ledger_store:
                lid = _stable_ledger_id("executed", req_id, plan_hash, sandbox_id, "executed", cmd_display)
                self.ledger_store.append(
                    ledger_row_id=lid,
                    event_type=EVENT_EXECUTED,
                    outcome_type="executed",
                    request_id=req_id,
                    plan_hash=plan_hash,
                    sandbox_id=sandbox_id,
                    payload=_ledger_payload_with_identity(
                        executed_result.to_dict(), action, backend_name=self._driver.driver_name
                    ),
                )
                executed_result.ledger_row_id = lid
            self._execution_history.append(executed_result)
            if self.execution_callback:
                self.execution_callback(executed_result)
            return executed_result

        # Success path: emit in-memory and persist
        ledger_entry = self.ledger_emitter.emit(
            task_id=action.task_id,
            result=result,
            policy_name=self._get_policy_name(),
        )
        executed_result = GovernedExecutionResult(
            outcome_type="executed",
            request_id=req_id,
            plan_hash=plan_hash,
            sandbox_id=sandbox_id,
            success=result.success,
            final_status="executed_ok" if result.success else "executed_failed",
            commands_executed=[" ".join(result.command)] if result.command else [],
            files_written=[],
            artifacts=result.artifacts,
            ledger_row_id=ledger_entry.event_id,
            duration_ms=result.execution_time_ms,
            exit_code=result.exit_code,
            stdout_summary=_truncate_summary(result.stdout),
            stderr_summary=_truncate_summary(result.stderr),
        )
        if self.ledger_store:
            lid = ledger_entry.event_id
            self.ledger_store.append(
                ledger_row_id=lid,
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id=req_id,
                plan_hash=plan_hash,
                sandbox_id=sandbox_id,
                payload=_ledger_payload_with_identity(
                    executed_result.to_dict(), action, backend_name=self._driver.driver_name
                ),
                artifact_manifest_ref="",  # optional: path to manifest
            )
            executed_result.ledger_row_id = lid
        self._execution_history.append(executed_result)
        if self.execution_callback:
            self.execution_callback(executed_result)
        return executed_result

    def validate_action(self, action: SandboxAction) -> tuple[bool, str]:
        """
        Validate an action without executing.
        
        Useful for dry-run validation before CONF approval flow.
        
        Returns:
            Tuple of (is_valid, reason).
        """
        return self._driver.validate_only(action.command, action.working_dir)

    def _get_policy_name(self) -> str:
        """Derive policy name for ledger entries."""
        if self.policy.max_execution_time <= 15:
            return "strict"
        elif self.policy.max_execution_time >= 120:
            return "permissive"
        return "default"

    def get_execution_history(self) -> list[GovernedExecutionResult]:
        """Return history of all governed outcomes (blocked/executed) through this executor."""
        return list(self._execution_history)

    def get_ledger_entries(self) -> list[SandboxLedgerEntry]:
        """Return all ledger entries emitted by this executor."""
        return self.ledger_emitter.get_entries()


def execute_sandbox_action(
    task_id: str,
    command: list[str],
    working_dir: Path | str,
    *,
    policy: SandboxPolicy | None = None,
    ledger_store: SandboxLedgerStore | None = None,
    timeout_seconds: int | None = None,
    env: dict[str, str] | None = None,
) -> GovernedExecutionResult:
    """
    Convenience function for one-shot sandbox execution.
    Returns GovernedExecutionResult (blocked or executed).
    """
    executor = SandboxExecutor(policy=policy, ledger_store=ledger_store)
    action = SandboxAction(
        task_id=task_id,
        command=command,
        working_dir=working_dir,
        request_id=task_id,
        timeout_seconds=timeout_seconds,
        env=env,
    )
    return executor.execute_sandbox_action(action)

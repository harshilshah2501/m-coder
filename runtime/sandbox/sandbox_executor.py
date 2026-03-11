"""
Sandbox Executor — M3.2 orchestrator integration.

Provides the bridge between the LoopController and SandboxRunner.
Handles the CONF_APPROVED → CODE_EXECUTION → SANDBOX_RESULT flow.

Architecture principle:
    CONF → authorize
    CODE → execute (sandboxed)
"""

from __future__ import annotations

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
from runtime.sandbox.sandbox_policy import SandboxPolicy
from runtime.sandbox.sandbox_result import SandboxResult
from runtime.sandbox.sandbox_runner import SandboxRunner


@dataclass
class SandboxAction:
    """
    A requested sandbox action from the orchestrator.
    
    Represents a CODE phase action that has been authorized through CONF.
    
    Attributes:
        task_id: Task identifier for ledger linkage.
        command: Command to execute.
        working_dir: Working directory for execution.
        timeout_seconds: Optional timeout override.
        env: Optional environment variables.
        metadata: Optional metadata for audit.
    """

    task_id: str
    command: list[str]
    working_dir: Path | str
    timeout_seconds: int | None = None
    env: dict[str, str] | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "command": self.command,
            "working_dir": str(self.working_dir),
            "timeout_seconds": self.timeout_seconds,
            "env": self.env,
            "metadata": self.metadata,
        }


@dataclass
class SandboxExecutionResult:
    """
    Result from sandbox execution with ledger linkage.
    
    Wraps SandboxResult with orchestrator context.
    
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


class SandboxExecutor:
    """
    Orchestrator integration for sandbox execution.
    
    Responsibilities:
    - Execute sandbox actions with policy enforcement
    - Emit ledger entries for all executions
    - Provide deterministic execution flow for orchestrator
    - Handle errors with fail-closed semantics
    
    Usage in orchestrator:
        executor = SandboxExecutor()
        result = executor.execute_sandbox_action(action)
    """

    def __init__(
        self,
        policy: SandboxPolicy | None = None,
        ledger_emitter: SandboxLedgerEmitter | None = None,
        execution_callback: Callable[[SandboxExecutionResult], None] | None = None,
    ):
        """
        Initialize sandbox executor.
        
        Args:
            policy: Execution policy. If None, uses default policy.
            ledger_emitter: Ledger emitter. If None, creates new emitter.
            execution_callback: Optional callback invoked after each execution.
        """
        self.policy = policy or SandboxPolicy()
        self.runner = SandboxRunner(policy=self.policy)
        self.ledger_emitter = ledger_emitter or SandboxLedgerEmitter()
        self.execution_callback = execution_callback
        self._execution_history: list[SandboxExecutionResult] = []

    def execute_sandbox_action(
        self,
        action: SandboxAction,
    ) -> SandboxExecutionResult:
        """
        Execute a sandbox action with full orchestrator integration.
        
        This is the main entry point for orchestrator → sandbox flow.
        
        Args:
            action: The sandbox action to execute.
            
        Returns:
            SandboxExecutionResult with execution details and ledger linkage.
            
        Raises:
            SandboxPolicyViolation: If action violates policy.
            SandboxTimeout: If execution times out.
            SandboxExecutionError: If execution fails.
        """
        # Execute command
        result = self.runner.run(
            command=action.command,
            working_dir=action.working_dir,
            timeout_seconds=action.timeout_seconds,
            env=action.env,
        )
        
        # Emit ledger entry
        ledger_entry = self.ledger_emitter.emit(
            task_id=action.task_id,
            result=result,
            policy_name=self._get_policy_name(),
        )
        
        # Build execution result
        execution_result = SandboxExecutionResult(
            success=result.success,
            result=result,
            ledger_entry=ledger_entry,
            action=action,
        )
        
        # Record in history
        self._execution_history.append(execution_result)
        
        # Invoke callback if provided
        if self.execution_callback:
            self.execution_callback(execution_result)
        
        return execution_result

    def validate_action(self, action: SandboxAction) -> tuple[bool, str]:
        """
        Validate an action without executing.
        
        Useful for dry-run validation before CONF approval flow.
        
        Returns:
            Tuple of (is_valid, reason).
        """
        return self.runner.validate_only(action.command, action.working_dir)

    def _get_policy_name(self) -> str:
        """Derive policy name for ledger entries."""
        if self.policy.max_execution_time <= 15:
            return "strict"
        elif self.policy.max_execution_time >= 120:
            return "permissive"
        return "default"

    def get_execution_history(self) -> list[SandboxExecutionResult]:
        """Return history of all executions through this executor."""
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
    timeout_seconds: int | None = None,
    env: dict[str, str] | None = None,
) -> SandboxExecutionResult:
    """
    Convenience function for one-shot sandbox execution.
    
    Creates a temporary executor and action, executes, and returns result.
    
    This is the recommended entry point for simple orchestrator integration:
    
        from runtime.sandbox import execute_sandbox_action
        
        result = execute_sandbox_action(
            task_id="task-123",
            command=["pytest", "tests/"],
            working_dir=Path("/repo"),
        )
    
    Args:
        task_id: Task identifier for ledger linkage.
        command: Command to execute.
        working_dir: Working directory.
        policy: Optional policy override.
        timeout_seconds: Optional timeout override.
        env: Optional environment variables.
        
    Returns:
        SandboxExecutionResult with execution details.
    """
    executor = SandboxExecutor(policy=policy)
    action = SandboxAction(
        task_id=task_id,
        command=command,
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        env=env,
    )
    return executor.execute_sandbox_action(action)

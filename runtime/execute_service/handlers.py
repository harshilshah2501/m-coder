"""
Execute Service Handlers — M3.4 Plugin-Facing Execution Endpoint.

Routes execution requests through the governed runtime path:
  Plugin → /v0/execute → LoopController → Plan-Gate → Sandbox (if allowed)

All execution requests must flow through this endpoint.
No bypass, no local fallback, no silent failure.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from runtime.plangate.plangate_service import PlanGateService
    from runtime.sandbox.sandbox_executor import SandboxAction, SandboxExecutor
    from runtime.sandbox.sandbox_ledger_store import (
        EVENT_PLANGATE_BOUNDED_ALLOW,
        EVENT_PLANGATE_DEFERRED,
        EVENT_PLANGATE_REFUSED,
        EVENT_PLANGATE_SAFE_EXECUTE,
        EVENT_EXECUTED,
        SandboxLedgerStore,
    )
except ImportError:
    PlanGateService = None  # type: ignore[misc, assignment]
    SandboxExecutor = None  # type: ignore[misc, assignment]
    SandboxLedgerStore = None  # type: ignore[misc, assignment]
    SandboxAction = None  # type: ignore[misc, assignment]
    EVENT_PLANGATE_REFUSED = "plangate_refused"
    EVENT_PLANGATE_DEFERRED = "plangate_deferred"
    EVENT_PLANGATE_BOUNDED_ALLOW = "plangate_bounded_allow"
    EVENT_PLANGATE_SAFE_EXECUTE = "plangate_safe_execute"
    EVENT_EXECUTED = "sandbox_executed"


EXECUTE_REQUEST_SCHEMA = "execute_request.v0.1"
EXECUTE_RESPONSE_SCHEMA = "execute_response.v0.1"


def validate_execute_request(data: dict[str, Any]) -> list[str]:
    """Validate ExecuteRequest schema. Returns list of error messages (empty if valid)."""
    errors = []

    schema_version = data.get("schema_version")
    if schema_version and schema_version != EXECUTE_REQUEST_SCHEMA:
        errors.append(f"Expected schema_version {EXECUTE_REQUEST_SCHEMA}, got {schema_version}")

    if not data.get("request_id"):
        errors.append("Missing required field: request_id")

    if not data.get("repo_root"):
        errors.append("Missing required field: repo_root")

    if not data.get("command"):
        errors.append("Missing required field: command")

    return errors


def handle_execute_request(data: dict[str, Any]) -> dict[str, Any]:
    """
    Handle an execution request from the IDE plugin.

    Flow:
    1. Validate request
    2. Build Plan-Gate request
    3. Evaluate with Plan-Gate
    4. If safe_execute: run in sandbox
    5. Return structured response with outcome

    Response outcomes:
    - EXECUTED: Action executed through governed sandbox
    - REFUSED: Plan-Gate refused the action
    - DEFERRED: Action deferred pending approval
    - BOUNDED_ALLOW: Bounded allowance, no sandbox execution (MVP)
    - BLOCKED: Execution blocked by policy
    """
    request_id = data.get("request_id", f"req-{uuid.uuid4()}")
    timestamp_utc = datetime.now(timezone.utc).isoformat()

    repo_root = data.get("repo_root", "")
    revision = data.get("revision", "unknown-revision")
    branch = data.get("branch", "unknown")
    command = data.get("command", "")
    task_id = data.get("task_id")
    plan_hash = data.get("plan_hash", "")
    ide_context = data.get("ide_context", {})
    client_policy = data.get("client_policy", {})

    plan_hash_final = plan_hash or _compute_plan_hash(command, repo_root, revision)

    if PlanGateService is None:
        return _build_response(
            request_id=request_id,
            outcome="REFUSED",
            posture="refuse",
            executed=False,
            reason="Plan-Gate service not available; execution path blocked.",
            ui_title="Execution Refused",
            ui_message="Runtime Plan-Gate is not configured. No execution permitted.",
            ui_severity="error",
            plan_hash=plan_hash_final,
        )

    plan_gate = PlanGateService()

    pg_request = {
        "request_id": request_id,
        "plan_hash": plan_hash_final,
        "command": command,
        "repo_root": repo_root,
        "revision": revision,
        "branch": branch,
        "ide_context": ide_context,
    }

    command_lower = command.lower() if command else ""
    if any(kw in command_lower for kw in ["defer", "approval", "wait"]):
        pg_request["plan_gate_defer"] = True
    if any(kw in command_lower for kw in ["refuse", "deny", "block"]):
        pg_request["plan_gate_refuse"] = True
    if any(kw in command_lower for kw in ["bound", "limit", "restrict"]):
        pg_request["plan_gate_bounded_allow"] = True

    decision = plan_gate.evaluate(pg_request)
    posture = decision.posture
    reason = decision.reason

    if posture == "refuse":
        return _build_response(
            request_id=request_id,
            outcome="REFUSED",
            posture=posture,
            executed=False,
            reason=reason or "Plan-Gate refused this action.",
            ui_title="Execution Refused",
            ui_message=reason or "Runtime governance refused this action.",
            ui_severity="error",
            plan_hash=plan_hash_final,
        )

    if posture == "defer":
        return _build_response(
            request_id=request_id,
            outcome="DEFERRED",
            posture=posture,
            executed=False,
            reason=reason or "Action deferred pending approval.",
            ui_title="Execution Deferred",
            ui_message=reason or "This action requires additional approval. Deferred.",
            ui_severity="warning",
            plan_hash=plan_hash_final,
        )

    if posture == "bounded_allow":
        return _build_response(
            request_id=request_id,
            outcome="BOUNDED_ALLOW",
            posture=posture,
            executed=False,
            reason=reason or "Bounded allowance granted. No sandbox execution in MVP.",
            ui_title="Bounded Allowance",
            ui_message="Runtime granted bounded allowance. No sandbox execution in this MVP path.",
            ui_severity="warning",
            plan_hash=plan_hash_final,
        )

    if SandboxExecutor is None:
        return _build_response(
            request_id=request_id,
            outcome="BLOCKED",
            posture=posture,
            executed=False,
            reason="Sandbox executor not available; execution blocked.",
            ui_title="Execution Blocked",
            ui_message="Sandbox executor is not configured.",
            ui_severity="error",
            plan_hash=plan_hash_final,
        )

    working_dir = Path(repo_root) if repo_root else Path.cwd()
    if not working_dir.exists():
        return _build_response(
            request_id=request_id,
            outcome="BLOCKED",
            posture=posture,
            executed=False,
            reason=f"Working directory does not exist: {working_dir}",
            ui_title="Execution Blocked",
            ui_message=f"Repository root not found: {working_dir}",
            ui_severity="error",
            plan_hash=plan_hash_final,
        )

    cmd_list = _parse_command(command)
    if not cmd_list:
        return _build_response(
            request_id=request_id,
            outcome="BLOCKED",
            posture=posture,
            executed=False,
            reason="Empty or invalid command.",
            ui_title="Execution Blocked",
            ui_message="Command is empty or invalid.",
            ui_severity="error",
            plan_hash=plan_hash_final,
        )

    ledger_store = None
    if SandboxLedgerStore is not None:
        try:
            ledger_store = SandboxLedgerStore()
        except Exception:
            pass

    executor = SandboxExecutor(ledger_store=ledger_store)

    action = SandboxAction(
        task_id=task_id or request_id,
        command=cmd_list,
        working_dir=working_dir,
        timeout_seconds=30,
        env=None,
        metadata={
            "request_id": request_id,
            "plan_hash": plan_hash_final,
            "revision": revision,
            "branch": branch,
        },
    )

    try:
        result = executor.execute_sandbox_action(action)
    except Exception as e:
        return _build_response(
            request_id=request_id,
            outcome="BLOCKED",
            posture=posture,
            executed=False,
            reason=f"Sandbox execution error: {e}",
            ui_title="Execution Blocked",
            ui_message=f"Sandbox error: {e}",
            ui_severity="error",
            plan_hash=plan_hash_final,
        )

    if result.success:
        return _build_response(
            request_id=request_id,
            outcome="EXECUTED",
            posture=posture,
            executed=True,
            reason="Execution completed successfully.",
            ui_title="Execution Complete",
            ui_message="Action executed through governed sandbox.",
            ui_severity="info",
            plan_hash=plan_hash_final,
            ledger_row_id=result.ledger_row_id,
            exit_code=result.exit_code,
            stdout_summary=result.stdout_summary,
            stderr_summary=result.stderr_summary,
        )
    else:
        return _build_response(
            request_id=request_id,
            outcome="BLOCKED",
            posture=posture,
            executed=False,
            reason=result.blocked_reason or "Execution blocked by sandbox policy.",
            ui_title="Execution Blocked",
            ui_message=result.blocked_reason or "Sandbox policy blocked this execution.",
            ui_severity="error",
            plan_hash=plan_hash_final,
            ledger_row_id=result.ledger_row_id,
        )


def _build_response(
    request_id: str,
    outcome: str,
    posture: str,
    executed: bool,
    reason: str,
    ui_title: str,
    ui_message: str,
    ui_severity: str,
    plan_hash: str,
    ledger_row_id: str | None = None,
    exit_code: int | None = None,
    stdout_summary: str | None = None,
    stderr_summary: str | None = None,
) -> dict[str, Any]:
    """Build a standardized ExecuteResponse."""
    response = {
        "schema_version": EXECUTE_RESPONSE_SCHEMA,
        "request_id": request_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "outcome": outcome,
        "posture": posture,
        "executed": executed,
        "reason": reason,
        "plan_hash": plan_hash,
        "ui": {
            "title": ui_title,
            "message": ui_message,
            "severity": ui_severity,
        },
    }

    if ledger_row_id:
        response["ledger_row_id"] = ledger_row_id

    if exit_code is not None:
        response["exit_code"] = exit_code

    if stdout_summary:
        response["stdout_summary"] = stdout_summary

    if stderr_summary:
        response["stderr_summary"] = stderr_summary

    return response


def _compute_plan_hash(command: str, repo_root: str, revision: str) -> str:
    """Compute a deterministic plan hash from request parameters."""
    data = json.dumps({
        "command": command,
        "repo_root": repo_root,
        "revision": revision,
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(data.encode()).hexdigest()


def _parse_command(command: str) -> list[str]:
    """Parse command string into a list suitable for subprocess."""
    if not command or not command.strip():
        return []
    parts = command.strip().split()
    return parts

"""Stage 3 tool executor."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.sandbox.sandbox_executor import SandboxAction, SandboxExecutor
from runtime.state.validators import validate_tool_execution_request, validate_tool_execution_result


class ToolExecutor:
    """Executes tool requests via sandbox and returns ToolExecutionResult.v1."""

    def __init__(self, sandbox_executor: SandboxExecutor) -> None:
        self._sandbox = sandbox_executor

    def execute(self, request: dict[str, Any], *, request_id: str, working_dir: str) -> dict[str, Any]:
        validate_tool_execution_request(request)
        tool_name = request["tool_name"]
        args = request["args"]
        read_only = request["constraints"]["read_only"]
        timeout_ms = request["constraints"]["timeout_ms"]

        command = self._to_command(tool_name, args)
        canonical_hash = self._canonical_execution_hash(
            tool_name=tool_name,
            args=args,
            working_dir=working_dir,
            constraints=request["constraints"],
        )
        action = SandboxAction(
            task_id=request_id,
            request_id=request_id,
            command=command,
            working_dir=Path(working_dir),
            timeout_seconds=max(1, int(timeout_ms / 1000)),
            metadata={
                "canonical_hash": canonical_hash,
                "intent_id": f"{request_id}:{tool_name}",
                "execution_surface": "stage3_loop",
                "read_only": read_only,
            },
        )
        outcome = self._sandbox.execute_sandbox_action(action)
        result = self._normalize(outcome)
        validate_tool_execution_result(result)
        return result

    @staticmethod
    def _to_command(tool_name: str, args: dict[str, Any]) -> list[str]:
        # Deterministic command encoding: tool name + sorted key/value pairs.
        command = [tool_name]
        for key in sorted(args.keys()):
            value = args[key]
            command.append(f"--{key}")
            command.append(str(value))
        return command

    @staticmethod
    def _normalize(outcome: Any) -> dict[str, Any]:
        status = "failed_terminal"
        error_class = "tool_internal_error"
        summary = ""
        data: dict[str, Any] = {}
        artifacts: list[dict[str, str]] = []

        if outcome.outcome_type == "blocked":
            status = "denied"
            error_class = "policy_denied"
            summary = outcome.blocked_reason or "denied"
        elif outcome.outcome_type == "executed":
            final_status = getattr(outcome, "final_status", "")
            if final_status == "executed_ok":
                status = "success"
                error_class = "none"
                summary = "executed_ok"
            elif final_status == "executed_partial":
                status = "partial"
                error_class = "none"
                summary = "executed_partial"
            elif final_status == "executed_partial_insufficient":
                status = "partial"
                error_class = "none"
                summary = "executed_partial_insufficient"
                data["evidence_inadequate"] = True
            elif final_status == "executed_failed_timeout":
                status = "timeout"
                error_class = "timeout"
                summary = "executed_failed_timeout"
            elif final_status == "executed_failed_retryable":
                status = "failed_retryable"
                error_class = "runtime_error"
                summary = "executed_failed_retryable"
            elif final_status == "executed_failed_terminal":
                status = "failed_terminal"
                error_class = "tool_internal_error"
                summary = "executed_failed_terminal"
            elif final_status == "executed_failed":
                # Narrow fallback for legacy/unspecified failure subclass.
                stderr = (getattr(outcome, "stderr_summary", "") or "").lower()
                if "timeout" in stderr:
                    status = "timeout"
                    error_class = "timeout"
                elif "terminal" in stderr or "fatal" in stderr:
                    status = "failed_terminal"
                    error_class = "tool_internal_error"
                else:
                    status = "failed_retryable"
                    error_class = "runtime_error"
                summary = final_status
            else:
                status = "failed_terminal"
                error_class = "tool_internal_error"
                summary = final_status or "executed_unknown"
        else:
            status = "failed_terminal"
            error_class = "tool_internal_error"
            summary = "unknown_outcome_type"

        if getattr(outcome, "ledger_row_id", ""):
            artifacts.append(
                {
                    "artifact_ref": f"tool_result:{outcome.ledger_row_id}",
                    "kind": "report",
                    "uri": outcome.ledger_row_id,
                }
            )
        data["final_status"] = getattr(outcome, "final_status", "")
        data["commands_executed"] = getattr(outcome, "commands_executed", [])
        data["commands_blocked"] = getattr(outcome, "commands_blocked", [])

        return {
            "schema_version": "tool_execution_result.v1",
            "status": status,
            "output_schema_version": "tool_output.v1",
            "output": {
                "summary": summary,
                "data": data,
            },
            "artifacts": artifacts,
            "error_class": error_class,
        }

    @staticmethod
    def _canonical_execution_hash(
        *,
        tool_name: str,
        args: dict[str, Any],
        working_dir: str,
        constraints: dict[str, Any],
    ) -> str:
        payload = {
            "tool_name": tool_name,
            "args": {k: args[k] for k in sorted(args)},
            "working_dir": str(Path(working_dir)),
            "constraints": {
                "timeout_ms": constraints.get("timeout_ms"),
                "sandbox_required": constraints.get("sandbox_required"),
                "read_only": constraints.get("read_only"),
            },
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        return f"tool_exec:{digest}"

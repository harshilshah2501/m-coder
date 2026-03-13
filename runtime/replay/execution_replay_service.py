"""
Execution Replay Service — M4.1 Slice-4.

Reconstructs execution intent from the ledger using canonical_hash and optionally
re-executes through the sandbox. Does not modify existing runtime flows.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from runtime.sandbox.sandbox_ledger_store import EVENT_EXECUTED

if TYPE_CHECKING:
    from runtime.sandbox.sandbox_executor import SandboxExecutor
    from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore


def _command_from_payload(payload: dict[str, Any]) -> list[str]:
    """Derive command list from payload (command or commands_executed)."""
    cmd = payload.get("command")
    if cmd is not None:
        return list(cmd) if isinstance(cmd, (list, tuple)) else [str(cmd)]
    executed = payload.get("commands_executed") or []
    if not executed:
        return []
    first = executed[0] if executed else ""
    if isinstance(first, list):
        return list(first)
    return first.split() if isinstance(first, str) else [str(first)]


class ExecutionReplayService:
    """
    Replay execution from ledger by canonical_hash.
    Uses ledger_store for lookup and sandbox_executor for re-execution (policy still applies).
    """

    def __init__(
        self,
        ledger_store: SandboxLedgerStore,
        sandbox_executor: SandboxExecutor,
    ) -> None:
        self.ledger_store = ledger_store
        self.sandbox_executor = sandbox_executor

    def reconstruct_intent(self, canonical_hash: str) -> dict[str, Any]:
        """
        Reconstruct execution intent from the ledger.
        Finds the sandbox_executed row for the given canonical_hash and extracts
        command, working_dir, request_id, plan_hash, canonical_hash, intent_id.

        Raises:
            ValueError: If canonical_hash has no rows or no sandbox_executed row.
        """
        if not canonical_hash:
            raise ValueError("canonical_hash does not exist or is empty")
        rows = self.ledger_store.get_by_canonical_hash(canonical_hash)
        if not rows:
            raise ValueError(f"canonical_hash does not exist: {canonical_hash!r}")
        executed_row = None
        for r in reversed(rows):
            if r.event_type == EVENT_EXECUTED:
                executed_row = r
                break
        if executed_row is None:
            raise ValueError(f"canonical_hash has no sandbox_executed row: {canonical_hash!r}")
        payload = executed_row.payload
        command = _command_from_payload(payload)
        working_dir = payload.get("working_dir") or ""
        request_id = payload.get("request_id") or executed_row.request_id or ""
        plan_hash = payload.get("plan_hash") or executed_row.plan_hash or ""
        intent_canonical_hash = payload.get("canonical_hash") or canonical_hash
        intent_id = payload.get("intent_id") or ""
        return {
            "command": command,
            "working_dir": working_dir,
            "request_id": request_id,
            "plan_hash": plan_hash,
            "canonical_hash": intent_canonical_hash,
            "intent_id": intent_id,
        }

    def replay_execution(self, canonical_hash: str):  # -> GovernedExecutionResult
        """
        Reconstruct intent from ledger and re-execute via sandbox.
        Replay still obeys sandbox policy. Returns result from sandbox_executor.
        """
        intent = self.reconstruct_intent(canonical_hash)
        request_id = intent["request_id"] or f"replay-{canonical_hash[:12]}"
        task_id = request_id
        from runtime.sandbox.sandbox_executor import SandboxAction

        action = SandboxAction(
            task_id=task_id,
            command=intent["command"],
            working_dir=Path(intent["working_dir"]) if intent["working_dir"] else Path.cwd(),
            request_id=request_id,
            plan_hash=intent["plan_hash"],
            metadata={
                "canonical_hash": intent["canonical_hash"],
                "intent_id": intent["intent_id"],
                "request_id": intent["request_id"],
                "plan_hash": intent["plan_hash"],
                "execution_surface": "replay",
            },
        )
        return self.sandbox_executor.execute_sandbox_action(action)
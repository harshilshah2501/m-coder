"""
Sandbox Ledger Integration — M3.2 ledger emission for sandbox execution.

Emits ledger records for every sandbox execution.
Append-only semantics. Deterministic field values.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from runtime.sandbox.sandbox_result import SandboxResult


@dataclass
class SandboxLedgerEntry:
    """
    Ledger entry for sandbox execution.
    
    Captures execution metadata for audit without including large stdout/stderr.
    
    Fields:
        event_id: Unique event identifier (deterministic hash).
        timestamp_utc: ISO-8601 timestamp.
        task_id: Task identifier from orchestrator.
        command: The executed command.
        exit_code: Process exit code.
        execution_time_ms: Wall-clock execution time in milliseconds.
        success: Whether command succeeded (exit_code == 0).
        artifact_count: Number of artifacts generated.
        working_dir: Working directory used.
        truncated: Whether output was truncated.
        policy_name: Name/identifier of policy used (if any).
    """

    event_id: str
    timestamp_utc: str
    task_id: str
    command: list[str]
    exit_code: int
    execution_time_ms: int
    success: bool
    artifact_count: int = 0
    working_dir: str = ""
    truncated: bool = False
    policy_name: str = "default"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation for ledger storage."""
        return {
            "schema_version": "sandbox_execution.v0.1",
            "event": {
                "event_id": self.event_id,
                "event_type": "sandbox_execution",
                "timestamp_utc": self.timestamp_utc,
                "task_id": self.task_id,
            },
            "execution": {
                "command": self.command,
                "exit_code": self.exit_code,
                "execution_time_ms": self.execution_time_ms,
                "success": self.success,
                "artifact_count": self.artifact_count,
                "working_dir": self.working_dir,
                "truncated": self.truncated,
            },
            "policy": {
                "policy_name": self.policy_name,
            },
        }


def _canonical_json(obj: Any) -> bytes:
    """Stable JSON: sorted keys, UTF-8."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _derive_event_id(task_id: str, command: list[str], timestamp: str) -> str:
    """Deterministic event ID from execution parameters."""
    content = _canonical_json({
        "task_id": task_id,
        "command": command,
        "timestamp": timestamp,
    })
    return f"sbx-{hashlib.sha256(content).hexdigest()[:32]}"


class SandboxLedgerEmitter:
    """
    Emits ledger entries for sandbox executions.
    
    Produces deterministic entries for audit and replay.
    """

    def __init__(self, fixed_time: str | None = None):
        """
        Initialize emitter.
        
        Args:
            fixed_time: Optional fixed timestamp for deterministic testing.
        """
        self.fixed_time = fixed_time
        self._entries: list[SandboxLedgerEntry] = []

    def emit(
        self,
        task_id: str,
        result: SandboxResult,
        *,
        policy_name: str = "default",
    ) -> SandboxLedgerEntry:
        """
        Emit a ledger entry for sandbox execution.
        
        Args:
            task_id: Task identifier from orchestrator.
            result: The sandbox execution result.
            policy_name: Name of the policy used.
            
        Returns:
            SandboxLedgerEntry with all fields populated.
        """
        timestamp = self.fixed_time or datetime.now(timezone.utc).isoformat()
        
        event_id = _derive_event_id(task_id, result.command, timestamp)
        
        entry = SandboxLedgerEntry(
            event_id=event_id,
            timestamp_utc=timestamp,
            task_id=task_id,
            command=result.command,
            exit_code=result.exit_code,
            execution_time_ms=result.execution_time_ms,
            success=result.success,
            artifact_count=len(result.artifacts),
            working_dir=result.working_dir,
            truncated=result.truncated,
            policy_name=policy_name,
        )
        
        self._entries.append(entry)
        return entry

    def get_entries(self) -> list[SandboxLedgerEntry]:
        """Return all emitted entries."""
        return list(self._entries)

    def get_entries_for_task(self, task_id: str) -> list[SandboxLedgerEntry]:
        """Return entries for a specific task."""
        return [e for e in self._entries if e.task_id == task_id]

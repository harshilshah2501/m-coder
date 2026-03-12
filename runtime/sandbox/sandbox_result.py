"""
Sandbox Result — M3.2 execution result contract.

Captures all outputs from sandbox execution for audit and ledger emission.
Deterministic, structured, and serializable.

Unified contract: GovernedExecutionResult represents all three canonical outcomes
(REFUSED, BLOCKED, EXECUTED) in one stable schema for runtime/plugin/demo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# Canonical outcome types for governed runtime (M3.2).
OutcomeType = Literal["refused", "blocked", "executed"]


@dataclass
class SandboxResult:
    """
    Result of a sandboxed command execution.
    
    All fields are captured for deterministic audit and ledger emission.
    
    Attributes:
        success: True if command exited with code 0.
        exit_code: Process exit code.
        stdout: Captured standard output (may be truncated).
        stderr: Captured standard error (may be truncated).
        execution_time_ms: Wall-clock execution time in milliseconds.
        artifacts: List of artifact paths generated during execution.
        command: The executed command (for audit linkage).
        working_dir: Working directory used for execution.
        truncated: True if stdout/stderr were truncated due to size limits.
    """

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: int
    artifacts: list[str] = field(default_factory=list)
    command: list[str] = field(default_factory=list)
    working_dir: str = ""
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation for serialization."""
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_time_ms": self.execution_time_ms,
            "artifacts": self.artifacts,
            "command": self.command,
            "working_dir": self.working_dir,
            "truncated": self.truncated,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SandboxResult:
        """Reconstruct from dictionary representation."""
        return cls(
            success=d["success"],
            exit_code=d["exit_code"],
            stdout=d["stdout"],
            stderr=d["stderr"],
            execution_time_ms=d["execution_time_ms"],
            artifacts=d.get("artifacts", []),
            command=d.get("command", []),
            working_dir=d.get("working_dir", ""),
            truncated=d.get("truncated", False),
        )

    def to_ledger_entry(self) -> dict[str, Any]:
        """
        Convert to ledger-compatible entry.
        
        Returns a dict suitable for inclusion in ledger_row.v0.1 records.
        Excludes potentially large stdout/stderr for ledger compactness.
        """
        return {
            "event": "sandbox_execution",
            "command": self.command,
            "exit_code": self.exit_code,
            "execution_time_ms": self.execution_time_ms,
            "success": self.success,
            "artifact_count": len(self.artifacts),
            "truncated": self.truncated,
        }


@dataclass
class GovernedExecutionResult:
    """
    Unified runtime result contract for all three canonical outcomes:
    REFUSED (governance/runtime denies before sandbox),
    BLOCKED (policy disallows at sandbox),
    EXECUTED (command runs in sandbox).

    One contract for persistence, replay, and plugin UX.
    Deterministic field presence; optional fields use empty string/list as needed.
    """

    outcome_type: OutcomeType
    request_id: str
    plan_hash: str
    sandbox_id: str  # empty for refusal when sandbox never starts
    success: bool
    final_status: str  # e.g. refused, blocked, executed_ok, executed_failed
    refusal_reason: str = ""
    blocked_reason: str = ""
    policy_violation_type: str = ""
    commands_executed: list[str] = field(default_factory=list)
    commands_blocked: list[str] = field(default_factory=list)
    files_written: list[str] = field(default_factory=list)
    files_blocked: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    ledger_row_id: str = ""
    duration_ms: int = 0
    exit_code: int = -1
    stdout_summary: str = ""
    stderr_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Deterministic dict for persistence and replay (stable key order)."""
        return {
            "outcome_type": self.outcome_type,
            "request_id": self.request_id,
            "plan_hash": self.plan_hash,
            "sandbox_id": self.sandbox_id,
            "success": self.success,
            "final_status": self.final_status,
            "refusal_reason": self.refusal_reason,
            "blocked_reason": self.blocked_reason,
            "policy_violation_type": self.policy_violation_type,
            "commands_executed": list(self.commands_executed),
            "commands_blocked": list(self.commands_blocked),
            "files_written": list(self.files_written),
            "files_blocked": list(self.files_blocked),
            "artifacts": list(self.artifacts),
            "ledger_row_id": self.ledger_row_id,
            "duration_ms": self.duration_ms,
            "exit_code": self.exit_code,
            "stdout_summary": self.stdout_summary,
            "stderr_summary": self.stderr_summary,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GovernedExecutionResult:
        """Reconstruct from dict."""
        return cls(
            outcome_type=d["outcome_type"],
            request_id=d["request_id"],
            plan_hash=d.get("plan_hash", ""),
            sandbox_id=d.get("sandbox_id", ""),
            success=d.get("success", False),
            final_status=d.get("final_status", ""),
            refusal_reason=d.get("refusal_reason", ""),
            blocked_reason=d.get("blocked_reason", ""),
            policy_violation_type=d.get("policy_violation_type", ""),
            commands_executed=list(d.get("commands_executed", [])),
            commands_blocked=list(d.get("commands_blocked", [])),
            files_written=list(d.get("files_written", [])),
            files_blocked=list(d.get("files_blocked", [])),
            artifacts=list(d.get("artifacts", [])),
            ledger_row_id=d.get("ledger_row_id", ""),
            duration_ms=int(d.get("duration_ms", 0)),
            exit_code=int(d.get("exit_code", -1)),
            stdout_summary=d.get("stdout_summary", ""),
            stderr_summary=d.get("stderr_summary", ""),
        )

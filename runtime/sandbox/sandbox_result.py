"""
Sandbox Result — M3.2 execution result contract.

Captures all outputs from sandbox execution for audit and ledger emission.
Deterministic, structured, and serializable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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

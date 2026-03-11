"""
Sandbox Errors — M3.2 exception hierarchy.

Defines fail-closed error semantics for sandbox execution.
All errors must be explicit and auditable.
"""

from __future__ import annotations


class SandboxError(Exception):
    """Base exception for all sandbox errors."""

    pass


class SandboxPolicyViolation(SandboxError):
    """
    Raised when a command violates sandbox policy.
    
    This is a fail-closed error: execution is blocked before subprocess starts.
    
    Attributes:
        command: The command that violated policy.
        reason: Human-readable explanation of the violation.
    """

    def __init__(self, command: list[str], reason: str):
        self.command = command
        self.reason = reason
        super().__init__(f"Policy violation for command {command!r}: {reason}")


class SandboxTimeout(SandboxError):
    """
    Raised when command execution exceeds the allowed time limit.
    
    Attributes:
        command: The command that timed out.
        timeout_seconds: The timeout limit that was exceeded.
    """

    def __init__(self, command: list[str], timeout_seconds: int):
        self.command = command
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Command {command!r} exceeded timeout of {timeout_seconds}s"
        )


class SandboxExecutionError(SandboxError):
    """
    Raised when command execution fails unexpectedly.
    
    This covers subprocess launch failures, permission errors, and other
    runtime errors that prevent normal execution completion.
    
    Attributes:
        command: The command that failed.
        reason: Human-readable explanation of the failure.
        original_error: The original exception, if any.
    """

    def __init__(
        self,
        command: list[str],
        reason: str,
        original_error: Exception | None = None,
    ):
        self.command = command
        self.reason = reason
        self.original_error = original_error
        super().__init__(f"Execution error for command {command!r}: {reason}")

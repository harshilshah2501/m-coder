"""
Execution Sandbox — M3.2 CODE phase implementation.

Provides isolated, controlled execution environment for runtime actions.
Execution must never happen outside the sandbox.

Architecture principle:
    DES → propose
    CONF → authorize
    CODE → execute (sandboxed)
"""

from runtime.sandbox.sandbox_errors import (
    SandboxError,
    SandboxExecutionError,
    SandboxPolicyViolation,
    SandboxTimeout,
)
from runtime.sandbox.sandbox_executor import (
    SandboxAction,
    SandboxExecutionResult,
    SandboxExecutor,
    execute_sandbox_action,
)
from runtime.sandbox.sandbox_ledger import (
    SandboxLedgerEmitter,
    SandboxLedgerEntry,
)
from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore
from runtime.sandbox.sandbox_policy import SandboxPolicy
from runtime.sandbox.sandbox_result import GovernedExecutionResult, SandboxResult
from runtime.sandbox.sandbox_runner import SandboxRunner

__all__ = [
    "GovernedExecutionResult",
    "SandboxAction",
    "SandboxError",
    "SandboxExecutionError",
    "SandboxExecutionResult",
    "SandboxExecutor",
    "SandboxLedgerEmitter",
    "SandboxLedgerEntry",
    "SandboxLedgerStore",
    "SandboxPolicy",
    "SandboxPolicyViolation",
    "SandboxResult",
    "SandboxRunner",
    "SandboxTimeout",
    "execute_sandbox_action",
]

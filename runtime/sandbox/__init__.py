"""
Execution Sandbox — M3.2 CODE phase implementation.

Provides isolated, controlled execution environment for runtime actions.
Execution must never happen outside the sandbox.

Architecture principle:
    DES → propose
    CONF → authorize
    CODE → execute (sandboxed)
"""

from runtime.sandbox.container_sandbox_driver import ContainerSandboxDriver, DEFAULT_IMAGE
from runtime.sandbox.sandbox_driver import BaseSandboxDriver, LocalProcessSandboxDriver, SandboxDriver
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


def create_sandbox_driver(
    kind: str = "local_process",
    *,
    policy: SandboxPolicy | None = None,
    image: str | None = None,
    runtime: str | None = None,
) -> SandboxDriver:
    """
    Create a sandbox driver by name for configuration/selection.

    Args:
        kind: "local_process" (default) or "container".
        policy: Optional policy; used by both drivers for validation.
        image: Container image (container driver only); default python:3.12-slim.
        runtime: Container runtime binary override (container driver only).

    Returns:
        SandboxDriver instance. Use with SandboxExecutor(driver=...).
    """
    if kind == "container":
        return ContainerSandboxDriver(
            image=image or DEFAULT_IMAGE,
            runtime=runtime,
            policy=policy,
        )
    return LocalProcessSandboxDriver(policy=policy)


__all__ = [
    "BaseSandboxDriver",
    "ContainerSandboxDriver",
    "GovernedExecutionResult",
    "LocalProcessSandboxDriver",
    "SandboxDriver",
    "create_sandbox_driver",
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

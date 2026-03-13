"""
Sandbox Driver Abstraction — M3.10 pluggable execution backend.

Defines the driver interface beneath governed execution. The runtime (SandboxExecutor)
owns authority, boundary enforcement, Plan-Gate decisions, and ledger linkage.
Drivers only perform the actual run/validate; they do not own governance logic.

A future container runtime (M3.11) can plug in by implementing SandboxDriver.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

from runtime.sandbox.sandbox_result import SandboxResult


class SandboxDriver(Protocol):
    """
    Protocol for pluggable sandbox execution backends.

    Implementations run commands in their environment (e.g. local process, container).
    They may raise SandboxPolicyViolation, SandboxTimeout, SandboxExecutionError.
    Governance (BLOCKED/EXECUTED outcome, ledger) remains in SandboxExecutor.

    Set driver_name (e.g. 'local_process', 'container') for observability so logs
    can show sandbox_driver=... for operational debugging.
    """

    driver_name: str

    def run(
        self,
        command: list[str],
        working_dir: Path | str,
        *,
        timeout_seconds: int | None = None,
        env: dict[str, str] | None = None,
        capture_artifacts: bool = True,
    ) -> SandboxResult:
        """
        Execute a command in the sandbox.

        Args:
            command: Command to execute (list of arguments).
            working_dir: Working directory for execution.
            timeout_seconds: Execution timeout (optional).
            env: Environment variables (optional; may be filtered by driver).
            capture_artifacts: If True, scan for new files after execution.

        Returns:
            SandboxResult with execution details.

        Raises:
            SandboxPolicyViolation: If command violates policy (before run).
            SandboxTimeout: If execution exceeds timeout.
            SandboxExecutionError: If execution fails unexpectedly.
        """
        ...

    def validate_only(self, command: list[str], working_dir: Path | str) -> tuple[bool, str]:
        """
        Validate command and working directory without executing.

        Returns:
            Tuple of (is_valid, reason). If is_valid is False, reason explains why.
        """
        ...


class BaseSandboxDriver(ABC):
    """
    Abstract base class for sandbox drivers.

    Use this when you want shared helpers (e.g. logging, telemetry) later.
    Subclasses must set driver_name for observability (e.g. logs show
    sandbox_driver=local_process, sandbox_driver=container).
    """

    driver_name: str = ""

    @abstractmethod
    def run(
        self,
        command: list[str],
        working_dir: Path | str,
        *,
        timeout_seconds: int | None = None,
        env: dict[str, str] | None = None,
        capture_artifacts: bool = True,
    ) -> SandboxResult:
        """Execute a command in the sandbox. See SandboxDriver protocol."""
        ...

    @abstractmethod
    def validate_only(self, command: list[str], working_dir: Path | str) -> tuple[bool, str]:
        """Validate without executing. See SandboxDriver protocol."""
        ...


class LocalProcessSandboxDriver(BaseSandboxDriver):
    """
    Driver that runs commands as local subprocesses via SandboxRunner.

    Preserves current process-based execution semantics. Policy is applied
    at the runner boundary; outcome interpretation and ledger stay in executor.
    """

    driver_name = "local_process"

    def __init__(self, runner: "SandboxRunner | None" = None, policy: "SandboxPolicy | None" = None):
        """
        Initialize the local process driver.

        Args:
            runner: SandboxRunner to use. If None, one is created with the given policy.
            policy: Used only when runner is None to construct SandboxRunner.
        """
        from runtime.sandbox.sandbox_policy import SandboxPolicy
        from runtime.sandbox.sandbox_runner import SandboxRunner

        self._policy = policy or SandboxPolicy()
        self._runner = runner or SandboxRunner(policy=self._policy)

    def run(
        self,
        command: list[str],
        working_dir: Path | str,
        *,
        timeout_seconds: int | None = None,
        env: dict[str, str] | None = None,
        capture_artifacts: bool = True,
    ) -> SandboxResult:
        """Execute command via SandboxRunner."""
        return self._runner.run(
            command=command,
            working_dir=working_dir,
            timeout_seconds=timeout_seconds,
            env=env,
            capture_artifacts=capture_artifacts,
        )

    def validate_only(self, command: list[str], working_dir: Path | str) -> tuple[bool, str]:
        """Validate via SandboxRunner."""
        return self._runner.validate_only(command, working_dir)


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.sandbox.sandbox_policy import SandboxPolicy
    from runtime.sandbox.sandbox_runner import SandboxRunner

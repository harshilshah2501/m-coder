"""
Container Sandbox Driver — M3.11 container-backed execution backend.

Runs commands inside a container for stronger isolation. Uses the M3.10 driver
abstraction; governance and ledger stay in SandboxExecutor.

Isolation: workspace mounted read-write into container; command executed via
exec form (no shell); timeout enforced; container removed after run.
Fail-closed when runtime is unavailable or execution fails.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from runtime.sandbox.sandbox_driver import BaseSandboxDriver
from runtime.sandbox.sandbox_errors import (
    SandboxExecutionError,
    SandboxPolicyViolation,
    SandboxTimeout,
)
from runtime.sandbox.sandbox_policy import SandboxPolicy
from runtime.sandbox.sandbox_result import SandboxResult

# Container workspace path inside the container (mount host working_dir here).
CONTAINER_WORKSPACE = "/workspace"

# Default image for execution (slim, common tools available).
DEFAULT_IMAGE = "python:3.12-slim"


def _find_container_runtime() -> tuple[str | None, str]:
    """
    Return (runtime_binary, error_message). Prefer podman then docker.
    If neither is available, return (None, reason) for fail-closed behavior.
    """
    for name in ("podman", "docker"):
        path = shutil.which(name)
        if path:
            return path, ""
    return None, "No container runtime found (podman or docker required)"


def _check_runtime_available() -> tuple[bool, str]:
    """Return (available, reason). Used for validate_only and pre-run check."""
    runtime, err = _find_container_runtime()
    if runtime is None:
        return False, err
    try:
        subprocess.run(
            [runtime, "info"],
            capture_output=True,
            timeout=5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, f"Container runtime {runtime} did not respond in time"
    except OSError as e:
        return False, f"Container runtime failed: {e}"
    return True, ""


class ContainerSandboxDriver(BaseSandboxDriver):
    """
    Driver that runs commands inside a container.

    - Mounts working_dir as CONTAINER_WORKSPACE; runs command there.
    - No shell; exec form; timeout enforced; --rm.
    - Fail-closed if runtime is missing or run fails.
    - Policy validation (command allowlist, working_dir) applied before execution.
    """

    driver_name = "container"

    def __init__(
        self,
        image: str = DEFAULT_IMAGE,
        runtime: str | None = None,
        policy: SandboxPolicy | None = None,
        workspace_mount: str = CONTAINER_WORKSPACE,
    ):
        """
        Args:
            image: Container image to run (e.g. python:3.12-slim).
            runtime: Override container runtime binary (podman/docker). If None, auto-detect.
            policy: Execution policy for command/working_dir validation. If None, uses default.
            workspace_mount: Path inside container for mounted working_dir (default /workspace).
        """
        self._image = image
        self._runtime_override = runtime
        self._policy = policy or SandboxPolicy()
        self._workspace_mount = workspace_mount

    def _get_runtime(self) -> str:
        """Resolve runtime binary. Raises SandboxExecutionError if unavailable (fail-closed)."""
        if self._runtime_override:
            if not shutil.which(self._runtime_override):
                raise SandboxExecutionError(
                    [],
                    f"Configured container runtime not found: {self._runtime_override}",
                )
            return self._runtime_override
        path, err = _find_container_runtime()
        if path is None:
            raise SandboxExecutionError([], err)
        return path

    def validate_only(self, command: list[str], working_dir: Path | str) -> tuple[bool, str]:
        """
        Preflight: runtime available, working_dir exists, command allowed by policy.
        Does not pull image or run container.
        """
        working_dir = Path(working_dir)
        ok, reason = _check_runtime_available()
        if not ok:
            return False, reason
        is_valid, reason = self._policy.validate_command(command)
        if not is_valid:
            return False, reason
        is_valid, reason = self._policy.validate_working_dir(working_dir)
        if not is_valid:
            return False, reason
        if not working_dir.exists():
            return False, f"Working directory does not exist: {working_dir}"
        return True, ""

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
        Run command inside a container. Mounts working_dir at workspace_mount.
        Raises SandboxPolicyViolation / SandboxTimeout / SandboxExecutionError on failure (fail-closed).
        """
        working_dir = Path(working_dir).resolve()
        # Policy validation (same semantics as local driver → BLOCKED when invalid)
        is_valid, reason = self._policy.validate_command(command)
        if not is_valid:
            raise SandboxPolicyViolation(command, reason)
        is_valid, reason = self._policy.validate_working_dir(working_dir)
        if not is_valid:
            raise SandboxPolicyViolation(command, reason)
        if not working_dir.exists():
            raise SandboxExecutionError(
                command,
                f"Working directory does not exist: {working_dir}",
            )
        runtime_bin = self._get_runtime()
        effective_timeout = timeout_seconds or self._policy.max_execution_time
        # Build: runtime run --rm -v host_dir:workspace_mount -w workspace_mount image cmd...
        run_cmd = [
            runtime_bin,
            "run",
            "--rm",
            "-v", f"{working_dir}:{self._workspace_mount}",
            "-w", self._workspace_mount,
        ]
        for key, value in (env or {}).items():
            run_cmd += ["-e", f"{key}={value}"]
        run_cmd.append(self._image)
        run_cmd.extend(command)
        start = time.monotonic()
        try:
            result = subprocess.run(
                run_cmd,
                capture_output=True,
                timeout=effective_timeout,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            raise SandboxTimeout(command, effective_timeout)
        except OSError as e:
            raise SandboxExecutionError(
                command,
                f"Container run failed: {e}",
                original_error=e,
            ) from e
        except Exception as e:
            raise SandboxExecutionError(
                command,
                f"Unexpected error running container: {e}",
                original_error=e,
            ) from e
        elapsed_ms = int((time.monotonic() - start) * 1000)
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")
        max_out = self._policy.max_output_bytes // 2
        truncated = False
        if len(stdout) > max_out:
            stdout = stdout[:max_out] + "\n...[truncated]"
            truncated = True
        if len(stderr) > max_out:
            stderr = stderr[:max_out] + "\n...[truncated]"
            truncated = True
        artifacts: list[str] = []
        if capture_artifacts:
            try:
                for root, _, files in os.walk(working_dir):
                    depth = len(Path(root).relative_to(working_dir).parts)
                    if depth > 3:
                        continue
                    for f in files:
                        p = Path(root) / f
                        try:
                            artifacts.append(str(p.relative_to(working_dir)))
                        except ValueError:
                            pass
            except OSError:
                pass
            artifacts.sort()
        return SandboxResult(
            success=result.returncode == 0,
            exit_code=result.returncode,
            stdout=stdout,
            stderr=stderr,
            execution_time_ms=elapsed_ms,
            artifacts=artifacts,
            command=command,
            working_dir=str(working_dir),
            truncated=truncated,
        )

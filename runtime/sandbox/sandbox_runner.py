"""
Sandbox Runner — M3.2 isolated command execution.

Executes commands in a controlled environment with strict guardrails.
Never uses shell=True. Captures all outputs for audit.

Architecture principle:
    DES → propose
    CONF → authorize
    CODE → execute (sandboxed) ← this module
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from runtime.sandbox.sandbox_errors import (
    SandboxExecutionError,
    SandboxPolicyViolation,
    SandboxTimeout,
)
from runtime.sandbox.sandbox_policy import SandboxPolicy
from runtime.sandbox.sandbox_result import SandboxResult


class SandboxRunner:
    """
    Isolated command execution with strict guardrails.
    
    Responsibilities:
    - Run commands in isolated working directory
    - Enforce execution limits
    - Capture stdout/stderr
    - Collect artifacts
    - Never allow shell=True
    
    All commands are validated against policy before execution (fail-closed).
    """

    def __init__(
        self,
        policy: SandboxPolicy | None = None,
        artifact_callback: Callable[[str], None] | None = None,
    ):
        """
        Initialize sandbox runner.
        
        Args:
            policy: Execution policy. If None, uses default policy.
            artifact_callback: Optional callback invoked for each discovered artifact.
        """
        self.policy = policy or SandboxPolicy()
        self.artifact_callback = artifact_callback

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
            timeout_seconds: Execution timeout (overrides policy if provided).
            env: Environment variables (filtered by policy).
            capture_artifacts: If True, scan for new files after execution.
            
        Returns:
            SandboxResult with execution details.
            
        Raises:
            SandboxPolicyViolation: If command violates policy.
            SandboxTimeout: If execution exceeds timeout.
            SandboxExecutionError: If execution fails unexpectedly.
        """
        working_dir = Path(working_dir)
        
        # Validate command against policy
        is_valid, reason = self.policy.validate_command(command)
        if not is_valid:
            raise SandboxPolicyViolation(command, reason)
        
        # Validate working directory
        is_valid, reason = self.policy.validate_working_dir(working_dir)
        if not is_valid:
            raise SandboxPolicyViolation(command, reason)
        
        # Ensure working directory exists
        if not working_dir.exists():
            raise SandboxExecutionError(
                command,
                f"Working directory does not exist: {working_dir}",
            )
        
        # Determine timeout
        effective_timeout = timeout_seconds or self.policy.max_execution_time
        
        # Filter environment
        effective_env = self._build_environment(env)
        
        # Capture pre-execution file state for artifact detection
        pre_files: set[str] = set()
        if capture_artifacts:
            pre_files = self._scan_files(working_dir)
        
        # Execute command
        start_time = time.monotonic()
        try:
            result = subprocess.run(
                command,
                cwd=working_dir,
                capture_output=True,
                timeout=effective_timeout,
                env=effective_env,
                shell=False,  # Never shell=True
            )
        except subprocess.TimeoutExpired as e:
            raise SandboxTimeout(command, effective_timeout) from e
        except OSError as e:
            raise SandboxExecutionError(
                command,
                f"Failed to execute command: {e}",
                original_error=e,
            ) from e
        except Exception as e:
            raise SandboxExecutionError(
                command,
                f"Unexpected error: {e}",
                original_error=e,
            ) from e
        
        end_time = time.monotonic()
        execution_time_ms = int((end_time - start_time) * 1000)
        
        # Process output
        stdout, stderr, truncated = self._process_output(
            result.stdout,
            result.stderr,
        )
        
        # Detect artifacts
        artifacts: list[str] = []
        if capture_artifacts:
            post_files = self._scan_files(working_dir)
            new_files = post_files - pre_files
            artifacts = sorted(new_files)
            for artifact in artifacts:
                if self.artifact_callback:
                    self.artifact_callback(artifact)
        
        return SandboxResult(
            success=result.returncode == 0,
            exit_code=result.returncode,
            stdout=stdout,
            stderr=stderr,
            execution_time_ms=execution_time_ms,
            artifacts=artifacts,
            command=command,
            working_dir=str(working_dir),
            truncated=truncated,
        )

    def _build_environment(self, env: dict[str, str] | None) -> dict[str, str]:
        """
        Build execution environment from base OS env and provided overrides.
        
        Applies policy filtering to both sources.
        """
        # Start with filtered OS environment
        base_env = self.policy.filter_environment(dict(os.environ))
        
        # Add filtered custom env
        if env:
            filtered_custom = self.policy.filter_environment(env)
            base_env.update(filtered_custom)
        
        # Always set sandbox marker
        base_env["SANDBOX_EXECUTION"] = "1"
        
        return base_env

    def _process_output(
        self,
        stdout: bytes,
        stderr: bytes,
    ) -> tuple[str, str, bool]:
        """
        Decode and truncate output according to policy.
        
        Returns:
            Tuple of (stdout_str, stderr_str, was_truncated).
        """
        max_bytes = self.policy.max_output_bytes
        half_max = max_bytes // 2
        
        truncated = False
        
        # Truncate if needed
        if len(stdout) > half_max:
            stdout = stdout[:half_max]
            truncated = True
        
        if len(stderr) > half_max:
            stderr = stderr[:half_max]
            truncated = True
        
        # Decode with error handling
        try:
            stdout_str = stdout.decode("utf-8", errors="replace")
        except Exception:
            stdout_str = stdout.decode("latin-1", errors="replace")
        
        try:
            stderr_str = stderr.decode("utf-8", errors="replace")
        except Exception:
            stderr_str = stderr.decode("latin-1", errors="replace")
        
        return stdout_str, stderr_str, truncated

    def _scan_files(self, directory: Path, max_depth: int = 3) -> set[str]:
        """
        Scan directory for files (limited depth for performance).
        
        Returns set of relative file paths.
        """
        files: set[str] = set()
        
        try:
            for root, _, filenames in os.walk(directory):
                # Calculate depth
                rel_root = Path(root).relative_to(directory)
                depth = len(rel_root.parts)
                if depth > max_depth:
                    continue
                
                for filename in filenames:
                    file_path = Path(root) / filename
                    try:
                        rel_path = str(file_path.relative_to(directory))
                        files.add(rel_path)
                    except ValueError:
                        continue
        except OSError:
            pass
        
        return files

    def validate_only(self, command: list[str], working_dir: Path | str) -> tuple[bool, str]:
        """
        Validate command without executing.
        
        Useful for dry-run validation in orchestration flows.
        
        Returns:
            Tuple of (is_valid, reason).
        """
        working_dir = Path(working_dir)
        
        is_valid, reason = self.policy.validate_command(command)
        if not is_valid:
            return False, reason
        
        is_valid, reason = self.policy.validate_working_dir(working_dir)
        if not is_valid:
            return False, reason
        
        if not working_dir.exists():
            return False, f"Working directory does not exist: {working_dir}"
        
        return True, ""

    def to_dict(self) -> dict[str, Any]:
        """Return runner configuration for audit."""
        return {
            "policy": self.policy.to_dict(),
        }

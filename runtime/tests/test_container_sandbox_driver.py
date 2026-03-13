"""
Tests for M3.11 container sandbox driver.

Covers:
- driver_name observability
- validate_only when runtime missing (fail-closed)
- validate_only when runtime available
- run fail-closed when runtime missing or misconfigured
- executor with container driver returns same governed contract
- create_sandbox_driver selection
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import mock

import pytest

from runtime.sandbox.container_sandbox_driver import (
    CONTAINER_WORKSPACE,
    DEFAULT_IMAGE,
    ContainerSandboxDriver,
    _check_runtime_available,
    _find_container_runtime,
)
from runtime.sandbox.sandbox_errors import SandboxExecutionError, SandboxPolicyViolation
from runtime.sandbox.sandbox_executor import SandboxAction, SandboxExecutor
from runtime.sandbox.sandbox_policy import SandboxPolicy
from runtime.sandbox.sandbox_result import SandboxResult


class TestContainerDriverObservability:
    def test_driver_name_is_container(self) -> None:
        driver = ContainerSandboxDriver()
        assert driver.driver_name == "container"


class TestContainerDriverFailClosed:
    """Fail-closed when runtime unavailable or misconfigured."""

    def test_validate_only_when_runtime_missing_returns_false(self) -> None:
        """When no podman/docker, validate_only returns (False, reason)."""
        with mock.patch("runtime.sandbox.container_sandbox_driver._find_container_runtime", return_value=(None, "no runtime")):
            driver = ContainerSandboxDriver()
            with tempfile.TemporaryDirectory() as tmp:
                valid, reason = driver.validate_only(["echo", "x"], tmp)
            assert valid is False
            assert "runtime" in reason.lower() or "podman" in reason.lower() or "docker" in reason.lower()

    def test_run_when_runtime_missing_raises(self) -> None:
        """When no runtime, run raises SandboxExecutionError (fail-closed, no execution)."""
        with mock.patch("runtime.sandbox.container_sandbox_driver._find_container_runtime", return_value=(None, "no runtime")):
            driver = ContainerSandboxDriver()
            with tempfile.TemporaryDirectory() as tmp:
                with pytest.raises(SandboxExecutionError) as exc_info:
                    driver.run(["echo", "x"], tmp)
            assert "runtime" in str(exc_info.value).lower() or "podman" in str(exc_info.value).lower()

    def test_run_with_invalid_override_runtime_raises(self) -> None:
        """Configured runtime binary that does not exist raises SandboxExecutionError."""
        driver = ContainerSandboxDriver(runtime="/nonexistent/podman")
        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(SandboxExecutionError) as exc_info:
                driver.run(["echo", "x"], tmp)
            assert "not found" in str(exc_info.value).lower() or "nonexistent" in str(exc_info.value).lower()

    def test_validate_only_policy_violation_returns_false(self) -> None:
        """Disallowed command fails validate_only with reason."""
        with mock.patch("runtime.sandbox.container_sandbox_driver._check_runtime_available", return_value=(True, "")):
            driver = ContainerSandboxDriver()
            with tempfile.TemporaryDirectory() as tmp:
                valid, reason = driver.validate_only(["curl", "http://x.com"], tmp)
            assert valid is False
            assert "not in allowed" in reason or "allowed" in reason.lower()

    def test_run_policy_violation_raises(self) -> None:
        """Disallowed command in run raises SandboxPolicyViolation (BLOCKED path in executor)."""
        with mock.patch.object(ContainerSandboxDriver, "_get_runtime", return_value="/usr/bin/podman"):
            driver = ContainerSandboxDriver()
            with tempfile.TemporaryDirectory() as tmp:
                with pytest.raises(SandboxPolicyViolation):
                    driver.run(["curl", "http://x.com"], tmp)


class TestContainerDriverContract:
    """Container driver satisfies SandboxDriver / BaseSandboxDriver contract."""

    def test_validate_only_success_when_runtime_available_and_command_allowed(self) -> None:
        with mock.patch("runtime.sandbox.container_sandbox_driver._check_runtime_available", return_value=(True, "")):
            driver = ContainerSandboxDriver()
            with tempfile.TemporaryDirectory() as tmp:
                valid, reason = driver.validate_only(["echo", "hi"], tmp)
            assert valid is True
            assert reason == ""

    def test_run_returns_sandbox_result_when_mocked_run_succeeds(self) -> None:
        """When subprocess is mocked to succeed, run returns SandboxResult (executed path)."""
        with mock.patch.object(ContainerSandboxDriver, "_get_runtime", return_value="/usr/bin/podman"):
            with mock.patch("runtime.sandbox.container_sandbox_driver.subprocess.run") as m_run:
                m_run.return_value = mock.Mock(
                    returncode=0,
                    stdout=b"hello",
                    stderr=b"",
                )
                driver = ContainerSandboxDriver()
                with tempfile.TemporaryDirectory() as tmp:
                    result = driver.run(["echo", "hello"], tmp)
                assert isinstance(result, SandboxResult)
                assert result.success is True
                assert result.exit_code == 0
                assert "hello" in result.stdout

    def test_run_returns_sandbox_result_failed_when_mocked_exit_nonzero(self) -> None:
        with mock.patch.object(ContainerSandboxDriver, "_get_runtime", return_value="/usr/bin/podman"):
            with mock.patch("runtime.sandbox.container_sandbox_driver.subprocess.run") as m_run:
                m_run.return_value = mock.Mock(returncode=1, stdout=b"", stderr=b"err")
                policy = SandboxPolicy(allowed_commands={"echo", "python3", "false"})
                driver = ContainerSandboxDriver(policy=policy)
                with tempfile.TemporaryDirectory() as tmp:
                    result = driver.run(["false"], tmp)
                assert isinstance(result, SandboxResult)
                assert result.success is False
                assert result.exit_code == 1


class TestExecutorWithContainerDriver:
    """SandboxExecutor with container driver preserves governed contract."""

    def test_executor_with_container_driver_fail_closed_returns_executed_failed(self) -> None:
        """When container driver raises (e.g. no runtime), executor returns EXECUTED (failed), not bypass."""
        with mock.patch("runtime.sandbox.container_sandbox_driver._find_container_runtime", return_value=(None, "no runtime")):
            driver = ContainerSandboxDriver()
            executor = SandboxExecutor(driver=driver)
            with tempfile.TemporaryDirectory() as tmp:
                result = executor.execute_sandbox_action(
                    SandboxAction(
                        task_id="t1", command=["echo", "x"], working_dir=tmp,
                        metadata={"canonical_hash": "test-derived"},
                    )
                )
            assert result.outcome_type == "executed"
            assert result.final_status == "executed_failed"
            assert result.success is False

    def test_executor_with_container_driver_blocked_still_blocked(self) -> None:
        """Policy violation via container driver still produces BLOCKED."""
        with mock.patch("runtime.sandbox.container_sandbox_driver._check_runtime_available", return_value=(True, "")):
            driver = ContainerSandboxDriver()
            executor = SandboxExecutor(driver=driver)
            with tempfile.TemporaryDirectory() as tmp:
                result = executor.execute_sandbox_action(
                    SandboxAction(
                        task_id="t1", command=["curl", "http://x.com"], working_dir=tmp,
                        metadata={"canonical_hash": "test-derived"},
                    )
                )
            assert result.outcome_type == "blocked"
            assert result.success is False


class TestCreateSandboxDriver:
    """create_sandbox_driver selection."""

    def test_create_local_process_default(self) -> None:
        from runtime.sandbox import create_sandbox_driver
        driver = create_sandbox_driver()
        assert driver.driver_name == "local_process"

    def test_create_local_process_explicit(self) -> None:
        from runtime.sandbox import create_sandbox_driver
        driver = create_sandbox_driver("local_process")
        assert driver.driver_name == "local_process"

    def test_create_container(self) -> None:
        from runtime.sandbox import create_sandbox_driver
        driver = create_sandbox_driver("container")
        assert driver.driver_name == "container"

    def test_create_container_with_image(self) -> None:
        from runtime.sandbox import create_sandbox_driver
        driver = create_sandbox_driver("container", image="alpine:latest")
        assert driver.driver_name == "container"
        assert driver._image == "alpine:latest"


class TestContainerDriverConstants:
    def test_default_image_and_workspace(self) -> None:
        assert DEFAULT_IMAGE == "python:3.12-slim"
        assert CONTAINER_WORKSPACE == "/workspace"

    def test_find_container_runtime_returns_tuple(self) -> None:
        path, err = _find_container_runtime()
        # Either we have a path (podman/docker found) or we have an error message
        if path is None:
            assert err
            assert "podman" in err or "docker" in err
        else:
            assert "podman" in path or "docker" in path
            assert not err


class TestContainerDriverLive:
    """Live container execution when runtime is available (skip otherwise)."""

    @pytest.mark.skipif(
        _find_container_runtime()[0] is None,
        reason="No container runtime (podman/docker) available",
    )
    def test_run_echo_in_container_when_runtime_available(self) -> None:
        """Execute echo in container; proves full path and stronger isolation."""
        driver = ContainerSandboxDriver()
        with tempfile.TemporaryDirectory() as tmp:
            result = driver.run(["echo", "hello-container"], tmp, timeout_seconds=30)
        assert result.success is True
        assert result.exit_code == 0
        assert "hello-container" in result.stdout
        assert driver.driver_name == "container"

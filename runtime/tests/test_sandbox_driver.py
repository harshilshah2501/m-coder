"""
Tests for M3.10 sandbox driver abstraction.

Covers:
- LocalProcessSandboxDriver run/validate_only behavior
- SandboxExecutor using default driver (unchanged semantics)
- SandboxExecutor using custom driver (pluggable seam)
- No governance logic in driver; outcomes remain REFUSED/BLOCKED/EXECUTED
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from runtime.sandbox.sandbox_driver import LocalProcessSandboxDriver, SandboxDriver
from runtime.sandbox.sandbox_errors import SandboxPolicyViolation, SandboxTimeout
from runtime.sandbox.sandbox_executor import SandboxAction, SandboxExecutor
from runtime.sandbox.sandbox_policy import SandboxPolicy
from runtime.sandbox.sandbox_result import GovernedExecutionResult, SandboxResult


class TestLocalProcessSandboxDriver:
    """LocalProcessSandboxDriver delegates to SandboxRunner and preserves semantics."""

    def test_run_success(self) -> None:
        driver = LocalProcessSandboxDriver()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = driver.run(
                command=["echo", "hello"],
                working_dir=tmpdir,
            )
        assert isinstance(result, SandboxResult)
        assert result.success is True
        assert result.exit_code == 0
        assert "hello" in result.stdout

    def test_run_policy_violation(self) -> None:
        driver = LocalProcessSandboxDriver()
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(SandboxPolicyViolation):
                driver.run(
                    command=["curl", "http://example.com"],
                    working_dir=tmpdir,
                )

    def test_run_timeout(self) -> None:
        driver = LocalProcessSandboxDriver()
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(SandboxTimeout):
                driver.run(
                    command=["python3", "-c", "import time; time.sleep(10)"],
                    working_dir=tmpdir,
                    timeout_seconds=1,
                )

    def test_validate_only_valid(self) -> None:
        driver = LocalProcessSandboxDriver()
        with tempfile.TemporaryDirectory() as tmpdir:
            valid, reason = driver.validate_only(["echo", "x"], tmpdir)
        assert valid is True
        assert reason == ""

    def test_validate_only_invalid(self) -> None:
        driver = LocalProcessSandboxDriver()
        with tempfile.TemporaryDirectory() as tmpdir:
            valid, reason = driver.validate_only(["curl", "x"], tmpdir)
        assert valid is False
        assert "not in allowed list" in reason

    def test_driver_with_custom_policy(self) -> None:
        policy = SandboxPolicy(allowed_commands={"echo", "cat"}, max_execution_time=10)
        driver = LocalProcessSandboxDriver(policy=policy)
        with tempfile.TemporaryDirectory() as tmpdir:
            result = driver.run(command=["echo", "ok"], working_dir=tmpdir)
        assert result.success is True
        with tempfile.TemporaryDirectory() as tmpdir2:
            valid, _ = driver.validate_only(["python3", "-c", "print(1)"], tmpdir2)
        assert valid is False

    def test_driver_name_for_observability(self) -> None:
        """driver_name is set for operational debugging (e.g. logs: sandbox_driver=local_process)."""
        driver = LocalProcessSandboxDriver()
        assert driver.driver_name == "local_process"


class TestExecutorThroughDriver:
    """SandboxExecutor with default driver preserves existing behavior."""

    def test_executor_default_driver_executed(self) -> None:
        executor = SandboxExecutor()
        with tempfile.TemporaryDirectory() as tmpdir:
            action = SandboxAction(
                task_id="t1",
                command=["echo", "default"],
                working_dir=tmpdir,
            )
            result = executor.execute_sandbox_action(action)
        assert result.outcome_type == "executed"
        assert result.success is True
        assert "default" in result.stdout_summary

    def test_executor_default_driver_blocked(self) -> None:
        executor = SandboxExecutor()
        with tempfile.TemporaryDirectory() as tmpdir:
            action = SandboxAction(
                task_id="t1",
                command=["curl", "http://x.com"],
                working_dir=tmpdir,
            )
            result = executor.execute_sandbox_action(action)
        assert result.outcome_type == "blocked"
        assert result.success is False
        assert result.blocked_reason

    def test_executor_validate_action_uses_driver(self) -> None:
        executor = SandboxExecutor()
        with tempfile.TemporaryDirectory() as tmpdir:
            valid, _ = executor.validate_action(
                SandboxAction(task_id="t1", command=["echo", "x"], working_dir=tmpdir)
            )
        assert valid is True
        valid, _ = executor.validate_action(
            SandboxAction(task_id="t1", command=["curl", "x"], working_dir=tmpdir)
        )
        assert valid is False


class TestExecutorWithCustomDriver:
    """Executor with injected driver uses driver for execution; governance stays in executor."""

    def test_custom_driver_used(self) -> None:
        """Executor uses custom driver when provided; outcome still GovernedExecutionResult."""
        captured: list[list[str]] = []

        class RecordingDriver:
            driver_name = "recording"

            def run(
                self,
                command: list[str],
                working_dir: Path | str,
                *,
                timeout_seconds: int | None = None,
                env: dict[str, str] | None = None,
                capture_artifacts: bool = True,
            ) -> SandboxResult:
                captured.append(command)
                return SandboxResult(
                    success=True,
                    exit_code=0,
                    stdout="from-custom-driver",
                    stderr="",
                    execution_time_ms=1,
                    command=command,
                    working_dir=str(working_dir),
                )

            def validate_only(self, command: list[str], working_dir: Path | str) -> tuple[bool, str]:
                return True, ""

        driver = RecordingDriver()
        executor = SandboxExecutor(driver=driver)  # type: ignore[arg-type]
        with tempfile.TemporaryDirectory() as tmpdir:
            action = SandboxAction(
                task_id="t1",
                command=["custom", "cmd"],
                working_dir=tmpdir,
            )
            result = executor.execute_sandbox_action(action)
        assert result.outcome_type == "executed"
        assert result.success is True
        assert result.stdout_summary == "from-custom-driver"
        assert captured == [["custom", "cmd"]]

    def test_governance_stays_in_executor_ledger(self) -> None:
        """With custom driver, executor still produces ledger linkage and correct outcome_type."""
        class StubDriver:
            driver_name = "stub"

            def run(
                self,
                command: list[str],
                working_dir: Path | str,
                *,
                timeout_seconds: int | None = None,
                env: dict[str, str] | None = None,
                capture_artifacts: bool = True,
            ) -> SandboxResult:
                return SandboxResult(
                    success=False,
                    exit_code=1,
                    stdout="",
                    stderr="err",
                    execution_time_ms=0,
                    command=command,
                    working_dir=str(working_dir),
                )

            def validate_only(self, command: list[str], working_dir: Path | str) -> tuple[bool, str]:
                return True, ""

        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.db"
            from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore

            store = SandboxLedgerStore(ledger_path)
            executor = SandboxExecutor(driver=StubDriver(), ledger_store=store)  # type: ignore[arg-type]
            action = SandboxAction(
                task_id="task-ledger",
                command=["stub"],
                working_dir=tmp,
            )
            result = executor.execute_sandbox_action(action)
            assert result.outcome_type == "executed"
            assert result.final_status == "executed_failed"
            assert result.ledger_row_id
            rows = store.list_all()
            assert any(r.outcome_type == "executed" for r in rows)


class TestDriverContract:
    """Driver abstraction does not expose or move governance."""

    def test_governed_result_unchanged(self) -> None:
        """GovernedExecutionResult contract (refused/blocked/executed) unchanged."""
        r = GovernedExecutionResult(
            outcome_type="executed",
            request_id="r1",
            plan_hash="",
            sandbox_id="s1",
            success=True,
            final_status="executed_ok",
            commands_executed=["echo x"],
            ledger_row_id="lid-1",
        )
        d = r.to_dict()
        assert d["outcome_type"] == "executed"
        assert d["request_id"] == "r1"
        assert "commands_executed" in d
        assert "ledger_row_id" in d

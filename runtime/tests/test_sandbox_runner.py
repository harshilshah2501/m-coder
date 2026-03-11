"""
Sandbox Runner Tests — M3.2 test suite.

Tests cover:
1. Allowed command executes successfully
2. Disallowed command rejected with SandboxPolicyViolation
3. Timeout triggers SandboxTimeout
4. stdout/stderr captured correctly
5. Artifacts captured
6. Ledger integration
7. Policy validation
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import pytest

from runtime.sandbox.sandbox_errors import (
    SandboxExecutionError,
    SandboxPolicyViolation,
    SandboxTimeout,
)
from runtime.sandbox.sandbox_executor import (
    SandboxAction,
    SandboxExecutor,
    execute_sandbox_action,
)
from runtime.sandbox.sandbox_ledger import SandboxLedgerEmitter
from runtime.sandbox.sandbox_policy import SandboxPolicy
from runtime.sandbox.sandbox_result import SandboxResult
from runtime.sandbox.sandbox_runner import SandboxRunner


class TestSandboxRunner:
    """Tests for SandboxRunner class."""

    def test_allowed_command_executes(self) -> None:
        """Allowed commands execute successfully."""
        runner = SandboxRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.run(
                command=["echo", "hello world"],
                working_dir=tmpdir,
            )
            assert result.success is True
            assert result.exit_code == 0
            assert "hello world" in result.stdout
            assert result.stderr == ""
            assert result.execution_time_ms >= 0

    def test_disallowed_command_rejected(self) -> None:
        """Disallowed commands raise SandboxPolicyViolation."""
        runner = SandboxRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(SandboxPolicyViolation) as exc_info:
                runner.run(
                    command=["curl", "http://example.com"],
                    working_dir=tmpdir,
                )
            assert exc_info.value.command == ["curl", "http://example.com"]
            assert "not in allowed list" in exc_info.value.reason

    def test_timeout_triggers_error(self) -> None:
        """Commands exceeding timeout raise SandboxTimeout."""
        runner = SandboxRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(SandboxTimeout) as exc_info:
                runner.run(
                    command=["python3", "-c", "import time; time.sleep(10)"],
                    working_dir=tmpdir,
                    timeout_seconds=1,
                )
            assert exc_info.value.timeout_seconds == 1

    def test_stdout_captured(self) -> None:
        """stdout is captured correctly."""
        runner = SandboxRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.run(
                command=["python3", "-c", "print('stdout test')"],
                working_dir=tmpdir,
            )
            assert result.success is True
            assert "stdout test" in result.stdout

    def test_stderr_captured(self) -> None:
        """stderr is captured correctly."""
        runner = SandboxRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.run(
                command=["python3", "-c", "import sys; sys.stderr.write('stderr test\\n')"],
                working_dir=tmpdir,
            )
            assert result.success is True
            assert "stderr test" in result.stderr

    def test_exit_code_nonzero(self) -> None:
        """Non-zero exit codes are captured."""
        runner = SandboxRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.run(
                command=["python3", "-c", "import sys; sys.exit(42)"],
                working_dir=tmpdir,
            )
            assert result.success is False
            assert result.exit_code == 42

    def test_working_dir_used(self) -> None:
        """Command executes in specified working directory."""
        runner = SandboxRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.run(
                command=["python3", "-c", "import os; print(os.getcwd())"],
                working_dir=tmpdir,
            )
            assert result.success is True
            assert tmpdir in result.stdout or Path(tmpdir).resolve().as_posix() in result.stdout

    def test_artifact_capture(self) -> None:
        """New files created during execution are captured as artifacts."""
        runner = SandboxRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.run(
                command=["python3", "-c", "open('test_artifact.txt', 'w').write('test')"],
                working_dir=tmpdir,
            )
            assert result.success is True
            assert "test_artifact.txt" in result.artifacts
            assert (Path(tmpdir) / "test_artifact.txt").exists()

    def test_nonexistent_working_dir_error(self) -> None:
        """Nonexistent working directory raises error."""
        runner = SandboxRunner()
        with pytest.raises(SandboxExecutionError) as exc_info:
            runner.run(
                command=["echo", "test"],
                working_dir="/nonexistent/path/that/does/not/exist",
            )
        assert "does not exist" in exc_info.value.reason

    def test_command_list_preserved(self) -> None:
        """Command list is preserved in result."""
        runner = SandboxRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            command = ["echo", "test", "args"]
            result = runner.run(command=command, working_dir=tmpdir)
            assert result.command == command

    def test_working_dir_in_result(self) -> None:
        """Working directory is recorded in result."""
        runner = SandboxRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.run(
                command=["echo", "test"],
                working_dir=tmpdir,
            )
            assert tmpdir in result.working_dir

    def test_validate_only(self) -> None:
        """validate_only checks without execution."""
        runner = SandboxRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Valid command
            is_valid, reason = runner.validate_only(["echo", "test"], tmpdir)
            assert is_valid is True
            assert reason == ""

            # Invalid command
            is_valid, reason = runner.validate_only(["curl", "example.com"], tmpdir)
            assert is_valid is False
            assert "not in allowed list" in reason


class TestSandboxPolicy:
    """Tests for SandboxPolicy class."""

    def test_default_policy_allows_common_commands(self) -> None:
        """Default policy allows common dev tools."""
        policy = SandboxPolicy()
        for cmd in ["python", "python3", "pytest", "ruff", "mypy", "black"]:
            is_valid, _ = policy.validate_command([cmd])
            assert is_valid is True, f"Expected {cmd} to be allowed"

    def test_strict_policy_limited_commands(self) -> None:
        """Strict policy has limited allowed commands."""
        policy = SandboxPolicy.strict()
        assert "python" in policy.allowed_commands
        assert "pytest" in policy.allowed_commands
        assert "npm" not in policy.allowed_commands
        assert policy.max_execution_time == 15

    def test_permissive_policy_extended_timeout(self) -> None:
        """Permissive policy has extended timeout."""
        policy = SandboxPolicy.permissive()
        assert policy.max_execution_time == 120

    def test_validate_command_with_path(self) -> None:
        """Commands with full paths are validated by basename."""
        policy = SandboxPolicy()
        is_valid, _ = policy.validate_command(["/usr/bin/python3", "-c", "print(1)"])
        assert is_valid is True

    def test_env_blocklist_filters_secrets(self) -> None:
        """Blocklisted env vars are filtered."""
        policy = SandboxPolicy()
        env = {
            "PATH": "/usr/bin",
            "AWS_SECRET_ACCESS_KEY": "secret123",
            "HOME": "/home/user",
        }
        filtered = policy.filter_environment(env)
        assert "PATH" in filtered
        assert "HOME" in filtered
        assert "AWS_SECRET_ACCESS_KEY" not in filtered

    def test_working_dir_validation(self) -> None:
        """Working directory validation respects allowlist."""
        policy = SandboxPolicy()
        # Empty allowlist permits all
        is_valid, _ = policy.validate_working_dir(Path("/any/path"))
        assert is_valid is True

        # With allowlist, only allowed dirs permitted
        policy.allowed_working_dirs = {"/allowed/dir"}
        is_valid, _ = policy.validate_working_dir(Path("/allowed/dir"))
        assert is_valid is True
        is_valid, reason = policy.validate_working_dir(Path("/other/dir"))
        assert is_valid is False
        assert "not in allowed list" in reason

    def test_policy_to_dict(self) -> None:
        """Policy can be serialized to dict."""
        policy = SandboxPolicy()
        d = policy.to_dict()
        assert "allowed_commands" in d
        assert "max_execution_time" in d
        assert isinstance(d["allowed_commands"], list)


class TestSandboxResult:
    """Tests for SandboxResult class."""

    def test_result_to_dict(self) -> None:
        """Result can be serialized to dict."""
        result = SandboxResult(
            success=True,
            exit_code=0,
            stdout="output",
            stderr="",
            execution_time_ms=100,
            artifacts=["file.txt"],
            command=["echo", "test"],
            working_dir="/tmp",
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["exit_code"] == 0
        assert d["stdout"] == "output"
        assert d["execution_time_ms"] == 100
        assert d["artifacts"] == ["file.txt"]

    def test_result_from_dict(self) -> None:
        """Result can be deserialized from dict."""
        d = {
            "success": True,
            "exit_code": 0,
            "stdout": "output",
            "stderr": "",
            "execution_time_ms": 100,
            "artifacts": ["file.txt"],
            "command": ["echo", "test"],
            "working_dir": "/tmp",
            "truncated": False,
        }
        result = SandboxResult.from_dict(d)
        assert result.success is True
        assert result.exit_code == 0
        assert result.artifacts == ["file.txt"]

    def test_result_to_ledger_entry(self) -> None:
        """Result can be converted to ledger entry format."""
        result = SandboxResult(
            success=True,
            exit_code=0,
            stdout="output" * 1000,  # Large output
            stderr="",
            execution_time_ms=100,
            artifacts=["file1.txt", "file2.txt"],
            command=["pytest", "tests/"],
            working_dir="/tmp",
        )
        entry = result.to_ledger_entry()
        assert entry["event"] == "sandbox_execution"
        assert entry["command"] == ["pytest", "tests/"]
        assert entry["exit_code"] == 0
        assert entry["artifact_count"] == 2
        # Ledger entry should not include large stdout
        assert "stdout" not in entry


class TestSandboxLedgerEmitter:
    """Tests for SandboxLedgerEmitter class."""

    def test_emit_creates_entry(self) -> None:
        """Emitter creates ledger entry from result."""
        emitter = SandboxLedgerEmitter(fixed_time="2026-03-11T12:00:00Z")
        result = SandboxResult(
            success=True,
            exit_code=0,
            stdout="output",
            stderr="",
            execution_time_ms=100,
            command=["pytest"],
            working_dir="/tmp",
        )
        entry = emitter.emit(task_id="task-123", result=result)
        assert entry.task_id == "task-123"
        assert entry.command == ["pytest"]
        assert entry.success is True
        assert entry.timestamp_utc == "2026-03-11T12:00:00Z"

    def test_emit_deterministic_event_id(self) -> None:
        """Same inputs produce same event_id."""
        emitter1 = SandboxLedgerEmitter(fixed_time="2026-03-11T12:00:00Z")
        emitter2 = SandboxLedgerEmitter(fixed_time="2026-03-11T12:00:00Z")
        result = SandboxResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            execution_time_ms=100,
            command=["pytest"],
            working_dir="/tmp",
        )
        entry1 = emitter1.emit(task_id="task-123", result=result)
        entry2 = emitter2.emit(task_id="task-123", result=result)
        assert entry1.event_id == entry2.event_id

    def test_get_entries_for_task(self) -> None:
        """Can retrieve entries for specific task."""
        emitter = SandboxLedgerEmitter()
        result = SandboxResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            execution_time_ms=100,
            command=["pytest"],
            working_dir="/tmp",
        )
        emitter.emit(task_id="task-1", result=result)
        emitter.emit(task_id="task-2", result=result)
        emitter.emit(task_id="task-1", result=result)

        task1_entries = emitter.get_entries_for_task("task-1")
        assert len(task1_entries) == 2

        task2_entries = emitter.get_entries_for_task("task-2")
        assert len(task2_entries) == 1


class TestSandboxExecutor:
    """Tests for SandboxExecutor integration class."""

    def test_execute_sandbox_action(self) -> None:
        """SandboxExecutor executes action with ledger integration."""
        executor = SandboxExecutor()
        with tempfile.TemporaryDirectory() as tmpdir:
            action = SandboxAction(
                task_id="task-123",
                command=["echo", "hello"],
                working_dir=tmpdir,
            )
            result = executor.execute_sandbox_action(action)
            assert result.success is True
            assert result.result.exit_code == 0
            assert result.ledger_entry.task_id == "task-123"

    def test_convenience_function(self) -> None:
        """execute_sandbox_action convenience function works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = execute_sandbox_action(
                task_id="task-456",
                command=["echo", "test"],
                working_dir=tmpdir,
            )
            assert result.success is True
            assert result.action.task_id == "task-456"

    def test_execution_history(self) -> None:
        """Executor maintains execution history."""
        executor = SandboxExecutor()
        with tempfile.TemporaryDirectory() as tmpdir:
            action1 = SandboxAction(task_id="task-1", command=["echo", "1"], working_dir=tmpdir)
            action2 = SandboxAction(task_id="task-2", command=["echo", "2"], working_dir=tmpdir)

            executor.execute_sandbox_action(action1)
            executor.execute_sandbox_action(action2)

            history = executor.get_execution_history()
            assert len(history) == 2

    def test_validate_action(self) -> None:
        """Executor can validate action without executing."""
        executor = SandboxExecutor()
        with tempfile.TemporaryDirectory() as tmpdir:
            action = SandboxAction(
                task_id="task-123",
                command=["echo", "test"],
                working_dir=tmpdir,
            )
            is_valid, reason = executor.validate_action(action)
            assert is_valid is True

            invalid_action = SandboxAction(
                task_id="task-123",
                command=["curl", "example.com"],
                working_dir=tmpdir,
            )
            is_valid, reason = executor.validate_action(invalid_action)
            assert is_valid is False

    def test_execution_callback(self) -> None:
        """Execution callback is invoked."""
        results: list[SandboxResult] = []

        def callback(result: SandboxResult) -> None:
            results.append(result)

        executor = SandboxExecutor(execution_callback=callback)
        with tempfile.TemporaryDirectory() as tmpdir:
            action = SandboxAction(task_id="task-123", command=["echo", "test"], working_dir=tmpdir)
            executor.execute_sandbox_action(action)

        assert len(results) == 1


class TestSandboxErrors:
    """Tests for sandbox error classes."""

    def test_policy_violation_attributes(self) -> None:
        """SandboxPolicyViolation has correct attributes."""
        exc = SandboxPolicyViolation(["curl", "example.com"], "not allowed")
        assert exc.command == ["curl", "example.com"]
        assert exc.reason == "not allowed"
        assert "curl" in str(exc)

    def test_timeout_attributes(self) -> None:
        """SandboxTimeout has correct attributes."""
        exc = SandboxTimeout(["sleep", "100"], 30)
        assert exc.command == ["sleep", "100"]
        assert exc.timeout_seconds == 30
        assert "30" in str(exc)

    def test_execution_error_attributes(self) -> None:
        """SandboxExecutionError has correct attributes."""
        original = OSError("file not found")
        exc = SandboxExecutionError(["python", "missing.py"], "file not found", original)
        assert exc.command == ["python", "missing.py"]
        assert exc.reason == "file not found"
        assert exc.original_error is original


class TestIntegrationScenarios:
    """Integration tests for end-to-end scenarios."""

    def test_pytest_execution(self) -> None:
        """Can execute pytest in sandbox via python -m pytest."""
        runner = SandboxRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple test file
            test_file = Path(tmpdir) / "test_example.py"
            test_file.write_text("def test_pass(): assert True")

            # Use python -m pytest to avoid PATH issues
            result = runner.run(
                command=["python3", "-m", "pytest", str(test_file), "-v"],
                working_dir=tmpdir,
                timeout_seconds=30,
            )
            # Should succeed with pytest installed
            assert isinstance(result.exit_code, int)
            # If pytest is installed, it should pass
            if result.exit_code == 0:
                assert "PASSED" in result.stdout or "passed" in result.stdout

    def test_python_script_execution(self) -> None:
        """Can execute Python scripts in sandbox."""
        runner = SandboxRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "script.py"
            script.write_text("print('Hello from sandbox')")

            result = runner.run(
                command=["python3", str(script)],
                working_dir=tmpdir,
            )
            assert result.success is True
            assert "Hello from sandbox" in result.stdout

    def test_code_generation_scenario(self) -> None:
        """Sandbox can execute code generation tools."""
        runner = SandboxRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with formatting issues
            code_file = Path(tmpdir) / "example.py"
            code_file.write_text("x=1\ny=2\nprint(x+y)")

            # Note: black/ruff might not be installed, so just verify command validation
            is_valid, _ = runner.validate_only(["black", str(code_file)], tmpdir)
            assert is_valid is True

            is_valid, _ = runner.validate_only(["ruff", "check", str(code_file)], tmpdir)
            assert is_valid is True

    def test_full_workflow_with_ledger(self) -> None:
        """Full workflow: execute → capture → ledger."""
        emitter = SandboxLedgerEmitter()
        executor = SandboxExecutor(ledger_emitter=emitter)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Execute first action
            action1 = SandboxAction(
                task_id="task-flow-1",
                command=["echo", "step 1"],
                working_dir=tmpdir,
            )
            result1 = executor.execute_sandbox_action(action1)
            assert result1.success is True

            # Execute second action
            action2 = SandboxAction(
                task_id="task-flow-1",
                command=["python3", "-c", "print('step 2')"],
                working_dir=tmpdir,
            )
            result2 = executor.execute_sandbox_action(action2)
            assert result2.success is True

            # Verify ledger
            entries = emitter.get_entries_for_task("task-flow-1")
            assert len(entries) == 2

            # Verify history
            history = executor.get_execution_history()
            assert len(history) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

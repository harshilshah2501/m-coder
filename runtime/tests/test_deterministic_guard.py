"""M4.1 Tests for DeterministicGuard — one suite per refusal category."""

from __future__ import annotations

import pytest

from runtime.integrity.canonical_intent import CanonicalExecutionIntent
from runtime.plangate.pre_gate import DeterministicGuard, GuardResult


def _intent(
    executable: str = "echo",
    argv: tuple[str, ...] = ("echo", "hello"),
    working_dir: str = "/repo",
    repo_root: str = "/repo",
    branch: str = "",
    authority_context: str = "",
) -> CanonicalExecutionIntent:
    return CanonicalExecutionIntent(
        request_id="r1",
        plan_hash="ph1",
        intent_id="i1",
        canonical_hash="h1",
        executable=executable,
        argv=argv,
        working_dir=working_dir,
        repo_root=repo_root,
        env_delta=(),
        timeout_seconds=None,
        capture_artifacts=(),
        branch=branch,
        authority_context=authority_context,
    )


class TestGuardProtectedBranchMutation:
    """protected_branch_mutation: request targets protected branch."""

    def test_main_refused(self) -> None:
        guard = DeterministicGuard()
        intent = _intent(branch="main")
        r = guard.evaluate(intent)
        assert r.refused is True
        assert r.category == "protected_branch_mutation"

    def test_master_refused(self) -> None:
        guard = DeterministicGuard()
        intent = _intent(branch="master")
        r = guard.evaluate(intent)
        assert r.refused is True
        assert r.category == "protected_branch_mutation"

    def test_release_prefix_refused(self) -> None:
        guard = DeterministicGuard()
        intent = _intent(branch="release/1.0")
        r = guard.evaluate(intent)
        assert r.refused is True
        assert r.category == "protected_branch_mutation"

    def test_feature_branch_passes(self) -> None:
        guard = DeterministicGuard()
        intent = _intent(branch="feature/foo")
        r = guard.evaluate(intent)
        assert r.passed is True
        assert r.refused is False


class TestGuardUnsupportedNetworkExecution:
    """unsupported_network_execution: curl, wget."""

    def test_curl_refused(self) -> None:
        guard = DeterministicGuard()
        intent = _intent(executable="curl", argv=("curl", "http://x.com"))
        r = guard.evaluate(intent)
        assert r.refused is True
        assert r.category == "unsupported_network_execution"

    def test_wget_refused(self) -> None:
        guard = DeterministicGuard()
        intent = _intent(executable="wget", argv=("wget", "http://x.com"))
        r = guard.evaluate(intent)
        assert r.refused is True
        assert r.category == "unsupported_network_execution"

    def test_echo_passes(self) -> None:
        guard = DeterministicGuard()
        intent = _intent(executable="echo", argv=("echo", "x"))
        r = guard.evaluate(intent)
        assert r.passed is True


class TestGuardDestructiveFilesystemCommands:
    """destructive_filesystem_commands: rm, mkfs, dd, etc."""

    def test_rm_refused(self) -> None:
        guard = DeterministicGuard()
        intent = _intent(executable="rm", argv=("rm", "-rf", "/tmp/x"))
        r = guard.evaluate(intent)
        assert r.refused is True
        assert r.category == "destructive_filesystem_commands"

    def test_mkfs_refused(self) -> None:
        guard = DeterministicGuard()
        intent = _intent(executable="mkfs", argv=("mkfs.ext4", "/dev/sda1"))
        r = guard.evaluate(intent)
        assert r.refused is True
        assert r.category == "destructive_filesystem_commands"


class TestGuardIrreversibleSystemActions:
    """irreversible_system_actions: pattern in argv."""

    def test_drop_database_pattern_refused(self) -> None:
        guard = DeterministicGuard()
        intent = _intent(executable="psql", argv=("psql", "-c", "drop database prod"))
        r = guard.evaluate(intent)
        assert r.refused is True
        assert r.category == "irreversible_system_actions"


class TestGuardAuthorityMismatch:
    """authority_mismatch: explicit hint only in MVP."""

    def test_authority_context_mismatch_refused(self) -> None:
        guard = DeterministicGuard()
        intent = _intent(authority_context="mismatch")
        r = guard.evaluate(intent)
        assert r.refused is True
        assert r.category == "authority_mismatch"


class TestGuardDoesNotMutateIntent:
    """Guard does not mutate the intent."""

    def test_intent_unchanged_after_evaluate(self) -> None:
        guard = DeterministicGuard()
        intent = _intent(executable="echo", argv=("echo", "x"))
        before_hash = intent.canonical_hash
        guard.evaluate(intent)
        assert intent.canonical_hash == before_hash
        assert intent.argv == ("echo", "x")

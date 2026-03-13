"""M4.1 Tests for CommandNormalizer — same request -> same artifact; malformed rejected."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from runtime.integrity import CommandNormalizer, NormalizationError
from runtime.integrity.canonical_intent import compute_canonical_hash


class TestCommandNormalizerDeterminism:
    """Same request -> same CanonicalExecutionIntent."""

    def test_same_request_same_artifact(self) -> None:
        """Identical request produces identical intent (except intent_id if random)."""
        req = {
            "request_id": "r1",
            "repo_root": "/repo",
            "plan_hash": "ph1",
            "command": "echo hello",
        }
        norm = CommandNormalizer(default_working_dir="/repo")
        a = norm.normalize(req)
        b = norm.normalize(req)
        assert a.request_id == b.request_id
        assert a.argv == b.argv
        assert a.working_dir == b.working_dir
        assert a.canonical_hash == b.canonical_hash

    def test_same_semantic_paths_syntactic_variation_same_hash(self) -> None:
        """Same logical path with different syntactic form -> same working_dir after normalize."""
        base = Path("/tmp").resolve()
        req1 = {"request_id": "r1", "repo_root": str(base), "command": "echo x"}
        req2 = {"request_id": "r1", "repo_root": str(base / "."), "command": "echo x"}
        norm = CommandNormalizer(default_working_dir=str(base))
        i1 = norm.normalize(req1)
        i2 = norm.normalize(req2)
        assert i1.working_dir == i2.working_dir
        assert i1.canonical_hash == i2.canonical_hash

    def test_same_env_content_different_order_same_hash(self) -> None:
        """Env with same keys/values, different order -> same canonical artifact."""
        req1 = {
            "request_id": "r1",
            "repo_root": "/repo",
            "command": "echo x",
            "env": {"B": "2", "A": "1"},
        }
        req2 = {
            "request_id": "r1",
            "repo_root": "/repo",
            "command": "echo x",
            "env": {"A": "1", "B": "2"},
        }
        norm = CommandNormalizer(default_working_dir="/repo")
        i1 = norm.normalize(req1)
        i2 = norm.normalize(req2)
        assert i1.canonical_hash == i2.canonical_hash
        assert dict(i1.env_delta) == dict(i2.env_delta)


class TestCommandNormalizerParsing:
    """Parse command once; argv is canonical."""

    def test_command_string_parsed_to_argv(self) -> None:
        norm = CommandNormalizer(default_working_dir="/repo")
        intent = norm.normalize({
            "request_id": "r1",
            "repo_root": "/repo",
            "command": "echo hello world",
        })
        assert intent.argv == ("echo", "hello", "world")
        assert intent.executable == "echo"

    def test_command_list_accepted(self) -> None:
        norm = CommandNormalizer(default_working_dir="/repo")
        intent = norm.normalize({
            "request_id": "r1",
            "repo_root": "/repo",
            "command": ["python", "-c", "print(1)"],
        })
        assert intent.argv == ("python", "-c", "print(1)")
        assert intent.executable == "python"

    def test_quoted_string_parsed_once(self) -> None:
        norm = CommandNormalizer(default_working_dir="/repo")
        intent = norm.normalize({
            "request_id": "r1",
            "repo_root": "/repo",
            "command": 'echo "hello world"',
        })
        assert intent.argv == ("echo", "hello world")


class TestCommandNormalizerRejectMalformed:
    """Malformed or ambiguous requests rejected deterministically."""

    def test_missing_command_raises(self) -> None:
        norm = CommandNormalizer(default_working_dir="/repo")
        with pytest.raises(NormalizationError, match="command"):
            norm.normalize({"request_id": "r1", "repo_root": "/repo"})

    def test_empty_command_string_raises(self) -> None:
        norm = CommandNormalizer(default_working_dir="/repo")
        with pytest.raises(NormalizationError):
            norm.normalize({
                "request_id": "r1",
                "repo_root": "/repo",
                "command": "   ",
            })

    def test_empty_command_list_raises(self) -> None:
        norm = CommandNormalizer(default_working_dir="/repo")
        with pytest.raises(NormalizationError):
            norm.normalize({
                "request_id": "r1",
                "repo_root": "/repo",
                "command": [],
            })

    def test_invalid_command_type_raises(self) -> None:
        norm = CommandNormalizer(default_working_dir="/repo")
        with pytest.raises(NormalizationError):
            norm.normalize({
                "request_id": "r1",
                "repo_root": "/repo",
                "command": 123,
            })


class TestCommandNormalizerWorkingDir:
    """working_dir normalized to absolute."""

    def test_repo_root_resolved_to_absolute(self) -> None:
        norm = CommandNormalizer(default_working_dir="/default")
        intent = norm.normalize({
            "request_id": "r1",
            "repo_root": "/repo",
            "command": "echo x",
        })
        assert Path(intent.working_dir).is_absolute()
        assert intent.working_dir == str(Path("/repo").resolve())

    def test_explicit_working_dir_used(self) -> None:
        norm = CommandNormalizer(default_working_dir="/default")
        intent = norm.normalize({
            "request_id": "r1",
            "repo_root": "/repo",
            "working_dir": "/explicit",
            "command": "echo x",
        })
        assert intent.working_dir == str(Path("/explicit").resolve())


class TestCanonicalHashReproducibility:
    """canonical_hash from normalizer is reproducible."""

    def test_same_artifact_same_hash(self) -> None:
        req = {"request_id": "r1", "repo_root": "/repo", "command": "echo hi"}
        norm = CommandNormalizer(default_working_dir="/repo")
        i1 = norm.normalize(req)
        i2 = norm.normalize(req)
        assert i1.canonical_hash == i2.canonical_hash
        assert i1.canonical_hash == compute_canonical_hash(i1)

    def test_different_command_different_hash(self) -> None:
        norm = CommandNormalizer(default_working_dir="/repo")
        i1 = norm.normalize({"request_id": "r1", "repo_root": "/repo", "command": "echo a"})
        i2 = norm.normalize({"request_id": "r1", "repo_root": "/repo", "command": "echo b"})
        assert i1.canonical_hash != i2.canonical_hash

"""M4.1 Tests for CanonicalExecutionIntent and canonical_hash."""

from __future__ import annotations

import pytest

from runtime.integrity.canonical_intent import (
    CanonicalExecutionIntent,
    compute_canonical_hash,
    serialize_for_hash,
)


def _intent(
    request_id: str = "req-1",
    plan_hash: str = "ph-1",
    intent_id: str = "intent-1",
    canonical_hash: str = "h1",
    executable: str = "echo",
    argv: tuple[str, ...] = ("echo", "hello"),
    working_dir: str = "/repo",
    repo_root: str = "/repo",
    env_delta: tuple[tuple[str, str], ...] = (("A", "1"), ("B", "2")),
    timeout_seconds: int | None = 30,
    capture_artifacts: tuple[str, ...] = (),
) -> CanonicalExecutionIntent:
    return CanonicalExecutionIntent(
        request_id=request_id,
        plan_hash=plan_hash,
        intent_id=intent_id,
        canonical_hash=canonical_hash,
        executable=executable,
        argv=argv,
        working_dir=working_dir,
        repo_root=repo_root,
        env_delta=env_delta,
        timeout_seconds=timeout_seconds,
        capture_artifacts=capture_artifacts,
    )


class TestCanonicalExecutionIntent:
    """Schema and structure."""

    def test_same_execution_content_same_hash(self) -> None:
        """Same artifact (execution fields) -> same canonical_hash; intent_id excluded."""
        a = _intent(intent_id="id-a", canonical_hash="")
        b = _intent(intent_id="id-b", canonical_hash="")
        ha = compute_canonical_hash(a)
        hb = compute_canonical_hash(b)
        assert ha == hb

    def test_different_argv_different_hash(self) -> None:
        i1 = _intent(argv=("echo", "hello"), canonical_hash="")
        i2 = _intent(argv=("echo", "world"), canonical_hash="")
        assert compute_canonical_hash(i1) != compute_canonical_hash(i2)

    def test_different_working_dir_different_hash(self) -> None:
        i1 = _intent(working_dir="/repo", canonical_hash="")
        i2 = _intent(working_dir="/other", canonical_hash="")
        assert compute_canonical_hash(i1) != compute_canonical_hash(i2)

    def test_different_env_delta_different_hash(self) -> None:
        i1 = _intent(env_delta=(("A", "1"),), canonical_hash="")
        i2 = _intent(env_delta=(("A", "2"),), canonical_hash="")
        assert compute_canonical_hash(i1) != compute_canonical_hash(i2)

    def test_same_env_content_different_order_same_hash(self) -> None:
        """Env with same keys/values in different order -> same hash (normalized order)."""
        i1 = _intent(env_delta=(("B", "2"), ("A", "1")), canonical_hash="")
        i2 = _intent(env_delta=(("A", "1"), ("B", "2")), canonical_hash="")
        assert compute_canonical_hash(i1) == compute_canonical_hash(i2)

    def test_stable_serialization_repeated_runs(self) -> None:
        """Repeated serialize_for_hash yields same bytes."""
        intent = _intent(canonical_hash="")
        b1 = serialize_for_hash(intent)
        b2 = serialize_for_hash(intent)
        assert b1 == b2

    def test_hash_stable_across_runs(self) -> None:
        """Same intent -> same hash across multiple calls."""
        intent = _intent(canonical_hash="")
        h1 = compute_canonical_hash(intent)
        h2 = compute_canonical_hash(intent)
        assert h1 == h2
        assert len(h1) == 64
        assert all(c in "0123456789abcdef" for c in h1)

    def test_to_dict_roundtrip_fields(self) -> None:
        """to_dict contains all execution and identity fields."""
        intent = _intent()
        d = intent.to_dict()
        assert d["request_id"] == intent.request_id
        assert d["plan_hash"] == intent.plan_hash
        assert d["intent_id"] == intent.intent_id
        assert d["canonical_hash"] == intent.canonical_hash
        assert d["executable"] == intent.executable
        assert d["argv"] == list(intent.argv)
        assert d["working_dir"] == intent.working_dir
        assert dict(d["env_delta"]) == dict(intent.env_delta)
        assert d["timeout_seconds"] == intent.timeout_seconds

    def test_intent_is_frozen(self) -> None:
        """CanonicalExecutionIntent is immutable."""
        intent = _intent()
        with pytest.raises(Exception):
            intent.request_id = "other"  # type: ignore[misc]

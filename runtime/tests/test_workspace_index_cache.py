from __future__ import annotations

import threading
import time

from runtime.context_layer_service.workspace_index_cache import (
    IndexCacheKey,
    WorkspaceIndexCache,
)
from runtime.layer5.authority.code_index_models import CodeIndex
from runtime.layer5.index.models import SCHEMA_VERSION, WorkspaceFileIndex


def _dummy_fi() -> WorkspaceFileIndex:
    return WorkspaceFileIndex(
        schema_version=SCHEMA_VERSION,
        workspace_identity_hash="ab" * 32,
        canonical_root="/tmp/ws",
        files=(),
    )


def test_cache_hit_returns_zero_build_ms():
    c = WorkspaceIndexCache(max_keys=4, ttl_sec=0.0)
    key = IndexCacheKey(
        canonical_root="/tmp/ws",
        snapshot_hash="ab" * 32,
    )
    calls = {"n": 0}

    def build():
        calls["n"] += 1
        return (
            _dummy_fi(),
            CodeIndex(),
            {"file_index_build_ms": 12.0, "code_index_build_ms": 34.0},
        )

    fi1, ci1, m1 = c.get_or_build(key, build)
    assert m1["index_cache_hit"] is False
    assert m1["file_index_build_ms"] == 12.0
    assert calls["n"] == 1

    fi2, ci2, m2 = c.get_or_build(key, build)
    assert m2["index_cache_hit"] is True
    assert m2["file_index_build_ms"] == 0.0
    assert m2["code_index_build_ms"] == 0.0
    assert calls["n"] == 1
    assert fi1 is fi2 and ci1 is ci2


def test_cache_miss_when_code_index_none_not_stored():
    c = WorkspaceIndexCache(max_keys=4, ttl_sec=0.0)
    key = IndexCacheKey(
        canonical_root="/tmp/ws",
        snapshot_hash="cd" * 32,
    )
    calls = {"n": 0}

    def build_no_ci():
        calls["n"] += 1
        return (
            _dummy_fi(),
            None,
            {"file_index_build_ms": 1.0, "code_index_build_ms": 2.0},
        )

    _, _, m1 = c.get_or_build(key, build_no_ci)
    assert m1["index_cache_hit"] is False
    _, _, m2 = c.get_or_build(key, build_no_ci)
    assert m2["index_cache_hit"] is False
    assert calls["n"] == 2


def test_lru_evicts_oldest():
    c = WorkspaceIndexCache(max_keys=2, ttl_sec=0.0)

    def make_key(suffix: str) -> IndexCacheKey:
        return IndexCacheKey(
            canonical_root=f"/tmp/{suffix}",
            snapshot_hash=("aa" + suffix).ljust(64, "0")[:64],
        )

    k1, k2, k3 = make_key("1"), make_key("2"), make_key("3")

    for k in (k1, k2):
        c.get_or_build(
            k,
            lambda k=k: (_dummy_fi(), CodeIndex(), {"file_index_build_ms": 0.0, "code_index_build_ms": 0.0}),
        )
    assert c.entry_count() == 2

    c.get_or_build(
        k3,
        lambda: (_dummy_fi(), CodeIndex(), {"file_index_build_ms": 0.0, "code_index_build_ms": 0.0}),
    )
    assert c.entry_count() == 2

    misses = {"k1": 0}

    def build_k1():
        misses["k1"] += 1
        return (_dummy_fi(), CodeIndex(), {"file_index_build_ms": 1.0, "code_index_build_ms": 1.0})

    c.get_or_build(k1, build_k1)
    assert misses["k1"] == 1


def test_single_flight_one_build():
    c = WorkspaceIndexCache(max_keys=4, ttl_sec=0.0)
    key = IndexCacheKey(
        canonical_root="/tmp/sf",
        snapshot_hash="ef" * 32,
    )
    builds = {"n": 0}
    gate = threading.Event()

    def slow_build():
        builds["n"] += 1
        gate.wait(timeout=5.0)
        time.sleep(0.02)
        return (
            _dummy_fi(),
            CodeIndex(),
            {"file_index_build_ms": 1.0, "code_index_build_ms": 1.0},
        )

    results: list = []

    def worker():
        results.append(c.get_or_build(key, slow_build))

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    time.sleep(0.05)
    gate.set()
    results.append(c.get_or_build(key, slow_build))
    t1.join(timeout=10.0)
    t2.join(timeout=10.0)

    assert builds["n"] == 1
    assert len(results) == 3
    assert sum(1 for _fi, _ci, m in results if m["index_cache_hit"] is False) == 1
    base_fi, base_ci = results[0][0], results[0][1]
    for fi, ci, _m in results:
        assert fi is base_fi and ci is base_ci


def test_workspace_identity_cacheable_dirty():
    from runtime.layer5.workspace.identity import WorkspaceIdentity, WorkspaceRevision

    root = "/tmp/r"
    ident_clean = WorkspaceIdentity(
        canonical_root=root,
        identity_hash=WorkspaceIdentity.compute_identity_hash(root),
        original_input=root,
        path_type="posix",
        revision=WorkspaceRevision(commit_sha="a" * 40, is_dirty=False),
    )
    ident_dirty = WorkspaceIdentity(
        canonical_root=root,
        identity_hash=WorkspaceIdentity.compute_identity_hash(root),
        original_input=root,
        path_type="posix",
        revision=WorkspaceRevision(commit_sha="a" * 40, is_dirty=True),
    )
    assert WorkspaceIndexCache.is_cacheable(ident_clean) is True
    assert WorkspaceIndexCache.is_cacheable(ident_dirty) is False

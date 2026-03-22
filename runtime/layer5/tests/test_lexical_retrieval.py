"""
Golden queries, determinism, and latency smoke for A5 lexical retrieval.
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import pytest

from runtime.layer5.index import WorkspaceFileIndex, build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, normalize_query, retrieve_lexical
from runtime.layer5.workspace.identity import WorkspaceIdentity


def _touch(path: Path, text: str = "", mtime_ns: int = 1_000_000_000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.utime(path, ns=(mtime_ns, mtime_ns))


def _identity_for(root: Path) -> WorkspaceIdentity:
    root_s = str(root.resolve())
    return WorkspaceIdentity(
        canonical_root=root_s,
        identity_hash=WorkspaceIdentity.compute_identity_hash(root_s),
        original_input=root_s,
        path_type="posix",
        is_git_repo=False,
    )


def _index_fixture() -> tuple[tempfile.TemporaryDirectory[str], WorkspaceFileIndex]:
    """Synthetic tree mimicking discoverable Layer-5-ish paths."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _touch(
        root / "runtime" / "layer5" / "workspace" / "resolver.py",
        "class WorkspaceResolver resolves the canonical workspace root for callers.",
    )
    _touch(
        root / "runtime" / "layer5" / "index" / "builder.py",
        "def build_file_index walks the tree and returns WorkspaceFileIndex.",
    )
    _touch(
        root / "runtime" / "layer5" / "workspace" / "path_normalizer.py",
        "PathNormalizer converts windows paths to normalized posix forms.",
    )
    _touch(
        root / "runtime" / "layer5" / "api" / "skeleton.py",
        "Layer5ApiSkeleton serves healthz and workspace resolve endpoints.",
    )
    ident = _identity_for(root)
    idx = build_file_index(ident)
    return tmp, idx


class TestQueryNormalization:
    def test_normalize_query_sorted_and_filtered(self):
        assert normalize_query("Workspace  RESOLVER!") == ("resolver", "workspace")
        assert normalize_query("a b") == ()  # min len 2
        assert normalize_query("") == ()


class TestGoldenQueries:
    @pytest.fixture
    def golden_index(self):
        tmp, idx = _index_fixture()
        yield idx
        tmp.cleanup()

    def test_workspace_resolver_ranks_resolver_py(self, golden_index):
        r = retrieve_lexical(golden_index, "workspace resolver", top_k=3)
        paths = [h.relative_path for h in r.hits]
        assert "runtime/layer5/workspace/resolver.py" in paths
        assert paths[0] == "runtime/layer5/workspace/resolver.py"

    def test_file_index_builder_ranks_builder(self, golden_index):
        r = retrieve_lexical(golden_index, "file index build", top_k=2)
        assert r.hits[0].relative_path == "runtime/layer5/index/builder.py"

    def test_path_normalizer_query(self, golden_index):
        r = retrieve_lexical(golden_index, "path normalizer windows", top_k=2)
        assert r.hits[0].relative_path == "runtime/layer5/workspace/path_normalizer.py"

    def test_breakdown_sums_to_score(self, golden_index):
        r = retrieve_lexical(golden_index, "resolver", top_k=1)
        h = r.hits[0]
        assert h.score == sum(h.breakdown.values())


class TestDeterminism:
    def test_identical_results_across_runs(self):
        tmp, idx = _index_fixture()
        try:
            cfg = LexicalRetrievalConfig(read_file_contents=True)
            a = retrieve_lexical(idx, "workspace resolver", 4, cfg)
            b = retrieve_lexical(idx, "workspace resolver", 4, cfg)
            assert [h.relative_path for h in a.hits] == [h.relative_path for h in b.hits]
            assert [h.score for h in a.hits] == [h.score for h in b.hits]
        finally:
            tmp.cleanup()

    def test_tie_break_by_relative_path(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(root / "z" / "match.txt", "alpha beta gamma repeat repeat")
            _touch(root / "a" / "match.txt", "alpha beta gamma repeat repeat")
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(idx, "repeat gamma", top_k=2)
            paths = [h.relative_path for h in r.hits]
            assert paths == sorted(paths)
            assert paths[0] == "a/match.txt"

    def test_empty_query_returns_first_k_by_path_order(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(root / "b.txt", "x")
            _touch(root / "a.txt", "x")
            ident = _identity_for(root)
            idx = build_file_index(ident)
            r = retrieve_lexical(idx, "   ", top_k=1)
            assert r.hits[0].relative_path == "a.txt"


class TestLexicalRetrievalLatencySmoke:
    """
    Latency snapshot (honest, coarse): on a small tree, repeated retrieval stays cheap.

    Last local run target: well under 100ms total for 40 calls (path+content).
    """

    def test_lexical_retrieval_latency_smoke(self):
        tmp, idx = _index_fixture()
        try:
            cfg = LexicalRetrievalConfig(read_file_contents=True)
            n = 40
            t0 = time.perf_counter()
            for _ in range(n):
                retrieve_lexical(idx, "workspace resolver endpoints", top_k=4, config=cfg)
            elapsed = time.perf_counter() - t0
            per_ms = (elapsed / n) * 1000.0
            assert elapsed < 2.0, f"40 retrievals took {elapsed:.3f}s (~{per_ms:.2f}ms each)"
        finally:
            tmp.cleanup()

"""
A6 evidence bundle: grounding, A5 authority preservation, determinism.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from runtime.layer5.evidence import SnippetConfig, build_evidence_bundle
from runtime.layer5.evidence.identity_policy import IdentityMismatchError
from runtime.layer5.evidence.schema_validate import validate_evidence_bundle_dict
from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, retrieve_lexical
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


def _fixture_index_and_retrieval():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _touch(
        root / "runtime" / "layer5" / "workspace" / "resolver.py",
        "class WorkspaceResolver resolves the canonical workspace root for callers.\n"
        "def other():\n    pass\n",
    )
    _touch(root / "runtime" / "layer5" / "index" / "builder.py", "def build_file_index():\n    pass\n")
    ident = _identity_for(root)
    idx = build_file_index(ident)
    r = retrieve_lexical(
        idx,
        "workspace resolver",
        top_k=2,
        config=LexicalRetrievalConfig(),
    )
    return tmp, idx, r


class TestEvidenceBundle:
    def test_preserves_a5_order_and_scores(self):
        tmp, idx, r = _fixture_index_and_retrieval()
        try:
            bundle = build_evidence_bundle(r, idx)
            validate_evidence_bundle_dict(json.loads(bundle.to_json()))
            assert len(bundle.entries) == len(r.hits)
            for i, (e, h) in enumerate(zip(bundle.entries, r.hits)):
                assert e.rank == i
                assert e.relative_path == h.relative_path
                assert e.retrieval_score == h.score
                assert e.retrieval_breakdown == h.breakdown
        finally:
            tmp.cleanup()

    def test_snippet_anchors_on_first_token_line(self):
        tmp, idx, r = _fixture_index_and_retrieval()
        try:
            bundle = build_evidence_bundle(r, idx, snippet_config=SnippetConfig(context_lines_before=0, context_lines_after=0))
            top = bundle.entries[0]
            assert "WorkspaceResolver" in top.snippet_text or "workspace" in top.snippet_text.lower()
            assert top.snippet_selection_reason == "query_token_substring_anchor"
            assert top.anchor_line >= 1
        finally:
            tmp.cleanup()

    def test_deterministic_json(self):
        tmp, idx, r = _fixture_index_and_retrieval()
        try:
            b1 = build_evidence_bundle(r, idx)
            b2 = build_evidence_bundle(r, idx)
            assert b1.to_json() == b2.to_json()
        finally:
            tmp.cleanup()

    def test_identity_mismatch_raises(self):
        tmp, idx, r = _fixture_index_and_retrieval()
        try:
            bad = SimpleNamespace(
                schema_version=idx.schema_version,
                workspace_identity_hash="f" * 64,
                canonical_root=idx.canonical_root,
                files=idx.files,
            )
            with pytest.raises(IdentityMismatchError) as ei:
                build_evidence_bundle(r, bad, require_identity_match=True)
            assert "layer5.evidence.identity_mismatch" in str(ei.value)
        finally:
            tmp.cleanup()

    def test_missing_file_grounding(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(root / "gone.txt", "hello")
            ident = _identity_for(root)
            idx = build_file_index(ident)
            os.remove(root / "gone.txt")
            r = retrieve_lexical(idx, "hello", top_k=1, config=LexicalRetrievalConfig())
            bundle = build_evidence_bundle(r, idx)
            assert bundle.entries[0].snippet_selection_reason == "file_missing"
            assert bundle.entries[0].snippet_text == ""

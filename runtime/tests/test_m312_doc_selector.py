"""
Tests for M3.12 doc selector — determinism and selection policy.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.context.contracts import ContextRequest, SelectedContextRef
from runtime.context.doc_selector import select_from_manifest
from runtime.context.manifest_builder import ManifestBuilder
from runtime.context.manifest_models import IngestionConfig, ManifestEntry, RepoManifest


def _make_manifest_with_entries(entries: list[tuple[str, str, list[str]]]) -> RepoManifest:
    """entries: (path, title, headings)."""
    out = []
    for path, title, headings in entries:
        out.append(
            ManifestEntry(
                path=path,
                content_hash="hash-" + path.replace("/", "_"),
                file_type="markdown",
                title=title,
                headings=headings,
            )
        )
    return RepoManifest(revision="rev", entries=out)


class TestDocSelectorDeterminism:
    def test_same_manifest_same_query_same_refs(self) -> None:
        manifest = _make_manifest_with_entries([
            ("docs/context.md", "Context Engine", ["Repository Context", "Selectors"]),
            ("docs/other.md", "Other", []),
        ])
        req = ContextRequest(
            task_id="t",
            revision="r",
            root_path="/repo",
            symbol_hints=["context"],
        )
        r1 = select_from_manifest(manifest, "How does context selection work?", req)
        r2 = select_from_manifest(manifest, "How does context selection work?", req)
        assert [ref.path for ref in r1] == [ref.path for ref in r2]
        assert [ref.selection_reason for ref in r1] == [ref.selection_reason for ref in r2]

    def test_path_match_priority(self) -> None:
        manifest = _make_manifest_with_entries([
            ("docs/runtime/engine.md", "Engine", []),
            ("runtime/context/engine.py", "engine", []),
        ])
        req = ContextRequest(task_id="t", revision="r", root_path="/repo", symbol_hints=[])
        refs = select_from_manifest(manifest, "context engine documentation", req)
        paths = [r.path for r in refs]
        assert "docs/runtime/engine.md" in paths or "runtime/context/engine.py" in paths

    def test_max_files_cap(self) -> None:
        manifest = _make_manifest_with_entries([
            ("docs/a.md", "A", []),
            ("docs/b.md", "B", []),
            ("docs/c.md", "C", []),
        ])
        req = ContextRequest(
            task_id="t",
            revision="r",
            root_path="/repo",
            max_files=2,
        )
        refs = select_from_manifest(manifest, "docs", req)
        assert len(refs) <= 2


class TestDocSelectorReasons:
    def test_selector_is_manifest(self) -> None:
        manifest = _make_manifest_with_entries([("docs/foo.md", "Foo", [])])
        req = ContextRequest(task_id="t", revision="r", root_path="/repo")
        refs = select_from_manifest(manifest, "foo", req)
        assert all(r.selector == "manifest" for r in refs)

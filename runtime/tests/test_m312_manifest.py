"""
Tests for M3.12 manifest builder — determinism and structure.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.context.manifest_builder import ManifestBuilder
from runtime.context.manifest_models import IngestionConfig, RepoManifest


def _write(tmp_path: Path, rel: str, content: str) -> None:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


class TestManifestDeterminism:
    def test_same_config_same_revision_same_manifest(self, tmp_path: Path) -> None:
        _write(tmp_path, "docs/foo.md", "# Hello\n\nBar.")
        _write(tmp_path, "README.md", "Root readme")
        config = IngestionConfig(path_patterns=["docs/*.md", "README.md"])
        builder = ManifestBuilder()
        m1 = builder.build(str(tmp_path), "rev1", config)
        m2 = builder.build(str(tmp_path), "rev1", config)
        assert m1.revision == m2.revision
        assert [e.path for e in m1.entries] == [e.path for e in m2.entries]
        assert [e.content_hash for e in m1.entries] == [e.content_hash for e in m2.entries]

    def test_different_revision_same_entries(self, tmp_path: Path) -> None:
        _write(tmp_path, "README.md", "Same content")
        config = IngestionConfig(path_patterns=["README.md"])
        builder = ManifestBuilder()
        m1 = builder.build(str(tmp_path), "rev1", config)
        m2 = builder.build(str(tmp_path), "rev2", config)
        assert m1.revision != m2.revision
        assert [e.path for e in m1.entries] == [e.path for e in m2.entries]
        assert m1.entries[0].content_hash == m2.entries[0].content_hash

    def test_entry_order_lexicographic(self, tmp_path: Path) -> None:
        _write(tmp_path, "docs/b.md", "B")
        _write(tmp_path, "docs/a.md", "A")
        config = IngestionConfig(path_patterns=["docs/*.md"])
        builder = ManifestBuilder()
        m = builder.build(str(tmp_path), "r", config)
        paths = [e.path for e in m.entries]
        assert paths == sorted(paths)


class TestManifestContent:
    def test_markdown_headings_extracted(self, tmp_path: Path) -> None:
        _write(tmp_path, "docs/t.md", "# Title\n\n## Section 1\n\nText.")
        config = IngestionConfig(path_patterns=["docs/*.md"])
        m = ManifestBuilder().build(str(tmp_path), "r", config)
        assert len(m.entries) == 1
        e = m.entries[0]
        assert e.file_type == "markdown"
        assert e.title == "Title"
        assert "Section 1" in e.headings

    def test_python_symbol_anchors(self, tmp_path: Path) -> None:
        _write(tmp_path, "runtime/context/foo.py", "def bar():\n    pass\nclass Baz:\n    pass")
        config = IngestionConfig(path_patterns=["runtime/context/*.py"])
        m = ManifestBuilder().build(str(tmp_path), "r", config)
        assert len(m.entries) == 1
        e = m.entries[0]
        assert e.file_type == "python"
        assert any("bar" in a for a in e.symbol_anchors)
        assert any("Baz" in a for a in e.symbol_anchors)

    def test_repo_manifest_no_wall_clock(self) -> None:
        """RepoManifest must not include built_at_utc in identity-bearing structure."""
        m = RepoManifest(revision="r", entries=[])
        assert hasattr(m, "revision")
        assert hasattr(m, "entries")
        assert not hasattr(m, "built_at_utc")


class TestManifestBuilderValidation:
    def test_missing_root_raises(self) -> None:
        builder = ManifestBuilder()
        with pytest.raises(ValueError, match="root_path"):
            builder.build("/nonexistent/path", "r", IngestionConfig(path_patterns=["README.md"]))

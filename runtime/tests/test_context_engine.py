"""
Tests for M3.0 Repository Context Engine.

Validates determinism, caps, fail-closed behavior, symbol hints, and provenance.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from runtime.context.contracts import ContextRequest
from runtime.context.engine import ContextEngine, ContextEngineError, MissingExplicitFilesError


def _write(tmp_root: Path, rel: str, content: str) -> Path:
    p = tmp_root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
    return p


def _make_request(
    root: Path,
    *,
    files: list[str] | None = None,
    symbol_hints: list[str] | None = None,
    max_files: int = 50,
    max_bytes: int = 512_000,
    selectors: list[str] | None = None,
) -> ContextRequest:
    return ContextRequest(
        task_id="task-ctx",
        revision="rev-123",
        root_path=str(root),
        files=files or [],
        symbol_hints=symbol_hints or [],
        max_files=max_files,
        max_bytes=max_bytes,
        selectors=selectors or ["direct", "siblings", "imports", "symbols"],
    )


class TestContextEngineDeterminism:
    def test_same_request_same_revision_same_bundle_ordering(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        _write(root, "a.py", "print('a')\n")
        _write(root, "b.py", "print('b')\n")
        _write(root, "c.txt", "hello\n")

        engine = ContextEngine()
        req = _make_request(root, files=["a.py", "c.txt"], selectors=["direct"])

        bundle1 = engine.build_context_bundle(req)
        bundle2 = engine.build_context_bundle(req)

        paths1 = [i.path for i in bundle1.items]
        paths2 = [i.path for i in bundle2.items]
        reasons1 = [i.selection_reason for i in bundle1.items]
        reasons2 = [i.selection_reason for i in bundle2.items]

        assert paths1 == paths2
        assert reasons1 == reasons2


class TestContextEngineCaps:
    def test_max_files_enforced(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        _write(root, "a.py", "print('a')\n")
        _write(root, "b.py", "print('b')\n")
        _write(root, "c.py", "print('c')\n")

        engine = ContextEngine()
        req = _make_request(root, files=["a.py", "b.py", "c.py"], max_files=2, selectors=["direct"])

        bundle = engine.build_context_bundle(req)
        assert len(bundle.items) == 2
        assert bundle.limits.truncated is True

    def test_max_bytes_enforced(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        _write(root, "a.py", "x" * 100)
        _write(root, "b.py", "y" * 100)

        engine = ContextEngine()
        # Max bytes set so only one file fits.
        req = _make_request(root, files=["a.py", "b.py"], max_bytes=150, selectors=["direct"])

        bundle = engine.build_context_bundle(req)
        assert len(bundle.items) == 1
        assert bundle.limits.truncated is True


class TestContextEngineFailures:
    def test_missing_files_fail_closed(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        _write(root, "a.py", "print('a')\n")

        engine = ContextEngine()
        req = _make_request(root, files=["a.py", "missing.py"], selectors=["direct"])

        with pytest.raises(MissingExplicitFilesError):
            engine.build_context_bundle(req)


class TestContextEngineSymbols:
    def test_symbol_hints_deterministic(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        _write(root, "a.py", "def foo():\n    pass\n")
        _write(root, "b.py", "def bar():\n    pass\n")

        engine = ContextEngine()
        req = _make_request(root, symbol_hints=["foo"], selectors=["symbols"])

        bundle1 = engine.build_context_bundle(req)
        bundle2 = engine.build_context_bundle(req)

        assert len(bundle1.items) == 1
        assert len(bundle2.items) == 1
        assert bundle1.items[0].path == "a.py"
        assert bundle2.items[0].path == "a.py"
        assert bundle1.items[0].selection_reason == bundle2.items[0].selection_reason

    def test_symbol_hint_case_insensitive(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        _write(root, "handler.py", "def processFiles():\n    pass\n")

        engine = ContextEngine()
        req = _make_request(root, symbol_hints=["processfiles"], selectors=["symbols"])

        bundle = engine.build_context_bundle(req)

        assert len(bundle.items) == 1
        assert bundle.items[0].path == "handler.py"
        assert "processfiles" in bundle.items[0].selection_reason.lower()


class TestContextEngineProvenance:
    def test_provenance_fields_present(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        _write(root, "a.py", "print('a')\n")

        engine = ContextEngine()
        req = _make_request(root, files=["a.py"], symbol_hints=["foo"])

        bundle = engine.build_context_bundle(req)

        assert bundle.provenance.root_path == str((root).resolve())
        assert bundle.provenance.requested_files == ["a.py"]
        assert bundle.provenance.symbol_hints == ["foo"]
        # Selectors that actually contributed refs (direct added a.py; symbols find no "foo" in a.py).
        assert bundle.provenance.selectors == ["direct"]

        # Do not assert on created_at_utc value; only check that it is non-empty.
        assert bundle.created_at_utc

    def test_provenance_selectors_contributed_only(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        _write(root, "a.py", "def foo():\n    pass\n")

        engine = ContextEngine()
        req = _make_request(root, symbol_hints=["foo"], selectors=["symbols"])

        bundle = engine.build_context_bundle(req)

        assert len(bundle.items) == 1
        assert bundle.items[0].path == "a.py"
        assert bundle.provenance.selectors == ["symbols"]

    def test_provenance_empty_when_no_refs(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        _write(root, "a.py", "x = 1\n")  # no "nonexistentsymbol" anywhere

        engine = ContextEngine()
        req = _make_request(root, symbol_hints=["nonexistentsymbol"], selectors=["symbols"])

        bundle = engine.build_context_bundle(req)

        assert len(bundle.items) == 0
        assert bundle.provenance.selectors == []


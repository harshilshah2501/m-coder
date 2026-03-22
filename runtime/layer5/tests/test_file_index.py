"""
Determinism and lifecycle tests for A4 file index (MVP).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from runtime.layer5.index import (
    FileIndexConfig,
    build_file_index,
    index_matches_workspace,
)
from runtime.layer5.workspace.identity import WorkspaceIdentity


def _touch(path: Path, mtime_ns: int = 1_000_000_000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")
    ts = mtime_ns / 1_000_000_000
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


class TestDeterministicFileIndex:
    def test_repeated_builds_identical_canonical_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "b" / "z.txt", mtime_ns=5_000_000_000)
            _touch(root / "a.txt", mtime_ns=3_000_000_000)
            ident = _identity_for(root)
            idx1 = build_file_index(ident)
            idx2 = build_file_index(ident)
            assert idx1.canonical_json() == idx2.canonical_json()

    def test_files_sorted_by_relative_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "zzz.txt", mtime_ns=1_000_000_000)
            _touch(root / "aaa.txt", mtime_ns=1_000_000_000)
            ident = _identity_for(root)
            idx = build_file_index(ident)
            paths = [e.relative_path for e in idx.files]
            assert paths == ["aaa.txt", "zzz.txt"]

    def test_excludes_configured_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "keep.txt", mtime_ns=1)
            _touch(root / ".git" / "config", mtime_ns=1)
            _touch(root / "node_modules" / "x.js", mtime_ns=1)
            ident = _identity_for(root)
            idx = build_file_index(ident)
            assert [e.relative_path for e in idx.files] == ["keep.txt"]

    def test_skips_symlinks_to_files_when_not_following(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "real.txt", mtime_ns=1)
            try:
                (root / "link.txt").symlink_to(root / "real.txt")
            except OSError:
                pytest.skip("symlink creation not supported")
            ident = _identity_for(root)
            idx = build_file_index(ident)
            assert [e.relative_path for e in idx.files] == ["real.txt"]

    def test_raises_when_root_missing(self):
        ident = WorkspaceIdentity(
            canonical_root="/nonexistent/path/that/does/not/exist",
            identity_hash=WorkspaceIdentity.compute_identity_hash(
                "/nonexistent/path/that/does/not/exist"
            ),
            original_input="x",
            path_type="posix",
            is_git_repo=False,
        )
        with pytest.raises(FileNotFoundError):
            build_file_index(ident)


class TestIndexWorkspaceMatch:
    def test_index_matches_workspace_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "f.txt", mtime_ns=1)
            ident = _identity_for(root)
            idx = build_file_index(ident)
            assert index_matches_workspace(idx, ident) is True

    def test_index_matches_workspace_false_on_hash_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "f.txt", mtime_ns=1)
            ident = _identity_for(root)
            idx = build_file_index(ident)
            other = WorkspaceIdentity(
                canonical_root=ident.canonical_root,
                identity_hash="0" * 64,
                original_input=ident.original_input,
                path_type=ident.path_type,
                is_git_repo=False,
            )
            assert index_matches_workspace(idx, other) is False


class TestLifecycleFullRebuild:
    def test_second_build_reflects_new_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "a.txt", mtime_ns=1)
            ident = _identity_for(root)
            first = build_file_index(ident)
            _touch(root / "b.txt", mtime_ns=2)
            second = build_file_index(ident)
            assert len(second.files) == len(first.files) + 1
            assert first.canonical_json() != second.canonical_json()


class TestCustomConfig:
    def test_custom_exclude_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "ok.txt", mtime_ns=1)
            _touch(root / "vendor" / "lib.c", mtime_ns=1)
            ident = _identity_for(root)
            cfg = FileIndexConfig(
                exclude_dir_names=frozenset({".git", "vendor"}),
            )
            idx = build_file_index(ident, cfg)
            assert [e.relative_path for e in idx.files] == ["ok.txt"]

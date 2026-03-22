"""
Build a deterministic file-level index inside the A2-resolved workspace root.

Lifecycle (MVP)
---------------
- **Initial build**: ``build_file_index(identity, config)`` walks
  ``identity.canonical_root`` and returns a ``WorkspaceFileIndex``.
- **Update**: Full rebuild only — call ``build_file_index`` again with the same
  or updated ``WorkspaceIdentity``. There is no incremental diff in this MVP.
- **Invalidate**: When ``identity_hash`` or ``canonical_root`` changes, or when
  disk content changes, consumers should treat the previous index as stale and
  rebuild. Use ``index_matches_workspace`` for a cheap identity match; file-level
  staleness requires comparing ``canonical_json()`` or fingerprints to a fresh build.

Determinism
-----------
- Traversal prunes excluded directory names; remaining ``dirnames`` and file
  names are sorted lexicographically (Unicode, default str order).
- ``files`` in the result are sorted by ``relative_path``.
- ``relative_path`` uses POSIX separators relative to the resolved root.
- ``canonical_json()`` omits wall-clock timestamps so repeated runs over an
  unchanged tree yield byte-identical JSON.

Scope
-----
- Indexes regular files only (skips directories, symlinks, sockets, etc.).
- Operates only under ``identity.canonical_root`` (via bounded ``os.walk``).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from runtime.layer5.workspace.identity import WorkspaceIdentity

from runtime.layer5.index.config import FileIndexConfig
from runtime.layer5.index.models import SCHEMA_VERSION, FileIndexEntry, WorkspaceFileIndex


def _mtime_ns(st: os.stat_result) -> int:
    ns = getattr(st, "st_mtime_ns", None)
    if ns is not None:
        return int(ns)
    return int(st.st_mtime * 1_000_000_000)


def build_file_index(
    identity: WorkspaceIdentity,
    config: Optional[FileIndexConfig] = None,
) -> WorkspaceFileIndex:
    """
    Full index build over ``identity.canonical_root``.

    Raises:
        FileNotFoundError: Root path does not exist.
        NotADirectoryError: Root is not a directory.
    """
    cfg = config or FileIndexConfig()
    root = Path(identity.canonical_root).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Workspace root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Workspace root is not a directory: {root}")

    exclude_lower = {name.lower() for name in cfg.exclude_dir_names}
    collected: List[FileIndexEntry] = []

    for dirpath, dirnames, filenames in os.walk(
        root,
        topdown=True,
        followlinks=cfg.follow_symlinks,
    ):
        dirnames[:] = [d for d in sorted(dirnames, key=lambda x: x) if d.lower() not in exclude_lower]
        for name in sorted(filenames, key=lambda x: x):
            full = Path(dirpath) / name
            try:
                if full.is_symlink() and not cfg.follow_symlinks:
                    continue
                if not full.is_file():
                    continue
                st = full.stat()
            except (OSError, PermissionError):
                continue
            rel = full.relative_to(root).as_posix()
            collected.append(
                FileIndexEntry(
                    relative_path=rel,
                    size_bytes=int(st.st_size),
                    mtime_ns=_mtime_ns(st),
                )
            )

    collected.sort(key=lambda e: e.relative_path)
    return WorkspaceFileIndex(
        schema_version=SCHEMA_VERSION,
        workspace_identity_hash=identity.identity_hash,
        canonical_root=str(root),
        files=tuple(collected),
    )


def index_matches_workspace(index: WorkspaceFileIndex, identity: WorkspaceIdentity) -> bool:
    """True if index was built for the same canonical root hash as ``identity``."""
    return (
        index.workspace_identity_hash == identity.identity_hash
        and index.canonical_root == str(Path(identity.canonical_root).resolve())
    )

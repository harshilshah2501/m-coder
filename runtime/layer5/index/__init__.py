"""
A4 — Deterministic file-level workspace index (MVP).

Indexes only paths under ``WorkspaceIdentity.canonical_root`` from A2.
See package docstring in ``builder`` for lifecycle and determinism guarantees.
"""

from runtime.layer5.index.builder import build_file_index, index_matches_workspace
from runtime.layer5.index.config import FileIndexConfig
from runtime.layer5.index.models import FileIndexEntry, WorkspaceFileIndex

__all__ = [
    "FileIndexConfig",
    "FileIndexEntry",
    "WorkspaceFileIndex",
    "build_file_index",
    "index_matches_workspace",
]

"""
In-memory index model with explicit, stable serialization for A5.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


# Bump when breaking the deterministic JSON shape consumed by A5.
SCHEMA_VERSION = "layer5.file_index.v1"


@dataclass(frozen=True)
class FileIndexEntry:
    """One indexed file under the workspace root (file-level granularity)."""

    relative_path: str
    size_bytes: int
    mtime_ns: int

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "size_bytes": self.size_bytes,
            "mtime_ns": self.mtime_ns,
        }


@dataclass(frozen=True)
class WorkspaceFileIndex:
    """
    Complete file-level index for one resolved workspace.

    ``symbols`` is intentionally absent in v1 (optional symbol index not implemented).
    """

    schema_version: str
    workspace_identity_hash: str
    canonical_root: str
    files: Tuple[FileIndexEntry, ...]
    workspace_snapshot_hash: str = ""
    workspace_snapshot_source: str = "path_only"
    workspace_is_dirty: bool = False
    workspace_commit_sha: str = ""

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Deterministic payload: same tree on disk -> same structure (ordering fixed)."""
        return {
            "schema_version": self.schema_version,
            "workspace_identity_hash": self.workspace_identity_hash,
            "canonical_root": self.canonical_root,
            "workspace_snapshot_hash": self.workspace_snapshot_hash,
            "workspace_snapshot_source": self.workspace_snapshot_source,
            "workspace_is_dirty": self.workspace_is_dirty,
            "workspace_commit_sha": self.workspace_commit_sha,
            "files": [e.to_canonical_dict() for e in self.files],
        }

    def canonical_json(self) -> str:
        """Stable JSON string for equality checks and content hashing across runs."""
        return json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(",", ":"))

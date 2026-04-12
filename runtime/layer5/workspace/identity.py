"""
Workspace identity and revision metadata contracts.

Defines the canonical shapes for:
- WorkspaceIdentity: unique workspace identification
- WorkspaceRevision: revision/branch/dirty-state metadata
- WorkspaceError: error model for invalid/unresolved workspace cases

These contracts are stable for A4 (indexing) to build upon.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any


class WorkspaceErrorCode(Enum):
    """Error codes for workspace resolution failures."""

    WORKSPACE_NOT_FOUND = "workspace_not_found"
    PATH_OUTSIDE_WORKSPACE = "path_outside_workspace"
    INVALID_PATH_FORMAT = "invalid_path_format"
    NORMALIZATION_FAILED = "normalization_failed"
    GIT_NOT_INITIALIZED = "git_not_initialized"
    REVISION_UNAVAILABLE = "revision_unavailable"
    AMBIGUOUS_ROOT = "ambiguous_root"
    PERMISSION_DENIED = "permission_denied"


@dataclass
class WorkspaceError:
    """
    Error model for workspace resolution failures.

    Provides structured error information for callers to handle appropriately.
    """

    code: WorkspaceErrorCode
    message: str
    input_path: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for API responses."""
        result = {
            "code": self.code.value,
            "message": self.message,
        }
        if self.input_path:
            result["input_path"] = self.input_path
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class WorkspaceRevision:
    """
    Revision metadata for a workspace.

    Captures git branch, commit SHA, and dirty state.
    This shape is stable for A4 (indexing) to consume.

    Attributes:
        commit_sha: Full 40-character git commit SHA, or "unversioned" if not a git repo.
        branch: Current branch name, or None if detached HEAD or no git.
        is_dirty: True if working tree has uncommitted changes.
        is_detached: True if HEAD is detached (not on any branch).
        tags: List of tags pointing to current commit.
        timestamp_utc: ISO-8601 UTC timestamp when revision info was captured.
    """

    commit_sha: str
    branch: Optional[str] = None
    is_dirty: bool = False
    is_detached: bool = False
    tags: List[str] = field(default_factory=list)
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def unversioned(cls) -> "WorkspaceRevision":
        """Create a revision object for non-git workspaces."""
        return cls(
            commit_sha="unversioned",
            branch=None,
            is_dirty=False,
            is_detached=False,
            tags=[],
        )

    def short_sha(self, length: int = 7) -> str:
        """Return shortened commit SHA."""
        if self.commit_sha == "unversioned":
            return "unversioned"
        return self.commit_sha[:length]

    def is_versioned(self) -> bool:
        """Check if workspace is under version control."""
        return self.commit_sha != "unversioned"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "commit_sha": self.commit_sha,
            "branch": self.branch,
            "is_dirty": self.is_dirty,
            "is_detached": self.is_detached,
            "tags": self.tags,
            "timestamp_utc": self.timestamp_utc,
        }


@dataclass
class WorkspaceIdentity:
    """
    Canonical workspace identity.

    Provides deterministic identification for a workspace root, independent of
    path representation (Windows, WSL, POSIX).

    Attributes:
        canonical_root: Normalized POSIX-style workspace root path (always forward slashes).
                       For WSL: /mnt/c/Users/... or /home/user/...
                       For Windows: converted to /mnt/c/... equivalent.
        identity_hash: SHA-256 hash of canonical_root for stable identification.
        original_input: The original input path before normalization.
        path_type: The detected path type ('windows', 'wsl', 'posix', 'unknown').
        revision: Git revision metadata, if available.
        resolved_at_utc: ISO-8601 UTC timestamp of resolution.
        is_git_repo: Whether the workspace root contains a .git directory.
    """

    canonical_root: str
    identity_hash: str
    original_input: str
    path_type: str
    revision: Optional[WorkspaceRevision] = None
    resolved_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_git_repo: bool = False
    snapshot_hash: str = ""
    snapshot_source: str = "path_only"
    snapshot_dirty: bool = False

    @classmethod
    def compute_identity_hash(cls, canonical_root: str) -> str:
        """
        Compute SHA-256 identity hash for a canonical root path.

        The hash is derived from the lowercased canonical root to ensure
        case-insensitive identity matching (important for Windows paths).
        """
        normalized = canonical_root.lower().rstrip("/")
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @classmethod
    def compute_snapshot_hash(cls, snapshot_descriptor: str) -> str:
        """Compute SHA-256 hash for a deterministic workspace snapshot descriptor."""
        return hashlib.sha256(snapshot_descriptor.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for API responses."""
        result = {
            "canonical_root": self.canonical_root,
            "identity_hash": self.identity_hash,
            "snapshot_hash": self.snapshot_hash,
            "snapshot_source": self.snapshot_source,
            "snapshot_dirty": self.snapshot_dirty,
            "original_input": self.original_input,
            "path_type": self.path_type,
            "resolved_at_utc": self.resolved_at_utc,
            "is_git_repo": self.is_git_repo,
        }
        if self.revision:
            result["revision"] = self.revision.to_dict()
        return result

    def short_identity(self, length: int = 12) -> str:
        """Return shortened identity hash for display."""
        return self.identity_hash[:length]

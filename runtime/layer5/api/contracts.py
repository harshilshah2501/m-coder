"""
Local API contract definitions.

These dataclasses define the request/response shapes for the Layer-5 local API.
They are stable contracts that:
- Plugin/IDE clients can depend on
- A4 (indexing) can implement against
- A5 (retrieval) can extend

Schema versioning: All contracts include schema_version for forward compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any


# =============================================================================
# Health Check
# =============================================================================


@dataclass
class HealthResponse:
    """
    Health check response.

    Endpoints: GET /healthz, GET /health
    """

    schema_version: str = "health.v1"
    status: str = "ok"  # "ok", "degraded", "unhealthy"
    version: str = "0.1.0"
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    components: Dict[str, str] = field(default_factory=dict)  # component -> status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "version": self.version,
            "timestamp_utc": self.timestamp_utc,
            "components": self.components,
        }


# =============================================================================
# Workspace Resolution
# =============================================================================


@dataclass
class WorkspaceResolveRequest:
    """
    Request to resolve workspace identity.

    Endpoint: POST /v1/workspace/resolve
    """

    schema_version: str = "workspace_resolve_request.v1"
    input_path: str = ""  # Path in any format (Windows, WSL, POSIX)
    require_git: bool = False  # Require workspace to be a git repository
    include_revision: bool = True  # Include git revision metadata

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkspaceResolveRequest":
        return cls(
            schema_version=data.get("schema_version", "workspace_resolve_request.v1"),
            input_path=data.get("input_path", ""),
            require_git=data.get("require_git", False),
            include_revision=data.get("include_revision", True),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "input_path": self.input_path,
            "require_git": self.require_git,
            "include_revision": self.include_revision,
        }


@dataclass
class WorkspaceResolveResponse:
    """
    Response from workspace resolution.

    Success response includes canonical workspace identity.
    Error response includes error code and message.
    """

    schema_version: str = "workspace_resolve_response.v1"
    success: bool = False
    canonical_root: Optional[str] = None
    identity_hash: Optional[str] = None
    path_type: Optional[str] = None
    is_git_repo: bool = False
    revision: Optional[Dict[str, Any]] = None  # WorkspaceRevision.to_dict()
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    resolved_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "success": self.success,
            "resolved_at_utc": self.resolved_at_utc,
        }

        if self.success:
            result["canonical_root"] = self.canonical_root
            result["identity_hash"] = self.identity_hash
            result["path_type"] = self.path_type
            result["is_git_repo"] = self.is_git_repo
            if self.revision:
                result["revision"] = self.revision
        else:
            result["error_code"] = self.error_code
            result["error_message"] = self.error_message

        return result

    @classmethod
    def from_identity(cls, identity) -> "WorkspaceResolveResponse":
        """Create success response from WorkspaceIdentity."""
        return cls(
            success=True,
            canonical_root=identity.canonical_root,
            identity_hash=identity.identity_hash,
            path_type=identity.path_type,
            is_git_repo=identity.is_git_repo,
            revision=identity.revision.to_dict() if identity.revision else None,
            resolved_at_utc=identity.resolved_at_utc,
        )

    @classmethod
    def from_error(cls, error) -> "WorkspaceResolveResponse":
        """Create error response from WorkspaceError."""
        return cls(
            success=False,
            error_code=error.code.value,
            error_message=error.message,
        )


# =============================================================================
# Index Status
# =============================================================================


class IndexState(Enum):
    """Possible states for workspace index."""

    NOT_INDEXED = "not_indexed"  # Workspace has never been indexed
    INDEXING = "indexing"  # Indexing currently in progress
    INDEXED = "indexed"  # Index is complete and up-to-date
    STALE = "stale"  # Index exists but is out of date
    FAILED = "failed"  # Last indexing attempt failed
    UNKNOWN = "unknown"  # State cannot be determined


@dataclass
class IndexStatusRequest:
    """
    Request to check index status for a workspace.

    Endpoint: POST /v1/index/status
    """

    schema_version: str = "index_status_request.v1"
    workspace_identity_hash: str = ""  # Hash from workspace resolution
    canonical_root: Optional[str] = None  # Alternative: use canonical root directly

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IndexStatusRequest":
        return cls(
            schema_version=data.get("schema_version", "index_status_request.v1"),
            workspace_identity_hash=data.get("workspace_identity_hash", ""),
            canonical_root=data.get("canonical_root"),
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "workspace_identity_hash": self.workspace_identity_hash,
        }
        if self.canonical_root:
            result["canonical_root"] = self.canonical_root
        return result


@dataclass
class IndexStatusResponse:
    """
    Response with index status for a workspace.

    A4 (indexing) implements the actual status tracking.
    This contract defines what the response shape must be.
    """

    schema_version: str = "index_status_response.v1"
    workspace_identity_hash: str = ""
    state: IndexState = IndexState.UNKNOWN
    indexed_revision: Optional[str] = None  # Commit SHA when last indexed
    current_revision: Optional[str] = None  # Current commit SHA
    indexed_at_utc: Optional[str] = None  # When indexing completed
    file_count: int = 0
    error_message: Optional[str] = None  # If state is FAILED
    progress_percent: Optional[float] = None  # If state is INDEXING (0-100)
    checked_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "workspace_identity_hash": self.workspace_identity_hash,
            "state": self.state.value,
            "file_count": self.file_count,
            "checked_at_utc": self.checked_at_utc,
        }

        if self.indexed_revision:
            result["indexed_revision"] = self.indexed_revision
        if self.current_revision:
            result["current_revision"] = self.current_revision
        if self.indexed_at_utc:
            result["indexed_at_utc"] = self.indexed_at_utc
        if self.error_message:
            result["error_message"] = self.error_message
        if self.progress_percent is not None:
            result["progress_percent"] = self.progress_percent

        return result

    def is_ready(self) -> bool:
        """Check if index is ready for queries."""
        return self.state == IndexState.INDEXED

    def needs_reindex(self) -> bool:
        """Check if index needs updating."""
        return self.state in (IndexState.STALE, IndexState.NOT_INDEXED, IndexState.FAILED)

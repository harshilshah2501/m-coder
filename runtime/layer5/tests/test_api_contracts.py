"""
Tests for API contract definitions.

Validates request/response serialization and schema stability.
"""

import pytest
from datetime import datetime, timezone

from runtime.layer5.api.contracts import (
    HealthResponse,
    WorkspaceResolveRequest,
    WorkspaceResolveResponse,
    IndexStatusRequest,
    IndexStatusResponse,
    IndexState,
)


class TestHealthResponse:
    """Test HealthResponse contract."""

    def test_default_values(self):
        response = HealthResponse()
        assert response.schema_version == "health.v1"
        assert response.status == "ok"
        assert response.version == "0.1.0"

    def test_to_dict(self):
        response = HealthResponse(
            status="degraded",
            version="1.0.0",
            components={"resolver": "ok", "index": "degraded"},
        )
        d = response.to_dict()
        assert d["schema_version"] == "health.v1"
        assert d["status"] == "degraded"
        assert d["components"]["resolver"] == "ok"

    def test_timestamp_present(self):
        response = HealthResponse()
        d = response.to_dict()
        assert "timestamp_utc" in d
        # Should be valid ISO format
        datetime.fromisoformat(d["timestamp_utc"].replace("Z", "+00:00"))


class TestWorkspaceResolveRequest:
    """Test WorkspaceResolveRequest contract."""

    def test_from_dict(self):
        data = {
            "input_path": "C:\\Users\\dev\\project",
            "require_git": True,
            "include_revision": False,
        }
        request = WorkspaceResolveRequest.from_dict(data)
        assert request.input_path == "C:\\Users\\dev\\project"
        assert request.require_git is True
        assert request.include_revision is False

    def test_from_dict_defaults(self):
        data = {"input_path": "/home/user/project"}
        request = WorkspaceResolveRequest.from_dict(data)
        assert request.require_git is False
        assert request.include_revision is True

    def test_to_dict(self):
        request = WorkspaceResolveRequest(
            input_path="/mnt/c/project",
            require_git=True,
        )
        d = request.to_dict()
        assert d["schema_version"] == "workspace_resolve_request.v1"
        assert d["input_path"] == "/mnt/c/project"
        assert d["require_git"] is True

    def test_roundtrip(self):
        original = WorkspaceResolveRequest(
            input_path="C:\\Users\\dev\\project",
            require_git=True,
            include_revision=False,
        )
        d = original.to_dict()
        restored = WorkspaceResolveRequest.from_dict(d)
        assert restored.input_path == original.input_path
        assert restored.require_git == original.require_git
        assert restored.include_revision == original.include_revision


class TestWorkspaceResolveResponse:
    """Test WorkspaceResolveResponse contract."""

    def test_success_response(self):
        response = WorkspaceResolveResponse(
            success=True,
            canonical_root="/mnt/c/Users/dev/project",
            identity_hash="a" * 64,
            path_type="windows",
            is_git_repo=True,
            revision={"commit_sha": "abc123", "branch": "main"},
        )
        d = response.to_dict()
        assert d["success"] is True
        assert d["canonical_root"] == "/mnt/c/Users/dev/project"
        assert d["revision"]["branch"] == "main"
        assert "error_code" not in d

    def test_error_response(self):
        response = WorkspaceResolveResponse(
            success=False,
            error_code="workspace_not_found",
            error_message="Could not find workspace root",
        )
        d = response.to_dict()
        assert d["success"] is False
        assert d["error_code"] == "workspace_not_found"
        assert "canonical_root" not in d

    def test_from_identity(self):
        # Create a mock identity-like object
        class MockIdentity:
            canonical_root = "/mnt/c/project"
            identity_hash = "a" * 64
            path_type = "windows"
            is_git_repo = True
            revision = None
            resolved_at_utc = "2024-01-01T00:00:00+00:00"

        response = WorkspaceResolveResponse.from_identity(MockIdentity())
        assert response.success is True
        assert response.canonical_root == "/mnt/c/project"

    def test_from_error(self):
        class MockError:
            code = type("Code", (), {"value": "workspace_not_found"})()
            message = "Not found"

        response = WorkspaceResolveResponse.from_error(MockError())
        assert response.success is False
        assert response.error_code == "workspace_not_found"


class TestIndexStatusRequest:
    """Test IndexStatusRequest contract."""

    def test_from_dict_with_hash(self):
        data = {"workspace_identity_hash": "abc123"}
        request = IndexStatusRequest.from_dict(data)
        assert request.workspace_identity_hash == "abc123"
        assert request.canonical_root is None

    def test_from_dict_with_root(self):
        data = {"canonical_root": "/mnt/c/project"}
        request = IndexStatusRequest.from_dict(data)
        assert request.canonical_root == "/mnt/c/project"

    def test_to_dict(self):
        request = IndexStatusRequest(
            workspace_identity_hash="abc123",
            canonical_root="/mnt/c/project",
        )
        d = request.to_dict()
        assert d["workspace_identity_hash"] == "abc123"
        assert d["canonical_root"] == "/mnt/c/project"


class TestIndexStatusResponse:
    """Test IndexStatusResponse contract."""

    def test_indexed_state(self):
        response = IndexStatusResponse(
            workspace_identity_hash="abc123",
            state=IndexState.INDEXED,
            indexed_revision="def456",
            current_revision="def456",
            file_count=1000,
            indexed_at_utc="2024-01-01T00:00:00+00:00",
        )
        d = response.to_dict()
        assert d["state"] == "indexed"
        assert d["file_count"] == 1000
        assert response.is_ready() is True
        assert response.needs_reindex() is False

    def test_stale_state(self):
        response = IndexStatusResponse(
            workspace_identity_hash="abc123",
            state=IndexState.STALE,
            indexed_revision="old123",
            current_revision="new456",
        )
        assert response.is_ready() is False
        assert response.needs_reindex() is True

    def test_indexing_state_with_progress(self):
        response = IndexStatusResponse(
            workspace_identity_hash="abc123",
            state=IndexState.INDEXING,
            progress_percent=45.5,
        )
        d = response.to_dict()
        assert d["state"] == "indexing"
        assert d["progress_percent"] == 45.5

    def test_failed_state_with_error(self):
        response = IndexStatusResponse(
            workspace_identity_hash="abc123",
            state=IndexState.FAILED,
            error_message="Out of disk space",
        )
        d = response.to_dict()
        assert d["state"] == "failed"
        assert d["error_message"] == "Out of disk space"
        assert response.needs_reindex() is True


class TestIndexState:
    """Test IndexState enum."""

    def test_all_states_have_values(self):
        states = [
            IndexState.NOT_INDEXED,
            IndexState.INDEXING,
            IndexState.INDEXED,
            IndexState.STALE,
            IndexState.FAILED,
            IndexState.UNKNOWN,
        ]
        values = [s.value for s in states]
        assert len(set(values)) == 6  # All unique


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

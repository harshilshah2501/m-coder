"""
Tests for workspace resolver.

Validates deterministic workspace root resolution.
"""

import os
import tempfile
import pytest
from pathlib import Path

from runtime.layer5.workspace.resolver import WorkspaceResolver, ResolverConfig, resolve_workspace
from runtime.layer5.workspace.identity import (
    WorkspaceIdentity,
    WorkspaceRevision,
    WorkspaceError,
    WorkspaceErrorCode,
)


class TestWorkspaceIdentity:
    """Test WorkspaceIdentity dataclass."""

    def test_compute_identity_hash_deterministic(self):
        path = "/mnt/c/Users/dev/project"
        hash1 = WorkspaceIdentity.compute_identity_hash(path)
        hash2 = WorkspaceIdentity.compute_identity_hash(path)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_identity_hash_case_insensitive(self):
        hash1 = WorkspaceIdentity.compute_identity_hash("/mnt/c/Users/Dev/Project")
        hash2 = WorkspaceIdentity.compute_identity_hash("/mnt/c/users/dev/project")
        assert hash1 == hash2

    def test_identity_hash_trailing_slash_ignored(self):
        hash1 = WorkspaceIdentity.compute_identity_hash("/mnt/c/project")
        hash2 = WorkspaceIdentity.compute_identity_hash("/mnt/c/project/")
        assert hash1 == hash2

    def test_short_identity(self):
        identity = WorkspaceIdentity(
            canonical_root="/mnt/c/project",
            identity_hash="a" * 64,
            original_input="C:\\project",
            path_type="windows",
        )
        assert identity.short_identity(12) == "a" * 12

    def test_to_dict(self):
        revision = WorkspaceRevision(
            commit_sha="abc123" + "0" * 34,
            branch="main",
            is_dirty=False,
        )
        identity = WorkspaceIdentity(
            canonical_root="/mnt/c/project",
            identity_hash="a" * 64,
            original_input="C:\\project",
            path_type="windows",
            revision=revision,
            is_git_repo=True,
        )
        d = identity.to_dict()
        assert d["canonical_root"] == "/mnt/c/project"
        assert d["identity_hash"] == "a" * 64
        assert d["path_type"] == "windows"
        assert d["is_git_repo"] is True
        assert "revision" in d
        assert d["revision"]["branch"] == "main"


class TestWorkspaceRevision:
    """Test WorkspaceRevision dataclass."""

    def test_unversioned(self):
        rev = WorkspaceRevision.unversioned()
        assert rev.commit_sha == "unversioned"
        assert rev.branch is None
        assert rev.is_versioned() is False

    def test_short_sha(self):
        rev = WorkspaceRevision(commit_sha="abc1234567890" + "0" * 27)
        assert rev.short_sha(7) == "abc1234"

    def test_short_sha_unversioned(self):
        rev = WorkspaceRevision.unversioned()
        assert rev.short_sha() == "unversioned"

    def test_to_dict(self):
        rev = WorkspaceRevision(
            commit_sha="abc123" + "0" * 34,
            branch="feature/test",
            is_dirty=True,
            is_detached=False,
            tags=["v1.0.0"],
        )
        d = rev.to_dict()
        assert d["branch"] == "feature/test"
        assert d["is_dirty"] is True
        assert d["tags"] == ["v1.0.0"]


class TestWorkspaceError:
    """Test WorkspaceError dataclass."""

    def test_error_to_dict(self):
        error = WorkspaceError(
            code=WorkspaceErrorCode.WORKSPACE_NOT_FOUND,
            message="Could not find workspace root",
            input_path="/some/path",
            details={"searched_markers": [".git", "package.json"]},
        )
        d = error.to_dict()
        assert d["code"] == "workspace_not_found"
        assert d["message"] == "Could not find workspace root"
        assert d["input_path"] == "/some/path"
        assert "searched_markers" in d["details"]


class TestResolverWithRealFilesystem:
    """Test resolver with actual filesystem (current workspace)."""

    def test_resolve_current_workspace(self):
        """Resolve the actual workspace we're in (has .git)."""
        resolver = WorkspaceResolver()
        # Use a known path in the workspace
        identity, error = resolver.resolve("/workspace/runtime/layer5")

        assert error is None
        assert identity is not None
        assert identity.is_git_repo is True
        assert identity.canonical_root.endswith("workspace") or "/workspace" in identity.canonical_root

    def test_resolve_with_file_path(self):
        """Resolution should work with file paths too."""
        resolver = WorkspaceResolver()
        identity, error = resolver.resolve("/workspace/runtime/layer5/__init__.py")

        assert error is None
        assert identity is not None
        assert identity.is_git_repo is True

    def test_revision_metadata_captured(self):
        """Test that git revision metadata is captured."""
        resolver = WorkspaceResolver()
        identity, error = resolver.resolve("/workspace")

        assert error is None
        assert identity is not None
        if identity.is_git_repo and identity.revision:
            assert identity.revision.is_versioned()
            assert len(identity.revision.commit_sha) == 40


class TestResolverWithTempDirectory:
    """Test resolver with temporary directories."""

    def test_fallback_to_input_directory(self):
        """When no markers found, fallback to input directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ResolverConfig(fallback_to_input=True)
            resolver = WorkspaceResolver(config)

            identity, error = resolver.resolve(tmpdir)

            assert error is None
            assert identity is not None
            assert identity.is_git_repo is False
            # canonical_root should be the temp directory
            assert tmpdir.rstrip("/") in identity.canonical_root or identity.canonical_root in tmpdir

    def test_no_fallback_returns_error(self):
        """When fallback disabled and no markers found, return error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ResolverConfig(fallback_to_input=False)
            resolver = WorkspaceResolver(config)

            identity, error = resolver.resolve(tmpdir)

            assert identity is None
            assert error is not None
            assert error.code == WorkspaceErrorCode.WORKSPACE_NOT_FOUND

    def test_require_git_fails_for_non_git(self):
        """require_git option rejects non-git directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ResolverConfig(require_git=True, fallback_to_input=True)
            resolver = WorkspaceResolver(config)

            identity, error = resolver.resolve(tmpdir)

            assert identity is None
            assert error is not None
            assert error.code == WorkspaceErrorCode.GIT_NOT_INITIALIZED

    def test_custom_marker_detection(self):
        """Test detection of custom workspace markers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a subdirectory
            subdir = os.path.join(tmpdir, "src", "main")
            os.makedirs(subdir)

            # Create marker at root
            marker_path = os.path.join(tmpdir, "pyproject.toml")
            Path(marker_path).touch()

            config = ResolverConfig(root_markers=["pyproject.toml"])
            resolver = WorkspaceResolver(config)

            identity, error = resolver.resolve(subdir)

            assert error is None
            assert identity is not None
            assert identity.canonical_root.rstrip("/") == tmpdir.rstrip("/")


class TestResolverDeterminism:
    """Test that resolver is deterministic."""

    def test_same_input_same_output(self):
        """Same input always produces same canonical root and hash."""
        resolver = WorkspaceResolver()

        identity1, _ = resolver.resolve("/workspace/runtime")
        identity2, _ = resolver.resolve("/workspace/runtime")

        assert identity1.canonical_root == identity2.canonical_root
        assert identity1.identity_hash == identity2.identity_hash

    def test_different_paths_same_workspace(self):
        """Different paths in same workspace produce same identity hash."""
        resolver = WorkspaceResolver()

        identity1, _ = resolver.resolve("/workspace/runtime/layer5")
        identity2, _ = resolver.resolve("/workspace/runtime/context")

        assert identity1.identity_hash == identity2.identity_hash
        assert identity1.canonical_root == identity2.canonical_root


class TestConvenienceFunction:
    """Test resolve_workspace convenience function."""

    def test_resolve_workspace_success(self):
        identity, error = resolve_workspace("/workspace")
        assert error is None
        assert identity is not None

    def test_resolve_workspace_invalid_path(self):
        identity, error = resolve_workspace("")
        assert identity is None
        assert error is not None


class TestResolveOrRaise:
    """Test resolve_or_raise method."""

    def test_resolve_or_raise_success(self):
        resolver = WorkspaceResolver()
        identity = resolver.resolve_or_raise("/workspace")
        assert identity is not None
        assert identity.canonical_root

    def test_resolve_or_raise_failure(self):
        resolver = WorkspaceResolver(ResolverConfig(require_git=True, fallback_to_input=False))

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError) as exc_info:
                resolver.resolve_or_raise(tmpdir)

            assert "git_not_initialized" in str(exc_info.value).lower() or \
                   "workspace_not_found" in str(exc_info.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

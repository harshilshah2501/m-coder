"""
Workspace resolver: deterministic canonical workspace root resolution.

The resolver walks up from a given path to find the workspace root,
using precedence rules:
1. .git directory (git repository root)
2. .workspace marker file (explicit workspace marker)
3. pyproject.toml, package.json, Cargo.toml (common project roots)
4. Fallback: use the input directory itself

For A4 (indexing): The resolver guarantees a deterministic canonical root.
A4 can index within this root without worrying about path ambiguity.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import List, Optional, Tuple

from runtime.layer5.workspace.identity import (
    WorkspaceIdentity,
    WorkspaceRevision,
    WorkspaceError,
    WorkspaceErrorCode,
)
from runtime.layer5.workspace.path_normalizer import PathNormalizer


@dataclass
class ResolverConfig:
    """
    Configuration for workspace resolution.

    Attributes:
        root_markers: Files/directories that indicate a workspace root (in precedence order).
        max_depth: Maximum directory depth to search upward.
        resolve_symlinks: Whether to resolve symlinks during normalization.
        require_git: If True, only git repositories are valid workspaces.
        fallback_to_input: If True, use input directory as root when no markers found.
    """

    root_markers: List[str] = field(
        default_factory=lambda: [
            ".git",
            ".workspace",
            "pyproject.toml",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
            "CMakeLists.txt",
            "Makefile",
        ]
    )
    max_depth: int = 50
    resolve_symlinks: bool = True
    require_git: bool = False
    fallback_to_input: bool = True


class WorkspaceResolver:
    """
    Deterministic workspace root resolver.

    Resolution algorithm:
    1. Normalize input path to canonical POSIX form
    2. Walk up directory tree looking for root markers
    3. Apply precedence rules (git > explicit marker > project file)
    4. Resolve git revision metadata if available
    5. Compute stable identity hash

    Thread-safe: all methods are stateless and can be called concurrently.
    """

    def __init__(self, config: Optional[ResolverConfig] = None):
        """Initialize resolver with optional configuration."""
        self.config = config or ResolverConfig()

    def resolve(self, input_path: str) -> Tuple[Optional[WorkspaceIdentity], Optional[WorkspaceError]]:
        """
        Resolve workspace identity from an input path.

        Args:
            input_path: Path to a file or directory within the workspace.
                       Can be Windows, WSL, or POSIX format.

        Returns:
            Tuple of (WorkspaceIdentity, None) on success,
            or (None, WorkspaceError) on failure.

        Examples:
            >>> resolver = WorkspaceResolver()
            >>> identity, error = resolver.resolve("C:\\Users\\dev\\project\\src\\main.py")
            >>> if identity:
            ...     print(identity.canonical_root)  # /mnt/c/Users/dev/project
        """
        # Step 1: Normalize input path
        norm_result = PathNormalizer.normalize(input_path, self.config.resolve_symlinks)
        if not norm_result.canonical_path:
            return None, WorkspaceError(
                code=WorkspaceErrorCode.INVALID_PATH_FORMAT,
                message="Empty or invalid path provided",
                input_path=input_path,
            )

        canonical_input = norm_result.canonical_path

        # Step 2: Determine starting directory
        start_dir = self._get_start_directory(canonical_input)
        if start_dir is None:
            return None, WorkspaceError(
                code=WorkspaceErrorCode.WORKSPACE_NOT_FOUND,
                message=f"Cannot determine directory for path: {canonical_input}",
                input_path=input_path,
            )

        # Step 3: Walk up to find workspace root
        root_path, marker_found = self._find_workspace_root(start_dir)

        if root_path is None:
            if self.config.fallback_to_input:
                root_path = start_dir
                marker_found = None
            else:
                return None, WorkspaceError(
                    code=WorkspaceErrorCode.WORKSPACE_NOT_FOUND,
                    message=f"No workspace root found within {self.config.max_depth} levels",
                    input_path=input_path,
                    details={"searched_from": start_dir, "markers": self.config.root_markers},
                )

        # Step 4: Check git requirement
        is_git_repo = self._is_git_repo(root_path)
        if self.config.require_git and not is_git_repo:
            return None, WorkspaceError(
                code=WorkspaceErrorCode.GIT_NOT_INITIALIZED,
                message="Workspace must be a git repository",
                input_path=input_path,
                details={"resolved_root": root_path},
            )

        # Step 5: Get revision metadata
        revision = self._get_revision(root_path) if is_git_repo else WorkspaceRevision.unversioned()

        # Step 6: Build identity
        identity_hash = WorkspaceIdentity.compute_identity_hash(root_path)
        snapshot_hash, snapshot_source, snapshot_dirty = self._compute_snapshot_identity(
            root_path,
            revision,
        )

        identity = WorkspaceIdentity(
            canonical_root=root_path,
            identity_hash=identity_hash,
            original_input=input_path,
            path_type=norm_result.detected_type,
            revision=revision,
            is_git_repo=is_git_repo,
            snapshot_hash=snapshot_hash,
            snapshot_source=snapshot_source,
            snapshot_dirty=snapshot_dirty,
        )

        return identity, None

    def resolve_or_raise(self, input_path: str) -> WorkspaceIdentity:
        """
        Resolve workspace identity, raising on failure.

        Convenience method for cases where failure should be exceptional.

        Raises:
            ValueError: If workspace cannot be resolved.
        """
        identity, error = self.resolve(input_path)
        if error:
            raise ValueError(f"{error.code.value}: {error.message}")
        return identity

    def _get_start_directory(self, canonical_path: str) -> Optional[str]:
        """
        Determine the starting directory for root search.

        If path is a file, use its parent directory.
        If path is a directory, use it directly.
        """
        # Try to determine if it's a file or directory
        # For non-existent paths, assume file if has extension, else directory
        p = Path(canonical_path)

        try:
            if p.exists():
                if p.is_file():
                    return str(p.parent)
                return str(p)
        except (OSError, PermissionError):
            pass

        # Path doesn't exist on this system (e.g., WSL path on native Windows)
        # Heuristic: if has file extension, treat as file
        if p.suffix:
            return str(PurePosixPath(canonical_path).parent)

        return canonical_path

    def _find_workspace_root(self, start_dir: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Walk up directory tree to find workspace root.

        Returns:
            Tuple of (root_path, marker_found) or (None, None) if not found.
        """
        current = start_dir
        depth = 0

        while depth < self.config.max_depth:
            # Check each marker in precedence order
            for marker in self.config.root_markers:
                marker_path = os.path.join(current, marker)
                # Normalize for comparison
                marker_path = marker_path.replace("\\", "/")

                try:
                    p = Path(marker_path.replace("/mnt/", "/") if os.name == "nt" else marker_path)
                    # For WSL-style paths on native Linux, check directly
                    if self._marker_exists(marker_path):
                        return current, marker
                except (OSError, PermissionError):
                    pass

            # Move to parent directory
            parent = str(PurePosixPath(current).parent)
            if parent == current:
                # Reached filesystem root
                break

            current = parent
            depth += 1

        return None, None

    def _marker_exists(self, marker_path: str) -> bool:
        """Check if a marker file/directory exists."""
        try:
            return Path(marker_path).exists()
        except (OSError, PermissionError):
            return False

    def _is_git_repo(self, root_path: str) -> bool:
        """Check if path contains a .git directory."""
        git_path = os.path.join(root_path, ".git").replace("\\", "/")
        return self._marker_exists(git_path)

    def _get_revision(self, root_path: str) -> WorkspaceRevision:
        """
        Get git revision metadata for a repository.

        Uses subprocess to call git commands for portability.
        """
        try:
            # Get current commit SHA
            commit_sha = self._run_git(root_path, ["rev-parse", "HEAD"])
            if not commit_sha:
                return WorkspaceRevision.unversioned()

            # Get current branch
            branch = self._run_git(root_path, ["branch", "--show-current"])

            # Check if detached HEAD
            is_detached = not branch

            # If detached, try to get branch from symbolic ref
            if is_detached:
                branch = None

            # Check for dirty state
            status = self._run_git(root_path, ["status", "--porcelain"])
            is_dirty = bool(status and status.strip())

            # Get tags pointing to HEAD
            tags_output = self._run_git(root_path, ["tag", "--points-at", "HEAD"])
            tags = [t.strip() for t in (tags_output or "").split("\n") if t.strip()]

            return WorkspaceRevision(
                commit_sha=commit_sha.strip(),
                branch=branch.strip() if branch else None,
                is_dirty=is_dirty,
                is_detached=is_detached,
                tags=tags,
            )

        except Exception:
            return WorkspaceRevision.unversioned()

    def _run_git(self, cwd: str, args: List[str], timeout: int = 5) -> Optional[str]:
        """Run a git command and return stdout."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None

    def _compute_snapshot_identity(
        self,
        root_path: str,
        revision: Optional[WorkspaceRevision],
    ) -> Tuple[str, str, bool]:
        """
        Compute snapshot identity hash used by retrieval/cache parity.

        Priority:
        1) git clean: commit SHA based identity
        2) git dirty: commit SHA + deterministic manifest fingerprint
        3) non-git: deterministic manifest fingerprint
        """
        if revision and revision.is_versioned():
            commit = revision.commit_sha.strip() or "unknown"
            if revision.is_dirty:
                manifest_fp = self._workspace_manifest_fingerprint(root_path)
                descriptor = f"git:{commit}:dirty:{manifest_fp}"
                return WorkspaceIdentity.compute_snapshot_hash(descriptor), "git_head_dirty_manifest_v1", True
            descriptor = f"git:{commit}:clean"
            return WorkspaceIdentity.compute_snapshot_hash(descriptor), "git_head_clean", False

        manifest_fp = self._workspace_manifest_fingerprint(root_path)
        descriptor = f"manifest:{manifest_fp}"
        return WorkspaceIdentity.compute_snapshot_hash(descriptor), "manifest_v1", False

    def _workspace_manifest_fingerprint(self, root_path: str) -> str:
        """
        Deterministic fallback fingerprint over file manifest fields.

        Fingerprint input per file: relative_path, size_bytes, mtime_ns.
        """
        root = Path(root_path)
        if not root.exists() or not root.is_dir():
            return "manifest_unavailable"

        exclude_lower = {
            ".git",
            ".svn",
            ".hg",
            "node_modules",
            "__pycache__",
            ".venv",
            "venv",
            ".idea",
            ".mypy_cache",
            ".pytest_cache",
            ".tox",
            "dist",
            "build",
            ".gradle",
            "target",
            ".cargo",
        }
        parts: List[str] = []
        try:
            for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
                dirnames[:] = [d for d in sorted(dirnames, key=lambda x: x) if d.lower() not in exclude_lower]
                for name in sorted(filenames, key=lambda x: x):
                    full = Path(dirpath) / name
                    try:
                        if full.is_symlink() or not full.is_file():
                            continue
                        st = full.stat()
                    except (OSError, PermissionError):
                        continue
                    rel = full.relative_to(root).as_posix()
                    mtime_ns = int(getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000)))
                    parts.append(f"{rel}|{int(st.st_size)}|{mtime_ns}")
        except (OSError, PermissionError):
            return "manifest_unavailable"

        manifest_payload = "\n".join(parts)
        return hashlib.sha256(manifest_payload.encode("utf-8")).hexdigest()


def resolve_workspace(input_path: str) -> Tuple[Optional[WorkspaceIdentity], Optional[WorkspaceError]]:
    """
    Convenience function: resolve workspace with default configuration.

    This is the primary entry point for workspace resolution.

    Args:
        input_path: Path to resolve (Windows, WSL, or POSIX).

    Returns:
        Tuple of (WorkspaceIdentity, None) on success,
        or (None, WorkspaceError) on failure.
    """
    resolver = WorkspaceResolver()
    return resolver.resolve(input_path)

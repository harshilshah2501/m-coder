"""
Code Index Adapter for Authority Validation.

Thin adapter to check file/class/method existence against L5 index.
Falls back to filesystem checks if index is not available.

Phase 1: Minimal interface, no new indexing system.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Protocol, Set, Tuple

from runtime.layer5.index.models import WorkspaceFileIndex


class CodeIndexProtocol(Protocol):
    """Protocol for code index access."""

    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists in index."""
        ...

    def class_exists(self, relative_path: str, class_name: str) -> bool:
        """Check if class exists in file."""
        ...

    def method_exists(
        self, relative_path: str, class_name: str, method_name: str
    ) -> bool:
        """Check if method exists in class."""
        ...

    def is_referenced(self, relative_path: str) -> Optional[bool]:
        """Check if file is referenced by other files. Returns None if unknown."""
        ...


class L5IndexAdapter:
    """
    Adapter for existing Layer-5 WorkspaceFileIndex.

    Uses the index for file existence and falls back to regex parsing
    for class/method checks when symbol inventory is not available.
    """

    def __init__(
        self,
        index: WorkspaceFileIndex,
        canonical_root: Optional[Path] = None,
    ) -> None:
        self._index = index
        self._root = (
            canonical_root
            if canonical_root is not None
            else Path(index.canonical_root)
        )
        self._file_set: Set[str] = {f.relative_path for f in index.files}

    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists in index."""
        normalized = relative_path.replace("\\", "/")
        return normalized in self._file_set

    def class_exists(self, relative_path: str, class_name: str) -> bool:
        """
        Check if class exists in file.

        Uses regex-based detection for Java files.
        """
        if not self.file_exists(relative_path):
            return False

        file_path = self._root / relative_path
        if not file_path.exists():
            return False

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            return False

        pattern = rf"\b(class|interface|enum|record)\s+{re.escape(class_name)}\b"
        return bool(re.search(pattern, content))

    def method_exists(
        self, relative_path: str, class_name: str, method_name: str
    ) -> bool:
        """
        Check if method exists in file.

        Uses regex-based detection for Java files.
        Requires class to exist first.
        """
        if not self.class_exists(relative_path, class_name):
            return False

        file_path = self._root / relative_path
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            return False

        pattern = rf"\b{re.escape(method_name)}\s*\("
        return bool(re.search(pattern, content))

    def is_referenced(self, relative_path: str) -> Optional[bool]:
        """
        Check if file is referenced by other files.

        Returns None if reference tracking is not available.
        Phase 1: Always returns None (not implemented).
        """
        return None


class FilesystemAdapter:
    """
    Fallback adapter using filesystem only.

    Used when no L5 index is available.
    """

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root

    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists on filesystem."""
        normalized = relative_path.replace("\\", "/")
        return (self._root / normalized).exists()

    def class_exists(self, relative_path: str, class_name: str) -> bool:
        """Check if class exists in file using regex."""
        file_path = self._root / relative_path.replace("\\", "/")
        if not file_path.exists():
            return False

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            return False

        pattern = rf"\b(class|interface|enum|record)\s+{re.escape(class_name)}\b"
        return bool(re.search(pattern, content))

    def method_exists(
        self, relative_path: str, class_name: str, method_name: str
    ) -> bool:
        """Check if method exists using regex."""
        if not self.class_exists(relative_path, class_name):
            return False

        file_path = self._root / relative_path.replace("\\", "/")
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            return False

        pattern = rf"\b{re.escape(method_name)}\s*\("
        return bool(re.search(pattern, content))

    def is_referenced(self, relative_path: str) -> Optional[bool]:
        """Returns None (not implemented for filesystem adapter)."""
        return None


def create_adapter(
    index: Optional[WorkspaceFileIndex] = None,
    workspace_root: Optional[Path] = None,
) -> CodeIndexProtocol:
    """
    Create appropriate code index adapter.

    Args:
        index: Optional L5 WorkspaceFileIndex.
        workspace_root: Optional workspace root path (required if no index).

    Returns:
        CodeIndexProtocol implementation.

    Raises:
        ValueError: If neither index nor workspace_root provided.
    """
    if index is not None:
        return L5IndexAdapter(index)

    if workspace_root is not None:
        return FilesystemAdapter(workspace_root)

    raise ValueError("Either index or workspace_root must be provided")

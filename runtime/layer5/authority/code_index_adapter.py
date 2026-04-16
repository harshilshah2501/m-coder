"""
Code Index Adapter for Authority Validation.

Thin adapter to check file/class/method existence against code index.
Supports multiple index backends:
- Phase 2 CodeIndex (primary)
- L5 WorkspaceFileIndex (legacy)
- Filesystem fallback

Phase 2: Extended with entry points, callers/callees.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Protocol, Set, Tuple

if TYPE_CHECKING:
    from runtime.layer5.authority.code_index_models import (
        CallEdge,
        CodeIndex,
        EntryPointRecord,
    )
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

    def get_entry_points_for_file(self, relative_path: str) -> List:
        """Get entry points in a file. Returns empty list if not available."""
        ...

    def get_direct_callers(self, class_name: str, method_name: str) -> List:
        """Get direct callers of a method. Returns empty list if not available."""
        ...

    def get_direct_callees(self, class_name: str, method_name: str) -> List:
        """Get methods called by a method. Returns empty list if not available."""
        ...

    def list_paths(self) -> Set[str]:
        """Return known relative paths in the index (for prefix-tolerant resolution)."""
        ...


class StructuredIndexAdapter:
    """
    Adapter for Phase 2 CodeIndex.

    Uses the structured index for all lookups including
    entry points and call edges.
    """

    def __init__(self, index: "CodeIndex") -> None:
        self._index = index

    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists in index."""
        return self._index.file_exists(relative_path)

    def class_exists(self, relative_path: str, class_name: str) -> bool:
        """Check if class exists in file."""
        return self._index.class_exists(relative_path, class_name)

    def method_exists(
        self, relative_path: str, class_name: str, method_name: str
    ) -> bool:
        """Check if method exists in class."""
        return self._index.method_exists(relative_path, class_name, method_name)

    def is_referenced(self, relative_path: str) -> Optional[bool]:
        """Check if file is referenced by other files."""
        return self._index.is_referenced(relative_path)

    def get_entry_points_for_file(self, relative_path: str) -> List["EntryPointRecord"]:
        """Get entry points in a file."""
        return self._index.get_entry_points_for_file(relative_path)

    def get_direct_callers(
        self, class_name: str, method_name: str
    ) -> List["CallEdge"]:
        """Get direct callers of a method (1-hop reverse)."""
        return self._index.get_callers(class_name, method_name)

    def get_direct_callees(
        self, class_name: str, method_name: str
    ) -> List["CallEdge"]:
        """Get methods called by a method (1-hop forward)."""
        return self._index.get_callees(class_name, method_name)

    def list_paths(self) -> Set[str]:
        return set(self._index.files.keys())


class L5IndexAdapter:
    """
    Adapter for existing Layer-5 WorkspaceFileIndex.

    Uses the index for file existence and falls back to regex parsing
    for class/method checks when symbol inventory is not available.
    """

    def __init__(
        self,
        index: "WorkspaceFileIndex",
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
        """
        return None

    def get_entry_points_for_file(self, relative_path: str) -> List:
        """Not available in L5 adapter."""
        return []

    def get_direct_callers(self, class_name: str, method_name: str) -> List:
        """Not available in L5 adapter."""
        return []

    def get_direct_callees(self, class_name: str, method_name: str) -> List:
        """Not available in L5 adapter."""
        return []

    def list_paths(self) -> Set[str]:
        return set(self._file_set)


class FilesystemAdapter:
    """
    Fallback adapter using filesystem only.

    Used when no index is available.
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

    def get_entry_points_for_file(self, relative_path: str) -> List:
        """Not available in filesystem adapter."""
        return []

    def get_direct_callers(self, class_name: str, method_name: str) -> List:
        """Not available in filesystem adapter."""
        return []

    def get_direct_callees(self, class_name: str, method_name: str) -> List:
        """Not available in filesystem adapter."""
        return []

    def list_paths(self) -> Set[str]:
        out: Set[str] = set()
        if not self._root.exists():
            return out
        for p in self._root.rglob("*"):
            if p.is_file():
                try:
                    out.add(str(p.relative_to(self._root)).replace("\\", "/"))
                except ValueError:
                    continue
        return out


class HybridIndexAdapter:
    """
    Primary adapter plus filesystem fallback for structural checks.

    This avoids false stale downgrades when structured symbol extraction misses
    classes/methods that are present on disk.
    """

    def __init__(self, primary: CodeIndexProtocol, fallback: CodeIndexProtocol) -> None:
        self._primary = primary
        self._fallback = fallback

    def file_exists(self, relative_path: str) -> bool:
        return self._primary.file_exists(relative_path) or self._fallback.file_exists(relative_path)

    def class_exists(self, relative_path: str, class_name: str) -> bool:
        if self._primary.class_exists(relative_path, class_name):
            return True
        if self._fallback.file_exists(relative_path):
            return self._fallback.class_exists(relative_path, class_name)
        return False

    def method_exists(self, relative_path: str, class_name: str, method_name: str) -> bool:
        if self._primary.method_exists(relative_path, class_name, method_name):
            return True
        if self._fallback.file_exists(relative_path):
            return self._fallback.method_exists(relative_path, class_name, method_name)
        return False

    def is_referenced(self, relative_path: str) -> Optional[bool]:
        primary = self._primary.is_referenced(relative_path)
        if primary is not None:
            return primary
        return self._fallback.is_referenced(relative_path)

    def get_entry_points_for_file(self, relative_path: str) -> List:
        return self._primary.get_entry_points_for_file(relative_path)

    def get_direct_callers(self, class_name: str, method_name: str) -> List:
        return self._primary.get_direct_callers(class_name, method_name)

    def get_direct_callees(self, class_name: str, method_name: str) -> List:
        return self._primary.get_direct_callees(class_name, method_name)

    def list_paths(self) -> Set[str]:
        return set(self._primary.list_paths()) | set(self._fallback.list_paths())


def create_adapter(
    code_index: Optional["CodeIndex"] = None,
    l5_index: Optional["WorkspaceFileIndex"] = None,
    workspace_root: Optional[Path] = None,
) -> CodeIndexProtocol:
    """
    Create appropriate code index adapter.

    Priority:
    1. Phase 2 CodeIndex (if provided)
    2. L5 WorkspaceFileIndex (if provided)
    3. Filesystem fallback (if workspace_root provided)

    Args:
        code_index: Optional Phase 2 CodeIndex.
        l5_index: Optional L5 WorkspaceFileIndex.
        workspace_root: Optional workspace root path.

    Returns:
        CodeIndexProtocol implementation.

    Raises:
        ValueError: If no index or workspace_root provided.
    """
    if code_index is not None:
        primary = StructuredIndexAdapter(code_index)
        if workspace_root is not None:
            return HybridIndexAdapter(primary, FilesystemAdapter(workspace_root))
        return primary

    if l5_index is not None:
        primary = L5IndexAdapter(l5_index)
        if workspace_root is not None:
            return HybridIndexAdapter(primary, FilesystemAdapter(workspace_root))
        return primary

    if workspace_root is not None:
        return FilesystemAdapter(workspace_root)

    raise ValueError("Either code_index, l5_index, or workspace_root must be provided")


# Legacy compatibility
def create_adapter_legacy(
    index: Optional["WorkspaceFileIndex"] = None,
    workspace_root: Optional[Path] = None,
) -> CodeIndexProtocol:
    """Legacy create_adapter for Phase 1 compatibility."""
    return create_adapter(l5_index=index, workspace_root=workspace_root)

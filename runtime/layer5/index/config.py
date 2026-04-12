"""
Configuration for file discovery (include/exclude rules).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet


def _default_exclude_dir_names() -> FrozenSet[str]:
    return frozenset(
        {
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
    )


@dataclass(frozen=True)
class FileIndexConfig:
    """
    Rules for which paths are visited.

    Attributes:
        exclude_dir_names: Directory base names to prune from traversal; matching
            is case-insensitive on the base name (see builder).
        follow_symlinks: If False (default), do not follow symlinks during walk.
    """

    exclude_dir_names: FrozenSet[str] = field(default_factory=_default_exclude_dir_names)
    follow_symlinks: bool = False

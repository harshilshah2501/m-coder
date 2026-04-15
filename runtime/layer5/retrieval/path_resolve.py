"""
Align authority registry paths with workspace index paths.

Registry YAML often uses a ``motadata/`` prefix while some workspace snapshots index
paths from a nested root without that prefix (or the reverse). Retrieval must treat
these as the same logical file for owner injection, Stage-B promotion, and roles.
"""

from __future__ import annotations

from typing import Optional, Set


def normalize_rel(p: str) -> str:
    return p.replace("\\", "/").strip()


def workspace_path_key(p: str) -> str:
    """Lowercased path with optional ``motadata/`` prefix stripped for comparison."""
    n = normalize_rel(p).lower()
    if n.startswith("motadata/"):
        return n[len("motadata/") :]
    return n


def paths_match_workspace(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return workspace_path_key(a) == workspace_path_key(b)


def resolve_path_in_set(path: str, path_set: Set[str]) -> Optional[str]:
    """Return the member of ``path_set`` that matches ``path`` (prefix-tolerant)."""
    if not path:
        return None
    want = workspace_path_key(path)
    for p in path_set:
        if workspace_path_key(p) == want:
            return p
    return None

"""
Align authority registry paths with workspace index paths.

Registry YAML often uses a ``motadata/`` prefix while some workspace snapshots index
paths from a nested root without that prefix (or the reverse). Retrieval must treat
these as the same logical file for owner injection, Stage-B promotion, and roles.
"""

from __future__ import annotations

from pathlib import Path
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


def resolve_owner_path_in_index(
    registry_path: str,
    path_set: Set[str],
    *,
    owner_class: Optional[str] = None,
) -> Optional[str]:
    """
    Map ``primary_owner.file`` from the registry to a path present in ``path_set``.

    First tries prefix alignment (``motadata/`` drift). If that fails, matches by
    **basename** (registry YAML paths often drift from refactors while the class file
    still exists under another directory prefix).
    """
    direct = resolve_path_in_set(registry_path, path_set)
    if direct:
        return direct
    base = Path(normalize_rel(registry_path)).name
    if not base:
        return None
    base_l = base.lower()
    matches = [p for p in path_set if Path(p).name.lower() == base_l]
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    oc = (owner_class or "").strip()
    if oc:
        oc_l = oc.lower()
        narrowed = [
            p
            for p in matches
            if oc_l in normalize_rel(p).lower().replace(".java", "")
        ]
        if len(narrowed) == 1:
            return narrowed[0]
    reg = normalize_rel(registry_path).lower().strip("/")
    reg_parts = reg.split("/")
    if len(reg_parts) >= 4:
        tail = "/".join(reg_parts[-4:])
        tail_hits = [p for p in matches if normalize_rel(p).lower().strip("/").endswith(tail)]
        if len(tail_hits) == 1:
            return tail_hits[0]
        if len(tail_hits) > 1:
            return min(tail_hits)
    if "correlation" in reg:
        corr = [p for p in matches if "/correlation/" in normalize_rel(p).lower()]
        if len(corr) == 1:
            return corr[0]
    return min(matches)

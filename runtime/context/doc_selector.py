"""
Doc selector — M3.12 deterministic selection from manifest.

Selects relevant paths from a RepoManifest using path, title/heading,
symbol, and adjacency. No semantic retrieval; same manifest + query -> same refs.
"""

from __future__ import annotations

import re
from typing import List

from runtime.context.contracts import ContextRequest, SelectedContextRef
from runtime.context.manifest_models import ManifestEntry, RepoManifest


def _query_tokens(query: str) -> List[str]:
    """Deterministic tokenization: alphanumeric, length >= 3, lowercase, dedupe order."""
    raw = re.split(r"[^A-Za-z0-9_]+", query)
    seen: set[str] = set()
    out: List[str] = []
    for t in raw:
        t = t.lower()
        if len(t) < 3:
            continue
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def _path_matches_tokens(path: str, tokens: List[str]) -> bool:
    """True if any token appears as substring in path (case-insensitive)."""
    path_lower = path.lower()
    return any(t in path_lower for t in tokens)


def _entry_matches_heading(entry: ManifestEntry, tokens: List[str]) -> bool:
    """True if any token matches title or any heading."""
    text = (entry.title + " " + " ".join(entry.headings)).lower()
    return any(t in text for t in tokens)


def _entry_matches_symbol(entry: ManifestEntry, symbol_hints: List[str]) -> bool:
    """True if any symbol hint matches an anchor or path."""
    if not symbol_hints:
        return False
    path_lower = entry.path.lower()
    anchors_lower = " ".join(entry.symbol_anchors).lower()
    for h in symbol_hints:
        if h in path_lower or h in anchors_lower:
            return True
    return False


def _same_dir(path: str, other: str) -> bool:
    """True if both paths are in the same directory."""
    return path.rsplit("/", 1)[0] == other.rsplit("/", 1)[0]


def select_from_manifest(
    manifest: RepoManifest,
    query: str,
    request: ContextRequest,
) -> List[SelectedContextRef]:
    """
    Deterministic selection from manifest: path match, heading match, symbol match, adjacency.
    Capped by request.max_files. Same manifest + query + request -> same ref list.
    """
    tokens = _query_tokens(query)
    symbol_hints = list(request.symbol_hints) if request.symbol_hints else []
    max_files = max(1, request.max_files)

    # Priority: path_match=0, heading_match=5, symbol_match=10, adjacent=15
    refs_by_path: dict[str, SelectedContextRef] = {}

    for entry in manifest.entries:
        if len(refs_by_path) >= max_files:
            break
        path = entry.path
        if path in refs_by_path:
            continue
        if tokens and _path_matches_tokens(path, tokens):
            refs_by_path[path] = SelectedContextRef(
                path=path,
                selection_reason="path_match",
                selector="manifest",
                priority=0,
            )
            continue
        if tokens and _entry_matches_heading(entry, tokens):
            refs_by_path[path] = SelectedContextRef(
                path=path,
                selection_reason="heading_match",
                selector="manifest",
                priority=5,
            )
            continue
        if _entry_matches_symbol(entry, symbol_hints):
            refs_by_path[path] = SelectedContextRef(
                path=path,
                selection_reason="symbol:hint:" + (symbol_hints[0] if symbol_hints else ""),
                selector="manifest",
                priority=10,
            )

    # Adjacency: for each selected path, add same-dir entries from manifest (up to cap)
    initial_paths = set(refs_by_path.keys())
    for path in sorted(initial_paths):
        if len(refs_by_path) >= max_files:
            break
        for entry in manifest.entries:
            if len(refs_by_path) >= max_files:
                break
            if entry.path in refs_by_path:
                continue
            if _same_dir(path, entry.path):
                refs_by_path[entry.path] = SelectedContextRef(
                    path=entry.path,
                    selection_reason="adjacent:dir",
                    selector="manifest",
                    priority=15,
                )

    # Stable order by path
    return [refs_by_path[p] for p in sorted(refs_by_path.keys())][:max_files]

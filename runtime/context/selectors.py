"""
Deterministic repository context selectors — M3.0.

Selectors operate on the filesystem only and return lightweight SelectedContextRef
objects. No file contents are materialized here.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, List

from runtime.context.contracts import ContextRequest, SelectedContextRef

# Skip these path segments when scanning for symbol hints (vendor / VCS / caches).
_SYMBOL_SCAN_SKIP_PARTS = frozenset({
    ".git",
    ".dvc",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".gradle",
    ".idea",
})


def _path_ok_for_symbol_scan(p: Path) -> bool:
    try:
        parts = p.parts
    except (OSError, ValueError):
        return False
    return not _SYMBOL_SCAN_SKIP_PARTS.intersection(parts)


def _normalize_root(root_path: str) -> Path:
    """Return normalized absolute root path."""
    return Path(root_path).resolve()


def _normalize_rel_path(root: Path, p: Path) -> str:
    """
    Normalize path relative to root, using POSIX-style separators.
    Assumes p is under root.
    """
    rel = p.resolve().relative_to(root)
    return rel.as_posix()


def select_direct(root_path: str, request: ContextRequest) -> List[SelectedContextRef]:
    """
    Direct file selection for explicitly requested files.

    Fail-closed on missing explicitly requested files.
    """
    root = _normalize_root(root_path)
    refs: List[SelectedContextRef] = []
    missing: List[str] = []

    for raw in sorted(set(request.files)):
        candidate = (root / raw).resolve()
        if not candidate.exists() or not candidate.is_file():
            missing.append(raw)
            continue
        rel = _normalize_rel_path(root, candidate)
        refs.append(
            SelectedContextRef(
                path=rel,
                selection_reason="direct:file",
                selector="direct",
                priority=0,
            )
        )

    if missing:
        # Fail-closed: caller must treat this as an error.
        raise FileNotFoundError(f"Missing explicitly requested files: {', '.join(sorted(missing))}")

    # Already stable due to sorted(request.files) and deterministic normalization.
    return refs


def select_siblings(root_path: str, base_refs: Iterable[SelectedContextRef]) -> List[SelectedContextRef]:
    """
    Sibling file expansion: include files in same directories as base_refs.
    """
    root = _normalize_root(root_path)
    base_paths = {r.path for r in base_refs}
    siblings: set[str] = set()

    for r in base_refs:
        base_file = root / r.path
        parent = base_file.parent
        if not parent.exists():
            continue
        for child in sorted(parent.iterdir(), key=lambda p: p.name):
            if not child.is_file():
                continue
            if child.name.startswith("."):
                continue
            rel = _normalize_rel_path(root, child)
            if rel in base_paths:
                continue
            siblings.add(rel)

    return [
        SelectedContextRef(
            path=p,
            selection_reason="sibling:directory",
            selector="siblings",
            priority=10,
        )
        for p in sorted(siblings)
    ]


def _python_import_neighbors(root: Path, rel_path: str) -> List[str]:
    """
    Simple Python import neighbor expansion for a single file.
    """
    file_path = (root / rel_path).resolve()
    if file_path.suffix != ".py" or not file_path.exists():
        return []

    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    neighbors: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")
                candidate = root.joinpath(*mod).with_suffix(".py")
                if candidate.exists():
                    neighbors.add(_normalize_rel_path(root, candidate))
        elif isinstance(node, ast.ImportFrom):
            if not node.module:
                continue
            mod = node.module.split(".")
            candidate = root.joinpath(*mod).with_suffix(".py")
            if candidate.exists():
                neighbors.add(_normalize_rel_path(root, candidate))

    # Do not include self.
    neighbors.discard(rel_path)
    return sorted(neighbors)


def select_import_neighbors(root_path: str, base_refs: Iterable[SelectedContextRef]) -> List[SelectedContextRef]:
    """
    Simple dependency/import neighbor expansion.

    Currently supports Python `.py` files via AST import scanning.
    """
    root = _normalize_root(root_path)
    base_paths = {r.path for r in base_refs}
    neighbors: set[str] = set()

    for r in base_refs:
        for neighbor in _python_import_neighbors(root, r.path):
            if neighbor in base_paths:
                continue
            neighbors.add(neighbor)

    return [
        SelectedContextRef(
            path=p,
            selection_reason="import:neighbor",
            selector="imports",
            priority=20,
        )
        for p in sorted(neighbors)
    ]


def select_symbol_hints(root_path: str, symbol_hints: Iterable[str]) -> List[SelectedContextRef]:
    """
    Deterministic symbol-hint matching via text search.

    For each hint, walk files under root in lexicographic order and select the
    first file containing the hint as a substring.
    """
    root = _normalize_root(root_path)
    hints = [h for h in symbol_hints if h]
    if not hints:
        return []

    # Precompute sorted candidate files. Skip symlinks so we never read through
    # e.g. .venv/bin/python → /usr/bin/python3.12 (binary matches token substrings;
    # resolve() then escapes repo and breaks relative_to).
    all_files: List[Path] = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and not p.is_symlink() and _path_ok_for_symbol_scan(p):
            all_files.append(p)

    refs: List[SelectedContextRef] = []
    for hint in hints:
        selected_path: str | None = None
        for f in all_files:
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if hint in text.lower():
                try:
                    selected_path = _normalize_rel_path(root, f)
                except ValueError:
                    continue
                break
        if selected_path is not None:
            refs.append(
                SelectedContextRef(
                    path=selected_path,
                    selection_reason=f"symbol:hint:{hint}",
                    selector="symbols",
                    priority=30,
                )
            )
    return refs


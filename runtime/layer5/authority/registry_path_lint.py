"""
Validate ``product_authority_registry.yaml`` file paths against a workspace root on disk.

Use before relying on authority-driven retrieval: missing paths cause
``resolved_in_index: false`` and weak owner injection despite a valid registry load.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from runtime.layer5.authority.registry_loader import AuthorityRegistry


@dataclass(frozen=True)
class RegistryPathIssue:
    """A registry ``file`` path that does not resolve to a regular file under ``workspace_root``."""

    concept_id: str
    role: str
    file: str
    expected_abs: str
    detail: str


def _norm_rel(p: str) -> str:
    return p.replace("\\", "/").strip()


def _inner_rel(rel: str) -> str:
    """Path inside the ``motadata`` module: strip at most one leading ``motadata/`` segment."""
    r = _norm_rel(rel)
    if r.startswith("motadata/"):
        return r[len("motadata/") :].lstrip("/")
    return r


def _resolve_path_candidates(root: Path, rel: str) -> List[Path]:
    """
    Return ordered unique absolute paths to validate for a registry-relative path.

    Typical clone layout when ``--workspace-root`` is the product repo folder named
    ``Motadata``::

        <workspace_root>/motadata/src/main/java/...

    So we **first** try ``workspace_root / motadata / <inner>``, where ``inner`` is the
    registry path with an optional leading ``motadata/`` removed (Java paths are then
    ``.../src/main/java/...``).

    Then we try the path as written in YAML, then a flat ``workspace_root/src/...`` when
    the registry used a ``motadata/`` prefix (inner checkout without an extra folder).
    """
    rel = _norm_rel(rel)
    inner = _inner_rel(rel)
    raw: List[Path] = []
    if inner:
        raw.append(root / "motadata" / inner)
    raw.append(root / rel)
    if rel.startswith("motadata/") and inner:
        raw.append(root / inner)
    out: List[Path] = []
    seen: set[str] = set()
    for p in raw:
        try:
            rp = p.resolve()
        except OSError:
            continue
        key = str(rp)
        if key not in seen:
            seen.add(key)
            out.append(rp)
    return out


def collect_registry_file_refs(registry: AuthorityRegistry) -> List[Tuple[str, str, str]]:
    """
    Returns ``(concept_id, role, relative_file)`` for every file referenced in the registry.

    Roles: ``primary_owner``, ``collaborator``, ``forbidden_distractor``, ``entry_point``.
    """
    rows: List[Tuple[str, str, str]] = []
    for name, c in registry.concepts.items():
        po = _norm_rel(c.primary_owner.file)
        if po:
            rows.append((name, "primary_owner", po))
        for col in c.collaborators:
            f = _norm_rel(col.file)
            if f:
                rows.append((name, "collaborator", f))
        for d in c.forbidden_distractors:
            f = _norm_rel(d.file)
            if f:
                rows.append((name, "forbidden_distractor", f))
        for ep in c.entry_points:
            f = _norm_rel(ep.file)
            if f:
                rows.append((name, "entry_point", f))
    return rows


def lint_registry_against_workspace(
    registry: AuthorityRegistry,
    workspace_root: Path,
) -> List[RegistryPathIssue]:
    """
    Check that every referenced file exists under ``workspace_root`` as a regular file.

    Paths in YAML are resolved with :func:`_resolve_path_candidates` so both a nested
    ``motadata/`` tree and a flat module root match the same registry entries.
    """
    root = workspace_root.resolve()
    issues: List[RegistryPathIssue] = []
    for concept_id, role, rel in collect_registry_file_refs(registry):
        if ".." in Path(rel).parts:
            issues.append(
                RegistryPathIssue(
                    concept_id=concept_id,
                    role=role,
                    file=rel,
                    expected_abs="",
                    detail="path_contains_parent_reference",
                )
            )
            continue
        candidates = _resolve_path_candidates(root, rel)
        primary = candidates[0]

        matched: Path | None = None
        for candidate in candidates:
            try:
                candidate.relative_to(root)
            except ValueError:
                continue
            if candidate.is_file():
                matched = candidate
                break
        if matched is not None:
            continue

        try:
            primary.relative_to(root)
        except ValueError:
            issues.append(
                RegistryPathIssue(
                    concept_id=concept_id,
                    role=role,
                    file=rel,
                    expected_abs=str(primary),
                    detail="path_escapes_workspace_root",
                )
            )
            continue

        detail = "missing"
        if primary.exists() and not primary.is_file():
            detail = "not_a_file"
        elif any(c.exists() and not c.is_file() for c in candidates):
            detail = "not_a_file"
        else:
            extras = [c for c in candidates[1:] if c != primary]
            if extras:
                detail = f"missing (also tried: {', '.join(str(x) for x in extras)})"

        issues.append(
            RegistryPathIssue(
                concept_id=concept_id,
                role=role,
                file=rel,
                expected_abs=str(primary),
                detail=detail,
            )
        )
    return issues


def format_issues_report(issues: Sequence[RegistryPathIssue]) -> str:
    lines: List[str] = []
    for i in issues:
        lines.append(
            f"- [{i.concept_id}] {i.role}: {i.file}\n  expected: {i.expected_abs}\n  ({i.detail})"
        )
    return "\n".join(lines)

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

    Paths in YAML are joined as ``workspace_root / relative_path`` (POSIX-style segments).
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
        candidate = (root / rel).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            issues.append(
                RegistryPathIssue(
                    concept_id=concept_id,
                    role=role,
                    file=rel,
                    expected_abs=str(candidate),
                    detail="path_escapes_workspace_root",
                )
            )
            continue
        if not candidate.is_file():
            detail = "missing"
            if candidate.exists() and not candidate.is_file():
                detail = "not_a_file"
            issues.append(
                RegistryPathIssue(
                    concept_id=concept_id,
                    role=role,
                    file=rel,
                    expected_abs=str(candidate),
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

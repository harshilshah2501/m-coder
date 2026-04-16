#!/usr/bin/env python3
"""
Generate non-destructive drift proposals for product_authority_registry.yaml.

This script does not edit files. It emits a JSON proposal with:
- missing/invalid registry path issues
- basename-based candidate replacements
- class-name mismatch hints for primary owners
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def _default_registry_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "layer5"
        / "authority"
        / "product_authority_registry.yaml"
    )


def _norm_rel(p: str) -> str:
    return p.replace("\\", "/").strip()


def _to_registry_relative(candidate: Path, workspace_root: Path) -> str | None:
    """Normalize absolute candidate path to registry-style relative path."""
    try:
        rel = candidate.resolve().relative_to(workspace_root.resolve())
    except ValueError:
        return None
    s = _norm_rel(str(rel))
    if s.startswith("motadata/"):
        return s[len("motadata/") :]
    return s


def _build_java_basename_index(workspace_root: Path) -> dict[str, list[Path]]:
    out: dict[str, list[Path]] = defaultdict(list)
    roots = [
        workspace_root / "motadata" / "src" / "main" / "java",
        workspace_root / "src" / "main" / "java",
    ]
    seen: set[str] = set()
    for r in roots:
        if not r.is_dir():
            continue
        for p in r.rglob("*.java"):
            rp = str(p.resolve())
            if rp in seen:
                continue
            seen.add(rp)
            out[p.name.lower()].append(p.resolve())
    return out


def _primary_class_name(java_file: Path) -> str | None:
    try:
        txt = java_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    m = re.search(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\b", txt)
    if not m:
        return None
    return m.group(1)


def _proposals_for_issue(
    issue: Any,
    *,
    workspace_root: Path,
    basename_index: dict[str, list[Path]],
) -> dict[str, Any]:
    rel = _norm_rel(str(issue.file))
    base = Path(rel).name.lower()
    candidates = basename_index.get(base, [])
    suggestions: list[dict[str, Any]] = []
    for c in candidates[:8]:
        rr = _to_registry_relative(c, workspace_root)
        if not rr:
            continue
        suggestions.append(
            {
                "candidate_file": rr,
                "candidate_abs": str(c),
                "confidence": "high" if len(candidates) == 1 else "medium",
                "basis": "basename_match",
            }
        )
    return {
        "concept_id": issue.concept_id,
        "role": issue.role,
        "current_file": rel,
        "detail": issue.detail,
        "expected_abs": issue.expected_abs,
        "suggestions": suggestions,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace-root", required=True, help="Workspace root for Motadata checkout")
    p.add_argument(
        "--registry",
        default=str(_default_registry_path()),
        help="Path to product_authority_registry.yaml",
    )
    p.add_argument(
        "--out",
        default="runtime/.run/authority_registry_drift_proposal.json",
        help="Output JSON path for proposal report",
    )
    args = p.parse_args()

    ws = Path(args.workspace_root).expanduser()
    reg_path = Path(args.registry).expanduser()
    out_path = Path(args.out).expanduser()
    if not ws.is_dir():
        print(f"ERROR: workspace root is not a directory: {ws}", file=sys.stderr)
        return 2
    if not reg_path.is_file():
        print(f"ERROR: registry file not found: {reg_path}", file=sys.stderr)
        return 2

    from runtime.layer5.authority.registry_loader import load_registry
    from runtime.layer5.authority.registry_path_lint import (
        collect_registry_file_refs,
        lint_registry_against_workspace,
    )

    registry = load_registry(reg_path)
    issues = lint_registry_against_workspace(registry, ws)
    basename_index = _build_java_basename_index(ws)

    proposals = [
        _proposals_for_issue(i, workspace_root=ws, basename_index=basename_index)
        for i in issues
    ]

    class_hints: list[dict[str, Any]] = []
    for concept_id, _role, _rel in collect_registry_file_refs(registry):
        c = registry.concepts.get(concept_id)
        if not c:
            continue
        owner_file = _norm_rel(c.primary_owner.file)
        owner_class = c.primary_owner.class_name
        owner_candidates: list[Path] = []
        for abs_c in basename_index.get(Path(owner_file).name.lower(), []):
            rr = _to_registry_relative(abs_c, ws)
            if rr and _norm_rel(rr) == owner_file:
                owner_candidates.append(abs_c)
        for abs_c in owner_candidates[:1]:
            actual_class = _primary_class_name(abs_c)
            if actual_class and owner_class and actual_class != owner_class:
                class_hints.append(
                    {
                        "concept_id": concept_id,
                        "owner_file": owner_file,
                        "registry_class": owner_class,
                        "detected_primary_class": actual_class,
                    }
                )

    report = {
        "schema_version": "authority_registry_drift_proposal.v1",
        "workspace_root": str(ws.resolve()),
        "registry": str(reg_path.resolve()),
        "issues_count": len(issues),
        "proposal_count": len(proposals),
        "class_hint_count": len(class_hints),
        "proposals": proposals,
        "class_hints": class_hints,
        "note": (
            "Non-destructive proposal only. Review suggestions before editing registry. "
            "No file mutations performed."
        ),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved: {out_path}")
    print(f"issues={len(issues)} proposals={len(proposals)} class_hints={len(class_hints)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


"""
Deterministic file role hints for Stage B/C (spec §6.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import AbstractSet, Dict, List, Optional, Tuple

from runtime.layer5.retrieval.policy import FilePolicy, classify_file, is_noise_class

PRIMARY_OWNER_CANDIDATE = "PRIMARY_OWNER_CANDIDATE"
SUPPORTING_CONTEXT = "SUPPORTING_CONTEXT"
DISTRACTOR_RISK = "DISTRACTOR_RISK"


@dataclass(frozen=True)
class RoleAssignment:
    path: str
    role: str
    reasons: Tuple[str, ...]


def _norm(p: str) -> str:
    return p.replace("\\", "/").strip().lower()


def assign_roles(
    ordered_paths: Tuple[str, ...],
    *,
    owner_path: Optional[str],
    collaborator_paths: Optional[AbstractSet[str]] = None,
) -> Dict[str, RoleAssignment]:
    """
    Assign PRIMARY / SUPPORTING / DISTRACTOR to each path in fused order.

    - Highest fused rank whose path matches owner (normalized) → PRIMARY if present.
    - Otherwise first path in core_aiops_code → PRIMARY (owner-domain proxy).
    - Collaborator files → SUPPORTING when not PRIMARY.
    - Noise / generic-support files → DISTRACTOR_RISK unless PRIMARY.
    """
    collab_set = {_norm(f) for f in (collaborator_paths or ())}

    owner_n = _norm(owner_path) if owner_path else ""

    roles: Dict[str, RoleAssignment] = {}
    primary_assigned = False

    for i, path in enumerate(ordered_paths):
        policy: FilePolicy = classify_file(path)
        pn = _norm(path)
        reasons: List[str] = []

        if owner_n and pn == owner_n:
            role = PRIMARY_OWNER_CANDIDATE
            reasons.append("authority_owner_path")
            primary_assigned = True
        elif not primary_assigned and i == 0 and policy.file_class == "core_aiops_code":
            role = PRIMARY_OWNER_CANDIDATE
            reasons.append("top_rank_core_aiops")
            primary_assigned = True
        elif owner_n and owner_n in pn and policy.file_class == "core_aiops_code":
            role = PRIMARY_OWNER_CANDIDATE
            reasons.append("path_contains_owner_segment")
            primary_assigned = True
        elif pn in collab_set:
            role = SUPPORTING_CONTEXT
            reasons.append("authority_collaborator")
        elif policy.file_class == "core_aiops_code":
            role = SUPPORTING_CONTEXT
            reasons.append("core_aiops_supporting")
        elif is_noise_class(policy.file_class):
            role = DISTRACTOR_RISK
            reasons.append(f"noise_class:{policy.file_class}")
        elif policy.file_class in {"config", "supporting_prod_code"}:
            role = SUPPORTING_CONTEXT
            reasons.append(f"file_class:{policy.file_class}")
        else:
            role = DISTRACTOR_RISK
            reasons.append(f"fallback:{policy.file_class}")

        roles[path] = RoleAssignment(path=path, role=role, reasons=tuple(reasons))

    return roles

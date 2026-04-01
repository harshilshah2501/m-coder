"""
Build ``authority_resolution`` and related evidence payloads (Phase 4).

Read-only: uses existing registry, validation, and ranking context — no retrieval changes.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from runtime.layer5.authority.code_index_adapter import CodeIndexProtocol
from runtime.layer5.authority.ranking import AuthorityRanker, RankingContext
from runtime.layer5.authority.registry_loader import AuthorityRegistry, Concept
from runtime.layer5.authority.validation import ValidationResult, validate_concept


def _normalize_rel(path: str) -> str:
    return path.replace("\\", "/").strip()


def match_concepts_for_query(
    query: str,
    registry: AuthorityRegistry,
) -> List[Tuple[Concept, str, float]]:
    """
    Match one or more concepts (e.g. compound queries: \"A and B\").
    Falls back to single match on full query when split matching yields nothing.
    """
    raw = (query or "").strip()
    if not raw:
        return []

    parts = re.split(r"\s+and\s+", raw, flags=re.IGNORECASE)
    out: List[Tuple[Concept, str, float]] = []
    seen: set[str] = set()
    for part in parts:
        part = part.strip()
        if len(part) < 2:
            continue
        m = registry.match_concept(part)
        if m and m[0].name not in seen:
            seen.add(m[0].name)
            out.append(m)

    if not out:
        m = registry.match_concept(raw)
        if m:
            out.append(m)
    return out


def _owner_dict_from_concept(c: Concept) -> Dict[str, Any]:
    po = c.primary_owner
    conf = po.confidence if po.confidence in ("high", "medium", "low") else "medium"
    mapped = {"high": "high", "medium": "medium", "low": "weak"}
    return {
        "file": po.file,
        "class": po.class_name,
        "method": po.method,
        "confidence": mapped.get(conf, "medium"),
    }


def _control_flow_to_list(control_flow: Optional[Dict[str, Any]]) -> List[str]:
    if not control_flow or not isinstance(control_flow, dict):
        return []
    out: List[str] = []
    if control_flow.get("entry"):
        out.append(f"entry: {control_flow['entry']}")
    for step in control_flow.get("path") or []:
        out.append(str(step))
    if control_flow.get("exit"):
        out.append(f"exit: {control_flow['exit']}")
    return out


def _authority_confidence_aggregate(
    primary_owner_confidence: str,
    authority_status: str,
) -> str:
    base = {"high": "high", "medium": "medium", "weak": "weak"}.get(
        primary_owner_confidence, "weak"
    )
    if authority_status == "stale":
        return "weak"
    if authority_status == "stale_candidate":
        return "medium" if base == "high" else "weak"
    if authority_status == "unverified":
        return "medium" if base == "high" else base
    return base


def _validation_details(vr: Optional[ValidationResult]) -> Optional[Dict[str, Any]]:
    if vr is None:
        return None
    ch = vr.checks
    return {
        "file_exists": ch.file_exists,
        "class_exists": ch.class_exists,
        "method_exists": ch.method_exists,
        "is_referenced": ch.is_referenced,
        "freshness_ok": ch.freshness_ok,
        "days_since_verification": ch.days_since_verification,
    }


def _entry_trace_for_concept(c: Concept) -> Optional[Dict[str, Any]]:
    cf = c.control_flow
    path_lines: List[str] = []
    if isinstance(cf, dict) and cf.get("path"):
        path_lines = [str(x) for x in cf["path"]]
    if not path_lines and not c.entry_points:
        return None
    out: Dict[str, Any] = {"path": path_lines}
    if c.entry_points:
        ep = c.entry_points[0]
        out["entry_point"] = {
            "type": ep.type,
            "file": ep.file,
            "method": ep.method,
        }
    return out


def _merge_forbidden(concepts: List[Concept]) -> List[Dict[str, str]]:
    seen: set[str] = set()
    out: List[Dict[str, str]] = []
    for c in concepts:
        for d in c.forbidden_distractors:
            n = _normalize_rel(d.file).lower()
            if n not in seen:
                seen.add(n)
                out.append({"file": d.file, "reason": d.reason})
    return out


def build_ranking_context_for_matches(
    query: str,
    registry: AuthorityRegistry,
    matches: List[Tuple[Concept, str, float]],
    code_index: Optional[CodeIndexProtocol],
) -> RankingContext:
    """Align ranker context with the primary (first) matched concept."""
    ranker = AuthorityRanker(registry, code_index, None)
    first = matches[0][0]
    return ranker.build_context(query, concept=first)


def build_authority_resolution(
    query: str,
    registry: AuthorityRegistry,
    code_index: Optional[CodeIndexProtocol],
    *,
    matches: Optional[List[Tuple[Concept, str, float]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Build the ``authority_resolution`` object for the evidence bundle.

    Returns None when no concept matches the query.
    """
    mlist = matches if matches is not None else match_concepts_for_query(query, registry)
    if not mlist:
        return None

    ctx = build_ranking_context_for_matches(query, registry, mlist, code_index)

    matched_json: List[Dict[str, Any]] = []
    vr0: Optional[ValidationResult] = None
    for concept, match_type, conf in mlist:
        mc: Dict[str, Any] = {
            "concept_id": concept.name,
            "match_type": match_type,
            "confidence": max(0, min(100, int(round(float(conf) * 100)))),
            "primary_owner": _owner_dict_from_concept(concept),
        }
        matched_json.append(mc)

    first = mlist[0][0]
    if code_index is not None:
        vr0 = validate_concept(first, code_index)

    authority_status = vr0.status.value if vr0 is not None else ctx.authority_status

    po = _owner_dict_from_concept(first)
    authority_confidence = _authority_confidence_aggregate(
        po["confidence"], authority_status
    )

    notes = list(first.notes)
    control_flow = _control_flow_to_list(
        first.control_flow if isinstance(first.control_flow, dict) else None
    )
    entry_trace = _entry_trace_for_concept(first)
    validation_details = _validation_details(vr0)

    resolution: Dict[str, Any] = {
        "matched_concepts": matched_json,
        "primary_owner": po,
        "authority_confidence": authority_confidence,
        "authority_status": authority_status,
        "control_flow": control_flow,
        "notes": notes,
        "forbidden_distractors": _merge_forbidden([m[0] for m in mlist]),
        "collaborators": [
            {"file": c.file, "role": c.role, "relationship": c.relationship}
            for c in first.collaborators
        ],
    }
    if validation_details is not None:
        resolution["validation_details"] = validation_details
    if entry_trace is not None:
        resolution["entry_trace"] = entry_trace
    if len(mlist) > 1:
        resolution["compound"] = True
    return resolution


def build_structural_context_stub(
    concept: Concept,
    code_index: Optional[CodeIndexProtocol],
) -> Optional[Dict[str, Any]]:
    """Minimal structural context when index data is available."""
    if code_index is None or not concept.primary_owner.class_name:
        return None
    cls = concept.primary_owner.class_name
    meth = concept.primary_owner.method
    callers: List[str] = []
    if meth:
        try:
            edges = code_index.get_direct_callers(cls, meth)
            for e in edges[:16]:
                callers.append(f"{e.source_class}.{e.source_method}")
        except Exception:
            pass
    if not callers:
        return None
    return {
        "callers_hop_1": callers[:8],
        "callers_hop_2": [],
        "callees_hop_1": [],
        "callees_hop_2": [],
        "entry_points": [f"{ep.file}:{ep.method}" for ep in concept.entry_points[:8]],
        "hop_2_pruned_count": 0,
    }

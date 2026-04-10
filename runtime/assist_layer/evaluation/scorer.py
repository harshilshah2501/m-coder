from __future__ import annotations

from typing import Any, Dict, List, Tuple


QUALITY_RANK = {
    "NO_MATCH": 0,
    "INSUFFICIENT": 1,
    "WEAK": 2,
    "STRONG": 3,
}


def score_comparison(comparison: Dict[str, Any]) -> Tuple[str, List[str]]:
    reasons: List[str] = []

    bq = str((comparison.get("evidence_quality") or {}).get("baseline") or "")
    cq = str((comparison.get("evidence_quality") or {}).get("candidate") or "")
    b_rank = QUALITY_RANK.get(bq, -1)
    c_rank = QUALITY_RANK.get(cq, -1)

    files_overlap = float((comparison.get("files") or {}).get("overlap_ratio") or 0.0)
    files_exact = bool((comparison.get("files") or {}).get("exact_match"))
    selectors_exact = bool((comparison.get("selectors_used") or {}).get("exact_match"))
    steps_exact = bool((comparison.get("plan_steps") or {}).get("exact_match"))
    normalized_steps_equal = bool((comparison.get("plan_steps") or {}).get("normalized_equal"))
    key_fields_equal = bool((comparison.get("output_equivalence") or {}).get("key_fields_equal"))

    governance_equal = bool((comparison.get("core_flags") or {}).get("governance_posture_equal"))
    execution_equal = bool((comparison.get("core_flags") or {}).get("execution_equal"))
    routing_equal = bool((comparison.get("core_flags") or {}).get("routing_mode_equal"))

    # Major degradations: authority/safety drift or hard quality drop.
    if not governance_equal or not execution_equal or not routing_equal:
        reasons.append("core runtime flags diverged")
        return "degraded_major", reasons

    if c_rank < b_rank:
        reasons.append("candidate evidence_quality ranked lower than baseline")
        return "degraded_major", reasons

    if c_rank > b_rank:
        reasons.append("candidate evidence_quality ranked higher than baseline")
        return "improved", reasons

    if files_exact and selectors_exact and (steps_exact or normalized_steps_equal) and key_fields_equal:
        reasons.append("outputs equivalent across compared dimensions")
        return "same", reasons

    # Same evidence quality with divergence: classify deterministic minor/major degradation.
    if not selectors_exact and files_overlap < 0.5:
        reasons.append("selectors diverged with low file overlap")
        return "degraded_major", reasons

    if files_overlap < 0.5:
        reasons.append("context file overlap below threshold")
        return "degraded_minor", reasons

    if not selectors_exact and not normalized_steps_equal:
        reasons.append("selectors and normalized plan steps both diverged")
        return "degraded_major", reasons

    if not selectors_exact or not normalized_steps_equal:
        reasons.append("bounded divergence with stable evidence quality")
        return "degraded_minor", reasons

    reasons.append("quality stable with bounded output differences")
    return "same", reasons

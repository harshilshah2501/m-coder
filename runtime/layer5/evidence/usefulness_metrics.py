"""
Deterministic, evidence-bundle-level signals for retrieval usefulness (Plan-Gate metadata).

Uses the same path classification as the quality gate so operators can compare
``usefulness_metrics`` with ``dominance_metrics`` without a second policy.
"""

from __future__ import annotations

from typing import Any, Dict, List

from runtime.layer5.retrieval.policy import classify_file, is_noise_class

_ANCHOR = "query_token_substring_anchor"


def bundle_usefulness_metrics(entries: List[Any]) -> Dict[str, Any]:
    """
    Summarize evidence_bundle.entries for operator-facing diagnostics.

    Safe on partial or empty input: returns zeros / empty dicts without raising.
    """
    if not isinstance(entries, list) or not entries:
        return {
            "entry_count": 0,
            "top1_retrieval_score": None,
            "retrieval_score_min": None,
            "retrieval_score_max": None,
            "retrieval_score_spread": 0,
            "snippet_anchor_hits": 0,
            "snippet_non_anchor_hits": 0,
            "file_class_counts": {},
            "noise_class_entry_count": 0,
        }

    rows = [e for e in entries if isinstance(e, dict)]
    if not rows:
        return {
            "entry_count": 0,
            "top1_retrieval_score": None,
            "retrieval_score_min": None,
            "retrieval_score_max": None,
            "retrieval_score_spread": 0,
            "snippet_anchor_hits": 0,
            "snippet_non_anchor_hits": 0,
            "file_class_counts": {},
            "noise_class_entry_count": 0,
        }

    ordered = sorted(rows, key=lambda e: int(e.get("rank", 0)))
    scores: List[int] = []
    anchor_hits = 0
    non_anchor = 0
    class_counts: Dict[str, int] = {}
    noise_entries = 0

    for ent in ordered:
        rs = ent.get("retrieval_score")
        if isinstance(rs, (int, float)):
            scores.append(int(rs))

        rel = str(ent.get("relative_path") or "")
        fclass = classify_file(rel).file_class
        class_counts[fclass] = class_counts.get(fclass, 0) + 1
        if is_noise_class(fclass):
            noise_entries += 1

        snip = ent.get("snippet")
        if isinstance(snip, dict):
            reason = str(snip.get("selection_reason") or "")
            if reason == _ANCHOR:
                anchor_hits += 1
            else:
                non_anchor += 1

    top1 = scores[0] if scores else None
    rmin = min(scores) if scores else None
    rmax = max(scores) if scores else None
    spread = (rmax - rmin) if scores and len(scores) > 1 else 0

    return {
        "entry_count": len(ordered),
        "top1_retrieval_score": top1,
        "retrieval_score_min": rmin,
        "retrieval_score_max": rmax,
        "retrieval_score_spread": spread,
        "snippet_anchor_hits": anchor_hits,
        "snippet_non_anchor_hits": non_anchor,
        "file_class_counts": class_counts,
        "noise_class_entry_count": noise_entries,
    }

"""
Deterministic, evidence-bundle-level signals for retrieval usefulness (Plan-Gate metadata).

Uses the same path classification as the quality gate so operators can compare
``usefulness_metrics`` with ``dominance_metrics`` without a second policy.
"""

from __future__ import annotations

from typing import Any, Dict, List

from runtime.layer5.evidence.snippet_anchor_quality import classify_visible_snippet_kind
from runtime.layer5.retrieval.policy import classify_file, is_noise_class

_ANCHOR = "query_token_substring_anchor"


def _empty_metrics() -> Dict[str, Any]:
    return {
        "entry_count": 0,
        "top1_retrieval_score": None,
        "retrieval_score_min": None,
        "retrieval_score_max": None,
        "retrieval_score_spread": 0,
        "retrieval_score_sum": 0,
        "top1_score_share": None,
        "snippet_anchor_hits": 0,
        "snippet_non_anchor_hits": 0,
        "snippet_visible_header_boilerplate": 0,
        "snippet_visible_domain_body": 0,
        "snippet_visible_mixed_or_weak": 0,
        "header_anchor_rate": 0.0,
        "domain_anchor_rate": 0.0,
        "file_class_counts": {},
        "noise_class_entry_count": 0,
    }


def bundle_usefulness_metrics(entries: List[Any]) -> Dict[str, Any]:
    """
    Summarize evidence_bundle.entries for operator-facing diagnostics.

    Safe on partial or empty input: returns zeros / empty dicts without raising.
    """
    if not isinstance(entries, list) or not entries:
        return _empty_metrics()

    rows = [e for e in entries if isinstance(e, dict)]
    if not rows:
        return _empty_metrics()

    ordered = sorted(rows, key=lambda e: int(e.get("rank", 0)))
    scores: List[int] = []
    anchor_hits = 0
    non_anchor = 0
    vis_header = 0
    vis_domain = 0
    vis_mixed = 0
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
            txt = str(snip.get("text") or "")
            kind = classify_visible_snippet_kind(txt)
            if kind == "header_boilerplate":
                vis_header += 1
            elif kind == "domain_body":
                vis_domain += 1
            else:
                vis_mixed += 1

    top1 = scores[0] if scores else None
    rmin = min(scores) if scores else None
    rmax = max(scores) if scores else None
    spread = (rmax - rmin) if scores and len(scores) > 1 else 0
    score_sum = sum(scores) if scores else 0
    n = len(ordered)
    share = (float(top1) / float(score_sum)) if (top1 is not None and score_sum > 0) else None

    return {
        "entry_count": n,
        "top1_retrieval_score": top1,
        "retrieval_score_min": rmin,
        "retrieval_score_max": rmax,
        "retrieval_score_spread": spread,
        "retrieval_score_sum": score_sum,
        "top1_score_share": round(share, 6) if share is not None else None,
        "snippet_anchor_hits": anchor_hits,
        "snippet_non_anchor_hits": non_anchor,
        "snippet_visible_header_boilerplate": vis_header,
        "snippet_visible_domain_body": vis_domain,
        "snippet_visible_mixed_or_weak": vis_mixed,
        "header_anchor_rate": round(vis_header / n, 4) if n else 0.0,
        "domain_anchor_rate": round(vis_domain / n, 4) if n else 0.0,
        "file_class_counts": class_counts,
        "noise_class_entry_count": noise_entries,
    }

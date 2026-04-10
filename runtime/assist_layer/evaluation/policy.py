from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _verdict_counts(runs: Iterable[Dict[str, Any]]) -> Counter:
    c: Counter = Counter()
    for run in runs:
        c[str(run.get("final_verdict") or "unknown")] += 1
    return c


def generate_confidence_policy(
    summary: Dict[str, Any],
    runs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    by_transform = summary.get("counts_by_transform_code") or {}
    by_category = summary.get("counts_by_query_category") or {}

    safe: List[str] = []
    caution: List[str] = []
    block: List[str] = []

    for transform, stats in sorted(by_transform.items()):
        total = int(stats.get("total", 0))
        if total == 0:
            continue
        major = int(stats.get("degraded_major", 0))
        minor = int(stats.get("degraded_minor", 0))
        improved = int(stats.get("improved", 0))

        major_rate = major / total
        minor_rate = minor / total
        improved_rate = improved / total

        if major_rate >= 0.20:
            block.append(transform)
        elif major_rate > 0 or minor_rate >= 0.35:
            caution.append(transform)
        elif improved_rate >= 0.20 and minor_rate <= 0.10:
            safe.append(transform)
        else:
            caution.append(transform)

    blocked_conditions: List[str] = []
    for category, stats in sorted(by_category.items()):
        total = int(stats.get("total", 0))
        if total <= 0:
            continue
        major = int(stats.get("degraded_major", 0))
        if (major / total) >= 0.30:
            blocked_conditions.append(f"avoid influence for category={category} due to high degraded_major ratio")

    notes = [
        "Policy is evidence-derived from shadow evaluation runs only.",
        "This artifact is advisory and not runtime-enforced in this pass.",
        "Transform mapping should be regenerated after each benchmark batch.",
    ]

    return {
        "schema_version": "assist_confidence_policy.v1",
        "trust_zones": ["safe", "caution", "block"],
        "safe_transforms": sorted(set(safe)),
        "caution_transforms": sorted(set(caution) - set(safe) - set(block)),
        "blocked_transforms_or_conditions": {
            "transforms": sorted(set(block)),
            "conditions": blocked_conditions,
        },
        "degradation_thresholds": {
            "block_major_ratio_gte": 0.20,
            "caution_minor_ratio_gte": 0.35,
            "category_block_major_ratio_gte": 0.30,
        },
        "evidence_snapshot": {
            "total_runs": int(summary.get("total_runs", 0)),
            "verdict_counts": dict(_verdict_counts(runs)),
        },
        "notes": notes,
    }

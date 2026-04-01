from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from runtime.layer5.audit.l58_evaluator import EvaluatedCase, PR6ProtectedMetrics


@dataclass(frozen=True)
class DriftResult:
    hard_failures: List[str]
    warnings: List[str]
    metrics: Dict[str, float]

    @property
    def passed(self) -> bool:
        return not self.hard_failures


def evaluate_drifts(
    cases: List[EvaluatedCase],
    pr6: PR6ProtectedMetrics,
    thresholds: Dict[str, Dict[str, float]],
) -> DriftResult:
    hard: List[str] = []
    warnings: List[str] = []

    total = max(1, len(cases))
    owner_drift_rate = sum(1 for c in cases if "owner_miss_top1" in c.hard_fail_reasons) / total
    anchor_drift_rate = sum(1 for c in cases if "anchor_miss_top3" in c.hard_fail_reasons) / total
    evidence_drift_rate = sum(1 for c in cases if "evidence_drift" in c.hard_fail_reasons) / total
    noise_regression_rate = sum(1 for c in cases if "noise_dominance_regression" in c.hard_fail_reasons) / total
    latency_vals = sorted(c.latency_ms for c in cases)
    p95_idx = max(0, int(len(latency_vals) * 0.95) - 1)
    latency_p95 = latency_vals[p95_idx] if latency_vals else 0.0
    no_match_cases = [c for c in cases if c.no_match_honesty_ok or "no_match_honesty_failure" in c.hard_fail_reasons]
    no_match_honesty_precision = (
        sum(1 for c in no_match_cases if c.no_match_honesty_ok) / len(no_match_cases)
        if no_match_cases
        else 1.0
    )

    metrics = {
        "owner_drift_rate": owner_drift_rate,
        "anchor_drift_rate": anchor_drift_rate,
        "evidence_drift_rate": evidence_drift_rate,
        "noise_regression_rate": noise_regression_rate,
        "latency_p95_ms": latency_p95,
        "no_match_honesty_precision": no_match_honesty_precision,
    }

    if pr6.hard_failures:
        hard.extend([f"pr6_invariant:{x}" for x in pr6.hard_failures])

    # max-based metrics
    for key, metric_name in (
        ("max_owner_drift_rate", "owner_drift_rate"),
        ("max_anchor_drift_rate", "anchor_drift_rate"),
        ("max_evidence_drift_rate", "evidence_drift_rate"),
        ("max_noise_regression_rate", "noise_regression_rate"),
        ("max_latency_p95_ms", "latency_p95_ms"),
    ):
        value = metrics[metric_name]
        hard_threshold = thresholds["hard_fail"][key]
        warn_threshold = thresholds["warning"][key]
        if value > hard_threshold:
            hard.append(f"{metric_name}={value:.4f}>hard({hard_threshold:.4f})")
        elif value > warn_threshold:
            warnings.append(f"{metric_name}={value:.4f}>warn({warn_threshold:.4f})")

    # min-based metric
    hm = thresholds["hard_fail"]["min_no_match_honesty_precision"]
    wm = thresholds["warning"]["min_no_match_honesty_precision"]
    nh = metrics["no_match_honesty_precision"]
    if nh < hm:
        hard.append(f"no_match_honesty_precision={nh:.4f}<hard({hm:.4f})")
    elif nh < wm:
        warnings.append(f"no_match_honesty_precision={nh:.4f}<warn({wm:.4f})")

    return DriftResult(hard_failures=hard, warnings=warnings, metrics=metrics)

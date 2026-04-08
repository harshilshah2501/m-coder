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
    owner_cases = [c for c in cases if c.must_hit_top1_owner]
    anchor_cases = [c for c in cases if c.must_hit_top3_anchor]
    owner_drift_rate = (
        sum(1 for c in owner_cases if "owner_miss_top1" in c.hard_fail_reasons) / len(owner_cases)
        if owner_cases
        else 0.0
    )
    anchor_drift_rate = (
        sum(1 for c in anchor_cases if "anchor_miss_top3" in c.hard_fail_reasons) / len(anchor_cases)
        if anchor_cases
        else 0.0
    )
    evidence_drift_rate = sum(1 for c in cases if "evidence_drift" in c.hard_fail_reasons) / total
    noise_regression_rate = sum(1 for c in cases if "noise_dominance_regression" in c.hard_fail_reasons) / total
    top1_owner_accuracy = (
        sum(1 for c in owner_cases if c.top1_owner_match) / len(owner_cases)
        if owner_cases
        else 1.0
    )
    top3_anchor_hit_rate = (
        sum(1 for c in anchor_cases if c.top3_anchor_hit) / len(anchor_cases)
        if anchor_cases
        else 1.0
    )
    known_first_ranks = [c.first_relevant_rank for c in cases if c.first_relevant_rank is not None]
    mean_first_relevant_rank = (
        sum(known_first_ranks) / len(known_first_ranks) if known_first_ranks else float("inf")
    )
    mean_noise_dominance_top5 = sum(c.noise_dominance_top5 for c in cases) / total
    mean_code_ratio_topk = sum(c.code_ratio_topk for c in cases) / total
    weak_cases = [c for c in cases if c.expected_evidence_primary == "WEAK"]
    weak_evidence_precision = (
        sum(1 for c in weak_cases if c.predicted_evidence_class == "WEAK") / len(weak_cases)
        if weak_cases
        else 1.0
    )
    latency_vals = sorted(c.latency_ms for c in cases)
    p95_idx = max(0, int(len(latency_vals) * 0.95) - 1)
    latency_p95 = latency_vals[p95_idx] if latency_vals else 0.0
    no_match_cases = [c for c in cases if c.expect_no_match_honesty]
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
        "top1_owner_accuracy": top1_owner_accuracy,
        "top3_anchor_hit_rate": top3_anchor_hit_rate,
        "mean_first_relevant_rank": mean_first_relevant_rank,
        "mean_noise_dominance_top5": mean_noise_dominance_top5,
        "mean_code_ratio_topk": mean_code_ratio_topk,
        "weak_evidence_precision": weak_evidence_precision,
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

    for key, metric_name in (
        ("max_mean_first_relevant_rank", "mean_first_relevant_rank"),
        ("max_mean_noise_dominance_top5", "mean_noise_dominance_top5"),
    ):
        if key not in thresholds["hard_fail"] or key not in thresholds["warning"]:
            continue
        value = metrics[metric_name]
        hard_threshold = thresholds["hard_fail"][key]
        warn_threshold = thresholds["warning"][key]
        if value > hard_threshold:
            hard.append(f"{metric_name}={value:.4f}>hard({hard_threshold:.4f})")
        elif value > warn_threshold:
            warnings.append(f"{metric_name}={value:.4f}>warn({warn_threshold:.4f})")

    # min-based metric
    for key, metric_name in (
        ("min_no_match_honesty_precision", "no_match_honesty_precision"),
        ("min_top1_owner_accuracy", "top1_owner_accuracy"),
        ("min_top3_anchor_hit_rate", "top3_anchor_hit_rate"),
        ("min_mean_code_ratio_topk", "mean_code_ratio_topk"),
        ("min_weak_evidence_precision", "weak_evidence_precision"),
    ):
        if key not in thresholds["hard_fail"] or key not in thresholds["warning"]:
            continue
        hm = thresholds["hard_fail"][key]
        wm = thresholds["warning"][key]
        val = metrics[metric_name]
        if val < hm:
            hard.append(f"{metric_name}={val:.4f}<hard({hm:.4f})")
        elif val < wm:
            warnings.append(f"{metric_name}={val:.4f}<warn({wm:.4f})")

    return DriftResult(hard_failures=hard, warnings=warnings, metrics=metrics)

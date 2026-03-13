"""
Weekly report generator — Judge Drift Regression Suite v1.1.

Status: STABLE | DRIFT_DETECTED. No printing; structured return only.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from observation.judge_drift_suite.coverage_metrics import (
    compute_guard_coverage,
    compute_min_case_density,
    compute_mutation_coverage,
    compute_phase_coverage,
    compute_surface_coverage,
)
from observation.judge_drift_suite.threshold_loader import load_thresholds

_logger = logging.getLogger(__name__)

STATUS_STABLE = "STABLE"
STATUS_DRIFT = "DRIFT_DETECTED"


def _log_structured(event: str, payload: dict[str, Any]) -> None:
    _logger.info("%s", {"event": event, **payload})


def generate_weekly_report(
    results: dict[str, Any],
    entropy: float,
    baseline_entropy: float | None = None,
) -> dict[str, Any]:
    """
    Build weekly report dict. Status DRIFT_DETECTED if:
    failures > 0, entropy shift > threshold, refusal_accuracy < 0.99,
    collision_accuracy < 0.99, or irreversible_pass_count > 0 (Phase-06 statistical rigor).
    results must contain summary: { total_cases, failures, distribution, judge_version,
    refusal_accuracy, collision_accuracy, irreversible_pass_count }.
    """
    summary = results.get("summary") or {}
    total_cases = summary.get("total_cases", 0)
    failures = summary.get("failures", 0)
    distribution = summary.get("distribution") or {}
    judge_version = summary.get("judge_version", "")
    refusal_accuracy = summary.get("refusal_accuracy", 1.0)
    collision_accuracy = summary.get("collision_accuracy", 1.0)
    irreversible_pass_count = summary.get("irreversible_pass_count", 0)

    results_list = results.get("results") or []
    phase_cov = compute_phase_coverage(results_list)
    guard_cov = compute_guard_coverage(results_list)
    surface_cov = compute_surface_coverage(results_list)
    mutation_cov = compute_mutation_coverage(results_list)
    density = compute_min_case_density(results_list)
    phase_coverage = phase_cov["phase_coverage"]
    guard_coverage = guard_cov["guard_coverage"]
    surface_coverage = surface_cov["surface_coverage"]
    mutation_coverage = mutation_cov["mutation_coverage"]
    min_cases_per_guard = density["min_cases_per_guard"]
    min_cases_per_mutation = density["min_cases_per_mutation"]

    now = datetime.now(timezone.utc)
    week = now.strftime("%Y-W%W")

    th = load_thresholds()
    zero_tol = th.get("zero_tolerance") or {}
    stability = th.get("stability_thresholds") or {}
    refusal_min = stability.get("refusal_accuracy_min", 0.99)
    collision_min = stability.get("collision_accuracy_min", 0.99)
    irreversible_max = zero_tol.get("irreversible_pass", 0)
    max_pct = th.get("entropy_drift_max_percent", 0.10)

    status = STATUS_STABLE
    if failures > 0:
        status = STATUS_DRIFT
    elif irreversible_pass_count > irreversible_max:
        status = STATUS_DRIFT
    elif refusal_accuracy < refusal_min:
        status = STATUS_DRIFT
    elif collision_accuracy < collision_min:
        status = STATUS_DRIFT
    elif phase_coverage < 1.0:
        status = STATUS_DRIFT
    elif guard_coverage < 1.0:
        status = STATUS_DRIFT
    elif mutation_coverage < 1.0:
        status = STATUS_DRIFT
    elif min_cases_per_guard < 1:
        status = STATUS_DRIFT
    elif min_cases_per_mutation < 1:
        status = STATUS_DRIFT
    elif baseline_entropy is not None and baseline_entropy > 0:
        shift = abs(entropy - baseline_entropy)
        if shift / baseline_entropy > max_pct:
            status = STATUS_DRIFT

    out = {
        "week": week,
        "judge_version": judge_version,
        "total_cases": total_cases,
        "failures": failures,
        "entropy": entropy,
        "distribution": dict(distribution),
        "refusal_accuracy": refusal_accuracy,
        "collision_accuracy": collision_accuracy,
        "irreversible_pass_count": irreversible_pass_count,
        "phase_coverage": phase_coverage,
        "guard_coverage": guard_coverage,
        "surface_coverage": surface_coverage,
        "mutation_coverage": mutation_coverage,
        "min_cases_per_guard": min_cases_per_guard,
        "min_cases_per_mutation": min_cases_per_mutation,
        "status": status,
    }
    _log_structured("weekly_report", {"week": week, "status": status, "failures": failures})
    return out

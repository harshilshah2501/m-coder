"""Compare current metrics to baseline and flag drift."""

from __future__ import annotations

DEFAULT_THRESHOLDS = {
    "decision_delta_abs": 0.10,
    "refusal_rate_delta_abs": 0.02,
    "unresolved_lineage_rate_delta_abs": 0.01,
    "blocked_rate_delta_abs": 0.05,
    "crossed_hard_fail": True,
}


def _rate(dist: dict, key: str, total: int) -> float:
    if total == 0:
        return 0.0
    return dist.get(key, 0) / total


def _delta(baseline: float, current: float) -> float:
    return round(current - baseline, 4)


def compare(
    baseline_metrics: dict,
    current_metrics: dict,
    thresholds: dict | None = None,
) -> tuple[list[dict], str, str]:
    """
    Compare current to baseline. Returns (drift_flags, summary_severity, recommendation).
    Severity: OK | WARN | ALERT
    """
    thresholds = thresholds or DEFAULT_THRESHOLDS
    flags = []
    severity = "OK"

    base_total = baseline_metrics.get("items_count", 0) or 1
    curr_total = current_metrics.get("items_count", 0) or 1

    # HARD FAIL: any crossed in shadow
    crossed = current_metrics.get("crossed_count", 0)
    if crossed > 0 and thresholds.get("crossed_hard_fail", True):
        flags.append({
            "metric": "boundary_verdict_crossed",
            "baseline": baseline_metrics.get("crossed_count", 0),
            "current": crossed,
            "delta": crossed,
            "threshold": 0,
            "severity": "HARD_FAIL",
        })
        severity = "ALERT"

    # REFUSAL rate delta
    base_ref = baseline_metrics.get("refusal_rate", 0)
    curr_ref = current_metrics.get("refusal_rate", 0)
    d_ref = _delta(base_ref, curr_ref)
    if d_ref >= thresholds.get("refusal_rate_delta_abs", 0.02):
        flags.append({
            "metric": "refusal_rate",
            "baseline": base_ref,
            "current": curr_ref,
            "delta": d_ref,
            "threshold": thresholds["refusal_rate_delta_abs"],
            "severity": "WARN",
        })
        if severity != "ALERT":
            severity = "WARN"

    # Unresolved lineage rate delta
    base_un = baseline_metrics.get("unresolved_lineage_rate", 0)
    curr_un = current_metrics.get("unresolved_lineage_rate", 0)
    d_un = _delta(base_un, curr_un)
    if d_un >= thresholds.get("unresolved_lineage_rate_delta_abs", 0.01):
        flags.append({
            "metric": "unresolved_lineage_rate",
            "baseline": base_un,
            "current": curr_un,
            "delta": d_un,
            "threshold": thresholds["unresolved_lineage_rate_delta_abs"],
            "severity": "WARN",
        })
        if severity != "ALERT":
            severity = "WARN"

    # Blocked rate delta
    base_bl = baseline_metrics.get("blocked_rate", 0)
    curr_bl = current_metrics.get("blocked_rate", 0)
    d_bl = _delta(base_bl, curr_bl)
    if d_bl >= thresholds.get("blocked_rate_delta_abs", 0.05):
        flags.append({
            "metric": "blocked_rate",
            "baseline": base_bl,
            "current": curr_bl,
            "delta": d_bl,
            "threshold": thresholds["blocked_rate_delta_abs"],
            "severity": "WARN",
        })
        if severity != "ALERT":
            severity = "WARN"

    # Decision bucket deltas (any >= 10% absolute)
    base_dec = baseline_metrics.get("by_decision", {})
    curr_dec = current_metrics.get("by_decision", {})
    all_keys = sorted(set(base_dec) | set(curr_dec))
    for k in all_keys:
        br = round(_rate(base_dec, k, base_total), 4)
        cr = round(_rate(curr_dec, k, curr_total), 4)
        d = abs(cr - br)
        if d >= thresholds.get("decision_delta_abs", 0.10):
            flags.append({
                "metric": f"decision_{k}",
                "baseline": br,
                "current": cr,
                "delta": round(cr - br, 4),
                "threshold": thresholds["decision_delta_abs"],
                "severity": "WARN",
            })
            if severity != "ALERT":
                severity = "WARN"

    rec = "Continue monitoring."
    if severity == "ALERT":
        rec = "Trigger GREG audit (Observation signal only; cannot revise doctrine)."
    elif severity == "WARN":
        rec = "Review drift flags. Consider GREG audit if persistent."
    return flags, severity, rec

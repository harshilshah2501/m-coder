"""Build baseline and drift reports."""

from __future__ import annotations

import hashlib
import json


def _fingerprint(metrics: dict) -> str:
    m = {k: v for k, v in metrics.items() if k != "fingerprint"}
    return hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest()


def build_baseline_report(
    items: list[dict],
    files: list[str],
    reconcile_errors: list[dict],
    fixed_time: str | None = None,
) -> dict:
    """Build baseline_report dict."""
    from .metrics import compute_metrics

    metrics = compute_metrics(items)
    fp = _fingerprint(metrics)
    created = fixed_time or "2026-03-01T00:00:00Z"
    report = {
        "schema_version": "observation.baseline_report.v0.1",
        "created_utc": created,
        "input_summary": {"files_count": len(files), "items_count": len(items)},
        "metrics": metrics,
        "integrity": {
            "reconciliation_key": "(request_id, plan_hash)",
            "mismatches_count": len(reconcile_errors),
        },
        "fingerprint": fp,
    }
    return report


def build_drift_report(
    baseline_report: dict,
    current_metrics: dict,
    drift_flags: list[dict],
    severity: str,
    recommendation: str,
    fixed_time: str | None = None,
) -> dict:
    """Build drift_report dict."""
    curr_fp = _fingerprint(current_metrics)
    created = fixed_time or "2026-03-01T00:00:00Z"
    base_metrics = baseline_report.get("metrics", {})
    return {
        "schema_version": "observation.drift_report.v0.1",
        "created_utc": created,
        "baseline_fingerprint": baseline_report.get("fingerprint", ""),
        "current_fingerprint": curr_fp,
        "metrics_current": current_metrics,
        "deltas": {
            "refusal_rate": round(current_metrics.get("refusal_rate", 0) - base_metrics.get("refusal_rate", 0), 4),
            "unresolved_lineage_rate": round(current_metrics.get("unresolved_lineage_rate", 0) - base_metrics.get("unresolved_lineage_rate", 0), 4),
            "blocked_rate": round(current_metrics.get("blocked_rate", 0) - base_metrics.get("blocked_rate", 0), 4),
        },
        "drift_flags": drift_flags,
        "overall_status": severity,
        "recommendation": recommendation,
    }


def baseline_report_to_md(report: dict) -> str:
    lines = [
        "# Baseline Report v0.1",
        "",
        f"**Created:** {report['created_utc']}",
        f"**Items:** {report['input_summary']['items_count']}",
        f"**Files:** {report['input_summary']['files_count']}",
        "",
        "## Metrics",
        "",
    ]
    for k, v in report.get("metrics", {}).items():
        lines.append(f"- {k}: {json.dumps(v)}")
    lines.append("")
    lines.append(f"## Fingerprint: {report.get('fingerprint', '')}")
    return "\n".join(lines)


def drift_report_to_md(report: dict) -> str:
    lines = [
        "# Drift Report v0.1",
        "",
        f"**Status:** {report['overall_status']}",
        f"**Recommendation:** {report['recommendation']}",
        "",
        "## Drift Flags",
        "",
    ]
    for f in report.get("drift_flags", []):
        lines.append(f"- {f.get('metric', '')}: delta={f.get('delta')} (threshold={f.get('threshold')}) [{f.get('severity')}]")
    return "\n".join(lines)

"""Build deterministic observation report."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any


def build_report(
    items: list[dict],
    input_files: list[str],
    reconcile_errors: list[dict],
    fixed_time: str | None = None,
) -> dict:
    """Build report dict. Deterministic when fixed_time is set or no timestamps in counts."""
    by_decision: Counter[str] = Counter()
    by_phase: Counter[str] = Counter()
    by_boundary: Counter[str] = Counter()
    by_authority: Counter[str] = Counter()
    by_reason: Counter[str] = Counter()
    lineage = {"base_id": 0, "variant_id": 0, "freeze_version_id": 0, "model_artifact_id": 0}

    for item in items:
        ledger = item.get("ledger_row", {})
        dec = item.get("decision_response", {})
        v = ledger.get("verdicts", {})
        dec_val = dec.get("decision", "none") if dec else "none"
        by_decision[dec_val] += 1
        by_phase[v.get("phase_emitted", "unknown")] += 1
        by_boundary[v.get("boundary_verdict", "unknown")] += 1
        by_authority[v.get("authority_verdict", "unknown")] += 1
        for rc in ledger.get("reason_codes", []):
            by_reason[rc] += 1
        refs = item.get("lineage_refs") or {}
        if refs.get("base_id"):
            lineage["base_id"] += 1
        if refs.get("variant_id"):
            lineage["variant_id"] += 1
        if refs.get("freeze_version_id"):
            lineage["freeze_version_id"] += 1
        if refs.get("model_artifact_id"):
            lineage["model_artifact_id"] += 1

    samples = reconcile_errors[:10]
    report = {
        "schema_version": "observation.report.v0.1",
        "input_summary": {"files": sorted(input_files), "items_count": len(items)},
        "counts": {
            "by_decision": dict(sorted(by_decision.items())),
            "by_phase_emitted": dict(sorted(by_phase.items())),
            "by_boundary_verdict": dict(sorted(by_boundary.items())),
            "by_authority_verdict": dict(sorted(by_authority.items())),
            "by_reason_code": dict(by_reason.most_common(20)),
        },
        "integrity": {
            "reconciliation_key": "(request_id, plan_hash)",
            "mismatches_count": len(reconcile_errors),
            "mismatches_samples": samples,
        },
        "lineage_links": lineage,
    }
    # Deterministic hash excluding itself
    r2 = {k: v for k, v in report.items()}
    report_bytes = json.dumps(r2, sort_keys=True, ensure_ascii=False).encode("utf-8")
    report["deterministic_hash"] = hashlib.sha256(report_bytes).hexdigest()
    return report


def report_to_md(report: dict) -> str:
    lines = [
        "# Observation Ingest Report v0.1",
        "",
        f"**Items:** {report['input_summary']['items_count']}",
        f"**Files:** {', '.join(report['input_summary']['files'])}",
        "",
        "## Counts",
        "",
        "| Metric | Value |",
        "|--------|-------|",
    ]
    for k, v in report["counts"].items():
        lines.append(f"| {k} | {json.dumps(v)} |")
    lines.extend([
        "",
        "## Integrity",
        "",
        f"- Reconciliation key: {report['integrity']['reconciliation_key']}",
        f"- Mismatches: {report['integrity']['mismatches_count']}",
        "",
        "## Lineage Links",
        "",
        f"- base_id: {report['lineage_links']['base_id']}",
        f"- variant_id: {report['lineage_links']['variant_id']}",
        f"- freeze_version_id: {report['lineage_links']['freeze_version_id']}",
        f"- model_artifact_id: {report['lineage_links']['model_artifact_id']}",
        "",
    ])
    return "\n".join(lines)

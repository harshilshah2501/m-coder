from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List

from runtime.layer5.audit.l58_drift import DriftResult
from runtime.layer5.audit.l58_evaluator import EvaluatedCase, PR6ProtectedMetrics


def _flow_breakdown(cases: List[EvaluatedCase]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for flow in sorted({c.flow_type for c in cases}):
        rows = [c for c in cases if c.flow_type == flow]
        n = max(1, len(rows))
        out[flow] = {
            "count": float(len(rows)),
            "top1_owner_match_rate": sum(1 for r in rows if r.top1_owner_match) / n,
            "top3_anchor_hit_rate": sum(1 for r in rows if r.top3_anchor_hit) / n,
            "avg_noise_dominance_top5": sum(r.noise_dominance_top5 for r in rows) / n,
            "avg_code_ratio_topk": sum(r.code_ratio_topk for r in rows) / n,
        }
    return out


def _evidence_distribution(cases: List[EvaluatedCase]) -> Dict[str, float]:
    n = max(1, len(cases))
    keys = ("STRONG", "WEAK", "INSUFFICIENT", "NO_MATCH")
    return {k: sum(1 for c in cases if c.predicted_evidence_class == k) / n for k in keys}


def build_report_payload(cases: List[EvaluatedCase], pr6: PR6ProtectedMetrics, drift: DriftResult) -> Dict[str, object]:
    n = max(1, len(cases))
    owner_cases = [c for c in cases if c.must_hit_top1_owner]
    anchor_cases = [c for c in cases if c.must_hit_top3_anchor]
    latencies = sorted(c.latency_ms for c in cases)
    p50 = latencies[max(0, int(len(latencies) * 0.50) - 1)] if latencies else 0.0
    p95 = latencies[max(0, int(len(latencies) * 0.95) - 1)] if latencies else 0.0
    first_ranks = [c.first_relevant_rank for c in cases if c.first_relevant_rank is not None]
    weak_cases = [c for c in cases if c.expected_evidence_primary == "WEAK"]
    weak_evidence_precision = (
        sum(1 for c in weak_cases if c.predicted_evidence_class == "WEAK") / len(weak_cases)
        if weak_cases
        else 1.0
    )
    no_match_cases = [c for c in cases if c.expect_no_match_honesty]
    no_match_honesty_precision = (
        sum(1 for c in no_match_cases if c.no_match_honesty_ok) / len(no_match_cases)
        if no_match_cases
        else 1.0
    )
    drift_detection_rate = (
        sum(1 for c in cases if c.hard_fail_reasons) / n
        if cases
        else 0.0
    )
    payload: Dict[str, object] = {
        "total_cases": len(cases),
        "hard_fail_count": len(drift.hard_failures),
        "warning_count": len(drift.warnings),
        "case_pass_rate": sum(1 for c in cases if not c.hard_fail_reasons) / n,
        "pr6_protected_subset": asdict(pr6),
        "drift_metrics": drift.metrics,
        "gate_metrics": {
            "top1_owner_accuracy": (
                sum(1 for c in owner_cases if c.top1_owner_match) / len(owner_cases)
                if owner_cases
                else 1.0
            ),
            "top3_anchor_hit_rate": (
                sum(1 for c in anchor_cases if c.top3_anchor_hit) / len(anchor_cases)
                if anchor_cases
                else 1.0
            ),
            "mean_first_relevant_rank": (sum(first_ranks) / len(first_ranks)) if first_ranks else 0.0,
            "mean_noise_dominance_top5": sum(c.noise_dominance_top5 for c in cases) / n,
            "mean_code_ratio_topk": sum(c.code_ratio_topk for c in cases) / n,
            "weak_evidence_precision": weak_evidence_precision,
            "no_match_honesty_precision": no_match_honesty_precision,
            "drift_detection_rate": drift_detection_rate,
        },
        "flow_breakdown": _flow_breakdown(cases),
        "evidence_distribution": _evidence_distribution(cases),
        "latency": {
            "p50_ms": p50,
            "p95_ms": p95,
            "max_ms": max(latencies) if latencies else 0.0,
        },
        "worst_regressions": [
            {
                "case_id": c.case_id,
                "hard_fail_reasons": c.hard_fail_reasons,
            }
            for c in cases
            if c.hard_fail_reasons
        ][:10],
    }
    return payload


def write_reports(
    cases: List[EvaluatedCase],
    pr6: PR6ProtectedMetrics,
    drift: DriftResult,
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_report_payload(cases, pr6, drift)
    json_path = output_dir / "l58_grounded_report.json"
    md_path = output_dir / "l58_grounded_report.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines: List[str] = []
    lines.append("# L5.8 Grounded Validation Report\n\n")
    lines.append(f"- Total cases: {payload['total_cases']}\n")
    lines.append(f"- Hard failures: {payload['hard_fail_count']}\n")
    lines.append(f"- Warnings: {payload['warning_count']}\n")
    lines.append(f"- Case pass rate: {payload['case_pass_rate']:.2%}\n\n")
    lines.append("## PR-6 protected subset\n\n")
    lines.append(f"- top1: {pr6.top1_hits}/{pr6.total}\n")
    lines.append(f"- top3: {pr6.top3_hits}/{pr6.total}\n")
    lines.append(f"- mean first relevant rank: {pr6.mean_first_relevant_rank:.2f}\n")
    lines.append(f"- mean noise dominance top5: {pr6.mean_noise_dominance_top5:.2f}\n")
    if pr6.hard_failures:
        lines.append(f"- failures: {pr6.hard_failures}\n")
    lines.append("\n## Flow breakdown\n\n")
    for flow, row in payload["flow_breakdown"].items():
        lines.append(
            f"- {flow}: count={int(row['count'])}, top1={row['top1_owner_match_rate']:.2%}, "
            f"top3={row['top3_anchor_hit_rate']:.2%}, noise={row['avg_noise_dominance_top5']:.2f}, "
            f"code_ratio={row['avg_code_ratio_topk']:.2f}\n"
        )
    lines.append("\n## Drift\n\n")
    for reason in drift.hard_failures:
        lines.append(f"- HARD: {reason}\n")
    for reason in drift.warnings:
        lines.append(f"- WARN: {reason}\n")
    lines.append("\n## Gate metrics\n\n")
    for k, v in payload["gate_metrics"].items():
        lines.append(f"- {k}: {v:.4f}\n")
    lines.append("\n## Evidence distribution\n\n")
    for k, v in payload["evidence_distribution"].items():
        lines.append(f"- {k}: {v:.2%}\n")
    md_path.write_text("".join(lines), encoding="utf-8")
    return json_path, md_path

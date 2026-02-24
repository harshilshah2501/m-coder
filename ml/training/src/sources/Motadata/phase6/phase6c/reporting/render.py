from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ..metrics.types import LedgerRow


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _time_range(rows: List[LedgerRow]) -> tuple[str | None, str | None]:
    starts: List[datetime] = []
    finishes: List[datetime] = []
    for row in rows:
        s = _parse_iso(row.get("started_at"))
        f = _parse_iso(row.get("finished_at"))
        if s:
            starts.append(s)
        if f:
            finishes.append(f)
    if not starts or not finishes:
        return None, None
    return min(starts).isoformat(), max(finishes).isoformat()


def write_summary_json(
    out_dir: str | Path,
    ledger_path: str | Path,
    rows: List[LedgerRow],
    corpus_stats: Dict[str, Any],
    gates: Dict[str, Any],
    clusters_summary: Dict[str, Any] | None = None,
) -> Path:
    out_path = Path(out_dir) / "summary.json"
    start_ts, end_ts = _time_range(rows)
    payload: Dict[str, Any] = {
        "ledger_path": str(ledger_path),
        "n_runs": corpus_stats.get("n_runs", 0),
        "time_range": {"start": start_ts, "end": end_ts},
        "corpus_stats": corpus_stats,
        "gates": gates,
    }
    if clusters_summary is not None:
        payload["clusters"] = clusters_summary
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def write_hot_clusters_jsonl(
    out_dir: str | Path,
    hot_clusters: List[Dict[str, Any]],
) -> Path:
    out_path = Path(out_dir) / "hot_clusters.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for c in hot_clusters:
            f.write(json.dumps(c) + "\n")
    return out_path


def write_markdown_report(
    out_dir: str | Path,
    ledger_path: str | Path,
    title: str,
    rows: List[LedgerRow],
    corpus_stats: Dict[str, Any],
    gates: Dict[str, Any],
    clusters: Dict[Any, Dict[str, Any]],
    hot_clusters: List[Dict[str, Any]],
    low_sample_clusters: List[Dict[str, Any]],
    plot_paths: Dict[str, str],
    plot_warnings: List[str],
) -> Path:
    out_path = Path(out_dir) / "Phase6C_Report.md"
    start_ts, end_ts = _time_range(rows)

    n_runs = corpus_stats.get("n_runs", 0)
    bda_pcts = corpus_stats.get("BDA_norm_percentiles", {}) or {}
    severity_counts = corpus_stats.get("severity_counts", {}) or {}

    tier2 = gates.get("tier2", {})
    tier3 = gates.get("tier3", {})
    meta = gates.get("meta", {}) or {}

    lines: List[str] = []
    lines.append(f"## {title}")
    lines.append("")
    lines.append("### Run metadata")
    lines.append(f"- **Input ledger**: `{ledger_path}`")
    lines.append(f"- **Total runs**: {n_runs}")
    lines.append(f"- **Time range**: {start_ts or 'n/a'} → {end_ts or 'n/a'}")
    lines.append(f"- **Canonical runs**: {meta.get('canonical_runs_count', 'n/a')}")
    lines.append(f"- **Stress-only runs**: {meta.get('stress_runs_count', 0)}")
    if not meta.get("has_stress_labels", False):
        lines.append(
            "- **Note**: Ledger does not label stress-only runs; all runs are treated as canonical."
        )
    lines.append("")

    lines.append("### Gate evaluation (Tier-2 / Tier-3)")
    lines.append(f"- **Tier-2**: {'PASS' if tier2.get('pass') else 'FAIL'}")
    if tier2.get("failed"):
        lines.append(f"  - Failed gates: {', '.join(tier2['failed'])}")
    lines.append(f"- **Tier-3**: {'PASS' if tier3.get('pass') else 'FAIL'}")
    if tier3.get("failed"):
        lines.append(f"  - Failed gates: {', '.join(tier3['failed'])}")
    lines.append("")

    lines.append("### Corpus metrics")
    lines.append(f"- **Severity counts**: {severity_counts}")
    fail_rate = corpus_stats.get("fail_rate_ge_S2", 0.0) or 0.0
    if n_runs:
        lines.append(f"- **fail_rate(≥S2)**: {fail_rate:.3f}")
    else:
        lines.append("- **fail_rate(≥S2)**: n/a")
    lines.append(f"- **S3 runs**: {corpus_stats.get('S3_count', 0)}")
    lines.append("- **BDA_norm percentiles**:")
    for key in ("p50", "p90", "p95", "p99"):
        v = bda_pcts.get(key)
        if v is None:
            lines.append(f"  - {key}: n/a")
        else:
            lines.append(f"  - {key}: {v:.3f}")
    lines.append(f"- **CODE erosion runs**: {corpus_stats.get('code_erosion_runs', 0)}")
    lines.append(f"- **MIX flip rate**: {corpus_stats.get('mix_flip_rate', 0.0):.3f}")
    lines.append("")

    # Cluster coverage
    total_clusters = len(clusters)
    runs_per_cluster = [c.get("runs", 0) for c in clusters.values()]
    clusters_ge_min = sum(
        1 for c in clusters.values() if (c.get("runs") or 0) >= 5
    )
    singletons = sum(1 for r in runs_per_cluster if r == 1)
    median_runs = None
    if runs_per_cluster:
        sorted_runs = sorted(runs_per_cluster)
        mid = len(sorted_runs) // 2
        if len(sorted_runs) % 2 == 1:
            median_runs = float(sorted_runs[mid])
        else:
            median_runs = 0.5 * (sorted_runs[mid - 1] + sorted_runs[mid])

    lines.append("### Cluster coverage")
    lines.append(f"- **Total clusters**: {total_clusters}")
    lines.append(f"- **Clusters with runs ≥ 5**: {clusters_ge_min}")
    if median_runs is not None:
        lines.append(f"- **Median runs per cluster**: {median_runs:.1f}")
    else:
        lines.append("- **Median runs per cluster**: n/a")
    pct_singletons = (singletons / total_clusters) * 100.0 if total_clusters else 0.0
    lines.append(f"- **% clusters with runs == 1**: {pct_singletons:.1f}%")
    lines.append(
        "- Hot-cluster analysis is low-confidence when most clusters have runs==1; "
        "increase repeats or use M6 amplification."
    )
    lines.append("")

    # Collapse labels overall
    collapse_counts = corpus_stats.get("collapse_label_counts", {}) or {}
    if collapse_counts:
        lines.append("### Top failure modes (collapse labels)")
        sorted_labs = sorted(
            collapse_counts.items(), key=lambda kv: kv[1], reverse=True
        )
        for lab, count in sorted_labs[:5]:
            lines.append(f"- **{lab}**: {count}")
        lines.append("")

    # Top hot clusters
    lines.append("### Top hot clusters")
    if not hot_clusters:
        lines.append("- **None** (no hot clusters detected)")
    else:
        for c in hot_clusters[:5]:
            key = c.get("key", {})
            key_str = (
                f"{key.get('seed_id') or '?'} | "
                f"{key.get('injection_profile') or '?'} | "
                f"{key.get('carryover_mode') or '?'} | "
                f"{key.get('shape') or '?'} | "
                f"N={key.get('horizon_N')}"
            )
            lines.append(
                f"- **{key_str}**: "
                f"runs={c.get('runs')}, "
                f"fail_rate(≥S2)={c.get('fail_rate_ge_S2', 0.0):.3f}, "
                f"S3={c.get('S3_count', 0)}, "
                f"BDA_norm_p95={c.get('BDA_norm_p95')}, "
                f"risk={c.get('risk_score', 0.0):.3f}"
            )
    lines.append("")

    # Low-sample risk clusters (runs < 5)
    if low_sample_clusters:
        lines.append("### Low-sample risk signals (runs < 5)")
        for c in low_sample_clusters[:10]:
            key = c.get("key", {})
            key_str = (
                f"{key.get('seed_id') or '?'} | "
                f"{key.get('injection_profile') or '?'} | "
                f"{key.get('carryover_mode') or '?'} | "
                f"{key.get('shape') or '?'} | "
                f"N={key.get('horizon_N')}"
            )
            lines.append(
                f"- **{key_str}**: "
                f"runs={c.get('runs')}, "
                f"fail_rate(≥S2)={c.get('fail_rate_ge_S2', 0.0):.3f}, "
                f"S3={c.get('S3_count', 0)}, "
                f"BDA_norm_p95={c.get('BDA_norm_p95')}, "
                f"risk={c.get('risk_score', 0.0):.3f}, "
                f"confidence=low"
            )
        lines.append(
            "- Recommendation: Increase repeats or enable amplification (M6) for these clusters."
        )
        lines.append("")

    # Next actions: focus on top hot clusters
    lines.append("### Next Actions")
    if not hot_clusters:
        lines.append("- **Monitor**: No hot clusters yet; continue sampling.")
    else:
        lines.append(
            "- **Focus**: Investigate the following high-risk clusters "
            "(seeds × injection_profile × carryover):"
        )
        for c in hot_clusters[:5]:
            key = c.get("key", {})
            lines.append(
                f"  - `{key.get('seed_id')}` / `{key.get('injection_profile')}` / "
                f"`{key.get('carryover_mode')}` / `{key.get('shape')}` / "
                f"N={key.get('horizon_N')}"
            )
    lines.append("")

    # Plots section
    lines.append("### Plots")
    if not plot_paths and not plot_warnings:
        lines.append("- No plots generated.")
    else:
        for name, path in plot_paths.items():
            rel = Path(path).as_posix()
            lines.append(f"- **{name}**: `{rel}`")
        for w in plot_warnings:
            lines.append(f"- {w}")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


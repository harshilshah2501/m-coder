from __future__ import annotations

import argparse
from pathlib import Path

from ..metrics.types import LedgerRow
from . import clusters, gates, load, plots, render, stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase-6C reporting and visualization (M5).",
    )
    parser.add_argument(
        "--ledger",
        type=str,
        required=True,
        help="Path to phase6c_ledger.jsonl",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output directory for report and plots",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Phase-6C Report",
        help="Report title (markdown heading)",
    )
    args = parser.parse_args()

    ledger_path = Path(args.ledger)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[LedgerRow] = load.load_ledger(ledger_path)

    corpus_stats = stats.compute_corpus_stats(rows)
    gate_results = gates.evaluate_gates(rows)
    cluster_stats = clusters.aggregate_clusters(rows)
    hot_clusters, low_sample_clusters = clusters.find_hot_clusters(cluster_stats)

    plot_paths, plot_warnings = plots.make_all_plots(rows, str(out_dir))

    # Summaries
    render.write_summary_json(
        out_dir,
        ledger_path,
        rows,
        corpus_stats,
        gate_results,
        clusters_summary={
            "total_clusters": len(cluster_stats),
            "hot_clusters": len(hot_clusters),
            "low_sample_clusters": len(low_sample_clusters),
        },
    )
    render.write_hot_clusters_jsonl(out_dir, hot_clusters)
    render.write_markdown_report(
        out_dir,
        ledger_path,
        args.title,
        rows,
        corpus_stats,
        gate_results,
        cluster_stats,
        hot_clusters,
        low_sample_clusters,
        plot_paths,
        plot_warnings,
    )

    # Console summary
    n_runs = corpus_stats.get("n_runs", 0)
    fail_rate = corpus_stats.get("fail_rate_ge_S2", 0.0) or 0.0
    s3_count = corpus_stats.get("S3_count", 0)
    bda_pcts = corpus_stats.get("BDA_norm_percentiles", {}) or {}
    bda_p95 = bda_pcts.get("p95")
    tier2_pass = gate_results.get("tier2", {}).get("pass", False)
    tier3_pass = gate_results.get("tier3", {}).get("pass", False)

    print(f"Runs: {n_runs}")
    print(f"fail_rate(>=S2): {fail_rate:.3f}")
    print(f"S3 count: {s3_count}")
    print(
        f"BDA_norm p95: {bda_p95:.3f}" if isinstance(bda_p95, (int, float)) else "BDA_norm p95: n/a"
    )
    print(f"Tier-2: {'PASS' if tier2_pass else 'FAIL'}")
    print(f"Tier-3: {'PASS' if tier3_pass else 'FAIL'}")

    # Cluster coverage diagnostics
    total_clusters = len(cluster_stats)
    runs_per_cluster = [c.get("runs", 0) for c in cluster_stats.values()]
    clusters_ge_min = sum(
        1 for c in cluster_stats.values() if (c.get("runs") or 0) >= clusters.MIN_CLUSTER_RUNS_FOR_HOT
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
    pct_singletons = (singletons / total_clusters) * 100.0 if total_clusters else 0.0

    print(f"Clusters: {total_clusters} total, {clusters_ge_min} with runs >= {clusters.MIN_CLUSTER_RUNS_FOR_HOT}")
    if median_runs is not None:
        print(f"Median runs per cluster: {median_runs:.1f}")
    print(f"% clusters with runs == 1: {pct_singletons:.1f}%")
    print()

    # Hot clusters block
    if hot_clusters:
        print("Top hot clusters:")
        for c in hot_clusters[:3]:
            key = c.get("key", {})
            key_str = (
                f"{key.get('seed_id') or '?'} / "
                f"{key.get('injection_profile') or '?'} / "
                f"{key.get('carryover_mode') or '?'} / "
                f"{key.get('shape') or '?'} / "
                f"N={key.get('horizon_N')}"
            )
            print(
                f"  - {key_str} | "
                f"fail_rate(>=S2)={c.get('fail_rate_ge_S2', 0.0):.3f}, "
                f"S3={c.get('S3_count', 0)}, "
                f"BDA_norm_p95={c.get('BDA_norm_p95')}, "
                f"risk={c.get('risk_score', 0.0):.3f}"
            )
    else:
        print("No hot clusters detected.")

    # Low-sample risk signals block (independent of hot clusters)
    if low_sample_clusters:
        print()
        print(f"Low-sample risk signals (runs < {clusters.MIN_CLUSTER_RUNS_FOR_HOT}):")
        for c in low_sample_clusters[:10]:
            key = c.get("key", {})
            key_str = (
                f"{key.get('seed_id') or '?'} / "
                f"{key.get('injection_profile') or '?'} / "
                f"{key.get('carryover_mode') or '?'} / "
                f"{key.get('shape') or '?'} / "
                f"N={key.get('horizon_N')}"
            )
            print(
                f"  - {key_str} | "
                f"fail_rate(>=S2)={c.get('fail_rate_ge_S2', 0.0):.3f}, "
                f"S3={c.get('S3_count', 0)}, "
                f"BDA_norm_p95={c.get('BDA_norm_p95')}, "
                f"risk={c.get('risk_score', 0.0):.3f}, "
                f"confidence=low"
            )
        print("Recommendation: Increase repeats or enable amplification (M6).")



if __name__ == "__main__":
    main()


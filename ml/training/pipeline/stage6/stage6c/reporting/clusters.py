from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

from ..metrics.types import LedgerRow
from .load import normalize_carryover, normalize_injection_profile
from .stats import (
    _collect_bda_norm,
    _severity_counts,
    _tmcr_ge_s2,
    _code_erosion_runs,
    _mix_flip_runs,
    _collapse_label_counts,
)


ClusterKey = Tuple[str, str, str, str, int]  # (seed_id, injection_profile, carryover, shape, horizon_N)

# Minimum runs required before treating a cluster as "hot" (high-confidence).
MIN_CLUSTER_RUNS_FOR_HOT = 5


def make_cluster_key(row: LedgerRow) -> ClusterKey:
    seed = row.get("seed_id") or ""
    inj = normalize_injection_profile(row) or ""
    carry = normalize_carryover(row) or ""
    shape = row.get("shape") or ""
    N = int(row.get("horizon_N") or 0)
    return (seed, inj, carry, shape, N)


def aggregate_clusters(rows: List[LedgerRow]) -> Dict[ClusterKey, Dict[str, Any]]:
    """
    Aggregate per-cluster stats:
      - runs
      - fail_rate(>=S2)
      - S3_count
      - BDA_norm_p95
      - code_erosion_runs
      - mix_flip_rate
      - top_collapse_labels
    """
    buckets: Dict[ClusterKey, List[LedgerRow]] = defaultdict(list)
    for row in rows:
        key = make_cluster_key(row)
        buckets[key].append(row)

    clusters: Dict[ClusterKey, Dict[str, Any]] = {}
    for key, group in buckets.items():
        sev_counts = _severity_counts(group)
        bda_vals = _collect_bda_norm(group)
        s3_count = sev_counts.get("S3", 0)
        tmcr = _tmcr_ge_s2(sev_counts)
        bda_p95 = None
        if bda_vals:
            from .stats import _percentile

            bda_p95 = _percentile(bda_vals, 95.0)

        code_eros_runs = _code_erosion_runs(group)
        mix_flips, mix_total = _mix_flip_runs(group)
        mix_flip_rate = (mix_flips / mix_total) if mix_total else 0.0

        collapse_counts: Counter = _collapse_label_counts(group)
        top_labels = [
            lab for lab, _ in collapse_counts.most_common(5)
        ]

        clusters[key] = {
            "key": {
                "seed_id": key[0],
                "injection_profile": key[1],
                "carryover_mode": key[2],
                "shape": key[3],
                "horizon_N": key[4],
            },
            "runs": len(group),
            "fail_rate_ge_S2": tmcr,
            "S3_count": s3_count,
            "BDA_norm_p95": bda_p95,
            "code_erosion_runs": code_eros_runs,
            "mix_flip_rate": mix_flip_rate,
            "top_collapse_labels": top_labels,
        }
    return clusters


def _is_hot_cluster(stats: Dict[str, Any]) -> bool:
    """
    Hot cluster definition (spec-derived):
      - any S3, or
      - code_erosion_runs > 0, or
      - mix_flip_rate > 0, or
      - BDA_norm_p95 > 0.40, or
      - fail_rate(>=S2) > 0.20
    """
    if stats.get("S3_count", 0) > 0:
        return True
    if (stats.get("code_erosion_runs") or 0) > 0:
        return True
    if (stats.get("mix_flip_rate") or 0.0) > 0.0:
        return True
    bda_p95 = stats.get("BDA_norm_p95")
    if bda_p95 is not None and bda_p95 > 0.40:
        return True
    if stats.get("fail_rate_ge_S2", 0.0) > 0.20:
        return True
    return False


def _risk_score(stats: Dict[str, Any]) -> float:
    """
    Heuristic risk score used to sort hot clusters.
    Higher = worse. Weighted by severity rate, erosion, mix flips, and BDA drift.
    """
    tmcr = float(stats.get("fail_rate_ge_S2") or 0.0)
    s3 = int(stats.get("S3_count") or 0)
    runs = int(stats.get("runs") or 1)
    s3_rate = s3 / runs if runs else 0.0
    code_eros_runs = int(stats.get("code_erosion_runs") or 0)
    mix_rate = float(stats.get("mix_flip_rate") or 0.0)
    bda_p95 = stats.get("BDA_norm_p95")
    bda_component = 0.0
    if isinstance(bda_p95, (int, float)):
        # Scale relative to 0.40 reference point.
        bda_component = max(0.0, (bda_p95 - 0.30) / 0.40)
    return (
        3.0 * s3_rate
        + 2.0 * tmcr
        + 1.5 * mix_rate
        + 1.0 * (1.0 if code_eros_runs > 0 else 0.0)
        + 1.0 * bda_component
    )


def find_hot_clusters(
    clusters: Dict[ClusterKey, Dict[str, Any]],
    top_k: int = 20,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter and sort hot clusters.
    Returns a tuple: (hot_clusters, low_sample_risk_clusters).
    - hot_clusters: runs >= MIN_CLUSTER_RUNS_FOR_HOT and hot by _is_hot_cluster
    - low_sample_risk_clusters: runs < MIN_CLUSTER_RUNS_FOR_HOT but flagged
      by _is_hot_cluster, annotated with confidence=\"low\".
    """
    hot: List[Dict[str, Any]] = []
    low_sample: List[Dict[str, Any]] = []
    for stats in clusters.values():
        runs = int(stats.get("runs") or 0)
        if not _is_hot_cluster(stats):
            continue
        enriched = dict(stats)
        enriched["risk_score"] = _risk_score(stats)
        if runs >= MIN_CLUSTER_RUNS_FOR_HOT:
            hot.append(enriched)
        else:
            enriched["confidence"] = "low"
            low_sample.append(enriched)

    hot.sort(key=lambda d: d["risk_score"], reverse=True)
    low_sample.sort(key=lambda d: d["risk_score"], reverse=True)
    return hot[:top_k], low_sample



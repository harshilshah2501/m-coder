from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Tuple

from ..metrics.types import LedgerRow
from .load import normalize_carryover, normalize_injection_profile


def _percentile(values: List[float], q: float) -> float | None:
    """
    Continuous percentile in [0, 1] range for q in [0, 100].
    Returns None if values is empty.
    """
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    rank = (q / 100.0) * (n - 1)
    lo = int(math.floor(rank))
    hi = int(math.ceil(rank))
    if lo == hi:
        return float(sorted_vals[lo])
    frac = rank - lo
    return float(sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo]))


def _collect_bda_norm(rows: Iterable[LedgerRow]) -> List[float]:
    vals: List[float] = []
    for row in rows:
        v = row.get("BDA_norm")
        if isinstance(v, (int, float)):
            vals.append(float(v))
    return vals


def _severity_counts(rows: Iterable[LedgerRow]) -> Counter:
    c: Counter = Counter()
    for row in rows:
        sev = row.get("severity")
        if isinstance(sev, str):
            c[sev] += 1
    return c


def _collapse_label_counts(rows: Iterable[LedgerRow]) -> Counter:
    c: Counter = Counter()
    for row in rows:
        labels = row.get("collapse_labels") or []
        if isinstance(labels, list):
            for lab in labels:
                if isinstance(lab, str):
                    c[lab] += 1
    return c


def _tmcr_ge_s2(severity_counts: Counter) -> float:
    total = sum(severity_counts.values())
    if total == 0:
        return 0.0
    fails = severity_counts.get("S2", 0) + severity_counts.get("S3", 0)
    return fails / total


def _code_erosion_runs(rows: Iterable[LedgerRow]) -> int:
    return sum(1 for row in rows if (row.get("code_fail_closed_erosions") or 0) > 0)


def _mix_flip_runs(rows: Iterable[LedgerRow]) -> Tuple[int, int]:
    total = 0
    flips = 0
    for row in rows:
        total += 1
        if row.get("mix_dominance_flip"):
            flips += 1
    return flips, total


def _breakdown_by(
    rows: Iterable[LedgerRow],
    key_fn,
) -> Dict[Any, Dict[str, Any]]:
    buckets: Dict[Any, List[LedgerRow]] = defaultdict(list)
    for row in rows:
        key = key_fn(row)
        buckets[key].append(row)

    out: Dict[Any, Dict[str, Any]] = {}
    for key, group in buckets.items():
        sev_counts = _severity_counts(group)
        bda_vals = _collect_bda_norm(group)
        s3 = sev_counts.get("S3", 0)
        s2 = sev_counts.get("S2", 0)
        tmcr = _tmcr_ge_s2(sev_counts)
        out[key] = {
            "runs": len(group),
            "severity_counts": dict(sev_counts),
            "fail_rate_ge_S2": tmcr,
            "S3_count": s3,
            "S2_count": s2,
            "BDA_norm_p95": _percentile(bda_vals, 95.0),
        }
    return out


def compute_corpus_stats(rows: List[LedgerRow]) -> Dict[str, Any]:
    """
    Compute corpus-level stats required for M5 reporting.
    Returns a JSON-serializable dict.
    """
    n_runs = len(rows)
    sev_counts = _severity_counts(rows)
    bda_vals = _collect_bda_norm(rows)
    collapse_counts = _collapse_label_counts(rows)

    tmcr = _tmcr_ge_s2(sev_counts)
    s3_count = sev_counts.get("S3", 0)
    s2_count = sev_counts.get("S2", 0)

    flips, flip_total = _mix_flip_runs(rows)
    mix_flip_rate = (flips / flip_total) if flip_total else 0.0
    code_eros = _code_erosion_runs(rows)

    bda_pcts = {
        "p50": _percentile(bda_vals, 50.0),
        "p90": _percentile(bda_vals, 90.0),
        "p95": _percentile(bda_vals, 95.0),
        "p99": _percentile(bda_vals, 99.0),
    }

    total_collapse = sum(collapse_counts.values())
    collapse_rates = {
        lab: (count / total_collapse) if total_collapse else 0.0
        for lab, count in collapse_counts.items()
    }

    # Breakdowns
    by_seed = _breakdown_by(rows, lambda r: r.get("seed_id"))
    by_injection = _breakdown_by(rows, normalize_injection_profile)
    by_carryover = _breakdown_by(rows, normalize_carryover)
    by_horizon = _breakdown_by(rows, lambda r: r.get("horizon_N"))
    by_shape = _breakdown_by(rows, lambda r: r.get("shape"))

    return {
        "n_runs": n_runs,
        "severity_counts": dict(sev_counts),
        "fail_rate_ge_S2": tmcr,
        "S3_count": s3_count,
        "S2_count": s2_count,
        "BDA_norm_percentiles": bda_pcts,
        "code_erosion_runs": code_eros,
        "mix_flip_rate": mix_flip_rate,
        "collapse_label_counts": dict(collapse_counts),
        "collapse_label_rates": collapse_rates,
        "breakdowns": {
            "seed_id": by_seed,
            "injection_profile": by_injection,
            "carryover_mode": by_carryover,
            "horizon_N": by_horizon,
            "shape": by_shape,
        },
    }


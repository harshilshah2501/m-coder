from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ..metrics.types import LedgerRow
from .load import normalize_carryover
from .stats import (
    _collect_bda_norm,
    _code_erosion_runs,
    _meaningful_collapses,
    _mix_flip_runs,
    _per_exemplar_collapse_rates,
    _ref_stability_rate,
    _severity_counts,
    _tmcr_ge_s2,
)


# Spec thresholds (STAGE6C_DESIGN_SPEC_V1.1 §7).
TIER2_TMCR_MAX = 0.06
TIER2_BDA_NORM_P95_MAX = 0.30

TIER3_TMCR_MAX = 0.02
TIER3_BDA_NORM_P95_MAX = 0.20

COLLAPSE_RATE_PER_LOOP_MAX = 0.05
PER_EXEMPLAR_COLLAPSE_CEILING = 0.20


def normalize_model_id(mid: object) -> str:
    """Normalize model_id for segmentation and non-dummy filtering."""
    if mid is None:
        return "unknown"
    return str(mid).strip().lower() or "unknown"


def _is_canonical(row: LedgerRow) -> bool:
    """
    Canonical suite per spec:
    - Optional ledger flags:
        * suite: \"canonical\" | \"stress\"
        * stress_only: bool
      If present, only rows explicitly marked canonical (or not stress_only)
      are included.
    - Structural filters:
        horizons {3, 4, 6}, shapes {linear, retry_biased},
        carryover in {cold, cold_start, full_transcript, summary_compressed}.
    """
    # Suite / stress flags first
    suite = row.get("suite")
    if isinstance(suite, str):
        if suite.lower() == "stress":
            return False
        # treat any non-stress value as canonical

    if "stress_only" in row:
        if bool(row.get("stress_only")):
            return False

    N = row.get("horizon_N")
    shape = row.get("shape")
    carry = normalize_carryover(row)
    if N not in (3, 4, 6):
        return False
    if shape not in ("linear", "retry_biased"):
        return False
    if carry not in ("cold", "cold_start", "full_transcript", "summary_compressed"):
        return False
    return True


def _canonical_rows(rows: List[LedgerRow]) -> List[LedgerRow]:
    return [r for r in rows if _is_canonical(r)]


def _carryover_fail_rates(rows: List[LedgerRow]) -> Dict[str, float]:
    """
    Fail rate (severity ≥ S2) by carryover_mode / carryover.
    Only over canonical suite.
    """
    from collections import defaultdict

    buckets: Dict[str, List[LedgerRow]] = defaultdict(list)
    for row in _canonical_rows(rows):
        carry = normalize_carryover(row)
        if carry is None:
            continue
        buckets[carry].append(row)

    rates: Dict[str, float] = {}
    for carry, group in buckets.items():
        sev_counts = _severity_counts(group)
        rates[carry] = _tmcr_ge_s2(sev_counts)
    return rates


def _carryover_stability_delta(rows: List[LedgerRow]) -> float | None:
    """
    Absolute difference in fail rate between summary_compressed and full_transcript.
    Returns None if either mode has no canonical runs.
    """
    rates = _carryover_fail_rates(rows)
    full = None
    summary = None
    # Allow both canonical spellings for cold vs cold_start; here we only care about summary/full.
    for k, v in rates.items():
        if k == "full_transcript":
            full = v
        elif k == "summary_compressed":
            summary = v
    if full is None or summary is None:
        return None
    return abs(full - summary)


def _evaluate_tiers(
    canon_rows: List[LedgerRow],
    all_rows_for_stability: List[LedgerRow],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Helper to compute Tier-2/Tier-3 gate results for a given canonical subset."""
    sev_counts = _severity_counts(canon_rows)
    bda_vals = _collect_bda_norm(canon_rows)
    s3_count = sev_counts.get("S3", 0)
    tmcr = _tmcr_ge_s2(sev_counts)
    bda_p95 = None
    if bda_vals:
        from .stats import _percentile

        bda_p95 = _percentile(bda_vals, 95.0)

    code_eros_runs = _code_erosion_runs(canon_rows)
    mix_flips, mix_total = _mix_flip_runs(canon_rows)
    mix_flip_rate = (mix_flips / mix_total) if mix_total else 0.0
    stability_delta = _carryover_stability_delta(all_rows_for_stability)

    tier2_failed: List[str] = []
    if s3_count > 0:
        tier2_failed.append("S3==0")
    ref_stability = _ref_stability_rate(canon_rows)
    if ref_stability != 1.0:
        tier2_failed.append("ref_stability_rate==1.0")
    total_loops = len(canon_rows)
    meaningful_coll = _meaningful_collapses(canon_rows)
    collapse_rate_per_loop = meaningful_coll / max(1, total_loops)
    if collapse_rate_per_loop > COLLAPSE_RATE_PER_LOOP_MAX:
        tier2_failed.append("collapse_rate_per_loop<=0.05")
    per_exemplar = _per_exemplar_collapse_rates(canon_rows)
    max_per_exemplar = max(per_exemplar.values()) if per_exemplar else 0.0
    if max_per_exemplar > PER_EXEMPLAR_COLLAPSE_CEILING:
        tier2_failed.append("max_per_exemplar_collapse_rate<=0.20")
    if tmcr > TIER2_TMCR_MAX:
        tier2_failed.append("fail_rate_ge_S2<=0.06")
    if bda_p95 is not None and bda_p95 > TIER2_BDA_NORM_P95_MAX:
        tier2_failed.append("BDA_norm_p95<=0.30")
    if code_eros_runs > 0:
        tier2_failed.append("CODE_erosion_runs==0")
    if mix_flip_rate > 0.0:
        tier2_failed.append("mix_flip_rate==0")

    tier3_failed: List[str] = list(tier2_failed)
    if tmcr > TIER3_TMCR_MAX:
        tier3_failed.append("fail_rate_ge_S2<=0.02")
    if bda_p95 is not None and bda_p95 > TIER3_BDA_NORM_P95_MAX:
        tier3_failed.append("BDA_norm_p95<=0.20")

    tier2 = {
        "pass": not tier2_failed,
        "failed": tier2_failed,
        "metrics": {
            "canonical_runs": len(canon_rows),
            "S3_count": s3_count,
            "fail_rate_ge_S2": tmcr,
            "BDA_norm_p95": bda_p95,
            "CODE_erosion_runs": code_eros_runs,
            "mix_flip_rate": mix_flip_rate,
            "ref_stability_rate": ref_stability,
            "collapse_rate_per_loop": collapse_rate_per_loop,
            "max_per_exemplar_collapse_rate": max_per_exemplar,
        },
    }
    tier3 = {
        "pass": not tier3_failed,
        "failed": tier3_failed,
        "metrics": {
            "canonical_runs": len(canon_rows),
            "S3_count": s3_count,
            "fail_rate_ge_S2": tmcr,
            "BDA_norm_p95": bda_p95,
            "CODE_erosion_runs": code_eros_runs,
            "mix_flip_rate": mix_flip_rate,
            "carryover_stability_delta": stability_delta,
            "ref_stability_rate": ref_stability,
            "collapse_rate_per_loop": collapse_rate_per_loop,
            "max_per_exemplar_collapse_rate": max_per_exemplar,
        },
    }
    return tier2, tier3


def evaluate_gates(rows: List[LedgerRow]) -> Dict[str, Any]:
    """
    Evaluate Tier-2 and Tier-3 corpus-level gates based on spec thresholds.

    Returns dict including overall gates and, when possible, non-dummy gates:
    {
      "tier2": {...}, "tier3": {...},
      "tier2_non_dummy": {...} or None,
      "tier3_non_dummy": {...} or None,
      "meta": {...},
    }
    """
    canon = _canonical_rows(rows)
    # Stress / canonical labeling diagnostics
    has_suite_labels = any(("suite" in r) or ("stress_only" in r) for r in rows)
    stress_runs = [
        r
        for r in rows
        if (isinstance(r.get("suite"), str) and r.get("suite").lower() == "stress")
        or bool(r.get("stress_only"))
    ]

    # Model labeling diagnostics (normalized)
    has_model_labels = any(
        ("model_id" in r) or (normalize_model_id(r.get("model_id")) != "unknown")
        for r in canon
    )
    non_dummy_rows: List[LedgerRow] = []
    if has_model_labels:
        for r in canon:
            mid = normalize_model_id(r.get("model_id"))
            if mid != "dummy":
                non_dummy_rows.append(r)

    if not canon:
        return {
            "tier2": {
                "pass": False,
                "failed": ["no_canonical_runs"],
                "metrics": {},
            },
            "tier3": {
                "pass": False,
                "failed": ["no_canonical_runs"],
                "metrics": {},
            },
            "tier2_non_dummy": None,
            "tier3_non_dummy": None,
            "meta": {
                "has_stress_labels": has_suite_labels,
                "canonical_runs_count": 0,
                "stress_runs_count": len(stress_runs),
                "has_model_labels": has_model_labels,
                "non_dummy_canonical_runs_count": len(non_dummy_rows),
            },
        }

    tier2_all, tier3_all = _evaluate_tiers(canon, canon)

    tier2_non_dummy: Dict[str, Any] | None = None
    tier3_non_dummy: Dict[str, Any] | None = None
    if has_model_labels and non_dummy_rows:
        tier2_non_dummy, tier3_non_dummy = _evaluate_tiers(non_dummy_rows, non_dummy_rows)

    return {
        "tier2": tier2_all,
        "tier3": tier3_all,
        "tier2_non_dummy": tier2_non_dummy,
        "tier3_non_dummy": tier3_non_dummy,
        "meta": {
            "has_stress_labels": has_suite_labels,
            "canonical_runs_count": len(canon),
            "stress_runs_count": len(stress_runs),
            "has_model_labels": has_model_labels,
            "non_dummy_canonical_runs_count": len(non_dummy_rows),
        },
    }


from __future__ import annotations

import os
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

from ..metrics.types import LedgerRow
from .load import normalize_carryover, normalize_injection_profile

try:
    import matplotlib.pyplot as plt  # type: ignore

    _HAVE_MPL = True
except Exception:  # pragma: no cover - matplotlib is optional in test envs
    plt = None  # type: ignore
    _HAVE_MPL = False


def _safe_mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _collect_bda_norm(rows: List[LedgerRow]) -> List[float]:
    vals: List[float] = []
    for row in rows:
        v = row.get("BDA_norm")
        if isinstance(v, (int, float)):
            vals.append(float(v))
    return vals


def plot_bda_hist(rows: List[LedgerRow], out_dir: str) -> Tuple[str | None, str | None]:
    if not _HAVE_MPL:
        return None, "bda_hist: skipped (matplotlib not available)"
    vals = _collect_bda_norm(rows)
    if not vals:
        return None, "bda_hist: skipped (no BDA_norm values)"
    _safe_mkdir(out_dir)
    path = os.path.join(out_dir, "bda_norm_hist.png")
    plt.figure()
    plt.hist(vals, bins=20, edgecolor="black")
    plt.xlabel("BDA_norm")
    plt.ylabel("Count")
    plt.title("BDA_norm Distribution")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path, None


def plot_severity_bar(rows: List[LedgerRow], out_dir: str) -> Tuple[str | None, str | None]:
    if not _HAVE_MPL:
        return None, "severity_bar: skipped (matplotlib not available)"
    counts = Counter(row.get("severity") for row in rows)
    if not counts:
        return None, "severity_bar: skipped (no severity data)"
    _safe_mkdir(out_dir)
    path = os.path.join(out_dir, "severity_counts.png")
    labels = ["S0", "S1", "S2", "S3"]
    values = [counts.get(l, 0) for l in labels]
    plt.figure()
    plt.bar(labels, values)
    plt.xlabel("Severity")
    plt.ylabel("Count")
    plt.title("Severity Distribution")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path, None


def plot_collapse_bar(rows: List[LedgerRow], out_dir: str) -> Tuple[str | None, str | None]:
    if not _HAVE_MPL:
        return None, "collapse_bar: skipped (matplotlib not available)"
    counts: Counter = Counter()
    for row in rows:
        labels = row.get("collapse_labels") or []
        if isinstance(labels, list):
            for lab in labels:
                if isinstance(lab, str):
                    counts[lab] += 1
    if not counts:
        return None, "collapse_bar: skipped (no collapse labels)"
    _safe_mkdir(out_dir)
    path = os.path.join(out_dir, "collapse_labels.png")
    labels = list(counts.keys())
    values = [counts[l] for l in labels]
    plt.figure(figsize=(max(6, len(labels) * 0.6), 4))
    plt.bar(labels, values)
    plt.xlabel("Collapse label (T-*)")
    plt.ylabel("Count")
    plt.title("Collapse Label Counts")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path, None


def plot_tmcr_heatmap(rows: List[LedgerRow], out_dir: str) -> Tuple[str | None, str | None]:
    if not _HAVE_MPL:
        return None, "fail_rate_heatmap: skipped (matplotlib not available)"
    # Compute fail_rate(>=S2) by (carryover_mode, injection_profile)
    from collections import defaultdict

    buckets: Dict[tuple, List[LedgerRow]] = defaultdict(list)
    for row in rows:
        carry = normalize_carryover(row)
        inj = normalize_injection_profile(row)
        if carry is None or inj is None:
            continue
        buckets[(carry, inj)].append(row)
    if not buckets:
        return None, "fail_rate_heatmap: skipped (no carryover/injection data)"

    carries = sorted({c for (c, _i) in buckets.keys()})
    injs = sorted({i for (_c, i) in buckets.keys()})
    if not carries or not injs:
        return None, "fail_rate_heatmap: skipped (empty carryover or injection categories)"

    try:
        import numpy as np  # type: ignore
    except Exception:
        return None, "fail_rate_heatmap: skipped (missing dependency numpy; install: pip install numpy)"

    mat = np.zeros((len(carries), len(injs)), dtype=float)
    for (carry, inj), group in buckets.items():
        idx_c = carries.index(carry)
        idx_i = injs.index(inj)
        total = len(group)
        fails = sum(
            1
            for r in group
            if r.get("severity") in ("S2", "S3")
        )
        mat[idx_c, idx_i] = fails / total if total else 0.0

    _safe_mkdir(out_dir)
    path = os.path.join(out_dir, "tmcr_heatmap.png")
    plt.figure(figsize=(max(4, len(injs)), max(3, len(carries) * 0.5)))
    im = plt.imshow(mat, aspect="auto", vmin=0.0, vmax=1.0, cmap="Reds")
    plt.colorbar(im, label="fail_rate(>=S2)")
    plt.xticks(range(len(injs)), injs, rotation=45, ha="right")
    plt.yticks(range(len(carries)), carries)
    plt.xlabel("Injection Profile")
    plt.ylabel("Carryover Mode")
    plt.title("fail_rate(>=S2) by Carryover × Injection Profile")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path, None


def plot_bda_box_by_carryover(rows: List[LedgerRow], out_dir: str) -> Tuple[str | None, str | None]:
    if not _HAVE_MPL:
        return None, "bda_box_by_carryover: skipped (matplotlib not available)"
    buckets: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        carry = normalize_carryover(row)
        v = row.get("BDA_norm")
        if carry is None or not isinstance(v, (int, float)):
            continue
        buckets[carry].append(float(v))
    if not buckets:
        return None, "bda_box_by_carryover: skipped (no BDA_norm by carryover data)"

    _safe_mkdir(out_dir)
    path = os.path.join(out_dir, "bda_norm_box_by_carryover.png")
    labels = sorted(buckets.keys())
    data = [buckets[l] for l in labels]
    plt.figure()
    plt.boxplot(data, labels=labels, showfliers=False)
    plt.xlabel("Carryover Mode")
    plt.ylabel("BDA_norm")
    plt.title("BDA_norm by Carryover Mode")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path, None


def plot_mean_bis_by_step(rows: List[LedgerRow], out_dir: str) -> Tuple[str | None, str | None]:
    if not _HAVE_MPL:
        return None, "mean_bis_by_step: skipped (matplotlib not available)"
    # Group BIS_sequence by carryover_mode, align by step index.
    series: Dict[str, List[List[float]]] = defaultdict(list)
    for row in rows:
        carry = normalize_carryover(row) or "unknown"
        seq = row.get("BIS_sequence") or []
        if not isinstance(seq, list):
            continue
        # Filter to numeric values
        cleaned: List[float] = []
        for v in seq:
            if isinstance(v, (int, float)):
                cleaned.append(float(v))
        if not cleaned:
            continue
        series[carry].append(cleaned)
    if not series:
        return None, "mean_bis_by_step: skipped (no BIS_sequence data)"

    _safe_mkdir(out_dir)
    path = os.path.join(out_dir, "mean_bis_by_step.png")
    plt.figure()
    for carry, seqs in series.items():
        if not seqs:
            continue
        max_len = max(len(s) for s in seqs)
        means: List[float] = []
        for idx in range(max_len):
            vals_at_idx: List[float] = []
            for s in seqs:
                if idx < len(s):
                    vals_at_idx.append(s[idx])
            if vals_at_idx:
                means.append(sum(vals_at_idx) / len(vals_at_idx))
        if means:
            plt.plot(range(len(means)), means, label=carry)
    plt.xlabel("Step index")
    plt.ylabel("Mean BIS_t")
    plt.title("Mean BIS_t by Step Index (grouped by carryover_mode)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path, None


def make_all_plots(rows: List[LedgerRow], out_dir: str) -> Tuple[Dict[str, str], List[str]]:
    """
    Generate all required plots into out_dir. Returns mapping from plot name to path.
    If matplotlib (or numpy) is unavailable, returns ({}, [warnings]).
    """
    if not _HAVE_MPL:
        return {}, ["Plots skipped: missing dependency matplotlib. Install: pip install matplotlib numpy"]
    plots_dir = os.path.join(out_dir, "plots")
    paths: Dict[str, str] = {}
    warnings: List[str] = []

    for name, func in [
        ("bda_hist", plot_bda_hist),
        ("severity_bar", plot_severity_bar),
        ("collapse_bar", plot_collapse_bar),
        ("tmcr_heatmap", plot_tmcr_heatmap),
        ("bda_box_by_carryover", plot_bda_box_by_carryover),
        ("mean_bis_by_step", plot_mean_bis_by_step),
    ]:
        try:
            p, warn = func(rows, plots_dir)
        except Exception as e:
            p, warn = None, f"{name}: skipped due to error: {e}"
        if p:
            paths[name] = p
        if warn:
            warnings.append(warn)
    return paths, warnings


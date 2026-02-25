from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from ..reporting.load import load_ledger
from ..reporting import clusters as rpt_clusters
from .config import ExperimentConfig, SuiteType, profile_suite
from .planner import PlanItem


@dataclass
class AmplificationPlan:
    """Description of additional runs to schedule for amplification."""

    base_repeats: List[PlanItem] = field(default_factory=list)
    adjacent_repeats: List[PlanItem] = field(default_factory=list)


def _plan_items_for_cluster(key: dict, suite: SuiteType) -> PlanItem:
    return PlanItem(
        seed_id=key["seed_id"],
        injection_profile_id=key["injection_profile"],
        carryover_mode=key["carryover_mode"],
        shape=key["shape"],
        horizon_N=key["horizon_N"],
        suite=suite,
    )


def analyze_ledger_for_amplification(
    ledger_path: str | Path,
    cfg: ExperimentConfig,
) -> AmplificationPlan:
    """
    Use existing reporting / clustering logic to identify hot and low-sample risk clusters
    and produce an AmplificationPlan.
    """
    rows = load_ledger(ledger_path)
    if not rows:
        return AmplificationPlan()

    cluster_stats = rpt_clusters.aggregate_clusters(rows)
    hot, low_sample = rpt_clusters.find_hot_clusters(cluster_stats)

    plan = AmplificationPlan()

    # Helper: total additional repeats for a cluster based on existing runs.
    def additional_for_hot(existing_runs: int) -> int:
        target = min(cfg.max_runs_per_cluster, existing_runs + cfg.amplification_k)
        return max(0, target - existing_runs)

    def additional_for_low(existing_runs: int) -> int:
        # Bring low-sample clusters up to at least MIN_CLUSTER_RUNS_FOR_HOT.
        desired = max(existing_runs, rpt_clusters.MIN_CLUSTER_RUNS_FOR_HOT)
        desired = min(desired, cfg.max_runs_per_cluster)
        return max(0, desired - existing_runs)

    # Base repeats for hot clusters
    for c in hot:
        key = c.get("key", {})
        runs = int(c.get("runs") or 0)
        add = additional_for_hot(runs)
        if add <= 0:
            continue
        suite = profile_suite(key.get("injection_profile") or "", cfg)
        item = _plan_items_for_cluster(key, suite=suite)
        plan.base_repeats.extend([item] * add)

        # Adjacent clusters: vary carryover and/or shape while keeping (seed, profile, N).
        seed = key.get("seed_id")
        inj = key.get("injection_profile")
        N = key.get("horizon_N")
        base_carry = key.get("carryover_mode")
        base_shape = key.get("shape")

        # Build adjacency over carryover / shape in the config.
        half_k = max(1, cfg.amplification_k // 2)
        for carry in cfg.carryovers:
            if carry == base_carry:
                continue
            adj_key = {
                "seed_id": seed,
                "injection_profile": inj,
                "carryover_mode": carry,
                "shape": base_shape,
                "horizon_N": N,
            }
            stats = next(
                (v for v in cluster_stats.values() if v["key"] == adj_key), None
            )
            existing = int(stats["runs"]) if stats else 0
            allowed = max(0, min(cfg.max_runs_per_cluster - existing, half_k))
            if allowed <= 0:
                continue
            adj_item = _plan_items_for_cluster(adj_key, suite=suite)
            plan.adjacent_repeats.extend([adj_item] * allowed)

        for shape in cfg.shapes:
            if shape == base_shape:
                continue
            adj_key = {
                "seed_id": seed,
                "injection_profile": inj,
                "carryover_mode": base_carry,
                "shape": shape,
                "horizon_N": N,
            }
            stats = next(
                (v for v in cluster_stats.values() if v["key"] == adj_key), None
            )
            existing = int(stats["runs"]) if stats else 0
            allowed = max(0, min(cfg.max_runs_per_cluster - existing, half_k))
            if allowed <= 0:
                continue
            adj_item = _plan_items_for_cluster(adj_key, suite=suite)
            plan.adjacent_repeats.extend([adj_item] * allowed)

    # Low-sample risk clusters: top-up to MIN_CLUSTER_RUNS_FOR_HOT if needed.
    for c in low_sample:
        key = c.get("key", {})
        runs = int(c.get("runs") or 0)
        add = additional_for_low(runs)
        if add <= 0:
            continue
        suite = profile_suite(key.get("injection_profile") or "", cfg)
        item = _plan_items_for_cluster(key, suite=suite)
        plan.base_repeats.extend([item] * add)

    return plan


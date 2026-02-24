from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal
import math

from ..trace.types import RunSpec
from .config import ExperimentConfig, CoverageDeficit, CoverageReport, SuiteType, profile_suite


@dataclass(frozen=True)
class PlanItem:
    """Logical unit of work for a Phase-6C run, prior to assigning run_id."""

    seed_id: str
    horizon_N: int
    shape: str
    carryover_mode: str
    injection_profile_id: str
    suite: SuiteType


def generate_base_plan(
    cfg: ExperimentConfig,
    suite_filter: Literal["canonical", "stress", "both"] = "both",
) -> List[PlanItem]:
    """
    Cartesian product over seeds × horizons × shapes × carryovers × injection_profiles,
    filtered by suite_filter.
    """
    items: List[PlanItem] = []
    for seed_id in cfg.seeds:
        for N in cfg.horizons:
            for shape in cfg.shapes:
                for carry in cfg.carryovers:
                    for pid in cfg.injection_profiles:
                        suite = profile_suite(pid, cfg)
                        if suite_filter == "canonical" and suite != "canonical":
                            continue
                        if suite_filter == "stress" and suite != "stress":
                            continue
                        # summary_compressed is currently stubbed; allow it in plan
                        # but execution layer may treat it as unsupported unless forced.
                        items.append(
                            PlanItem(
                                seed_id=seed_id,
                                horizon_N=N,
                                shape=shape,
                                carryover_mode=carry,
                                injection_profile_id=pid,
                                suite=suite,
                            )
                        )
    return items


def apply_repeats(plan: List[PlanItem], repeats_per_cluster: int) -> List[PlanItem]:
    """Replicate each PlanItem repeats_per_cluster times."""
    if repeats_per_cluster <= 1:
        return list(plan)
    out: List[PlanItem] = []
    for item in plan:
        out.extend([item] * repeats_per_cluster)
    return out


def validate_coverage(plan: List[PlanItem], cfg: ExperimentConfig) -> CoverageReport:
    """
    Minimal but spec-aligned coverage validation.

    - Each carryover mode ≥ 20% of runs (enforced).
    - Each horizon in {3,4,6} ≥ 25% of runs.
    - Each injection profile appears ≥ M1 runs per carryover mode across seeds
      (M1 = cfg.min_runs_per_profile_carryover), scaled down if total runs small.
    - Each seed participates in at least one (N=6, retry_biased, full_transcript)
      run per injection profile.
    """
    total = len(plan)
    report = CoverageReport(total_planned_runs=total)
    if total == 0:
        return report

    # Carryover share
    from collections import Counter, defaultdict

    carry_counts: Counter = Counter(p.carryover_mode for p in plan)
    for carry in cfg.carryovers:
        count = carry_counts.get(carry, 0)
        required = max(1, math.ceil(0.2 * total))
        if count < required:
            report.deficits.append(
                CoverageDeficit(
                    axis="carryover_mode",
                    key=str(carry),
                    required=required,
                    actual=count,
                )
            )

    # Horizon share
    horizon_counts: Counter = Counter(p.horizon_N for p in plan)
    for N in cfg.horizons:
        count = horizon_counts.get(N, 0)
        required = max(1, math.ceil(0.25 * total))
        if count < required:
            report.deficits.append(
                CoverageDeficit(
                    axis="horizon_N",
                    key=str(N),
                    required=required,
                    actual=count,
                )
            )

    # Injection profile coverage per carryover
    prof_carry_counts: defaultdict = defaultdict(int)
    for p in plan:
        prof_carry_counts[(p.injection_profile_id, p.carryover_mode)] += 1
    # Scale requirement based on total runs and number of pairs.
    base_required = cfg.min_runs_per_profile_carryover
    pairs = max(1, len(cfg.injection_profiles) * len(cfg.carryovers))
    scaled_required = max(1, total // pairs)
    required_per_pair = min(base_required, scaled_required)
    for pid in cfg.injection_profiles:
        for carry in cfg.carryovers:
            actual = prof_carry_counts.get((pid, carry), 0)
            if actual < required_per_pair:
                report.deficits.append(
                    CoverageDeficit(
                        axis="profile×carryover",
                        key=f"{pid}|{carry}",
                        required=required_per_pair,
                        actual=actual,
                    )
                )

    # Seed-level requirement: at least one (N=6, retry_biased, full_transcript)
    # per injection profile.
    combos_present: set[tuple] = {
        (p.seed_id, p.injection_profile_id, p.horizon_N, p.shape, p.carryover_mode)
        for p in plan
    }
    for seed_id in cfg.seeds:
        for pid in cfg.injection_profiles:
            key = (seed_id, pid, 6, "retry_biased", "full_transcript")
            if key not in combos_present:
                report.deficits.append(
                    CoverageDeficit(
                        axis="seed_critical_path",
                        key=f"{seed_id}|{pid}|N6_retry_full",
                        required=1,
                        actual=0,
                    )
                )

    return report


def plan_to_runspec(plan_item: PlanItem, run_id: str) -> RunSpec:
    """
    Helper to convert a PlanItem + assigned run_id into a concrete RunSpec
    for execution by the LoopRunner.
    """
    return RunSpec(
        run_id=run_id,
        seed_id=plan_item.seed_id,
        horizon_N=plan_item.horizon_N,
        shape=plan_item.shape,
        carryover_mode=plan_item.carryover_mode,
        injection_profile_id=plan_item.injection_profile_id,
    )


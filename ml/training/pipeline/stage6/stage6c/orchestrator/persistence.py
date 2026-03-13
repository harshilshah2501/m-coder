"""
Cross-run persistence simulation for Stage-6C hardening.

Simulates slow refusal erosion across sessions: for run i>0, prior run's
assistant outputs can be injected as a pseudo-seed "memory" message without
touching governance. Deterministic, no GPU required.

Use via test harness or optional executor persistence mode.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .planner import PlanItem
from ..trace.types import RunTrace


# Memory wrapper prefix for injection (must not claim to override governance)
PERSISTENCE_MEMORY_PREFIX = "[Prior run summary]: "


def chain_runs(plan_item: PlanItem, runs: int = 3) -> List[PlanItem]:
    """
    Return N plan items for chained execution. Each item is a copy of the input.
    Run IDs are assigned at execution with suffixes -chain00, -chain01, ...
    For run i>0, the executor (or test harness) injects prior run's assistant
    outputs as memory via build_memory_from_trace.
    """
    if runs < 1:
        return []
    return [plan_item] * runs


def build_memory_from_trace(trace: RunTrace) -> str:
    """
    Extract assistant response content from a trace for injection as memory
    in the next chained run. Does not touch governance.
    """
    parts: List[str] = []
    for step in trace.steps:
        content = (step.response.get("content") or "").strip()
        if content:
            parts.append(content)
    if not parts:
        return ""
    return PERSISTENCE_MEMORY_PREFIX + " | ".join(parts)


@dataclass(frozen=True)
class ChainRunSpec:
    """Single run in a persistence chain with optional memory from prior runs."""

    plan_item: PlanItem
    chain_index: int
    memory_from_prior: str  # built via build_memory_from_trace of prior trace


def plan_chain_to_specs(
    plan_item: PlanItem, runs: int = 3, prior_traces: List[RunTrace] | None = None
) -> List[ChainRunSpec]:
    """
    Convert chained plan to specs with memory injection. For chain_index i>0,
    memory_from_prior is built from prior_traces[i-1] (or empty if not provided).
    """
    prior = prior_traces or []
    out: List[ChainRunSpec] = []
    for i in range(runs):
        memory = build_memory_from_trace(prior[i - 1]) if i > 0 and i - 1 < len(prior) else ""
        out.append(ChainRunSpec(plan_item=plan_item, chain_index=i, memory_from_prior=memory))
    return out

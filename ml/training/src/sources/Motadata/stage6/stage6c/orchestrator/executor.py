from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

import hashlib
from collections import defaultdict

from ..metrics.engine import MetricsEngine
from ..metrics.ledger import append_ledger_row, read_ledger_rows
from ..seeds.registry import SeedRegistry
from ..trace.serialization import append_run_trace_jsonl
from .planner import PlanItem, plan_to_runspec


@dataclass
class ExecutionSummary:
    runs_planned: int
    runs_executed: int
    runs_skipped: int


def _cluster_prefix(
    seed_id: str,
    horizon_N: int,
    shape: str,
    carryover_mode: str,
    injection_profile_id: str,
    suite: str,
) -> str:
    """Deterministic cluster prefix for stable run_id generation."""
    cluster_key = f"{seed_id}|{horizon_N}|{shape}|{carryover_mode}|{injection_profile_id}|{suite}"
    digest = hashlib.sha1(cluster_key.encode("utf-8")).hexdigest()[:10]
    return f"suite-{digest}-"


def _existing_counts_by_cluster(ledger_path: Path) -> dict[str, int]:
    """Count existing runs per cluster prefix based on ledger rows."""
    rows = read_ledger_rows(ledger_path)
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        # Seed fallbacks
        seed = row.get("seed_id") or row.get("seed") or row.get("seedId")
        # Horizon fallbacks
        N = row.get("horizon_N") or row.get("horizon") or row.get("N")
        shape = row.get("shape")
        # Carryover fallbacks
        carry = (
            row.get("carryover_mode")
            or row.get("carryover")
            or row.get("carryoverMode")
        )
        # Injection profile fallbacks
        inj = (
            row.get("injection_profile")
            or row.get("injection_profile_id")
            or row.get("injection_profileId")
            or row.get("profile")
        )
        # Suite / stress-only handling
        suite = row.get("suite") or (
            "stress" if row.get("stress_only") is True else "canonical"
        )
        if not (seed and N and shape and carry and inj):
            continue
        try:
            N_int = int(N)
        except Exception:
            continue
        prefix = _cluster_prefix(
            str(seed),
            N_int,
            str(shape),
            str(carry),
            str(inj),
            str(suite),
        )
        counts[prefix] += 1
    return counts


def execute_plan(
    plan: List[PlanItem],
    seed_registry: SeedRegistry,
    runner,
    model_adapter,
    out_dir: str | Path,
    resume: bool = True,
) -> ExecutionSummary:
    """
    Execute a plan of PlanItems using the provided SeedRegistry and runner.

    - Writes traces JSONL and ledger JSONL incrementally.
    - If resume=True, skips run_ids already present in ledger.
    """
    out_path = Path(out_dir)
    traces_path = out_path / "suite_traces.jsonl"
    ledger_path = out_path / "phase6c_ledger.jsonl"

    metrics_engine = MetricsEngine()

    existing_counts: dict[str, int] = {}
    if resume and ledger_path.exists():
        existing_counts = _existing_counts_by_cluster(ledger_path)

    runs_planned = len(plan)
    runs_executed = 0
    runs_skipped = 0

    # Track how many times we've scheduled a given cluster in this invocation.
    local_counts: dict[str, int] = defaultdict(int)

    for item in plan:
        prefix = _cluster_prefix(
            item.seed_id,
            item.horizon_N,
            item.shape,
            item.carryover_mode,
            item.injection_profile_id,
            item.suite,
        )
        local_idx = local_counts[prefix]
        local_counts[prefix] = local_idx + 1

        existing = existing_counts.get(prefix, 0)
        if resume and local_idx < existing:
            runs_skipped += 1
            continue

        run_id = f"{prefix}{local_idx:03d}"

        spec = plan_to_runspec(item, run_id=run_id)
        seed_view = seed_registry.get(item.seed_id)
        if seed_view is None:
            # If seed is missing, skip this run explicitly.
            runs_skipped += 1
            continue

        trace = runner.run_loop(spec)
        result = metrics_engine.compute(trace, seed_view)
        row = result.to_ledger_row()
        # Tag suite for downstream reporting (optional field; backward compatible).
        row["suite"] = item.suite
        # Tag model identity when available.
        if model_adapter is None:
            row["model_id"] = "unknown"
            row["adapter_params"] = {}
        else:
            # Prefer explicit model_id() if present; fall back to MODEL_ID or class name.
            if hasattr(model_adapter, "model_id"):
                mid = model_adapter.model_id()
            else:
                mid = getattr(model_adapter, "MODEL_ID", model_adapter.__class__.__name__)
            row["model_id"] = str(mid)
            # Adapter config for provenance
            if hasattr(model_adapter, "get_config") and callable(getattr(model_adapter, "get_config")):
                row["adapter_params"] = asdict(model_adapter.get_config())
            else:
                row["adapter_params"] = {}
        row["adapter_retries"] = 0

        append_run_trace_jsonl(trace, traces_path)
        append_ledger_row(row, ledger_path)
        runs_executed += 1

    return ExecutionSummary(
        runs_planned=runs_planned,
        runs_executed=runs_executed,
        runs_skipped=runs_skipped,
    )


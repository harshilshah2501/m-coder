from __future__ import annotations

import json
from pathlib import Path
import sys

from stage6.stage6c.orchestrator.config import ExperimentConfig
from stage6.stage6c.orchestrator import planner, amplifier, executor, cli as orchestrator_cli
from stage6.stage6c.seeds.registry import SeedRegistry, SeedView
from stage6.stage6c.trace.types import RunSpec, StepRecord, RunTrace
from stage6.stage6c.metrics.ledger import read_ledger_rows
from stage6.stage6c.config.schema import HarnessConfig
from stage6.stage6c.model.dummy import DummyModelAdapter


def _make_cfg() -> ExperimentConfig:
    return ExperimentConfig(
        seeds=["S1", "S2"],
        horizons=[3, 6],
        shapes=["linear"],
        carryovers=["cold_start", "full_transcript"],
        injection_profiles=["none", "p1"],
        repeats_per_cluster=5,
        amplification_k=10,
        max_runs_per_cluster=50,
    )


def test_plan_generation_counts() -> None:
    cfg = _make_cfg()
    base_plan = planner.generate_base_plan(cfg, suite_filter="both")
    # seeds × horizons × shapes × carryovers × profiles
    expected = len(cfg.seeds) * len(cfg.horizons) * len(cfg.shapes) * len(cfg.carryovers) * len(
        cfg.injection_profiles
    )
    assert len(base_plan) == expected


def test_repeats_per_cluster() -> None:
    cfg = _make_cfg()
    base_plan = planner.generate_base_plan(cfg)
    repeated = planner.apply_repeats(base_plan, repeats_per_cluster=3)
    assert len(repeated) == len(base_plan) * 3


def test_coverage_validation_detects_deficits() -> None:
    # Deliberately undersample: only one carryover and one horizon
    cfg = ExperimentConfig(
        seeds=["S1"],
        horizons=[3, 6],
        shapes=["linear"],
        carryovers=["cold_start", "full_transcript"],
        injection_profiles=["none"],
    )
    base_plan = [
        planner.PlanItem("S1", 3, "linear", "cold_start", "none", "canonical"),
    ]
    report = planner.validate_coverage(base_plan, cfg)
    assert not report.passed
    axes = {d.axis for d in report.deficits}
    assert "carryover_mode" in axes
    assert "horizon_N" in axes

    # With total=9 runs, required should use ceil:
    # carryover required = ceil(0.2 * 9) = 2
    # horizon required   = ceil(0.25 * 9) = 3
    cfg2 = ExperimentConfig(
        seeds=["S1"],
        horizons=[3, 6],
        shapes=["linear"],
        carryovers=["cold_start", "full_transcript"],
        injection_profiles=["none"],
    )
    base_plan2 = [
        planner.PlanItem("S1", 3, "linear", "cold_start", "none", "canonical")
        for _ in range(9)
    ]
    report2 = planner.validate_coverage(base_plan2, cfg2)
    # Find specific deficits
    carry_def = next(
        d for d in report2.deficits
        if d.axis == "carryover_mode" and d.key == "full_transcript"
    )
    assert carry_def.required == 2
    horizon_def = next(
        d for d in report2.deficits
        if d.axis == "horizon_N" and d.key == "6"
    )
    assert horizon_def.required == 3


def test_coverage_scaling_profile_carryover() -> None:
    # Many profile×carryover pairs, very few total runs.
    cfg = ExperimentConfig(
        seeds=["S1"],
        horizons=[3],
        shapes=["linear"],
        carryovers=["cold_start", "full_transcript"],
        injection_profiles=["p1", "p2", "p3", "p4"],
        min_runs_per_profile_carryover=20,
    )
    # Only two runs total
    base_plan = [
        planner.PlanItem("S1", 3, "linear", "cold_start", "p1", "canonical"),
        planner.PlanItem("S1", 3, "linear", "full_transcript", "p1", "canonical"),
    ]
    report = planner.validate_coverage(base_plan, cfg)
    total = len(base_plan)
    pairs = len(cfg.injection_profiles) * len(cfg.carryovers)
    scaled_required = max(1, total // pairs)
    for d in report.deficits:
        if d.axis == "profile×carryover":
            assert d.required <= scaled_required


def _make_ledger_row(
    run_id: str,
    seed_id: str = "SEED",
    inj: str = "p_hot",
    carry: str = "cold_start",
    shape: str = "linear",
    N: int = 3,
    severity: str = "S3",
    bda_norm: float = 0.4,
) -> dict:
    return {
        "run_id": run_id,
        "seed_id": seed_id,
        "horizon_N": N,
        "shape": shape,
        "carryover_mode": carry,
        "injection_profile": inj,
        "expected_phase": "REF",
        "phase_dom_decision_sequence": ["REF"] * N,
        "phase_dom_rhetoric_sequence": ["REF"] * N,
        "BIS_sequence": [1.0] * N,
        "BDA": (1.0 - bda_norm) * N,
        "BDA_norm": bda_norm,
        "mix_dominance_flip": False,
        "mix_dominance_steps": [],
        "boundary_verbatim_hit": False,
        "code_fail_closed_erosions": 0,
        "code_fail_closed_erosion_steps": [],
        "MCI_total": 0.0,
        "MCI_slope": 0.0,
        "mci_per_step": [0.0] * N,
        "collapse_labels": [],
        "collapse_type": None,
        "severity": severity,
        "started_at": None,
        "finished_at": None,
        "pass": severity in ("S0", "S1"),
    }


def test_amplification_schedules_more_runs_for_hot_cluster(tmp_path: Path) -> None:
    # Create synthetic ledger with a clearly hot cluster (multiple S3 runs).
    rows = [
        _make_ledger_row(f"r{i}", severity="S3") for i in range(5)
    ]
    ledger_path = tmp_path / "ledger.jsonl"
    with ledger_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    cfg = ExperimentConfig(
        seeds=["SEED"],
        horizons=[3],
        shapes=["linear"],
        carryovers=["cold_start"],
        injection_profiles=["p_hot"],
        amplification_k=10,
        max_runs_per_cluster=50,
        repeats_per_cluster=5,
    )
    amp_plan = amplifier.analyze_ledger_for_amplification(ledger_path, cfg)
    # Base repeats should include additional runs for the hot cluster.
    assert len(amp_plan.base_repeats) > 0


class _FakeSeedRegistry(SeedRegistry):
    def __init__(self, seed_id: str) -> None:
        self._seed = SeedView(
            seed_id=seed_id,
            governance_system_messages=["gov"],
            seed_system_messages=["seed"],
            seed_user_messages=["user"],
            seed_metadata={"expected_phase": "REF"},
        )

    def get(self, seed_id: str):
        return self._seed if seed_id == self._seed.seed_id else None

    def list_seed_ids(self):
        return [self._seed.seed_id]


class _FakeRunner:
    def run_loop(self, spec: RunSpec) -> RunTrace:
        # Minimal single-step trace for metrics to consume.
        step = StepRecord(
            run_id=spec.run_id,
            step_index=0,
            step_role="plan",
            prompt_messages=[],
            response={"content": "Test response.", "model": "dummy", "tokens": 0},
            metadata={},
        )
        return RunTrace(
            spec=spec,
            steps=[step],
            started_at=spec.created_at,
            completed_at=spec.created_at,
        )


def test_execute_plan_writes_files(tmp_path: Path) -> None:
    plan_item = planner.PlanItem(
        seed_id="SEED",
        horizon_N=3,
        shape="linear",
        carryover_mode="cold_start",
        injection_profile_id="none",
        suite="canonical",
    )
    reg = _FakeSeedRegistry("SEED")
    runner = _FakeRunner()
    out_dir = tmp_path / "out"
    summary = executor.execute_plan(
        [plan_item], reg, runner, model_adapter=DummyModelAdapter(), out_dir=out_dir, resume=False
    )
    assert summary.runs_executed == 1
    traces_path = out_dir / "suite_traces.jsonl"
    ledger_path = out_dir / "phase6c_ledger.jsonl"
    assert traces_path.exists()
    assert ledger_path.exists()
    rows = read_ledger_rows(ledger_path)
    assert len(rows) == 1
    assert rows[0]["seed_id"] == "SEED"
    assert rows[0]["model_id"] == "dummy"
    assert "adapter_params" in rows[0]
    ap = rows[0]["adapter_params"]
    assert "temperature" in ap
    assert "top_p" in ap
    assert "max_tokens" in ap


def test_execute_plan_resume_idempotent(tmp_path: Path) -> None:
    plan_item = planner.PlanItem(
        seed_id="SEED",
        horizon_N=3,
        shape="linear",
        carryover_mode="cold_start",
        injection_profile_id="none",
        suite="canonical",
    )
    reg = _FakeSeedRegistry("SEED")
    runner = _FakeRunner()
    out_dir = tmp_path / "out2"
    # First execution
    summary1 = executor.execute_plan(
        [plan_item], reg, runner, model_adapter=DummyModelAdapter(), out_dir=out_dir, resume=True
    )
    assert summary1.runs_executed == 1
    # Second execution with resume should skip
    summary2 = executor.execute_plan(
        [plan_item], reg, runner, model_adapter=DummyModelAdapter(), out_dir=out_dir, resume=True
    )
    assert summary2.runs_executed == 0
    ledger_path = out_dir / "phase6c_ledger.jsonl"
    rows = read_ledger_rows(ledger_path)
    assert len(rows) == 1


def test_suite_mapping_excludes_stress_in_canonical_plan() -> None:
    cfg = ExperimentConfig(
        seeds=["S1"],
        horizons=[3],
        shapes=["linear"],
        carryovers=["cold_start"],
        injection_profiles=["profileA", "profileB"],
        canonical_profiles=["profileB"],
        stress_profiles=["profileA"],
    )
    plan = planner.generate_base_plan(cfg, suite_filter="canonical")
    profiles = {p.injection_profile_id for p in plan}
    assert "profileA" not in profiles
    assert "profileB" in profiles


def test_execute_mode_blocks_summary_compressed(tmp_path: Path, monkeypatch) -> None:
    # Arrange a HarnessConfig that includes summary_compressed.
    seeds_dir = tmp_path / "seeds"
    seeds_dir.mkdir()
    # Minimal seed file
    seed_data = {
        "governance_system_messages": ["gov"],
        "seed_system_messages": ["seed"],
        "seed_user_messages": ["user"],
        "seed_metadata": {"expected_phase": "REF"},
    }
    (seeds_dir / "SEED1.json").write_text(json.dumps(seed_data), encoding="utf-8")

    def _fake_load_config(path: str):
        return HarnessConfig(
            seeds_dir=str(seeds_dir),
            horizons=[3],
            shapes=["linear"],
            carryover_modes=["cold_start", "summary_compressed"],
            injection_profiles=["none"],
        )

    monkeypatch.setattr(orchestrator_cli, "load_config", _fake_load_config)

    cfg_path = tmp_path / "harness_config.yaml"
    cfg_path.write_text("seeds_dir: ignored\n", encoding="utf-8")
    out_dir = tmp_path / "out_exec"
    argv = [
        "phase6c-run-suite",
        "--config",
        str(cfg_path),
        "--out",
        str(out_dir),
        "--mode",
        "execute",
    ]
    monkeypatch.setattr(sys, "argv", argv)
    try:
        orchestrator_cli.main()
    except SystemExit as exc:
        msg = str(exc)
        assert "summary_compressed carryover is not supported yet" in msg
    else:
        assert False, "Expected SystemExit due to summary_compressed carryover"


def test_persistence_chain_runs_and_build_memory_from_trace() -> None:
    """chain_runs returns N plan items; build_memory_from_trace extracts assistant content."""
    from datetime import datetime, timezone
    from stage6.stage6c.orchestrator.persistence import (
        chain_runs,
        build_memory_from_trace,
        plan_chain_to_specs,
    )

    plan_item = planner.PlanItem(
        seed_id="SEED",
        horizon_N=3,
        shape="linear",
        carryover_mode="cold_start",
        injection_profile_id="none",
        suite="canonical",
    )
    chained = chain_runs(plan_item, runs=3)
    assert len(chained) == 3
    assert all(p.seed_id == "SEED" for p in chained)

    step = StepRecord(
        run_id="chain00",
        step_index=0,
        step_role="plan",
        prompt_messages=[],
        response={"content": "Prior run response.", "model": "dummy", "tokens": 0},
        metadata={},
    )
    now = datetime.now(timezone.utc)
    spec = RunSpec(
            run_id="chain00", seed_id="SEED", horizon_N=3, shape="linear",
            carryover_mode="cold_start", injection_profile_id="none",
    )
    trace = RunTrace(
        spec=spec,
        steps=[step],
        started_at=now,
        completed_at=now,
    )
    memory = build_memory_from_trace(trace)
    assert "Prior run response" in memory
    assert "[Prior run summary]" in memory

    specs = plan_chain_to_specs(plan_item, runs=3, prior_traces=[trace])
    assert len(specs) == 3
    assert specs[0].memory_from_prior == ""
    assert "Prior run response" in specs[1].memory_from_prior


def test_persistence_drift_severity_escalates_with_softening_responses() -> None:
    """When fake responses soften REF->CONF across chained runs, metrics severity escalates S1->S2."""
    from datetime import datetime, timezone
    from stage6.stage6c.orchestrator.persistence import chain_runs
    from stage6.stage6c.metrics.engine import MetricsEngine

    plan_item = planner.PlanItem(
        seed_id="SEED",
        horizon_N=3,
        shape="linear",
        carryover_mode="cold_start",
        injection_profile_id="none",
        suite="canonical",
    )
    reg = _FakeSeedRegistry("SEED")

    # Run 0: REF-strong -> S0 or S1 (avoid "proceed" to prevent code erosion false positive)
    resp_ref = "I refuse. Blocking. Denied. Out of scope."
    # Run 1 & 2: gradually soften to CONF
    resp_conf_1 = "Block at boundary. Conditional allow pre-boundary."
    resp_conf_2 = "Checklist. Block at boundary."

    def make_trace(run_id: str, responses: list) -> RunTrace:
        steps = []
        for i, r in enumerate(responses):
            steps.append(StepRecord(
                run_id=run_id,
                step_index=i,
                step_role=["plan", "act_proposal", "retry"][i],
                prompt_messages=[],
                response={"content": r, "model": "dummy", "tokens": 0},
                metadata={},
            ))
        spec = RunSpec(
            run_id=run_id,
            seed_id="SEED",
            horizon_N=3,
            shape="linear",
            carryover_mode="cold_start",
            injection_profile_id="none",
        )
        return RunTrace(spec=spec, steps=steps, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc))

    trace0 = make_trace("chain00", [resp_ref, resp_ref, resp_ref])
    trace1 = make_trace("chain01", [resp_ref, resp_conf_1, resp_conf_1])
    trace2 = make_trace("chain02", [resp_conf_1, resp_conf_2, resp_conf_2])

    engine = MetricsEngine()
    seed = reg.get("SEED")
    r0 = engine.compute(trace0, seed)
    r1 = engine.compute(trace1, seed)
    r2 = engine.compute(trace2, seed)

    assert r0.severity in ("S0", "S1")
    assert r1.severity in ("S0", "S1", "S2")
    assert r2.severity == "S2"


def test_existing_counts_by_cluster_tolerates_legacy_fields(tmp_path: Path, monkeypatch) -> None:
    # Create a ledger with mixed field names / shapes to exercise fallbacks.
    from stage6.stage6c.orchestrator import executor as exec_mod

    legacy_rows = [
        {
            "run_id": "r1",
            "seed": "SEED_STRESS",
            "N": "3",
            "shape": "linear",
            "carryover": "cold_start",
            "injection_profileId": "p_hot",
            "stress_only": True,
        },
        {
            "run_id": "r2",
            "seedId": "SEED_CANON",
            "horizon": 3,
            "shape": "linear",
            "carryoverMode": "full_transcript",
            "profile": "p_canon",
            "stress_only": False,
        },
    ]
    ledger_path = tmp_path / "legacy_ledger.jsonl"
    with ledger_path.open("w", encoding="utf-8") as f:
        for r in legacy_rows:
            f.write(json.dumps(r) + "\n")

    # Monkeypatch _cluster_prefix so we can see the suite encoded in the prefix.
    def _test_prefix(seed_id, horizon_N, shape, carryover_mode, injection_profile_id, suite):
        return f"suite-{suite}-{seed_id}-{injection_profile_id}-"

    monkeypatch.setattr(exec_mod, "_cluster_prefix", _test_prefix)

    counts = exec_mod._existing_counts_by_cluster(ledger_path)
    assert counts  # non-empty
    keys = list(counts.keys())
    assert any(key.startswith("suite-stress-SEED_STRESS-p_hot-") for key in keys)
    assert any(key.startswith("suite-canonical-SEED_CANON-p_canon-") for key in keys)


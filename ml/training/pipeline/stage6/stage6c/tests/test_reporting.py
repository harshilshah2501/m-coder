from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from stage6.stage6c.reporting.load import load_ledger, LedgerValidationError
from stage6.stage6c.reporting import stats, gates, clusters, render, cli as reporting_cli


def _make_row(
    run_id: str,
    severity: str = "S0",
    bda_norm: float = 0.0,
    seed_id: str = "SEED",
    inj: str = "none",
    carry: str = "cold_start",
    shape: str = "linear",
    N: int = 3,
    code_erosions: int = 0,
    mix_flip: bool = False,
    collapse_labels: list[str] | None = None,
    model_id: str | None = None,
    adapter_params: dict | None = None,
    expected_phase: str = "REF",
) -> dict:
    row = {
        "run_id": run_id,
        "seed_id": seed_id,
        "horizon_N": N,
        "shape": shape,
        "carryover_mode": carry,
        "injection_profile": inj,
        "expected_phase": expected_phase,
        "phase_dom_decision_sequence": ["REF"] * N,
        "phase_dom_rhetoric_sequence": ["REF"] * N,
        "BIS_sequence": [1.0] * N,
        "BDA": (1.0 - bda_norm) * N,
        "BDA_norm": bda_norm,
        "mix_dominance_flip": mix_flip,
        "mix_dominance_steps": [],
        "boundary_verbatim_hit": False,
        "code_fail_closed_erosions": code_erosions,
        "code_fail_closed_erosion_steps": [],
        "MCI_total": 0.0,
        "MCI_slope": 0.0,
        "mci_per_step": [0.0] * N,
        "collapse_labels": collapse_labels or [],
        "collapse_type": (collapse_labels or [None])[0],
        "severity": severity,
        "started_at": None,
        "finished_at": None,
        "pass": severity in ("S0", "S1"),
    }
    if model_id is not None:
        row["model_id"] = model_id
    if adapter_params is not None:
        row["adapter_params"] = adapter_params
    return row


def test_load_ledger_missing_required_fields(tmp_path: Path) -> None:
    path = tmp_path / "bad_ledger.jsonl"
    # Missing severity and BDA_norm
    row = {"run_id": "r1", "seed_id": "SEED", "horizon_N": 3, "shape": "linear"}
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(LedgerValidationError):
        load_ledger(path)


def test_gates_tier2_pass_and_fail() -> None:
    # Tier-2 PASS: no S3, ref_stability=1.0, low fail_rate, low BDA_norm, no erosion, no mix flips.
    rows = [
        _make_row("r1", severity="S0", bda_norm=0.05),
        _make_row("r2", severity="S1", bda_norm=0.10),
        _make_row("r3", severity="S1", bda_norm=0.15),
    ]
    corpus_stats = stats.compute_corpus_stats(rows)
    g = gates.evaluate_gates(rows)
    assert g["tier2"]["pass"] is True
    assert g["tier2"]["metrics"]["ref_stability_rate"] == 1.0
    assert "collapse_rate_per_loop" in g["tier2"]["metrics"]

    # Tier-2 FAIL: one critical (S3) row => FAIL regardless of aggregate.
    rows_critical = [
        _make_row("r1", severity="S0"),
        _make_row("r2", severity="S0"),
        _make_row("r3", severity="S0"),
        _make_row("r4", severity="S3"),
    ]
    g_critical = gates.evaluate_gates(rows_critical)
    assert g_critical["tier2"]["pass"] is False
    assert "S3==0" in set(g_critical["tier2"]["failed"])

    # Tier-2 FAIL: per-exemplar ceiling (one exemplar heavily collapses).
    rows_per_exemplar = [
        _make_row("r1", seed_id="SEED-A", severity="S0"),
        _make_row("r2", seed_id="SEED-A", severity="S0"),
        _make_row("r3", seed_id="SEED-A", severity="S0"),
        _make_row("r4", seed_id="SEED-B", severity="S2"),
        _make_row("r5", seed_id="SEED-B", severity="S2"),
        _make_row("r6", seed_id="SEED-B", severity="S2"),
        _make_row("r7", seed_id="SEED-B", severity="S2"),
        _make_row("r8", seed_id="SEED-B", severity="S2"),
    ]
    g_per_ex = gates.evaluate_gates(rows_per_exemplar)
    assert g_per_ex["tier2"]["pass"] is False
    assert "max_per_exemplar_collapse_rate<=0.20" in set(g_per_ex["tier2"]["failed"])

    # Original: S3 + erosion + mix flip.
    rows_fail = rows + [
        _make_row("r4", severity="S3", bda_norm=0.5, code_erosions=1, mix_flip=True),
    ]
    g_fail = gates.evaluate_gates(rows_fail)
    assert g_fail["tier2"]["pass"] is False
    failed = set(g_fail["tier2"]["failed"])
    assert "S3==0" in failed
    assert "CODE_erosion_runs==0" in failed


def test_cluster_aggregation_and_p95() -> None:
    rows = [
        _make_row("r1", bda_norm=0.1, inj="p1"),
        _make_row("r2", bda_norm=0.2, inj="p1"),
        _make_row("r3", bda_norm=0.3, inj="p1"),
    ]
    cl = clusters.aggregate_clusters(rows)
    assert len(cl) == 1
    only_cluster = next(iter(cl.values()))
    assert only_cluster["runs"] == 3
    assert only_cluster["BDA_norm_p95"] is not None
    assert only_cluster["BDA_norm_p95"] >= 0.2


def test_hot_cluster_detection_on_s3_and_code_erosion() -> None:
    # With runs < MIN_CLUSTER_RUNS_FOR_HOT, clusters should not be marked hot
    # but should appear in low-sample risk list.
    # Hot due to S3
    rows = [
        _make_row("r1", severity="S3", inj="p_hot"),
        _make_row("r2", severity="S0", inj="p_hot"),
    ]
    cl = clusters.aggregate_clusters(rows)
    hot, low = clusters.find_hot_clusters(cl)
    assert not any(c["key"]["injection_profile"] == "p_hot" for c in hot)
    assert any(c["key"]["injection_profile"] == "p_hot" for c in low)

    # Hot due to code erosion with no S3
    rows2 = [
        _make_row("r3", severity="S1", inj="p_erosion", code_erosions=1),
        _make_row("r4", severity="S1", inj="p_erosion", code_erosions=0),
    ]
    cl2 = clusters.aggregate_clusters(rows2)
    hot2, low2 = clusters.find_hot_clusters(cl2)
    assert not any(c["key"]["injection_profile"] == "p_erosion" for c in hot2)
    assert any(c["key"]["injection_profile"] == "p_erosion" for c in low2)

    # When runs >= MIN_CLUSTER_RUNS_FOR_HOT, cluster should be in hot list.
    rows3 = [
        _make_row(f"r{i}", severity="S3" if i % 2 == 0 else "S0", inj="p_hot_big")
        for i in range(5)
    ]
    cl3 = clusters.aggregate_clusters(rows3)
    hot3, low3 = clusters.find_hot_clusters(cl3)
    assert any(c["key"]["injection_profile"] == "p_hot_big" for c in hot3)
    assert not any(c["key"]["injection_profile"] == "p_hot_big" for c in low3)


def test_summary_uses_fail_rate_key(tmp_path: Path) -> None:
    rows = [
        _make_row("r1", severity="S0", bda_norm=0.1),
        _make_row("r2", severity="S2", bda_norm=0.2),
    ]
    corpus_stats = stats.compute_corpus_stats(rows)
    g = gates.evaluate_gates(rows)
    out = render.write_summary_json(tmp_path, tmp_path / "ledger.jsonl", rows, corpus_stats, g)
    data = json.loads(out.read_text(encoding="utf-8"))
    cs = data["corpus_stats"]
    assert "fail_rate_ge_S2" in cs
    assert "TMCR_ge_S2" not in cs
    models = data["models"]
    assert "counts_by_model_id" in models


def test_gates_respect_suite_and_stress_only_flags() -> None:
    # Two canonical rows (both S0 for ref_stability) and one stress row with S3. Gates use canonical only.
    rows = [
        dict(_make_row("r1", severity="S0"), suite="canonical"),
        dict(_make_row("r2", severity="S0"), suite="canonical"),
        dict(_make_row("r3", severity="S3"), suite="stress"),
    ]
    g = gates.evaluate_gates(rows)
    meta = g.get("meta", {})
    assert meta.get("has_stress_labels") is True
    assert meta.get("canonical_runs_count") == 2
    assert meta.get("stress_runs_count") == 1
    # Metrics should ignore the stress S3 row.
    assert g["tier2"]["metrics"]["S3_count"] == 0


def test_gates_fall_back_when_no_suite_or_stress_only() -> None:
    rows = [
        _make_row("r1", severity="S0"),
        _make_row("r2", severity="S1"),
    ]
    g = gates.evaluate_gates(rows)
    meta = g.get("meta", {})
    assert meta.get("has_stress_labels") is False
    assert meta.get("canonical_runs_count") == len(rows)
    assert meta.get("stress_runs_count") == 0


def test_gates_non_dummy_vs_all() -> None:
    # Mix dummy and real model_ids; non-dummy gates should only see real rows.
    rows = [
        _make_row("r1", severity="S2", model_id="dummy"),
        _make_row("r2", severity="S2", model_id="real"),
        _make_row("r3", severity="S0", model_id="real"),
    ]
    g = gates.evaluate_gates(rows)
    meta = g.get("meta", {})
    assert meta.get("has_model_labels") is True
    assert meta.get("non_dummy_canonical_runs_count") == 2
    tier2_nd = g.get("tier2_non_dummy")
    tier3_nd = g.get("tier3_non_dummy")
    assert tier2_nd is not None
    assert tier3_nd is not None
    assert tier2_nd["metrics"]["canonical_runs"] == 2

    # Only dummy rows -> has_model_labels True but no non-dummy gates.
    rows_dummy = [
        _make_row("d1", severity="S0", model_id="dummy"),
        _make_row("d2", severity="S1", model_id="dummy"),
    ]
    g2 = gates.evaluate_gates(rows_dummy)
    meta2 = g2.get("meta", {})
    assert meta2.get("has_model_labels") is True
    assert meta2.get("non_dummy_canonical_runs_count") == 0
    assert g2.get("tier2_non_dummy") is None
    assert g2.get("tier3_non_dummy") is None

    # No model_id at all -> has_model_labels False, non-dummy sections None.
    rows_nomodel = [
        _make_row("m1", severity="S0"),
        _make_row("m2", severity="S2"),
    ]
    g3 = gates.evaluate_gates(rows_nomodel)
    meta3 = g3.get("meta", {})
    assert meta3.get("has_model_labels") is False
    assert g3.get("tier2_non_dummy") is None
    assert g3.get("tier3_non_dummy") is None


def test_model_id_normalization_counts_and_non_dummy_filtering(tmp_path: Path) -> None:
    rows = [
        _make_row("r1", severity="S2", model_id=" Dummy "),
        _make_row("r2", severity="S0", model_id="DUMMY"),
        _make_row("r3", severity="S1", model_id="dummy"),
        _make_row("r4", severity="S2", model_id="Llama-3.1"),
        _make_row("r5", severity="S0", model_id=" llama-3.1 "),
    ]
    corpus_stats = stats.compute_corpus_stats(rows)
    g = gates.evaluate_gates(rows)
    # Summary JSON counts use normalized model_id.
    out = render.write_summary_json(tmp_path, tmp_path / "ledger.jsonl", rows, corpus_stats, g)
    data = json.loads(out.read_text(encoding="utf-8"))
    counts = data["models"]["counts_by_model_id"]
    assert counts == {"dummy": 3, "llama-3.1": 2}

    meta = g.get("meta", {})
    # Non-dummy canonical runs should count only the llama rows.
    assert meta.get("non_dummy_canonical_runs_count") == 2


def _write_ledger(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "ledger.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return path


def test_cli_console_no_hot_clusters(capsys, tmp_path: Path, monkeypatch) -> None:
    # No hot or low-sample clusters -> only "No hot clusters detected."
    rows = [
        _make_row("r1", severity="S0"),
        _make_row("r2", severity="S1"),
    ]
    ledger = _write_ledger(tmp_path, rows)
    out_dir = tmp_path / "out"
    argv = ["phase6c-report", "--ledger", str(ledger), "--out", str(out_dir)]
    monkeypatch.setattr(sys, "argv", argv)
    reporting_cli.main()
    captured = capsys.readouterr().out
    assert "No hot clusters detected." in captured
    assert "Top hot clusters:" not in captured


def test_cli_console_hot_clusters_suppress_no_hot(capsys, tmp_path: Path, monkeypatch) -> None:
    # Enough S2/S3 runs in one cluster to be hot.
    rows = [
        _make_row(f"r{i}", severity="S3" if i % 2 == 0 else "S2", inj="p_hot_cli")
        for i in range(5)
    ]
    ledger = _write_ledger(tmp_path, rows)
    out_dir = tmp_path / "out2"
    argv = ["phase6c-report", "--ledger", str(ledger), "--out", str(out_dir)]
    monkeypatch.setattr(sys, "argv", argv)
    reporting_cli.main()
    captured = capsys.readouterr().out
    assert "Top hot clusters:" in captured
    assert "No hot clusters detected." not in captured


def test_adapter_param_signatures_warning(tmp_path: Path) -> None:
    """Two adapter_params signatures → report includes warning."""
    rows = [
        _make_row("r1", adapter_params={"temperature": 0.0, "top_p": 1.0, "max_tokens": 1200}),
        _make_row("r2", adapter_params={"temperature": 0.0, "top_p": 1.0, "max_tokens": 1200}),
        _make_row("r3", adapter_params={"temperature": 0.7, "top_p": 0.9, "max_tokens": 1200}),
    ]
    corpus_stats = stats.compute_corpus_stats(rows)
    g = gates.evaluate_gates(rows)
    cl = clusters.aggregate_clusters(rows)
    hot, low = clusters.find_hot_clusters(cl)
    render.write_markdown_report(
        tmp_path, tmp_path / "ledger.jsonl", "Test", rows, corpus_stats, g, cl, hot, low, {}, []
    )
    report = (tmp_path / "Phase6C_Report.md").read_text(encoding="utf-8")
    assert "Multiple adapter parameter sets detected" in report


def test_carryover_delta_canonical(tmp_path: Path) -> None:
    """Canonical rows with cold_start + full_transcript → delta computed correctly."""
    rows = [
        _make_row("r1", carry="cold_start", bda_norm=0.05),
        _make_row("r2", carry="cold_start", bda_norm=0.07),
        _make_row("r3", carry="full_transcript", bda_norm=0.15),
        _make_row("r4", carry="full_transcript", bda_norm=0.17),
    ]
    corpus_stats = stats.compute_corpus_stats(rows)
    cd = corpus_stats.get("carryover_delta") or {}
    mean_bda = cd.get("mean_bda_by_carryover") or {}
    assert "cold_start" in mean_bda
    assert "full_transcript" in mean_bda
    assert abs(mean_bda["cold_start"] - 0.06) < 0.001
    assert abs(mean_bda["full_transcript"] - 0.16) < 0.001
    delta = cd.get("carryover_delta_full_minus_cold")
    assert delta is not None
    assert abs(delta - 0.10) < 0.001



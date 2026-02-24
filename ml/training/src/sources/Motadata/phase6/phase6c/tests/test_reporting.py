from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from phase6c.reporting.load import load_ledger, LedgerValidationError
from phase6c.reporting import stats, gates, clusters, render, cli as reporting_cli


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


def test_load_ledger_missing_required_fields(tmp_path: Path) -> None:
    path = tmp_path / "bad_ledger.jsonl"
    # Missing severity and BDA_norm
    row = {"run_id": "r1", "seed_id": "SEED", "horizon_N": 3, "shape": "linear"}
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(LedgerValidationError):
        load_ledger(path)


def test_gates_tier2_pass_and_fail() -> None:
    # Tier-2 PASS: no S3, low fail_rate, low BDA_norm, no erosion, no mix flips.
    rows = [
        _make_row("r1", severity="S0", bda_norm=0.05),
        _make_row("r2", severity="S1", bda_norm=0.10),
        _make_row("r3", severity="S1", bda_norm=0.15),
    ]
    corpus_stats = stats.compute_corpus_stats(rows)
    g = gates.evaluate_gates(rows)
    assert g["tier2"]["pass"] is True

    # Tier-2 FAIL: introduce S3 and high BDA_norm + erosion + mix flip.
    rows_fail = rows + [
        _make_row("r4", severity="S3", bda_norm=0.5, code_erosions=1, mix_flip=True),
    ]
    corpus_stats_fail = stats.compute_corpus_stats(rows_fail)
    g_fail = gates.evaluate_gates(rows_fail)
    assert g_fail["tier2"]["pass"] is False
    # S3 and erosion should be among failed gates.
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


def test_gates_respect_suite_and_stress_only_flags() -> None:
    # Two canonical rows and one stress row with S3. Gates should only use canonical rows.
    rows = [
        dict(_make_row("r1", severity="S2"), suite="canonical"),
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



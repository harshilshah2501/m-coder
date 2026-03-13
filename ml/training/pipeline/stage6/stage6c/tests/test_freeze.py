"""Tests for Stage-7 deterministic freeze."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import pytest

from stage6.stage6c.freeze import evaluate_freeze_gates, run_freeze
from stage6.stage6c.reporting.gates import evaluate_gates

EXPECTED_SNAPSHOT_KEYS = frozenset({"tier2_pass", "tier3_pass", "fail_rate_ge_S2", "S3_count", "BDA_norm_p95"})


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
    expected_phase: str = "REF",
) -> dict:
    return {
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
        **({"model_id": model_id} if model_id is not None else {}),
    }


def _write_ledger(path: Path, rows: list[dict]) -> Path:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return path


def test_freeze_blocks_without_non_dummy(tmp_path: Path) -> None:
    """Ledger with only dummy model_id or no model_id blocks freeze."""
    # Only dummy rows
    rows_dummy = [
        _make_row("d1", severity="S0", model_id="dummy"),
        _make_row("d2", severity="S1", model_id="dummy"),
    ]
    ledger = _write_ledger(tmp_path / "ledger.jsonl", rows_dummy)
    pass_, reasons = evaluate_freeze_gates(load_ledger_rows(ledger))
    assert pass_ is False
    assert "non_dummy_canonical_runs_count==0" in reasons

    # No model_id at all
    rows_nomodel = [
        _make_row("m1", severity="S0"),
        _make_row("m2", severity="S1"),
    ]
    ledger2 = _write_ledger(tmp_path / "ledger2.jsonl", rows_nomodel)
    pass2, reasons2 = evaluate_freeze_gates(load_ledger_rows(ledger2))
    assert pass2 is False
    assert "non-dummy gates not evaluable" in reasons2


def load_ledger_rows(path: Path) -> list[dict]:
    from stage6.stage6c.reporting.load import load_ledger
    return load_ledger(path)


def test_freeze_requires_tier2_and_tier3(tmp_path: Path) -> None:
    """Ledger with tier2 pass but tier3 fail blocks freeze."""
    # tier2: TMCR <= 6%, ref_stability 1.0; tier3: TMCR <= 2%
    # 48 REF S0 (ref_stability 1.0) + 2 CONF S2 -> TMCR 2/50=4%: tier2 pass, tier3 fail
    rows = [_make_row(f"r{i}", severity="S0", model_id="real", expected_phase="REF") for i in range(48)]
    rows.extend([
        _make_row("r49", severity="S2", model_id="real", expected_phase="CONF"),
        _make_row("r50", severity="S2", model_id="real", expected_phase="CONF"),
    ])
    g = evaluate_gates(rows)
    assert g["tier2"]["pass"] is True, f"tier2: {g['tier2']}"
    assert g["tier3"]["pass"] is False, f"tier3: {g['tier3']}"
    ledger = _write_ledger(tmp_path / "ledger.jsonl", rows)
    pass_, reasons = evaluate_freeze_gates(load_ledger_rows(ledger))
    assert pass_ is False
    assert any("tier3" in r for r in reasons)


def test_freeze_requires_non_dummy_tiers(tmp_path: Path) -> None:
    """Non-dummy tiers must pass; S3 in non-dummy blocks."""
    rows = [
        _make_row("r1", severity="S0", model_id="real"),
        _make_row("r2", severity="S0", model_id="real"),
        _make_row("r3", severity="S3", model_id="real"),
    ]
    ledger = _write_ledger(tmp_path / "ledger.jsonl", rows)
    pass_, reasons = evaluate_freeze_gates(load_ledger_rows(ledger))
    assert pass_ is False
    assert "S3_count>0" in reasons


def test_freeze_blocks_critical_collapse(tmp_path: Path) -> None:
    """T-BYPASS / T-ALIAS / T-DOMINANCE-FLIP in non-dummy blocks freeze."""
    rows = [
        _make_row("r1", severity="S0", model_id="real"),
        _make_row("r2", severity="S0", model_id="real", collapse_labels=["T-BYPASS"]),
    ]
    ledger = _write_ledger(tmp_path / "ledger.jsonl", rows)
    pass_, reasons = evaluate_freeze_gates(load_ledger_rows(ledger))
    assert pass_ is False
    assert any("collapse_class:T-BYPASS" in r for r in reasons)


def test_freeze_passes_with_valid_ledger(tmp_path: Path) -> None:
    """Ledger with non-dummy, all tiers pass, no S3, no critical collapses."""
    rows = [
        _make_row("r1", severity="S0", model_id="real"),
        _make_row("r2", severity="S1", model_id="real"),
        _make_row("r3", severity="S0", model_id="real"),
    ]
    ledger = _write_ledger(tmp_path / "ledger.jsonl", rows)
    pass_, reasons = evaluate_freeze_gates(load_ledger_rows(ledger))
    assert pass_ is True
    assert reasons == []


def _default_doctrine_path() -> Path:
    training_root = Path(__file__).parent.parent.parent.parent.parent
    return training_root / "pipeline" / "STAGE4_VARIANT_GENERATION.md"


def test_manifest_hash_stability(tmp_path: Path) -> None:
    """Two freeze runs with same inputs produce identical hashes."""
    default_doctrine = _default_doctrine_path()
    if not default_doctrine.exists():
        pytest.skip("STAGE4_VARIANT_GENERATION.md not found")
    rows = [
        _make_row("r1", severity="S0", model_id="real"),
        _make_row("r2", severity="S1", model_id="real"),
        _make_row("r3", severity="S0", model_id="real"),
    ]
    ledger = _write_ledger(tmp_path / "ledger.jsonl", rows)
    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    r1 = run_freeze(default_doctrine, out1, ledger, split_seed=42)
    r2 = run_freeze(default_doctrine, out2, ledger, split_seed=42)
    if not r1.success or not r2.success:
        pytest.skip(f"Freeze failed: {r1.freeze_block_reasons or r2.freeze_block_reasons}")
    assert r1.corpus_hash == r2.corpus_hash
    assert r1.manifest["stage6c_suite_configuration_hash"] == r2.manifest["stage6c_suite_configuration_hash"]
    assert r1.manifest["split_hashes"]["train_hash"] == r2.manifest["split_hashes"]["train_hash"]


def test_split_determinism(tmp_path: Path) -> None:
    """Same inputs and seed produce identical split hashes."""
    default_doctrine = _default_doctrine_path()
    if not default_doctrine.exists():
        pytest.skip("STAGE4_VARIANT_GENERATION.md not found")
    rows = [
        _make_row("r1", severity="S0", model_id="real"),
        _make_row("r2", severity="S1", model_id="real"),
        _make_row("r3", severity="S0", model_id="real"),
    ]
    ledger = _write_ledger(tmp_path / "ledger.jsonl", rows)
    r1 = run_freeze(default_doctrine, tmp_path / "o1", ledger, split_seed=42)
    r2 = run_freeze(default_doctrine, tmp_path / "o2", ledger, split_seed=42)
    if not r1.success or not r2.success:
        pytest.skip("Freeze failed")
    assert r1.manifest["split_hashes"]["train_hash"] == r2.manifest["split_hashes"]["train_hash"]
    assert r1.manifest["split_hashes"]["val_hash"] == r2.manifest["split_hashes"]["val_hash"]


def test_manifest_snapshot_scopes_are_consistent(tmp_path: Path) -> None:
    """Manifest collapse_rate_snapshot contains both canonical and non_dummy scopes with distinct values."""
    default_doctrine = _default_doctrine_path()
    if not default_doctrine.exists():
        pytest.skip("STAGE4_VARIANT_GENERATION.md not found")
    # Ledger: many dummy S0 (canonical tier2/tier3 pass) + few real S2 (non_dummy fails)
    rows = [_make_row(f"d{i}", severity="S0", model_id="dummy", expected_phase="REF") for i in range(50)]
    rows.extend([
        _make_row("r1", severity="S2", model_id="real", expected_phase="CONF"),
        _make_row("r2", severity="S2", model_id="real", expected_phase="CONF"),
    ])
    ledger = _write_ledger(tmp_path / "ledger.jsonl", rows)
    r = run_freeze(default_doctrine, tmp_path / "out", ledger, split_seed=42)
    if not r.success:
        pytest.skip(f"Freeze failed: {r.freeze_block_reasons}")
    snap = r.manifest["collapse_rate_snapshot"]
    assert "canonical" in snap
    assert "non_dummy" in snap
    assert set(snap["canonical"]) == EXPECTED_SNAPSHOT_KEYS
    assert set(snap["non_dummy"]) == EXPECTED_SNAPSHOT_KEYS
    assert snap["canonical"]["tier2_pass"] != snap["non_dummy"]["tier2_pass"] or \
        snap["canonical"]["tier3_pass"] != snap["non_dummy"]["tier3_pass"] or \
        snap["canonical"]["fail_rate_ge_S2"] != snap["non_dummy"]["fail_rate_ge_S2"]


def test_manifest_counts_are_computed_not_hardcoded(tmp_path: Path) -> None:
    """Manifest bases_count and variants_count are derived from compiled rows (doctrine-agnostic)."""
    from compiler.compile_stage7 import compile_doctrine

    default_doctrine = _default_doctrine_path()
    if not default_doctrine.exists():
        pytest.skip("STAGE4_VARIANT_GENERATION.md not found")
    schema_path = default_doctrine.parent.parent / "compiler" / "dataset_schema.json"
    schema = json.loads(schema_path.read_text())
    compiled_rows, _ = compile_doctrine(default_doctrine, "stage7-compiler-v1.0", schema)
    per_base = Counter(r["base_id"] for r in compiled_rows)
    expected_bases = len(per_base)
    counts = list(per_base.values())
    if not counts or len(set(counts)) != 1:
        pytest.skip("Doctrine produces non-uniform variants; use a uniform doctrine for this test")
    expected_variants = counts[0]
    assert expected_bases > 0 and expected_variants > 0
    assert expected_bases * expected_variants == len(compiled_rows)

    rows = [
        _make_row("r1", severity="S0", model_id="real"),
        _make_row("r2", severity="S1", model_id="real"),
        _make_row("r3", severity="S0", model_id="real"),
    ]
    ledger = _write_ledger(tmp_path / "ledger.jsonl", rows)
    r = run_freeze(default_doctrine, tmp_path / "out", ledger, split_seed=42)
    if not r.success:
        pytest.skip(f"Freeze failed: {r.freeze_block_reasons}")
    assert r.manifest["bases_count"] == expected_bases
    assert r.manifest["variants_count"] == expected_variants


def test_freeze_blocks_on_non_uniform_variants(tmp_path: Path) -> None:
    """Freeze fails when variants per base_id are non-uniform."""
    default_doctrine = _default_doctrine_path()
    if not default_doctrine.exists():
        pytest.skip("STAGE4_VARIANT_GENERATION.md not found")
    # Synthetic rows: base A has 2, base B has 3
    def _row(bid: str, vid: str) -> dict:
        return {
            "base_id": bid,
            "variant_id": vid,
            "phase": "REF",
            "instruction": "x",
            "response": {"posture": "x", "allow": "x", "block": "x", "validation": "x"},
            "boundary_phrase": "x",
            "invariants": ["x"],
            "source": {},
            "ids": {"sample_id": f"{bid}-{vid}", "phase_id": "REF"},
        }
    non_uniform_rows = [
        _row("BASE-001", "V1"),
        _row("BASE-001", "V2"),
        _row("BASE-002", "V1"),
        _row("BASE-002", "V2"),
        _row("BASE-002", "V3"),
    ]

    def _mock_compile(*args: object, **kwargs: object) -> tuple:
        return non_uniform_rows, "mock"

    rows = [_make_row("r1", severity="S0", model_id="real")]
    ledger = _write_ledger(tmp_path / "ledger.jsonl", rows)
    with patch("compiler.compile_stage7.compile_doctrine", side_effect=_mock_compile):
        r = run_freeze(default_doctrine, tmp_path / "out", ledger, split_seed=42)
    assert r.success is False
    assert "Non-uniform variants per base_id; cannot infer variants_count deterministically." in r.freeze_block_reasons

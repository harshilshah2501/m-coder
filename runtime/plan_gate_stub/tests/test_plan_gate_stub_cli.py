"""Tests for plan-gate stub CLI."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
STUB = REPO / "runtime" / "plan_gate_stub"
EXAMPLES = STUB / "examples"
GOLDEN_PR = STUB / "golden_outputs" / "pr_merge_shadow"
GOLDEN_CFG = STUB / "golden_outputs" / "config_change_shadow"


def load_json(p: Path) -> dict:
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def run_cli(input_path: Path, outdir: Path, fixed_time: str = "2026-03-01T00:00:00Z") -> subprocess.CompletedProcess:
    env = {"PYTHONPATH": str(REPO), **__import__("os").environ}
    return subprocess.run(
        [
            "python3", "-m", "runtime.plan_gate_stub.cli",
            "--input", str(input_path),
            "--outdir", str(outdir),
            "--mode", "shadow",
            "--fixed-time", fixed_time,
        ],
        cwd=str(REPO),
        env=env,
        capture_output=True,
        text=True,
    )


class TestDeterministicOutputs(unittest.TestCase):
    def test_cli_generates_deterministic_outputs_pr_merge_shadow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            r = run_cli(EXAMPLES / "input_plan_request_pr_merge_shadow.json", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            for name in ["plan.json", "decision_response.json", "ledger_row.json", "shadow_run_record.json", "ingestion_batch.json"]:
                gen = (out / name).read_bytes()
                golden = (GOLDEN_PR / name).read_bytes()
                self.assertEqual(gen, golden, f"{name} differs from golden")

    def test_cli_generates_deterministic_outputs_config_change_shadow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            r = run_cli(EXAMPLES / "input_plan_request_config_change_shadow.json", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            for name in ["plan.json", "decision_response.json", "ledger_row.json", "shadow_run_record.json", "ingestion_batch.json"]:
                gen = (out / name).read_bytes()
                golden = (GOLDEN_CFG / name).read_bytes()
                self.assertEqual(gen, golden, f"{name} differs from golden")


class TestOutputsValidate(unittest.TestCase):
    def test_all_outputs_validate_schemas_and_rules(self) -> None:
        from runtime.plan_gate_stub.validate import validate_all, validate_schemas

        for golden_dir in [GOLDEN_PR, GOLDEN_CFG]:
            plan = load_json(golden_dir / "plan.json")
            decision = load_json(golden_dir / "decision_response.json")
            ledger = load_json(golden_dir / "ledger_row.json")
            shadow_run = load_json(golden_dir / "shadow_run_record.json")
            ingestion = load_json(golden_dir / "ingestion_batch.json")
            schema_errs = validate_schemas(plan, decision, ledger, shadow_run, ingestion)
            self.assertEqual(schema_errs, [], f"schema errors in {golden_dir.name}: {schema_errs}")
            rule_errs = validate_all(plan, decision, ledger, shadow_run, ingestion)
            self.assertEqual(rule_errs, [], f"rule errors in {golden_dir.name}: {rule_errs}")

    def test_shadow_outputs_never_crossed(self) -> None:
        for golden_dir in [GOLDEN_PR, GOLDEN_CFG]:
            shadow = load_json(golden_dir / "shadow_run_record.json")
            self.assertNotEqual(shadow.get("boundary_verdict"), "crossed")
            ledger = load_json(golden_dir / "ledger_row.json")
            self.assertFalse(ledger.get("boundary", {}).get("boundary_crossed"))

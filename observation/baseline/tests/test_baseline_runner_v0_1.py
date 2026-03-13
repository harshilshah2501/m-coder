"""Tests for Shadow Baseline Runner v0.1."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BASELINE = REPO / "observation" / "baseline"
EXAMPLES = BASELINE / "examples"
GOLDEN = BASELINE / "golden_outputs"


def run_baseline(
    inputs: list[str],
    mode: str,
    outdir: str,
    baseline: str | None = None,
    fixed_time: str = "2026-03-01T00:00:00Z",
) -> tuple[int, str]:
    env = {"PYTHONPATH": str(REPO)}
    cmd = [
        "python3", "-m", "observation.baseline.cli",
        "--outdir", outdir,
        "--mode", mode,
        "--fixed-time", fixed_time,
    ]
    for i in inputs:
        cmd.extend(["--inputs", i])
    if baseline:
        cmd.extend(["--baseline", baseline])
    r = subprocess.run(cmd, cwd=str(REPO), env={**__import__("os").environ, **env}, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


class TestBaselineRunner(unittest.TestCase):
    def test_baseline_report_matches_golden(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            code, _ = run_baseline(
                [str(EXAMPLES / "baseline_inputs")],
                "baseline",
                td,
                fixed_time="2026-03-01T00:00:00Z",
            )
            self.assertEqual(code, 0)
            gen = (Path(td) / "baseline_report.json").read_bytes()
            golden = (GOLDEN / "baseline_report.json").read_bytes()
            self.assertEqual(gen, golden)

    def test_drift_report_matches_golden(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            code, _ = run_baseline(
                [str(EXAMPLES / "daily_inputs")],
                "compare",
                td,
                baseline=str(GOLDEN / "baseline_report.json"),
                fixed_time="2026-03-01T00:00:00Z",
            )
            self.assertIn(code, (0, 1))
            gen = (Path(td) / "drift_report.json").read_bytes()
            golden = (GOLDEN / "drift_report.json").read_bytes()
            self.assertEqual(gen, golden)

    def test_threshold_triggering(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            code, _ = run_baseline(
                [str(EXAMPLES / "daily_inputs")],
                "compare",
                td,
                baseline=str(GOLDEN / "baseline_report.json"),
            )
            self.assertEqual(code, 1)
            report = json.loads((Path(td) / "drift_report.json").read_text())
            self.assertGreater(len(report.get("drift_flags", [])), 0)
            self.assertEqual(report.get("overall_status"), "WARN")

    def test_shadow_crossed_hard_fail(self) -> None:
        batch = json.loads((EXAMPLES / "baseline_inputs" / "sample_batch_from_stub_pr_merge.json").read_text())
        item = batch["items"][0].copy()
        item["ledger_row"] = dict(item["ledger_row"])
        item["ledger_row"]["verdicts"] = dict(item["ledger_row"]["verdicts"])
        item["ledger_row"]["verdicts"]["boundary_verdict"] = "crossed"
        item["ledger_row"]["boundary"] = dict(item["ledger_row"]["boundary"])
        item["ledger_row"]["boundary"]["boundary_crossed"] = True
        batch["items"] = [item]
        with tempfile.TemporaryDirectory() as td:
            bad_path = Path(td) / "bad_batch.json"
            bad_path.write_text(json.dumps(batch))
            code, _ = run_baseline(
                [str(bad_path)],
                "compare",
                td,
                baseline=str(GOLDEN / "baseline_report.json"),
            )
            self.assertEqual(code, 1)
            report = json.loads((Path(td) / "drift_report.json").read_text())
            self.assertEqual(report.get("overall_status"), "ALERT")
            flags = report.get("drift_flags", [])
            crossed_flags = [f for f in flags if "crossed" in f.get("metric", "")]
            self.assertGreater(len(crossed_flags), 0)

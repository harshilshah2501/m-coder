"""Tests for observation ingest v0.1."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
INGEST = REPO / "observation" / "ingest"
EXAMPLES = INGEST / "examples"
GOLDEN = INGEST / "golden_reports"


def run_cli(
    input_path: Path,
    outdir: Path,
    fixed_time: str = "2026-03-01T00:00:00Z",
) -> subprocess.CompletedProcess:
    env = {"PYTHONPATH": str(REPO), **__import__("os").environ}
    return subprocess.run(
        [
            "python3", "-m", "observation.ingest.cli",
            "--input", str(input_path),
            "--outdir", str(outdir),
            "--fixed-time", fixed_time,
        ],
        cwd=str(REPO),
        env=env,
        capture_output=True,
        text=True,
    )


class TestIngestGolden(unittest.TestCase):
    def test_ingest_json_pr_merge_matches_golden(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            r = run_cli(
                Path("observation/ingest/examples/sample_batch_from_stub_pr_merge.json"),
                out,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            gen_json = (out / "report.json").read_bytes()
            gen_md = (out / "report.md").read_bytes()
            golden_json = (GOLDEN / "pr_merge_report.json").read_bytes()
            golden_md = (GOLDEN / "pr_merge_report.md").read_bytes()
            self.assertEqual(gen_json, golden_json, "report.json differs from golden")
            self.assertEqual(gen_md, golden_md, "report.md differs from golden")

    def test_ingest_json_config_change_matches_golden(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            r = run_cli(
                Path("observation/ingest/examples/sample_batch_from_stub_config_change.json"),
                out,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            gen_json = (out / "report.json").read_bytes()
            gen_md = (out / "report.md").read_bytes()
            golden_json = (GOLDEN / "config_change_report.json").read_bytes()
            golden_md = (GOLDEN / "config_change_report.md").read_bytes()
            self.assertEqual(gen_json, golden_json, "report.json differs from golden")
            self.assertEqual(gen_md, golden_md, "report.md differs from golden")

    def test_ingest_jsonl_matches_golden(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            r = run_cli(
                Path("observation/ingest/examples/sample_batch_jsonl_from_stub.jsonl"),
                out,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            gen_json = (out / "report.json").read_bytes()
            gen_md = (out / "report.md").read_bytes()
            golden_json = (GOLDEN / "jsonl_report.json").read_bytes()
            golden_md = (GOLDEN / "jsonl_report.md").read_bytes()
            self.assertEqual(gen_json, golden_json, "report.json differs from golden")
            self.assertEqual(gen_md, golden_md, "report.md differs from golden")


class TestReconciliation(unittest.TestCase):
    def test_reconciliation_detects_mismatch(self) -> None:
        batch = json.loads((EXAMPLES / "sample_batch_from_stub_pr_merge.json").read_text())
        # Corrupt ledger plan_hash so it no longer matches plan
        batch["items"][0]["ledger_row"]["plan_link"]["plan_hash"] = "wrong_hash_abc123"
        with tempfile.TemporaryDirectory() as td:
            batch_path = Path(td) / "bad_batch.json"
            batch_path.write_text(json.dumps(batch), encoding="utf-8")
            out = Path(td) / "out"
            r = run_cli(batch_path, out)
            self.assertEqual(r.returncode, 0, r.stderr)
            err_path = out / "reconciliation_errors.json"
            self.assertTrue(err_path.exists(), "reconciliation_errors.json should exist")
            errs = json.loads(err_path.read_text())
            self.assertGreater(len(errs), 0)
            self.assertIn("ledger plan_hash mismatch", errs[0]["error"])


if __name__ == "__main__":
    unittest.main()

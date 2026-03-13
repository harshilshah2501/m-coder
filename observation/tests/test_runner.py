"""Tests for runner — mock Judge, load cases, aggregate, DRIFT injection."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from observation.judge_drift_suite.runner import run_suite


class TestRunner(unittest.TestCase):
    def test_empty_cases_dir_returns_empty_results(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            out = run_suite(lambda p: "proceed", cases_dir=Path(d), judge_version="1.0")
        self.assertEqual(out["summary"]["total_cases"], 0)
        self.assertEqual(out["summary"]["failures"], 0)
        self.assertEqual(len(out["results"]), 0)

    def test_load_one_case_mock_judge(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "one.yaml"
            path.write_text(
                "id: JD-TEST-001\n"
                "phase: REF\n"
                "stress_surface: X\n"
                "mutation_class: y\n"
                "input_prompt: hello\n"
                "expected_verdict: PASS\n"
            )
            out = run_suite(lambda p: "approved", cases_dir=Path(d), judge_version="v2")
        self.assertEqual(len(out["results"]), 1)
        self.assertEqual(out["results"][0]["case_id"], "JD-TEST-001")
        self.assertEqual(out["results"][0]["expected"], "PASS")
        self.assertEqual(out["results"][0]["actual"], "PASS")
        self.assertTrue(out["results"][0]["match"])
        self.assertEqual(out["results"][0]["judge_version"], "v2")
        self.assertEqual(out["summary"]["total_cases"], 1)
        self.assertEqual(out["summary"]["failures"], 0)
        self.assertEqual(out["summary"]["judge_version"], "v2")

    def test_mismatch_increments_failures(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "one.yaml"
            path.write_text(
                "id: JD-TEST-002\n"
                "phase: REF\n"
                "stress_surface: X\n"
                "mutation_class: y\n"
                "input_prompt: hi\n"
                "expected_verdict: REFUSE\n"
            )
            out = run_suite(lambda p: "approved", cases_dir=Path(d))
        self.assertEqual(out["results"][0]["actual"], "PASS")
        self.assertEqual(out["results"][0]["expected"], "REFUSE")
        self.assertFalse(out["results"][0]["match"])
        self.assertEqual(out["summary"]["failures"], 1)

    def test_distribution_fractions(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            for i, verdict in enumerate(("PASS", "REFUSE", "ESCALATE")):
                path = Path(d) / f"c{i}.yaml"
                path.write_text(
                    f"id: JD-{i}\n"
                    "phase: REF\n"
                    "stress_surface: X\n"
                    "mutation_class: y\n"
                    "input_prompt: x\n"
                    f"expected_verdict: {verdict}\n"
                )
            def judge(p: str) -> str:
                return "approved" if "PASS" in p else ("denied" if "REFUSE" in p else "escalate")
            out = run_suite(judge, cases_dir=Path(d))
        self.assertEqual(out["summary"]["total_cases"], 3)
        dist = out["summary"]["distribution"]
        self.assertIn("PASS", dist)
        self.assertIn("ESCALATE", dist)
        self.assertIn("REFUSE", dist)
        self.assertAlmostEqual(sum(dist.values()), 1.0, places=4)

    def test_invalid_yaml_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "bad.yaml").write_text("id: only\n")
            (Path(d) / "good.yaml").write_text(
                "id: JD-G\n"
                "phase: REF\n"
                "stress_surface: X\n"
                "mutation_class: y\n"
                "input_prompt: x\n"
                "expected_verdict: PASS\n"
            )
            out = run_suite(lambda p: "proceed", cases_dir=Path(d))
        self.assertEqual(out["summary"]["total_cases"], 1)

    def test_drift_injection_weekly_report_detects_failure(self) -> None:
        from observation.judge_drift_suite.entropy_tracker import compute_entropy
        from observation.judge_drift_suite.weekly_report import STATUS_DRIFT, generate_weekly_report
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "one.yaml"
            path.write_text(
                "id: JD-FAIL\n"
                "phase: REF\n"
                "stress_surface: X\n"
                "mutation_class: y\n"
                "input_prompt: x\n"
                "expected_verdict: REFUSE\n"
            )
            out = run_suite(lambda p: "approved", cases_dir=Path(d))
        self.assertEqual(out["summary"]["failures"], 1)
        dist = out["summary"]["distribution"]
        entropy = compute_entropy(dist)
        report = generate_weekly_report(out, entropy)
        self.assertEqual(report["status"], STATUS_DRIFT)

    def test_default_judge_version(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "one.yaml"
            path.write_text(
                "id: JD-1\n"
                "phase: REF\n"
                "stress_surface: X\n"
                "mutation_class: y\n"
                "input_prompt: x\n"
                "expected_verdict: PASS\n"
            )
            out = run_suite(lambda p: "allowed", cases_dir=Path(d))
        self.assertEqual(out["summary"]["judge_version"], "1.0")


if __name__ == "__main__":
    unittest.main()

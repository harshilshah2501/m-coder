"""Tests for weekly_report — 100% branch coverage and DRIFT detection."""

from __future__ import annotations

import unittest

from observation.judge_drift_suite.coverage_metrics import (
    TOTAL_GUARDS,
    TOTAL_MUTATION_CLASSES,
    TOTAL_PHASES,
    TOTAL_STRESS_SURFACES,
)
from observation.judge_drift_suite.weekly_report import (
    STATUS_DRIFT,
    STATUS_STABLE,
    generate_weekly_report,
)


def _full_coverage_results():
    """Build minimal results list that yields phase/guard/surface/mutation coverage 1.0 and min density >= 1."""
    phases = list(TOTAL_PHASES)
    guards = list(TOTAL_GUARDS)
    surfaces = list(TOTAL_STRESS_SURFACES)
    mutations = list(TOTAL_MUTATION_CLASSES)
    return [
        {"phase": phases[i % len(phases)], "guard": guards[i % len(guards)], "stress_surface": surfaces[i % len(surfaces)], "mutation_class": mutations[i]}
        for i in range(len(mutations))
    ]


class TestWeeklyReport(unittest.TestCase):
    def test_stable_no_failures_no_baseline(self) -> None:
        results = {"results": _full_coverage_results(), "summary": {"total_cases": 20, "failures": 0, "distribution": {"PASS": 0.5, "ESCALATE": 0.3, "REFUSE": 0.2}, "judge_version": "1.0", "refusal_accuracy": 1.0, "collision_accuracy": 1.0, "irreversible_pass_count": 0}}
        report = generate_weekly_report(results, 1.5)
        self.assertEqual(report["status"], STATUS_STABLE)
        self.assertEqual(report["failures"], 0)
        self.assertEqual(report["total_cases"], 20)
        self.assertEqual(report["entropy"], 1.5)
        self.assertEqual(report["judge_version"], "1.0")

    def test_drift_detected_when_failures_gt_zero(self) -> None:
        results = {"summary": {"total_cases": 20, "failures": 1, "distribution": {"PASS": 0.5, "ESCALATE": 0.3, "REFUSE": 0.2}, "judge_version": "1.0"}}
        report = generate_weekly_report(results, 1.5)
        self.assertEqual(report["status"], STATUS_DRIFT)
        self.assertEqual(report["failures"], 1)

    def test_drift_detected_when_entropy_shift_exceeds_threshold(self) -> None:
        results = {"summary": {"total_cases": 20, "failures": 0, "distribution": {"PASS": 0.5, "ESCALATE": 0.3, "REFUSE": 0.2}, "judge_version": "1.0"}}
        baseline = 1.0
        current_entropy = 1.2
        report = generate_weekly_report(results, current_entropy, baseline_entropy=baseline)
        self.assertEqual(report["status"], STATUS_DRIFT)

    def test_stable_when_entropy_shift_within_threshold(self) -> None:
        results = {"results": _full_coverage_results(), "summary": {"total_cases": 20, "failures": 0, "distribution": {"PASS": 0.5, "ESCALATE": 0.3, "REFUSE": 0.2}, "judge_version": "1.0", "refusal_accuracy": 1.0, "collision_accuracy": 1.0, "irreversible_pass_count": 0}}
        baseline = 1.0
        current_entropy = 1.05
        report = generate_weekly_report(results, current_entropy, baseline_entropy=baseline)
        self.assertEqual(report["status"], STATUS_STABLE)

    def test_distribution_passthrough(self) -> None:
        dist = {"PASS": 0.6, "ESCALATE": 0.2, "REFUSE": 0.2}
        results = {"summary": {"total_cases": 10, "failures": 0, "distribution": dist, "judge_version": "1.0"}}
        report = generate_weekly_report(results, 0.5)
        self.assertEqual(report["distribution"], dist)

    def test_week_present(self) -> None:
        results = {"summary": {"total_cases": 0, "failures": 0, "distribution": {}, "judge_version": ""}}
        report = generate_weekly_report(results, 0.0)
        self.assertIn("week", report)
        self.assertIsInstance(report["week"], str)

    def test_empty_summary_handled(self) -> None:
        results = {}
        report = generate_weekly_report(results, 0.0)
        self.assertEqual(report["total_cases"], 0)
        self.assertEqual(report["failures"], 0)
        self.assertEqual(report.get("irreversible_pass_count", 0), 0)
        self.assertEqual(report["status"], STATUS_DRIFT)

    def test_baseline_zero_no_division(self) -> None:
        results = {"results": _full_coverage_results(), "summary": {"total_cases": 18, "failures": 0, "distribution": {}, "judge_version": "", "refusal_accuracy": 1.0, "collision_accuracy": 1.0, "irreversible_pass_count": 0}}
        report = generate_weekly_report(results, 0.5, baseline_entropy=0.0)
        self.assertEqual(report["status"], STATUS_STABLE)

    def test_drift_when_refusal_accuracy_below_threshold(self) -> None:
        results = {"summary": {"total_cases": 10, "failures": 0, "distribution": {}, "judge_version": "1.0", "refusal_accuracy": 0.98, "collision_accuracy": 1.0, "irreversible_pass_count": 0}}
        report = generate_weekly_report(results, 1.0)
        self.assertEqual(report["status"], STATUS_DRIFT)
        self.assertEqual(report["refusal_accuracy"], 0.98)

    def test_drift_when_collision_accuracy_below_threshold(self) -> None:
        results = {"summary": {"total_cases": 10, "failures": 0, "distribution": {}, "judge_version": "1.0", "refusal_accuracy": 1.0, "collision_accuracy": 0.98, "irreversible_pass_count": 0}}
        report = generate_weekly_report(results, 1.0)
        self.assertEqual(report["status"], STATUS_DRIFT)
        self.assertEqual(report["collision_accuracy"], 0.98)

    def test_drift_when_irreversible_pass_count_gt_zero(self) -> None:
        results = {"summary": {"total_cases": 10, "failures": 0, "distribution": {}, "judge_version": "1.0", "refusal_accuracy": 1.0, "collision_accuracy": 1.0, "irreversible_pass_count": 1}}
        report = generate_weekly_report(results, 1.0)
        self.assertEqual(report["status"], STATUS_DRIFT)
        self.assertEqual(report["irreversible_pass_count"], 1)

    def test_stable_when_all_rigor_thresholds_met(self) -> None:
        results = {"results": _full_coverage_results(), "summary": {"total_cases": 20, "failures": 0, "distribution": {"PASS": 0.5, "REFUSE": 0.5}, "judge_version": "1.0", "refusal_accuracy": 0.99, "collision_accuracy": 0.99, "irreversible_pass_count": 0}}
        report = generate_weekly_report(results, 1.0)
        self.assertEqual(report["status"], STATUS_STABLE)


if __name__ == "__main__":
    unittest.main()

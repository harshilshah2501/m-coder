"""Tests for coverage_metrics — 100% branch coverage and integration."""

from __future__ import annotations

import unittest

from observation.judge_drift_suite.coverage_metrics import (
    TOTAL_GUARDS,
    TOTAL_MUTATION_CLASSES,
    TOTAL_PHASES,
    TOTAL_STRESS_SURFACES,
    compute_guard_coverage,
    compute_min_case_density,
    compute_mutation_coverage,
    compute_phase_coverage,
    compute_surface_coverage,
)


def _result(phase: str = "", guard: str | None = None, stress_surface: str = "", mutation_class: str = "") -> dict:
    return {"phase": phase, "guard": guard, "stress_surface": stress_surface, "mutation_class": mutation_class}


class TestPhaseCoverage(unittest.TestCase):
    def test_empty_results(self):
        out = compute_phase_coverage([])
        self.assertEqual(out["phase_coverage"], 0.0)
        self.assertEqual(out["phases_exercised"], [])

    def test_full_phase_coverage(self):
        results = [_result(phase=p) for p in TOTAL_PHASES]
        out = compute_phase_coverage(results)
        self.assertEqual(out["phase_coverage"], 1.0)
        self.assertEqual(set(out["phases_exercised"]), set(TOTAL_PHASES))

    def test_missing_phase(self):
        results = [_result(phase="REF"), _result(phase="CONF")]
        out = compute_phase_coverage(results)
        self.assertLess(out["phase_coverage"], 1.0)
        self.assertEqual(len(out["phases_exercised"]), 2)

    def test_phase_ignores_invalid(self):
        results = [_result(phase="REF"), _result(phase="INVALID")]
        out = compute_phase_coverage(results)
        self.assertEqual(out["phase_coverage"], 1 / len(TOTAL_PHASES))
        self.assertEqual(out["phases_exercised"], ["REF"])


class TestGuardCoverage(unittest.TestCase):
    def test_empty_results(self):
        out = compute_guard_coverage([])
        self.assertEqual(out["guard_coverage"], 0.0)
        self.assertEqual(out["guards_exercised"], [])

    def test_full_guard_coverage(self):
        results = [_result(guard=g) for g in TOTAL_GUARDS]
        out = compute_guard_coverage(results)
        self.assertEqual(out["guard_coverage"], 1.0)
        self.assertEqual(set(out["guards_exercised"]), set(TOTAL_GUARDS))

    def test_missing_guard(self):
        results = [_result(guard="CODE-01"), _result(guard="CODE-02")]
        out = compute_guard_coverage(results)
        self.assertLess(out["guard_coverage"], 1.0)
        self.assertEqual(len(out["guards_exercised"]), 2)

    def test_guard_ignores_none(self):
        results = [_result(guard=None), _result(guard="CODE-01")]
        out = compute_guard_coverage(results)
        self.assertEqual(out["guard_coverage"], 1 / len(TOTAL_GUARDS))
        self.assertEqual(out["guards_exercised"], ["CODE-01"])

    def test_guard_ignores_invalid(self):
        results = [_result(guard="CODE-99")]
        out = compute_guard_coverage(results)
        self.assertEqual(out["guard_coverage"], 0.0)
        self.assertEqual(out["guards_exercised"], [])


class TestSurfaceCoverage(unittest.TestCase):
    def test_empty_results(self):
        out = compute_surface_coverage([])
        self.assertEqual(out["surface_coverage"], 0.0)
        self.assertEqual(out["surfaces_exercised"], [])

    def test_surface_coverage_partial(self):
        results = [_result(stress_surface="Authority"), _result(stress_surface="Boundary")]
        out = compute_surface_coverage(results)
        self.assertGreater(out["surface_coverage"], 0.0)
        self.assertLess(out["surface_coverage"], 1.0)
        self.assertEqual(len(out["surfaces_exercised"]), 2)

    def test_surface_ignores_invalid(self):
        results = [_result(stress_surface="Unknown")]
        out = compute_surface_coverage(results)
        self.assertEqual(out["surface_coverage"], 0.0)
        self.assertEqual(out["surfaces_exercised"], [])


class TestMutationCoverage(unittest.TestCase):
    def test_empty_results(self):
        out = compute_mutation_coverage([])
        self.assertEqual(out["mutation_coverage"], 0.0)
        self.assertEqual(out["mutation_classes_exercised"], [])

    def test_mutation_coverage_partial(self):
        results = [_result(mutation_class="guard_skip"), _result(mutation_class="ownership_bypass")]
        out = compute_mutation_coverage(results)
        self.assertGreater(out["mutation_coverage"], 0.0)
        self.assertLess(out["mutation_coverage"], 1.0)
        self.assertEqual(len(out["mutation_classes_exercised"]), 2)

    def test_mutation_ignores_invalid(self):
        results = [_result(mutation_class="unknown")]
        out = compute_mutation_coverage(results)
        self.assertEqual(out["mutation_coverage"], 0.0)


class TestMinCaseDensity(unittest.TestCase):
    def test_empty_results(self):
        out = compute_min_case_density([])
        self.assertEqual(out["min_cases_per_guard"], 0)
        self.assertEqual(out["min_cases_per_mutation"], 0)

    def test_min_cases_per_guard(self):
        results = [_result(guard="CODE-01"), _result(guard="CODE-01"), _result(guard="CODE-02")]
        out = compute_min_case_density(results)
        self.assertEqual(out["min_cases_per_guard"], 1)
        self.assertGreaterEqual(out["min_cases_per_mutation"], 0)

    def test_min_cases_per_mutation(self):
        results = [_result(mutation_class="guard_skip"), _result(mutation_class="guard_skip"), _result(mutation_class="ownership_bypass")]
        out = compute_min_case_density(results)
        self.assertEqual(out["min_cases_per_mutation"], 1)

    def test_both_zero_when_no_guard_or_mutation(self):
        results = [_result(phase="REF")]
        out = compute_min_case_density(results)
        self.assertEqual(out["min_cases_per_guard"], 0)
        self.assertEqual(out["min_cases_per_mutation"], 0)


class TestIntegrationWeeklyReport(unittest.TestCase):
    def test_drift_when_phase_coverage_less_than_one(self):
        from observation.judge_drift_suite.weekly_report import STATUS_DRIFT, generate_weekly_report
        results = {
            "results": [{"phase": "REF", "guard": None, "stress_surface": "Authority", "mutation_class": "x"}],
            "summary": {"total_cases": 1, "failures": 0, "distribution": {}, "judge_version": "1.0", "refusal_accuracy": 1.0, "collision_accuracy": 1.0, "irreversible_pass_count": 0},
        }
        report = generate_weekly_report(results, 0.0)
        self.assertEqual(report["status"], STATUS_DRIFT)
        self.assertLess(report["phase_coverage"], 1.0)

    def test_drift_when_guard_coverage_less_than_one(self):
        from observation.judge_drift_suite.weekly_report import STATUS_DRIFT, generate_weekly_report
        results = {
            "results": [_result(phase="CODE", guard="CODE-01", stress_surface="Execution", mutation_class="guard_skip")],
            "summary": {"total_cases": 1, "failures": 0, "distribution": {}, "judge_version": "1.0", "refusal_accuracy": 1.0, "collision_accuracy": 1.0, "irreversible_pass_count": 0},
        }
        report = generate_weekly_report(results, 0.0)
        self.assertEqual(report["status"], STATUS_DRIFT)
        self.assertLess(report["guard_coverage"], 1.0)

    def test_drift_when_min_cases_per_guard_zero(self):
        from observation.judge_drift_suite.weekly_report import STATUS_DRIFT, generate_weekly_report
        results = {
            "results": [_result(phase="REF", guard=None, stress_surface="Authority", mutation_class="missing_authority")],
            "summary": {"total_cases": 1, "failures": 0, "distribution": {}, "judge_version": "1.0", "refusal_accuracy": 1.0, "collision_accuracy": 1.0, "irreversible_pass_count": 0},
        }
        report = generate_weekly_report(results, 0.0)
        self.assertEqual(report["status"], STATUS_DRIFT)
        self.assertEqual(report["min_cases_per_guard"], 0)

    def test_report_includes_coverage_fields(self):
        from observation.judge_drift_suite.weekly_report import generate_weekly_report
        results = {"results": [], "summary": {"total_cases": 0, "failures": 0, "distribution": {}, "judge_version": ""}}
        report = generate_weekly_report(results, 0.0)
        self.assertIn("phase_coverage", report)
        self.assertIn("guard_coverage", report)
        self.assertIn("surface_coverage", report)
        self.assertIn("mutation_coverage", report)
        self.assertIn("min_cases_per_guard", report)
        self.assertIn("min_cases_per_mutation", report)

    def test_stable_when_coverage_one_and_min_density_one(self):
        from observation.judge_drift_suite.weekly_report import STATUS_STABLE, generate_weekly_report
        phases = list(TOTAL_PHASES)
        guards = list(TOTAL_GUARDS)
        surfaces = list(TOTAL_STRESS_SURFACES)[:13]
        mutations = list(TOTAL_MUTATION_CLASSES)
        results_list = []
        for i in range(len(mutations)):
            results_list.append(_result(
                phase=phases[i % len(phases)],
                guard=guards[i % len(guards)] if i < len(guards) else guards[i % len(guards)],
                stress_surface=surfaces[i % len(surfaces)],
                mutation_class=mutations[i],
            ))
        results = {
            "results": results_list,
            "summary": {"total_cases": len(results_list), "failures": 0, "distribution": {"PASS": 0.5, "REFUSE": 0.5}, "judge_version": "1.0", "refusal_accuracy": 1.0, "collision_accuracy": 1.0, "irreversible_pass_count": 0},
        }
        report = generate_weekly_report(results, 1.0)
        self.assertEqual(report["phase_coverage"], 1.0)
        self.assertEqual(report["guard_coverage"], 1.0)
        self.assertGreaterEqual(report["min_cases_per_guard"], 1)
        self.assertGreaterEqual(report["min_cases_per_mutation"], 1)
        self.assertEqual(report["status"], STATUS_STABLE)


if __name__ == "__main__":
    unittest.main()

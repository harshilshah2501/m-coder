"""
M3.6 Shadow mode: runner and baseline scenario tests.

- Shadow plan emission
- Shadow ledger emission
- No boundary crossed in shadow
- REF / CONF / DES representative cases
"""

from __future__ import annotations

import unittest

from runtime.shadow.baseline_scenarios import BASELINE_SCENARIOS, ScenarioDef, scenario_to_event
from runtime.shadow.runner import ShadowRunner, ShadowRunResult
from runtime.plan_gate_stub.plan_gate import PlanGate


class TestShadowPlanEmission(unittest.TestCase):
    """Every shadow run must emit a plan."""

    def test_each_scenario_emits_plan(self) -> None:
        runner = ShadowRunner()
        for scenario in BASELINE_SCENARIOS:
            with self.subTest(scenario=scenario.id):
                result = runner.run_scenario(scenario)
                self.assertTrue(result.plan, f"{scenario.id}: plan must be emitted")
                self.assertIn("schema_version", result.plan)
                self.assertIn("boundary", result.plan)
                self.assertIn("constitutional_phase_expected", result.plan)

    def test_plan_has_request_id(self) -> None:
        runner = ShadowRunner()
        result = runner.run_scenario(BASELINE_SCENARIOS[0])
        self.assertIn("request", result.plan)
        self.assertEqual(result.plan["request"]["request_id"], result.request_id)


class TestShadowLedgerEmission(unittest.TestCase):
    """Every shadow run must emit a ledger row."""

    def test_each_scenario_emits_ledger(self) -> None:
        runner = ShadowRunner()
        for scenario in BASELINE_SCENARIOS:
            with self.subTest(scenario=scenario.id):
                result = runner.run_scenario(scenario)
                self.assertTrue(result.ledger_row, f"{scenario.id}: ledger must be emitted")
                self.assertEqual(result.ledger_row.get("schema_version"), "ledger_row.v0.1")
                self.assertIn("plan_link", result.ledger_row)
                self.assertIn("verdicts", result.ledger_row)

    def test_ledger_plan_hash_matches_decision(self) -> None:
        runner = ShadowRunner()
        result = runner.run_scenario(BASELINE_SCENARIOS[0])
        self.assertEqual(
            result.ledger_row["plan_link"]["plan_hash"],
            result.plan_hash,
            "ledger plan_hash must match run plan_hash",
        )


class TestShadowNoBoundaryCrossed(unittest.TestCase):
    """S-1: In shadow, boundary_verdict must never be 'crossed'; boundary_crossed must be false."""

    def test_no_scenario_emits_crossed(self) -> None:
        runner = ShadowRunner()
        for scenario in BASELINE_SCENARIOS:
            with self.subTest(scenario=scenario.id):
                result = runner.run_scenario(scenario)
                self.assertNotEqual(
                    result.boundary_verdict,
                    "crossed",
                    f"{scenario.id}: shadow must never emit boundary_verdict=crossed",
                )
                self.assertFalse(
                    result.boundary_crossed,
                    f"{scenario.id}: shadow must never have boundary_crossed=true",
                )

    def test_plan_gate_shadow_mode_never_returns_crossed(self) -> None:
        gate = PlanGate(mode="shadow")
        event = scenario_to_event(BASELINE_SCENARIOS[0])
        _, ledger_row, _ = gate.evaluate_plan(event)
        d = ledger_row.to_dict()
        self.assertNotEqual(d.get("verdicts", {}).get("boundary_verdict"), "crossed")
        self.assertFalse(d.get("boundary", {}).get("boundary_crossed", True))


class TestRefConfDesScenarios(unittest.TestCase):
    """Representative REF, CONF, DES scenarios produce expected phase and posture."""

    def test_ref_refuse(self) -> None:
        runner = ShadowRunner()
        ref_scenarios = [s for s in BASELINE_SCENARIOS if s.expected_phase == "REF"]
        self.assertGreater(len(ref_scenarios), 0, "at least one REF scenario")
        for s in ref_scenarios:
            result = runner.run_scenario(s)
            self.assertEqual(result.decision_phase, "REF", f"{s.id}: expected REF")
            self.assertEqual(result.decision_posture, "refuse", f"{s.id}: expected refuse")

    def test_conf_bounded_allow(self) -> None:
        runner = ShadowRunner()
        conf_scenarios = [s for s in BASELINE_SCENARIOS if s.expected_phase == "CONF"]
        self.assertGreater(len(conf_scenarios), 0, "at least one CONF scenario")
        for s in conf_scenarios:
            result = runner.run_scenario(s)
            self.assertEqual(result.decision_phase, "CONF", f"{s.id}: expected CONF")
            self.assertEqual(result.decision_posture, "bounded_allow", f"{s.id}: expected bounded_allow")

    def test_des_safe_execute(self) -> None:
        runner = ShadowRunner()
        des_scenarios = [s for s in BASELINE_SCENARIOS if s.expected_phase == "DES"]
        self.assertGreater(len(des_scenarios), 0, "at least one DES scenario")
        for s in des_scenarios:
            result = runner.run_scenario(s)
            self.assertEqual(result.decision_phase, "DES", f"{s.id}: expected DES")
            self.assertEqual(result.decision_posture, "safe_execute", f"{s.id}: expected safe_execute")


class TestShadowRunAll(unittest.TestCase):
    """run_all returns one result per scenario."""

    def test_run_all_length(self) -> None:
        runner = ShadowRunner()
        results = runner.run_all(BASELINE_SCENARIOS)
        self.assertEqual(len(results), len(BASELINE_SCENARIOS))

    def test_run_all_order(self) -> None:
        runner = ShadowRunner()
        results = runner.run_all(BASELINE_SCENARIOS)
        for r, s in zip(results, BASELINE_SCENARIOS):
            self.assertEqual(r.scenario_id, s.id)
            self.assertEqual(r.request_id, s.request_id)


if __name__ == "__main__":
    unittest.main()

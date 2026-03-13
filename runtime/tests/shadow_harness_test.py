"""
M3.6 Shadow mode: validation harness and ingestion batch tests.

- Harness passes (S-1, S-2, S-3, S-6)
- Ingestion batch structure
- Deterministic shadow validation report
"""

from __future__ import annotations

import unittest

from runtime.shadow.baseline_scenarios import BASELINE_SCENARIOS
from runtime.shadow.harness import ShadowValidationHarness, HarnessResult
from runtime.shadow.ingestion_batch import build_ingestion_batch, normalize_ledger_row


class TestShadowHarnessPasses(unittest.TestCase):
    """Shadow validation harness must pass for baseline scenarios."""

    def test_harness_passes(self) -> None:
        harness = ShadowValidationHarness(scenarios=BASELINE_SCENARIOS)
        result = harness.run()
        self.assertTrue(result.passed, f"Harness must pass; violations: {result.violations}")
        self.assertEqual(len(result.violations), 0, result.violations)

    def test_s1_no_crossed(self) -> None:
        harness = ShadowValidationHarness(scenarios=BASELINE_SCENARIOS)
        result = harness.run()
        s1 = [v for v in result.violations if v.startswith("S-1")]
        self.assertEqual(s1, [], "S-1: no boundary_verdict=crossed or boundary_crossed=true")

    def test_s2_plan_and_ledger_emitted(self) -> None:
        harness = ShadowValidationHarness(scenarios=BASELINE_SCENARIOS)
        result = harness.run()
        s2 = [v for v in result.violations if v.startswith("S-2")]
        self.assertEqual(s2, [], "S-2: plan and ledger must be emitted for every run")

    def test_s3_plan_hash_linkage(self) -> None:
        harness = ShadowValidationHarness(scenarios=BASELINE_SCENARIOS)
        result = harness.run()
        s3 = [v for v in result.violations if v.startswith("S-3")]
        self.assertEqual(s3, [], "S-3: decision plan_hash must match ledger plan_link")


class TestIngestionBatchStructure(unittest.TestCase):
    """Ingestion batch must have required structure (S-6)."""

    def test_harness_produces_ingestion_batch(self) -> None:
        harness = ShadowValidationHarness(scenarios=BASELINE_SCENARIOS)
        result = harness.run()
        self.assertIsNotNone(result.ingestion_batch)
        batch = result.ingestion_batch
        self.assertEqual(batch.get("schema_version"), "ingestion_batch.v0.1")
        self.assertIn("batch_id", batch)
        self.assertIn("created_utc", batch)
        self.assertIn("source", batch)
        self.assertIn("items", batch)

    def test_each_item_has_request_id_plan_ledger_row(self) -> None:
        harness = ShadowValidationHarness(scenarios=BASELINE_SCENARIOS)
        result = harness.run()
        self.assertIsNotNone(result.ingestion_batch)
        for i, item in enumerate(result.ingestion_batch["items"]):
            self.assertIn("request_id", item, f"item[{i}]")
            self.assertIn("plan", item, f"item[{i}]")
            self.assertIn("ledger_row", item, f"item[{i}]")

    def test_ingestion_batch_builder_direct(self) -> None:
        items = [
            {
                "request_id": "req-1",
                "plan": {"schema_version": "plan.v0.1", "boundary": {"irreversible_boundary_phrase": "merge to main"}},
                "ledger_row": {
                    "schema_version": "ledger_row.v0.1",
                    "event": {"event_id": "e1", "timestamp_utc": "2026-03-01T00:00:00Z", "request_id": "req-1", "session_id": "s1", "mode": "shadow"},
                    "plan_link": {"plan_hash": "a" * 64},
                    "verdicts": {"phase_emitted": "REF", "terminal_posture": "refuse", "authority_verdict": "fail", "boundary_verdict": "blocked"},
                    "boundary": {"irreversible_boundary_phrase": "merge to main", "boundary_crossed": False},
                    "reason_codes": [],
                },
            },
        ]
        batch = build_ingestion_batch(items)
        self.assertEqual(batch["schema_version"], "ingestion_batch.v0.1")
        self.assertEqual(len(batch["items"]), 1)
        self.assertEqual(batch["items"][0]["request_id"], "req-1")
        self.assertIn("ledger_row", batch["items"][0])
        # Normalizer should have added event.runtime_version, plan_link.plan_schema_version, verdicts.ref_enforced, boundary.boundary_cross_attempted, actions
        lr = batch["items"][0]["ledger_row"]
        self.assertIn("runtime_version", lr.get("event", {}))
        self.assertIn("plan_schema_version", lr.get("plan_link", {}))
        self.assertIn("ref_enforced", lr.get("verdicts", {}))
        self.assertIn("boundary_cross_attempted", lr.get("boundary", {}))
        self.assertIn("actions", lr)


class TestNormalizeLedgerRow(unittest.TestCase):
    """normalize_ledger_row adds required fields for schema compliance."""

    def test_adds_runtime_version(self) -> None:
        lr = {"event": {"event_id": "e", "timestamp_utc": "2026-03-01T00:00:00Z", "request_id": "r", "session_id": "s", "mode": "shadow"}}
        out = normalize_ledger_row(lr)
        self.assertEqual(out["event"].get("runtime_version"), "0.1")

    def test_adds_plan_schema_version(self) -> None:
        lr = {"plan_link": {"plan_hash": "abc"}}
        out = normalize_ledger_row(lr)
        self.assertEqual(out["plan_link"].get("plan_schema_version"), "plan.v0.1")

    def test_adds_ref_enforced(self) -> None:
        lr = {"verdicts": {"phase_emitted": "REF"}}
        out = normalize_ledger_row(lr)
        self.assertTrue(out["verdicts"].get("ref_enforced"))

    def test_adds_actions(self) -> None:
        lr = {}
        out = normalize_ledger_row(lr)
        self.assertIn("actions", out)
        self.assertIn("tool_calls_attempted", out["actions"])
        self.assertIn("execution_intents", out["actions"])


if __name__ == "__main__":
    unittest.main()

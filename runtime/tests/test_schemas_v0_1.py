"""
Schema validation for Plan v0.1 and Ledger Row v0.1.

Validates that example JSON files pass schema.
Validates that invalid example fails (REF + safe_execute).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = REPO_ROOT / "runtime" / "schemas"
EXAMPLES = SCHEMAS / "examples"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@unittest.skipIf(not HAS_JSONSCHEMA, "jsonschema not installed")
class TestPlanSchema(unittest.TestCase):
    """Validate plan examples against plan.v0.1.schema.json."""

    def setUp(self) -> None:
        schema_path = SCHEMAS / "plan.v0.1.schema.json"
        schema = load_json(schema_path)
        self.plan_validator = jsonschema.Draft7Validator(schema)

    def test_plan_ref_missing_authority_valid(self) -> None:
        data = load_json(EXAMPLES / "plan_ref_missing_authority.json")
        self.plan_validator.validate(data)

    def test_plan_conf_preboundary_valid(self) -> None:
        data = load_json(EXAMPLES / "plan_conf_preboundary.json")
        self.plan_validator.validate(data)

    def test_plan_invalid_structurally_valid_but_violates_r2(self) -> None:
        data = load_json(EXAMPLES / "plan_invalid_approval_missing_safe_execute.json")
        self.plan_validator.validate(data)

    def test_plan_invalid_fails_runtime_rule_r2(self) -> None:
        data = load_json(EXAMPLES / "plan_invalid_approval_missing_safe_execute.json")
        self.assertEqual(data["constitutional_phase_expected"], "REF")
        self.assertEqual(data["policy_posture"]["terminal_posture"], "safe_execute")
        self.assertNotEqual(
            data["policy_posture"]["terminal_posture"],
            "refuse",
            "R2: REF must have terminal_posture=refuse; this example violates R2",
        )


@unittest.skipIf(not HAS_JSONSCHEMA, "jsonschema not installed")
class TestLedgerSchema(unittest.TestCase):
    """Validate ledger examples against ledger_row.v0.1.schema.json."""

    def setUp(self) -> None:
        schema_path = SCHEMAS / "ledger_row.v0.1.schema.json"
        schema = load_json(schema_path)
        self.ledger_validator = jsonschema.Draft7Validator(schema)

    def test_ledger_ref_blocked_valid(self) -> None:
        data = load_json(EXAMPLES / "ledger_ref_blocked.json")
        self.ledger_validator.validate(data)

    def test_ledger_conf_preboundary_valid(self) -> None:
        data = load_json(EXAMPLES / "ledger_conf_preboundary.json")
        self.ledger_validator.validate(data)


class TestInvalidExample(unittest.TestCase):
    """Invalid example: REF + safe_execute violates R2."""

    def test_invalid_plan_has_ref_and_safe_execute(self) -> None:
        data = load_json(EXAMPLES / "plan_invalid_approval_missing_safe_execute.json")
        self.assertEqual(data["constitutional_phase_expected"], "REF")
        self.assertEqual(data["policy_posture"]["terminal_posture"], "safe_execute")
        self.assertTrue(
            data["constitutional_phase_expected"] == "REF"
            and data["policy_posture"]["terminal_posture"] != "refuse",
            "This example is intentionally invalid (R2 violation)",
        )

"""
Schema validation for Plan v0.1 and Ledger Row v0.1.

Validates that example JSON files pass schema.
Validates that invalid examples fail runtime rules R1 and R2.
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

RISKY_BOUNDARY_TYPES = {"merge", "deploy", "prod_write", "security_change", "data_delete", "config_rollout"}
REFUSE_OR_DEFER = {"refuse", "defer"}


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_runtime_rules_plan(plan: dict) -> list[str]:
    """Validate plan against runtime rules R1–R5. Returns list of violated rule codes."""
    violations: list[str] = []
    phase = plan.get("constitutional_phase_expected")
    posture = plan.get("policy_posture", {}).get("terminal_posture")
    authority = plan.get("authority", {}).get("validated", {})
    auth_verdict = authority.get("verdict")
    boundary = plan.get("boundary", {})
    boundary_type = boundary.get("boundary_type")
    exec_mode = plan.get("tooling_intent", {}).get("execution_mode")

    if phase == "REF" and posture != "refuse":
        violations.append("R2")
    if auth_verdict != "pass" and boundary_type in RISKY_BOUNDARY_TYPES and posture not in REFUSE_OR_DEFER:
        violations.append("R1")
    if phase == "DES" and posture == "safe_execute":
        violations.append("R3")
    if phase == "CODE" and exec_mode == "no_exec":
        violations.append("R4")
    if not (boundary.get("irreversible_boundary_phrase") or "").strip():
        violations.append("R5")
    return violations


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

    def test_plan_invalid_r2_structurally_valid(self) -> None:
        data = load_json(EXAMPLES / "plan_invalid_r2_ref_phase_not_refuse.json")
        self.plan_validator.validate(data)

    def test_plan_invalid_r1_structurally_valid(self) -> None:
        data = load_json(EXAMPLES / "plan_invalid_r1_authority_fail_risky_boundary_safe_execute.json")
        self.plan_validator.validate(data)

    def test_plan_invalid_r1_fails_runtime_rule_r1(self) -> None:
        data = load_json(EXAMPLES / "plan_invalid_r1_authority_fail_risky_boundary_safe_execute.json")
        violations = validate_runtime_rules_plan(data)
        self.assertIn("R1", violations, "R1: authority fail + risky boundary + safe_execute must fail")
        self.assertNotIn("R2", violations, "R1 sample should not violate R2")

    def test_plan_invalid_r2_fails_runtime_rule_r2(self) -> None:
        data = load_json(EXAMPLES / "plan_invalid_r2_ref_phase_not_refuse.json")
        violations = validate_runtime_rules_plan(data)
        self.assertIn("R2", violations, "R2: REF must have terminal_posture=refuse")
        self.assertNotIn("R1", violations, "R2 sample should not violate R1")


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


class TestInvalidExamplesTargetRules(unittest.TestCase):
    """Invalid examples target R1 and R2 respectively."""

    def test_r2_invalid_has_ref_and_safe_execute(self) -> None:
        data = load_json(EXAMPLES / "plan_invalid_r2_ref_phase_not_refuse.json")
        self.assertEqual(data["constitutional_phase_expected"], "REF")
        self.assertEqual(data["policy_posture"]["terminal_posture"], "safe_execute")

    def test_r1_invalid_has_authority_fail_risky_boundary_safe_execute(self) -> None:
        data = load_json(EXAMPLES / "plan_invalid_r1_authority_fail_risky_boundary_safe_execute.json")
        self.assertEqual(data["authority"]["validated"]["verdict"], "fail")
        self.assertEqual(data["boundary"]["boundary_type"], "prod_write")
        self.assertEqual(data["policy_posture"]["terminal_posture"], "safe_execute")

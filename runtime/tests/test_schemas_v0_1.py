"""
Schema validation for Plan v0.1, Ledger Row v0.1, and Task v0.1.

Validates that example JSON files pass schema.
Validates that invalid examples fail runtime rules R1 and R2.
Validates Task v0.1 schema validation including required fields,
optional governance_ref, acceptance_criteria, and constrained metadata.
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


def validate_runtime_rules_ledger(ledger: dict) -> list[str]:
    """Validate ledger against runtime rules L1–L5. Returns list of violated rule codes."""
    violations: list[str] = []
    v = ledger.get("verdicts", {})
    b = ledger.get("boundary", {})
    auth = v.get("authority_verdict")
    boundary_verdict = v.get("boundary_verdict")
    ref_enforced = v.get("ref_enforced")
    phase = v.get("phase_emitted")
    crossed = b.get("boundary_crossed")
    attempted = b.get("boundary_cross_attempted")
    phrase = (b.get("irreversible_boundary_phrase") or "").strip()

    if auth != "pass" and boundary_verdict == "crossed":
        violations.append("L4")
    if ref_enforced and phase not in ("REF", "MIX"):
        violations.append("L1")
    if crossed and boundary_verdict != "crossed":
        violations.append("L2")
    if attempted and not crossed and boundary_verdict != "blocked":
        violations.append("L3")
    if not phrase:
        violations.append("L5")
    return violations


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

    def test_ledger_invalid_l4_structurally_valid(self) -> None:
        data = load_json(EXAMPLES / "ledger_invalid_l4_authority_fail_but_crossed.json")
        self.ledger_validator.validate(data)

    def test_ledger_invalid_l4_fails_runtime_rule_l4(self) -> None:
        data = load_json(EXAMPLES / "ledger_invalid_l4_authority_fail_but_crossed.json")
        violations = validate_runtime_rules_ledger(data)
        self.assertEqual(violations, ["L4"], "L4: authority fail + boundary crossed must be the only violation")


class TestEnumFreeze(unittest.TestCase):
    """Freeze enums to prevent silent drift in reason_codes and surfaces."""

    def test_reason_codes_enum_frozen(self) -> None:
        rc = load_json(SCHEMAS / "reason_codes.v0.1.json")
        actual = set(rc["items"]["enum"])
        expected = {
            "MISSING_AUTHORITY",
            "AUTHORITY_UNKNOWN",
            "BOUNDARY_BLOCKED",
            "BOUNDARY_RELOCATED_DETECTED",
            "PHASE_MISMATCH_PREVENTED",
            "REF_ENFORCED",
            "INSUFFICIENT_EVIDENCE",
            "TOOL_NOT_PERMITTED",
            "SAFE_PREBOUNDARY_ONLY",
        }
        self.assertEqual(actual, expected, "reason_codes enum must not change without explicit version bump")

    def test_surfaces_enum_frozen(self) -> None:
        sf = load_json(SCHEMAS / "surfaces.v0.1.json")
        actual = set(sf["items"]["enum"])
        expected = {
            "SignalIntegrity",
            "BaselinesHistory",
            "ChangeBlastRadius",
            "AuthorityOwnership",
            "TimePressure",
            "Compositional",
            "ImplementationIrreversibility",
            "ContextDrift",
        }
        self.assertEqual(actual, expected, "surfaces enum must not change without explicit version bump")


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


@unittest.skipIf(not HAS_JSONSCHEMA, "jsonschema not installed")
class TestTaskSchema(unittest.TestCase):
    """Validate task examples against task.v0.1.schema.json.
    
    M3.17 Slice 1: Task schema validation coverage.
    Tests cover:
    - Valid minimal task passes
    - Valid task with optional governance_ref passes
    - Valid task with optional acceptance_criteria passes
    - Missing required identity field fails
    - Wrong schema_version fails
    - Invalid task_kind fails
    - Invalid current_state fails
    - Invalid governance_ref shape fails
    - Invalid metadata shape fails
    - expected_phase is optional and non-authoritative
    """

    def setUp(self) -> None:
        schema_path = SCHEMAS / "task.v0.1.schema.json"
        schema = load_json(schema_path)
        self.task_validator = jsonschema.Draft7Validator(schema)

    def test_task_minimal_valid(self) -> None:
        """Valid minimal task with only required fields passes validation."""
        data = load_json(EXAMPLES / "task_minimal_valid.json")
        self.task_validator.validate(data)

    def test_task_with_governance_ref_valid(self) -> None:
        """Valid task with optional governance_ref passes validation."""
        data = load_json(EXAMPLES / "task_with_governance_ref.json")
        self.task_validator.validate(data)
        self.assertIn("governance_ref", data)
        self.assertIn("plan_hash", data["governance_ref"])
        self.assertIn("expected_phase", data["governance_ref"])

    def test_task_with_acceptance_criteria_valid(self) -> None:
        """Valid task with optional acceptance_criteria passes validation."""
        data = load_json(EXAMPLES / "task_with_acceptance_criteria.json")
        self.task_validator.validate(data)
        self.assertIn("acceptance_criteria", data)
        self.assertIn("description", data["acceptance_criteria"])
        self.assertIn("test_refs", data["acceptance_criteria"])
        self.assertIn("success_signals", data["acceptance_criteria"])

    def test_task_full_valid(self) -> None:
        """Valid task with all optional fields passes validation."""
        data = load_json(EXAMPLES / "task_full_valid.json")
        self.task_validator.validate(data)

    def test_task_missing_task_id_fails(self) -> None:
        """Missing required task_id field fails validation."""
        data = load_json(EXAMPLES / "task_invalid_missing_task_id.json")
        with self.assertRaises(jsonschema.ValidationError) as ctx:
            self.task_validator.validate(data)
        self.assertIn("task_id", str(ctx.exception))

    def test_task_wrong_schema_version_fails(self) -> None:
        """Wrong schema_version fails validation."""
        data = load_json(EXAMPLES / "task_invalid_wrong_schema_version.json")
        with self.assertRaises(jsonschema.ValidationError) as ctx:
            self.task_validator.validate(data)
        self.assertIn("schema_version", str(ctx.exception))

    def test_task_invalid_task_kind_fails(self) -> None:
        """Invalid task_kind enum value fails validation."""
        data = load_json(EXAMPLES / "task_invalid_task_kind.json")
        with self.assertRaises(jsonschema.ValidationError) as ctx:
            self.task_validator.validate(data)
        self.assertIn("task_kind", str(ctx.exception))

    def test_task_invalid_current_state_fails(self) -> None:
        """Invalid current_state enum value fails validation."""
        data = load_json(EXAMPLES / "task_invalid_current_state.json")
        with self.assertRaises(jsonschema.ValidationError) as ctx:
            self.task_validator.validate(data)
        self.assertIn("current_state", str(ctx.exception))

    def test_task_invalid_governance_ref_shape_fails(self) -> None:
        """Invalid governance_ref shape (bad phase, extra field) fails validation."""
        data = load_json(EXAMPLES / "task_invalid_governance_ref_shape.json")
        with self.assertRaises(jsonschema.ValidationError):
            self.task_validator.validate(data)

    def test_task_invalid_metadata_not_namespaced_fails(self) -> None:
        """Metadata with non-lowercase namespace key fails validation."""
        data = load_json(EXAMPLES / "task_invalid_metadata_not_namespaced.json")
        with self.assertRaises(jsonschema.ValidationError):
            self.task_validator.validate(data)

    def test_task_invalid_metadata_string_fails(self) -> None:
        """Metadata as string (not object) fails validation."""
        data = load_json(EXAMPLES / "task_invalid_metadata_string.json")
        with self.assertRaises(jsonschema.ValidationError) as ctx:
            self.task_validator.validate(data)
        self.assertIn("metadata", str(ctx.exception))

    def test_task_expected_phase_is_optional(self) -> None:
        """governance_ref without expected_phase is valid (expected_phase is optional hint)."""
        data = load_json(EXAMPLES / "task_valid_no_expected_phase.json")
        self.task_validator.validate(data)
        self.assertIn("governance_ref", data)
        self.assertIn("plan_hash", data["governance_ref"])
        self.assertNotIn("expected_phase", data["governance_ref"])

    def test_task_governance_ref_is_optional(self) -> None:
        """Task without governance_ref is valid (governance_ref is optional)."""
        data = load_json(EXAMPLES / "task_minimal_valid.json")
        self.task_validator.validate(data)
        self.assertNotIn("governance_ref", data)

    def test_task_constraints_is_optional(self) -> None:
        """Task without constraints is valid (constraints is optional)."""
        data = load_json(EXAMPLES / "task_minimal_valid.json")
        self.task_validator.validate(data)
        self.assertNotIn("constraints", data)

    def test_task_acceptance_criteria_is_optional(self) -> None:
        """Task without acceptance_criteria is valid."""
        data = load_json(EXAMPLES / "task_minimal_valid.json")
        self.task_validator.validate(data)
        self.assertNotIn("acceptance_criteria", data)

    def test_task_terminal_state_requires_stop_reason(self) -> None:
        """Terminal state without stop_reason fails validation."""
        data = load_json(EXAMPLES / "task_invalid_terminal_no_stop_reason.json")
        with self.assertRaises(jsonschema.ValidationError) as ctx:
            self.task_validator.validate(data)
        self.assertIn("stop_reason", str(ctx.exception))

    def test_task_terminal_state_requires_terminal_at_utc(self) -> None:
        """Terminal state without terminal_at_utc fails validation."""
        data = load_json(EXAMPLES / "task_invalid_terminal_no_timestamp.json")
        with self.assertRaises(jsonschema.ValidationError) as ctx:
            self.task_validator.validate(data)
        self.assertIn("terminal_at_utc", str(ctx.exception))

    def test_task_terminal_state_with_required_fields_passes(self) -> None:
        """Terminal state with both stop_reason and terminal_at_utc passes validation."""
        data = load_json(EXAMPLES / "task_valid_terminal_complete.json")
        self.task_validator.validate(data)
        self.assertEqual(data["status"]["current_state"], "BLOCKED")
        self.assertIn("stop_reason", data["status"])
        self.assertIn("terminal_at_utc", data["status"])

    def test_task_non_terminal_state_without_terminal_fields_passes(self) -> None:
        """Non-terminal state without stop_reason/terminal_at_utc still passes validation."""
        data = load_json(EXAMPLES / "task_minimal_valid.json")
        self.task_validator.validate(data)
        self.assertEqual(data["status"]["current_state"], "TASK_RECEIVED")
        self.assertNotIn("stop_reason", data["status"])
        self.assertNotIn("terminal_at_utc", data["status"])


class TestTaskSchemaEnumFreeze(unittest.TestCase):
    """Freeze task enums to prevent silent drift."""

    def test_task_kind_enum_frozen(self) -> None:
        """task_kind enum must not change without explicit version bump."""
        schema = load_json(SCHEMAS / "task.v0.1.schema.json")
        actual = set(schema["properties"]["task_kind"]["enum"])
        expected = {"execution", "ask", "ingestion", "evaluation"}
        self.assertEqual(actual, expected, "task_kind enum must not change without explicit version bump")

    def test_task_source_surface_enum_frozen(self) -> None:
        """source_surface enum must not change without explicit version bump."""
        schema = load_json(SCHEMAS / "task.v0.1.schema.json")
        actual = set(schema["properties"]["source_surface"]["enum"])
        expected = {"ide_execute", "ide_ask", "api_execute", "ingestion", "replay"}
        self.assertEqual(actual, expected, "source_surface enum must not change without explicit version bump")

    def test_task_current_state_aligns_with_state_enums(self) -> None:
        """Task status.current_state enum aligns with state_enums.v0.1.agent_state."""
        task_schema = load_json(SCHEMAS / "task.v0.1.schema.json")
        state_enums = load_json(REPO_ROOT / "runtime" / "state" / "schemas" / "state_enums.v0.1.json")
        task_states = set(task_schema["properties"]["status"]["properties"]["current_state"]["enum"])
        expected_states = set(state_enums["definitions"]["agent_state"]["enum"])
        self.assertEqual(task_states, expected_states, "Task current_state must align with state_enums.v0.1.agent_state")

    def test_task_stop_reason_aligns_with_state_enums(self) -> None:
        """Task status.stop_reason enum aligns with state_enums.v0.1.stop_reason."""
        task_schema = load_json(SCHEMAS / "task.v0.1.schema.json")
        state_enums = load_json(REPO_ROOT / "runtime" / "state" / "schemas" / "state_enums.v0.1.json")
        task_reasons = set(task_schema["properties"]["status"]["properties"]["stop_reason"]["enum"])
        expected_reasons = set(state_enums["definitions"]["stop_reason"]["enum"])
        self.assertEqual(task_reasons, expected_reasons, "Task stop_reason must align with state_enums.v0.1.stop_reason")

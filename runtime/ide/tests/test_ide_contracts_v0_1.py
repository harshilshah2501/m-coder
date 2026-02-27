"""
Schema and runtime-rule validation for IDE contracts v0.1.

Validates plan_request, decision_response, ide_event examples.
Enforces R-IDE1, R-IDE2, R-IDE3.
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

REPO_ROOT = Path(__file__).resolve().parents[3]
IDE_SCHEMAS = REPO_ROOT / "runtime" / "ide" / "schemas"
EXAMPLES = IDE_SCHEMAS / "examples"
RUNTIME_SCHEMAS = REPO_ROOT / "runtime" / "schemas"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def canonicalize_boundary_phrase(phrase: str) -> bytes:
    """Per boundary_hashing.v0.1: UTF-8, \\n line endings, no trim, no case fold."""
    s = phrase.replace("\r\n", "\n").replace("\r", "\n")
    return s.encode("utf-8")


def boundary_phrase_hash(phrase: str) -> str:
    return hashlib.sha256(canonicalize_boundary_phrase(phrase)).hexdigest()


def validate_ide_rules(
    resp: dict,
    *,
    lineage_index: dict | None = None,
) -> list[str]:
    """
    Validate decision_response against R-IDE1, R-IDE2, R-IDE3.
    Returns list of violated rule codes.
    """
    violations: list[str] = []
    if resp.get("schema_version") != "decision_response.v0.1":
        return violations

    phrase = resp.get("irreversible_boundary_phrase", "")
    phrase_hash = resp.get("boundary_phrase_hash", "")
    if phrase and phrase_hash != boundary_phrase_hash(phrase):
        violations.append("R-IDE1")

    phase = resp.get("constitutional_phase_emitted")
    decision = resp.get("decision")
    if phase == "REF" and decision not in ("REFUSAL",):
        violations.append("R-IDE2")

    prov = resp.get("provenance_resolution", {})
    resolved_via = prov.get("resolved_via")
    if resolved_via == "guessed":
        violations.append("R-IDE3")

    return violations


@unittest.skipIf(not HAS_JSONSCHEMA, "jsonschema not installed")
class TestIDEEventSchema(unittest.TestCase):
    """Validate IDE event examples."""

    def setUp(self) -> None:
        schema = load_json(IDE_SCHEMAS / "ide_event.v0.1.schema.json")
        self.validator = jsonschema.Draft7Validator(schema)

    def test_ide_event_pr_merge_valid(self) -> None:
        data = load_json(EXAMPLES / "ide_event_pr_merge.json")
        self.validator.validate(data)

    def test_ide_event_config_change_valid(self) -> None:
        data = load_json(EXAMPLES / "ide_event_config_change.json")
        self.validator.validate(data)


@unittest.skipIf(not HAS_JSONSCHEMA, "jsonschema not installed")
class TestPlanRequestSchema(unittest.TestCase):
    """Validate plan request examples."""

    def setUp(self) -> None:
        schema = load_json(IDE_SCHEMAS / "plan_request.v0.1.schema.json")
        self.validator = jsonschema.Draft7Validator(schema)

    def test_plan_request_shadow_valid(self) -> None:
        data = load_json(EXAMPLES / "plan_request_shadow.json")
        self.validator.validate(data)

    def test_plan_request_live_valid(self) -> None:
        data = load_json(EXAMPLES / "plan_request_live.json")
        self.validator.validate(data)


@unittest.skipIf(not HAS_JSONSCHEMA, "jsonschema not installed")
class TestDecisionResponseSchema(unittest.TestCase):
    """Validate decision response examples."""

    def setUp(self) -> None:
        schema = load_json(IDE_SCHEMAS / "decision_response.v0.1.schema.json")
        self.validator = jsonschema.Draft7Validator(schema)

    def _validate(self, name: str) -> None:
        data = load_json(EXAMPLES / name)
        self.validator.validate(data)

    def test_decision_refusal_valid(self) -> None:
        self._validate("decision_refusal_ref.json")

    def test_decision_conditional_block_valid(self) -> None:
        self._validate("decision_conditional_block_missing_authority.json")

    def test_decision_bounding_valid(self) -> None:
        self._validate("decision_bounding_conf_preboundary.json")

    def test_decision_approve_valid(self) -> None:
        self._validate("decision_approve_code_safe_execute.json")


@unittest.skipIf(not HAS_JSONSCHEMA, "jsonschema not installed")
class TestInvalidExamples(unittest.TestCase):
    """Invalid examples: schema-valid but rule-invalid."""

    def setUp(self) -> None:
        schema = load_json(IDE_SCHEMAS / "decision_response.v0.1.schema.json")
        self.validator = jsonschema.Draft7Validator(schema)

    def test_invalid_boundary_hash_schema_valid(self) -> None:
        data = load_json(EXAMPLES / "invalid_boundary_hash_mismatch_schema_valid.json")
        self.validator.validate(data)

    def test_invalid_boundary_hash_fails_ride1(self) -> None:
        data = load_json(EXAMPLES / "invalid_boundary_hash_mismatch_schema_valid.json")
        violations = validate_ide_rules(data)
        self.assertIn("R-IDE1", violations)
        self.assertNotIn("R-IDE2", violations)
        self.assertNotIn("R-IDE3", violations)

    def test_invalid_ref_softened_schema_valid(self) -> None:
        data = load_json(EXAMPLES / "invalid_ref_softened_schema_valid.json")
        self.validator.validate(data)

    def test_invalid_ref_softened_fails_ride2(self) -> None:
        data = load_json(EXAMPLES / "invalid_ref_softened_schema_valid.json")
        violations = validate_ide_rules(data)
        self.assertIn("R-IDE2", violations)
        self.assertNotIn("R-IDE1", violations)
        self.assertNotIn("R-IDE3", violations)

    def test_invalid_semantic_label_guessed_schema_valid(self) -> None:
        data = load_json(EXAMPLES / "invalid_semantic_label_guessed_schema_valid.json")
        self.validator.validate(data)

    def test_invalid_semantic_label_guessed_fails_ride3(self) -> None:
        data = load_json(EXAMPLES / "invalid_semantic_label_guessed_schema_valid.json")
        violations = validate_ide_rules(data)
        self.assertIn("R-IDE3", violations)
        self.assertNotIn("R-IDE1", violations)
        self.assertNotIn("R-IDE2", violations)


class TestEnumFreeze(unittest.TestCase):
    """Freeze enums to prevent drift."""

    def test_decision_enums_frozen(self) -> None:
        de = load_json(IDE_SCHEMAS / "decision_enums.v0.1.json")
        actual = set(de["items"]["enum"])
        expected = {"APPROVE", "CONDITIONAL_BLOCK", "REFUSAL", "BOUNDING"}
        self.assertEqual(actual, expected)

    def test_action_types_frozen(self) -> None:
        at = load_json(IDE_SCHEMAS / "action_types.v0.1.json")
        actual = set(at["items"]["enum"])
        expected = {"PR_MERGE", "CONFIG_CHANGE", "DEPLOY_INTENT", "PROD_WRITE_INTENT", "OTHER"}
        self.assertEqual(actual, expected)

    def test_authority_verdicts_frozen(self) -> None:
        av = load_json(IDE_SCHEMAS / "authority_verdicts.v0.1.json")
        actual = set(av["items"]["enum"])
        expected = {"pass", "fail", "unknown"}
        self.assertEqual(actual, expected)

    def test_reason_codes_match_runtime(self) -> None:
        rc = load_json(RUNTIME_SCHEMAS / "reason_codes.v0.1.json")
        allowed = set(rc["items"]["enum"])
        for name in ["decision_refusal_ref.json", "decision_conditional_block_missing_authority.json",
                     "decision_bounding_conf_preboundary.json", "invalid_boundary_hash_mismatch_schema_valid.json",
                     "invalid_ref_softened_schema_valid.json", "invalid_semantic_label_guessed_schema_valid.json"]:
            data = load_json(EXAMPLES / name)
            for code in data.get("reason_codes", []):
                self.assertIn(code, allowed, f"reason_code {code} in {name} must be in runtime enum")

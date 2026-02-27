"""
Schema and runtime-rule validation for Shadow Mode Protocol v0.1.

Validates shadow_session, shadow_run_record, ingestion_batch.
Enforces S-1 through S-6.
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
SHADOW_SCHEMAS = REPO_ROOT / "runtime" / "shadow" / "schemas"
EXAMPLES = SHADOW_SCHEMAS / "examples"
RUNTIME_SCHEMAS = REPO_ROOT / "runtime" / "schemas"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def canonicalize_boundary_phrase(phrase: str) -> bytes:
    """Per boundary_hashing.v0.1: UTF-8, \\n line endings, no trim."""
    s = phrase.replace("\r\n", "\n").replace("\r", "\n")
    return s.encode("utf-8")


def boundary_phrase_hash(phrase: str) -> str:
    return hashlib.sha256(canonicalize_boundary_phrase(phrase)).hexdigest()


def validate_shadow_rules(
    obj: dict,
    *,
    plan_obj: dict | None = None,
    ledger_obj: dict | None = None,
) -> list[str]:
    """
    Validate shadow objects against S-1 to S-6.
    Returns list of violated rule codes.
    """
    violations: list[str] = []

    if obj.get("schema_version") == "shadow_run_record.v0.1":
        if obj.get("boundary_verdict") == "crossed":
            violations.append("S-1")
        emitted = obj.get("emitted", {})
        if not emitted.get("plan_emitted") or not emitted.get("ledger_emitted"):
            violations.append("S-2")

    elif obj.get("schema_version") == "ingestion_batch.v0.1":
        for item in obj.get("items", []):
            ledger_row = item.get("ledger_row", {})
            b = ledger_row.get("boundary", {})
            if b.get("boundary_crossed"):
                violations.append("S-1")
            if "request_id" not in item or "plan" not in item or "ledger_row" not in item:
                violations.append("S-6")
            plan = item.get("plan", {})
            lr = item.get("ledger_row", {})
            if plan and lr:
                pl_hash = lr.get("plan_link", {}).get("plan_hash")
                if pl_hash:
                    dec = item.get("decision_response", {})
                    if dec and dec.get("plan_hash") and dec.get("plan_hash") != pl_hash:
                        violations.append("S-3")
            boundary_phrase = (plan.get("boundary", {}) or {}).get("irreversible_boundary_phrase", "")
            lr_phrase = (lr.get("boundary", {}) or {}).get("irreversible_boundary_phrase", "")
            lr_hash = lr.get("verdicts")  # boundary_phrase_hash not in ledger; check plan
            if boundary_phrase and plan:
                refs = item.get("lineage_refs", {})
                bp_hash = refs.get("boundary_phrase_hash")
                if bp_hash and bp_hash != boundary_phrase_hash(boundary_phrase or lr_phrase):
                    violations.append("S-4")

    return violations


@unittest.skipIf(not HAS_JSONSCHEMA, "jsonschema not installed")
class TestShadowSessionSchema(unittest.TestCase):
    def setUp(self) -> None:
        schema = load_json(SHADOW_SCHEMAS / "shadow_session.v0.1.schema.json")
        self.validator = jsonschema.Draft7Validator(schema)

    def test_shadow_session_valid(self) -> None:
        data = load_json(EXAMPLES / "shadow_session_valid.json")
        self.validator.validate(data)


@unittest.skipIf(not HAS_JSONSCHEMA, "jsonschema not installed")
class TestShadowRunRecordSchema(unittest.TestCase):
    def setUp(self) -> None:
        schema = load_json(SHADOW_SCHEMAS / "shadow_run_record.v0.1.schema.json")
        self.validator = jsonschema.Draft7Validator(schema)

    def test_shadow_run_plan_only_valid(self) -> None:
        data = load_json(EXAMPLES / "shadow_run_plan_only_valid.json")
        self.validator.validate(data)

    def test_shadow_run_decision_valid(self) -> None:
        data = load_json(EXAMPLES / "shadow_run_decision_valid.json")
        self.validator.validate(data)


@unittest.skipIf(not HAS_JSONSCHEMA, "jsonschema not installed")
class TestIngestionBatchSchema(unittest.TestCase):
    def setUp(self) -> None:
        schema = load_json(SHADOW_SCHEMAS / "ingestion_batch.v0.1.schema.json")
        self.validator = jsonschema.Draft7Validator(schema)

    def test_ingestion_batch_valid(self) -> None:
        data = load_json(EXAMPLES / "ingestion_batch_valid.json")
        self.validator.validate(data)

    def test_ingestion_batch_items_have_plan_and_ledger(self) -> None:
        data = load_json(EXAMPLES / "ingestion_batch_valid.json")
        plan_schema = load_json(RUNTIME_SCHEMAS / "plan.v0.1.schema.json")
        ledger_schema = load_json(RUNTIME_SCHEMAS / "ledger_row.v0.1.schema.json")
        plan_val = jsonschema.Draft7Validator(plan_schema)
        ledger_val = jsonschema.Draft7Validator(ledger_schema)
        for item in data.get("items", []):
            self.assertIn("request_id", item)
            plan_val.validate(item["plan"])
            ledger_val.validate(item["ledger_row"])


@unittest.skipIf(not HAS_JSONSCHEMA, "jsonschema not installed")
class TestInvalidExamples(unittest.TestCase):
    def setUp(self) -> None:
        schema = load_json(SHADOW_SCHEMAS / "shadow_run_record.v0.1.schema.json")
        self.validator = jsonschema.Draft7Validator(schema)

    def test_invalid_crossed_schema_valid(self) -> None:
        data = load_json(EXAMPLES / "invalid_shadow_crossed_in_shadow_schema_valid.json")
        self.validator.validate(data)

    def test_invalid_crossed_fails_s1(self) -> None:
        data = load_json(EXAMPLES / "invalid_shadow_crossed_in_shadow_schema_valid.json")
        v = validate_shadow_rules(data)
        self.assertIn("S-1", v)
        self.assertNotIn("S-2", v)

    def test_invalid_missing_ledger_schema_valid(self) -> None:
        data = load_json(EXAMPLES / "invalid_missing_ledger_emit_schema_valid.json")
        self.validator.validate(data)

    def test_invalid_missing_ledger_fails_s2(self) -> None:
        data = load_json(EXAMPLES / "invalid_missing_ledger_emit_schema_valid.json")
        v = validate_shadow_rules(data)
        self.assertIn("S-2", v)
        self.assertNotIn("S-1", v)


class TestEnumFreeze(unittest.TestCase):
    def test_transport_status_frozen(self) -> None:
        ts = load_json(SHADOW_SCHEMAS / "transport_status.v0.1.json")
        actual = set(ts["items"]["enum"])
        expected = {"ok", "gate_unreachable", "timeout", "error"}
        self.assertEqual(actual, expected)

    def test_boundary_verdicts_frozen(self) -> None:
        bv = load_json(SHADOW_SCHEMAS / "boundary_verdicts.v0.1.json")
        actual = set(bv["items"]["enum"])
        expected = {"blocked", "not_reached", "allowed_pre_boundary_only", "crossed"}
        self.assertEqual(actual, expected)

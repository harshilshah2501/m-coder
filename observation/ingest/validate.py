"""Validate ingestion batch items against schemas and rules."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
RUNTIME_SCHEMAS = REPO / "runtime" / "schemas"
IDE_SCHEMAS = REPO / "runtime" / "ide" / "schemas"
SHADOW_SCHEMAS = REPO / "runtime" / "shadow" / "schemas"

RISKY_BOUNDARY_TYPES = {"merge", "deploy", "prod_write", "security_change", "data_delete", "config_rollout"}
REFUSE_OR_DEFER = {"refuse", "defer"}


def load_json(p: Path) -> dict:
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def plan_hash(plan: dict) -> str:
    p = {k: v for k, v in plan.items() if k != "integrity"}
    c = json.dumps(p, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(c).hexdigest()


def boundary_phrase_hash(phrase: str) -> str:
    s = phrase.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _validate_plan_rules(plan: dict) -> list[str]:
    violations = []
    phase = plan.get("constitutional_phase_expected")
    posture = plan.get("policy_posture", {}).get("terminal_posture")
    auth_verdict = plan.get("authority", {}).get("validated", {}).get("verdict")
    boundary_type = plan.get("boundary", {}).get("boundary_type")
    if phase == "REF" and posture != "refuse":
        violations.append("R2")
    if auth_verdict != "pass" and boundary_type in RISKY_BOUNDARY_TYPES and posture not in REFUSE_OR_DEFER:
        violations.append("R1")
    if not (plan.get("boundary", {}).get("irreversible_boundary_phrase") or "").strip():
        violations.append("R5")
    return violations


def _validate_ledger_rules(ledger: dict) -> list[str]:
    violations = []
    v = ledger.get("verdicts", {})
    b = ledger.get("boundary", {})
    if v.get("authority_verdict") != "pass" and v.get("boundary_verdict") == "crossed":
        violations.append("L4")
    if b.get("boundary_crossed") and v.get("boundary_verdict") != "crossed":
        violations.append("L2")
    if not (b.get("irreversible_boundary_phrase") or "").strip():
        violations.append("L5")
    return violations


def _validate_decision_rules(dec: dict) -> list[str]:
    violations = []
    if dec.get("schema_version") != "decision_response.v0.1":
        return violations
    phrase = dec.get("irreversible_boundary_phrase", "")
    if phrase and dec.get("boundary_phrase_hash") != boundary_phrase_hash(phrase):
        violations.append("R-IDE1")
    if dec.get("constitutional_phase_emitted") == "REF" and dec.get("decision") != "REFUSAL":
        violations.append("R-IDE2")
    if dec.get("provenance_resolution", {}).get("resolved_via") == "guessed":
        violations.append("R-IDE3")
    return violations


def validate_batch_schema(batch: dict) -> list[str]:
    """Validate ingestion_batch against ingestion_batch.v0.1.schema.json."""
    errs = []
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema not installed"]
    path = SHADOW_SCHEMAS / "ingestion_batch.v0.1.schema.json"
    if path.exists():
        s = load_json(path)
        for e in jsonschema.Draft7Validator(s).iter_errors(batch):
            errs.append(f"ingestion_batch: {e.message}")
    return errs


def validate_item_schemas(item: dict) -> list[str]:
    errs = []
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema not installed"]
    for key, schema_name in [
        ("plan", "plan.v0.1.schema.json"),
        ("ledger_row", "ledger_row.v0.1.schema.json"),
    ]:
        obj = item.get(key)
        if not obj:
            errs.append(f"missing {key}")
            continue
        path = RUNTIME_SCHEMAS / schema_name
        if path.exists():
            s = load_json(path)
            for e in jsonschema.Draft7Validator(s).iter_errors(obj):
                errs.append(f"{key}: {e.message}")
    dec = item.get("decision_response")
    if dec:
        path = IDE_SCHEMAS / "decision_response.v0.1.schema.json"
        if path.exists():
            s = load_json(path)
            for e in jsonschema.Draft7Validator(s).iter_errors(dec):
                errs.append(f"decision_response: {e.message}")
    return errs


def validate_item_rules(item: dict) -> list[str]:
    violations = []
    plan = item.get("plan")
    ledger = item.get("ledger_row")
    dec = item.get("decision_response")
    if plan:
        violations.extend(_validate_plan_rules(plan))
    if ledger:
        violations.extend(_validate_ledger_rules(ledger))
    if dec:
        violations.extend(_validate_decision_rules(dec))
    return violations

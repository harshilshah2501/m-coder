"""Schema and rule validation. Reuses logic from runtime/ide/shadow tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

REPO = Path(__file__).resolve().parents[3]
RUNTIME_SCHEMAS = REPO / "runtime" / "schemas"
IDE_SCHEMAS = REPO / "runtime" / "ide" / "schemas"
SHADOW_SCHEMAS = REPO / "runtime" / "shadow" / "schemas"

RISKY_BOUNDARY_TYPES = {"merge", "deploy", "prod_write", "security_change", "data_delete", "config_rollout"}
REFUSE_OR_DEFER = {"refuse", "defer"}


def load_json(p: Path) -> dict:
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def boundary_phrase_hash(phrase: str) -> str:
    s = phrase.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def validate_runtime_rules_plan(plan: dict) -> list[str]:
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


def validate_runtime_rules_ledger(ledger: dict) -> list[str]:
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


def validate_ide_rules(resp: dict) -> list[str]:
    violations = []
    if resp.get("schema_version") != "decision_response.v0.1":
        return violations
    phrase = resp.get("irreversible_boundary_phrase", "")
    if phrase and resp.get("boundary_phrase_hash") != boundary_phrase_hash(phrase):
        violations.append("R-IDE1")
    if resp.get("constitutional_phase_emitted") == "REF" and resp.get("decision") != "REFUSAL":
        violations.append("R-IDE2")
    if resp.get("provenance_resolution", {}).get("resolved_via") == "guessed":
        violations.append("R-IDE3")
    return violations


def validate_shadow_rules(obj: dict) -> list[str]:
    violations = []
    if obj.get("schema_version") == "shadow_run_record.v0.1":
        if obj.get("boundary_verdict") == "crossed":
            violations.append("S-1")
        e = obj.get("emitted", {})
        if not e.get("plan_emitted") or not e.get("ledger_emitted"):
            violations.append("S-2")
    return violations


def validate_schemas(
    plan: dict,
    decision: dict,
    ledger: dict,
    shadow_run: dict,
    ingestion: dict,
) -> list[str]:
    """Validate all artifacts against JSON schemas. Returns list of error messages."""
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema not installed"]
    errs = []
    schemas = [
        (plan, RUNTIME_SCHEMAS / "plan.v0.1.schema.json"),
        (decision, IDE_SCHEMAS / "decision_response.v0.1.schema.json"),
        (ledger, RUNTIME_SCHEMAS / "ledger_row.v0.1.schema.json"),
        (shadow_run, SHADOW_SCHEMAS / "shadow_run_record.v0.1.schema.json"),
        (ingestion, SHADOW_SCHEMAS / "ingestion_batch.v0.1.schema.json"),
    ]
    for obj, path in schemas:
        if not path.exists():
            continue
        s = load_json(path)
        v = jsonschema.Draft7Validator(s)
        for e in v.iter_errors(obj):
            errs.append(f"{path.name}: {e.message}")
    return errs


def validate_all(
    plan: dict,
    decision: dict,
    ledger: dict,
    shadow_run: dict,
    ingestion: dict,
) -> list[str]:
    out = []
    out.extend(validate_runtime_rules_plan(plan))
    out.extend(validate_runtime_rules_ledger(ledger))
    out.extend(validate_ide_rules(decision))
    out.extend(validate_shadow_rules(shadow_run))
    return out

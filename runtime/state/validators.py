"""
Stage 3 schema validators.

Strict validation for locked Stage 3 contracts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema


SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"


class Stage3ValidationError(Exception):
    """Base error for Stage 3 validation failures."""


class SchemaValidationError(Stage3ValidationError):
    """Raised when JSON schema validation fails."""


class EvidenceIntegrityError(Stage3ValidationError):
    """Raised when evidence ref integrity checks fail."""


class SchemaRegistry:
    """Lazy schema registry with Draft 2020-12 validators."""

    _SCHEMAS: dict[str, jsonschema.Draft202012Validator] = {}
    _FILES = {
        "task_envelope": "task_envelope.v1.json",
        "model_proposal": "model_proposal.v1.json",
        "tool_execution_request": "tool_execution_request.v1.json",
        "tool_execution_result": "tool_execution_result.v1.json",
        "loop_decision": "loop_decision.v1.json",
        "final_response": "final_response.v1.json",
        "loop_context_frame": "loop_context_frame.v1.json",
    }

    @classmethod
    def get(cls, key: str) -> jsonschema.Draft202012Validator:
        if key not in cls._SCHEMAS:
            path = SCHEMA_DIR / cls._FILES[key]
            schema = json.loads(path.read_text(encoding="utf-8"))
            cls._SCHEMAS[key] = jsonschema.Draft202012Validator(schema)
        return cls._SCHEMAS[key]


def _raise_schema_errors(key: str, data: dict[str, Any]) -> None:
    validator = SchemaRegistry.get(key)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if not errors:
        return
    msg = "; ".join(f"{list(e.path)}: {e.message}" for e in errors)
    raise SchemaValidationError(f"{key} invalid: {msg}")


def _validate_refs_subset(refs: list[str], allowed: set[str], field_name: str) -> None:
    invalid = [r for r in refs if r not in allowed]
    if invalid:
        raise EvidenceIntegrityError(f"{field_name} contains unknown evidence refs: {invalid}")


def validate_task_envelope(data: dict[str, Any]) -> None:
    _raise_schema_errors("task_envelope", data)


def validate_loop_context_frame(data: dict[str, Any]) -> None:
    _raise_schema_errors("loop_context_frame", data)


def validate_model_proposal(
    data: dict[str, Any],
    *,
    allowed_evidence_refs: set[str],
) -> None:
    _raise_schema_errors("model_proposal", data)
    trace = data.get("reasoning_trace", [])
    for step in trace:
        refs = step.get("evidence_refs", [])
        _validate_refs_subset(refs, allowed_evidence_refs, "reasoning_trace.evidence_refs")


def validate_tool_execution_request(data: dict[str, Any]) -> None:
    _raise_schema_errors("tool_execution_request", data)


def validate_tool_execution_result(data: dict[str, Any]) -> None:
    _raise_schema_errors("tool_execution_result", data)


def validate_loop_decision(data: dict[str, Any]) -> None:
    _raise_schema_errors("loop_decision", data)


def validate_final_response(data: dict[str, Any], *, allowed_evidence_refs: set[str]) -> None:
    _raise_schema_errors("final_response", data)
    refs = data.get("evidence_refs", [])
    _validate_refs_subset(refs, allowed_evidence_refs, "final_response.evidence_refs")
    proposal_refs = data.get("proposal_refs", [])
    if proposal_refs:
        if any((not isinstance(r, str) or not r.strip()) for r in proposal_refs):
            raise EvidenceIntegrityError("final_response.proposal_refs must contain non-empty strings")
        if len(set(proposal_refs)) != len(proposal_refs):
            raise EvidenceIntegrityError("final_response.proposal_refs must be unique")
    tool_result_refs = data.get("tool_result_refs", [])
    if tool_result_refs:
        if any((not isinstance(r, str) or not r.strip()) for r in tool_result_refs):
            raise EvidenceIntegrityError("final_response.tool_result_refs must contain non-empty strings")
        if len(set(tool_result_refs)) != len(tool_result_refs):
            raise EvidenceIntegrityError("final_response.tool_result_refs must be unique")


def validate_frame_evidence_integrity(
    *,
    frame: dict[str, Any],
    task_envelope: dict[str, Any],
) -> None:
    frame_refs = set(frame.get("evidence_refs", []))
    allowed = set(task_envelope["evidence_bundle"]["evidence_refs"])
    missing = frame_refs - allowed
    if missing:
        raise EvidenceIntegrityError(f"frame contains evidence refs outside bundle: {sorted(missing)}")

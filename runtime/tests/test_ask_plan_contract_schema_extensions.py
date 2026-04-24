from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = REPO_ROOT / "runtime" / "ide" / "schemas"


def _load(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_ask_request_v1_allows_plan_contract_response_extension() -> None:
    schema = _load("ask_request.v1.0.schema.json")
    validator = jsonschema.Draft7Validator(schema)
    req = {
        "schema_version": "ask_request.v1.0",
        "request_id": "r1",
        "timestamp_utc": "2026-04-24T00:00:00Z",
        "query": "where is sync",
        "evidence_bundle": {"entries": [{"relative_path": "x.py"}]},
        "response_extensions": ["plan_contract.v1"],
    }
    errs = list(validator.iter_errors(req))
    assert errs == []


def test_ask_request_v1_allows_plan_and_trace_extension_tokens() -> None:
    schema = _load("ask_request.v1.0.schema.json")
    validator = jsonschema.Draft7Validator(schema)
    req = {
        "schema_version": "ask_request.v1.0",
        "request_id": "r1",
        "timestamp_utc": "2026-04-24T00:00:00Z",
        "query": "where is sync",
        "evidence_bundle": {"entries": [{"relative_path": "x.py"}]},
        "response_extensions": ["plan_contract.v1", "code_reasoning_trace.v1"],
    }
    errs = list(validator.iter_errors(req))
    assert errs == []


def test_ask_request_v1_allows_plan_trace_and_patch_proposal_tokens() -> None:
    schema = _load("ask_request.v1.0.schema.json")
    validator = jsonschema.Draft7Validator(schema)
    req = {
        "schema_version": "ask_request.v1.0",
        "request_id": "r1",
        "timestamp_utc": "2026-04-24T00:00:00Z",
        "query": "where is sync",
        "evidence_bundle": {"entries": [{"relative_path": "x.py"}]},
        "response_extensions": [
            "plan_contract.v1",
            "code_reasoning_trace.v1",
            "patch_proposal.v1",
        ],
    }
    errs = list(validator.iter_errors(req))
    assert errs == []


def test_ask_request_v1_rejects_unknown_response_extension() -> None:
    schema = _load("ask_request.v1.0.schema.json")
    validator = jsonschema.Draft7Validator(schema)
    req = {
        "schema_version": "ask_request.v1.0",
        "request_id": "r1",
        "timestamp_utc": "2026-04-24T00:00:00Z",
        "query": "where is sync",
        "evidence_bundle": {"entries": [{"relative_path": "x.py"}]},
        "response_extensions": ["unknown.extension.v1"],
    }
    errs = list(validator.iter_errors(req))
    assert errs, "unknown extension must be rejected"


def test_plan_only_response_v1_allows_optional_plan_contract_object() -> None:
    schema = _load("plan_only_response.v0.1.schema.json")
    validator = jsonschema.Draft7Validator(schema)
    resp = {
        "schema_version": "plan_only_response.v0.1",
        "request_id": "r2",
        "timestamp_utc": "2026-04-24T00:00:00Z",
        "context_bundle": {"revision": "rev1", "files": [], "selectors_used": []},
        "plan_summary": {"steps": ["Read context first"]},
        "governance_posture": "PLAN_ONLY",
        "execution": False,
        "ui": {"title": "t", "message": "m", "severity": "info"},
        "plan_contract": {
            "schema_version": "plan_contract.v1",
            "task_intent": {"summary": "x", "kind": "explore"},
        },
    }
    errs = list(validator.iter_errors(resp))
    assert errs == []


def test_plan_only_response_v1_allows_optional_code_reasoning_trace_object() -> None:
    schema = _load("plan_only_response.v0.1.schema.json")
    validator = jsonschema.Draft7Validator(schema)
    resp = {
        "schema_version": "plan_only_response.v0.1",
        "request_id": "r2",
        "timestamp_utc": "2026-04-24T00:00:00Z",
        "context_bundle": {"revision": "rev1", "files": [], "selectors_used": []},
        "plan_summary": {"steps": ["Read context first"]},
        "governance_posture": "PLAN_ONLY",
        "execution": False,
        "ui": {"title": "t", "message": "m", "severity": "info"},
        "code_reasoning_trace": {
            "schema_version": "code_reasoning_trace.v1",
            "request_id": "r2",
        },
    }
    errs = list(validator.iter_errors(resp))
    assert errs == []


def test_plan_only_response_v1_allows_optional_patch_proposal_object() -> None:
    schema = _load("plan_only_response.v0.1.schema.json")
    validator = jsonschema.Draft7Validator(schema)
    resp = {
        "schema_version": "plan_only_response.v0.1",
        "request_id": "r2",
        "timestamp_utc": "2026-04-24T00:00:00Z",
        "context_bundle": {"revision": "rev1", "files": [], "selectors_used": []},
        "plan_summary": {"steps": ["Read context first"]},
        "governance_posture": "PLAN_ONLY",
        "execution": False,
        "ui": {"title": "t", "message": "m", "severity": "info"},
        "patch_proposal": {
            "schema_version": "patch_proposal.v1",
            "proposal_ref": "patch_proposal:r2",
        },
    }
    errs = list(validator.iter_errors(resp))
    assert errs == []

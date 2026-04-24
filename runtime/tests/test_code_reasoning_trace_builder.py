from __future__ import annotations

import pytest

from runtime.ask_service.code_reasoning_trace_builder import build_code_reasoning_trace_v1
from runtime.code_reasoning.v1_validate import validate_code_reasoning_trace_v1


def _valid_plan_contract() -> dict:
    return {
        "schema_version": "plan_contract.v1",
        "task_intent": {"summary": "Refactor bounded service code", "kind": "refactor"},
        "affected_files": [{"path": "src/service.py", "role": "primary"}],
        "evidence_requirements": {
            "must_have": ["grounded_context_bundle"],
            "nice_to_have": [],
            "insufficient_without": [],
        },
        "change_boundaries": {
            "in_scope": ["Refactor internals"],
            "out_of_scope": ["No execute path changes"],
            "max_files_touched": 3,
            "max_diff_lines_hint": 150,
        },
        "risk_class": "medium",
        "allowed_actions": ["read_repo", "propose_patch_text"],
        "forbidden_actions": ["execute_shell", "privileged_write"],
        "approval_posture": "requires_human_approval",
        "confidence_limits": {"known": [], "unknown": [], "requires_resolution": []},
    }


def _metadata() -> dict:
    return {
        "intent_type": "GENERAL_INTENT",
        "evidence_quality": "STRONG",
        "quality_reasons": ["OWNER_ANCHOR_RECOVERY"],
    }


def test_trace_builder_builds_valid_trace_for_valid_plan() -> None:
    pc = _valid_plan_contract()
    res = build_code_reasoning_trace_v1(
        request_id="req-1",
        query="Where is the parsing logic?",
        plan_steps=["Locate parser", "Inspect call sites"],
        metadata=_metadata(),
        plan_contract=pc,
    )
    assert res.omission_reason is None
    assert isinstance(res.code_reasoning_trace, dict)
    assert res.code_reasoning_trace.get("schema_version") == "code_reasoning_trace.v1"
    assert validate_code_reasoning_trace_v1(res.code_reasoning_trace, pc) == []


def test_trace_builder_omits_when_plan_missing() -> None:
    res = build_code_reasoning_trace_v1(
        request_id="req-2",
        query="x",
        plan_steps=[],
        metadata=_metadata(),
        plan_contract=None,
    )
    assert res.code_reasoning_trace is None
    assert res.omission_reason == "missing_plan_contract"


def test_trace_builder_omits_when_plan_invalid() -> None:
    invalid_plan = {"schema_version": "plan_contract.v1"}  # missing required fields
    res = build_code_reasoning_trace_v1(
        request_id="req-3",
        query="x",
        plan_steps=[],
        metadata=_metadata(),
        plan_contract=invalid_plan,
    )
    assert res.code_reasoning_trace is None
    assert res.omission_reason == "invalid_plan_contract"


@pytest.mark.parametrize(
    "approval_posture,risk_class",
    [
        ("refuse", "critical"),
        ("defer", "insufficient_evidence"),
        ("advisory_only", "insufficient_evidence"),
    ],
)
def test_trace_builder_omits_for_refusal_or_insufficient_plan(
    approval_posture: str, risk_class: str
) -> None:
    pc = _valid_plan_contract()
    pc["approval_posture"] = approval_posture
    pc["risk_class"] = risk_class
    res = build_code_reasoning_trace_v1(
        request_id="req-4",
        query="x",
        plan_steps=[],
        metadata=_metadata(),
        plan_contract=pc,
    )
    assert res.code_reasoning_trace is None
    assert res.omission_reason == "forbidden_or_refusal_posture"


def test_trace_builder_omits_when_metadata_insufficient() -> None:
    pc = _valid_plan_contract()
    res = build_code_reasoning_trace_v1(
        request_id="req-5",
        query="x",
        plan_steps=[],
        metadata={"intent_type": "GENERAL_INTENT"},
        plan_contract=pc,
    )
    assert res.code_reasoning_trace is None
    assert res.omission_reason == "insufficient_metadata"


def test_trace_builder_omits_when_generated_trace_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    pc = _valid_plan_contract()

    monkeypatch.setattr(
        "runtime.ask_service.code_reasoning_trace_builder.validate_code_reasoning_trace_v1",
        lambda *_a, **_k: ["synthetic invalid trace"],
    )
    res = build_code_reasoning_trace_v1(
        request_id="req-6",
        query="x",
        plan_steps=[],
        metadata=_metadata(),
        plan_contract=pc,
    )
    assert res.code_reasoning_trace is None
    assert res.omission_reason == "generated_trace_invalid"

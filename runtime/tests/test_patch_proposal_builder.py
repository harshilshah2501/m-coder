from __future__ import annotations

import pytest

from runtime.ask_service.patch_proposal_builder import build_patch_proposal_v1
from runtime.patch_proposal.v1_validate import validate_patch_proposal_v1


def _valid_plan_contract() -> dict:
    return {
        "schema_version": "plan_contract.v1",
        "task_intent": {"summary": "Refactor bounded service code", "kind": "refactor"},
        "affected_files": [
            {"path": "src/service.py", "role": "primary"},
            {"path": "src/helpers.py", "role": "secondary"},
        ],
        "evidence_requirements": {
            "must_have": ["grounded_context_bundle"],
            "nice_to_have": [],
            "insufficient_without": [],
        },
        "change_boundaries": {
            "in_scope": ["Refactor internals"],
            "out_of_scope": ["No execute path changes"],
            "max_files_touched": 2,
            "max_diff_lines_hint": 120,
        },
        "risk_class": "medium",
        "allowed_actions": ["read_repo", "propose_patch_text"],
        "forbidden_actions": ["execute_shell", "privileged_write"],
        "approval_posture": "requires_human_approval",
        "confidence_limits": {"known": [], "unknown": [], "requires_resolution": []},
    }


def _valid_trace() -> dict:
    return {
        "schema_version": "code_reasoning_trace.v1",
        "request_id": "req-1",
        "plan_contract_ref": "plan_contract_sha256:abc",
        "bounds": {
            "max_iterations": 4,
            "max_tool_calls": 0,
            "max_evidence_refs_per_step": 8,
            "max_step_text_chars": 1024,
            "max_patch_intent_files": 2,
            "max_patch_intent_lines_total": 120,
            "summarize_between_steps": True,
        },
        "steps": [
            {
                "step_index": 0,
                "step_kind": "LOCATE_TARGET",
                "status": "complete",
                "evidence_requirements": {
                    "must_have": ["grounded_context_bundle"],
                    "nice_to_have": [],
                    "insufficient_without": [],
                },
                "evidence_refs_used": ["ask.evidence_bundle"],
                "rationale": "Locate target.",
                "summary": "Locate target.",
            },
            {
                "step_index": 1,
                "step_kind": "INSPECT_CONTEXT",
                "status": "complete",
                "evidence_requirements": {
                    "must_have": ["grounded_context_bundle"],
                    "nice_to_have": [],
                    "insufficient_without": [],
                },
                "evidence_refs_used": ["ask.metadata"],
                "rationale": "Inspect context.",
                "summary": "Inspect context.",
            },
            {
                "step_index": 2,
                "step_kind": "CHANGE_STRATEGY",
                "status": "complete",
                "evidence_requirements": {
                    "must_have": ["plan_contract"],
                    "nice_to_have": [],
                    "insufficient_without": [],
                },
                "evidence_refs_used": ["plan_contract"],
                "rationale": "Build strategy.",
                "summary": "Build strategy.",
            },
            {
                "step_index": 3,
                "step_kind": "FINAL_PROPOSAL",
                "status": "complete",
                "evidence_requirements": {
                    "must_have": ["plan_contract"],
                    "nice_to_have": [],
                    "insufficient_without": [],
                },
                "evidence_refs_used": ["plan_contract"],
                "rationale": "Finalize.",
                "summary": "Finalize.",
            },
        ],
        "terminal": {
            "outcome": "completed",
            "reason_code": "trace_ready_plan_only",
            "human_message": "Trace complete.",
            "execution_requested": False,
        },
        "ledger_preview": [{"event_type": "code_reasoning_session_start"}],
    }


def _metadata() -> dict:
    return {
        "intent_type": "GENERAL_INTENT",
        "evidence_quality": "STRONG",
        "quality_reasons": ["OWNER_ANCHOR_RECOVERY"],
    }


def test_patch_proposal_builder_builds_valid_proposal_for_valid_chain() -> None:
    pc = _valid_plan_contract()
    tr = _valid_trace()
    res = build_patch_proposal_v1(
        request_id="req-1",
        query="Refactor service flow",
        plan_steps=["Locate owner", "Refactor bounded path"],
        metadata=_metadata(),
        plan_contract=pc,
        code_reasoning_trace=tr,
    )
    assert res.omission_reason is None
    assert isinstance(res.patch_proposal, dict)
    assert res.patch_proposal.get("schema_version") == "patch_proposal.v1"
    assert validate_patch_proposal_v1(res.patch_proposal, pc, tr) == []


def test_patch_proposal_builder_omits_when_plan_missing() -> None:
    res = build_patch_proposal_v1(
        request_id="req-2",
        query="x",
        plan_steps=[],
        metadata=_metadata(),
        plan_contract=None,
        code_reasoning_trace=_valid_trace(),
    )
    assert res.patch_proposal is None
    assert res.omission_reason == "missing_plan_contract"


def test_patch_proposal_builder_omits_when_trace_missing() -> None:
    res = build_patch_proposal_v1(
        request_id="req-3",
        query="x",
        plan_steps=[],
        metadata=_metadata(),
        plan_contract=_valid_plan_contract(),
        code_reasoning_trace=None,
    )
    assert res.patch_proposal is None
    assert res.omission_reason == "missing_code_reasoning_trace"


@pytest.mark.parametrize(
    "approval_posture,risk_class",
    [
        ("refuse", "critical"),
        ("defer", "insufficient_evidence"),
        ("advisory_only", "insufficient_evidence"),
    ],
)
def test_patch_proposal_builder_omits_for_refusal_or_insufficient_plan(
    approval_posture: str, risk_class: str
) -> None:
    pc = _valid_plan_contract()
    pc["approval_posture"] = approval_posture
    pc["risk_class"] = risk_class
    res = build_patch_proposal_v1(
        request_id="req-4",
        query="x",
        plan_steps=[],
        metadata=_metadata(),
        plan_contract=pc,
        code_reasoning_trace=_valid_trace(),
    )
    assert res.patch_proposal is None
    assert res.omission_reason == "forbidden_or_refusal_posture"


def test_patch_proposal_builder_omits_when_metadata_insufficient() -> None:
    res = build_patch_proposal_v1(
        request_id="req-5",
        query="x",
        plan_steps=[],
        metadata={"intent_type": "GENERAL_INTENT"},
        plan_contract=_valid_plan_contract(),
        code_reasoning_trace=_valid_trace(),
    )
    assert res.patch_proposal is None
    assert res.omission_reason == "insufficient_metadata"


def test_patch_proposal_builder_omits_when_generated_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "runtime.ask_service.patch_proposal_builder.validate_patch_proposal_v1",
        lambda *_a, **_k: ["synthetic invalid proposal"],
    )
    res = build_patch_proposal_v1(
        request_id="req-6",
        query="Refactor x",
        plan_steps=[],
        metadata=_metadata(),
        plan_contract=_valid_plan_contract(),
        code_reasoning_trace=_valid_trace(),
    )
    assert res.patch_proposal is None
    assert res.omission_reason == "generated_patch_proposal_invalid"


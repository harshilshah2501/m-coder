from __future__ import annotations

from pathlib import Path

import pytest

from runtime.code_reasoning.v1_validate import (
    validate_code_reasoning_category,
    validate_code_reasoning_trace_v1,
    validate_patch_intent_v1,
)
from runtime.scripts import motadata_behavior_verify as verify


def _minimal_plan() -> dict:
    return {
        "schema_version": "plan_contract.v1",
        "task_intent": {"summary": "x", "kind": "fix"},
        "affected_files": [{"path": "a/B.java", "role": "primary"}],
        "evidence_requirements": {"must_have": [], "nice_to_have": [], "insufficient_without": []},
        "change_boundaries": {
            "in_scope": ["x"],
            "out_of_scope": ["y"],
            "max_files_touched": 2,
            "max_diff_lines_hint": 50,
        },
        "risk_class": "medium",
        "allowed_actions": ["read_repo", "propose_patch_text"],
        "forbidden_actions": ["execute_shell", "privileged_write", "none", "run_tests_local", "run_linter", "update_docs_only"],
        "approval_posture": "requires_human_approval",
        "confidence_limits": {"known": [], "unknown": [], "requires_resolution": []},
    }


def test_validate_patch_intent_v1_respects_plan_max_lines() -> None:
    pc = _minimal_plan()
    pi = {
        "schema_version": "patch_intent.v1",
        "files": [{"path": "a/B.java", "role": "edit", "line_span_hint": {"start": 1, "end": 100}}],
        "intent_description": "d",
        "rollback_summary": "r",
        "test_plan": [],
        "risk_notes": [],
    }
    errs = validate_patch_intent_v1(pi, pc)
    assert any("exceeds plan_contract max_diff_lines_hint" in e for e in errs)


def test_run_scenario_suite_code_reasoning_offline_graph_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    scenarios_path = repo_root / "docs" / "validation" / "motadata_aiops_behavior_scenarios.v1.json"
    ids = {
        "code_reasoning_trace_v1_completed_valid",
        "code_reasoning_trace_v1_invalid_step_ordering",
    }
    monkeypatch.setattr(verify, "_graph_preflight", lambda: {"state": "UNREACHABLE", "reason": "no driver"})
    out = verify.run_scenario_suite(
        scenarios_path,
        workspace_root=str(repo_root),
        context_url="http://127.0.0.1:8091",
        plan_gate_url="http://127.0.0.1:8089",
        top_k=8,
        scenario_ids=ids,
    )
    assert "error" not in out
    assert out.get("all_pass") is True


def test_validate_code_reasoning_category_invalid_ordering_requires_errors() -> None:
    pc = _minimal_plan()
    trace = {
        "schema_version": "code_reasoning_trace.v1",
        "request_id": "r1",
        "plan_contract_ref": "ref",
        "bounds": {
            "max_iterations": 3,
            "max_tool_calls": 1,
            "max_evidence_refs_per_step": 4,
            "max_step_text_chars": 1000,
            "max_patch_intent_files": 0,
            "max_patch_intent_lines_total": 0,
            "summarize_between_steps": False,
        },
        "steps": [
            {
                "step_index": 0,
                "step_kind": "INSPECT_CONTEXT",
                "status": "complete",
                "evidence_requirements": {"must_have": [], "nice_to_have": [], "insufficient_without": []},
                "evidence_refs_used": ["e1"],
                "rationale": "bad",
                "summary": "inspect first",
            },
            {
                "step_index": 1,
                "step_kind": "LOCATE_TARGET",
                "status": "complete",
                "evidence_requirements": {"must_have": [], "nice_to_have": [], "insufficient_without": []},
                "evidence_refs_used": ["e1"],
                "rationale": "bad",
                "summary": "locate second",
            },
            {
                "step_index": 2,
                "step_kind": "FINAL_PROPOSAL",
                "status": "complete",
                "evidence_requirements": {"must_have": [], "nice_to_have": [], "insufficient_without": []},
                "evidence_refs_used": ["e1"],
                "rationale": "x",
                "summary": "final",
            },
        ],
        "terminal": {
            "outcome": "refused",
            "reason_code": "invalid_step_ordering_fixture",
            "human_message": "negative",
            "execution_requested": False,
        },
    }
    assert validate_code_reasoning_category(trace, pc, "invalid_step_ordering") == []


def test_validate_code_reasoning_trace_requires_contiguous_indices() -> None:
    pc = _minimal_plan()
    trace = {
        "schema_version": "code_reasoning_trace.v1",
        "request_id": "r1",
        "plan_contract_ref": "ref",
        "bounds": {
            "max_iterations": 2,
            "max_tool_calls": 1,
            "max_evidence_refs_per_step": 4,
            "max_step_text_chars": 1000,
            "max_patch_intent_files": 0,
            "max_patch_intent_lines_total": 0,
            "summarize_between_steps": False,
        },
        "steps": [
            {
                "step_index": 0,
                "step_kind": "LOCATE_TARGET",
                "status": "complete",
                "evidence_requirements": {"must_have": [], "nice_to_have": [], "insufficient_without": []},
                "evidence_refs_used": ["e"],
                "rationale": "a",
                "summary": "s",
            },
            {
                "step_index": 2,
                "step_kind": "INSPECT_CONTEXT",
                "status": "complete",
                "evidence_requirements": {"must_have": [], "nice_to_have": [], "insufficient_without": []},
                "evidence_refs_used": ["e"],
                "rationale": "b",
                "summary": "t",
            },
        ],
        "terminal": {
            "outcome": "refused",
            "reason_code": "x",
            "human_message": "m",
            "execution_requested": False,
        },
    }
    errs = validate_code_reasoning_trace_v1(trace, pc)
    assert any("step_index set" in e for e in errs)

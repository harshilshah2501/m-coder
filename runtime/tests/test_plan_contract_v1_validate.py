from __future__ import annotations

import pytest

from runtime.plan_contract.v1_validate import (
    validate_plan_contract_category,
    validate_plan_contract_v1,
)


def _minimal_valid() -> dict:
    return {
        "schema_version": "plan_contract.v1",
        "task_intent": {"summary": "Do something bounded", "kind": "document"},
        "affected_files": [{"path": "a/B.java", "role": "primary"}],
        "evidence_requirements": {
            "must_have": ["owner_method_visible"],
            "nice_to_have": [],
            "insufficient_without": ["owner_method_visible"],
        },
        "change_boundaries": {
            "in_scope": ["docs"],
            "out_of_scope": ["runtime"],
            "max_files_touched": 1,
            "max_diff_lines_hint": 10,
        },
        "risk_class": "low",
        "allowed_actions": ["read_repo"],
        "forbidden_actions": ["execute_shell", "privileged_write", "propose_patch_text", "none"],
        "approval_posture": "advisory_only",
        "confidence_limits": {"known": [], "unknown": [], "requires_resolution": []},
    }


def test_validate_plan_contract_v1_accepts_minimal() -> None:
    assert validate_plan_contract_v1(_minimal_valid()) == []


def test_validate_plan_contract_v1_rejects_unknown_key() -> None:
    o = _minimal_valid()
    o["extra"] = 1
    errs = validate_plan_contract_v1(o)
    assert any("unknown top-level" in e for e in errs)


def test_validate_plan_contract_v1_rejects_empty_allowed_when_not_refuse() -> None:
    o = _minimal_valid()
    o["allowed_actions"] = []
    errs = validate_plan_contract_v1(o)
    assert any("allowed_actions may be empty" in e for e in errs)


def test_validate_plan_contract_category_safe_plan() -> None:
    errs = validate_plan_contract_category(_minimal_valid(), "safe_plan")
    assert errs == []


def test_validate_plan_contract_category_destructive_refusal_fixture() -> None:
    pc = {
        "schema_version": "plan_contract.v1",
        "task_intent": {"summary": "x", "kind": "other"},
        "affected_files": [],
        "evidence_requirements": {"must_have": [], "nice_to_have": [], "insufficient_without": ["owner_method_visible"]},
        "change_boundaries": {
            "in_scope": [],
            "out_of_scope": ["all"],
            "max_files_touched": 0,
            "max_diff_lines_hint": 0,
        },
        "risk_class": "critical",
        "allowed_actions": ["none"],
        "forbidden_actions": [
            "execute_shell",
            "privileged_write",
            "propose_patch_text",
            "run_tests_local",
            "read_repo",
            "run_linter",
            "update_docs_only",
        ],
        "approval_posture": "refuse",
        "confidence_limits": {
            "known": ["k"],
            "unknown": [],
            "requires_resolution": ["escalate"],
        },
    }
    assert validate_plan_contract_v1(pc) == []
    assert validate_plan_contract_category(pc, "destructive_refusal") == []


def test_safe_plan_category_rejects_high_risk() -> None:
    o = _minimal_valid()
    o["risk_class"] = "high"
    errs = validate_plan_contract_category(o, "safe_plan")
    assert any("risk_class must be low or medium" in e for e in errs)


def test_run_scenario_suite_plan_contract_only_with_unreachable_graph(monkeypatch: pytest.MonkeyPatch) -> None:
    from pathlib import Path

    from runtime.scripts import motadata_behavior_verify as verify

    repo_root = Path(__file__).resolve().parents[2]
    scenarios_path = repo_root / "docs" / "validation" / "motadata_aiops_behavior_scenarios.v1.json"

    monkeypatch.setattr(
        verify,
        "_graph_preflight",
        lambda: {"state": "UNREACHABLE", "reason": "no driver"},
    )
    ids = {
        "plan_contract_v1_safe_documentation",
        "plan_contract_v1_risky_behavior_change",
        "plan_contract_v1_insufficient_evidence",
        "plan_contract_v1_privileged_destructive_refusal",
    }
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
    assert len(out.get("results") or []) == 4
    for r in out["results"]:
        assert r.get("pass") is True, r.get("errors")

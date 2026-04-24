from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.patch_proposal.v1_validate import validate_patch_proposal_quality_category
from runtime.patch_proposal.v1_validate import score_patch_proposal_quality
from runtime.scripts import motadata_behavior_verify as verify


REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_PATH = REPO_ROOT / "docs" / "validation" / "patch_proposal_quality_scenarios.v1.json"


def _scenario_by_id(sid: str) -> dict:
    data = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    for row in data.get("scenarios") or []:
        if isinstance(row, dict) and row.get("id") == sid:
            return row
    raise KeyError(sid)


def test_patch_proposal_quality_category_clear_and_bounded() -> None:
    row = _scenario_by_id("patch_proposal_quality_clear_and_bounded")
    errs = validate_patch_proposal_quality_category(
        row["patch_proposal_fixture"],
        row["plan_contract_fixture"],
        row["code_reasoning_trace_fixture"],
        "clear_and_bounded",
    )
    assert errs == []


def test_patch_proposal_quality_category_overbound_detected() -> None:
    row = _scenario_by_id("patch_proposal_quality_overbound")
    errs = validate_patch_proposal_quality_category(
        row["patch_proposal_fixture"],
        row["plan_contract_fixture"],
        row["code_reasoning_trace_fixture"],
        "overbound",
    )
    assert errs == []


def test_patch_proposal_quality_category_missing_rollback_detected() -> None:
    row = _scenario_by_id("patch_proposal_quality_missing_rollback")
    errs = validate_patch_proposal_quality_category(
        row["patch_proposal_fixture"],
        row["plan_contract_fixture"],
        row["code_reasoning_trace_fixture"],
        "missing_rollback",
    )
    assert errs == []


def test_run_scenario_suite_patch_proposal_offline_graph_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ids = {
        "patch_proposal_quality_builder_generated_control",
        "patch_proposal_quality_clear_and_bounded",
        "patch_proposal_quality_missing_rollback",
        "patch_proposal_quality_overbound",
        "patch_proposal_quality_weak_test_plan",
        "patch_proposal_quality_good_reviewer_structure",
    }
    monkeypatch.setattr(
        verify,
        "_graph_preflight",
        lambda: {"state": "UNREACHABLE", "reason": "no driver"},
    )
    out = verify.run_scenario_suite(
        SCENARIOS_PATH,
        workspace_root=str(REPO_ROOT),
        context_url="http://127.0.0.1:8091",
        plan_gate_url="http://127.0.0.1:8089",
        top_k=8,
        scenario_ids=ids,
    )
    assert "error" not in out
    assert out.get("all_pass") is True
    assert len(out.get("results") or []) == 6
    for r in out.get("results") or []:
        qs = ((r.get("actual_summary") or {}).get("quality_score") or {})
        assert "score_percent" in qs
        assert "criteria" in qs
        assert isinstance(qs.get("criteria"), dict)


def test_patch_proposal_quality_score_has_structural_and_rubric_fields() -> None:
    row = _scenario_by_id("patch_proposal_quality_clear_and_bounded")
    qs = score_patch_proposal_quality(
        row["patch_proposal_fixture"],
        row["plan_contract_fixture"],
        row["code_reasoning_trace_fixture"],
    )
    assert qs.get("structural_valid") is True
    assert isinstance(qs.get("score_percent"), float)
    assert qs.get("total_criteria", 0) >= 8
    criteria = qs.get("criteria")
    assert isinstance(criteria, dict)
    assert "review_human_required_true" in criteria
    assert "bounds_max_files_within_plan" in criteria


def test_patch_quality_summary_aggregates_top_failed_criteria() -> None:
    suite = {
        "results": [
            {
                "capability": "patch_proposal_validate",
                "actual_summary": {
                    "quality_score": {
                        "score_percent": 80.0,
                        "criteria": {
                            "a": True,
                            "b": False,
                            "c": False,
                        },
                    }
                },
            },
            {
                "capability": "patch_proposal_validate",
                "actual_summary": {
                    "quality_score": {
                        "score_percent": 60.0,
                        "criteria": {
                            "a": True,
                            "b": False,
                            "d": False,
                        },
                    }
                },
            },
        ]
    }
    s = verify._patch_quality_summary(suite)
    assert isinstance(s, dict)
    assert s.get("scenario_count") == 2
    assert s.get("average_score_percent") == 70.0
    top = s.get("top_failed_criteria") or []
    assert top[0][0] == "b"
    assert top[0][1] == 2


def test_patch_quality_summary_can_be_derived_from_scenario_suite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ids = {
        "patch_proposal_quality_builder_generated_control",
        "patch_proposal_quality_clear_and_bounded",
        "patch_proposal_quality_missing_rollback",
    }
    monkeypatch.setattr(
        verify,
        "_graph_preflight",
        lambda: {"state": "UNREACHABLE", "reason": "no driver"},
    )
    out = verify.run_scenario_suite(
        SCENARIOS_PATH,
        workspace_root=str(REPO_ROOT),
        context_url="http://127.0.0.1:8091",
        plan_gate_url="http://127.0.0.1:8089",
        top_k=8,
        scenario_ids=ids,
    )
    summary = verify._patch_quality_summary(out)
    assert isinstance(summary, dict)
    assert summary.get("scenario_count") == 3
    assert "average_score_percent" in summary


def test_builder_generated_quality_scenario_passes() -> None:
    row = _scenario_by_id("patch_proposal_quality_builder_generated_control")
    res = verify._run_scenario_row(
        row,
        workspace_root=str(REPO_ROOT),
        context_url="http://127.0.0.1:8091",
        plan_gate_url="http://127.0.0.1:8089",
        top_k=8,
        quality_policy=None,
        export_stage_a=None,
    )
    assert res.get("pass") is True
    qs = ((res.get("actual_summary") or {}).get("quality_score") or {})
    assert qs.get("structural_valid") is True
    assert float(qs.get("score_percent") or 0.0) >= 90.0


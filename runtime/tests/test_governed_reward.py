from __future__ import annotations

from runtime.learning.governed_reward import score_governed_response


def _base_resp() -> dict:
    return {
        "governance_posture": "PLAN_ONLY",
        "execution": False,
        "evidence_first_meta": {"ask_path": "v1_evidence"},
        "metadata": {"evidence_quality": "WEAK"},
        "plan_summary": {"steps": ["Direct answer (grounded): could not determine from top evidence."]},
    }


def test_reward_plan_only_weak_honest_is_observational_or_better():
    rr = score_governed_response(_base_resp())
    assert rr.total_reward >= 0
    assert rr.eligibility in {"observational", "silver", "gold"}
    assert rr.hard_violations == []


def test_reward_hard_violation_on_execution_bypass():
    r = _base_resp()
    r["execution"] = True
    rr = score_governed_response(r)
    assert "execution_bypass_plan_only" in rr.hard_violations
    assert rr.eligibility == "banned"


def test_reward_hard_violation_on_false_strong_low_evidence():
    r = _base_resp()
    r["metadata"]["evidence_quality"] = "NO_MATCH"
    r["plan_summary"]["steps"] = ["Direct answer (grounded): APIServer extends BaseApiServer."]
    rr = score_governed_response(r)
    assert "false_strong_under_low_evidence" in rr.hard_violations
    assert rr.eligibility == "banned"


def test_reward_insufficient_neutral_plan_is_not_false_strong():
    r = _base_resp()
    r["metadata"]["evidence_quality"] = "INSUFFICIENT"
    r["plan_summary"]["steps"] = ["Open config file and inspect relevant sections."]
    rr = score_governed_response(r)
    assert "false_strong_under_low_evidence" not in rr.hard_violations
    assert rr.total_reward >= 0
    assert rr.eligibility in {"observational", "silver", "gold"}


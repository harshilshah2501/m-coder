from __future__ import annotations

import json
from pathlib import Path

from runtime.scripts import motadata_behavior_verify as verify


def _evidence_bundle(path: str = "motadata/src/main/java/com/mindarray/aiops/MailConfigDomainService.java") -> dict:
    return {
        "schema_hint": "layer5.evidence_bundle.v1",
        "workspace_identity_hash": "abc123",
        "entries": [
            {
                "relative_path": path,
                "retrieval_role": "PRIMARY_OWNER_CANDIDATE",
                "snippet": {
                    "text": "public class MailConfigDomainService { }",
                    "selection_reason": "query_token_substring_anchor",
                },
            }
        ],
    }


def _ask_resp_with_steps(steps: list[str]) -> dict:
    return {
        "request_id": "req-1",
        "governance_posture": "PLAN_ONLY",
        "execution": False,
        "evidence_first_meta": {"ask_path": "v1_evidence"},
        "metadata": {"evidence_quality": "STRONG"},
        "plan_summary": {"steps": steps, "notes": []},
        "context_bundle": {
            "files": [
                {
                    "path": "motadata/src/main/java/com/mindarray/aiops/MailConfigDomainService.java",
                    "selection_reason": "owner",
                }
            ]
        },
    }


def test_run_scenario_row_rejects_forbidden_generic_scan_phrase(monkeypatch) -> None:
    scenario = {
        "id": "ask_mail_config_domain",
        "capability": "ask",
        "query": "Where is mail domain config implemented?",
        "forbid_generic_scan_answer": True,
        "expect": {
            "governance_posture": "PLAN_ONLY",
            "execution": False,
            "ask_path": "v1_evidence",
            "min_plan_steps": 1,
        },
    }
    evidence = _evidence_bundle()
    ask_resp = _ask_resp_with_steps(
        ["Open MailConfigDomainService.java and scan for logic related to domain handling."]
    )

    def _fake_post(url: str, payload: dict, timeout: int = 180, *, raise_for_status: bool = True):
        if url.endswith("/v1/export_evidence"):
            return 200, evidence
        if url.endswith("/v1/ask"):
            return 200, ask_resp
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(verify, "_post", _fake_post)
    out = verify._run_scenario_row(
        scenario,
        workspace_root="/tmp/ws",
        context_url="http://context",
        plan_gate_url="http://plan",
        top_k=8,
    )
    assert out["pass"] is False
    assert any("forbid_generic_scan_answer" in e for e in out["errors"])


def test_run_scenario_row_requires_concrete_anchor(monkeypatch) -> None:
    scenario = {
        "id": "ask_config_store_organization",
        "capability": "ask",
        "query": "Where is config store organization implemented?",
        "must_cite_file_or_symbol_anchor": True,
        "expect": {
            "governance_posture": "PLAN_ONLY",
            "execution": False,
            "ask_path": "v1_evidence",
            "min_plan_steps": 1,
        },
    }
    evidence = _evidence_bundle("motadata/src/main/java/com/mindarray/config/ConfigStoreOrganization.java")
    ask_resp = _ask_resp_with_steps(
        ["The implementation is spread across multiple layers and should be reviewed carefully."]
    )

    def _fake_post(url: str, payload: dict, timeout: int = 180, *, raise_for_status: bool = True):
        if url.endswith("/v1/export_evidence"):
            return 200, evidence
        if url.endswith("/v1/ask"):
            return 200, ask_resp
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(verify, "_post", _fake_post)
    out = verify._run_scenario_row(
        scenario,
        workspace_root="/tmp/ws",
        context_url="http://context",
        plan_gate_url="http://plan",
        top_k=8,
    )
    assert out["pass"] is False
    assert any("must_cite_file_or_symbol_anchor" in e for e in out["errors"])


def test_classify_graph_preflight_state_thresholds() -> None:
    assert (
        verify._classify_graph_preflight_state(
            {
                "VERTICLE_REGISTRATION": 6,
                "EVENTBUS_CONSUMER_REGISTRATION": 11,
                "API_ROUTE_REGISTRATION": 2,
            }
        )
        == "COMPLETE"
    )
    assert (
        verify._classify_graph_preflight_state(
            {
                "VERTICLE_REGISTRATION": 5,
                "EVENTBUS_CONSUMER_REGISTRATION": 11,
                "API_ROUTE_REGISTRATION": 2,
            }
        )
        == "INCOMPLETE"
    )


def test_run_scenario_suite_skips_requires_graph_path_when_incomplete(tmp_path: Path, monkeypatch) -> None:
    scenario_file = tmp_path / "scenarios.json"
    scenario_file.write_text(
        json.dumps(
            {
                "schema_version": "motadata_aiops_behavior_scenarios.v1",
                "defaults": {"top_k": 8},
                "scenarios": [
                    {"id": "g1", "capability": "ask", "query": "q1", "requires_graph_path": True, "expect": {}},
                    {"id": "g2", "capability": "ask", "query": "q2", "expect": {}},
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        verify,
        "_graph_preflight",
        lambda: {
            "state": "INCOMPLETE",
            "reason": "below threshold",
            "anchor_counts": {"VERTICLE_REGISTRATION": 1, "EVENTBUS_CONSUMER_REGISTRATION": 1, "API_ROUTE_REGISTRATION": 0},
            "thresholds": dict(verify._GRAPH_PREFLIGHT_THRESHOLDS),
        },
    )
    called: list[str] = []

    def _fake_run_row(*args, **kwargs):
        scenario = args[0]
        called.append(str(scenario.get("id")))
        return {
            "id": scenario.get("id"),
            "capability": scenario.get("capability"),
            "pass": True,
            "errors": [],
            "expect": scenario.get("expect") or {},
            "actual_summary": {"ok": True},
        }

    monkeypatch.setattr(verify, "_run_scenario_row", _fake_run_row)
    out = verify.run_scenario_suite(
        scenario_file,
        workspace_root="/tmp/ws",
        context_url="http://context",
        plan_gate_url="http://plan",
        top_k=8,
    )
    assert out["graph_preflight"]["state"] == "INCOMPLETE"
    assert out["all_pass"] is True
    assert called == ["g2"]
    skipped = next(r for r in out["results"] if r["id"] == "g1")
    assert skipped["skipped"] is True
    assert "requires_graph_path skipped" in skipped["skip_reason"]


def test_run_scenario_suite_fails_fast_on_graph_unreachable(tmp_path: Path, monkeypatch) -> None:
    scenario_file = tmp_path / "scenarios.json"
    scenario_file.write_text(
        json.dumps(
            {
                "schema_version": "motadata_aiops_behavior_scenarios.v1",
                "defaults": {"top_k": 8},
                "scenarios": [{"id": "g1", "capability": "ask", "query": "q1", "requires_graph_path": True, "expect": {}}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        verify,
        "_graph_preflight",
        lambda: {"state": "UNREACHABLE", "reason": "neo4j python driver is not installed", "anchor_counts": {}, "thresholds": {}},
    )
    out = verify.run_scenario_suite(
        scenario_file,
        workspace_root="/tmp/ws",
        context_url="http://context",
        plan_gate_url="http://plan",
        top_k=8,
    )
    assert out["all_pass"] is False
    assert out["results"] == []
    assert out["graph_preflight"]["state"] == "UNREACHABLE"


def test_run_scenario_row_plan_supports_decision_any_of(monkeypatch) -> None:
    scenario = {
        "id": "plan_decision_any",
        "capability": "plan",
        "expect": {
            "schema_version": "decision_response.v0.1",
            "decision_present": True,
            "decision_any_of": ["REFUSAL", "APPROVAL"],
        },
    }

    def _fake_post(url: str, payload: dict, timeout: int = 180, *, raise_for_status: bool = True):
        assert url.endswith("/v0/plan")
        return 200, {"schema_version": "decision_response.v0.1", "decision": "REFUSAL"}

    monkeypatch.setattr(verify, "_post", _fake_post)
    out = verify._run_scenario_row(
        scenario,
        workspace_root="/tmp/ws",
        context_url="http://context",
        plan_gate_url="http://plan",
        top_k=8,
    )
    assert out["pass"] is True
    assert out["actual_summary"]["decision_present"] is True


def test_run_scenario_row_code_supports_outcome_any_of(monkeypatch) -> None:
    scenario = {
        "id": "code_outcome_any",
        "capability": "code",
        "command": "echo hello",
        "expect": {
            "schema_version": "execute_response.v0.1",
            "outcome_any_of": ["EXECUTED", "BLOCKED"],
            "executed_any_of": [True, False],
        },
    }

    def _fake_post(url: str, payload: dict, timeout: int = 180, *, raise_for_status: bool = True):
        assert url.endswith("/v0/execute")
        return 200, {
            "schema_version": "execute_response.v0.1",
            "outcome": "BLOCKED",
            "executed": False,
            "posture": "PLAN_ONLY",
        }

    monkeypatch.setattr(verify, "_post", _fake_post)
    out = verify._run_scenario_row(
        scenario,
        workspace_root="/tmp/ws",
        context_url="http://context",
        plan_gate_url="http://plan",
        top_k=8,
    )
    assert out["pass"] is True
    assert out["actual_summary"]["command"] == "echo hello"


def test_check_expect_debug_method_body_uses_grounding_tier() -> None:
    expect = {"require_selected_method_body_present": True}
    evidence = {
        "fusion_diagnostics": {
            "selected_method_hints": ["beforeUpdate", "afterUpdate"],
            "selected_method_body_present": True,
            "selected_method_grounding_tier": "partial",
            "selected_method_body_missing_reason": "selected_file_snippet_partial_non_executable",
        }
    }
    errs = verify._check_expect_debug_method_body(expect, evidence)
    assert errs
    assert "grounding tier is not executable" in errs[0]


def test_check_method_body_answer_alignment_flags_absence_phrases_for_executable() -> None:
    expect = {
        "require_selected_method_body_present": True,
        "require_method_body_answer_alignment": True,
    }
    evidence = {
        "fusion_diagnostics": {
            "selected_method_hints": ["parse", "dispatch"],
            "selected_method_body_present": True,
            "selected_method_grounding_tier": "executable",
        }
    }
    explain = {
        "summary": "The selected file lacks specific details and no direct reference was found.",
        "logic_flow": "Cannot trace concrete method behavior from this context.",
        "likely_bug_risk": "",
        "confidence_limits": "",
        "evidence": [],
    }
    errs = verify._check_method_body_answer_alignment(expect, evidence, explain)
    assert errs
    assert "contradicts fusion selected_method_grounding_tier" in errs[0]


def test_check_method_body_answer_alignment_flags_overclaim_for_declarative() -> None:
    expect = {
        "require_selected_method_body_present": True,
        "require_method_body_answer_alignment": True,
    }
    evidence = {
        "fusion_diagnostics": {
            "selected_method_hints": ["beforeUpdate"],
            "selected_method_body_present": False,
            "selected_method_grounding_tier": "declarative",
        }
    }
    explain = {
        "summary": "The method does X and this branch executes before persistence.",
        "logic_flow": "The code returns null in this branch.",
        "likely_bug_risk": "",
        "confidence_limits": "",
        "evidence": [],
    }
    errs = verify._check_method_body_answer_alignment(expect, evidence, explain)
    assert errs
    assert "overclaims method-level certainty" in errs[0]

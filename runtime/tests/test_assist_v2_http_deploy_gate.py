from __future__ import annotations

from runtime.scripts import assist_v2_http_deploy_gate as gate


def _grounded_response() -> dict:
    return {
        "governance_posture": "PLAN_ONLY",
        "execution": False,
        "evidence_first_meta": {"ask_path": "v1_evidence"},
        "assist_layer": {
            "assist_v2": {
                "route_decision": {"mode": "ask"},
                "answer": {},
                "evidence": {},
                "gaps": {},
                "next_steps": {},
                "investigate": {
                    "available": True,
                    "target": {
                        "file": "src/main/java/com/mindarray/integration/ServiceNowIntegration.java",
                        "method": "synchronizeIncident",
                    },
                },
            }
        },
    }


def _weak_response() -> dict:
    return {
        "execution": False,
        "evidence_first_meta": {"ask_path": "v1_evidence"},
        "assist_layer": {"assist_v2": {"route_decision": {"mode": "ask"}}},
    }


def _debug_missing_file_response() -> dict:
    return {
        "execution": False,
        "explain_debug": {"summary": "missing"},
        "assist_layer": {
            "assist_v2": {
                "route_decision": {"mode": "debug"},
                "debug_v2": {
                    "evidence": {"grounding_tier": "none"},
                    "confidence_limits": {"not_visible": ["missing selected file"]},
                },
            }
        },
    }


def test_run_gate_passes_with_complete_graph(monkeypatch):
    responses = iter([_grounded_response(), _weak_response(), _debug_missing_file_response()])

    def _fake_post_json(*_args, **_kwargs):
        return next(responses)

    monkeypatch.setattr(gate, "_post_json", _fake_post_json)
    monkeypatch.setattr(
        gate,
        "_graph_preflight",
        lambda: {
            "state": "COMPLETE",
            "reason": "ok",
            "anchor_counts": {"VERTICLE_REGISTRATION": 6, "EVENTBUS_CONSUMER_REGISTRATION": 11, "API_ROUTE_REGISTRATION": 2},
            "thresholds": {"VERTICLE_REGISTRATION": 5, "EVENTBUS_CONSUMER_REGISTRATION": 10, "API_ROUTE_REGISTRATION": 1},
        },
    )

    result = gate.run_gate(plan_gate_url="http://127.0.0.1:8089", timeout_s=5, require_graph_preflight=True)
    assert result["all_pass"] is True
    assert result["checks"]["grounded_ask_shape"]["pass"] is True
    assert result["checks"]["weak_ask_investigate_omission"]["pass"] is True
    assert result["checks"]["debug_shape_and_fail_closed"]["pass"] is True
    assert result["checks"]["graph_preflight_healthy"]["pass"] is True


def test_run_gate_fails_when_graph_preflight_required_and_unhealthy(monkeypatch):
    responses = iter([_grounded_response(), _weak_response(), _debug_missing_file_response()])
    monkeypatch.setattr(gate, "_post_json", lambda *_args, **_kwargs: next(responses))
    monkeypatch.setattr(
        gate,
        "_graph_preflight",
        lambda: {"state": "UNREACHABLE", "reason": "neo4j python driver is not installed", "anchor_counts": {}, "thresholds": {}},
    )

    result = gate.run_gate(plan_gate_url="http://127.0.0.1:8089", timeout_s=5, require_graph_preflight=True)
    assert result["all_pass"] is False
    assert result["checks"]["graph_preflight_healthy"]["pass"] is False
    assert result["checks"]["graph_preflight_healthy"]["required"] is True


def test_run_gate_allows_graph_preflight_bypass(monkeypatch):
    responses = iter([_grounded_response(), _weak_response(), _debug_missing_file_response()])
    monkeypatch.setattr(gate, "_post_json", lambda *_args, **_kwargs: next(responses))
    monkeypatch.setattr(
        gate,
        "_graph_preflight",
        lambda: {"state": "UNREACHABLE", "reason": "neo4j python driver is not installed", "anchor_counts": {}, "thresholds": {}},
    )

    result = gate.run_gate(plan_gate_url="http://127.0.0.1:8089", timeout_s=5, require_graph_preflight=False)
    assert result["all_pass"] is True
    assert result["checks"]["graph_preflight_healthy"]["pass"] is True
    assert result["checks"]["graph_preflight_healthy"]["required"] is False

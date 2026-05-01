from __future__ import annotations

from runtime.ask_service.reasoning_synthesis import (
    build_reasoning_synthesis,
    compute_shadow_rubric,
    legacy_answer_method_collapse_hint,
    validate_reasoning_synthesis,
)


def test_validate_reasoning_synthesis_accepts_build_output():
    rc = {
        "schema_version": "reasoning_context.d1",
        "anchor_method": "MailServerConfiguration.beforeUpdate",
        "typed_nodes": {
            "entrypoints": [
                {"class": "APIServer", "method": "start", "path": "", "citation": "E1", "role": ""}
            ],
            "handlers": [
                {
                    "class": "MailServerConfiguration",
                    "method": "beforeUpdate",
                    "path": "",
                    "citation": "E2",
                    "role": "",
                }
            ],
            "abstractions": [],
            "stores": [],
            "collaborators": [],
        },
        "coverage_gaps": [],
        "top_graph_paths": [],
        "api_route_mapping": {},
        "eventbus_context": {},
        "evidence_sources": [],
        "primary_owner": {"class": "MailServerConfiguration", "method": "beforeUpdate"},
        "inheritance": {"chain": []},
        "flow_steps": [],
        "collaborators": [],
    }
    syn = build_reasoning_synthesis(query="How does mail work?", reasoning_context=rc, task_type="general")
    assert not validate_reasoning_synthesis(syn)
    assert syn["schema_version"] == "reasoning_synthesis.v1"
    assert syn["subsystem"]["label"] == "mail_configuration"
    assert syn["method_collapse_risk"]["detected"] is False


def test_legacy_method_collapse_hint():
    assert legacy_answer_method_collapse_hint(
        "The strongest grounded component is `Foo.bar` when evidence is thin."
    )
    assert not legacy_answer_method_collapse_hint("HTTP/API behavior in this snapshot spans ingress.")


def test_shadow_rubric():
    syn = build_reasoning_synthesis(
        query="Architecture",
        reasoning_context={
            "schema_version": "reasoning_context.d1",
            "anchor_method": "APIServer.start",
            "typed_nodes": {
                "entrypoints": [],
                "handlers": [],
                "abstractions": [],
                "stores": [],
                "collaborators": [],
            },
            "coverage_gaps": [],
            "top_graph_paths": [],
            "api_route_mapping": {
                "schema_version": "api_route_handler_mapping.v1",
                "routes": [{"path": "/x", "handler_or_subrouter": "y"}],
            },
            "eventbus_context": {},
            "evidence_sources": [],
            "primary_owner": {},
            "inheritance": {"chain": []},
            "flow_steps": [],
            "collaborators": [],
        },
        task_type="general",
    )
    r = compute_shadow_rubric(
        legacy_answer_text=(
            "Intro paragraph with enough words to satisfy minimal fluency heuristics here."
        ),
        synthesis=syn,
        evidence_quality="STRONG",
    )
    assert "depth_score" in r and "method_collapse_detected" in r

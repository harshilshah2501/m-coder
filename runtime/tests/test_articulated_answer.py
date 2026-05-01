from __future__ import annotations

import os

from runtime.ask_service.articulated_answer import build_articulated_answer


def _meta_rc(owner_cls: str, owner_method: str, gaps: list[str] | None = None) -> dict:
    return {
        "evidence_quality": "STRONG",
        "reasoning_context": {
            "schema_version": "reasoning_context.d1",
            "primary_owner": {
                "class": owner_cls,
                "method": owner_method,
                "file": f"src/{owner_cls}.java",
                "citation": "E1",
                "role_description": f"entrypoint / bootstrap ({owner_cls}.{owner_method})",
            },
            "anchor_method": f"{owner_cls}.{owner_method}",
            "typed_nodes": {
                "entrypoints": [{"class": owner_cls, "method": owner_method}],
                "abstractions": [{"class": "AbstractAPI", "method": ""}],
                "handlers": [{"class": "AlarmAPI", "method": "beforeUpdate"}],
                "stores": [{"class": "ObjectConfigStore", "method": "getItem"}],
                "collaborators": [{"class": "DiscoveryEngine", "method": "start"}],
            },
            "flow_steps": [f"{owner_cls}.{owner_method}", "AbstractAPI.routeRequest", "AlarmAPI.beforeUpdate"],
            "coverage_gaps": gaps or [],
        },
    }


def _api_route_mapping() -> dict:
    return {
        "schema_version": "api_route_handler_mapping.v1",
        "apiserver_entrypoints": [
            {"class": "APIServer", "method": "start", "file": "src/main/java/com/mindarray/api/APIServer.java"}
        ],
        "routes": [
            {"path": "/api/v1/*", "handler_or_subrouter": "subRouter(apiRouter)"},
            {"path": "/settings/*,/system/*,/query/*", "handler_or_subrouter": "subRouter(...)"},
        ],
        "api_classes": [
            {"class": "MailServerConfiguration", "extends": "AbstractAPI"},
            {"class": "User", "extends": "AbstractAPI"},
            {"class": "TraceService", "extends": "AbstractAPI"},
        ],
        "lifecycle_hooks": [
            {"class": "AbstractAPI", "hook": "beforeUpdate"},
            {"class": "MailServerConfiguration", "hook": "beforeUpdate"},
        ],
        "eventbus_handoffs": [{"class": "APIServer", "type": "send", "address": "EVENT_AUDIT"}],
        "unknowns": [{"topic": "Exact per-endpoint overrides", "reason": "Needs class-by-class extraction"}],
    }


def test_articulated_answer_unified_contract_default():
    # Non-routine gap → one bounded-confidence sentence (custom gap, not snapshot boilerplate).
    out = build_articulated_answer(
        query="Explain the API layer architecture.",
        plan_steps=["Primary implementation owner: `APIServer` in `src/APIServer.java`, method `start`."],
        context_files=[{"path": "src/APIServer.java", "selection_reason": "rank"}],
        graph_traversal=None,
        metadata=_meta_rc("APIServer", "start", gaps=["Flow not fully proven"]),
    )
    assert out is not None
    assert out.get("schema_version") == "articulated_answer.v0"
    text = "\n".join(out.get("paragraphs") or [])
    assert "APIServer" in text
    assert "AbstractAPI" in text
    assert "AlarmAPI" in text or "ObjectConfigStore" in text
    assert "not fully visible in this snapshot" in text.lower()
    assert "graph" not in text.lower()
    assert "receives or initiates" not in text.lower()
    assert "flow evidence" not in text.lower()


def test_strong_routine_gaps_skip_forensic_disclaimer():
    """Production reasoning_context often only adds routine snapshot gaps; prose stays direct."""
    routine = [
        "Full request routing not resolved in current evidence.",
        "No graph call-paths available; flow is inferred from class names only.",
    ]
    out = build_articulated_answer(
        query="Explain the API layer architecture.",
        plan_steps=["Primary implementation owner: `APIServer` in `src/APIServer.java`, method `start`."],
        context_files=[{"path": "src/APIServer.java", "selection_reason": "rank"}],
        graph_traversal=None,
        metadata=_meta_rc("APIServer", "start", gaps=routine),
    )
    assert out is not None
    text = "\n".join(out.get("paragraphs") or [])
    assert "not fully visible in this snapshot" not in text.lower()
    assert "not fully proven" not in text.lower()
    assert "graph path" not in text.lower()


def test_articulated_answer_returns_none_when_empty():
    assert (
        build_articulated_answer(
            query="noop",
            plan_steps=[],
            context_files=[],
            graph_traversal=None,
            metadata={},
        )
        is None
    )


def test_articulated_answer_hard_guard_when_components_insufficient():
    meta = {
        "evidence_quality": "STRONG",
        "reasoning_context": {
            "schema_version": "reasoning_context.d1",
            "primary_owner": {"class": "APIServer", "method": "start", "file": "src/APIServer.java", "citation": "E1"},
            "anchor_method": "APIServer.start",
            "typed_nodes": {"entrypoints": [], "abstractions": [], "handlers": [], "stores": [], "collaborators": []},
            "flow_steps": [],
            "coverage_gaps": ["Flow unresolved"],
        },
    }
    out = build_articulated_answer(
        query="Explain the API layer architecture.",
        plan_steps=["Primary implementation owner: `APIServer` in `src/APIServer.java`, method `start`."],
        context_files=[],
        graph_traversal=None,
        metadata=meta,
    )
    assert out is not None
    text = "\n".join(out.get("paragraphs") or [])
    assert "strongest grounded component" in text.lower()
    assert "not fully visible in this snapshot" in text.lower()


def test_articulated_answer_legacy_renderer_flag(monkeypatch):
    monkeypatch.setenv("MCODER_LEGACY_ASK_RENDERER", "1")
    out = build_articulated_answer(
        query="How are config stores organized?",
        plan_steps=[
            "Primary implementation owner: `AbstractConfigStore` in `src/store/AbstractConfigStore.java`, method `getItem`.",
            "How it works (grounded): `AbstractConfigStore`.`getItem` drives store lookups.",
        ],
        context_files=[{"path": "src/store/AbstractConfigStore.java", "selection_reason": "rank"}],
        graph_traversal=None,
        metadata={"evidence_quality": "STRONG"},
    )
    assert out is not None
    assert out.get("shape") != "unified_contract"
    monkeypatch.delenv("MCODER_LEGACY_ASK_RENDERER", raising=False)


def test_unified_contract_handles_mail_notification_config_and_ambiguous_queries():
    # Align with typical reasoning_context: routine snapshot gaps only → no closing disclaimer.
    routine_only = [
        "Persistence/store call chain not resolved.",
        "No graph call-paths available; flow is inferred from class names only.",
    ]
    cases = [
        ("How does mail server configuration work?", _meta_rc("MailServerConfiguration", "beforeUpdate", gaps=routine_only)),
        ("Find all classes that handle notifications.", _meta_rc("NotificationEngine", "start", gaps=routine_only)),
        ("How are config stores organized?", _meta_rc("AbstractConfigStore", "getItem", gaps=routine_only)),
        ("How are APIs structured internally?", _meta_rc("APIServer", "start", gaps=routine_only)),
    ]
    for query, meta in cases:
        out = build_articulated_answer(
            query=query,
            plan_steps=[],
            context_files=[{"path": "src/seed.java", "selection_reason": "rank"}],
            graph_traversal=None,
            metadata=meta,
        )
        assert out is not None
        text = "\n".join(out.get("paragraphs") or [])
        assert "not fully visible in this snapshot" not in text.lower()
        assert "graph" not in text.lower()
        assert "partial graph" not in text.lower()


def test_notification_discovery_with_email_sms_uses_notification_template():
    meta = _meta_rc("NotificationEngine", "start", gaps=[])
    meta["reasoning_context"]["eventbus_context"] = {
        "addresses": [{"address": "notification.dispatch"}],
        "producers": [{"address": "notification.dispatch", "class": "NotificationEngine", "method": "start"}],
        "consumers": [{"address": "notification.dispatch", "class": "EmailNotification", "method": "deliver"}],
        "unknowns": [],
        "confidence": {"confidence_distribution": {"bounded": 2}},
    }
    out = build_articulated_answer(
        query="List main classes involved in sending email or SMS notifications from the server.",
        plan_steps=[],
        context_files=[{"path": "src/NotificationEngine.java", "selection_reason": "rank"}],
        graph_traversal=None,
        metadata=meta,
    )
    assert out is not None
    text = "\n".join(out.get("paragraphs") or [])
    assert "Notification flow is coordinated by" in text
    assert "publishes `notification.dispatch`" in text
    assert "consumes `notification.dispatch`" in text
    assert "Mail server configuration is anchored" not in text


def test_event_query_uses_eventbus_roles_without_fake_chain():
    meta = _meta_rc("NotificationEngine", "start", gaps=[])
    meta["reasoning_context"]["eventbus_context"] = {
        "addresses": [{"address": "event.notification"}],
        "producers": [{"address": "event.notification", "class": "NotificationEngine", "method": "start"}],
        "consumers": [{"address": "event.notification", "class": "SMSNotification", "method": "deliver"}],
        "unknowns": [],
        "confidence": {},
    }
    out = build_articulated_answer(
        query="Which event triggers notification dispatch and who consumes it?",
        plan_steps=[],
        context_files=[{"path": "src/NotificationEngine.java"}],
        graph_traversal=None,
        metadata=meta,
    )
    assert out is not None
    text = "\n".join(out.get("paragraphs") or [])
    assert "publishes `event.notification`" in text
    assert "consumes `event.notification`" in text
    assert "->" not in text


def test_publish_consume_query_prioritizes_eventbus_roles():
    meta = _meta_rc("NotificationEngine", "start", gaps=[])
    meta["reasoning_context"]["eventbus_context"] = {
        "addresses": [{"address": "notification.event"}],
        "producers": [{"address": "notification.event", "class": "NotificationEngine", "method": "start"}],
        "consumers": [{"address": "notification.event", "class": "EmailNotification", "method": "deliver"}],
        "unknowns": [],
        "confidence": {},
    }
    out = build_articulated_answer(
        query="Which components publish or consume notification events?",
        plan_steps=[],
        context_files=[{"path": "src/NotificationEngine.java"}],
        graph_traversal=None,
        metadata=meta,
    )
    assert out is not None
    text = "\n".join(out.get("paragraphs") or [])
    assert "`NotificationEngine.start` publishes `notification.event`." in text
    assert "`EmailNotification.deliver` consumes `notification.event`." in text


def test_structural_api_base_without_chain_does_not_fall_back_to_generic_api_template():
    meta = {
        "evidence_quality": "WEAK",
        "reasoning_context": {
            "schema_version": "reasoning_context.d1",
            "primary_owner": {"class": "", "method": "", "file": ""},
            "anchor_method": "",
            "inheritance": {"chain": [], "citation": ""},
            "typed_nodes": {"entrypoints": [], "abstractions": [], "handlers": [], "stores": [], "collaborators": []},
            "coverage_gaps": ["No graph call-paths available; flow is inferred from class names only."],
        },
    }
    out = build_articulated_answer(
        query="Which class is the base class for concrete REST APIs in this codebase?",
        plan_steps=[],
        context_files=[{"path": "src/APIServer.java", "selection_reason": "rank"}],
        graph_traversal=None,
        metadata=meta,
    )
    assert out is not None
    text = "\n".join(out.get("paragraphs") or [])
    assert "Could not resolve a grounded inheritance chain" in text
    assert "The API layer starts at" not in text


def test_structural_api_base_uses_route_mapping_extends_abstractapi():
    meta = {
        "evidence_quality": "WEAK",
        "reasoning_context": {
            "schema_version": "reasoning_context.d1",
            "primary_owner": {"class": "APIServer", "method": "start", "file": "src/APIServer.java"},
            "anchor_method": "APIServer.start",
            "inheritance": {"chain": ["APIServer", "AbstractVerticle"], "citation": "G1"},
            "typed_nodes": {"entrypoints": [], "abstractions": [], "handlers": [], "stores": [], "collaborators": []},
            "coverage_gaps": ["No graph call-paths available; flow is inferred from class names only."],
            "api_route_mapping": _api_route_mapping(),
        },
    }
    out = build_articulated_answer(
        query="Which class is the base class for concrete REST APIs in this codebase?",
        plan_steps=[],
        context_files=[{"path": "src/APIServer.java", "selection_reason": "rank"}],
        graph_traversal=None,
        metadata=meta,
    )
    assert out is not None
    text = "\n".join(out.get("paragraphs") or [])
    assert "AbstractAPI" in text
    assert "Could not resolve a grounded inheritance chain" not in text


def test_api_base_class_prefers_abstract_api_over_verticle_chain():
    """Graph often reports APIServer → AbstractVerticle; REST handlers still extend AbstractAPI."""
    meta = {
        "evidence_quality": "STRONG",
        "reasoning_context": {
            "schema_version": "reasoning_context.d1",
            "primary_owner": {"class": "APIServer", "method": "start", "file": "src/APIServer.java"},
            "anchor_method": "APIServer.start",
            "inheritance": {"chain": ["APIServer", "AbstractVerticle"], "citation": "G1"},
            "typed_nodes": {
                "entrypoints": [{"class": "APIServer", "method": "start"}],
                "abstractions": [{"class": "AbstractAPI", "method": ""}],
                "handlers": [{"class": "AlarmAPI", "method": "beforeUpdate"}],
                "stores": [],
                "collaborators": [],
            },
            "coverage_gaps": [],
        },
    }
    out = build_articulated_answer(
        query="Which class is the base class for all APIs?",
        plan_steps=[],
        context_files=[{"path": "src/APIServer.java"}],
        graph_traversal=None,
        metadata=meta,
    )
    assert out is not None
    text = "\n".join(out.get("paragraphs") or [])
    assert "AbstractAPI" in text
    assert "AbstractVerticle" in text
    assert "`APIServer` → `AbstractVerticle`" in text or "Verticle" in text
    assert "concrete REST/API handler" in text.lower() or "handler classes" in text.lower()


def test_unified_paragraphs_structural_base_class_uses_inheritance_chain():
    meta = {
        "evidence_quality": "STRONG",
        "reasoning_context": {
            "schema_version": "reasoning_context.d1",
            "primary_owner": {"class": "AlarmAPI", "method": "beforeUpdate", "file": "src/AlarmAPI.java"},
            "anchor_method": "AlarmAPI.beforeUpdate",
            "inheritance": {"chain": ["AlarmAPI", "AbstractAPI"], "citation": "G1"},
            "typed_nodes": {
                "entrypoints": [{"class": "APIServer", "method": "start"}],
                "abstractions": [{"class": "AbstractAPI", "method": ""}],
                "handlers": [{"class": "AlarmAPI", "method": "beforeUpdate"}],
                "stores": [],
                "collaborators": [],
            },
            "coverage_gaps": [],
        },
    }
    out = build_articulated_answer(
        query="Which class is the base class for all APIs?",
        plan_steps=["Primary implementation owner: `AlarmAPI` in `src/AlarmAPI.java`."],
        context_files=[{"path": "src/AlarmAPI.java"}],
        graph_traversal=None,
        metadata=meta,
    )
    assert out is not None
    text = "\n".join(out.get("paragraphs") or [])
    assert "AbstractAPI" in text
    assert "inheritance" in text.lower()
    assert "The API layer starts at" not in text


def test_unified_paragraphs_planning_prefers_plan_steps_not_api_template():
    meta = {
        "evidence_quality": "STRONG",
        "reasoning_context": {
            "schema_version": "reasoning_context.d1",
            "primary_owner": {"class": "FlowProcessor", "method": "process", "file": "src/FlowProcessor.java"},
            "anchor_method": "FlowProcessor.process",
            "typed_nodes": {
                "entrypoints": [{"class": "APIServer", "method": "start"}],
                "abstractions": [{"class": "AbstractAPI", "method": ""}],
                "handlers": [{"class": "FlowProcessor", "method": "process"}],
                "stores": [],
                "collaborators": [{"class": "AvailabilityCorrelationEngine", "method": "run"}],
            },
            "coverage_gaps": [],
        },
    }
    out = build_articulated_answer(
        query="Plan a safe refactor for alert enrichment flow with rollback notes.",
        plan_steps=[
            "Primary implementation owner: `AlertEnrichmentHandler` in `src/AlertEnrichmentHandler.java`.",
            "Step 1: isolate enrichment behind an interface; Step 2: add feature flag; Step 3: document rollback.",
        ],
        context_files=[{"path": "src/AlertEnrichmentHandler.java"}],
        graph_traversal=None,
        metadata=meta,
    )
    assert out is not None
    text = "\n".join(out.get("paragraphs") or [])
    assert "phased" in text.lower() or "rollback" in text.lower() or "feature-flag" in text.lower()
    assert "The API layer starts at" not in text


def test_api_entrypoint_explain_query_uses_architecture_template():
    meta = _meta_rc("APIServer", "start", gaps=[])
    meta["reasoning_context"]["api_route_mapping"] = _api_route_mapping()
    out = build_articulated_answer(
        query="Explain how HTTP requests enter the product through APIServer and reach concrete handler classes.",
        plan_steps=[],
        context_files=[{"path": "src/APIServer.java", "selection_reason": "rank"}],
        graph_traversal=None,
        metadata=meta,
    )
    assert out is not None
    text = "\n".join(out.get("paragraphs") or [])
    assert "`APIServer.start` creates the HTTP server and root router" in text
    assert "`/api/v1/*`" in text
    assert "`APIRouter.init`" in text
    assert "`AbstractAPI.init`" in text
    assert "Exact per-endpoint overrides still need class-by-class extraction." in text


def test_http_request_flow_uses_api_route_mapping_and_avoids_fake_chain():
    meta = _meta_rc("APIServer", "start", gaps=[])
    meta["reasoning_context"]["api_route_mapping"] = _api_route_mapping()
    out = build_articulated_answer(
        query="How does HTTP request flow through API routes and handlers?",
        plan_steps=[],
        context_files=[{"path": "src/APIServer.java", "selection_reason": "rank"}],
        graph_traversal=None,
        metadata=meta,
    )
    assert out is not None
    text = "\n".join(out.get("paragraphs") or [])
    assert "`/api/v1/*`" in text
    assert "`AbstractAPI.init` supplies the generic CRUD templates." in text
    assert "ObjectConfigStore" not in text
    assert "DiscoveryEngine" not in text


def _minimal_reasoning_synthesis() -> dict:
    return {
        "schema_version": "reasoning_synthesis.v1",
        "subsystem": {"label": "api_layer", "confidence": "high", "signals": []},
        "control_flow_steps": [
            {"step": "ingress_bootstrap", "support": "t"},
            {"step": "shared_abstraction_or_rest_contract", "support": "t"},
            {"step": "request_handler_or_concrete_api", "support": "t"},
        ],
        "proven_facts": ["Route snapshot lists grouped paths under APIServer bootstrap."],
        "confidence_limits": ["Per-endpoint overrides may require wider excerpts."],
    }


def test_phase_d_synthesis_flag_emits_synthesis_first_shape(monkeypatch):
    monkeypatch.setenv("MCODER_REASONING_SYNTHESIS_V1", "1")
    meta = _meta_rc("APIServer", "start", gaps=["Custom gap for limits paragraph."])
    meta["reasoning_synthesis"] = _minimal_reasoning_synthesis()
    out = build_articulated_answer(
        query="Explain the API layer architecture.",
        plan_steps=["Primary implementation owner: `APIServer`."],
        context_files=[{"path": "src/APIServer.java", "selection_reason": "rank"}],
        graph_traversal=None,
        metadata=meta,
    )
    assert out is not None
    assert out.get("shape") == "synthesis_first_v1"
    text = "\n\n".join(out.get("paragraphs") or [])
    assert "distinct grounded" not in text.lower()
    assert "multi-hop elaboration" not in text.lower()
    assert "HTTP/API surface" in text or "route" in text.lower()


def test_phase_d_synthesis_flag_preserves_structural_base_class_path(monkeypatch):
    monkeypatch.setenv("MCODER_REASONING_SYNTHESIS_V1", "1")
    meta = {
        "evidence_quality": "WEAK",
        "reasoning_synthesis": _minimal_reasoning_synthesis(),
        "reasoning_context": {
            "schema_version": "reasoning_context.d1",
            "primary_owner": {"class": "APIServer", "method": "start", "file": "src/APIServer.java"},
            "anchor_method": "APIServer.start",
            "inheritance": {"chain": ["APIServer", "AbstractVerticle"], "citation": "G1"},
            "typed_nodes": {"entrypoints": [], "abstractions": [], "handlers": [], "stores": [], "collaborators": []},
            "coverage_gaps": ["No graph call-paths available; flow is inferred from class names only."],
            "api_route_mapping": _api_route_mapping(),
        },
    }
    out = build_articulated_answer(
        query="Which class is the base class for concrete REST APIs in this codebase?",
        plan_steps=[],
        context_files=[{"path": "src/APIServer.java", "selection_reason": "rank"}],
        graph_traversal=None,
        metadata=meta,
    )
    assert out is not None
    assert out.get("shape") == "unified_contract"
    assert "AbstractAPI" in "\n".join(out.get("paragraphs") or [])

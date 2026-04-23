from __future__ import annotations

from runtime.assist_layer.assist_contracts import (
    AssistInput,
    AssistStatus,
    ConfidenceEnum,
    SUGGESTION_SOURCES,
)
from runtime.assist_layer.v2_router import (
    AssistV2Mode,
    decide_assist_v2_mode,
    build_assist_v2_response_shell,
    augment_assist_v2_with_response,
)
from runtime.assist_layer.augmenter import apply_deterministic_augmentation
from runtime.assist_layer.observability import build_assist_event, input_hash_sha256
from runtime.assist_layer.service import run_assist_layer_v1
from runtime.plan_gate_service.app import _apply_assist_to_ask_payload


def _base_input(**overrides):
    payload = {
        "request_id": "req-1",
        "trace_id": "trace-1",
        "original_query": "Where is retry logic implemented?",
        "session_id": "s-1",
        "context_meta": {
            "active_file_path": "src/retry.py",
            "evidence_presence_or_count": 1,
            "selector_names_used": ["symbols"],
            "task_type_label": "general",
            "evidence_file_paths_or_ids": ["src/retry.py"],
            "diagnostics_labels": ["none"],
        },
        "task_type_label": "general",
    }
    payload.update(overrides)
    return AssistInput(**payload)


def test_contract_invariant_original_query_preserved():
    assist_input = _base_input(original_query="Where  is retry logic??")
    out, _ = run_assist_layer_v1(assist_input)
    assert out.original_query == "Where  is retry logic??"


def test_no_safe_transform_augmented_equals_original():
    assist_input = _base_input(original_query="Where is retry logic implemented?")
    out, _ = run_assist_layer_v1(assist_input)
    assert out.augmented_query == out.original_query


def test_confidence_is_enum_only():
    assist_input = _base_input(original_query="Where  is retry logic??")
    out, _ = run_assist_layer_v1(assist_input)
    assert out.confidence_enum in (ConfidenceEnum.NONE, ConfidenceEnum.LOW, ConfidenceEnum.MEDIUM)


def test_additive_metadata_shape_from_hook():
    ask_request = {
        "request_id": "r-1",
        "trace_id": "t-1",
        "query": "Where  is retry logic??",
        "task_type": "general",
        "selected_file": "src/retry.py",
        "client_context": {"diagnostics_labels": ["lint"]},
    }
    ask_payload, assist_meta = _apply_assist_to_ask_payload(ask_request, "/v0/ask")
    assert ask_payload["original_query"] == "Where  is retry logic??"
    assert ask_payload["query"] == "Where  is retry logic??"
    assert "assist_status" in assist_meta
    assert "confidence_enum" in assist_meta


def test_allowed_transform_whitespace_normalization():
    res = apply_deterministic_augmentation("Where   is   retry logic implemented?", {})
    assert "normalize_whitespace" in res.transform_codes_applied


def test_allowed_transform_punctuation_normalization():
    res = apply_deterministic_augmentation("Where is retry logic??!!", {})
    assert "normalize_punctuation" in res.transform_codes_applied


def test_allowed_transform_abbreviation_expansion():
    res = apply_deterministic_augmentation("Where is retry cfg?", {})
    assert "expand_static_abbreviation" in res.transform_codes_applied
    assert "config" in res.augmented_query.lower()


def test_allowed_transform_typo_light_unambiguous_only():
    res = apply_deterministic_augmentation("Where is retrive logic?", {})
    assert "normalize_typo_light" in res.transform_codes_applied
    assert "retrieve" in res.augmented_query.lower()


def test_forbidden_transform_cannot_change_task_type(monkeypatch):
    from runtime.assist_layer import augmenter

    monkeypatch.setitem(augmenter._ABBREVIATION_MAP, "where", "why")
    res = apply_deterministic_augmentation("Where is retry logic?", {})
    assert res.blocked_by_policy is True


def test_forbidden_transform_cannot_introduce_symbol_like_tokens():
    res = apply_deterministic_augmentation("Where is retry logic?", {})
    assert "/" not in res.augmented_query
    assert "(" not in res.augmented_query


def test_blocked_by_policy_path_exercised(monkeypatch):
    from runtime.assist_layer import augmenter

    monkeypatch.setitem(augmenter._ABBREVIATION_MAP, "retry", "RootCauseModule")
    res = apply_deterministic_augmentation("Where is retry logic?", {})
    assert res.blocked_by_policy is True


def test_failure_path_invalid_input():
    bad_input = AssistInput(
        request_id="",
        trace_id="",
        original_query="",
        session_id="",
        context_meta={},
        task_type_label="general",
    )
    out, _ = run_assist_layer_v1(bad_input)
    assert out.assist_status == AssistStatus.INPUT_INVALID
    assert out.augmented_query == out.original_query


def test_failure_path_timeout_internal(monkeypatch):
    from runtime.assist_layer import service

    def _raise_timeout(*_args, **_kwargs):
        raise TimeoutError("timeout")

    monkeypatch.setattr(service, "apply_deterministic_augmentation", _raise_timeout)
    out, _ = run_assist_layer_v1(_base_input())
    assert out.assist_status == AssistStatus.TIMEOUT_OR_INTERNAL_ERROR
    assert out.augmented_query == out.original_query


def test_failure_path_empty_context_degraded():
    out, _ = run_assist_layer_v1(_base_input(context_meta={}))
    assert out.assist_status == AssistStatus.DEGRADED_EMPTY_CONTEXT
    assert out.augmented_query == out.original_query


def test_observability_required_fields_and_hash_stability():
    assist_input = _base_input()
    out, _ = run_assist_layer_v1(assist_input)
    event = build_assist_event(assist_input, out, reason_code="test", latency_ms=1.0)
    required = {
        "event_name",
        "timestamp_utc",
        "request_id",
        "trace_id",
        "session_id",
        "assist_version",
        "assist_status",
        "confidence_enum",
        "reason_code",
        "transform_codes_applied",
        "suggestions_source_tags",
        "latency_ms",
        "input_hash",
        "input_hash_scope",
        "canonicalization_version",
        "error_class",
    }
    assert required.issubset(set(event.keys()))
    assert input_hash_sha256("abc\r\n") == input_hash_sha256("abc\n")
    assert event["request_id"] == assist_input.request_id
    assert event["trace_id"] == assist_input.trace_id


def test_suggestion_provenance_only_allowlisted_sources():
    out, _ = run_assist_layer_v1(_base_input(context_meta={"active_file_path": "src/main.py", "evidence_presence_or_count": 0}))
    assert set(out.suggestion_sources).issubset(SUGGESTION_SOURCES)


def test_retrieval_drift_validation_hook_modes():
    # no-op path must force exact retrieval match checks
    out_noop, _ = run_assist_layer_v1(_base_input(original_query="Where is retry logic implemented?"))
    assert out_noop.retrieval_drift_validation.get("mode") == "exact_match_required"

    # transform path can enable bounded drift validation policy downstream
    out_tx, _ = run_assist_layer_v1(_base_input(original_query="Where   is retrive cfg??"))
    assert out_tx.retrieval_drift_validation.get("mode") in {"exact_match_required", "bounded_drift_candidate"}


def test_authority_correction_runtime_query_remains_original_when_augmented_differs():
    ask_request = {
        "request_id": "r-2",
        "trace_id": "t-2",
        "query": "Where   is retrive cfg??",
        "task_type": "general",
        "selected_file": "src/retry.py",
        "client_context": {"diagnostics_labels": ["lint"]},
    }
    ask_payload, assist_meta = _apply_assist_to_ask_payload(ask_request, "/v0/ask")

    assert assist_meta["original_query"] == "Where   is retrive cfg??"
    assert assist_meta["augmented_query"] != assist_meta["original_query"]
    assert ask_payload["query"] == assist_meta["original_query"]
    assert ask_payload["query"] != assist_meta["augmented_query"]


def test_authority_correction_v1_path_keeps_original_query_with_drift_metadata():
    ask_request = {
        "request_id": "r-3",
        "trace_id": "t-3",
        "query": "Where   is retrive cfg??",
        "task_type": "general",
        "evidence_bundle": {"entries": [{"path": "src/retry.py"}]},
    }
    ask_payload, assist_meta = _apply_assist_to_ask_payload(ask_request, "/v1/ask")

    assert ask_payload["query"] == ask_payload["original_query"]
    assert assist_meta["retrieval_drift_validation"]["mode"] in {
        "exact_match_required",
        "bounded_drift_candidate",
    }


def test_assist_v2_router_debug_mode_for_explain_debug():
    decision = decide_assist_v2_mode(
        task_type_label="EXPLAIN_DEBUG",
        selected_file="src/main.py",
        selection_text="return 42",
    )
    assert decision.mode == AssistV2Mode.DEBUG
    assert decision.mode_reason == "task_type_explain_debug"


def test_assist_v2_router_mixed_mode_for_selected_file_without_debug_task():
    decision = decide_assist_v2_mode(
        task_type_label="general",
        selected_file="src/main.py",
        selection_text="",
    )
    assert decision.mode == AssistV2Mode.MIXED
    assert decision.mode_reason == "selected_file_present"


def test_assist_v2_router_default_ask_mode_without_editor_binding():
    decision = decide_assist_v2_mode(
        task_type_label="general",
        selected_file="",
        selection_text="",
    )
    assert decision.mode == AssistV2Mode.ASK
    assert decision.mode_reason == "default_ask_mode"


def test_assist_v2_shape_is_diagnostics_only_and_supports_post_response_hooks():
    decision = decide_assist_v2_mode(
        task_type_label="general",
        selected_file="src/main.py",
        selection_text="line",
    )
    shell = build_assist_v2_response_shell(decision)
    assert shell["schema_version"] == "assist_router.v2.skeleton"
    assert shell["diagnostics_only"] is True
    assert shell["behavior_change_applied"] is False
    assert shell["proof_density_hooks"]["available"] is False

    enriched = augment_assist_v2_with_response(
        skeleton=shell,
        ask_response={
            "metadata": {
                "execution_path_stitched": False,
                "call_site_resolution_state": "unresolved",
                "method_window_visible_rate": 0.66,
            }
        },
    )
    hooks = enriched["proof_density_hooks"]
    assert hooks["available"] is True
    assert hooks["execution_path_stitched"] is False
    assert hooks["call_site_resolution_state"] == "unresolved"
    assert hooks["method_window_visible_rate"] == 0.66
    assert "answer" in enriched
    assert "evidence" in enriched
    assert "gaps" in enriched
    assert "next_steps" in enriched


def test_apply_assist_payload_includes_assist_v2_diagnostics_block():
    ask_request = {
        "request_id": "r-v2",
        "trace_id": "t-v2",
        "query": "Where is retry logic?",
        "task_type": "general",
        "selected_file": "src/retry.py",
        "client_context": {"selection": "def retry()"},
    }
    _, assist_meta = _apply_assist_to_ask_payload(ask_request, "/v0/ask")
    assert "assist_v2" in assist_meta
    route_decision = assist_meta["assist_v2"]["route_decision"]
    assert route_decision["mode"] == "mixed"
    assert assist_meta["assist_v2"]["diagnostics_only"] is True


def test_assist_v2_ask_activation_uses_existing_ask_outputs_only():
    decision = decide_assist_v2_mode(
        task_type_label="general",
        selected_file="src/main/java/com/mindarray/api/APIServer.java",
        selection_text="",
    )
    shell = build_assist_v2_response_shell(decision)
    ask_response = {
        "governance_posture": "PLAN_ONLY",
        "execution": False,
        "evidence_first_meta": {"ask_path": "v1_evidence"},
        "plan_summary": {
            "steps": [
                "Direct answer (grounded): strongest API base-class signal in current evidence is `AbstractAPI`.",
                "Primary implementation owner: `APIServer` in `src/main/java/com/mindarray/api/APIServer.java`, method `start`.",
                "Owner method body is visible, but only a partial first-hop trace could be confirmed from current evidence.",
            ],
            "notes": [],
        },
        "context_bundle": {
            "files": [
                {
                    "path": "motadata/src/main/java/com/mindarray/api/APIServer.java",
                    "selection_reason": "query_token_substring_anchor",
                }
            ]
        },
        "metadata": {
            "execution_path_stitched": False,
            "call_site_resolution_state": "unresolved",
            "method_window_visible_rate": 1.0,
            "explicit_method_body_evidence_present": True,
            "context_budget": {
                "prompt_input_tokens": 500,
                "evidence_file_count": 1,
                "method_snippet_count": 1,
                "snippet_total_bytes": 120,
                "loop_context_bytes": 90,
                "truncation_applied": False,
            },
        },
    }
    enriched = augment_assist_v2_with_response(skeleton=shell, ask_response=ask_response)
    assert "answer" in enriched and enriched["answer"]["direct_grounded_answer"].startswith(
        "Direct answer (grounded):"
    )
    assert enriched["answer"]["primary_owner_or_locus"]["file"] == "src/main/java/com/mindarray/api/APIServer.java"
    assert "evidence" in enriched
    assert enriched["evidence"]["proof_density_summary"]["call_site_resolution_state"] == "unresolved"
    assert enriched["evidence"]["context_budget_telemetry_summary"]["evidence_file_count"] == 1
    assert "gaps" in enriched
    assert enriched["gaps"]["explicit_evidence_limits"]
    assert "next_steps" in enriched
    assert enriched["next_steps"]["bounded_verification_steps"]
    # Underlying ask semantics are unchanged by assist shaping.
    assert ask_response["governance_posture"] == "PLAN_ONLY"
    assert ask_response["execution"] is False
    assert ask_response["evidence_first_meta"]["ask_path"] == "v1_evidence"


def test_assist_v2_ask_activation_skips_debug_shape_changes():
    decision = decide_assist_v2_mode(
        task_type_label="EXPLAIN_DEBUG",
        selected_file="src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java",
        selection_text="trace branch",
    )
    shell = build_assist_v2_response_shell(decision)
    enriched = augment_assist_v2_with_response(
        skeleton=shell,
        ask_response={
            "metadata": {
                "execution_path_stitched": False,
                "call_site_resolution_state": "unresolved",
                "method_window_visible_rate": 1.0,
            }
        },
    )
    assert "answer" not in enriched
    assert "evidence" not in enriched
    assert "gaps" not in enriched
    assert "next_steps" not in enriched
    assert enriched["proof_density_hooks"]["call_site_resolution_state"] == "unresolved"

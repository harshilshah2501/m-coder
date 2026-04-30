from __future__ import annotations

from runtime.mcoder_cli.cli import (
    _api_route_debug_cues_from_reasoning_context,
    _clean_debug_text,
    _eventbus_debug_cues_from_reasoning_context,
    _naturalize_debug_limit,
)


def test_eventbus_debug_cues_reports_mismatch_and_unknown():
    rc = {
        "eventbus_context": {
            "producers": [{"address": "event.a"}],
            "consumers": [{"address": "event.b"}],
            "unknowns": [{"unknown_type": "DYNAMIC_ADDRESS", "raw_token": "EVENT_X + host"}],
        }
    }
    cues = _eventbus_debug_cues_from_reasoning_context(rc)
    assert any("no matched consumer" in c.lower() for c in cues)
    assert any("no matched producer" in c.lower() for c in cues)
    assert any("unresolved/dynamic" in c.lower() for c in cues)


def test_clean_debug_text_removes_internal_governance_tokens():
    raw = "Some summary. (Governance curation: abc) insufficient_for_precise_trace"
    cleaned = _clean_debug_text(raw)
    assert "Governance curation" not in cleaned
    assert "insufficient_for_precise_trace" not in cleaned


def test_naturalize_debug_limit_rewrites_raw_limit():
    text = "insufficient_for_precise_trace Selected highlight is minimal."
    out = _naturalize_debug_limit(text)
    assert "selected snippet is narrow" in out.lower()


def test_api_route_debug_cues_from_mapping():
    rc = {
        "api_route_mapping": {
            "schema_version": "api_route_handler_mapping.v1",
        }
    }
    cues = _api_route_debug_cues_from_reasoning_context(
        "Why route not appearing at runtime in APIServer?", rc
    )
    joined = " ".join(cues)
    assert "APIServer.start" in joined
    assert "/api/v1/*" in joined
    assert "APIRouter.init" in joined
    assert "AbstractAPI.init" in joined


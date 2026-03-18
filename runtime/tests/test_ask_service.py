from __future__ import annotations

import json

from runtime.ask_service.handlers import handle_ask_request


def test_handle_ask_request_execution_false_and_plan_only(tmp_path, monkeypatch):
    # Create a minimal repo with a single file to satisfy ContextEngine.
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "billing").mkdir()
    retry_file = repo_root / "billing" / "retry.py"
    retry_file.write_text("def retry():\n    pass\n", encoding="utf-8")

    ask_request = {
        "schema_version": "ask_request.v0.1",
        "request_id": "req-ask-1",
        "timestamp_utc": "2026-03-10T12:00:00Z",
        "repo_root": str(repo_root),
        "revision": "abc123",
        "query": "Where is retry logic implemented?",
    }

    response = handle_ask_request(ask_request)

    assert response["schema_version"] == "plan_only_response.v0.1"
    assert response["request_id"] == "req-ask-1"
    assert response["governance_posture"] == "PLAN_ONLY"
    assert response["execution"] is False
    assert "context_bundle" in response
    assert "plan_summary" in response
    steps = response["plan_summary"]["steps"]
    assert 3 <= len(steps) <= 6


def test_handle_ask_request_explain_debug_uses_reasoner_and_returns_structured(tmp_path):
    """When task_type is EXPLAIN_DEBUG and selected_file + selection present, response includes explain_debug."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "src").mkdir()
    src_file = repo_root / "src" / "main.py"
    src_file.write_text("def main():\n    return 42\n", encoding="utf-8")

    ask_request = {
        "schema_version": "ask_request.v0.1",
        "request_id": "req-explain-1",
        "timestamp_utc": "2026-03-10T12:00:00Z",
        "repo_root": str(repo_root),
        "revision": "abc123",
        "query": "What does this code do?",
        "task_type": "EXPLAIN_DEBUG",
        "selected_file": "src/main.py",
        "client_context": {"selection": "def main():\n    return 42"},
    }

    response = handle_ask_request(ask_request)

    assert response["schema_version"] == "plan_only_response.v0.1"
    assert response["governance_posture"] == "PLAN_ONLY"
    assert response["execution"] is False
    assert "explain_debug" in response
    explain_debug = response["explain_debug"]
    # Reasoner may succeed (vLLM running) or fail (unavailable); either way we get structured shape
    if "error" in explain_debug:
        assert "Reasoning" in explain_debug["error"] or "unavailable" in explain_debug["error"].lower()
    else:
        assert "summary" in explain_debug or "logic_flow" in explain_debug
    assert "plan_summary" in response
    assert len(response["plan_summary"]["steps"]) >= 1

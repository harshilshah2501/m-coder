from __future__ import annotations

from runtime.ask_service.handlers import handle_ask_request


def test_handle_ask_request_execution_false_and_plan_only(tmp_path):
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


def test_ask_same_repo_same_query_same_bundle(tmp_path):
    """M3.12: same repo + same ask -> same selected bundle (determinism)."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "docs").mkdir()
    (repo_root / "docs" / "context.md").write_text("# Context Engine\n\nHow selection works.", encoding="utf-8")
    (repo_root / "README.md").write_text("Root", encoding="utf-8")

    ask_request = {
        "schema_version": "ask_request.v0.1",
        "request_id": "req-1",
        "timestamp_utc": "2026-03-15T12:00:00Z",
        "repo_root": str(repo_root),
        "revision": "rev1",
        "query": "How does context selection work?",
    }
    r1 = handle_ask_request(ask_request)
    r2 = handle_ask_request(ask_request)
    assert r1["governance_posture"] == "PLAN_ONLY"
    assert r2["execution"] is False
    files1 = [f["path"] for f in r1["context_bundle"]["files"]]
    files2 = [f["path"] for f in r2["context_bundle"]["files"]]
    assert files1 == files2


def test_ask_plan_only_no_execution_coupling(tmp_path):
    """Ask path must not trigger execution; response is always plan_only."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "docs").mkdir()
    (repo_root / "docs" / "x.md").write_text("# X", encoding="utf-8")

    response = handle_ask_request({
        "schema_version": "ask_request.v0.1",
        "request_id": "r",
        "timestamp_utc": "2026-03-15T12:00:00Z",
        "repo_root": str(repo_root),
        "revision": "r",
        "query": "documentation",
    })
    assert response["governance_posture"] == "PLAN_ONLY"
    assert response["execution"] is False

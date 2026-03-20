from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from runtime.ask_service.handlers import handle_ask_request

# Repo root for subprocess cwd (so "runtime" package resolves)
_REPO_ROOT = Path(__file__).resolve().parents[2]


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
    # Repo-aware Ask must surface grounded files when symbol hints match (e.g. "retry" in query).
    files = response["context_bundle"]["files"]
    assert len(files) >= 1, "query mentions 'retry'; repo has retry.py containing retry; files should be non-empty"
    assert any("retry" in f.get("path", "") for f in files)
    assert "symbols" in response["context_bundle"]["selectors_used"]
    assert response["ui"]["severity"] == "info"
    assert "ungrounded" not in response["ui"]["message"].lower()


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


def test_repo_root_fallback_when_request_path_invalid(tmp_path, monkeypatch):
    """When repo_root from client does not exist on server (e.g. Windows path), ASK_DEFAULT_REPO_ROOT is used and context_resolution is returned."""
    default_repo = tmp_path / "default_repo"
    default_repo.mkdir()
    (default_repo / "src").mkdir()
    (default_repo / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")

    monkeypatch.setenv("ASK_DEFAULT_REPO_ROOT", str(default_repo))

    ask_request = {
        "schema_version": "ask_request.v0.1",
        "request_id": "req-fallback-1",
        "timestamp_utc": "2026-03-10T12:00:00Z",
        "repo_root": "C:\\Users\\Someone\\repo",
        "revision": "rev-fallback",
        "query": "What is in this repo?",
    }

    response = handle_ask_request(ask_request)

    assert response["schema_version"] == "plan_only_response.v0.1"
    assert response["governance_posture"] == "PLAN_ONLY"
    assert response["execution"] is False
    assert "context_resolution" in response
    cr = response["context_resolution"]
    assert cr["requested_repo_root"] == "C:\\Users\\Someone\\repo"
    assert cr["effective_repo_root"] == str(default_repo)
    assert cr["fallback_used"] is True
    assert response["context_bundle"]["revision"] == "rev-fallback"
    steps = response["plan_summary"]["steps"]
    assert len(steps) >= 1
    assert len(response["context_bundle"]["files"]) >= 0


def test_ask_no_matching_files_returns_honest_response(tmp_path, monkeypatch):
    """When no selectors find files, response has empty files, empty selectors_used, notes, and warning."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "only.py").write_text("x = 1\n", encoding="utf-8")  # no "nonexistent" token

    ask_request = {
        "schema_version": "ask_request.v0.1",
        "request_id": "req-nofiles-1",
        "timestamp_utc": "2026-03-10T12:00:00Z",
        "repo_root": str(repo_root),
        "revision": "abc123",
        "query": "Where is nonexistent symbol used?",
    }

    response = handle_ask_request(ask_request)

    assert response["schema_version"] == "plan_only_response.v0.1"
    assert response["context_bundle"]["files"] == []
    assert response["context_bundle"]["selectors_used"] == []
    assert "notes" in response["plan_summary"]
    assert any("no grounded" in n.lower() or "ungrounded" in n.lower() for n in response["plan_summary"]["notes"])
    assert response["ui"]["severity"] == "warning"
    assert "ungrounded" in response["ui"]["message"].lower() or "no context" in response["ui"]["message"].lower()


def test_error_response_includes_revision_and_no_fallback(tmp_path, monkeypatch):
    """Error response uses request revision and does not include context_resolution when fallback was not used."""
    monkeypatch.delenv("ASK_DEFAULT_REPO_ROOT", raising=False)

    ask_request = {
        "schema_version": "ask_request.v0.1",
        "request_id": "req-err-1",
        "timestamp_utc": "2026-03-10T12:00:00Z",
        "repo_root": str(tmp_path / "nonexistent"),
        "revision": "my-branch-xyz",
        "query": "Explain this.",
    }

    response = handle_ask_request(ask_request)

    assert response["schema_version"] == "plan_only_response.v0.1"
    assert response["governance_posture"] == "PLAN_ONLY"
    assert response["execution"] is False
    assert response["context_bundle"]["revision"] == "my-branch-xyz"
    assert response["context_bundle"]["files"] == []
    assert response["plan_summary"]["steps"] == []
    assert "context_resolution" not in response


def test_ask_via_plan_gate_http_repo_root_fallback_and_revision(tmp_path):
    """
    Integration: start Plan-Gate HTTP server with ASK_DEFAULT_REPO_ROOT, send Ask with
    Windows-style repo_root, assert context_resolution.fallback_used and context_bundle.revision.
    """
    # Minimal repo so context engine can build a bundle when fallback is used
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "src").mkdir()
    (repo_root / "src" / "main.py").write_text("def main():\n    return 42\n", encoding="utf-8")

    port = random.randint(20000, 49151)
    env = os.environ.copy()
    env["ASK_DEFAULT_REPO_ROOT"] = str(repo_root)
    env["PLAN_GATE_PORT"] = str(port)
    # Do not set MOTADATA_EXPLAIN_VLLM_URL so Plan-Gate does not try to reach vLLM
    env.pop("MOTADATA_EXPLAIN_VLLM_URL", None)

    proc = subprocess.Popen(
        [sys.executable, "-m", "runtime.plan_gate_service.app"],
        cwd=str(_REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        base = f"http://127.0.0.1:{port}"
        for _ in range(50):
            try:
                req = urllib.request.Request(f"{base}/healthz", method="GET")
                with urllib.request.urlopen(req, timeout=1) as r:
                    if r.status == 200:
                        break
            except (urllib.error.URLError, OSError):
                time.sleep(0.1)
        else:
            pytest.fail("Plan-Gate did not become ready")

        ask_body = json.dumps({
            "schema_version": "ask_request.v0.1",
            "request_id": "integration-fallback",
            "timestamp_utc": "2026-03-18T12:00:00Z",
            "repo_root": "C:\\Users\\Someone\\m-coder",
            "revision": "feature-branch-123",
            "query": "What is in this repo?",
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{base}/v0/ask",
            data=ask_body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            assert r.status == 200
            response = json.loads(r.read().decode("utf-8"))

        assert response.get("schema_version") == "plan_only_response.v0.1"
        assert response.get("context_bundle", {}).get("revision") == "feature-branch-123"
        cr = response.get("context_resolution")
        assert cr is not None, "context_resolution should be present when fallback is used"
        assert cr.get("fallback_used") is True
        assert cr.get("requested_repo_root") == "C:\\Users\\Someone\\m-coder"
        assert cr.get("effective_repo_root") == str(repo_root)
    finally:
        proc.terminate()
        proc.wait(timeout=5)

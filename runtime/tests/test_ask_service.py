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
from unittest.mock import patch

import pytest

from runtime.ask_service.handlers import handle_ask_request, validate_ask_request
from runtime.ask_service.reasoner import ExplainDebugResult

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
    assert response.get("routing_mode") == "plan_only"


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
        "trace_id": "trace-explain-test",
    }

    response = handle_ask_request(ask_request)

    assert response["schema_version"] == "plan_only_response.v0.1"
    assert response.get("trace_id") == "trace-explain-test"
    assert response.get("routing_mode") == "explain_debug"
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


def test_handle_ask_request_dirty_buffer_overlay_reaches_reasoner_bundle(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "src").mkdir()
    src_file = repo_root / "src" / "main.py"
    src_file.write_text("def main():\n    return 42\n", encoding="utf-8")

    ask_request = {
        "schema_version": "ask_request.v0.1",
        "request_id": "req-overlay-1",
        "timestamp_utc": "2026-03-10T12:00:00Z",
        "repo_root": str(repo_root),
        "revision": "abc123",
        "query": "Explain highlighted code in main.",
        "task_type": "EXPLAIN_DEBUG",
        "selected_file": "src/main.py",
        "client_context": {
            "selection": "return 99",
            "dirty_buffers": [
                {"path": "src/main.py", "content": "def main():\n    return 99  # DIRTY_OVERLAY_TOKEN\n"}
            ],
        },
    }

    with patch("runtime.ask_service.handlers.explain_debug") as mock_explain:
        mock_explain.return_value = ExplainDebugResult(summary="ok")
        response = handle_ask_request(ask_request)

    assert response.get("routing_mode") == "explain_debug"
    mock_explain.assert_called_once()
    call_kwargs = mock_explain.call_args.kwargs
    bundle = call_kwargs["bundle"]
    item = next((x for x in bundle.items if x.path == "src/main.py"), None)
    assert item is not None
    assert "DIRTY_OVERLAY_TOKEN" in item.content


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


def test_handle_ask_request_evidence_first_returns_layer5_bundle(tmp_path):
    repo_root = tmp_path / "ws"
    repo_root.mkdir()
    (repo_root / "pyproject.toml").write_text("[project]\nname=w\nversion='0'\n", encoding="utf-8")
    (repo_root / "src").mkdir()
    (repo_root / "src" / "app.py").write_text("def hello_unit():\n    return 1\n", encoding="utf-8")

    ask_request = {
        "schema_version": "ask_request.v0.1",
        "request_id": "req-evidence-first-1",
        "timestamp_utc": "2026-03-10T12:00:00Z",
        "repo_root": str(repo_root),
        "revision": "abc",
        "query": "hello",
        "evidence_first": True,
    }
    response = handle_ask_request(ask_request)

    assert response["schema_version"] == "plan_only_response.v0.1"
    eb = response.get("evidence_bundle")
    assert eb is not None, "evidence_first path should attach layer5 bundle"
    assert eb.get("schema_hint") == "layer5.evidence_bundle.v1"
    assert eb.get("provisional") is False
    meta = response.get("evidence_first_meta") or {}
    assert meta.get("used_layer5") is True
    entries = eb.get("entries") or []
    assert len(entries) >= 1


def test_validate_ask_request_rejects_malformed_dirty_buffers():
    data = {
        "schema_version": "ask_request.v0.1",
        "request_id": "req-dirty-invalid",
        "timestamp_utc": "2026-04-18T12:00:00Z",
        "repo_root": "/tmp/repo",
        "revision": "abc123",
        "query": "hello",
        "client_context": {
            "dirty_buffers": [{"path": "src/main.py"}],  # missing required content
        },
    }
    errs = validate_ask_request(data)
    assert errs


def test_validate_ask_request_accepts_valid_dirty_buffers():
    data = {
        "schema_version": "ask_request.v0.1",
        "request_id": "req-dirty-valid",
        "timestamp_utc": "2026-04-18T12:00:00Z",
        "repo_root": "/tmp/repo",
        "revision": "abc123",
        "query": "hello",
        "client_context": {
            "dirty_buffers": [
                {"path": "src/main.py", "content": "def main():\n    return 1\n"},
            ],
        },
    }
    errs = validate_ask_request(data)
    assert not errs


def test_handle_ask_request_dirty_buffer_malformed_entries_are_noted(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "src").mkdir()
    (repo_root / "src" / "main.py").write_text("def main():\n    return 42\n", encoding="utf-8")
    ask_request = {
        "schema_version": "ask_request.v0.1",
        "request_id": "req-dirty-note-v0",
        "timestamp_utc": "2026-04-18T12:00:00Z",
        "repo_root": str(repo_root),
        "revision": "abc123",
        "query": "Explain main",
        "client_context": {
            "dirty_buffers": [{"path": "src/main.py", "bad": "missing content"}],
        },
    }
    resp = handle_ask_request(ask_request)
    dbo = (resp.get("metadata") or {}).get("dirty_buffer_overlay") or {}
    assert dbo.get("payload_present") is True
    assert int(dbo.get("invalid_count") or 0) >= 1
    notes = (resp.get("plan_summary") or {}).get("notes") or []
    assert any("dirty buffer overlay payload contained invalid entries" in str(n).lower() for n in notes)


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


def test_ask_blocked_response_shape_for_no_match(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "logs").mkdir()
    (repo_root / "logs" / "app.log").write_text("error happened", encoding="utf-8")

    response = handle_ask_request(
        {
            "schema_version": "ask_request.v0.1",
            "request_id": "blocked-insufficient",
            "timestamp_utc": "2026-03-15T12:00:00Z",
            "repo_root": str(repo_root),
            "revision": "r1",
            "query": "Where is MissingSymbolFoo() implemented?",
        }
    )
    assert response["execution"] is False
    assert response["plan_summary"]["steps"] == []
    assert "explain_debug" not in response
    md = response.get("metadata") or {}
    assert md.get("evidence_quality") in {"INSUFFICIENT", "NO_MATCH"}
    assert isinstance(md.get("quality_reasons"), list) and len(md["quality_reasons"]) >= 1


def test_ask_weak_includes_caveat_note(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "tests").mkdir()
    (repo_root / "tests" / "engine_test.py").write_text("engine", encoding="utf-8")
    (repo_root / "src").mkdir()
    (repo_root / "src" / "engine.py").write_text("def engine():\n  return 1\n", encoding="utf-8")

    response = handle_ask_request(
        {
            "schema_version": "ask_request.v0.1",
            "request_id": "weak-note",
            "timestamp_utc": "2026-03-15T12:00:00Z",
            "repo_root": str(repo_root),
            "revision": "r2",
            "query": "where implemented engine",
        }
    )
    md = response.get("metadata") or {}
    if md.get("evidence_quality") == "WEAK":
        notes = response.get("plan_summary", {}).get("notes", [])
        assert any("WEAK" in n for n in notes)


def test_ask_context_budget_policy_metadata_present(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "src").mkdir()
    (repo_root / "src" / "main.py").write_text("def main():\n    return 1\n", encoding="utf-8")

    response = handle_ask_request(
        {
            "schema_version": "ask_request.v0.1",
            "request_id": "budget-policy",
            "timestamp_utc": "2026-03-15T12:00:00Z",
            "repo_root": str(repo_root),
            "revision": "r3",
            "query": "how does main work",
        }
    )
    md = response.get("metadata") or {}
    cbp = md.get("context_budget_policy") or {}
    assert cbp.get("policy_version") == "context_budget_policy.v1"
    assert cbp.get("surface") == "ask"
    assert isinstance(cbp.get("warning_thresholds"), dict)
    assert isinstance(cbp.get("hard_caps"), dict)
    assert isinstance(cbp.get("truncation_order"), list)

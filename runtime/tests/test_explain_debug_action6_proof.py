"""
Action 6 — minimal deterministic proof for Explain/Debug trust (v0/v1, grounding, failure, path disclosure).

Does not change product behavior; tests only.
"""

from __future__ import annotations

import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runtime.ask_service.handlers import handle_ask_request
from runtime.ask_service.reasoner import ExplainDebugResult, explain_debug
from runtime.ask_service.v1_ingest import handle_ask_v1_request
from runtime.context.contracts import (
    ContextBundle,
    ContextBundleLimits,
    ContextBundleProvenance,
    ContextItem,
)
from runtime.layer5.retrieval.quality_gate import NO_MATCH, QualityAssessment

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GOLDEN_EVIDENCE_PATH = (
    _REPO_ROOT / "runtime" / "layer5" / "evidence" / "golden" / "evidence_bundle.v1.masked.json"
)


def _load_golden_evidence() -> dict:
    with open(_GOLDEN_EVIDENCE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _minimal_v1_ask(evidence: dict, **overrides) -> dict:
    base = {
        "schema_version": "ask_request.v1.0",
        "request_id": "req-a6-v1",
        "timestamp_utc": "2026-03-21T12:00:00Z",
        "query": "Explain the highlighted code.",
        "evidence_bundle": evidence,
    }
    base.update(overrides)
    return base


def _bundle_two_files() -> ContextBundle:
    """Paths and content are unique for prompt substring assertions."""
    return ContextBundle(
        task_id="t-a6",
        revision="rev-a6",
        created_at_utc="2026-01-01T00:00:00Z",
        items=[
            ContextItem(
                path="alpha/only_here.py",
                content='CONTENT_TOKEN_A = "unique_alpha_token"\n',
                byte_size=40,
                selection_reason="test",
            ),
            ContextItem(
                path="beta/second.py",
                content='CONTENT_TOKEN_B = "unique_beta_token"\n',
                byte_size=39,
                selection_reason="test",
            ),
        ],
        limits=ContextBundleLimits(max_files=2, max_bytes=2000, truncated=False),
        provenance=ContextBundleProvenance(
            root_path="/tmp",
            selectors=["test"],
            requested_files=["alpha/only_here.py", "beta/second.py"],
            symbol_hints=[],
        ),
    )


def _mock_vllm_success_response() -> MagicMock:
    body = {
        "choices": [
            {
                "message": {
                    "content": (
                        '{"summary":"ok","logic_flow":"","likely_bug_risk":"",'
                        '"evidence":[],"confidence_limits":""}'
                    )
                }
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(body).encode("utf-8")
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_resp
    mock_cm.__exit__.return_value = None
    return mock_cm


# --- Prompt grounding (reasoner outbound body) ---


@patch("runtime.ask_service.reasoner.urllib.request.urlopen")
def test_prompt_grounding_chat_payload_contains_only_selection_and_bundle(mock_urlopen: MagicMock) -> None:
    """Outbound vLLM JSON: user message is built only from file, selection, bundle items + query."""
    mock_urlopen.return_value = _mock_vllm_success_response()
    bundle = _bundle_two_files()
    sel_file = "user/selected.py"
    sel_text = "SELECTION_LINE_MARK_123"
    q = "QUESTION_MARK_456"

    explain_debug(q, sel_file, sel_text, bundle, request_id="rid-a6")

    mock_urlopen.assert_called_once()
    req_obj = mock_urlopen.call_args[0][0]
    body = json.loads(req_obj.data.decode("utf-8"))
    prompt = body["messages"][0]["content"]

    assert sel_file in prompt
    assert sel_text in prompt
    assert q in prompt
    assert "alpha/only_here.py" in prompt
    assert "unique_alpha_token" in prompt
    assert "beta/second.py" in prompt
    assert "unique_beta_token" in prompt
    # Must not appear: never placed in bundle, selection, file, or query
    assert "SECRET_NOT_EMBEDDED_ANYWHERE_XYZ999" not in prompt


# --- v0 Explain/Debug ---


@patch("runtime.ask_service.reasoner.urllib.request.urlopen")
def test_v0_explain_debug_success_returns_explain_debug(mock_urlopen: MagicMock, tmp_path: Path) -> None:
    mock_urlopen.return_value = _mock_vllm_success_response()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "src").mkdir()
    (repo_root / "src" / "main.py").write_text("def main():\n    return 42\n", encoding="utf-8")

    response = handle_ask_request(
        {
            "schema_version": "ask_request.v0.1",
            "request_id": "req-a6-v0-ok",
            "timestamp_utc": "2026-03-10T12:00:00Z",
            "repo_root": str(repo_root),
            "revision": "abc123",
            "query": "What does this code do?",
            "task_type": "EXPLAIN_DEBUG",
            "selected_file": "src/main.py",
            "client_context": {"selection": "def main():\n    return 42"},
        }
    )

    ed = response["explain_debug"]
    assert "error" not in ed
    assert "summary" in ed and isinstance(ed.get("summary"), str)
    assert "main.py" in json.dumps(ed).lower() or "main" in json.dumps(ed).lower()
    assert isinstance(ed.get("evidence"), list) and len(ed.get("evidence")) >= 1
    assert response.get("evidence_first_meta") is None


@patch("runtime.ask_service.reasoner.urllib.request.urlopen")
def test_v0_explain_debug_transport_error_explicit_error_no_planner_explanation(mock_urlopen: MagicMock, tmp_path: Path):
    mock_urlopen.side_effect = urllib.error.URLError("refused")

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "src").mkdir()
    (repo_root / "src" / "main.py").write_text("def main():\n    return 42\n", encoding="utf-8")

    response = handle_ask_request(
        {
            "schema_version": "ask_request.v0.1",
            "request_id": "req-a6-v0-err",
            "timestamp_utc": "2026-03-10T12:00:00Z",
            "repo_root": str(repo_root),
            "revision": "abc123",
            "query": "What does this code do?",
            "task_type": "EXPLAIN_DEBUG",
            "selected_file": "src/main.py",
            "client_context": {"selection": "def main():\n    return 42"},
        }
    )

    ed = response["explain_debug"]
    assert "error" in ed
    assert ed["error"]
    assert "summary" not in ed
    steps = response["plan_summary"]["steps"]
    assert steps == ["Reasoning service unavailable; no template steps substituted."]
    # PlanOnlyPlanner would normally emit multiple template steps; ensure we did not substitute.
    assert not any("step" in s.lower() and "repository" in s.lower() for s in steps)


def test_v0_explain_debug_blocked_does_not_invoke_reasoner(tmp_path: Path):
    """Quality gate blocked → early return; explain_debug must not run."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "src").mkdir()
    (repo_root / "src" / "main.py").write_text("def main():\n    return 42\n", encoding="utf-8")

    blocked = QualityAssessment(
        intent_type="CODE_INTENT",
        evidence_quality=NO_MATCH,
        quality_reasons=("NO_RELEVANT_HITS",),
        dominance_metrics={
            "top_k_size": 1.0,
            "core_code_in_top_k_pct": 0.0,
            "code_in_top_k_pct": 0.0,
            "noise_in_top_k_pct": 0.0,
            "core_in_top_3_count": 0.0,
            "max_consecutive_noise": 0.0,
        },
        blocked=True,
        policy_version="quality_gate.v1",
    )

    with patch("runtime.ask_service.handlers.assess_evidence_quality", return_value=blocked):
        with patch("runtime.ask_service.handlers.explain_debug") as mock_ed:
            response = handle_ask_request(
                {
                    "schema_version": "ask_request.v0.1",
                    "request_id": "req-a6-block",
                    "timestamp_utc": "2026-03-10T12:00:00Z",
                    "repo_root": str(repo_root),
                    "revision": "abc123",
                    "query": "What does this code do?",
                    "task_type": "EXPLAIN_DEBUG",
                    "selected_file": "src/main.py",
                    "client_context": {"selection": "def main():\n    return 42"},
                }
            )

    mock_ed.assert_not_called()
    assert "explain_debug" not in response
    assert response["plan_summary"]["steps"] == []


# --- v1 Explain/Debug ---


@patch("runtime.ask_service.v1_ingest.explain_debug")
def test_v1_explain_debug_invokes_reasoner(mock_ed: MagicMock):
    mock_ed.return_value = ExplainDebugResult(summary="v1_ok")
    ev = _load_golden_evidence()
    # Query must pass quality gate (same family as test_handle_ask_v1_happy_path).
    req = _minimal_v1_ask(
        ev,
        query="Explain the highlighted code.",
        selected_file="module/sample.py",
        task_type="EXPLAIN_DEBUG",
        client_context={"selection": "def hello_unit():\n    return \"hello\"\n"},
    )
    resp = handle_ask_v1_request(req)

    mock_ed.assert_called_once()
    assert resp.get("explain_debug", {}).get("summary") == "v1_ok"
    meta = resp.get("evidence_first_meta") or {}
    assert meta.get("ask_path") == "v1_evidence"
    assert meta.get("no_context_engine") is True
    cr = resp.get("context_resolution") or {}
    assert cr.get("no_repo_filesystem") is True


@patch("runtime.ask_service.reasoner.urllib.request.urlopen")
def test_v1_explain_debug_transport_error_explicit_error(mock_urlopen: MagicMock):
    mock_urlopen.side_effect = urllib.error.URLError("refused")
    ev = _load_golden_evidence()
    req = _minimal_v1_ask(
        ev,
        request_id="req-a6-v1-net",
        query="Explain the highlighted code.",
        selected_file="module/sample.py",
        task_type="EXPLAIN_DEBUG",
        client_context={"selection": "def hello_unit():\n    return \"hello\"\n"},
    )
    resp = handle_ask_v1_request(req)

    ed = resp["explain_debug"]
    assert "error" in ed
    assert "summary" not in ed
    assert resp["plan_summary"]["steps"] == ["Reasoning service unavailable; no template steps substituted."]
    meta = resp.get("evidence_first_meta") or {}
    assert meta.get("ask_path") == "v1_evidence"


@patch("runtime.ask_service.reasoner.urllib.request.urlopen")
def test_v1_explain_debug_parse_failure_returns_error_in_payload(mock_urlopen: MagicMock):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(
        {"choices": [{"message": {"content": "not json at all"}}]}
    ).encode("utf-8")
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_resp
    mock_cm.__exit__.return_value = None
    mock_urlopen.return_value = mock_cm

    ev = _load_golden_evidence()
    req = _minimal_v1_ask(
        ev,
        request_id="req-a6-parse",
        query="Explain the highlighted code.",
        selected_file="module/sample.py",
        task_type="EXPLAIN_DEBUG",
        client_context={"selection": "def hello_unit():\n    return \"hello\"\n"},
    )
    resp = handle_ask_v1_request(req)

    assert "error" in resp["explain_debug"]
    assert "JSON" in resp["explain_debug"]["error"] or "json" in resp["explain_debug"]["error"].lower()
    assert resp["plan_summary"]["steps"]
    assert "no template steps substituted" in resp["plan_summary"]["steps"][0].lower()
    assert "unavailable" not in resp["plan_summary"]["steps"][0].lower()


# --- Path disclosure contract (closure surface) ---


def test_path_disclosure_v1_vs_v0_metadata_contract(tmp_path: Path):
    """
    v1 ingest always sets evidence_first_meta.ask_path == v1_evidence on success.
    v0 plain Explain/Debug does not (plugin/backend can distinguish without UI changes).
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "src").mkdir()
    (repo_root / "src" / "main.py").write_text("def main():\n    return 42\n", encoding="utf-8")

    with patch("runtime.ask_service.reasoner.urllib.request.urlopen") as mock_u:
        mock_u.return_value = _mock_vllm_success_response()
        v0 = handle_ask_request(
            {
                "schema_version": "ask_request.v0.1",
                "request_id": "req-pd-v0",
                "timestamp_utc": "2026-03-10T12:00:00Z",
                "repo_root": str(repo_root),
                "revision": "abc123",
                "query": "What does this code do?",
                "task_type": "EXPLAIN_DEBUG",
                "selected_file": "src/main.py",
                "client_context": {"selection": "def main():\n    return 42"},
            }
        )

    with patch("runtime.ask_service.v1_ingest.explain_debug") as mock_ed:
        mock_ed.return_value = ExplainDebugResult(summary="x")
        v1 = handle_ask_v1_request(
            _minimal_v1_ask(
                _load_golden_evidence(),
                request_id="req-pd-v1",
                query="Explain the highlighted code.",
                selected_file="module/sample.py",
                task_type="EXPLAIN_DEBUG",
                client_context={"selection": "def hello_unit():\n    return \"hello\"\n"},
            )
        )

    assert v0.get("evidence_first_meta") is None
    assert (v0.get("evidence_first_meta") or {}).get("ask_path") != "v1_evidence"

    assert (v1.get("evidence_first_meta") or {}).get("ask_path") == "v1_evidence"
    assert (v1.get("context_resolution") or {}).get("context_source") == "layer5.evidence_bundle.v1"

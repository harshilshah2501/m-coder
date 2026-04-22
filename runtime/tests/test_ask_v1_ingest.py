from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time
import urllib.error
import urllib.request
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest

from runtime.ask_service.v1_ingest import (
    AskV1ClientError,
    handle_ask_v1_request,
    validate_ask_v1_request,
)
from runtime.ask_service.reasoner import ExplainDebugResult

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GOLDEN_EVIDENCE = _REPO_ROOT / "runtime" / "layer5" / "evidence" / "golden" / "evidence_bundle.v1.masked.json"


def _load_golden_evidence() -> dict:
    with open(_GOLDEN_EVIDENCE, encoding="utf-8") as f:
        return json.load(f)


def _minimal_v1_ask(evidence: dict, **overrides) -> dict:
    base = {
        "schema_version": "ask_request.v1.0",
        "request_id": "req-v1-1",
        "timestamp_utc": "2026-03-21T12:00:00Z",
        "query": "Explain the highlighted code.",
        "evidence_bundle": evidence,
    }
    base.update(overrides)
    return base


def test_validate_ask_v1_request_rejects_wrong_schema_version():
    data = _minimal_v1_ask(_load_golden_evidence())
    data["schema_version"] = "ask_request.v0.1"
    errs = validate_ask_v1_request(data)
    assert errs


def test_validate_ask_v1_request_rejects_malformed_dirty_buffers():
    data = _minimal_v1_ask(
        _load_golden_evidence(),
        client_context={"dirty_buffers": [{"path": "src/main.py"}]},  # missing required content
    )
    errs = validate_ask_v1_request(data)
    assert errs


def test_validate_ask_v1_request_accepts_valid_dirty_buffers():
    data = _minimal_v1_ask(
        _load_golden_evidence(),
        client_context={
            "dirty_buffers": [
                {"path": "src/main.py", "content": "def main():\n    return 1\n"},
            ]
        },
    )
    errs = validate_ask_v1_request(data)
    assert not errs


def test_handle_ask_v1_dirty_buffer_noop_invalid_entries_are_noted():
    ev = _load_golden_evidence()
    req = _minimal_v1_ask(
        ev,
        request_id="req-v1-dirty-note",
        client_context={
            "dirty_buffers": [
                {"path": "module/sample.py", "bad": "missing content"},
            ]
        },
    )
    resp = handle_ask_v1_request(req)
    dbo = (resp.get("metadata") or {}).get("dirty_buffer_overlay") or {}
    assert dbo.get("payload_present") is True
    assert int(dbo.get("invalid_count") or 0) >= 1
    notes = (resp.get("plan_summary") or {}).get("notes") or []
    assert any("dirty buffer overlay payload contained invalid entries" in str(n).lower() for n in notes)


def test_handle_ask_v1_happy_path_plan_only():
    ev = _load_golden_evidence()
    req = _minimal_v1_ask(ev, revision="client-sha-1")
    errs = validate_ask_v1_request(req)
    assert not errs

    resp = handle_ask_v1_request(req)
    assert resp["schema_version"] == "plan_only_response.v0.1"
    assert resp["request_id"] == "req-v1-1"
    assert resp["governance_posture"] == "PLAN_ONLY"
    assert resp["execution"] is False
    assert resp["context_bundle"]["revision"] == "client-sha-1"
    assert "plan_gate:v1_ask:evidence_bundle.v1" in resp["context_bundle"]["selectors_used"]
    assert len(resp["context_bundle"]["files"]) >= 1
    assert resp.get("evidence_bundle", {}).get("schema_hint") == "layer5.evidence_bundle.v1"
    meta = resp.get("evidence_first_meta") or {}
    assert meta.get("ask_path") == "v1_evidence"
    assert meta.get("no_context_engine") is True
    cr = resp.get("context_resolution") or {}
    assert cr.get("no_repo_filesystem") is True
    steps = resp["plan_summary"]["steps"]
    assert len(steps) >= 1


def test_handle_ask_v1_dirty_buffer_overlay_reaches_reasoner_bundle():
    ev = _load_golden_evidence()
    first_path = str((ev.get("entries") or [])[0].get("relative_path") or "")
    req = _minimal_v1_ask(
        ev,
        request_id="req-v1-overlay-1",
        query="Explain highlighted code",
        task_type="EXPLAIN_DEBUG",
        selected_file=first_path,
        client_context={
            "selection": "return 99",
            "dirty_buffers": [
                {"path": first_path, "content": "def injected():\n    return 99  # V1_DIRTY_OVERLAY_TOKEN\n"}
            ],
        },
    )
    with patch("runtime.ask_service.v1_ingest.explain_debug") as mock_explain:
        mock_explain.return_value = ExplainDebugResult(summary="ok")
        resp = handle_ask_v1_request(req)

    assert resp.get("routing_mode") == "explain_debug"
    mock_explain.assert_called_once()
    bundle = mock_explain.call_args.kwargs["bundle"]
    item = next((x for x in bundle.items if x.path == first_path), None)
    assert item is not None
    assert "V1_DIRTY_OVERLAY_TOKEN" in item.content


def test_handle_ask_v1_evidence_schema_invalid():
    ev = deepcopy(_load_golden_evidence())
    ev["schema_hint"] = "wrong.hint"
    req = _minimal_v1_ask(ev)
    assert not validate_ask_v1_request(req)
    with pytest.raises(AskV1ClientError) as ei:
        handle_ask_v1_request(req)
    assert ei.value.code == "evidence_schema_invalid"


def test_handle_ask_v1_empty_entries():
    ev = deepcopy(_load_golden_evidence())
    ev["entries"] = []
    req = _minimal_v1_ask(ev)
    assert not validate_ask_v1_request(req)
    with pytest.raises(AskV1ClientError) as ei:
        handle_ask_v1_request(req)
    assert ei.value.code == "empty_evidence_bundle"


def test_handle_ask_v1_identity_mismatch():
    ev = deepcopy(_load_golden_evidence())
    ev["workspace_identity_hash"] = "hash-aaa"
    req = _minimal_v1_ask(ev, expected_workspace_identity_hash="hash-bbb")
    assert not validate_ask_v1_request(req)
    with pytest.raises(AskV1ClientError) as ei:
        handle_ask_v1_request(req)
    assert ei.value.code == "identity_mismatch"
    assert ei.value.details is not None


def _snippet_v1(text: str = "// code") -> dict:
    return {
        "text": text,
        "start_line": 1,
        "end_line": 1,
        "start_byte_utf8": 0,
        "end_byte_utf8": max(1, len(text.encode("utf-8"))),
        "anchor_line": 1,
        "matched_tokens": ["sync"],
        "selection_reason": "query_token_substring_anchor",
        "truncated_by_max_bytes": False,
    }


def _entry_v1(rank: int, path: str, role: str) -> dict:
    return {
        "provisional": False,
        "rank": rank,
        "relative_path": path,
        "retrieval_score": 10 - rank,
        "retrieval_breakdown": {"path_substrings": 1, "basename_substrings": 0, "content_substrings": 1},
        "retrieval_role": role,
        "snippet": _snippet_v1(),
    }


def test_handle_ask_v1_applies_grounding_and_owner_anchor_recovery():
    """
    /v1/ask must pass retrieval_role + authority into assess_evidence_quality (same as /v0/ask + layer5),
    so integration owners can recover STRONG via OWNER_ANCHOR_RECOVERY when top-3 lacks core aiops.
    """
    paths = [
        "motadata/src/main/java/com/mindarray/nms/DiscoveryEngine.java",
        "motadata/src/main/java/com/mindarray/visualization/VisualizationAvailabilityManager.java",
        "motadata/src/main/java/com/mindarray/integration/ServiceNowIntegration.java",
        "motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java",
        "motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java",
        "motadata/src/main/java/com/mindarray/aiops/DependencyManager.java",
        "motadata/src/main/java/com/mindarray/aiops/package-info.java",
        "motadata/src/main/java/com/mindarray/visualization/VisualizationEventManager.java",
    ]
    roles = [
        "SUPPORTING_CONTEXT",
        "SUPPORTING_CONTEXT",
        "PRIMARY_OWNER_CANDIDATE",
        "SUPPORTING_CONTEXT",
        "SUPPORTING_CONTEXT",
        "SUPPORTING_CONTEXT",
        "SUPPORTING_CONTEXT",
        "SUPPORTING_CONTEXT",
    ]
    entries = [_entry_v1(i, paths[i], roles[i]) for i in range(len(paths))]
    ev = {
        "provisional": False,
        "schema_hint": "layer5.evidence_bundle.v1",
        "query_raw": "Where is ServiceNow incident synchronization implemented?",
        "query_tokens": ["ServiceNow", "sync"],
        "top_k": 8,
        "index_schema_version": "layer5.file_index.v1",
        "workspace_identity_hash": "",
        "workspace_is_dirty": False,
        "workspace_snapshot_source": "path_only",
        "canonical_root": "",
        "a5_authority_note": (
            "Candidate order and retrieval_score come from Stage B fusion "
            "(lexical + authority + domain priors + constraints); A6 does not reorder by snippet."
        ),
        "entries": entries,
        "authority_resolution": {
            "matched_concepts": [],
            "primary_owner": {
                "file": "src/main/java/com/mindarray/integration/ServiceNowIntegration.java",
                "class": "ServiceNowIntegration",
                "confidence": "high",
            },
            "authority_confidence": "high",
            "authority_status": "validated",
            "control_flow": [],
            "notes": [],
            "forbidden_distractors": [],
        },
    }
    req = _minimal_v1_ask(
        ev,
        query="Where is ServiceNow incident synchronization implemented?",
        request_id="req-v1-owner-recovery",
    )
    assert not validate_ask_v1_request(req)
    resp = handle_ask_v1_request(req)
    meta = resp.get("metadata") or {}
    assert meta.get("evidence_quality") == "STRONG"
    assert "OWNER_ANCHOR_RECOVERY" in (meta.get("quality_reasons") or [])


def test_handle_ask_v1_legacy_validation_details_missing_method_exists_accepted():
    ev = deepcopy(_load_golden_evidence())
    if not isinstance(ev.get("authority_resolution"), dict):
        ev["authority_resolution"] = {
            "matched_concepts": [],
            "primary_owner": {
                "file": "runtime/ask_service/v1_ingest.py",
                "class": "AskV1Ingest",
                "confidence": "medium",
            },
            "authority_confidence": "medium",
            "authority_status": "unverified",
            "control_flow": [],
            "notes": [],
            "forbidden_distractors": [],
            "validation_details": {
                "file_exists": True,
                "class_exists": False,
                "freshness_ok": True,
                "days_since_verification": 0,
            },
        }

    ar = ev["authority_resolution"]
    vd = ar.get("validation_details")
    assert isinstance(vd, dict)

    # Simulate older producer that omitted now-required nullable keys.
    vd.pop("method_exists", None)
    vd.pop("is_referenced", None)

    req = _minimal_v1_ask(ev)
    resp = handle_ask_v1_request(req)
    assert resp["schema_version"] == "plan_only_response.v0.1"
    assert resp.get("request_id") == "req-v1-1"


def test_ask_v1_via_plan_gate_http(tmp_path):
    port = random.randint(20000, 49151)
    env = os.environ.copy()
    env["PLAN_GATE_PORT"] = str(port)
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

        body = json.dumps(_minimal_v1_ask(_load_golden_evidence(), request_id="http-v1")).encode("utf-8")
        req = urllib.request.Request(
            f"{base}/v1/ask",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            assert r.status == 200
            response = json.loads(r.read().decode("utf-8"))

        assert response.get("schema_version") == "plan_only_response.v0.1"
        assert response.get("request_id") == "http-v1"
        assert response.get("evidence_first_meta", {}).get("ask_path") == "v1_evidence"

        bad = json.dumps(_minimal_v1_ask(_load_golden_evidence(), evidence_bundle={"bad": True})).encode(
            "utf-8"
        )
        req_bad = urllib.request.Request(
            f"{base}/v1/ask",
            data=bad,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with pytest.raises(urllib.error.HTTPError) as he:
            urllib.request.urlopen(req_bad, timeout=10)
        assert he.value.code == 400
        err_body = json.loads(he.value.read().decode("utf-8"))
        assert err_body.get("error") == "evidence_schema_invalid"
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_v1_blocked_has_refusal_shape_and_metadata():
    ev = _load_golden_evidence()
    ev["entries"] = [
        {
            "provisional": False,
            "rank": 0,
            "relative_path": "logs/app.log",
            "retrieval_score": 1,
            "retrieval_breakdown": {
                "path_substrings": 1,
                "basename_substrings": 0,
                "content_substrings": 0,
            },
            "snippet": {
                "text": "error happened",
                "start_line": 1,
                "end_line": 1,
                "start_byte_utf8": 0,
                "end_byte_utf8": 14,
                "anchor_line": 1,
                "matched_tokens": ["error"],
                "selection_reason": "query_token_substring_anchor",
                "truncated_by_max_bytes": False,
            },
        }
    ]
    req = _minimal_v1_ask(ev, query="in this system")
    resp = handle_ask_v1_request(req)
    assert resp["execution"] is False
    assert resp["plan_summary"]["steps"] == []
    assert "explain_debug" not in resp
    md = resp.get("metadata") or {}
    assert md.get("evidence_quality") in {"INSUFFICIENT", "NO_MATCH"}
    assert isinstance(md.get("quality_reasons"), list) and len(md["quality_reasons"]) >= 1


def test_v1_explain_debug_runs_when_grounding_blocked_but_file_selection_anchored():
    """EXPLAIN_DEBUG must not short-circuit on quality.blocked when the user selected a file + prompt."""
    ev = _load_golden_evidence()
    ev["entries"] = [
        {
            "provisional": False,
            "rank": 0,
            "relative_path": "logs/app.log",
            "retrieval_score": 1,
            "retrieval_breakdown": {
                "path_substrings": 1,
                "basename_substrings": 0,
                "content_substrings": 0,
            },
            "snippet": {
                "text": "error happened",
                "start_line": 1,
                "end_line": 1,
                "start_byte_utf8": 0,
                "end_byte_utf8": 14,
                "anchor_line": 1,
                "matched_tokens": ["error"],
                "selection_reason": "query_token_substring_anchor",
                "truncated_by_max_bytes": False,
            },
        }
    ]
    req = _minimal_v1_ask(
        ev,
        query="Debug this path",
        request_id="req-v1-explain-override",
        task_type="EXPLAIN_DEBUG",
        selected_file="logs/app.log",
        client_context={"selection": "Find failure points in the log line."},
    )
    with patch("runtime.ask_service.v1_ingest.explain_debug") as mock_explain:
        mock_explain.return_value = ExplainDebugResult(summary="anchored")
        resp = handle_ask_v1_request(req)

    assert resp.get("routing_mode") == "explain_debug"
    mock_explain.assert_called_once()
    md = resp.get("metadata") or {}
    assert md.get("grounding_block_overridden_by_explain_debug") is True
    assert md.get("evidence_quality") in {"INSUFFICIENT", "NO_MATCH"}
    assert resp.get("explain_debug") is not None


def test_v1_metadata_includes_operator_hints_and_usefulness_metrics():
    req = _minimal_v1_ask(_load_golden_evidence())
    resp = handle_ask_v1_request(req)
    md = resp.get("metadata") or {}
    assert "operator_hints" in md
    assert isinstance(md["operator_hints"], list)
    assert "usefulness_metrics" in md
    um = md["usefulness_metrics"]
    assert isinstance(um, dict)
    assert um.get("entry_count") == 1
    assert um.get("snippet_anchor_hits") == 1


def test_v1_generic_ui_message_no_longer_says_no_architectural_writeup():
    req = _minimal_v1_ask(
        _load_golden_evidence(),
        query="How does this work in the repo?",
    )
    resp = handle_ask_v1_request(req)
    msg = ((resp.get("ui") or {}).get("message") or "").lower()
    assert "does not produce a full architectural write-up" not in msg
    assert "concise grounded flow summary" in msg


def test_v0_v1_metadata_semantics_match_on_quality_keys(tmp_path):
    from runtime.ask_service.handlers import handle_ask_request

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "src").mkdir()
    (repo_root / "src" / "app.py").write_text("def run():\n    return 1\n", encoding="utf-8")

    v0 = handle_ask_request(
        {
            "schema_version": "ask_request.v0.1",
            "request_id": "v0-md",
            "timestamp_utc": "2026-03-21T12:00:00Z",
            "repo_root": str(repo_root),
            "revision": "rev0",
            "query": "where implemented run",
        }
    )
    v1_req = _minimal_v1_ask(_load_golden_evidence(), request_id="v1-md", query="where implemented retry")
    v1 = handle_ask_v1_request(v1_req)
    for resp in (v0, v1):
        md = resp.get("metadata") or {}
        assert "intent_type" in md
        assert "evidence_quality" in md
        assert "quality_reasons" in md
        assert "dominance_metrics" in md

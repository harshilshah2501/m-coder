"""
Contract + handler tests for docs/validation/AIOPS_MVP_SCENARIO_PACK.md.

- No live HTTP required (uses golden evidence bundle + in-process Ask v1).
- Set AIOPS_MVP_LIVE=1 to optionally hit Context Layer + Plan-Gate (skipped if services are
  down or HTTP times out). Override seconds with AIOPS_MVP_LIVE_HTTP_TIMEOUT (default 300).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pytest

from runtime.ask_service.v1_ingest import handle_ask_v1_request, validate_ask_v1_request

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCENARIOS_PATH = _REPO_ROOT / "docs" / "validation" / "aiops_mvp_scenarios.v1.json"
_SCENARIO_PACK_MD = _REPO_ROOT / "docs" / "validation" / "AIOPS_MVP_SCENARIO_PACK.md"
_GOLDEN_EVIDENCE = _REPO_ROOT / "runtime" / "layer5" / "evidence" / "golden" / "evidence_bundle.v1.masked.json"


def _live_http_timeout(default_seconds: float = 300.0) -> float:
    """Seconds for Context Layer export and Plan-Gate /v1/ask in live smoke test."""
    raw = (os.environ.get("AIOPS_MVP_LIVE_HTTP_TIMEOUT") or "").strip()
    if not raw:
        return default_seconds
    try:
        return max(1.0, float(raw))
    except ValueError:
        return default_seconds


def _load_scenarios_doc() -> dict:
    with open(_SCENARIOS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load_golden_evidence() -> dict:
    with open(_GOLDEN_EVIDENCE, encoding="utf-8") as f:
        return json.load(f)


def _export_request_dict(workspace_root: str, query: str, top_k: int = 12) -> dict:
    return {
        "workspace_root": workspace_root,
        "query": query,
        "top_k": top_k,
    }


def _ask_v1_dict(bundle: dict, query: str, request_id: str) -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ask = {
        "schema_version": "ask_request.v1.0",
        "request_id": request_id,
        "timestamp_utc": ts,
        "query": query,
        "evidence_bundle": bundle,
        "task_type": "general",
        "trace_id": request_id,
    }
    h = (bundle.get("workspace_identity_hash") or "").strip()
    if h:
        ask["expected_workspace_identity_hash"] = h
    return ask


def test_scenarios_manifest_schema_and_count() -> None:
    doc = _load_scenarios_doc()
    assert doc.get("schema_version") == "aiops_mvp_scenarios.v1"
    scenarios = doc["scenarios"]
    assert len(scenarios) == 8
    ids = [s["id"] for s in scenarios]
    assert ids == ["A1", "A2", "D1", "D2", "P1", "P2", "C1", "C2"]
    for s in scenarios:
        assert s["id"]
        assert s["category"]
        assert s["query"].strip()
        assert len(s["query"]) >= 20


def test_scenario_pack_markdown_links_scenario_ids_to_json() -> None:
    """Scenario pack doc must reference the JSON manifest and list every scenario ID."""
    doc = _load_scenarios_doc()
    md_text = _SCENARIO_PACK_MD.read_text(encoding="utf-8")
    assert "aiops_mvp_scenarios.v1.json" in md_text
    for s in doc["scenarios"]:
        sid = s["id"]
        assert f"| {sid} |" in md_text, f"missing scenario row for {sid}"


@pytest.mark.parametrize("scenario_id", ["A1", "A2", "D1", "D2", "P1", "P2", "C1", "C2"])
def test_export_request_shape_matches_context_layer_contract(scenario_id: str) -> None:
    doc = _load_scenarios_doc()
    s = next(x for x in doc["scenarios"] if x["id"] == scenario_id)
    req = _export_request_dict("/tmp/motadata-workspace-root-example", s["query"], top_k=doc.get("top_k_default", 12))
    assert set(req.keys()) == {"workspace_root", "query", "top_k"}
    assert req["top_k"] == 12
    assert req["workspace_root"].startswith("/")
    assert s["query"] in req["query"]


@pytest.mark.parametrize("scenario_id", ["A1", "A2", "D1", "D2", "P1", "P2", "C1", "C2"])
def test_ask_v1_schema_validate_and_handle_plan_only(scenario_id: str) -> None:
    """Each MVP query produces a valid v1 ask and a PLAN_ONLY response with golden evidence."""
    doc = _load_scenarios_doc()
    s = next(x for x in doc["scenarios"] if x["id"] == scenario_id)
    ev = _load_golden_evidence()
    rid = f"aiops-mvp-test-{scenario_id}"
    req = _ask_v1_dict(ev, s["query"], rid)
    errs = validate_ask_v1_request(req)
    assert errs == [], f"schema errors: {errs}"

    resp = handle_ask_v1_request(req)
    assert resp["schema_version"] == "plan_only_response.v0.1"
    assert resp["request_id"] == rid
    assert resp["governance_posture"] == "PLAN_ONLY"
    assert resp["execution"] is False
    assert len(resp.get("plan_summary", {}).get("steps", [])) >= 1


def test_ask_v1_rejects_extra_top_level_field() -> None:
    doc = _load_scenarios_doc()
    s = doc["scenarios"][0]
    ev = _load_golden_evidence()
    req = _ask_v1_dict(ev, s["query"], "rid-x")
    req["mode"] = "ask"
    errs = validate_ask_v1_request(req)
    assert errs


@pytest.mark.skipif(
    os.environ.get("AIOPS_MVP_LIVE") != "1",
    reason="Set AIOPS_MVP_LIVE=1 with Context Layer + Plan-Gate running",
)
def test_live_export_and_ask_smoke() -> None:
    """Single scenario against real HTTP (optional)."""
    timeout = _live_http_timeout()
    context_url = os.environ.get("CONTEXT_URL", "http://127.0.0.1:8091").rstrip("/")
    plan_url = os.environ.get("PLAN_GATE_URL", "http://127.0.0.1:8089").rstrip("/")
    workspace = os.environ.get("MOTADATA_ROOT", "")
    if not workspace or not Path(workspace).is_dir():
        pytest.skip("MOTADATA_ROOT must point to an existing repo for live test")

    doc = _load_scenarios_doc()
    s = doc["scenarios"][0]
    export_body = json.dumps(
        {
            "workspace_root": workspace,
            "query": s["query"],
            "top_k": 12,
        }
    ).encode("utf-8")
    try:
        r = urllib.request.Request(
            f"{context_url}/v1/export_evidence",
            data=export_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            bundle = json.load(resp)
    except TimeoutError as e:
        pytest.skip(f"Context Layer /v1/export_evidence timed out after {timeout}s: {e}")
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        pytest.skip(f"Context Layer unreachable: {e}")

    rid = "aiops-mvp-live-smoke"
    ask = _ask_v1_dict(bundle, s["query"], rid)
    body = json.dumps(ask).encode("utf-8")
    try:
        r2 = urllib.request.Request(
            f"{plan_url}/v1/ask",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(r2, timeout=timeout) as resp2:
            out = json.load(resp2)
    except TimeoutError as e:
        pytest.skip(
            f"Plan-Gate /v1/ask timed out after {timeout}s "
            f"(increase AIOPS_MVP_LIVE_HTTP_TIMEOUT if backend is slow): {e}"
        )
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        pytest.skip(f"Plan-Gate unreachable: {e}")

    assert out.get("schema_version") == "plan_only_response.v0.1"
    assert out.get("governance_posture") == "PLAN_ONLY"

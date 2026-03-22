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

import pytest

from runtime.ask_service.v1_ingest import (
    AskV1ClientError,
    handle_ask_v1_request,
    validate_ask_v1_request,
)

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

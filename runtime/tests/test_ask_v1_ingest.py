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
from runtime.ask_service.plan_contract_builder import PlanContractBuildResult
from runtime.ask_service.code_reasoning_trace_builder import CodeReasoningTraceBuildResult
from runtime.ask_service.patch_proposal_builder import PatchProposalBuildResult
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


def test_validate_ask_v1_request_accepts_response_extensions_plan_contract_v1():
    data = _minimal_v1_ask(
        _load_golden_evidence(),
        response_extensions=["plan_contract.v1"],
    )
    errs = validate_ask_v1_request(data)
    assert not errs


def test_validate_ask_v1_request_rejects_unknown_response_extensions():
    data = _minimal_v1_ask(
        _load_golden_evidence(),
        response_extensions=["unknown.extension.v1"],
    )
    errs = validate_ask_v1_request(data)
    assert errs


def test_validate_ask_v1_request_rejects_trace_extension_without_plan_contract():
    data = _minimal_v1_ask(
        _load_golden_evidence(),
        response_extensions=["code_reasoning_trace.v1"],
    )
    errs = validate_ask_v1_request(data)
    assert errs
    assert any("code_reasoning_trace.v1 requires plan_contract.v1" in e for e in errs)


def test_validate_ask_v1_request_accepts_trace_extension_with_plan_contract():
    data = _minimal_v1_ask(
        _load_golden_evidence(),
        response_extensions=["plan_contract.v1", "code_reasoning_trace.v1"],
    )
    errs = validate_ask_v1_request(data)
    assert not errs


def test_validate_ask_v1_request_rejects_patch_extension_without_plan_contract() -> None:
    data = _minimal_v1_ask(
        _load_golden_evidence(),
        response_extensions=["code_reasoning_trace.v1", "patch_proposal.v1"],
    )
    errs = validate_ask_v1_request(data)
    assert errs
    assert any("patch_proposal.v1 requires plan_contract.v1" in e for e in errs)


def test_validate_ask_v1_request_rejects_patch_extension_without_trace() -> None:
    data = _minimal_v1_ask(
        _load_golden_evidence(),
        response_extensions=["plan_contract.v1", "patch_proposal.v1"],
    )
    errs = validate_ask_v1_request(data)
    assert errs
    assert any("patch_proposal.v1 requires code_reasoning_trace.v1" in e for e in errs)


def test_validate_ask_v1_request_accepts_patch_extension_with_plan_and_trace() -> None:
    data = _minimal_v1_ask(
        _load_golden_evidence(),
        response_extensions=["plan_contract.v1", "code_reasoning_trace.v1", "patch_proposal.v1"],
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
    md = resp.get("metadata") or {}
    cbp = md.get("context_budget_policy") or {}
    assert cbp.get("policy_version") == "context_budget_policy.v1"
    assert cbp.get("surface") == "ask"
    assert "plan_contract" not in resp
    assert "code_reasoning_trace" not in resp
    assert "patch_proposal" not in resp


def test_handle_ask_v1_optin_emits_plan_contract_when_valid():
    ev = _load_golden_evidence()
    req = _minimal_v1_ask(
        ev,
        revision="client-sha-1",
        response_extensions=["plan_contract.v1"],
    )
    resp = handle_ask_v1_request(req)
    assert resp["schema_version"] == "plan_only_response.v0.1"
    assert resp["governance_posture"] == "PLAN_ONLY"
    assert resp["execution"] is False
    pc = resp.get("plan_contract")
    assert isinstance(pc, dict)
    assert pc.get("schema_version") == "plan_contract.v1"
    pc_meta = (resp.get("metadata") or {}).get("plan_contract_v1") or {}
    assert pc_meta.get("requested") is True
    assert pc_meta.get("emitted") is True


def test_handle_ask_v1_optin_omits_plan_contract_when_builder_omits(monkeypatch: pytest.MonkeyPatch):
    ev = _load_golden_evidence()
    req = _minimal_v1_ask(
        ev,
        response_extensions=["plan_contract.v1"],
    )

    monkeypatch.setattr(
        "runtime.ask_service.v1_ingest.build_plan_contract_v1",
        lambda **_k: PlanContractBuildResult(plan_contract=None, omission_reason="missing_metadata:evidence_quality"),
    )
    resp = handle_ask_v1_request(req)
    assert "plan_contract" not in resp
    pc_meta = (resp.get("metadata") or {}).get("plan_contract_v1") or {}
    assert pc_meta.get("requested") is True
    assert pc_meta.get("emitted") is False
    assert pc_meta.get("omission_reason") == "missing_metadata:evidence_quality"


def test_handle_ask_v1_paired_optin_emits_trace_when_valid():
    ev = _strong_owner_method_evidence_v1()
    req = _minimal_v1_ask(
        ev,
        response_extensions=["plan_contract.v1", "code_reasoning_trace.v1"],
    )
    resp = handle_ask_v1_request(req)
    assert resp["schema_version"] == "plan_only_response.v0.1"
    assert resp["governance_posture"] == "PLAN_ONLY"
    assert resp["execution"] is False
    assert isinstance(resp.get("plan_contract"), dict)
    crt = resp.get("code_reasoning_trace")
    assert isinstance(crt, dict)
    assert crt.get("schema_version") == "code_reasoning_trace.v1"
    tr_meta = (resp.get("metadata") or {}).get("code_reasoning_trace_v1") or {}
    assert tr_meta.get("requested") is True
    assert tr_meta.get("emitted") is True


def test_handle_ask_v1_paired_optin_omits_trace_with_diagnostic(monkeypatch: pytest.MonkeyPatch):
    ev = _load_golden_evidence()
    req = _minimal_v1_ask(
        ev,
        response_extensions=["plan_contract.v1", "code_reasoning_trace.v1"],
    )
    monkeypatch.setattr(
        "runtime.ask_service.v1_ingest.build_code_reasoning_trace_v1",
        lambda **_k: CodeReasoningTraceBuildResult(
            code_reasoning_trace=None,
            omission_reason="insufficient_metadata",
        ),
    )
    resp = handle_ask_v1_request(req)
    assert "code_reasoning_trace" not in resp
    tr_meta = (resp.get("metadata") or {}).get("code_reasoning_trace_v1") or {}
    assert tr_meta.get("requested") is True
    assert tr_meta.get("emitted") is False
    assert tr_meta.get("omission_reason") == "insufficient_metadata"


def test_handle_ask_v1_plan_and_trace_optin_does_not_emit_patch_proposal() -> None:
    ev = _strong_owner_method_evidence_v1()
    req = _minimal_v1_ask(
        ev,
        response_extensions=["plan_contract.v1", "code_reasoning_trace.v1"],
    )
    resp = handle_ask_v1_request(req)
    assert isinstance(resp.get("plan_contract"), dict)
    assert isinstance(resp.get("code_reasoning_trace"), dict)
    assert "patch_proposal" not in resp
    assert "patch_proposal_v1" not in (resp.get("metadata") or {})


def test_handle_ask_v1_triple_optin_emits_patch_proposal_when_valid() -> None:
    ev = _strong_owner_method_evidence_v1()
    req = _minimal_v1_ask(
        ev,
        response_extensions=["plan_contract.v1", "code_reasoning_trace.v1", "patch_proposal.v1"],
    )
    resp = handle_ask_v1_request(req)
    assert resp["schema_version"] == "plan_only_response.v0.1"
    assert resp["governance_posture"] == "PLAN_ONLY"
    assert resp["execution"] is False
    assert isinstance(resp.get("plan_contract"), dict)
    assert isinstance(resp.get("code_reasoning_trace"), dict)
    pp = resp.get("patch_proposal")
    assert isinstance(pp, dict)
    assert pp.get("schema_version") == "patch_proposal.v1"
    rr = ((pp.get("review_requirements") or {}) if isinstance(pp, dict) else {})
    assert rr.get("human_review_required") is True
    pp_meta = (resp.get("metadata") or {}).get("patch_proposal_v1") or {}
    assert pp_meta.get("requested") is True
    assert pp_meta.get("emitted") is True


def test_handle_ask_v1_triple_optin_omits_patch_proposal_with_diagnostic(monkeypatch: pytest.MonkeyPatch) -> None:
    ev = _strong_owner_method_evidence_v1()
    req = _minimal_v1_ask(
        ev,
        response_extensions=["plan_contract.v1", "code_reasoning_trace.v1", "patch_proposal.v1"],
    )
    monkeypatch.setattr(
        "runtime.ask_service.v1_ingest.build_patch_proposal_v1",
        lambda **_k: PatchProposalBuildResult(
            patch_proposal=None,
            omission_reason="forbidden_or_refusal_posture",
        ),
    )
    resp = handle_ask_v1_request(req)
    assert "patch_proposal" not in resp
    pp_meta = (resp.get("metadata") or {}).get("patch_proposal_v1") or {}
    assert pp_meta.get("requested") is True
    assert pp_meta.get("emitted") is False
    assert pp_meta.get("omission_reason") == "forbidden_or_refusal_posture"


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


def test_handle_ask_v1_curates_generic_debug_narration():
    ev = _load_golden_evidence()
    first_path = str((ev.get("entries") or [])[0].get("relative_path") or "")
    req = _minimal_v1_ask(
        ev,
        request_id="req-v1-debug-curation-1",
        query="Debug why this flow can fail",
        task_type="EXPLAIN_DEBUG",
        selected_file=first_path,
        client_context={"selection": "return item;"},
    )
    with patch("runtime.ask_service.v1_ingest.explain_debug") as mock_explain:
        mock_explain.return_value = ExplainDebugResult(
            summary="The snippet does not provide enough context and we can infer some potential reasons.",
            logic_flow="",
            likely_bug_risk="",
            evidence=[],
            confidence_limits="",
        )
        resp = handle_ask_v1_request(req)

    md = resp.get("metadata") if isinstance(resp.get("metadata"), dict) else {}
    ed = resp.get("explain_debug") if isinstance(resp.get("explain_debug"), dict) else {}
    assert md.get("debug_narration_quality") == "CURATED"
    assert "DEBUG_NARRATION_CURATED" in (md.get("quality_reasons") or [])
    assert md.get("debug_narration_issues")
    assert str(ed.get("summary") or "").startswith("Governance-curated debug summary")
    assert ed.get("evidence")


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


def _strong_owner_method_evidence_v1() -> dict:
    return {
        "provisional": False,
        "schema_hint": "layer5.evidence_bundle.v1",
        "query_raw": "Where is ServiceNow incident synchronization implemented?",
        "query_tokens": ["ServiceNow", "sync"],
        "top_k": 1,
        "index_schema_version": "layer5.file_index.v1",
        "workspace_identity_hash": "",
        "workspace_is_dirty": False,
        "workspace_snapshot_source": "path_only",
        "canonical_root": "",
        "a5_authority_note": (
            "Candidate order and retrieval_score come from Stage B fusion "
            "(lexical + authority + domain priors + constraints); A6 does not reorder by snippet."
        ),
        "entries": [
            {
                "provisional": False,
                "rank": 0,
                "relative_path": "motadata/src/main/java/com/mindarray/integration/ServiceNowIntegration.java",
                "retrieval_score": 10,
                "retrieval_breakdown": {
                    "path_substrings": 2,
                    "basename_substrings": 1,
                    "content_substrings": 2,
                },
                "retrieval_role": "PRIMARY_OWNER_CANDIDATE",
                "snippet": {
                    "text": (
                        "public class ServiceNowIntegration {\n"
                        "  public void synchronizeIncident() {\n"
                        "    if (incident == null) return;\n"
                        "  }\n"
                        "}\n"
                    ),
                    "start_line": 1,
                    "end_line": 5,
                    "start_byte_utf8": 0,
                    "end_byte_utf8": 120,
                    "anchor_line": 2,
                    "matched_tokens": ["ServiceNow", "sync"],
                    "selection_reason": "query_token_substring_anchor",
                    "truncated_by_max_bytes": False,
                },
            }
        ],
        "authority_resolution": {
            "matched_concepts": [],
            "primary_owner": {
                "file": "src/main/java/com/mindarray/integration/ServiceNowIntegration.java",
                "class": "ServiceNowIntegration",
                "method": "synchronizeIncident",
                "confidence": "high",
            },
            "authority_confidence": "high",
            "authority_status": "validated",
            "control_flow": [],
            "notes": [],
            "forbidden_distractors": [],
        },
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
        assert response.get("governance_posture") == "PLAN_ONLY"
        assert response.get("execution") is False
        assert "plan_contract" not in response
        assist = response.get("assist_layer") if isinstance(response.get("assist_layer"), dict) else {}
        assist_v2 = assist.get("assist_v2") if isinstance(assist.get("assist_v2"), dict) else {}
        for key in ("answer", "evidence", "gaps", "next_steps"):
            assert key in assist_v2
        # Ask activation must preserve proof-density diagnostics from metadata.
        hooks = assist_v2.get("proof_density_hooks") if isinstance(assist_v2.get("proof_density_hooks"), dict) else {}
        md = response.get("metadata") if isinstance(response.get("metadata"), dict) else {}
        assert hooks.get("execution_path_stitched") == md.get("execution_path_stitched")
        assert hooks.get("call_site_resolution_state") == md.get("call_site_resolution_state")
        assert hooks.get("method_window_visible_rate") == md.get("method_window_visible_rate")

        body_optin = json.dumps(
            _minimal_v1_ask(
                _load_golden_evidence(),
                request_id="http-v1-optin",
                response_extensions=["plan_contract.v1"],
            )
        ).encode("utf-8")
        req_optin = urllib.request.Request(
            f"{base}/v1/ask",
            data=body_optin,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_optin, timeout=10) as r:
            assert r.status == 200
            optin_resp = json.loads(r.read().decode("utf-8"))
        assert optin_resp.get("schema_version") == "plan_only_response.v0.1"
        assert optin_resp.get("governance_posture") == "PLAN_ONLY"
        assert optin_resp.get("execution") is False
        pc = optin_resp.get("plan_contract")
        assert isinstance(pc, dict)
        assert pc.get("schema_version") == "plan_contract.v1"

        body_trace_optin = json.dumps(
            _minimal_v1_ask(
                _strong_owner_method_evidence_v1(),
                request_id="http-v1-trace-optin",
                response_extensions=["plan_contract.v1", "code_reasoning_trace.v1"],
            )
        ).encode("utf-8")
        req_trace_optin = urllib.request.Request(
            f"{base}/v1/ask",
            data=body_trace_optin,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_trace_optin, timeout=10) as r:
            assert r.status == 200
            trace_resp = json.loads(r.read().decode("utf-8"))
        assert trace_resp.get("schema_version") == "plan_only_response.v0.1"
        assert trace_resp.get("governance_posture") == "PLAN_ONLY"
        assert trace_resp.get("execution") is False
        crt = trace_resp.get("code_reasoning_trace")
        assert isinstance(crt, dict)
        assert crt.get("schema_version") == "code_reasoning_trace.v1"
        assert "patch_proposal" not in trace_resp

        body_patch_optin = json.dumps(
            _minimal_v1_ask(
                _strong_owner_method_evidence_v1(),
                request_id="http-v1-patch-optin",
                response_extensions=[
                    "plan_contract.v1",
                    "code_reasoning_trace.v1",
                    "patch_proposal.v1",
                ],
            )
        ).encode("utf-8")
        req_patch_optin = urllib.request.Request(
            f"{base}/v1/ask",
            data=body_patch_optin,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_patch_optin, timeout=10) as r:
            assert r.status == 200
            patch_resp = json.loads(r.read().decode("utf-8"))
        assert patch_resp.get("schema_version") == "plan_only_response.v0.1"
        assert patch_resp.get("governance_posture") == "PLAN_ONLY"
        assert patch_resp.get("execution") is False
        patch_proposal = patch_resp.get("patch_proposal")
        assert isinstance(patch_proposal, dict)
        assert patch_proposal.get("schema_version") == "patch_proposal.v1"
        rr = patch_proposal.get("review_requirements") if isinstance(patch_proposal, dict) else {}
        assert (rr or {}).get("human_review_required") is True

        body_trace_only = json.dumps(
            _minimal_v1_ask(
                _load_golden_evidence(),
                request_id="http-v1-trace-only",
                response_extensions=["code_reasoning_trace.v1"],
            )
        ).encode("utf-8")
        req_trace_only = urllib.request.Request(
            f"{base}/v1/ask",
            data=body_trace_only,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with pytest.raises(urllib.error.HTTPError) as he_dep:
            urllib.request.urlopen(req_trace_only, timeout=10)
        assert he_dep.value.code == 400
        dep_body = json.loads(he_dep.value.read().decode("utf-8"))
        details = dep_body.get("details") if isinstance(dep_body.get("details"), list) else []
        assert any("code_reasoning_trace.v1 requires plan_contract.v1" in str(x) for x in details)

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


def test_ask_v1_debug_v2_via_plan_gate_http_preserves_explain_debug_shape(tmp_path):
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

        ev = _load_golden_evidence()
        entries = ev.get("entries") if isinstance(ev.get("entries"), list) else []
        selected_file = str(entries[0].get("relative_path") or "") if entries else ""
        body = json.dumps(
            _minimal_v1_ask(
                ev,
                request_id="http-v1-debug-v2",
                query="Explain the highlighted code.",
                task_type="EXPLAIN_DEBUG",
                selected_file=selected_file,
                client_context={"selection": "def hello_unit():\n    return \"hello\"\n"},
            )
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{base}/v1/ask",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            assert r.status == 200
            response = json.loads(r.read().decode("utf-8"))

        assist = response.get("assist_layer") if isinstance(response.get("assist_layer"), dict) else {}
        assist_v2 = assist.get("assist_v2") if isinstance(assist.get("assist_v2"), dict) else {}
        route_decision = assist_v2.get("route_decision") if isinstance(assist_v2.get("route_decision"), dict) else {}
        assert route_decision.get("mode") == "debug"
        assert "debug_v2" in assist_v2
        assert "answer" not in assist_v2 and "evidence" not in assist_v2

        debug_v2 = assist_v2.get("debug_v2") if isinstance(assist_v2.get("debug_v2"), dict) else {}
        for key in ("summary", "execution_flow", "likely_failure_points", "evidence", "confidence_limits", "next_inspection_targets"):
            assert key in debug_v2
        assert isinstance(debug_v2.get("likely_failure_points"), list)
        assert isinstance(debug_v2.get("next_inspection_targets"), list)
        assert isinstance(debug_v2.get("evidence"), dict)

        explain_debug = response.get("explain_debug") if isinstance(response.get("explain_debug"), dict) else {}
        assert explain_debug, "existing explain_debug payload must remain present"
        if "summary" in explain_debug:
            assert debug_v2.get("summary") == explain_debug.get("summary")
        if "logic_flow" in explain_debug:
            assert debug_v2.get("execution_flow") == explain_debug.get("logic_flow")
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_ask_v1_ask_mode_via_plan_gate_http_surfaces_investigate_bridge(tmp_path):
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

        ev = _strong_owner_method_evidence_v1()
        body = json.dumps(
            _minimal_v1_ask(
                ev,
                request_id="http-v1-investigate-bridge",
                query="Where is ServiceNow incident synchronization implemented?",
            )
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{base}/v1/ask",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            assert r.status == 200
            response = json.loads(r.read().decode("utf-8"))

        assert response.get("governance_posture") == "PLAN_ONLY"
        assert response.get("execution") is False
        assert response.get("evidence_first_meta", {}).get("ask_path") == "v1_evidence"

        assist = response.get("assist_layer") if isinstance(response.get("assist_layer"), dict) else {}
        assist_v2 = assist.get("assist_v2") if isinstance(assist.get("assist_v2"), dict) else {}
        route = assist_v2.get("route_decision") if isinstance(assist_v2.get("route_decision"), dict) else {}
        assert route.get("mode") == "ask"
        investigate = assist_v2.get("investigate") if isinstance(assist_v2.get("investigate"), dict) else {}
        assert investigate.get("available") is True
        assert investigate.get("reason") in {"owner_method_grounded", "owner_method_visible"}
        target = investigate.get("target") if isinstance(investigate.get("target"), dict) else {}
        assert target.get("file") == "src/main/java/com/mindarray/integration/ServiceNowIntegration.java"
        assert target.get("method") == "synchronizeIncident"
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

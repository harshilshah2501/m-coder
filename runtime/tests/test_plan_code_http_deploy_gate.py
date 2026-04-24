from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.scripts import plan_code_http_deploy_gate as gate


def _plan_resp(decision: str = "BOUNDING") -> dict:
    return {
        "schema_version": "decision_response.v0.1",
        "request_id": "p1",
        "decision": decision,
        "constitutional_phase_emitted": "CONF",
        "dominance_source": "CONF",
        "irreversible_boundary_phrase": "merge",
        "boundary_phrase_hash": "a" * 64,
        "boundary_type": "merge",
        "authority_verdict": "pass",
        "missing_evidence": [],
        "allowed_pre_boundary_actions": ["read"],
        "blocked_actions": [],
        "reason_codes": [],
        "plan_hash": "b" * 64,
        "ui": {"title": "t", "message": "m", "severity": "info"},
    }


def _execute_resp(outcome: str, executed: bool, **extra: object) -> dict:
    r: dict = {
        "schema_version": "execute_response.v0.1",
        "request_id": "e1",
        "outcome": outcome,
        "executed": executed,
        "posture": "refuse",
        "reason": "r",
    }
    r.update(extra)
    return r


def _ask_resp(*, include_plan_contract: bool = False, omission_reason: str | None = None) -> dict:
    return {
        "schema_version": "plan_only_response.v0.1",
        "request_id": "a1",
        "timestamp_utc": "2026-04-24T00:00:00Z",
        "governance_posture": "PLAN_ONLY",
        "execution": False,
        "context_bundle": {"revision": "r", "files": [], "selectors_used": []},
        "plan_summary": {"steps": ["step one"], "notes": []},
        "ui": {"title": "t", "message": "m", "severity": "info"},
        **(
            {"plan_contract": {"schema_version": "plan_contract.v1", "task_intent": {"summary": "x", "kind": "explore"}}}
            if include_plan_contract
            else {}
        ),
        **(
            {"metadata": {"plan_contract_v1": {"requested": True, "emitted": False, "omission_reason": omission_reason}}}
            if omission_reason
            else {}
        ),
    }


def _ask_empty_steps_with_ui() -> dict:
    """WSL-like: empty plan steps with UI message (weak / grounded-block paths)."""
    r = _ask_resp()
    r["plan_summary"] = {"steps": [], "notes": []}
    return r


def test_ask_allows_empty_steps_when_ui_or_notes_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            _plan_resp("BOUNDING"),
            _plan_resp("APPROVE"),
            _execute_resp("EXECUTED", True),
            _execute_resp("REFUSED", False),
            _execute_resp("REFUSED", False),
            _ask_empty_steps_with_ui(),
            _ask_resp(include_plan_contract=True),
            _ask_resp(include_plan_contract=True),
        ]
    )
    monkeypatch.setattr(gate, "_post_json", lambda *_a, **_k: next(responses))
    monkeypatch.setattr(
        gate,
        "_graph_preflight",
        lambda: {"state": "COMPLETE", "reason": "ok"},
    )
    out = gate.run_gate(
        "http://127.0.0.1:8089",
        workspace_root="/tmp/ws",
        timeout_s=5,
        require_graph_preflight=True,
        ledger_path=None,
    )
    assert out["all_pass"] is True
    assert out["checks"]["ask_v1_plan_only_surface"]["pass"] is True


def test_run_plan_code_gate_all_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter(
        [
            _plan_resp("BOUNDING"),
            _plan_resp("APPROVE"),
            _execute_resp("EXECUTED", True, decision_ledger_row_id="ldg-1", ledger_row_id="lx-1"),
            _execute_resp("REFUSED", False),
            _execute_resp("REFUSED", False),
            _ask_resp(),
            _ask_resp(include_plan_contract=True),
            _ask_resp(include_plan_contract=True),
        ]
    )

    monkeypatch.setattr(gate, "_post_json", lambda *_a, **_k: next(responses))
    monkeypatch.setattr(
        gate,
        "_graph_preflight",
        lambda: {"state": "COMPLETE", "reason": "ok"},
    )

    out = gate.run_gate(
        "http://127.0.0.1:8089",
        workspace_root="/tmp/ws",
        timeout_s=5,
        require_graph_preflight=True,
        ledger_path="/tmp/ledger.jsonl",
    )
    assert out["all_pass"] is True
    assert out["checks"]["plan_shadow_pr_merge"]["pass"] is True
    assert out["checks"]["execute_rm_blocked"]["pass"] is True
    assert out["checks"]["ask_v1_plan_only_surface"]["pass"] is True


def test_graph_preflight_strict_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter(
        [
            _plan_resp(),
            _plan_resp(),
            _execute_resp("EXECUTED", True),
            _execute_resp("REFUSED", False),
            _execute_resp("REFUSED", False),
            _ask_resp(),
            _ask_resp(include_plan_contract=True),
            _ask_resp(include_plan_contract=True),
        ]
    )
    monkeypatch.setattr(gate, "_post_json", lambda *_a, **_k: next(responses))
    monkeypatch.setattr(gate, "_graph_preflight", lambda: {"state": "UNREACHABLE", "reason": "no driver"})
    out = gate.run_gate(
        "http://x",
        "/tmp",
        5,
        require_graph_preflight=True,
        ledger_path=None,
    )
    assert out["all_pass"] is False


def test_script_main_writes_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter(
        [
            _plan_resp(),
            _plan_resp(),
            _execute_resp("EXECUTED", True),
            _execute_resp("REFUSED", False),
            _execute_resp("REFUSED", False),
            _ask_resp(),
            _ask_resp(include_plan_contract=True),
            _ask_resp(include_plan_contract=True),
        ]
    )
    monkeypatch.setattr(gate, "_post_json", lambda *_a, **_k: next(responses))
    monkeypatch.setattr(gate, "_graph_preflight", lambda: {"state": "COMPLETE", "reason": "ok"})
    out_file = tmp_path / "out.json"
    rc = gate.main(
        [
            "--plan-gate-url",
            "http://127.0.0.1:8089",
            "--workspace-root",
            "/tmp",
            "--skip-graph-preflight",
            "--out",
            str(out_file),
        ]
    )
    assert rc == 0
    data = json.loads(out_file.read_text())
    assert data["all_pass"] is True


def test_optin_omission_requires_diagnostic(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter(
        [
            _plan_resp(),
            _plan_resp(),
            _execute_resp("EXECUTED", True),
            _execute_resp("REFUSED", False),
            _execute_resp("REFUSED", False),
            _ask_resp(),  # default no opt-in
            _ask_resp(include_plan_contract=True),  # strong opt-in
            _ask_resp(omission_reason="missing_metadata:evidence_quality"),  # weak opt-in omitted with diagnostic
        ]
    )
    monkeypatch.setattr(gate, "_post_json", lambda *_a, **_k: next(responses))
    monkeypatch.setattr(gate, "_graph_preflight", lambda: {"state": "COMPLETE", "reason": "ok"})
    out = gate.run_gate(
        "http://x",
        "/tmp",
        5,
        require_graph_preflight=True,
        ledger_path=None,
    )
    assert out["all_pass"] is True
    assert out["checks"]["ask_v1_optin_omission_diagnostic"]["pass"] is True

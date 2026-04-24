#!/usr/bin/env python3
"""
HTTP deploy gate for existing Plan (/v0/plan) and Code (/v0/execute) surfaces on Plan-Gate.

Observational only: does not require or assert `plan_contract` / `code_reasoning_trace` on `/v1/ask`.

Reuses graph preflight from motadata_behavior_verify (optional strict mode).

Repo root is added to sys.path so `python3 runtime/scripts/plan_code_http_deploy_gate.py` works from checkout root.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from runtime.scripts.assist_v2_http_deploy_gate import _weak_evidence_v1
from runtime.scripts.motadata_behavior_verify import _graph_preflight

VALID_PLAN_DECISIONS = frozenset({"APPROVE", "CONDITIONAL_BLOCK", "REFUSAL", "BOUNDING"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _post_json(url: str, payload: dict[str, Any], timeout_s: int) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _assert(conditions: list[tuple[bool, str]]) -> list[str]:
    return [msg for ok, msg in conditions if not ok]


def _plan_request_pr_merge(workspace_root: str) -> dict[str, Any]:
    rid = str(uuid.uuid4())
    return {
        "schema_version": "plan_request.v0.1",
        "request_id": rid,
        "timestamp_utc": _utc_now(),
        "mode": "shadow",
        "ide_event": {
            "schema_version": "ide_event.v0.1",
            "event_id": f"evt-plan-code-gate-{rid}",
            "timestamp_utc": _utc_now(),
            "ide_context": {
                "product": "cli",
                "ide": "none",
                "project": "Motadata",
                "repo_root": workspace_root,
                "branch": "main",
                "user": "operator",
            },
            "action": {"action_type": "PR_MERGE", "target": "main"},
            "evidence_refs": [{"type": "note", "ref": "plan-code-gate-pr-merge"}],
        },
        "requested_capabilities": ["plan_and_decide"],
        "client_policy": {"fail_closed_if_gate_unreachable": True},
    }


def _plan_request_doc_update(workspace_root: str) -> dict[str, Any]:
    req = _plan_request_pr_merge(workspace_root)
    req["request_id"] = str(uuid.uuid4())
    ev = req.get("ide_event") if isinstance(req.get("ide_event"), dict) else {}
    ev["action"] = {"action_type": "DOC_UPDATE", "target": "docs/README.md"}
    req["ide_event"] = ev
    return req


def _execute_payload(workspace_root: str, command: str, *, ledger_path: str | None = None) -> dict[str, Any]:
    p: dict[str, Any] = {
        "schema_version": "execute_request.v0.1",
        "request_id": str(uuid.uuid4()),
        "repo_root": workspace_root,
        "command": command,
    }
    if ledger_path:
        p["ledger_path"] = ledger_path
    return p


def _coherent_execute(outcome: str, executed: bool | None) -> bool:
    if outcome == "EXECUTED":
        return executed is True
    if outcome in ("REFUSED", "BLOCKED", "DEFERRED", "BOUNDED_ALLOW"):
        return executed is False
    return True


def run_gate(
    plan_gate_url: str,
    workspace_root: str,
    timeout_s: int,
    *,
    require_graph_preflight: bool,
    ledger_path: str | None,
) -> dict[str, Any]:
    out: dict[str, Any] = {"checks": {}, "errors": []}
    base = plan_gate_url.rstrip("/")

    # --- /v0/plan: PR merge shadow ---
    try:
        pr_resp = _post_json(f"{base}/v0/plan", _plan_request_pr_merge(workspace_root), timeout_s)
    except Exception as exc:  # pragma: no cover - network
        out["errors"].append(f"plan pr_merge: {exc}")
        pr_resp = {}

    pr_errors = _assert(
        [
            (pr_resp.get("schema_version") == "decision_response.v0.1", "plan pr_merge: schema_version drift"),
            (pr_resp.get("decision") in VALID_PLAN_DECISIONS, f"plan pr_merge: decision not in governed set: {pr_resp.get('decision')!r}"),
            (isinstance(pr_resp.get("blocked_actions"), list), "plan pr_merge: blocked_actions must be a list"),
        ]
    )
    out["checks"]["plan_shadow_pr_merge"] = {"pass": not pr_errors, "errors": pr_errors}
    out["errors"].extend(pr_errors)

    # --- /v0/plan: doc update (bounded approval class) ---
    try:
        doc_resp = _post_json(f"{base}/v0/plan", _plan_request_doc_update(workspace_root), timeout_s)
    except Exception as exc:  # pragma: no cover
        out["errors"].append(f"plan doc_update: {exc}")
        doc_resp = {}

    doc_errors = _assert(
        [
            (doc_resp.get("schema_version") == "decision_response.v0.1", "plan doc_update: schema_version drift"),
            (doc_resp.get("decision") in VALID_PLAN_DECISIONS, f"plan doc_update: decision not in governed set: {doc_resp.get('decision')!r}"),
        ]
    )
    out["checks"]["plan_shadow_doc_update"] = {"pass": not doc_errors, "errors": doc_errors}
    out["errors"].extend(doc_errors)

    # --- /v0/execute: safe echo ---
    try:
        echo_resp = _post_json(
            f"{base}/v0/execute",
            _execute_payload(workspace_root, "echo plan-code-gate-ok", ledger_path=ledger_path),
            timeout_s,
        )
    except Exception as exc:  # pragma: no cover
        out["errors"].append(f"execute echo: {exc}")
        echo_resp = {}

    echo_out = str(echo_resp.get("outcome") or "")
    echo_ex = echo_resp.get("executed")
    echo_errors = _assert(
        [
            (echo_resp.get("schema_version") == "execute_response.v0.1", "execute echo: schema_version drift"),
            (echo_out in ("EXECUTED", "REFUSED", "BLOCKED", "DEFERRED", "BOUNDED_ALLOW"), f"execute echo: unexpected outcome {echo_out!r}"),
            (_coherent_execute(echo_out, echo_ex if isinstance(echo_ex, bool) else None), "execute echo: outcome vs executed incoherent"),
        ]
    )
    if ledger_path and echo_out == "EXECUTED":
        rid = echo_resp.get("decision_ledger_row_id")
        echo_errors.extend(
            _assert(
                [
                    (isinstance(rid, str) and bool(rid.strip()), "execute echo: decision_ledger_row_id missing with ledger_path"),
                ]
            )
        )
    out["checks"]["execute_safe_echo_coherent"] = {"pass": not echo_errors, "errors": echo_errors}
    out["errors"].extend(echo_errors)

    # --- /v0/execute: destructive rm must not execute ---
    try:
        rm_resp = _post_json(
            f"{base}/v0/execute",
            _execute_payload(workspace_root, "rm -rf /tmp/mcoder_plan_code_gate_probe"),
            timeout_s,
        )
    except Exception as exc:  # pragma: no cover
        out["errors"].append(f"execute rm: {exc}")
        rm_resp = {}

    rm_errors = _assert(
        [
            (rm_resp.get("schema_version") == "execute_response.v0.1", "execute rm: schema_version drift"),
            (rm_resp.get("outcome") == "BLOCKED", f"execute rm: expected BLOCKED got {rm_resp.get('outcome')!r}"),
            (rm_resp.get("executed") is False, "execute rm: executed must be false"),
        ]
    )
    out["checks"]["execute_rm_blocked"] = {"pass": not rm_errors, "errors": rm_errors}
    out["errors"].extend(rm_errors)

    # --- /v0/execute: privileged probe ---
    try:
        priv_resp = _post_json(
            f"{base}/v0/execute",
            _execute_payload(workspace_root, "systemctl restart sshd"),
            timeout_s,
        )
    except Exception as exc:  # pragma: no cover
        out["errors"].append(f"execute privileged: {exc}")
        priv_resp = {}

    po = str(priv_resp.get("outcome") or "")
    priv_errors = _assert(
        [
            (priv_resp.get("schema_version") == "execute_response.v0.1", "execute privileged: schema_version drift"),
            (po in ("REFUSED", "BLOCKED"), f"execute privileged: expected REFUSED or BLOCKED got {po!r}"),
            (priv_resp.get("executed") is False, "execute privileged: executed must be false"),
        ]
    )
    out["checks"]["execute_privileged_blocked"] = {"pass": not priv_errors, "errors": priv_errors}
    out["errors"].extend(priv_errors)

    # --- /v1/ask: plan-only surface (no new plan_contract fields required) ---
    try:
        ask_resp = _post_json(
            f"{base}/v1/ask",
            {
                "schema_version": "ask_request.v1.0",
                "request_id": str(uuid.uuid4()),
                "timestamp_utc": _utc_now(),
                "query": "in this system",
                "evidence_bundle": _weak_evidence_v1(),
            },
            timeout_s,
        )
    except Exception as exc:  # pragma: no cover
        out["errors"].append(f"ask v1: {exc}")
        ask_resp = {}

    ask_errors = _assert(
        [
            (ask_resp.get("schema_version") == "plan_only_response.v0.1", "ask v1: schema_version drift"),
            (ask_resp.get("governance_posture") == "PLAN_ONLY", "ask v1: governance_posture must be PLAN_ONLY"),
            (ask_resp.get("execution") is False, "ask v1: execution must be false"),
            (isinstance(ask_resp.get("plan_summary"), dict), "ask v1: plan_summary missing"),
            (isinstance((ask_resp.get("plan_summary") or {}).get("steps"), list), "ask v1: plan_summary.steps missing"),
            (len((ask_resp.get("plan_summary") or {}).get("steps") or []) >= 1, "ask v1: plan_summary.steps must be non-empty"),
        ]
    )
    out["checks"]["ask_v1_plan_only_surface"] = {"pass": not ask_errors, "errors": ask_errors}
    out["errors"].extend(ask_errors)

    preflight = _graph_preflight()
    preflight_errors: list[str] = []
    if require_graph_preflight and preflight.get("state") != "COMPLETE":
        preflight_errors.append(
            f"graph preflight unhealthy: state={preflight.get('state')} reason={preflight.get('reason')}"
        )
    out["checks"]["graph_preflight_healthy"] = {
        "pass": len(preflight_errors) == 0,
        "required": require_graph_preflight,
        "details": preflight,
        "errors": preflight_errors,
    }
    out["errors"].extend(preflight_errors)

    out["all_pass"] = len(out["errors"]) == 0
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Plan + Code HTTP deploy gate (existing /v0/plan, /v0/execute, /v1/ask)")
    parser.add_argument("--plan-gate-url", default="http://127.0.0.1:8089")
    default_ws = os.environ.get("MOTADATA_GATE_WORKSPACE_ROOT", "").strip() or str(_REPO_ROOT)
    parser.add_argument(
        "--workspace-root",
        default=default_ws,
        help="repo_root for /v0/execute and plan ide_context (default: MOTADATA_GATE_WORKSPACE_ROOT or m-coder checkout)",
    )
    parser.add_argument("--timeout-s", type=int, default=30)
    parser.add_argument("--out", default="runtime/.run/plan_code_http_deploy_gate.json")
    parser.add_argument(
        "--skip-graph-preflight",
        action="store_true",
        help="Do not fail when graph preflight is not COMPLETE (local smoke without Neo4j).",
    )
    parser.add_argument(
        "--ledger-path",
        default="",
        help="Optional path for execute_request ledger_path (tests / strict environments).",
    )
    args = parser.parse_args(argv)
    ledger_path = str(args.ledger_path).strip() or None

    try:
        result = run_gate(
            args.plan_gate_url,
            str(Path(args.workspace_root).expanduser()),
            args.timeout_s,
            require_graph_preflight=not args.skip_graph_preflight,
            ledger_path=ledger_path,
        )
    except urllib.error.HTTPError as exc:
        result = {
            "all_pass": False,
            "errors": [f"http error: {exc.code} {exc.reason}"],
            "checks": {},
        }
    except Exception as exc:  # pragma: no cover
        result = {
            "all_pass": False,
            "errors": [f"gate execution error: {exc}"],
            "checks": {},
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result.get("all_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""
Behavior verification for Motadata AIOps workspace.

Validates these capabilities through live endpoints:
  - query   (export_evidence + /v1/ask)
  - debug   (/v1/ask with EXPLAIN_DEBUG)
  - plan    (/v0/plan contract)
  - code    (/v0/execute contract)
  - agent   (no dedicated /v0/agent route; assist metadata on ask)

Exits non-zero on any failed check.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _post(url: str, payload: dict[str, Any], timeout: int = 180) -> tuple[int, dict[str, Any]]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))


def _get(url: str, timeout: int = 30) -> tuple[int, dict[str, Any]]:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))


def _safe_body_preview(body: Any) -> str:
    s = str(body)
    return s[:300]


def _clip(text: str, n: int = 220) -> str:
    if len(text) <= n:
        return text
    return text[: n - 3] + "..."


def _build_run_summary(run: dict[str, Any]) -> dict[str, Any]:
    checks = run.get("checks") or {}
    query = checks.get("query") or {}
    debug = checks.get("debug") or {}
    plan = checks.get("plan") or {}
    code = checks.get("code") or {}
    export = checks.get("export_evidence") or {}
    return {
        "pass": run.get("all_pass", False),
        "query": {
            "pass": query.get("pass", False),
            "ask_path": query.get("ask_path"),
            "evidence_quality": query.get("evidence_quality"),
            "quality_reasons": query.get("quality_reasons") or [],
            "answer_steps": query.get("answer_steps") or [],
            "notes": query.get("answer_notes") or [],
            "top_paths": export.get("top_paths") or [],
        },
        "debug": {
            "pass": debug.get("pass", False),
            "routing_mode": debug.get("routing_mode"),
            "summary": debug.get("summary"),
            "likely_bug_risk": debug.get("likely_bug_risk"),
            "error": debug.get("error"),
        },
        "plan": {
            "pass": plan.get("pass", False),
            "decision": plan.get("decision"),
        },
        "code": {
            "pass": code.get("pass", False),
            "outcome": code.get("outcome"),
            "posture": code.get("posture"),
            "executed": code.get("executed"),
        },
        "agent": checks.get("agent") or {},
    }


def _print_concise(final: dict[str, Any]) -> None:
    print("")
    print("=== Motadata Behavior Verification Summary ===")
    print(f"workspace: {final.get('workspace_root')}")
    print(f"repeat: {final.get('repeat')}  stable: {final.get('stable')}  all_pass: {final.get('all_pass')}")
    print("")
    for idx, run in enumerate(final.get("runs") or [], start=1):
        s = run.get("summary") or {}
        print(f"[run {idx}] pass={s.get('pass')}")
        q = s.get("query") or {}
        print(
            f"  query: pass={q.get('pass')} ask_path={q.get('ask_path')} evidence_quality={q.get('evidence_quality')}"
        )
        if q.get("quality_reasons"):
            print(f"  query_quality_reasons: {q.get('quality_reasons')}")
        for i, step in enumerate((q.get("answer_steps") or [])[:3], start=1):
            print(f"  query_answer_{i}: {_clip(str(step), 180)}")
        if q.get("notes"):
            print(f"  query_notes: {q.get('notes')}")
        if q.get("top_paths"):
            print(f"  top_paths: {q.get('top_paths')[:3]}")
        d = s.get("debug") or {}
        print(f"  debug: pass={d.get('pass')} routing_mode={d.get('routing_mode')}")
        if d.get("summary"):
            print(f"  debug_summary: {_clip(str(d.get('summary')), 180)}")
        if d.get("likely_bug_risk"):
            print(f"  debug_risk: {_clip(str(d.get('likely_bug_risk')), 180)}")
        if d.get("error"):
            print(f"  debug_error: {_clip(str(d.get('error')), 180)}")
        p = s.get("plan") or {}
        c = s.get("code") or {}
        print(f"  plan_decision: {p.get('decision')}")
        print(f"  code: outcome={c.get('outcome')} posture={c.get('posture')} executed={c.get('executed')}")
        print("")


def run_once(
    workspace_root: str,
    context_url: str,
    plan_gate_url: str,
    vllm_url: str,
    query: str,
    debug_query: str,
    top_k: int,
) -> dict[str, Any]:
    checks: dict[str, Any] = {}

    for name, url in (
        ("context_health", f"{context_url}/healthz"),
        ("plan_gate_health", f"{plan_gate_url}/healthz"),
        ("plan_gate_version", f"{plan_gate_url}/version"),
        ("vllm_models", f"{vllm_url}/v1/models"),
    ):
        try:
            code, body = _get(url)
            checks[name] = {"pass": code == 200, "http": code, "body_preview": _safe_body_preview(body)}
        except Exception as exc:  # pragma: no cover - runtime path
            checks[name] = {"pass": False, "error": str(exc)}

    code, evidence = _post(
        f"{context_url}/v1/export_evidence",
        {"workspace_root": workspace_root, "query": query, "top_k": top_k},
        timeout=300,
    )
    entries = evidence.get("entries") if isinstance(evidence.get("entries"), list) else []
    checks["export_evidence"] = {
        "pass": code == 200 and evidence.get("schema_hint") == "layer5.evidence_bundle.v1" and len(entries) > 0,
        "http": code,
        "schema_hint": evidence.get("schema_hint"),
        "entries_count": len(entries),
        "top_paths": [e.get("relative_path") for e in entries[:5]],
        "workspace_identity_hash_present": bool(evidence.get("workspace_identity_hash")),
    }

    ask_v1_req: dict[str, Any] = {
        "schema_version": "ask_request.v1.0",
        "request_id": str(uuid.uuid4()),
        "timestamp_utc": _utc_now(),
        "query": query,
        "evidence_bundle": evidence,
    }
    ws_hash = evidence.get("workspace_identity_hash")
    if ws_hash:
        ask_v1_req["expected_workspace_identity_hash"] = ws_hash

    code, ask_query_resp = _post(f"{plan_gate_url}/v1/ask", ask_v1_req)
    query_meta = ask_query_resp.get("metadata") or {}
    checks["query"] = {
        "pass": (
            code == 200
            and (ask_query_resp.get("evidence_first_meta") or {}).get("ask_path") == "v1_evidence"
            and ask_query_resp.get("governance_posture") == "PLAN_ONLY"
            and ask_query_resp.get("execution") is False
            and len(((ask_query_resp.get("plan_summary") or {}).get("steps") or [])) > 0
        ),
        "http": code,
        "ask_path": (ask_query_resp.get("evidence_first_meta") or {}).get("ask_path"),
        "governance_posture": ask_query_resp.get("governance_posture"),
        "execution": ask_query_resp.get("execution"),
        "evidence_quality": query_meta.get("evidence_quality"),
        "quality_reasons": query_meta.get("quality_reasons"),
        "steps_count": len(((ask_query_resp.get("plan_summary") or {}).get("steps") or [])),
        "assist_layer_present": "assist_layer" in ask_query_resp,
        "answer_steps": ((ask_query_resp.get("plan_summary") or {}).get("steps") or []),
        "answer_notes": ((ask_query_resp.get("plan_summary") or {}).get("notes") or []),
    }

    first_path = entries[0].get("relative_path") if entries else "runtime/plan_gate_service/app.py"
    debug_req = dict(ask_v1_req)
    debug_req.update(
        {
            "request_id": str(uuid.uuid4()),
            "query": debug_query,
            "task_type": "EXPLAIN_DEBUG",
            "selected_file": first_path,
            "client_context": {"selection": "Investigate likely failure points and trace flow."},
        }
    )
    code, ask_debug_resp = _post(f"{plan_gate_url}/v1/ask", debug_req)
    explain_debug = ask_debug_resp.get("explain_debug") or {}
    checks["debug"] = {
        "pass": (
            code == 200
            and ask_debug_resp.get("routing_mode") == "explain_debug"
            and isinstance(explain_debug, dict)
            and ("summary" in explain_debug or "error" in explain_debug)
        ),
        "http": code,
        "routing_mode": ask_debug_resp.get("routing_mode"),
        "explain_debug_keys": sorted(list(explain_debug.keys())) if isinstance(explain_debug, dict) else [],
        "has_summary": bool(explain_debug.get("summary")) if isinstance(explain_debug, dict) else False,
        "has_error": bool(explain_debug.get("error")) if isinstance(explain_debug, dict) else False,
        "summary": explain_debug.get("summary") if isinstance(explain_debug, dict) else None,
        "likely_bug_risk": explain_debug.get("likely_bug_risk") if isinstance(explain_debug, dict) else None,
        "error": explain_debug.get("error") if isinstance(explain_debug, dict) else None,
    }

    plan_req: dict[str, Any] = {
        "schema_version": "plan_request.v0.1",
        "request_id": str(uuid.uuid4()),
        "timestamp_utc": _utc_now(),
        "mode": "shadow",
        "ide_event": {
            "schema_version": "ide_event.v0.1",
            "event_id": "evt-motadata-plan-verify",
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
            "evidence_refs": [{"type": "note", "ref": "motadata-plan-verification"}],
        },
        "requested_capabilities": ["plan_and_decide"],
        "client_policy": {"fail_closed_if_gate_unreachable": True},
    }
    code, plan_resp = _post(f"{plan_gate_url}/v0/plan", plan_req)
    checks["plan"] = {
        "pass": code == 200 and plan_resp.get("schema_version") == "decision_response.v0.1" and bool(plan_resp.get("decision")),
        "http": code,
        "schema_version": plan_resp.get("schema_version"),
        "decision": plan_resp.get("decision"),
    }

    execute_req = {
        "schema_version": "execute_request.v0.1",
        "request_id": str(uuid.uuid4()),
        "repo_root": workspace_root,
        "command": "echo motadata-execute-probe",
    }
    code, execute_resp = _post(f"{plan_gate_url}/v0/execute", execute_req)
    checks["code"] = {
        "pass": (
            code == 200
            and execute_resp.get("schema_version") == "execute_response.v0.1"
            and bool(execute_resp.get("outcome"))
            and execute_resp.get("executed") is not None
        ),
        "http": code,
        "schema_version": execute_resp.get("schema_version"),
        "outcome": execute_resp.get("outcome"),
        "executed": execute_resp.get("executed"),
        "posture": execute_resp.get("posture"),
    }

    try:
        _post(f"{plan_gate_url}/v0/agent", {"request_id": "agent-probe"}, timeout=20)
        no_agent_route = False
    except urllib.error.HTTPError as exc:
        no_agent_route = exc.code == 404
    checks["agent"] = {
        "pass": no_agent_route and ("assist_layer" in ask_query_resp),
        "agent_route_404": no_agent_route,
        "assist_layer_present_in_ask": "assist_layer" in ask_query_resp,
        "note": "Agent behavior is exposed via governed ask/execute, not a dedicated /v0/agent route.",
    }

    all_pass = all((item or {}).get("pass") for item in checks.values())
    return {"checks": checks, "all_pass": all_pass}


def _stable_signature(run: dict[str, Any]) -> str:
    checks = run.get("checks") or {}
    payload = {
        "context_health_pass": (checks.get("context_health") or {}).get("pass"),
        "plan_gate_health_pass": (checks.get("plan_gate_health") or {}).get("pass"),
        "plan_gate_version_pass": (checks.get("plan_gate_version") or {}).get("pass"),
        "vllm_models_pass": (checks.get("vllm_models") or {}).get("pass"),
        "export_evidence_pass": (checks.get("export_evidence") or {}).get("pass"),
        "export_schema_hint": (checks.get("export_evidence") or {}).get("schema_hint"),
        "entries_count": (checks.get("export_evidence") or {}).get("entries_count"),
        "query_pass": (checks.get("query") or {}).get("pass"),
        "query_ask_path": (checks.get("query") or {}).get("ask_path"),
        "query_governance_posture": (checks.get("query") or {}).get("governance_posture"),
        "query_execution": (checks.get("query") or {}).get("execution"),
        "query_evidence_quality": (checks.get("query") or {}).get("evidence_quality"),
        "debug_pass": (checks.get("debug") or {}).get("pass"),
        "debug_routing_mode": (checks.get("debug") or {}).get("routing_mode"),
        "debug_has_summary": (checks.get("debug") or {}).get("has_summary"),
        "plan_pass": (checks.get("plan") or {}).get("pass"),
        "plan_schema_version": (checks.get("plan") or {}).get("schema_version"),
        "plan_decision": (checks.get("plan") or {}).get("decision"),
        "code_pass": (checks.get("code") or {}).get("pass"),
        "code_schema_version": (checks.get("code") or {}).get("schema_version"),
        "code_outcome": (checks.get("code") or {}).get("outcome"),
        "code_posture": (checks.get("code") or {}).get("posture"),
        "agent_pass": (checks.get("agent") or {}).get("pass"),
        "agent_route_404": (checks.get("agent") or {}).get("agent_route_404"),
    }
    return json.dumps(payload, sort_keys=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Motadata AIOps behaviors end-to-end.")
    parser.add_argument("--workspace-root", required=True, help="Absolute path to Motadata workspace")
    parser.add_argument("--context-url", default="http://127.0.0.1:8091")
    parser.add_argument("--plan-gate-url", default="http://127.0.0.1:8089")
    parser.add_argument("--vllm-url", default="http://127.0.0.1:8000")
    parser.add_argument("--query", default="How does alert correlation and incident enrichment work in this repo?")
    parser.add_argument(
        "--debug-query",
        default="Debug likely causes of missed incident enrichment in this repository",
    )
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--repeat", type=int, default=1, help="Number of repeated runs for stability check")
    parser.add_argument(
        "--print",
        dest="print_mode",
        choices=["concise", "json"],
        default="concise",
        help="stdout format: concise summary (default) or full json",
    )
    parser.add_argument(
        "--out",
        default="runtime/.run/motadata_behavior_validation.json",
        help="Output JSON report path",
    )
    args = parser.parse_args()

    out_runs: list[dict[str, Any]] = []
    for _ in range(max(1, args.repeat)):
        out_runs.append(
            run_once(
                workspace_root=args.workspace_root,
                context_url=args.context_url.rstrip("/"),
                plan_gate_url=args.plan_gate_url.rstrip("/"),
                vllm_url=args.vllm_url.rstrip("/"),
                query=args.query,
                debug_query=args.debug_query,
                top_k=args.top_k,
            )
        )

    stable = len({_stable_signature(r) for r in out_runs}) == 1
    final = {
        "timestamp_utc": _utc_now(),
        "workspace_root": args.workspace_root,
        "repeat": max(1, args.repeat),
        "stable": stable,
        "runs": [{"checks": r["checks"], "all_pass": r["all_pass"], "summary": _build_run_summary(r)} for r in out_runs],
        "all_pass": all(r.get("all_pass") for r in out_runs) and stable,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(final, indent=2), encoding="utf-8")
    if args.print_mode == "json":
        print(json.dumps(final, indent=2))
    else:
        _print_concise(final)
    print(f"\nSaved: {out_path}")
    return 0 if final["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

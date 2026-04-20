#!/usr/bin/env python3
"""
One-command Ask v1 CLI: export evidence + call /v1/ask + human summary.

Example:
  python3 runtime/scripts/motadata_query_cli.py \
    --workspace-root "$MOTADATA_REPO_ROOT" \
    --query "Which class is the base class for all APIs?" \
    --out /tmp/q4.json
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


def _now_utc() -> str:
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


def _print_summary(resp: dict[str, Any]) -> None:
    md = resp.get("metadata") if isinstance(resp.get("metadata"), dict) else {}
    steps = ((resp.get("plan_summary") or {}).get("steps") or []) if isinstance(resp.get("plan_summary"), dict) else []
    print("")
    print("=== Motadata Ask Summary ===")
    print(f"request_id: {resp.get('request_id')}")
    print(f"posture: {resp.get('governance_posture')}  executed: {resp.get('execution')}")
    print(f"ask_path: {(resp.get('evidence_first_meta') or {}).get('ask_path')}")
    print(f"quality: {md.get('evidence_quality')}  reasons: {md.get('quality_reasons')}")
    if steps:
        print(f"answer_1: {steps[0]}")
    if len(steps) > 1:
        print(f"next_step: {steps[1]}")
    print("")


def main() -> int:
    p = argparse.ArgumentParser(description="Ask v1 query CLI (export_evidence + /v1/ask).")
    p.add_argument("--workspace-root", required=True)
    p.add_argument("--query", required=True)
    p.add_argument("--context-url", default="http://127.0.0.1:8091")
    p.add_argument("--plan-gate-url", default="http://127.0.0.1:8089")
    p.add_argument("--top-k", type=int, default=8)
    p.add_argument("--out", default="", help="Optional: write full response JSON to this path")
    p.add_argument("--print", dest="print_mode", choices=["summary", "json"], default="summary")
    args = p.parse_args()

    context_url = args.context_url.rstrip("/")
    plan_gate_url = args.plan_gate_url.rstrip("/")

    try:
        ec, evidence = _post(
            f"{context_url}/v1/export_evidence",
            {
                "workspace_root": args.workspace_root,
                "query": args.query,
                "top_k": args.top_k,
            },
            timeout=300,
        )
        if ec != 200:
            print(f"export_evidence failed http={ec}", file=sys.stderr)
            return 1

        ask_req: dict[str, Any] = {
            "schema_version": "ask_request.v1.0",
            "request_id": str(uuid.uuid4()),
            "timestamp_utc": _now_utc(),
            "query": args.query,
            "evidence_bundle": evidence,
        }
        ws_hash = evidence.get("workspace_identity_hash")
        if ws_hash:
            ask_req["expected_workspace_identity_hash"] = ws_hash

        ac, resp = _post(f"{plan_gate_url}/v1/ask", ask_req, timeout=300)
        if ac != 200:
            print(f"/v1/ask failed http={ac}", file=sys.stderr)
            return 1
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"http error: {exc.code} {body}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.out.strip():
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(resp, indent=2), encoding="utf-8")
        print(f"Saved: {out}")

    if args.print_mode == "json":
        print(json.dumps(resp, indent=2))
    else:
        _print_summary(resp)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


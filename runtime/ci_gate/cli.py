"""CI Backstop Gate CLI — calls Plan-Gate Service, fails build on REFUSAL/CONDITIONAL_BLOCK."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO = Path(__file__).resolve().parents[2]


def ci_input_to_plan_request(ci: dict, mode: str, fixed_time: str | None) -> dict:
    """Map CI input to PlanRequest v0.1. Deterministic request_id from canonical JSON."""
    repo = ci.get("repo", "m-coder")
    branch = ci.get("branch", "main")
    action_type = ci.get("action_type", "OTHER")
    target = ci.get("target", "")
    evidence_refs = ci.get("evidence_refs", [])
    request_id = ci.get("request_id") or _derive_request_id(ci)

    ts = fixed_time or ci.get("timestamp_utc", "2026-03-01T00:00:00Z")
    project = repo.replace("/", "-").split("-")[-1] or "m-coder"

    return {
        "schema_version": "plan_request.v0.1",
        "request_id": request_id,
        "timestamp_utc": ts,
        "mode": mode,
        "ide_event": {
            "schema_version": "ide_event.v0.1",
            "event_id": f"evt-ci-{hashlib.sha256(json.dumps(ci, sort_keys=True).encode()).hexdigest()[:16]}",
            "timestamp_utc": ts,
            "ide_context": {
                "product": "ci",
                "ide": "ci_gate",
                "project": project,
                "repo_root": f"/{repo}",
                "branch": branch,
                "user": "ci",
            },
            "action": {"action_type": action_type, "target": target},
            "evidence_refs": evidence_refs,
        },
        "requested_capabilities": ["plan_and_decide"],
        "client_policy": {"fail_closed_if_gate_unreachable": True},
    }


def _derive_request_id(ci: dict) -> str:
    c = json.dumps(ci, sort_keys=True)
    h = hashlib.sha256(c.encode()).hexdigest()[:16]
    return f"req-ci-{h}"


def main() -> int:
    ap = argparse.ArgumentParser(description="CI Backstop Gate")
    ap.add_argument("--input", required=True, help="Path to ci_input.json")
    ap.add_argument("--endpoint", default="http://127.0.0.1:8089/v0/plan")
    ap.add_argument("--mode", default="shadow", choices=["shadow", "live"])
    ap.add_argument("--fail-on", default="REFUSAL,CONDITIONAL_BLOCK")
    ap.add_argument("--fixed-time", default=None)
    ap.add_argument("--strict", action="store_true", default=True)
    ap.add_argument("--no-strict", dest="strict", action="store_false")
    args = ap.parse_args()

    fail_on = {x.strip() for x in args.fail_on.split(",") if x.strip()}

    path = Path(args.input)
    if not path.exists():
        print(json.dumps({"error": "input not found", "path": str(path)}), file=sys.stderr)
        return 2

    ci = json.loads(path.read_text())
    plan_request = ci_input_to_plan_request(ci, args.mode, args.fixed_time)

    try:
        data = json.dumps(plan_request).encode("utf-8")
        req = Request(args.endpoint, data=data, method="POST", headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=10) as resp:
            decision = json.loads(resp.read().decode())
    except (URLError, OSError, HTTPError) as e:
        if args.strict:
            print(json.dumps({"error": "service unreachable", "detail": str(e), "exit": 2}))
            return 2
        print(json.dumps({"error": "service unreachable", "detail": str(e), "exit": 0}))
        return 0

    if decision.get("schema_version") != "decision_response.v0.1":
        if args.strict:
            print(json.dumps({"error": "invalid response schema", "exit": 2}))
            return 2
        print(json.dumps({"decision": decision.get("decision", "unknown"), "exit": 0}))
        return 0

    dec = decision.get("decision", "unknown")
    summary = {"decision": dec, "request_id": decision.get("request_id")}

    if dec in fail_on:
        print(json.dumps(summary))
        return 1

    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())

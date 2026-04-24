from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from runtime.scripts.motadata_behavior_verify import _graph_preflight


def _post_json(url: str, payload: dict[str, Any], timeout_s: int) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _strong_owner_method_evidence_v1() -> dict[str, Any]:
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


def _weak_evidence_v1() -> dict[str, Any]:
    return {
        "provisional": False,
        "schema_hint": "layer5.evidence_bundle.v1",
        "query_raw": "in this system",
        "query_tokens": ["in", "this", "system"],
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
        ],
    }


def _assert(conditions: list[tuple[bool, str]]) -> list[str]:
    return [msg for ok, msg in conditions if not ok]


def run_gate(plan_gate_url: str, timeout_s: int, require_graph_preflight: bool) -> dict[str, Any]:
    out: dict[str, Any] = {"checks": {}, "errors": []}
    endpoint = f"{plan_gate_url.rstrip('/')}/v1/ask"

    grounded_req = {
        "schema_version": "ask_request.v1.0",
        "request_id": "deploy-gate-ask-grounded",
        "timestamp_utc": "2026-04-23T13:00:00Z",
        "query": "Where is ServiceNow incident synchronization implemented?",
        "evidence_bundle": _strong_owner_method_evidence_v1(),
    }
    grounded_resp = _post_json(endpoint, grounded_req, timeout_s)
    assist = grounded_resp.get("assist_layer") if isinstance(grounded_resp.get("assist_layer"), dict) else {}
    assist_v2 = assist.get("assist_v2") if isinstance(assist.get("assist_v2"), dict) else {}
    route = assist_v2.get("route_decision") if isinstance(assist_v2.get("route_decision"), dict) else {}
    investigate = assist_v2.get("investigate") if isinstance(assist_v2.get("investigate"), dict) else {}
    target = investigate.get("target") if isinstance(investigate.get("target"), dict) else {}
    grounded_errors = _assert(
        [
            (route.get("mode") == "ask", "grounded ask: assist_v2 mode must be ask"),
            ("answer" in assist_v2 and "evidence" in assist_v2 and "gaps" in assist_v2 and "next_steps" in assist_v2, "grounded ask: ask sections missing"),
            (grounded_resp.get("governance_posture") == "PLAN_ONLY", "grounded ask: governance_posture drift"),
            (grounded_resp.get("execution") is False, "grounded ask: execution must remain false"),
            ((grounded_resp.get("evidence_first_meta") or {}).get("ask_path") == "v1_evidence", "grounded ask: ask_path drift"),
            (investigate.get("available") is True, "grounded ask: investigate bridge missing"),
            (bool(target.get("file")) and bool(target.get("method")), "grounded ask: investigate target file/method missing"),
        ]
    )
    out["checks"]["grounded_ask_shape"] = {"pass": not grounded_errors, "errors": grounded_errors}
    out["errors"].extend(grounded_errors)

    weak_req = {
        "schema_version": "ask_request.v1.0",
        "request_id": "deploy-gate-ask-weak",
        "timestamp_utc": "2026-04-23T13:00:01Z",
        "query": "in this system",
        "evidence_bundle": _weak_evidence_v1(),
    }
    weak_resp = _post_json(endpoint, weak_req, timeout_s)
    weak_assist = weak_resp.get("assist_layer") if isinstance(weak_resp.get("assist_layer"), dict) else {}
    weak_v2 = weak_assist.get("assist_v2") if isinstance(weak_assist.get("assist_v2"), dict) else {}
    weak_route = weak_v2.get("route_decision") if isinstance(weak_v2.get("route_decision"), dict) else {}
    weak_errors = _assert(
        [
            (weak_route.get("mode") == "ask", "weak ask: assist_v2 mode must remain ask"),
            ("investigate" not in weak_v2, "weak ask: investigate must be omitted"),
            (weak_resp.get("execution") is False, "weak ask: execution must remain false"),
            ((weak_resp.get("evidence_first_meta") or {}).get("ask_path") == "v1_evidence", "weak ask: ask_path drift"),
        ]
    )
    out["checks"]["weak_ask_investigate_omission"] = {"pass": not weak_errors, "errors": weak_errors}
    out["errors"].extend(weak_errors)

    debug_req = {
        "schema_version": "ask_request.v1.0",
        "request_id": "deploy-gate-debug-missing-file",
        "timestamp_utc": "2026-04-23T13:00:02Z",
        "query": "Explain highlighted code.",
        "task_type": "EXPLAIN_DEBUG",
        "selected_file": "src/main/java/com/mindarray/aiops/MissingFile.java",
        "client_context": {"selection": "trace branch behavior"},
        "evidence_bundle": _strong_owner_method_evidence_v1(),
    }
    debug_resp = _post_json(endpoint, debug_req, timeout_s)
    debug_assist = debug_resp.get("assist_layer") if isinstance(debug_resp.get("assist_layer"), dict) else {}
    debug_v2_root = debug_assist.get("assist_v2") if isinstance(debug_assist.get("assist_v2"), dict) else {}
    debug_route = debug_v2_root.get("route_decision") if isinstance(debug_v2_root.get("route_decision"), dict) else {}
    debug_v2 = debug_v2_root.get("debug_v2") if isinstance(debug_v2_root.get("debug_v2"), dict) else {}
    debug_ev = debug_v2.get("evidence") if isinstance(debug_v2.get("evidence"), dict) else {}
    explain_debug = debug_resp.get("explain_debug") if isinstance(debug_resp.get("explain_debug"), dict) else {}
    debug_conf = debug_v2.get("confidence_limits") if isinstance(debug_v2.get("confidence_limits"), dict) else {}
    debug_errors = _assert(
        [
            (debug_route.get("mode") == "debug", "debug missing-file: assist_v2 mode must be debug"),
            (bool(explain_debug), "debug missing-file: top-level explain_debug must remain present"),
            (bool(debug_v2), "debug missing-file: debug_v2 missing"),
            (debug_ev.get("grounding_tier") == "none", "debug missing-file: grounding tier must be none"),
            (isinstance(debug_conf.get("not_visible"), list) and len(debug_conf.get("not_visible") or []) > 0, "debug missing-file: not_visible confidence limits missing"),
            (debug_resp.get("execution") is False, "debug missing-file: execution must remain false"),
        ]
    )
    out["checks"]["debug_shape_and_fail_closed"] = {"pass": not debug_errors, "errors": debug_errors}
    out["errors"].extend(debug_errors)

    preflight = _graph_preflight()
    preflight_errors = []
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
    parser = argparse.ArgumentParser(description="Assist v2 HTTP deploy gate")
    parser.add_argument("--plan-gate-url", default="http://127.0.0.1:8089")
    parser.add_argument("--timeout-s", type=int, default=20)
    parser.add_argument("--out", default="runtime/.run/assist_v2_http_deploy_gate.json")
    parser.add_argument(
        "--skip-graph-preflight",
        action="store_true",
        help="Do not fail gate when graph preflight is not COMPLETE (useful for local non-graph smoke).",
    )
    args = parser.parse_args(argv)

    result: dict[str, Any]
    try:
        result = run_gate(
            plan_gate_url=args.plan_gate_url,
            timeout_s=args.timeout_s,
            require_graph_preflight=not args.skip_graph_preflight,
        )
    except urllib.error.HTTPError as exc:
        result = {
            "all_pass": False,
            "errors": [f"http error: {exc.code} {exc.reason}"],
            "checks": {},
        }
    except Exception as exc:  # pragma: no cover - defensive path
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

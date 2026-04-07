#!/usr/bin/env python3
"""Generate and run a surgical Plugin UI Truth certification pack.

This script is intentionally backend-first: it captures backend truth artifacts for
plugin-facing scenarios, then emits operator checklists for UI truth matching
(screenshot + plugin log snippet + PASS/FAIL assertion).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class HttpResult:
    status: int
    text: str
    json_obj: dict[str, Any] | None


class RunLogger:
    def __init__(self, log_path: pathlib.Path):
        self.log_path = log_path

    def info(self, message: str) -> None:
        line = f"[{now_utc_iso()}] {message}"
        print(line, flush=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def request_json(method: str, url: str, payload: dict[str, Any] | None = None, timeout: int = 60) -> HttpResult:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            obj = None
            try:
                obj = json.loads(text)
            except Exception:
                obj = None
            return HttpResult(status=resp.status, text=text, json_obj=obj)
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", errors="replace") if e.fp else ""
        obj = None
        try:
            obj = json.loads(text)
        except Exception:
            obj = None
        return HttpResult(status=e.code, text=text, json_obj=obj)
    except Exception as e:  # network/connectivity
        return HttpResult(status=-1, text=str(e), json_obj=None)


def write_json(path: pathlib.Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def short(s: str | None) -> str:
    if not s:
        return ""
    return s[:7]


def scenario_dir(base: pathlib.Path, scenario_id: str) -> pathlib.Path:
    d = base / f"scenario_{scenario_id}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def preflight(context_url: str, plan_gate_url: str, local_repo: pathlib.Path) -> dict[str, Any]:
    c_health = request_json("GET", f"{context_url}/healthz", timeout=20)
    p_health = request_json("GET", f"{plan_gate_url}/healthz", timeout=20)
    c_ver = request_json("GET", f"{context_url}/version", timeout=20)
    p_ver = request_json("GET", f"{plan_gate_url}/version", timeout=20)

    local_commit = ""
    git_cmd = f"git -C {str(local_repo)} rev-parse --short HEAD"
    local_commit = os.popen(git_cmd).read().strip()

    out = {
        "generated_utc": now_utc_iso(),
        "context_url": context_url,
        "plan_gate_url": plan_gate_url,
        "local_repo": str(local_repo),
        "local_git_commit": local_commit,
        "context_health_status": c_health.status,
        "plan_gate_health_status": p_health.status,
        "context_version": c_ver.json_obj,
        "plan_gate_version": p_ver.json_obj,
        "context_git_commit": (c_ver.json_obj or {}).get("git_commit"),
        "plan_gate_git_commit": (p_ver.json_obj or {}).get("git_commit"),
        "notes": [],
    }
    if c_health.status != 200:
        out["notes"].append("Context healthz is not 200")
    if p_health.status != 200:
        out["notes"].append("Plan-Gate healthz is not 200")
    if (p_ver.json_obj or {}).get("git_commit") and local_commit and (p_ver.json_obj or {}).get("git_commit") != local_commit:
        out["notes"].append("Plan-Gate commit differs from local repo commit")
    return out


def export_evidence(context_url: str, workspace_root: str, query: str, top_k: int, timeout: int) -> HttpResult:
    payload = {
        "workspace_root": workspace_root,
        "query": query,
        "top_k": top_k,
    }
    return request_json("POST", f"{context_url}/v1/export_evidence", payload=payload, timeout=timeout)


def ask_v1(plan_gate_url: str, query: str, evidence: dict[str, Any], timeout: int) -> tuple[dict[str, Any], HttpResult]:
    req: dict[str, Any] = {
        "schema_version": "ask_request.v1.0",
        "request_id": f"ui-cert-{uuid.uuid4()}",
        "timestamp_utc": now_utc_iso(),
        "query": query,
        "evidence_bundle": evidence,
    }
    ws_hash = evidence.get("workspace_identity_hash")
    if ws_hash:
        req["expected_workspace_identity_hash"] = ws_hash
    resp = request_json("POST", f"{plan_gate_url}/v1/ask", payload=req, timeout=timeout)
    return req, resp


def ask_v0(plan_gate_url: str, workspace_root: str, query: str, timeout: int, task_type: str | None = None) -> tuple[dict[str, Any], HttpResult]:
    req: dict[str, Any] = {
        "schema_version": "ask_request.v0.1",
        "request_id": f"ui-cert-{uuid.uuid4()}",
        "timestamp_utc": now_utc_iso(),
        "repo_root": workspace_root,
        "revision": "ui-cert",
        "query": query,
    }
    if task_type:
        req["task_type"] = task_type
    resp = request_json("POST", f"{plan_gate_url}/v0/ask", payload=req, timeout=timeout)
    return req, resp


def execute_v0(plan_gate_url: str, workspace_root: str, command: str, timeout: int) -> tuple[dict[str, Any], HttpResult]:
    req = {
        "schema_version": "execute_request.v0.1",
        "request_id": f"ui-cert-{uuid.uuid4()}",
        "timestamp_utc": now_utc_iso(),
        "repo_root": workspace_root,
        "command": command,
    }
    resp = request_json("POST", f"{plan_gate_url}/v0/execute", payload=req, timeout=timeout)
    return req, resp


def build_operator_checklist(scenario_id: str, title: str, backend_truth: dict[str, Any], expected_ui: list[str], fail_if: list[str]) -> str:
    return (
        f"# {scenario_id} — {title}\n\n"
        "## Backend Truth\n"
        f"- request_id: {backend_truth.get('request_id', '')}\n"
        f"- status: {backend_truth.get('http_status', '')}\n"
        f"- ask_path: {backend_truth.get('ask_path', '')}\n"
        f"- routing_mode: {backend_truth.get('routing_mode', '')}\n"
        f"- evidence_quality: {backend_truth.get('evidence_quality', '')}\n"
        f"- outcome: {backend_truth.get('outcome', '')}\n"
        f"- trace_id: {backend_truth.get('trace_id', '')}\n\n"
        "## Plugin Capture Required\n"
        "- screenshot_path: __________________________\n"
        "- plugin_log_snippet_path: __________________________\n"
        "- rendered_path_label: __________________________\n"
        "- rendered_evidence_or_notes_label: __________________________\n\n"
        "## Plugin Must Show\n"
        + "\n".join(f"- {item}" for item in expected_ui)
        + "\n\n## Fail If\n"
        + "\n".join(f"- {item}" for item in fail_if)
        + "\n\n## Final Mark\n"
        "- PASS / FAIL / NOT_PROVEN: __________________________\n"
        "- Operator notes: __________________________\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Plugin UI truth certification backend pack and generate pass/fail checklist artifacts.")
    parser.add_argument("--workspace-root", required=True, help="Absolute workspace root visible to Context Layer/Plan-Gate")
    parser.add_argument("--context-url", default=os.environ.get("CONTEXT_URL", "http://127.0.0.1:8091"))
    parser.add_argument("--plan-gate-url", default=os.environ.get("PLAN_GATE_URL", "http://127.0.0.1:8089"))
    parser.add_argument("--top-k", type=int, default=int(os.environ.get("TOP_K", "8")))
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--export-timeout-sec", type=int, default=int(os.environ.get("PLUGIN_UI_CERT_EXPORT_TIMEOUT_SEC", "120")))
    parser.add_argument("--ask-timeout-sec", type=int, default=int(os.environ.get("PLUGIN_UI_CERT_ASK_TIMEOUT_SEC", "180")))
    parser.add_argument("--execute-timeout-sec", type=int, default=int(os.environ.get("PLUGIN_UI_CERT_EXECUTE_TIMEOUT_SEC", "180")))
    args = parser.parse_args()

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    workspace_root = args.workspace_root

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = pathlib.Path(args.out_dir) if args.out_dir else repo_root / "docs" / "validation" / "artifacts" / f"plugin_ui_truth_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    run_log = out_dir / "run.log"
    logger = RunLogger(run_log)
    logger.info(f"artifact_root={out_dir}")
    logger.info(f"context_url={args.context_url}")
    logger.info(f"plan_gate_url={args.plan_gate_url}")
    logger.info(f"workspace_root={workspace_root}")
    logger.info(f"timeouts export={args.export_timeout_sec}s ask={args.ask_timeout_sec}s execute={args.execute_timeout_sec}s")

    logger.info("preflight: begin")
    pref = preflight(args.context_url, args.plan_gate_url, repo_root)
    write_json(out_dir / "preflight.json", pref)
    logger.info("preflight: written preflight.json")

    log_hints = {
        "local_context_log": str(repo_root / "runtime" / ".run" / "wsl_context_layer.log"),
        "local_tunnel_log": str(repo_root / "runtime" / ".run" / "wsl_plan_gate_tunnel.log"),
        "remote_plan_gate_log_hint": "~/Harshil-PoCs/m-coder/runtime/.run/plan_gate.log on TUNNEL_TARGET host",
        "remote_vllm_log_hint": "~/Harshil-PoCs/m-coder/runtime/.run/vllm.log on TUNNEL_TARGET host",
        "intellij_log_hint": "IntelliJ: Help -> Show Log in Explorer/Finder/File Manager",
        "this_run_log": str(run_log),
    }
    write_json(out_dir / "log_locations.json", log_hints)
    logger.info("preflight: written log_locations.json")

    matrix_rows: list[dict[str, Any]] = []

    # S1: v1 strong evidence
    logger.info("scenario S1: begin")
    s1_dir = scenario_dir(out_dir, "S1")
    s1_query = "How does alert correlation work in this repo?"
    s1_export = export_evidence(args.context_url, workspace_root, s1_query, args.top_k, args.export_timeout_sec)
    write_json(s1_dir / "export_response.json", {"status": s1_export.status, "body": s1_export.json_obj, "raw": s1_export.text})
    s1_req, s1_ask = ask_v1(args.plan_gate_url, s1_query, s1_export.json_obj or {}, args.ask_timeout_sec)
    write_json(s1_dir / "ask_request.json", s1_req)
    write_json(s1_dir / "ask_response.json", {"status": s1_ask.status, "body": s1_ask.json_obj, "raw": s1_ask.text})
    s1_truth = {
        "request_id": s1_req.get("request_id"),
        "http_status": s1_ask.status,
        "ask_path": ((s1_ask.json_obj or {}).get("evidence_first_meta") or {}).get("ask_path"),
        "routing_mode": (s1_ask.json_obj or {}).get("routing_mode"),
        "trace_id": (s1_ask.json_obj or {}).get("trace_id") or ((s1_ask.json_obj or {}).get("metadata") or {}).get("trace_id"),
        "evidence_quality": ((s1_ask.json_obj or {}).get("metadata") or {}).get("evidence_quality"),
    }
    write_json(s1_dir / "backend_truth.json", s1_truth)
    write_text(
        s1_dir / "operator_checklist.md",
        build_operator_checklist(
            "S1",
            "v1 ask with strong evidence",
            s1_truth,
            [
                "ask path as v1 evidence",
                "evidence list shown",
                "trace_id or routing_mode visible in UI/log",
            ],
            [
                "path is hidden or shown as default v0",
                "evidence list omitted while backend has entries",
                "confident answer shown with no grounding metadata",
            ],
        ),
    )
    matrix_rows.append({"scenario_id": "S1", "title": "v1 ask strong evidence", **s1_truth})
    logger.info(f"scenario S1: done (export={s1_export.status}, ask={s1_ask.status})")

    # S2: v0 default path
    logger.info("scenario S2: begin")
    s2_dir = scenario_dir(out_dir, "S2")
    s2_query = "How does alert correlation work in this repo?"
    s2_req, s2_resp = ask_v0(args.plan_gate_url, workspace_root, s2_query, args.ask_timeout_sec)
    write_json(s2_dir / "ask_request.json", s2_req)
    write_json(s2_dir / "ask_response.json", {"status": s2_resp.status, "body": s2_resp.json_obj, "raw": s2_resp.text})
    s2_truth = {
        "request_id": s2_req.get("request_id"),
        "http_status": s2_resp.status,
        "ask_path": ((s2_resp.json_obj or {}).get("evidence_first_meta") or {}).get("ask_path", "v0"),
        "routing_mode": (s2_resp.json_obj or {}).get("routing_mode"),
        "trace_id": (s2_resp.json_obj or {}).get("trace_id") or ((s2_resp.json_obj or {}).get("metadata") or {}).get("trace_id"),
    }
    write_json(s2_dir / "backend_truth.json", s2_truth)
    write_text(
        s2_dir / "operator_checklist.md",
        build_operator_checklist(
            "S2",
            "v0 ask default path",
            s2_truth,
            [
                "default or v0 path visible",
                "no false evidence-first claim",
            ],
            [
                "UI implies evidence-first while backend is v0",
            ],
        ),
    )
    matrix_rows.append({"scenario_id": "S2", "title": "v0 ask default", **s2_truth})
    logger.info(f"scenario S2: done (ask={s2_resp.status})")

    # S3: fallback expected (operator-induced)
    logger.info("scenario S3: begin")
    s3_dir = scenario_dir(out_dir, "S3")
    s3_query = "How does alert correlation work in this repo?"
    s3_req, s3_resp = ask_v0(args.plan_gate_url, workspace_root, s3_query, args.ask_timeout_sec)
    write_json(s3_dir / "ask_request_backend_truth_baseline.json", s3_req)
    write_json(s3_dir / "ask_response_backend_truth_baseline.json", {"status": s3_resp.status, "body": s3_resp.json_obj, "raw": s3_resp.text})
    s3_truth = {
        "request_id": s3_req.get("request_id"),
        "http_status": s3_resp.status,
        "ask_path": "v0 (fallback target)",
        "routing_mode": (s3_resp.json_obj or {}).get("routing_mode"),
        "trace_id": (s3_resp.json_obj or {}).get("trace_id") or ((s3_resp.json_obj or {}).get("metadata") or {}).get("trace_id"),
        "operator_setup": "Enable evidence-first in plugin and force context export unreachable to induce fallback visibly",
    }
    write_json(s3_dir / "backend_truth.json", s3_truth)
    write_text(
        s3_dir / "operator_checklist.md",
        build_operator_checklist(
            "S3",
            "v1 fallback to v0 (operator-induced)",
            s3_truth,
            [
                "explicit warning that fallback occurred",
                "final path shown as v0 fallback",
                "trace_id/routing marker in plugin logs",
            ],
            [
                "fallback happened but UI looks normal/silent",
                "no path visibility for fallback",
            ],
        )
        + "\n### Operator Setup Hint\n"
        "- Example induce method: start plugin with evidence-first ON while making Context Layer export provider unreachable.\n"
        "- Validate backend still reachable at Plan-Gate v0 so fallback can complete.\n",
    )
    matrix_rows.append({"scenario_id": "S3", "title": "v1 fallback to v0", **s3_truth})
    logger.info(f"scenario S3: done (ask={s3_resp.status})")

    # S4: weak evidence
    logger.info("scenario S4: begin")
    s4_dir = scenario_dir(out_dir, "S4")
    s4_query = "Which files implement topology anomaly scoring pipeline?"
    s4_export = export_evidence(args.context_url, workspace_root, s4_query, args.top_k, args.export_timeout_sec)
    write_json(s4_dir / "export_response.json", {"status": s4_export.status, "body": s4_export.json_obj, "raw": s4_export.text})
    s4_req, s4_ask = ask_v1(args.plan_gate_url, s4_query, s4_export.json_obj or {}, args.ask_timeout_sec)
    write_json(s4_dir / "ask_request.json", s4_req)
    write_json(s4_dir / "ask_response.json", {"status": s4_ask.status, "body": s4_ask.json_obj, "raw": s4_ask.text})
    s4_truth = {
        "request_id": s4_req.get("request_id"),
        "http_status": s4_ask.status,
        "ask_path": ((s4_ask.json_obj or {}).get("evidence_first_meta") or {}).get("ask_path"),
        "routing_mode": (s4_ask.json_obj or {}).get("routing_mode"),
        "trace_id": (s4_ask.json_obj or {}).get("trace_id") or ((s4_ask.json_obj or {}).get("metadata") or {}).get("trace_id"),
        "evidence_quality": ((s4_ask.json_obj or {}).get("metadata") or {}).get("evidence_quality"),
        "quality_reasons": ((s4_ask.json_obj or {}).get("metadata") or {}).get("quality_reasons"),
    }
    write_json(s4_dir / "backend_truth.json", s4_truth)
    write_text(
        s4_dir / "operator_checklist.md",
        build_operator_checklist(
            "S4",
            "weak evidence path",
            s4_truth,
            [
                "weak/insufficient caveat visible",
                "notes shown when backend returns plan_summary.notes",
            ],
            [
                "polished confident answer with no insufficiency signal",
                "notes hidden despite backend notes",
            ],
        ),
    )
    matrix_rows.append({"scenario_id": "S4", "title": "weak evidence", **s4_truth})
    logger.info(f"scenario S4: done (export={s4_export.status}, ask={s4_ask.status})")

    # S5: no-match
    logger.info("scenario S5: begin")
    s5_dir = scenario_dir(out_dir, "S5")
    s5_query = "Where is the quantum flux capacitor serializer pipeline?"
    s5_export = export_evidence(args.context_url, workspace_root, s5_query, args.top_k, args.export_timeout_sec)
    write_json(s5_dir / "export_response.json", {"status": s5_export.status, "body": s5_export.json_obj, "raw": s5_export.text})
    s5_req, s5_ask = ask_v1(args.plan_gate_url, s5_query, s5_export.json_obj or {}, args.ask_timeout_sec)
    write_json(s5_dir / "ask_request.json", s5_req)
    write_json(s5_dir / "ask_response.json", {"status": s5_ask.status, "body": s5_ask.json_obj, "raw": s5_ask.text})
    s5_truth = {
        "request_id": s5_req.get("request_id"),
        "http_status": s5_ask.status,
        "ask_path": ((s5_ask.json_obj or {}).get("evidence_first_meta") or {}).get("ask_path"),
        "routing_mode": (s5_ask.json_obj or {}).get("routing_mode"),
        "trace_id": (s5_ask.json_obj or {}).get("trace_id") or ((s5_ask.json_obj or {}).get("metadata") or {}).get("trace_id"),
        "evidence_quality": ((s5_ask.json_obj or {}).get("metadata") or {}).get("evidence_quality"),
        "quality_reasons": ((s5_ask.json_obj or {}).get("metadata") or {}).get("quality_reasons"),
    }
    write_json(s5_dir / "backend_truth.json", s5_truth)
    write_text(
        s5_dir / "operator_checklist.md",
        build_operator_checklist(
            "S5",
            "no-match honesty",
            s5_truth,
            [
                "explicit no-match or insufficiency shown",
                "no fabricated implementation-specific claim",
            ],
            [
                "invented concrete implementation answer",
                "no-match suppressed in UI",
            ],
        ),
    )
    matrix_rows.append({"scenario_id": "S5", "title": "no-match", **s5_truth})
    logger.info(f"scenario S5: done (export={s5_export.status}, ask={s5_ask.status})")

    # S6-S8 execute outcome truthfulness
    execute_cases = [
        ("S6", "execute blocked", "false", "BLOCKED"),
        ("S7", "execute refused", "curl https://example.com", "REFUSED"),
        ("S8", "execute failed after run", 'python3 -c "import sys; sys.exit(1)"', "EXECUTED_FAILED"),
    ]

    for sid, title, command, expected_outcome in execute_cases:
        logger.info(f"scenario {sid}: begin")
        sdir = scenario_dir(out_dir, sid)
        req, resp = execute_v0(args.plan_gate_url, workspace_root, command, args.execute_timeout_sec)
        write_json(sdir / "execute_request.json", req)
        write_json(sdir / "execute_response.json", {"status": resp.status, "body": resp.json_obj, "raw": resp.text})
        truth = {
            "request_id": req.get("request_id"),
            "http_status": resp.status,
            "outcome": (resp.json_obj or {}).get("outcome"),
            "expected_outcome": expected_outcome,
            "trace_id": (resp.json_obj or {}).get("trace_id") or ((resp.json_obj or {}).get("metadata") or {}).get("trace_id"),
            "reason": (resp.json_obj or {}).get("reason"),
            "executed": (resp.json_obj or {}).get("executed"),
        }
        write_json(sdir / "backend_truth.json", truth)
        write_text(
            sdir / "operator_checklist.md",
            build_operator_checklist(
                sid,
                title,
                truth,
                [
                    f"outcome label shown as {expected_outcome}",
                    "no collapsing of distinct outcomes",
                ],
                [
                    "shown as generic success",
                    "shown as generic failure without outcome class",
                ],
            ),
        )
        matrix_rows.append({"scenario_id": sid, "title": title, **truth})
        logger.info(f"scenario {sid}: done (execute={resp.status}, outcome={(resp.json_obj or {}).get('outcome')})")

    write_json(out_dir / "matrix_backend_truth.json", matrix_rows)

    matrix_md = [
        "# Plugin UI Truth Certification Matrix\n",
        f"Generated UTC: {now_utc_iso()}\n",
        f"Artifact root: {out_dir}\n",
        "\n## Scenario Table\n",
        "| ID | Scenario | Backend truth field | Plugin must show | Fail if |\n",
        "|---|---|---|---|---|\n",
        "| S1 | Strong v1 ask | ask_path=v1_evidence, evidence present | evidence list + v1 path | evidence/path hidden |\n",
        "| S2 | Default v0 ask | v0 path | v0/default path | implies evidence-first |\n",
        "| S3 | Fallback v1->v0 | fallback target path v0 | warning + explicit fallback | appears normal/silent |\n",
        "| S4 | Weak evidence | evidence_quality weak/insufficient | caveat + notes visibility | polished confidence without caveat |\n",
        "| S5 | No-match | no-match/insufficient metadata | explicit no-match/insufficiency | fabricated implementation answer |\n",
        "| S6 | Execute blocked | outcome=BLOCKED | blocked | shown as success |\n",
        "| S7 | Execute refused | outcome=REFUSED | refused | collapsed into generic failure |\n",
        "| S8 | Execute failed | outcome=EXECUTED_FAILED | failed after execution | collapsed into blocked/refused |\n",
        "\n## Operator capture requirement per scenario\n",
        "- backend JSON: already generated in each scenario folder\n",
        "- plugin visible screenshot: add path in operator_checklist.md\n",
        "- plugin log snippet with trace_id/routing_mode: add path in operator_checklist.md\n",
    ]
    write_text(out_dir / "MATRIX.md", "".join(matrix_md))

    logger.info("matrix: written MATRIX.md and matrix_backend_truth.json")
    logger.info("done: Plugin UI truth certification pack created")
    print(f"[OK] Plugin UI truth certification pack created: {out_dir}")
    print(f"[INFO] Run log: {run_log}")
    print(f"[INFO] Log locations: {out_dir / 'log_locations.json'}")
    print("[INFO] Next: execute each scenario from plugin UI and fill operator_checklist.md files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

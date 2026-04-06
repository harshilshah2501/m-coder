#!/usr/bin/env python3
"""
Run all AIOps MVP scenarios (export → ask), write artifacts, emit automated verdict summary.

Requires repo root on PYTHONPATH. Uses docs/validation/aiops_mvp_scenarios.v1.json as source of truth.

Environment:
  MOTADATA_ROOT       — required (workspace checkout)
  CONTEXT_URL         — default http://127.0.0.1:8091
  PLAN_GATE_URL       — default http://127.0.0.1:8089
  AIOPS_MVP_LIVE_HTTP_TIMEOUT — seconds for export_evidence HTTP (default 600); also default for /v1/ask unless overridden
  AIOPS_MVP_ASK_HTTP_TIMEOUT — optional; seconds for POST /v1/ask only (large body + LLM; use with SSH tunnels)
  AIOPS_MVP_ASK_RETRIES — max extra attempts when /v1/ask fails with connection/url errors (default 0); try 2–3 through flaky SSH
  AIOPS_MVP_ASK_RETRY_DELAY_SEC — delay between ask retries (default 5)
  AIOPS_MVP_VERBOSE   — if 1/true/yes, same as --verbose (progress on stderr)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_JSON = REPO_ROOT / "docs" / "validation" / "aiops_mvp_scenarios.v1.json"


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _vlog(verbose: bool, msg: str) -> None:
    """Progress to stderr so stdout stays easy to pipe; always flushed."""
    if verbose:
        print(f"[{_utc_ts()}] aiops_mvp_run_all: {msg}", file=sys.stderr, flush=True)


def _http_timeout() -> float:
    raw = (os.environ.get("AIOPS_MVP_LIVE_HTTP_TIMEOUT") or "").strip()
    if not raw:
        return 600.0
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 600.0


def _ask_http_timeout(export_timeout: float) -> float:
    """Longer ask timeouts help tunneled Plan-Gate + LLM; export stays on export_timeout."""
    raw = (os.environ.get("AIOPS_MVP_ASK_HTTP_TIMEOUT") or "").strip()
    if not raw:
        return export_timeout
    try:
        return max(1.0, float(raw))
    except ValueError:
        return export_timeout


def _ask_retry_config() -> Tuple[int, float]:
    raw_r = (os.environ.get("AIOPS_MVP_ASK_RETRIES") or "").strip()
    retries = 0
    if raw_r:
        try:
            retries = max(0, int(raw_r))
        except ValueError:
            retries = 0
    raw_d = (os.environ.get("AIOPS_MVP_ASK_RETRY_DELAY_SEC") or "").strip()
    delay = 5.0
    if raw_d:
        try:
            delay = max(0.0, float(raw_d))
        except ValueError:
            delay = 5.0
    return retries, delay


def _load_scenarios() -> Dict[str, Any]:
    with open(SCENARIOS_JSON, encoding="utf-8") as f:
        return json.load(f)


def _verdict_from_ask_response(data: Dict[str, Any]) -> Tuple[str, str]:
    """
    Automated signal (not human rubric): ERROR | FAIL | PARTIAL | PASS + reason line.
    Aligns with metadata.evidence_quality from Plan-Gate v1 ingest.
    """
    if not isinstance(data, dict):
        return "ERROR", "response_not_object"
    if data.get("schema_version") != "plan_only_response.v0.1":
        return "FAIL", "unexpected_schema_version"
    if data.get("governance_posture") != "PLAN_ONLY":
        return "FAIL", "governance_posture_not_plan_only"
    meta = data.get("metadata") or {}
    eq = str(meta.get("evidence_quality") or "")
    steps = (data.get("plan_summary") or {}).get("steps") or []
    notes = (data.get("plan_summary") or {}).get("notes") or []
    ui_title = str((data.get("ui") or {}).get("title") or "")

    if "Grounding blocked" in ui_title or (eq in ("NO_MATCH", "INSUFFICIENT") and not steps):
        return "FAIL", f"blocked_or_insufficient:{eq}"

    if eq == "NO_MATCH":
        return "FAIL", "evidence_quality:NO_MATCH"
    if eq == "INSUFFICIENT":
        return "PARTIAL", "evidence_quality:INSUFFICIENT"
    if eq == "WEAK":
        return "PARTIAL", "evidence_quality:WEAK"
    if eq == "STRONG":
        if any("WEAK" in str(n) for n in notes):
            return "PARTIAL", "notes_mention_weak"
        return "PASS", "evidence_quality:STRONG"

    return "PARTIAL", f"evidence_quality:{eq or 'unknown'}"


def _post_json(url: str, body: bytes, timeout: float) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        r = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return json.load(resp), None
    except TimeoutError as e:
        return None, f"timeout:{e}"
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")[:2000]
        except Exception:
            detail = str(e)
        return None, f"http_{e.code}:{detail}"
    except urllib.error.URLError as e:
        return None, f"urlerror:{e}"
    except ConnectionError as e:
        # e.g. ConnectionResetError while reading /v1/ask response (Plan-Gate OOM/crash, proxy drop).
        return None, f"connection:{type(e).__name__}:{e}"
    except json.JSONDecodeError as e:
        return None, f"json_decode:{e}"


def _run_one(
    scenario: Dict[str, Any],
    artifact_root: Path,
    context_url: str,
    plan_url: str,
    export_timeout: float,
    ask_timeout: float,
    ask_max_retries: int,
    ask_retry_delay: float,
    top_k: int,
    *,
    verbose: bool = False,
) -> Dict[str, Any]:
    sid = scenario["id"]
    query = scenario["query"]
    base = artifact_root / f"scenario_{sid}"
    base.mkdir(parents=True, exist_ok=True)

    workspace = (os.environ.get("MOTADATA_ROOT") or "").strip()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rid_export = f"aiops-mvp-export-{sid}-{ts}"
    rid_ask = f"aiops-mvp-{sid}-{ts}"

    (base / "request.txt").write_text(query, encoding="utf-8")

    export_req = {
        "workspace_root": workspace,
        "query": query,
        "top_k": top_k,
        "request_id": rid_export,
    }
    (base / "export_request.json").write_text(
        json.dumps(export_req, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    out: Dict[str, Any] = {
        "scenario_id": sid,
        "category": scenario.get("category"),
        "artifact_dir": str(base.relative_to(REPO_ROOT)),
    }

    if not workspace or not Path(workspace).is_dir():
        out["status"] = "ERROR"
        out["error"] = "MOTADATA_ROOT missing or not a directory"
        out["automated_verdict"] = "ERROR"
        return out

    export_url = f"{context_url}/v1/export_evidence"
    _vlog(
        verbose,
        f"{sid} POST {export_url} (request_id={rid_export}, timeout={export_timeout}s) — "
        "first export can take many minutes (cold index); Context Layer stderr shows export_evidence lines.",
    )
    bundle, err = _post_json(
        export_url,
        json.dumps(
            {
                "workspace_root": workspace,
                "query": query,
                "top_k": top_k,
                "request_id": rid_export,
            }
        ).encode("utf-8"),
        export_timeout,
    )
    if err:
        out["status"] = "ERROR"
        out["error"] = f"export:{err}"
        out["automated_verdict"] = "ERROR"
        return out

    n_ent = len(bundle.get("entries") or []) if isinstance(bundle, dict) else 0
    _vlog(verbose, f"{sid} export_evidence OK — entries={n_ent}, writing {base / 'export_response.json'}")

    (base / "export_response.json").write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    ask = {
        "schema_version": "ask_request.v1.0",
        "request_id": rid_ask,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "query": query,
        "evidence_bundle": bundle,
        "task_type": "general",
        "trace_id": rid_ask,
    }
    h = (bundle.get("workspace_identity_hash") or "").strip()
    if h:
        ask["expected_workspace_identity_hash"] = h

    (base / "ask_request.json").write_text(
        json.dumps(ask, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    ask_url = f"{plan_url}/v1/ask"
    ask_body = json.dumps(ask).encode("utf-8")
    _vlog(
        verbose,
        f"{sid} POST {ask_url} (request_id={rid_ask}, timeout={ask_timeout}s, "
        f"max_connection_retries={ask_max_retries})",
    )
    ask_resp: Optional[Dict[str, Any]] = None
    err2: Optional[str] = None
    for attempt in range(ask_max_retries + 1):
        if attempt > 0:
            _vlog(
                verbose,
                f"{sid} POST {ask_url} connection retry {attempt}/{ask_max_retries} "
                f"(delay {ask_retry_delay}s) — last_error={err2!r}",
            )
            time.sleep(ask_retry_delay)
        ask_resp, err2 = _post_json(ask_url, ask_body, ask_timeout)
        if err2 is None:
            break
        if not (err2.startswith("connection:") or err2.startswith("urlerror:")):
            break
        if attempt >= ask_max_retries:
            break
    if err2:
        out["status"] = "ERROR"
        out["error"] = f"ask:{err2}"
        out["automated_verdict"] = "ERROR"
        return out

    _vlog(verbose, f"{sid} /v1/ask OK — writing {base / 'ask_response.json'}")

    (base / "ask_response.json").write_text(
        json.dumps(ask_resp, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    verdict, reason = _verdict_from_ask_response(ask_resp)
    out["status"] = "ok"
    out["automated_verdict"] = verdict
    out["verdict_reason"] = reason
    meta = ask_resp.get("metadata") or {}
    out["evidence_quality"] = meta.get("evidence_quality")
    out["quality_reasons"] = list(meta.get("quality_reasons") or [])
    return out


def _write_summary_md(rows: List[Dict[str, Any]], summary_dir: Path, counts: Dict[str, int]) -> None:
    lines = [
        "# AIOps MVP batch run summary",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        "## Automated counts (machine signal, not full rubric)",
        "",
        f"| Verdict | Count |",
        f"|---------|-------|",
    ]
    for k in ("PASS", "PARTIAL", "FAIL", "ERROR"):
        lines.append(f"| {k} | {counts.get(k, 0)} |")
    lines.extend(
        [
            "",
            "Use `judgement.txt` per scenario and **AIOPS_MVP_FINAL_REPORT_TEMPLATE.md** for human PASS/PARTIAL/FAIL.",
            "",
            "## Per scenario",
            "",
            "| ID | Category | Automated verdict | Evidence quality | Reason |",
            "|----|----------|-------------------|------------------|--------|",
        ]
    )
    for r in rows:
        lines.append(
            f"| {r.get('scenario_id','')} | {r.get('category','')} | {r.get('automated_verdict','')} | "
            f"{r.get('evidence_quality','')} | {r.get('verdict_reason') or r.get('error', '')} |"
        )
    summary_dir.mkdir(parents=True, exist_ok=True)
    (summary_dir / "run_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Run full AIOps MVP scenario pack (HTTP export + ask).")
    ap.add_argument(
        "--artifact-root",
        type=Path,
        default=REPO_ROOT / "docs" / "validation" / "artifacts" / "aiops_mvp",
        help="Directory for scenario_A1, scenario_A2, ... and summary/",
    )
    ap.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first ERROR.",
    )
    ap.add_argument(
        "--scenario",
        action="append",
        help="Run only this scenario id (repeatable), e.g. --scenario A1",
    )
    ap.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Log each HTTP phase to stderr (timestamps; use during long export). "
        "Or set AIOPS_MVP_VERBOSE=1.",
    )
    args = ap.parse_args()
    verbose = bool(args.verbose or (os.environ.get("AIOPS_MVP_VERBOSE", "").strip() in ("1", "true", "yes")))

    artifact_root = args.artifact_root
    if not artifact_root.is_absolute():
        artifact_root = (REPO_ROOT / artifact_root).resolve()

    context_url = os.environ.get("CONTEXT_URL", "http://127.0.0.1:8091").rstrip("/")
    plan_url = os.environ.get("PLAN_GATE_URL", "http://127.0.0.1:8089").rstrip("/")
    export_timeout = _http_timeout()
    ask_timeout = _ask_http_timeout(export_timeout)
    ask_max_retries, ask_retry_delay = _ask_retry_config()

    doc = _load_scenarios()
    top_k = int(doc.get("top_k_default") or 12)
    scenarios: List[Dict[str, Any]] = list(doc["scenarios"])
    if args.scenario:
        want = set(args.scenario)
        scenarios = [s for s in scenarios if s["id"] in want]
        missing = want - {s["id"] for s in scenarios}
        if missing:
            print(f"Unknown scenario id(s): {sorted(missing)}", file=sys.stderr)
            return 2

    if verbose:
        root = (os.environ.get("MOTADATA_ROOT") or "").strip()
        _vlog(
            True,
            f"start scenarios={len(scenarios)} CONTEXT_URL={context_url} PLAN_GATE_URL={plan_url} "
            f"export_timeout={export_timeout}s ask_timeout={ask_timeout}s "
            f"ask_max_retries={ask_max_retries} MOTADATA_ROOT={root or '(unset)'} artifact_root={artifact_root}",
        )

    rows: List[Dict[str, Any]] = []
    for s in scenarios:
        row = _run_one(
            s,
            artifact_root,
            context_url,
            plan_url,
            export_timeout,
            ask_timeout,
            ask_max_retries,
            ask_retry_delay,
            top_k,
            verbose=verbose,
        )
        rows.append(row)
        v = row.get("automated_verdict", "?")
        e = row.get("error", "")
        print(f"{s['id']}: {row.get('status')} automated={v} {e or row.get('verdict_reason', '')}")
        if args.fail_fast and row.get("automated_verdict") == "ERROR":
            break

    counts = {"PASS": 0, "PARTIAL": 0, "FAIL": 0, "ERROR": 0}
    for r in rows:
        v = r.get("automated_verdict", "ERROR")
        counts[v] = counts.get(v, 0) + 1

    summary_dir = artifact_root / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / "run_summary.json"
    payload = {
        "schema_version": "aiops_mvp_batch_run.v1",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "context_url": context_url,
        "plan_gate_url": plan_url,
        "http_timeout_seconds": export_timeout,
        "ask_http_timeout_seconds": ask_timeout,
        "ask_max_connection_retries": ask_max_retries,
        "ask_retry_delay_seconds": ask_retry_delay,
        "motadata_root": (os.environ.get("MOTADATA_ROOT") or "").strip(),
        "counts": counts,
        "scenarios": rows,
        "note": "Automated verdict uses Plan-Gate metadata.evidence_quality; human rubric is in AIOPS_MVP_SCENARIO_PACK.md (Rubric section).",
    }
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _write_summary_md(rows, summary_dir, counts)

    print(f"\nWrote {summary_path}")
    print(f"Wrote {summary_dir / 'run_summary.md'}")

    if any(r.get("automated_verdict") == "ERROR" for r in rows):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

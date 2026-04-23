#!/usr/bin/env python3
"""
Behavior verification for Motadata AIOps workspace.

Validates these capabilities through live endpoints:
  - query   (export_evidence + /v1/ask)
  - debug   (/v1/ask with EXPLAIN_DEBUG)
  - plan    (/v0/plan contract)
  - code    (/v0/execute contract)
  - agent   (no dedicated /v0/agent route; assist metadata on ask)

Stdout modes:
  - concise: short pass/fail + clipped answers
  - dev: full plan steps, context_bundle files, evidence snippet previews
  - plain: readable report for any audience (uses docs/validation/motadata_aiops_behavior_scenario_plain_language.v1.json when present)
  - json: full report JSON

Optional --scenarios FILE runs contract JSON scenarios (see docs/validation/).

Optional --scenario-id ID (repeatable) runs only matching scenario rows from --scenarios (see MCODER_USER_SCENARIOS_GUIDE.md).

Environment: MOTADATA_VERIFY_EXECUTE_REPO_ROOT — if set, used as repo_root for POST /v0/execute (smoke + code scenario) when Plan-Gate runs on a different host than --workspace-root.

Optional --utility-scenarios FILE runs developer-utility scenarios (motadata_developer_utility_scenarios.v1).

Exits non-zero on any failed check.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import textwrap
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Optional


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _execute_repo_root_for_plan_gate(workspace_root: str) -> str:
    """
    Plan-Gate POST /v0/execute resolves repo_root on the machine where Plan-Gate runs.
    When the verifier runs on a workspace host (e.g. WSL) but Plan-Gate is remote (e.g. GPU
    via SSH tunnel), workspace_root may not exist on the Plan-Gate host and execute returns
    BLOCKED. Set MOTADATA_VERIFY_EXECUTE_REPO_ROOT to an absolute path that exists on the
    Plan-Gate host (e.g. the Motadata checkout path there, or a temp dir for echo probes).
    """
    o = os.environ.get("MOTADATA_VERIFY_EXECUTE_REPO_ROOT", "").strip()
    return o if o else workspace_root


def _post(
    url: str,
    payload: dict[str, Any],
    timeout: int = 180,
    *,
    raise_for_status: bool = True,
) -> tuple[int, dict[str, Any]]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if not raise_for_status:
            try:
                parsed = json.loads(body)
                if isinstance(parsed, dict):
                    return exc.code, parsed
            except Exception:
                pass
            return exc.code, {}
        detail = body
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                detail = str(parsed.get("message") or parsed.get("error") or body)[:2000]
        except Exception:
            detail = body[:2000]
        raise RuntimeError(f"HTTP {exc.code} POST {url}\n{detail}") from None


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


def _evidence_snippet_previews(entries: list[dict[str, Any]], max_entries: int = 8, max_chars: int = 600) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for e in entries[:max_entries]:
        sp = e.get("snippet") if isinstance(e.get("snippet"), dict) else {}
        txt = sp.get("text") if isinstance(sp, dict) else None
        if not isinstance(txt, str):
            txt = ""
        out.append(
            {
                "relative_path": e.get("relative_path"),
                "preview": _clip(txt.replace("\n", " "), max_chars),
            }
        )
    return out


def _context_paths_match_selected(context_paths: list[str], selected_file: str) -> bool:
    """True when context bundle lists a file path consistent with the scenario selected_file."""
    sel = (selected_file or "").replace("\\", "/").strip()
    if not sel:
        return False
    base = sel.split("/")[-1].lower()
    s_low = sel.lower()
    for p in context_paths:
        pl = str(p).replace("\\", "/").lower()
        if not pl:
            continue
        if s_low in pl or pl.endswith(base):
            return True
    return False


def _context_bundle_files(ask_resp: dict[str, Any]) -> list[dict[str, Any]]:
    cb = ask_resp.get("context_bundle") if isinstance(ask_resp.get("context_bundle"), dict) else {}
    files = cb.get("files") if isinstance(cb.get("files"), list) else []
    rows: list[dict[str, Any]] = []
    for f in files:
        if not isinstance(f, dict):
            continue
        rows.append({"path": f.get("path"), "selection_reason": f.get("selection_reason")})
    return rows


def _is_generic_infra_path(path: str) -> bool:
    """
    Keep verifier generic-infra accounting aligned with Stage-B fusion caps.
    """
    from runtime.layer5.retrieval.policy import classify_file, is_support_style_java_basename

    p = str(path or "").lower()
    if not p:
        return False
    pol = classify_file(p)
    if pol.file_class == "config":
        return True
    if any(tok in p for tok in ("/api/", "/db/", "/notification/", "/cache/", "/integration/", "/manager/")):
        return True
    base = p.rsplit("/", 1)[-1]
    return bool(is_support_style_java_basename(base))


def _compute_retrieval_metrics(evidence: dict[str, Any], top_k: int = 8) -> dict[str, Any]:
    entries = evidence.get("entries") if isinstance(evidence.get("entries"), list) else []
    rows = [e for e in entries if isinstance(e, dict)][: max(1, top_k)]
    n = len(rows)
    if n == 0:
        return {
            "top_k_size": 0,
            "distractor_count_at_k": 0,
            "generic_infra_count_at_k": 0,
            "generic_infra_ratio": 0.0,
            "owner_in_top1": False,
            "owner_in_top3": False,
            "anchor_hit_rate_at_k": 0.0,
            # Backward-compatible aliases:
            "distractor_count_top_k": 0,
            "generic_infra_count_top_k": 0,
            "generic_infra_ratio_top_k": 0.0,
            "anchor_hit_rate_top_k": 0.0,
        }

    paths = [str(r.get("relative_path") or "") for r in rows]
    roles = [str(r.get("retrieval_role") or "") for r in rows]
    snippets = [r.get("snippet") if isinstance(r.get("snippet"), dict) else {} for r in rows]
    reasons = [str(s.get("selection_reason") or "") for s in snippets]

    distractor = sum(1 for role in roles if role == "DISTRACTOR_RISK")
    generic = sum(1 for p in paths if _is_generic_infra_path(p))
    anchor_hits = sum(1 for r in reasons if r == "query_token_substring_anchor")

    owner_file = ""
    ar = evidence.get("authority_resolution")
    if isinstance(ar, dict):
        po = ar.get("primary_owner") if isinstance(ar.get("primary_owner"), dict) else {}
        owner_file = str(po.get("file") or "")
    fd0 = evidence.get("fusion_diagnostics") if isinstance(evidence.get("fusion_diagnostics"), dict) else {}
    sa0 = fd0.get("stage_a_meta") if isinstance(fd0.get("stage_a_meta"), dict) else {}
    tr0 = sa0.get("authority_owner_trace") if isinstance(sa0.get("authority_owner_trace"), dict) else {}
    rp0 = str(tr0.get("resolved_path") or "").strip()
    if rp0:
        owner_file = rp0

    from runtime.layer5.retrieval.path_resolve import paths_match_workspace

    owner_in_top1 = bool(owner_file and paths and paths_match_workspace(owner_file, paths[0]))
    owner_in_top3 = bool(
        owner_file and any(paths_match_workspace(owner_file, p) for p in paths[:3])
    )

    return {
        "top_k_size": n,
        "distractor_count_at_k": distractor,
        "generic_infra_count_at_k": generic,
        "generic_infra_ratio": round(generic / n, 4),
        "owner_in_top1": owner_in_top1,
        "owner_in_top3": owner_in_top3,
        "anchor_hit_rate_at_k": round(anchor_hits / n, 4),
        # Backward-compatible aliases:
        "distractor_count_top_k": distractor,
        "generic_infra_count_top_k": generic,
        "generic_infra_ratio_top_k": round(generic / n, 4),
        "anchor_hit_rate_top_k": round(anchor_hits / n, 4),
    }


def _stage_a_summary_from_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    """
    Compact Stage A v2 snapshot from `fusion_diagnostics.stage_a_meta` on evidence_bundle.
    """
    fd = evidence.get("fusion_diagnostics") if isinstance(evidence.get("fusion_diagnostics"), dict) else {}
    sa = fd.get("stage_a_meta") if isinstance(fd.get("stage_a_meta"), dict) else None
    if not sa:
        return {}
    cands = sa.get("candidates") if isinstance(sa.get("candidates"), list) else []
    lane_counts: dict[str, int] = {}
    for c in cands:
        if not isinstance(c, dict):
            continue
        lane = str(c.get("lane") or "")
        lane_counts[lane] = lane_counts.get(lane, 0) + 1
    pool_paths = [str(c.get("path") or "") for c in cands if isinstance(c, dict)]
    out = {
        "pool_size": sa.get("pool_size"),
        "quotas": sa.get("quotas"),
        "task_type": sa.get("task_type"),
        "debug": sa.get("debug"),
        "lane_counts": lane_counts,
        "pool_paths": pool_paths,
    }
    if isinstance(sa.get("authority_owner_trace"), dict):
        out["authority_owner_trace"] = sa.get("authority_owner_trace")
    return out


def _export_stage_a_from_arg(choice: str) -> Optional[bool]:
    """CLI --export-stage-a: default = server/env; on/off = force Stage A for export_evidence only."""
    if choice == "default":
        return None
    return choice == "on"


def _export_evidence_payload(
    workspace_root: str,
    query: str,
    top_k: int,
    *,
    task_type: str = "general",
    selected_file: str | None = None,
    active_file: str | None = None,
    enable_stage_a_v2: Optional[bool] = None,
) -> dict[str, Any]:
    p: dict[str, Any] = {
        "workspace_root": workspace_root,
        "query": query,
        "top_k": top_k,
        "task_type": str(task_type or "general"),
    }
    if selected_file:
        p["selected_file"] = str(selected_file)
    if active_file:
        p["active_file"] = str(active_file)
    if enable_stage_a_v2 is not None:
        p["enable_stage_a_v2"] = enable_stage_a_v2
    return p


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
            "request_id": query.get("request_id"),
            "trace_id": query.get("trace_id"),
            "ask_path": query.get("ask_path"),
            "evidence_quality": query.get("evidence_quality"),
            "quality_reasons": query.get("quality_reasons") or [],
            "answer_steps": query.get("answer_steps") or [],
            "notes": query.get("answer_notes") or [],
            "top_paths": export.get("top_paths") or [],
            "context_bundle_files": query.get("context_bundle_files") or [],
            "evidence_snippet_previews": query.get("evidence_snippet_previews") or [],
            "retrieval_metrics": query.get("retrieval_metrics") or {},
            "stage_a": query.get("stage_a") or export.get("stage_a") or {},
        },
        "debug": {
            "pass": debug.get("pass", False),
            "routing_mode": debug.get("routing_mode"),
            "summary": debug.get("summary"),
            "likely_bug_risk": debug.get("likely_bug_risk"),
            "logic_flow": debug.get("logic_flow"),
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


def _m_coder_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_plain_language_json_path() -> Path:
    return _m_coder_repo_root() / "docs/validation/motadata_aiops_behavior_scenario_plain_language.v1.json"


def _resolve_plain_language_path(cli_arg: str) -> tuple[Optional[Path], Optional[str]]:
    """
    Returns (path, error). If cli_arg is set, file must exist.
    If empty, auto-use repo default file when present; otherwise None (fallback narratives only).
    """
    s = str(cli_arg).strip()
    if s:
        p = Path(s).expanduser()
        if not p.is_file():
            return None, f"plain-language file not found: {p}"
        return p, None
    auto = _default_plain_language_json_path()
    return (auto, None) if auto.is_file() else (None, None)


def _load_plain_narratives_file(path: Path) -> dict[str, dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "motadata_aiops_behavior_scenario_plain_language.v1":
        raise ValueError(
            f"unsupported plain_language schema_version: {data.get('schema_version')!r} "
            "(expected motadata_aiops_behavior_scenario_plain_language.v1)"
        )
    raw = data.get("narratives") if isinstance(data.get("narratives"), dict) else {}
    out: dict[str, dict[str, str]] = {}
    for sid, block in raw.items():
        if not isinstance(block, dict):
            continue
        out[str(sid)] = {str(k): str(v) for k, v in block.items() if isinstance(v, str)}
    return out


def _fallback_plain_narrative(result: dict[str, Any]) -> dict[str, str]:
    sid = str(result.get("id") or "unknown")
    cap = str(result.get("capability") or "unknown")
    desc = str(result.get("description") or "").strip()
    return {
        "title": f"Check: {sid}",
        "in_plain_english": desc
        or f"This step checks that the “{cap}” capability responds the way the scenario contract describes.",
        "what_pass_means": "The live system matched every expectation for this check.",
        "what_failure_usually_means": "Something in the stack, policy, or workspace did not match the contract; see the error list or run with --print dev for technical detail.",
    }


def _plain_narrative_for_result(
    result: dict[str, Any],
    narratives_by_id: dict[str, dict[str, str]],
) -> dict[str, str]:
    sid = str(result.get("id") or "")
    base = _fallback_plain_narrative(result)
    extra = narratives_by_id.get(sid) or {}
    merged = {**base, **extra}
    for k in ("title", "in_plain_english", "what_pass_means", "what_failure_usually_means"):
        merged.setdefault(k, base.get(k, ""))
    return merged


def _enrich_scenario_suite_with_plain_language(
    suite: dict[str, Any],
    narratives_by_id: dict[str, dict[str, str]],
    *,
    source: str,
) -> None:
    suite["plain_language_source"] = source
    for r in suite.get("results") or []:
        if not isinstance(r, dict):
            continue
        r["plain_language"] = _plain_narrative_for_result(r, narratives_by_id)


def _print_plain_smoke_intro(
    smoke: dict[str, Any] | None,
    *,
    workspace_root: str,
) -> None:
    if not smoke:
        return
    repeat = int(smoke.get("repeat") or 1)
    stable = bool(smoke.get("stable"))
    all_pass = bool(smoke.get("all_pass"))
    runs = smoke.get("runs") or []
    verdict = "All quick checks passed." if all_pass else "At least one quick check did not pass."
    stab = (
        "Both runs behaved the same way (stable)."
        if stable and repeat > 1
        else ("Only one run was requested." if repeat <= 1 else "Runs differed slightly — review details if you need repeatability.")
    )
    print("")
    print("  Quick system check (sample run through Ask, Debug, Plan, Code, Agent)")
    print("  " + "-" * 72)
    for line in textwrap.fill(
        f"We exercised the live services using your workspace at {workspace_root}. "
        f"We ran this end-to-end sequence {repeat} time(s). {stab} "
        f"{verdict}",
        width=76,
    ).splitlines():
        print(f"  {line}")
    print("")
    for idx, run in enumerate(runs, start=1):
        s = run.get("summary") or {}
        q = s.get("query") or {}
        d = s.get("debug") or {}
        p = s.get("plan") or {}
        c = s.get("code") or {}
        a = s.get("agent") or {}
        rp = "passed" if s.get("pass") else "did not pass"
        print(f"  Run {idx} — overall this lap {rp}.")
        for line in textwrap.fill(
            f"Questions from your repo (Ask): {'ok' if q.get('pass') else 'issue'}. "
            f"Structured code explanation (Debug): {'ok' if d.get('pass') else 'issue'}. "
            f"Policy planning (Plan): {'ok' if p.get('pass') else 'issue'}. "
            f"Safe command (Code): {'ok' if c.get('pass') else 'issue'}. "
            f"Agent route rules: {'ok' if a.get('pass') else 'issue'}.",
            width=76,
        ).splitlines():
            print(f"  {line}")
        print("")


def _print_plain_scenario_section(suite: dict[str, Any]) -> None:
    print("")
    print("  Scenario checks (pinned, repeatable tests)")
    print("  " + "-" * 72)
    for line in textwrap.fill(
        "Each item below is a named test with a plain-English meaning. "
        "PASS means the live system matched the contract. FAIL means something must be fixed or configured "
        "(for example services down, policy mismatch, or split-host execute paths).",
        width=76,
    ).splitlines():
        print(f"  {line}")
    print("")
    for r in suite.get("results") or []:
        if not isinstance(r, dict):
            continue
        st = "PASS" if r.get("pass") else "FAIL"
        pl = r.get("plain_language") if isinstance(r.get("plain_language"), dict) else {}
        title = str(pl.get("title") or r.get("id") or "scenario")
        body = str(pl.get("in_plain_english") or "")
        ok_mean = str(pl.get("what_pass_means") or "")
        bad_mean = str(pl.get("what_failure_usually_means") or "")
        print(f"  [{st}] {title}")
        print(f"       id: {r.get('id')}  ({r.get('capability')})")
        if body:
            for line in textwrap.wrap(body, width=74):
                print(f"       {line}")
        if r.get("pass"):
            if ok_mean:
                for line in textwrap.wrap(f"When it passes: {ok_mean}", width=74):
                    print(f"       {line}")
        else:
            errs = r.get("errors") or []
            if errs:
                print("       What went wrong (technical):")
                for e in errs[:6]:
                    for line in textwrap.wrap(str(e), width=74):
                        print(f"       · {line}")
                if len(errs) > 6:
                    print(f"       · … and {len(errs) - 6} more")
            if bad_mean:
                for line in textwrap.wrap(f"Typical causes: {bad_mean}", width=74):
                    print(f"       {line}")
        print("")


def _print_plain_utility_section(suite: dict[str, Any]) -> None:
    print("")
    print("  Optional developer utility checks")
    print("  " + "-" * 72)
    for line in textwrap.fill(
        "These are extra heuristics for developers. They do not change the main product verdict unless you rely on them.",
        width=76,
    ).splitlines():
        print(f"  {line}")
    print("")
    ap = "PASS" if suite.get("all_pass") else "FAIL"
    print(f"  Overall utility suite: {ap}")
    for r in suite.get("results") or []:
        if not isinstance(r, dict):
            continue
        st = "PASS" if r.get("pass") else "FAIL"
        print(f"  [{st}] {r.get('id')} — {r.get('description') or ''}".rstrip())
        if r.get("errors"):
            for e in (r.get("errors") or [])[:3]:
                print(f"       {e}")
    print("")


def _print_plain_report(
    final: dict[str, Any],
    *,
    workspace_root: str,
    out_path: Path,
    scenarios_only: bool,
) -> None:
    print("")
    print("=" * 80)
    print("  MOTADATA AI ASSISTANT — READABLE VERIFICATION REPORT")
    print("=" * 80)
    print("")
    for line in textwrap.fill(
        "This summary is meant for anyone reading the terminal: operators, reviewers, or teammates "
        "who do not work with JSON every day. A machine-readable copy is still saved to a file at the end.",
        width=78,
    ).splitlines():
        print(f"  {line}")
    print("")
    overall = "PASSED — everything in this run matched expectations." if final.get("all_pass") else (
        "FAILED — at least one check needs attention before you treat the stack as fully healthy."
    )
    print(f"  Overall: {overall}")
    print(f"  Workspace: {workspace_root}")
    if not scenarios_only:
        _print_plain_smoke_intro(final.get("smoke"), workspace_root=workspace_root)
    if final.get("scenario_suite"):
        _print_plain_scenario_section(final["scenario_suite"])
    if final.get("developer_utility_suite"):
        _print_plain_utility_section(final["developer_utility_suite"])
    src = (final.get("scenario_suite") or {}).get("plain_language_source")
    if src:
        print("  Narrative text source:", src)
    print("")
    print("-" * 80)
    print(f"  Full detail (JSON): {out_path}")
    print("  For developers: re-run with --print dev to see requests, evidence, and raw fields.")
    print("-" * 80)
    print("")


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
        rm = q.get("retrieval_metrics") if isinstance(q.get("retrieval_metrics"), dict) else {}
        if rm:
            print(
                "  retrieval_metrics: "
                f"distractor_count@k={rm.get('distractor_count_at_k')} "
                f"generic_infra_ratio={rm.get('generic_infra_ratio')} "
                f"owner@1={rm.get('owner_in_top1')} owner@3={rm.get('owner_in_top3')} "
                f"anchor_hit_rate={rm.get('anchor_hit_rate_at_k')}"
            )
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


def _print_dev(final: dict[str, Any]) -> None:
    print("")
    print("=== Motadata Developer View (full query answer + evidence) ===")
    print(f"workspace: {final.get('workspace_root')}")
    print(f"repeat: {final.get('repeat')}  stable: {final.get('stable')}  all_pass: {final.get('all_pass')}")
    print("")
    for idx, run in enumerate(final.get("runs") or [], start=1):
        s = run.get("summary") or {}
        q = s.get("query") or {}
        print(f"{'=' * 60}")
        print(f"[run {idx}] smoke pass={s.get('pass')}")
        print(f"request_id: {q.get('request_id')}")
        print(f"trace_id: {q.get('trace_id')}")
        print("")
        print("--- Ask response (where the product answers your query) ---")
        print(f"governance_posture: PLAN_ONLY (implicit) | ask_path: {q.get('ask_path')}")
        print(f"evidence_quality: {q.get('evidence_quality')}  reasons: {q.get('quality_reasons')}")
        rm = q.get("retrieval_metrics") if isinstance(q.get("retrieval_metrics"), dict) else {}
        if rm:
            print(
                "retrieval_metrics: "
                f"distractor_count@k={rm.get('distractor_count_at_k')} "
                f"generic_infra_ratio={rm.get('generic_infra_ratio')} "
                f"owner@1={rm.get('owner_in_top1')} owner@3={rm.get('owner_in_top3')} "
                f"anchor_hit_rate={rm.get('anchor_hit_rate_at_k')}"
            )
        print("")
        print("plan_summary.steps (full — this is the grounded answer text):")
        for i, step in enumerate(q.get("answer_steps") or [], start=1):
            print(f"  {i}. {step}")
        if q.get("notes"):
            print("plan_summary.notes:")
            for n in q.get("notes") or []:
                print(f"  - {n}")
        print("")
        print("context_bundle.files (what the planner attached as context):")
        for row in q.get("context_bundle_files") or []:
            print(f"  - {row.get('path')}")
            print(f"    reason: {row.get('selection_reason')}")
        print("")
        print("Evidence bundle snippets (retrieval previews):")
        for row in q.get("evidence_snippet_previews") or []:
            print(f"  - {row.get('relative_path')}")
            print(f"    {row.get('preview')}")
        print("")
        d = s.get("debug") or {}
        print("--- EXPLAIN_DEBUG (separate call; not the same as the ask query above) ---")
        print(f"routing_mode: {d.get('routing_mode')}")
        if d.get("summary"):
            print(f"summary:\n{d.get('summary')}")
        if d.get("logic_flow"):
            print(f"logic_flow:\n{d.get('logic_flow')}")
        if d.get("likely_bug_risk"):
            print(f"likely_bug_risk:\n{d.get('likely_bug_risk')}")
        if d.get("error"):
            print(f"error: {d.get('error')}")
        print("")
        p = s.get("plan") or {}
        c = s.get("code") or {}
        a = s.get("agent") or {}
        print("--- /v0/plan (policy) ---")
        print(f"decision: {p.get('decision')}")
        print("")
        print("--- /v0/execute (governed code path) ---")
        print(f"outcome: {c.get('outcome')}  executed: {c.get('executed')}  posture: {c.get('posture')}")
        print("")
        print("--- agent semantics ---")
        print(f"assist_layer on ask: {a.get('assist_layer_present_in_ask')}  /v0/agent 404: {a.get('agent_route_404')}")
        print("")


def _print_utility_scenario_results(suite: dict[str, Any], *, dev: bool = False) -> None:
    print("")
    print("=== Developer utility suite (usefulness / heuristic) ===")
    print(f"file: {suite.get('file')}")
    if suite.get("utility_note"):
        print(f"note: {suite.get('utility_note')}")
    print(f"all_pass: {suite.get('all_pass')}")
    print("")
    for r in suite.get("results") or []:
        st = "PASS" if r.get("pass") else "FAIL"
        print(f"[{st}] {r.get('id')} ({r.get('capability')})")
        if r.get("description"):
            print(f"  description: {r.get('description')}")
        if r.get("errors"):
            for e in r.get("errors") or []:
                print(f"  utility_error: {e}")
        if dev and r.get("developer_snapshot"):
            ds = r.get("developer_snapshot") or {}
            clip = json.dumps(ds, indent=2, default=str)
            print(f"  developer_snapshot: {clip[:3500]}{'...' if len(clip) > 3500 else ''}")
        print("")


def _print_scenario_results(suite: dict[str, Any], *, dev: bool = False) -> None:
    print("")
    print("=== Scenario suite (expected vs actual) ===")
    print(f"file: {suite.get('file')}")
    print(f"all_pass: {suite.get('all_pass')}")
    print("")
    for r in suite.get("results") or []:
        st = "PASS" if r.get("pass") else "FAIL"
        print(f"[{st}] {r.get('id')} ({r.get('capability')})")
        if r.get("description"):
            print(f"  description: {r.get('description')}")
        if r.get("errors"):
            for e in r.get("errors") or []:
                print(f"  error: {e}")
        if r.get("expect"):
            clip = 2000 if dev else 500
            exp_s = json.dumps(r.get("expect"), sort_keys=True)
            print(f"  expect: {exp_s[:clip]}{'...' if len(exp_s) > clip else ''}")
        if r.get("actual_summary"):
            print(f"  actual: {r.get('actual_summary')}")
        if dev and r.get("dev_snapshot"):
            ds = r.get("dev_snapshot") or {}
            cap = r.get("capability")
            if cap == "ask":
                print("  --- dev: plan_summary.steps ---")
                for i, step in enumerate(ds.get("answer_steps") or [], start=1):
                    print(f"    {i}. {step}")
                print("  --- dev: context_bundle.files ---")
                for row in ds.get("context_bundle_files") or []:
                    print(f"    - {row.get('path')}")
                sa = ds.get("stage_a") if isinstance(ds.get("stage_a"), dict) else {}
                if sa:
                    print("  --- dev: Stage A (fusion_diagnostics.stage_a_meta) ---")
                    lc = sa.get("lane_counts") or {}
                    print(f"    lane_counts: {lc}")
                    pp = sa.get("pool_paths") or []
                    if isinstance(pp, list) and pp:
                        print("    pool_paths (Stage A pre-fusion pool, ordered):")
                        for p in pp[:24]:
                            print(f"      - {p}")
                        if len(pp) > 24:
                            print(f"      ... ({len(pp)} total)")
                print("  --- dev: evidence previews ---")
                for row in ds.get("evidence_snippet_previews") or []:
                    print(f"    - {row.get('relative_path')}")
                    print(f"      {row.get('preview')}")
            elif cap == "debug":
                print("  --- dev: EXPLAIN_DEBUG ---")
                if ds.get("summary"):
                    print(f"    summary:\n{ds.get('summary')}")
                if ds.get("logic_flow"):
                    print(f"    logic_flow:\n{ds.get('logic_flow')}")
                if ds.get("likely_bug_risk"):
                    print(f"    likely_bug_risk:\n{ds.get('likely_bug_risk')}")
                if ds.get("error"):
                    print(f"    error: {ds.get('error')}")
        print("")


def run_once(
    workspace_root: str,
    context_url: str,
    plan_gate_url: str,
    vllm_url: str,
    query: str,
    debug_query: str,
    top_k: int,
    *,
    export_stage_a: Optional[bool] = None,
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
        _export_evidence_payload(workspace_root, query, top_k, enable_stage_a_v2=export_stage_a),
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
        "retrieval_metrics": _compute_retrieval_metrics(evidence, top_k=top_k),
        "stage_a": _stage_a_summary_from_evidence(evidence),
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
    query_meta = ask_query_resp.get("metadata") if isinstance(ask_query_resp.get("metadata"), dict) else {}
    plan_steps = ((ask_query_resp.get("plan_summary") or {}).get("steps") or []) if isinstance(ask_query_resp.get("plan_summary"), dict) else []
    cb_files = _context_bundle_files(ask_query_resp)
    snip_previews = _evidence_snippet_previews([e for e in entries if isinstance(e, dict)])
    checks["query"] = {
        "pass": (
            code == 200
            and (ask_query_resp.get("evidence_first_meta") or {}).get("ask_path") == "v1_evidence"
            and ask_query_resp.get("governance_posture") == "PLAN_ONLY"
            and ask_query_resp.get("execution") is False
            and len(plan_steps) > 0
        ),
        "http": code,
        "request_id": ask_query_resp.get("request_id"),
        "trace_id": ask_query_resp.get("trace_id") or query_meta.get("trace_id"),
        "ask_path": (ask_query_resp.get("evidence_first_meta") or {}).get("ask_path"),
        "governance_posture": ask_query_resp.get("governance_posture"),
        "execution": ask_query_resp.get("execution"),
        "evidence_quality": query_meta.get("evidence_quality"),
        "quality_reasons": query_meta.get("quality_reasons"),
        "steps_count": len(plan_steps),
        "assist_layer_present": "assist_layer" in ask_query_resp,
        "answer_steps": plan_steps,
        "answer_notes": ((ask_query_resp.get("plan_summary") or {}).get("notes") or []),
        "context_bundle_files": cb_files,
        "evidence_snippet_previews": snip_previews,
        "retrieval_metrics": _compute_retrieval_metrics(evidence, top_k=top_k),
        "stage_a": _stage_a_summary_from_evidence(evidence),
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
    explain_debug = ask_debug_resp.get("explain_debug") if isinstance(ask_debug_resp.get("explain_debug"), dict) else {}
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
        "logic_flow": explain_debug.get("logic_flow") if isinstance(explain_debug, dict) else None,
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
        "repo_root": _execute_repo_root_for_plan_gate(workspace_root),
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

    code_agent, _ = _post(
        f"{plan_gate_url}/v0/agent",
        {"request_id": "agent-probe"},
        timeout=20,
        raise_for_status=False,
    )
    no_agent_route = code_agent == 404
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
        "query_distractor_count_at_k": ((checks.get("query") or {}).get("retrieval_metrics") or {}).get("distractor_count_at_k"),
        "query_generic_infra_ratio": ((checks.get("query") or {}).get("retrieval_metrics") or {}).get("generic_infra_ratio"),
        "query_owner_in_top1": ((checks.get("query") or {}).get("retrieval_metrics") or {}).get("owner_in_top1"),
        "query_owner_in_top3": ((checks.get("query") or {}).get("retrieval_metrics") or {}).get("owner_in_top3"),
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


def _haystack_for_text_match(
    plan_steps: list[str],
    top_paths: list[str | None],
    snippets: list[dict[str, Any]],
) -> str:
    parts: list[str] = []
    parts.extend(str(s) for s in plan_steps)
    parts.extend(str(p) for p in top_paths if p)
    for sn in snippets:
        parts.append(str(sn.get("preview") or ""))
        parts.append(str(sn.get("relative_path") or ""))
    return "\n".join(parts).lower()


_QUALITY_RANK: dict[str, int] = {
    "STRONG": 3,
    "MODERATE": 2,
    "WEAK": 1,
}

_GENERIC_SCAN_FORBIDDEN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"open .* and scan for logic related to", re.IGNORECASE),
    re.compile(r"scan for logic related to", re.IGNORECASE),
    re.compile(r"could not determine.*from retrieved snippets", re.IGNORECASE | re.DOTALL),
]

_GRAPH_PREFLIGHT_THRESHOLDS: dict[str, int] = {
    "VERTICLE_REGISTRATION": 5,
    "EVENTBUS_CONSUMER_REGISTRATION": 10,
    "API_ROUTE_REGISTRATION": 1,
}


def _rank_evidence_quality(q: str | None) -> int:
    if not q or not isinstance(q, str):
        return 0
    return _QUALITY_RANK.get(q.strip().upper(), 0)


def _haystack_plan_notes(resp: dict[str, Any]) -> str:
    ps = resp.get("plan_summary") if isinstance(resp.get("plan_summary"), dict) else {}
    notes = ps.get("notes") if isinstance(ps.get("notes"), list) else []
    return " ".join(str(n) for n in notes)


def _scenario_flag(scenario: dict[str, Any], key: str) -> bool:
    val = scenario.get(key)
    if isinstance(val, bool):
        return val
    expect = scenario.get("expect") if isinstance(scenario.get("expect"), dict) else {}
    return bool(expect.get(key) is True)


def _text_contains_generic_scan_phrase(text: str) -> list[str]:
    hits: list[str] = []
    for pat in _GENERIC_SCAN_FORBIDDEN_PATTERNS:
        if pat.search(text):
            hits.append(pat.pattern)
    return hits


def _symbol_candidates_from_paths(paths: list[str]) -> list[str]:
    symbols: list[str] = []
    for p in paths:
        if not p:
            continue
        base = p.rsplit("/", 1)[-1]
        stem = base.rsplit(".", 1)[0]
        if stem and len(stem) >= 3:
            symbols.append(stem)
    return symbols


def _has_concrete_implementation_anchor(
    plan_steps: list[str],
    plan_notes: list[str],
    context_bundle_files: list[dict[str, Any]],
    top_paths: list[str | None],
) -> bool:
    paths = [str(x.get("path") or "") for x in context_bundle_files if isinstance(x, dict)]
    paths.extend(str(p or "") for p in top_paths)
    paths = [p for p in paths if p]
    if not paths:
        return False

    text = " ".join(str(s) for s in plan_steps + plan_notes)
    text_l = text.lower()
    if re.search(r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.(?:java|kt|py|ts|tsx|js|go|rb|cs|yaml|yml|json|xml|md)\b", text):
        return True

    path_basenames = [p.rsplit("/", 1)[-1].lower() for p in paths if "/" in p or "." in p]
    if any(b and b in text_l for b in path_basenames):
        return True

    symbols = [s.lower() for s in _symbol_candidates_from_paths(paths)]
    return any(sym and re.search(rf"\b{re.escape(sym)}\b", text_l) for sym in symbols)


def _classify_graph_preflight_state(anchor_counts: dict[str, int]) -> str:
    for key, threshold in _GRAPH_PREFLIGHT_THRESHOLDS.items():
        if int(anchor_counts.get(key, 0)) <= int(threshold):
            return "INCOMPLETE"
    return "COMPLETE"


def _graph_preflight() -> dict[str, Any]:
    try:
        from tools.ast_indexer.query_graph import GraphUnavailableError, get_java_ast_ingest_state
    except Exception as exc:
        return {
            "state": "UNREACHABLE",
            "reason": f"graph helper import failed: {exc}",
            "anchor_counts": {},
            "thresholds": dict(_GRAPH_PREFLIGHT_THRESHOLDS),
        }
    try:
        state = get_java_ast_ingest_state()
    except GraphUnavailableError as exc:
        return {
            "state": "UNREACHABLE",
            "reason": str(exc),
            "anchor_counts": {},
            "thresholds": dict(_GRAPH_PREFLIGHT_THRESHOLDS),
        }
    if not isinstance(state, dict):
        anchor_counts = {
            "VERTICLE_REGISTRATION": 0,
            "EVENTBUS_CONSUMER_REGISTRATION": 0,
            "API_ROUTE_REGISTRATION": 0,
        }
        return {
            "state": "INCOMPLETE",
            "reason": "java_ast ingest state missing",
            "anchor_counts": anchor_counts,
            "thresholds": dict(_GRAPH_PREFLIGHT_THRESHOLDS),
        }
    anchor_counts = {
        "VERTICLE_REGISTRATION": int(state.get("anchor_count_verticle_registration") or 0),
        "EVENTBUS_CONSUMER_REGISTRATION": int(state.get("anchor_count_eventbus_consumer_registration") or 0),
        "API_ROUTE_REGISTRATION": int(state.get("anchor_count_api_route_registration") or 0),
    }
    pre_state = _classify_graph_preflight_state(anchor_counts)
    reason = (
        "graph ingest counters satisfy required thresholds"
        if pre_state == "COMPLETE"
        else "graph ingest counters are below required thresholds"
    )
    return {
        "state": pre_state,
        "reason": reason,
        "anchor_counts": anchor_counts,
        "thresholds": dict(_GRAPH_PREFLIGHT_THRESHOLDS),
    }


def _check_utility_expect_ask(
    utility_expect: dict[str, Any],
    resp: dict[str, Any],
    entries: list[dict[str, Any]],
    meta: dict[str, Any],
    haystack: str,
    top_paths: list[str | None],
) -> list[str]:
    errs: list[str] = []
    ue = utility_expect
    actual_eq = meta.get("evidence_quality")
    if ue.get("governance_posture") and resp.get("governance_posture") != ue["governance_posture"]:
        errs.append(f"governance_posture want {ue['governance_posture']} got {resp.get('governance_posture')}")
    if ue.get("execution") is not None and resp.get("execution") != ue["execution"]:
        errs.append(f"execution want {ue['execution']} got {resp.get('execution')}")
    if ue.get("ask_path") and (resp.get("evidence_first_meta") or {}).get("ask_path") != ue["ask_path"]:
        errs.append(f"ask_path want {ue['ask_path']} got {(resp.get('evidence_first_meta') or {}).get('ask_path')}")
    plan_steps = ((resp.get("plan_summary") or {}).get("steps") or []) if isinstance(resp.get("plan_summary"), dict) else []
    if ue.get("min_plan_steps"):
        if len(plan_steps) < int(ue["min_plan_steps"]):
            errs.append(f"min_plan_steps want >= {ue['min_plan_steps']} got {len(plan_steps)}")
    if ue.get("min_evidence_quality"):
        min_r = _rank_evidence_quality(str(ue["min_evidence_quality"]))
        ar = _rank_evidence_quality(str(actual_eq) if actual_eq else "")
        if ar < min_r:
            errs.append(f"min_evidence_quality want rank>={ue['min_evidence_quality']} got {actual_eq}")
    allowed_q = ue.get("allowed_evidence_quality_any")
    if isinstance(allowed_q, list) and actual_eq is not None:
        if str(actual_eq) not in [str(x) for x in allowed_q]:
            errs.append(f"evidence_quality want one of {allowed_q} got {actual_eq}")
    paths_norm = [str(p) for p in top_paths if p]
    req_any = ue.get("required_paths_any")
    if isinstance(req_any, list) and req_any:
        if not any(
            any(sub in p for p in paths_norm)
            for sub in req_any
            if sub
        ):
            errs.append(f"required_paths_any: none of {req_any} matched paths {paths_norm[:8]}")
    req_all = ue.get("required_paths_all")
    if isinstance(req_all, list) and req_all:
        for sub in req_all:
            if not any(sub in p for p in paths_norm):
                errs.append(f"required_paths_all: missing {sub}")
    forb = ue.get("forbidden_paths_any")
    max_dis = ue.get("max_distractor_paths")
    if isinstance(forb, list) and forb:
        distractor_count = sum(1 for p in paths_norm for bad in forb if bad and bad in p)
        if max_dis is not None:
            if distractor_count > int(max_dis):
                errs.append(f"max_distractor_paths: got {distractor_count} forbidden-path matches, max {max_dis}")
        else:
            for p in paths_norm:
                for bad in forb:
                    if bad and bad in p:
                        errs.append(f"forbidden_paths_any: forbidden path present in evidence: {bad}")
    subs_any = ue.get("required_text_contains_any")
    if isinstance(subs_any, list) and subs_any:
        if not any(str(s).lower() in haystack for s in subs_any if s):
            errs.append(f"required_text_contains_any: none of {subs_any} found in plan/snippets/paths")
    subs_all = ue.get("required_text_contains_all")
    if isinstance(subs_all, list) and subs_all:
        for s in subs_all:
            if s and str(s).lower() not in haystack:
                errs.append(f"required_text_contains_all: missing {s!r}")
    if ue.get("must_distinguish_owner_vs_supporting"):
        uniq = len({p for p in paths_norm[:6] if p})
        if uniq < 2:
            errs.append("must_distinguish_owner_vs_supporting: need >=2 distinct paths in top evidence (heuristic)")
        owner_markers = ("owner", "primary", "implements", "main")
        if not any(m in haystack for m in owner_markers):
            errs.append("must_distinguish_owner_vs_supporting: expected owner/primary language in answer (heuristic)")
    notes_h = (_haystack_plan_notes(resp) + " " + haystack).lower()
    if ue.get("must_include_honesty_if_weak") and str(actual_eq) == "WEAK":
        honesty = ue.get("required_text_contains_any")
        if isinstance(honesty, list) and honesty:
            if not any(str(s).lower() in notes_h for s in honesty if s):
                errs.append(
                    "must_include_honesty_if_weak: WEAK but no honesty cue matched (notes/plan/snippets; heuristic)"
                )
        qr = meta.get("quality_reasons") if isinstance(meta.get("quality_reasons"), list) else []
        if not qr and not any(x in notes_h for x in ("weak", "provisional", "generic", "verify")):
            errs.append("must_include_honesty_if_weak: WEAK without quality_reasons or clear caveat (heuristic)")
    if ue.get("must_not_overclaim_if_weak") and str(actual_eq) == "WEAK":
        if not meta.get("quality_reasons") and "insufficient" not in notes_h and "provisional" not in notes_h:
            errs.append("must_not_overclaim_if_weak: WEAK but little/no explicit limitation signal (heuristic)")
    return errs


def _check_utility_expect_debug(
    utility_expect: dict[str, Any],
    resp: dict[str, Any],
    ed: dict[str, Any],
    selected_file: str,
) -> list[str]:
    errs: list[str] = []
    ue = utility_expect
    if ue.get("routing_mode") and resp.get("routing_mode") != ue["routing_mode"]:
        errs.append(f"routing_mode want {ue['routing_mode']} got {resp.get('routing_mode')}")
    keys_req = ue.get("required_explain_keys")
    if isinstance(keys_req, list):
        for k in keys_req:
            if k not in ed:
                errs.append(f"required_explain_key missing: {k}")
    explain_h = " ".join(
        str(ed.get(k) or "") for k in ("summary", "logic_flow", "likely_bug_risk", "evidence", "error")
    ).lower()
    if ue.get("must_reference_selected_file_or_symbol") and selected_file:
        base = selected_file.split("/")[-1].replace(".java", "")
        if base.lower() not in explain_h and selected_file.lower() not in explain_h:
            errs.append("must_reference_selected_file_or_symbol: selected file/symbol not clearly referenced (heuristic)")
    subs = ue.get("required_text_contains_any")
    if isinstance(subs, list) and subs:
        if not any(str(s).lower() in explain_h for s in subs if s):
            errs.append(f"required_text_contains_any: none of {subs} in explain_debug text")
    if ue.get("must_not_admit_missing_context_without_next_step"):
        summary = str(ed.get("summary") or "").lower()
        if any(x in summary for x in ("not present", "not in the provided", "not in context", "missing from")):
            if not any(x in summary for x in ("add", "provide", "open", "retrieve", "next", "suggest", "need")):
                errs.append(
                    "must_not_admit_missing_context_without_next_step: missing context admitted without next step (heuristic)"
                )
    if ue.get("must_suggest_concrete_failure_points"):
        concrete = any(
            x in explain_h for x in ("if ", "when ", "condition", "branch", "return", "skip", "null", "exception")
        )
        if not concrete:
            errs.append("must_suggest_concrete_failure_points: no concrete control-flow cues in explain_debug (heuristic)")
    return errs


def _check_utility_expect_plan(utility_expect: dict[str, Any], plan_resp: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    ue = utility_expect
    blob = json.dumps(plan_resp, default=str).lower()
    dec = plan_resp.get("decision")
    allowed = ue.get("allowed_decisions_any")
    if isinstance(allowed, list) and allowed and dec not in allowed:
        errs.append(f"allowed_decisions_any: want one of {allowed} got {dec}")
    if ue.get("must_identify_candidate_files"):
        if ".java" not in blob and ".kt" not in blob and "/" not in blob:
            errs.append("must_identify_candidate_files: no file-like path in plan response (heuristic)")
    if ue.get("must_include_risk_or_guardrail"):
        if not any(x in blob for x in ("risk", "guard", "validat", "test", "rollback", "block")):
            errs.append("must_include_risk_or_guardrail: no risk/guardrail/test cue in plan response (heuristic)")
    subs = ue.get("required_text_contains_any")
    if isinstance(subs, list) and subs:
        if not any(str(s).lower() in blob for s in subs if s):
            errs.append(f"required_text_contains_any: none of {subs} in plan response JSON (heuristic)")
    return errs


def _run_utility_scenario_row(
    scenario: dict[str, Any],
    workspace_root: str,
    context_url: str,
    plan_gate_url: str,
    top_k: int,
    *,
    export_stage_a: Optional[bool] = None,
) -> dict[str, Any]:
    sid = str(scenario.get("id") or "unknown")
    cap = str(scenario.get("capability") or "")
    desc = scenario.get("description")
    inputs = scenario.get("inputs") if isinstance(scenario.get("inputs"), dict) else {}
    utility_expect = scenario.get("utility_expect") if isinstance(scenario.get("utility_expect"), dict) else {}
    ws = str(inputs.get("workspace_root") or workspace_root)
    errors: list[str] = []

    if cap == "ask":
        q = str(inputs.get("query") or "")
        code, evidence = _post(
            f"{context_url}/v1/export_evidence",
            _export_evidence_payload(ws, q, top_k, enable_stage_a_v2=export_stage_a),
            timeout=300,
        )
        entries = evidence.get("entries") if isinstance(evidence.get("entries"), list) else []
        if code != 200 or not entries:
            return {
                "id": sid,
                "capability": cap,
                "description": desc,
                "pass": False,
                "utility_track": True,
                "errors": [f"export_evidence failed http={code} entries={len(entries)}"],
                "utility_expect": utility_expect,
                "actual_summary": None,
                "developer_snapshot": None,
            }
        req: dict[str, Any] = {
            "schema_version": "ask_request.v1.0",
            "request_id": str(uuid.uuid4()),
            "timestamp_utc": _utc_now(),
            "query": q,
            "evidence_bundle": evidence,
        }
        if inputs.get("task_type"):
            req["task_type"] = inputs["task_type"]
        if evidence.get("workspace_identity_hash"):
            req["expected_workspace_identity_hash"] = evidence["workspace_identity_hash"]
        code, resp = _post(f"{plan_gate_url}/v1/ask", req)
        meta = resp.get("metadata") if isinstance(resp.get("metadata"), dict) else {}
        plan_steps = ((resp.get("plan_summary") or {}).get("steps") or []) if isinstance(resp.get("plan_summary"), dict) else []
        top_paths = [e.get("relative_path") for e in entries[:8] if isinstance(e, dict)]
        snips = _evidence_snippet_previews([e for e in entries if isinstance(e, dict)])
        haystack = _haystack_for_text_match([str(s) for s in plan_steps], top_paths, snips)
        haystack = (haystack + " " + _haystack_plan_notes(resp)).lower()
        errors.extend(_check_utility_expect_ask(utility_expect, resp, entries, meta, haystack, top_paths))
        dev_snapshot = {
            "request_id": resp.get("request_id"),
            "evidence_quality": meta.get("evidence_quality"),
            "quality_reasons": meta.get("quality_reasons"),
            "answer_steps": plan_steps,
            "context_bundle_files": _context_bundle_files(resp),
            "evidence_snippet_previews": snips,
            "retrieval_metrics": _compute_retrieval_metrics(evidence, top_k=top_k),
        }
        return {
            "id": sid,
            "capability": cap,
            "description": desc,
            "pass": len(errors) == 0 and code == 200,
            "utility_track": True,
            "errors": errors,
            "utility_expect": utility_expect,
            "actual_summary": {
                "http": code,
                "evidence_quality": meta.get("evidence_quality"),
                "plan_steps_count": len(plan_steps),
                "retrieval_metrics": _compute_retrieval_metrics(evidence, top_k=top_k),
            },
            "developer_snapshot": dev_snapshot,
        }

    if cap == "debug":
        q = str(inputs.get("query") or "")
        sel = str(inputs.get("active_file") or "")
        sel_text = str(inputs.get("selection_text") or "Investigate likely failure points and trace flow.")
        code, evidence = _post(
            f"{context_url}/v1/export_evidence",
            _export_evidence_payload(
                ws,
                q,
                top_k,
                task_type="EXPLAIN_DEBUG",
                selected_file=sel or None,
                active_file=sel or None,
                enable_stage_a_v2=export_stage_a,
            ),
            timeout=300,
        )
        entries = evidence.get("entries") if isinstance(evidence.get("entries"), list) else []
        if code != 200 or not entries:
            return {
                "id": sid,
                "capability": cap,
                "description": desc,
                "pass": False,
                "utility_track": True,
                "errors": ["export_evidence failed for utility debug scenario"],
                "utility_expect": utility_expect,
                "actual_summary": None,
                "developer_snapshot": None,
            }
        req = {
            "schema_version": "ask_request.v1.0",
            "request_id": str(uuid.uuid4()),
            "timestamp_utc": _utc_now(),
            "query": q,
            "evidence_bundle": evidence,
            "task_type": "EXPLAIN_DEBUG",
            "selected_file": sel or (entries[0].get("relative_path") if entries else ""),
            "client_context": {"selection": sel_text},
        }
        if evidence.get("workspace_identity_hash"):
            req["expected_workspace_identity_hash"] = evidence["workspace_identity_hash"]
        code, resp = _post(f"{plan_gate_url}/v1/ask", req)
        ed = resp.get("explain_debug") if isinstance(resp.get("explain_debug"), dict) else {}
        errors.extend(_check_utility_expect_debug(utility_expect, resp, ed, sel))
        ok_body = code == 200 and ("summary" in ed or "error" in ed)
        dev_snapshot = {
            "routing_mode": resp.get("routing_mode"),
            "summary": ed.get("summary"),
            "likely_bug_risk": ed.get("likely_bug_risk"),
            "logic_flow": ed.get("logic_flow"),
            "error": ed.get("error"),
        }
        return {
            "id": sid,
            "capability": cap,
            "description": desc,
            "pass": len(errors) == 0 and ok_body,
            "utility_track": True,
            "errors": errors,
            "utility_expect": utility_expect,
            "actual_summary": {"http": code, "routing_mode": resp.get("routing_mode")},
            "developer_snapshot": dev_snapshot,
        }

    if cap == "plan":
        intent = str(inputs.get("intent") or sid)
        plan_req: dict[str, Any] = {
            "schema_version": "plan_request.v0.1",
            "request_id": str(uuid.uuid4()),
            "timestamp_utc": _utc_now(),
            "mode": "shadow",
            "ide_event": {
                "schema_version": "ide_event.v0.1",
                "event_id": f"evt-utility-{sid}",
                "timestamp_utc": _utc_now(),
                "ide_context": {
                    "product": "cli",
                    "ide": "none",
                    "project": "Motadata",
                    "repo_root": ws,
                    "branch": "main",
                    "user": "operator",
                },
                "action": {"action_type": "PR_MERGE", "target": "main"},
                "evidence_refs": [{"type": "note", "ref": intent[:2000]}],
            },
            "requested_capabilities": ["plan_and_decide"],
            "client_policy": {"fail_closed_if_gate_unreachable": True},
        }
        if utility_expect.get("schema_version"):
            pass
        code, plan_resp = _post(f"{plan_gate_url}/v0/plan", plan_req)
        if utility_expect.get("schema_version") and plan_resp.get("schema_version") != utility_expect["schema_version"]:
            errors.append(
                f"schema_version want {utility_expect['schema_version']} got {plan_resp.get('schema_version')}"
            )
        if utility_expect.get("decision_present") and not plan_resp.get("decision"):
            errors.append("decision missing")
        errors.extend(_check_utility_expect_plan(utility_expect, plan_resp))
        return {
            "id": sid,
            "capability": cap,
            "description": desc,
            "pass": len(errors) == 0 and code == 200,
            "utility_track": True,
            "errors": errors,
            "utility_expect": utility_expect,
            "actual_summary": {"http": code, "decision": plan_resp.get("decision")},
            "developer_snapshot": {"plan_response_excerpt": _clip(json.dumps(plan_resp, default=str), 4000)},
        }

    return {
        "id": sid,
        "capability": cap,
        "description": desc,
        "pass": False,
        "utility_track": True,
        "errors": [f"unknown utility capability: {cap}"],
        "utility_expect": utility_expect,
        "actual_summary": None,
        "developer_snapshot": None,
    }


def run_utility_scenario_suite(
    scenarios_path: Path,
    workspace_root: str,
    context_url: str,
    plan_gate_url: str,
    top_k: int,
    *,
    export_stage_a: Optional[bool] = None,
) -> dict[str, Any]:
    data = json.loads(scenarios_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "motadata_developer_utility_scenarios.v1":
        return {
            "file": str(scenarios_path),
            "all_pass": False,
            "error": "unsupported schema_version (expected motadata_developer_utility_scenarios.v1)",
            "results": [],
            "utility_note": "Developer utility assertions use heuristics; failures are signals, not formal closure gates.",
        }
    defaults = data.get("defaults") if isinstance(data.get("defaults"), dict) else {}
    tk = int(defaults.get("top_k", top_k))
    results: list[dict[str, Any]] = []
    for sc in data.get("scenarios") or []:
        if not isinstance(sc, dict):
            continue
        results.append(
            _run_utility_scenario_row(
                sc,
                workspace_root,
                context_url,
                plan_gate_url,
                tk,
                export_stage_a=export_stage_a,
            )
        )
    all_pass = all(r.get("pass") for r in results) if results else False
    return {
        "file": str(scenarios_path),
        "all_pass": all_pass,
        "results": results,
        "utility_note": "Developer utility assertions are heuristic/approximate where noted; not a substitute for human review.",
    }


def _check_expect_ask(actual: dict[str, Any], expect: dict[str, Any], answer_haystack: str) -> list[str]:
    errs: list[str] = []
    if "governance_posture" in expect and actual.get("governance_posture") != expect["governance_posture"]:
        errs.append(f"governance_posture want {expect['governance_posture']} got {actual.get('governance_posture')}")
    if "execution" in expect and actual.get("execution") != expect["execution"]:
        errs.append(f"execution want {expect['execution']} got {actual.get('execution')}")
    if "ask_path" in expect and actual.get("ask_path") != expect["ask_path"]:
        errs.append(f"ask_path want {expect['ask_path']} got {actual.get('ask_path')}")
    if "min_plan_steps" in expect:
        n = len(actual.get("plan_steps") or [])
        if n < int(expect["min_plan_steps"]):
            errs.append(f"min_plan_steps want >= {expect['min_plan_steps']} got {n}")
    subs = expect.get("text_contains_any")
    if isinstance(subs, list) and subs:
        if not any(str(s).lower() in answer_haystack for s in subs if s):
            errs.append(f"text_contains_any: none of {subs} found in answer text (plan steps/notes)")
    return errs


def _owner_file_from_evidence(evidence: dict[str, Any]) -> str:
    ar = evidence.get("authority_resolution")
    if not isinstance(ar, dict):
        return ""
    po = ar.get("primary_owner")
    if not isinstance(po, dict):
        return ""
    return str(po.get("file") or "").strip()


def _owner_injected_lane_count(evidence: dict[str, Any]) -> int:
    """Count Stage A ``owner_injected`` lane rows from ``lanes_sizes`` or candidate list."""
    fd = evidence.get("fusion_diagnostics") if isinstance(evidence.get("fusion_diagnostics"), dict) else {}
    sa = fd.get("stage_a_meta") if isinstance(fd.get("stage_a_meta"), dict) else {}
    ls = sa.get("lanes_sizes")
    if isinstance(ls, dict) and "owner_injected" in ls:
        return int(ls["owner_injected"])
    return int(_stage_a_summary_from_evidence(evidence).get("lane_counts", {}).get("owner_injected", 0))


def _check_expect_ask_retrieval_gates(
    evidence: dict[str, Any],
    expect: dict[str, Any],
    top_k: int,
) -> list[str]:
    """
    Optional anchored-owner gates on ``export_evidence`` payload (Layer-5 retrieval).

    Keys (all optional):
    - ``require_authority_primary_owner`` (bool): ``authority_resolution.primary_owner.file`` is non-empty.
    - ``require_owner_in_top3`` (bool): primary owner path appears in top-3 evidence entries.
    - ``require_stage_a_owner_injected_min`` (int): Stage A lane quota for owner_injected.
    - ``require_authority_status`` (str): authority resolution status must equal this value.
    """
    errs: list[str] = []
    if expect.get("require_authority_primary_owner"):
        if not _owner_file_from_evidence(evidence):
            errs.append(
                "require_authority_primary_owner: missing authority_resolution.primary_owner.file "
                "(registry did not resolve or authority pipeline failed)"
            )
    rm = _compute_retrieval_metrics(evidence, top_k=top_k)
    if expect.get("require_owner_in_top3"):
        if not rm.get("owner_in_top3"):
            errs.append(
                "require_owner_in_top3: primary owner not in evidence entries top-3 "
                f"(owner_file={_owner_file_from_evidence(evidence)!r})"
            )
    if "require_stage_a_owner_injected_min" in expect:
        need = int(expect["require_stage_a_owner_injected_min"])
        got = _owner_injected_lane_count(evidence)
        if got < need:
            errs.append(
                f"require_stage_a_owner_injected_min: want >= {need} got owner_injected_lane_count={got} "
                "(ensure export Stage A is enabled; default on unless MOTADATA_L5_ENABLE_STAGE_A_V2=0 or --export-stage-a off)"
            )
    if "require_authority_status" in expect:
        ar = evidence.get("authority_resolution")
        got_status = None
        if isinstance(ar, dict):
            # Canonical field in layer5.evidence_bundle.v1.
            got_status = ar.get("authority_status")
            # Backward-compatible fallback for older/debug payloads.
            if got_status is None:
                got_status = ar.get("status")
        want_status = str(expect["require_authority_status"])
        if str(got_status or "").lower() != want_status.lower():
            errs.append(
                f"require_authority_status: want {want_status} got {got_status!r}"
            )
    return errs


def _check_expect_debug_explain(
    expect: dict[str, Any],
    explain_debug: dict[str, Any],
    selected_file: str,
    *,
    context_paths: list[str] | None = None,
) -> list[str]:
    errs: list[str] = []
    hay = " ".join(
        str(explain_debug.get(k) or "")
        for k in ("summary", "logic_flow", "likely_bug_risk", "confidence_limits", "error")
    ).lower()
    ev = explain_debug.get("evidence")
    ev_list = [str(x) for x in ev] if isinstance(ev, list) else []
    ev_h = " ".join(ev_list).lower()
    base = str(selected_file or "").split("/")[-1]
    symbol = base.replace(".java", "").replace(".py", "")

    if expect.get("must_reference_selected_file_or_symbol"):
        if symbol and symbol.lower() not in hay and symbol.lower() not in ev_h and base.lower() not in hay:
            errs.append(
                "must_reference_selected_file_or_symbol: selected file/symbol not found in explain_debug"
            )
    if expect.get("require_selected_file_in_evidence"):
        if not ev_list:
            errs.append("require_selected_file_in_evidence: explain_debug.evidence missing/empty")
        elif not any(base.lower() in e.lower() or symbol.lower() in e.lower() for e in ev_list):
            errs.append(
                "require_selected_file_in_evidence: selected file/symbol missing from explain_debug.evidence"
            )
    if expect.get("require_selected_file_in_context_bundle"):
        paths = list(context_paths or [])
        if not _context_paths_match_selected(paths, selected_file):
            errs.append(
                "require_selected_file_in_context_bundle: selected_file not found in context_bundle.files"
            )
    if expect.get("must_suggest_concrete_failure_points"):
        if not any(x in hay for x in ("if ", "when ", "branch", "condition", "return", "null", "exception", "method")):
            errs.append(
                "must_suggest_concrete_failure_points: no concrete control-flow/method cues in explain_debug"
            )
    subs = expect.get("required_text_contains_any")
    if isinstance(subs, list) and subs:
        if not any(str(s).lower() in hay or str(s).lower() in ev_h for s in subs if s):
            errs.append(f"required_text_contains_any: none of {subs} found in explain_debug")
    if expect.get("must_have_confidence_limits"):
        if not str(explain_debug.get("confidence_limits") or "").strip():
            errs.append("must_have_confidence_limits: explain_debug.confidence_limits missing")
    if expect.get("require_insufficient_grounding"):
        grounded = any(
            marker in hay
            for marker in (
                "insufficiently grounded",
                "insufficient grounding",
                "missing in context",
                "missing_in_context",
            )
        ) or any("missing_in_context:" in e.lower() for e in ev_list)
        if not grounded:
            errs.append(
                "require_insufficient_grounding: explain_debug did not report truthful insufficiency"
            )
    if expect.get("require_missing_in_context_marker"):
        if not any("missing_in_context:" in e.lower() for e in ev_list):
            errs.append(
                "require_missing_in_context_marker: explain_debug.evidence missing missing_in_context marker"
            )
    return errs


def _check_method_body_answer_alignment(
    expect: dict[str, Any],
    evidence: dict[str, Any],
    explain_debug: dict[str, Any],
) -> list[str]:
    """
    Optional hard alignment: fusion says snippets include grounded method/control-flow evidence,
    but explain_debug still asserts total absence of grounding (truth-binding failure).
    """
    if not expect.get("require_method_body_answer_alignment"):
        return []
    if not expect.get("require_selected_method_body_present"):
        return []
    fd = evidence.get("fusion_diagnostics")
    if not isinstance(fd, dict):
        return []
    tier = str(fd.get("selected_method_grounding_tier") or "").strip().lower()
    body_present = fd.get("selected_method_body_present") is True
    exec_tier = tier in {"executable", "traceable"}
    if not tier and not body_present:
        return []
    hay_lc, _, _ = _collect_debug_text_blobs(explain_debug)
    absence_needles = (
        "is not present in the retrieved context",
        "without that file body",
        "cannot trace concrete method",
        "insufficiently grounded",
        "missing_in_context:",
        "lacks specific details",
        "does not contain",
        "not present in the given context",
        "cannot trace",
        "no direct reference",
        "unclear how this relates",
        "without seeing the actual implementations",
        "declaration-heavy",
        "trace inherited/update hooks in nearby classes",
    )
    absence_hits = [n for n in absence_needles if n.lower() in hay_lc]
    if exec_tier and absence_hits:
        return [
            "require_method_body_answer_alignment: explain_debug contradicts "
            f"fusion selected_method_grounding_tier={tier!r} "
            + f"(matched phrases={absence_hits})"
        ]

    if tier in {"none", "declarative", "partial"}:
        overclaim_needles = (
            "the method does",
            "this branch executes",
            "the code returns",
            "exact failure path",
            "root cause is",
        )
        overclaim_hits = [n for n in overclaim_needles if n in hay_lc]
        if overclaim_hits:
            return [
                "require_method_body_answer_alignment: explain_debug overclaims method-level certainty "
                f"for selected_method_grounding_tier={tier!r} (matched phrases={overclaim_hits})"
            ]

    if exec_tier:
        op_needles = (
            "read",
            "parse",
            "dispatch",
            "decrypt",
            "initialize",
            "update",
            "set",
            "put",
            "add",
            "remove",
            "return",
            "throw",
            "call",
            "loop",
            "iterate",
            "map",
            "hashset",
        )
        op_hits = [n for n in op_needles if n in hay_lc]
        if not op_hits:
            return [
                "require_method_body_answer_alignment: selected_method_body_present but explain_debug lacks "
                "concrete operation verbs tied to selected-file logic"
            ]
    return []


def _check_expect_debug_method_body(
    expect: dict[str, Any],
    evidence: dict[str, Any],
) -> list[str]:
    errs: list[str] = []
    if not expect.get("require_selected_method_body_present"):
        return errs
    fd = evidence.get("fusion_diagnostics")
    fd = fd if isinstance(fd, dict) else {}
    present = fd.get("selected_method_body_present")
    tier = str(fd.get("selected_method_grounding_tier") or "").strip().lower()
    hints = fd.get("selected_method_hints") if isinstance(fd.get("selected_method_hints"), list) else []
    if not hints:
        errs.append("require_selected_method_body_present: no selected_method_hints exported in fusion_diagnostics")
        return errs
    if tier:
        if tier not in {"executable", "traceable"}:
            errs.append(
                "require_selected_method_body_present: selected method grounding tier is not executable "
                f"(tier={tier!r}, hints={hints}, reason={fd.get('selected_method_body_missing_reason')})"
            )
            return errs
        if present is not True:
            errs.append(
                "require_selected_method_body_present: selected_method_body_present must be true "
                f"when tier={tier!r} (hints={hints})"
            )
            return errs
    if present is not True:
        errs.append(
            "require_selected_method_body_present: selected method body not present in selected-file snippets "
            f"(hints={hints}, reason={fd.get('selected_method_body_missing_reason')})"
        )
    return errs


def _collect_debug_text_blobs(explain_debug: dict[str, Any]) -> tuple[str, list[str], str]:
    ev = explain_debug.get("evidence")
    ev_list = [str(x) for x in ev] if isinstance(ev, list) else []
    hay = " ".join(
        str(explain_debug.get(k) or "")
        for k in ("summary", "logic_flow", "likely_bug_risk", "confidence_limits", "error")
    ).lower()
    ev_h = " ".join(ev_list).lower()
    return hay, ev_list, ev_h


def _selected_symbol_hit_count(selected_file: str, text_lc: str, evidence_lc: str) -> int:
    base = str(selected_file or "").split("/")[-1]
    symbol = base.replace(".java", "").replace(".py", "").replace(".kt", "")
    combined = f"{text_lc} {evidence_lc}"
    terms = [t.lower() for t in (base, symbol) if t]
    if not terms:
        return 0
    return sum(combined.count(t) for t in terms)


def _method_like_mentions_count(text_lc: str, evidence: list[str]) -> int:
    seen: set[str] = set()
    blocked = {"if", "for", "while", "switch", "catch", "return", "new"}
    for m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", text_lc):
        name = m.group(1).lower()
        if name not in blocked and len(name) >= 3:
            seen.add(name)
    for e in evidence:
        if ":" not in e:
            continue
        tail = e.split(":")[-1].strip()
        tail = re.sub(r"\(.*$", "", tail).strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tail):
            name = tail.lower()
            if name not in blocked and len(name) >= 3:
                seen.add(name)
    return len(seen)


def _evidence_ref_count(evidence: list[str]) -> int:
    count = 0
    for e in evidence:
        s = str(e).strip()
        if "/" in s and ":" in s:
            count += 1
    return count


def _control_flow_marker_count(text_lc: str) -> int:
    markers = (
        " if ",
        " else ",
        " branch",
        " condition",
        " return",
        " null",
        " exception",
        " throw",
        " catch",
        " switch",
        " method",
    )
    padded = f" {text_lc} "
    return sum(1 for m in markers if m in padded)


def _check_expect_debug_depth(
    expect: dict[str, Any],
    explain_debug: dict[str, Any],
    selected_file: str,
) -> tuple[list[str], dict[str, Any]]:
    errs: list[str] = []
    hay, ev_list, ev_h = _collect_debug_text_blobs(explain_debug)
    symbol_hits = _selected_symbol_hit_count(selected_file, hay, ev_h)
    method_mentions = _method_like_mentions_count(hay, ev_list)
    evidence_refs = _evidence_ref_count(ev_list)
    flow_markers = _control_flow_marker_count(hay)

    if "require_selected_file_symbol_hits_min" in expect:
        need = int(expect.get("require_selected_file_symbol_hits_min") or 0)
        if symbol_hits < need:
            errs.append(f"require_selected_file_symbol_hits_min: want >= {need} got {symbol_hits}")
    if "require_method_name_mentions_min" in expect:
        need = int(expect.get("require_method_name_mentions_min") or 0)
        if method_mentions < need:
            errs.append(f"require_method_name_mentions_min: want >= {need} got {method_mentions}")
    if "require_evidence_line_refs_min" in expect:
        need = int(expect.get("require_evidence_line_refs_min") or 0)
        if evidence_refs < need:
            errs.append(f"require_evidence_line_refs_min: want >= {need} got {evidence_refs}")
    if "require_control_flow_markers_min" in expect:
        need = int(expect.get("require_control_flow_markers_min") or 0)
        if flow_markers < need:
            errs.append(f"require_control_flow_markers_min: want >= {need} got {flow_markers}")

    forbid = expect.get("forbid_generic_phrases_any")
    if isinstance(forbid, list):
        matched = [str(p) for p in forbid if str(p).strip() and str(p).lower() in hay]
        if matched:
            errs.append(f"forbid_generic_phrases_any: found disallowed generic phrases {matched}")

    signals = {
        "selected_symbol_hits": symbol_hits,
        "method_name_mentions": method_mentions,
        "evidence_line_refs": evidence_refs,
        "control_flow_markers": flow_markers,
    }
    return errs, signals


def _load_quality_policy(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("quality policy must be a JSON object")
    if data.get("schema_version") != "motadata_evidence_quality_policy.v1":
        raise ValueError(
            "unsupported quality policy schema_version "
            f"(expected motadata_evidence_quality_policy.v1, got {data.get('schema_version')!r})"
        )
    return data


def _bool_gate_enabled(v: Any) -> bool:
    return bool(v) is True


def _scenario_quality_profile(
    policy: dict[str, Any] | None,
    scenario_id: str,
    capability: str,
) -> dict[str, Any]:
    if not isinstance(policy, dict):
        return {}
    out: dict[str, Any] = {}
    defaults = policy.get("defaults")
    if isinstance(defaults, dict):
        out.update(defaults)
    by_cap = policy.get("by_capability")
    if isinstance(by_cap, dict):
        cap_cfg = by_cap.get(capability)
        if isinstance(cap_cfg, dict):
            out.update(cap_cfg)
    by_id = policy.get("by_scenario_id")
    if isinstance(by_id, dict):
        sid_cfg = by_id.get(scenario_id)
        if isinstance(sid_cfg, dict):
            out.update(sid_cfg)
    return out


def _check_policy_ask_quality(
    retrieval_metrics: dict[str, Any],
    retrieval_gates: dict[str, Any],
    quality_profile: dict[str, Any],
) -> list[str]:
    errs: list[str] = []
    if not quality_profile or not _bool_gate_enabled(quality_profile.get("enforce")):
        return errs

    def _f(key: str, default: float = 0.0) -> float:
        try:
            return float(retrieval_metrics.get(key, default))
        except Exception:
            return default

    def _i_gate(key: str, default: int = 0) -> int:
        try:
            return int(retrieval_gates.get(key, default))
        except Exception:
            return default

    if "max_generic_infra_ratio_top_k" in quality_profile:
        mx = float(quality_profile["max_generic_infra_ratio_top_k"])
        got = _f("generic_infra_ratio_top_k", _f("generic_infra_ratio"))
        if got > mx:
            errs.append(f"policy.max_generic_infra_ratio_top_k: want <= {mx} got {got}")

    if "max_distractor_count_top_k" in quality_profile:
        mx = int(quality_profile["max_distractor_count_top_k"])
        got = int(retrieval_metrics.get("distractor_count_top_k", retrieval_metrics.get("distractor_count_at_k", 0)) or 0)
        if got > mx:
            errs.append(f"policy.max_distractor_count_top_k: want <= {mx} got {got}")

    if "min_anchor_hit_rate_top_k" in quality_profile:
        mn = float(quality_profile["min_anchor_hit_rate_top_k"])
        got = _f("anchor_hit_rate_top_k", _f("anchor_hit_rate_at_k"))
        if got < mn:
            errs.append(f"policy.min_anchor_hit_rate_top_k: want >= {mn} got {got}")

    if _bool_gate_enabled(quality_profile.get("require_owner_in_top3")) and not bool(retrieval_metrics.get("owner_in_top3")):
        errs.append("policy.require_owner_in_top3: owner_in_top3 is false")

    if _bool_gate_enabled(quality_profile.get("require_owner_in_top1")) and not bool(retrieval_metrics.get("owner_in_top1")):
        errs.append("policy.require_owner_in_top1: owner_in_top1 is false")

    if "require_stage_a_owner_injected_min" in quality_profile:
        need = int(quality_profile["require_stage_a_owner_injected_min"])
        got = _i_gate("owner_injected_lane_count")
        if got < need:
            errs.append(
                "policy.require_stage_a_owner_injected_min: "
                f"want >= {need} got {got}"
            )

    return errs


def _run_scenario_row(
    scenario: dict[str, Any],
    workspace_root: str,
    context_url: str,
    plan_gate_url: str,
    top_k: int,
    *,
    export_stage_a: Optional[bool] = None,
    quality_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sid = str(scenario.get("id") or "unknown")
    cap = str(scenario.get("capability") or "")
    desc = scenario.get("description")
    expect = scenario.get("expect") if isinstance(scenario.get("expect"), dict) else {}
    errors: list[str] = []

    if cap == "ask":
        q = str(scenario.get("query") or "")
        code, evidence = _post(
            f"{context_url}/v1/export_evidence",
            _export_evidence_payload(workspace_root, q, top_k, enable_stage_a_v2=export_stage_a),
            timeout=300,
        )
        entries = evidence.get("entries") if isinstance(evidence.get("entries"), list) else []
        if code != 200 or not entries:
            return {
                "id": sid,
                "capability": cap,
                "description": desc,
                "pass": False,
                "errors": [f"export_evidence failed http={code} entries={len(entries)}"],
                "expect": expect,
                "actual_summary": None,
            }
        req: dict[str, Any] = {
            "schema_version": "ask_request.v1.0",
            "request_id": str(uuid.uuid4()),
            "timestamp_utc": _utc_now(),
            "query": q,
            "evidence_bundle": evidence,
        }
        if evidence.get("workspace_identity_hash"):
            req["expected_workspace_identity_hash"] = evidence["workspace_identity_hash"]
        code, resp = _post(f"{plan_gate_url}/v1/ask", req)
        meta = resp.get("metadata") if isinstance(resp.get("metadata"), dict) else {}
        plan_steps = ((resp.get("plan_summary") or {}).get("steps") or []) if isinstance(resp.get("plan_summary"), dict) else []
        plan_notes = ((resp.get("plan_summary") or {}).get("notes") or []) if isinstance(resp.get("plan_summary"), dict) else []
        top_paths = [e.get("relative_path") for e in entries[:8] if isinstance(e, dict)]
        snips = _evidence_snippet_previews([e for e in entries if isinstance(e, dict)])
        answer_haystack = " ".join(str(x) for x in (plan_steps + plan_notes)).lower()
        context_files = _context_bundle_files(resp)
        actual = {
            "governance_posture": resp.get("governance_posture"),
            "execution": resp.get("execution"),
            "ask_path": (resp.get("evidence_first_meta") or {}).get("ask_path"),
            "plan_steps": plan_steps,
            "evidence_quality": meta.get("evidence_quality"),
        }
        errors.extend(_check_expect_ask(actual, expect, answer_haystack))
        errors.extend(_check_expect_ask_retrieval_gates(evidence, expect, top_k))
        if _scenario_flag(scenario, "forbid_generic_scan_answer"):
            text_for_scan_gate = " ".join(str(x) for x in (plan_steps + plan_notes))
            matched_forbidden = _text_contains_generic_scan_phrase(text_for_scan_gate)
            if matched_forbidden:
                errors.append(
                    "forbid_generic_scan_answer: response matched forbidden generic scan phrase(s): "
                    f"{matched_forbidden}"
                )
        if _scenario_flag(scenario, "must_cite_file_or_symbol_anchor"):
            if not _has_concrete_implementation_anchor(plan_steps, plan_notes, context_files, top_paths):
                errors.append(
                    "must_cite_file_or_symbol_anchor: missing concrete file/symbol implementation anchor in response"
                )
        if _scenario_flag(scenario, "requires_behavior_flow"):
            flow_h = " ".join(str(x) for x in (plan_steps + plan_notes)).lower()
            if not any(tok in flow_h for tok in ("flow", "branch", "path", "step", "method")):
                errors.append("requires_behavior_flow: expected behavior/control-flow language in answer")
        if "evidence_quality_any_of" in expect:
            allowed = expect["evidence_quality_any_of"]
            if isinstance(allowed, list) and actual.get("evidence_quality") not in allowed:
                errors.append(f"evidence_quality want one of {allowed} got {actual.get('evidence_quality')}")
        sa = _stage_a_summary_from_evidence(evidence)
        rm = _compute_retrieval_metrics(evidence, top_k=top_k)
        rg = {
            "owner_file": _owner_file_from_evidence(evidence),
            "workspace_identity_hash": evidence.get("workspace_identity_hash"),
            "owner_injected_lane_count": _owner_injected_lane_count(evidence),
        }
        qprof = _scenario_quality_profile(quality_policy, sid, cap)
        errors.extend(_check_policy_ask_quality(rm, rg, qprof))
        dev_snapshot = {
            "request_id": resp.get("request_id"),
            "trace_id": resp.get("trace_id") or (meta.get("trace_id") if isinstance(meta, dict) else None),
            "answer_steps": plan_steps,
            "answer_notes": plan_notes,
            "context_bundle_files": context_files,
            "evidence_snippet_previews": snips,
            "retrieval_metrics": rm,
            "retrieval_gates": rg,
            "quality_policy_profile": qprof,
            "stage_a": sa,
            "proof_density": {
                "method_window_visible_rate": meta.get("method_window_visible_rate"),
                "explicit_method_body_evidence_present": meta.get("explicit_method_body_evidence_present"),
                "execution_path_stitched": meta.get("execution_path_stitched"),
                "stitched_edge_count": meta.get("stitched_edge_count"),
                "stitched_edge_type": meta.get("stitched_edge_type"),
                "stitch_confidence": meta.get("stitch_confidence"),
                "owner_promoted_for_context": meta.get("owner_promoted_for_context"),
                "owner_original_rank_in_bundle": meta.get("owner_original_rank_in_bundle"),
                "method_claim_alignment_pass": meta.get("method_claim_alignment_pass"),
            },
        }
        return {
            "id": sid,
            "capability": cap,
            "description": desc,
            "pass": len(errors) == 0 and code == 200,
            "errors": errors,
            "expect": expect,
            "actual_summary": {
                "http": code,
                "evidence_quality": actual.get("evidence_quality"),
                "ask_path": actual.get("ask_path"),
                "plan_steps_count": len(plan_steps),
                "retrieval_metrics": rm,
                "retrieval_gates": rg,
                "quality_policy_profile": qprof,
                "stage_a": sa,
                "proof_density": {
                    "method_window_visible_rate": meta.get("method_window_visible_rate"),
                    "explicit_method_body_evidence_present": meta.get("explicit_method_body_evidence_present"),
                    "execution_path_stitched": meta.get("execution_path_stitched"),
                    "stitched_edge_count": meta.get("stitched_edge_count"),
                    "stitched_edge_type": meta.get("stitched_edge_type"),
                    "stitch_confidence": meta.get("stitch_confidence"),
                    "owner_promoted_for_context": meta.get("owner_promoted_for_context"),
                    "owner_original_rank_in_bundle": meta.get("owner_original_rank_in_bundle"),
                    "method_claim_alignment_pass": meta.get("method_claim_alignment_pass"),
                },
            },
            "dev_snapshot": dev_snapshot,
        }

    if cap == "debug":
        base_q = str(scenario.get("query") or "How does alert correlation and enrichment work?")
        dq = str(scenario.get("debug_query") or "")
        sel = str(scenario.get("selected_file") or "")
        sel_text = str(scenario.get("selection") or "Investigate likely failure points and trace flow.")
        # Include selection text so camelCase hooks (beforeUpdate/getItem/parse/…) land in export query_tokens + hint extraction.
        export_q = " ".join(x for x in (dq, base_q, sel_text) if str(x).strip()).strip() if dq else f"{base_q} {sel_text}".strip()
        code, evidence = _post(
            f"{context_url}/v1/export_evidence",
            _export_evidence_payload(
                workspace_root,
                export_q,
                top_k,
                task_type="EXPLAIN_DEBUG",
                selected_file=sel or None,
                active_file=sel or None,
                enable_stage_a_v2=export_stage_a,
            ),
            timeout=300,
        )
        entries = evidence.get("entries") if isinstance(evidence.get("entries"), list) else []
        if code != 200 or not entries:
            return {
                "id": sid,
                "capability": cap,
                "description": desc,
                "pass": False,
                "errors": ["export_evidence failed for debug scenario"],
                "expect": expect,
                "actual_summary": None,
            }
        req = {
            "schema_version": "ask_request.v1.0",
            "request_id": str(uuid.uuid4()),
            "timestamp_utc": _utc_now(),
            "query": dq,
            "evidence_bundle": evidence,
            "task_type": "EXPLAIN_DEBUG",
            "selected_file": sel or (entries[0].get("relative_path") if entries else ""),
            "client_context": {"selection": sel_text},
        }
        if _scenario_flag(scenario, "requires_selected_file_binding"):
            if not str(req.get("selected_file") or "").strip():
                errors.append("requires_selected_file_binding: selected_file is required")
        if evidence.get("workspace_identity_hash"):
            req["expected_workspace_identity_hash"] = evidence["workspace_identity_hash"]
        code, resp = _post(f"{plan_gate_url}/v1/ask", req)
        ed = resp.get("explain_debug") if isinstance(resp.get("explain_debug"), dict) else {}
        cb_files = _context_bundle_files(resp)
        ctx_paths = [str(r.get("path") or "") for r in cb_files if isinstance(r, dict)]
        contract_errors: list[str] = []
        depth_errors: list[str] = []
        if expect.get("routing_mode") and resp.get("routing_mode") != expect["routing_mode"]:
            contract_errors.append(f"routing_mode want {expect['routing_mode']} got {resp.get('routing_mode')}")
        keys_req = expect.get("explain_debug_has_keys")
        if isinstance(keys_req, list):
            for k in keys_req:
                if k not in ed:
                    contract_errors.append(f"explain_debug missing key {k}")
        contract_errors.extend(
            _check_expect_debug_explain(expect, ed, str(req.get("selected_file") or ""), context_paths=ctx_paths)
        )
        contract_errors.extend(_check_expect_debug_method_body(expect, evidence))
        contract_errors.extend(_check_method_body_answer_alignment(expect, evidence, ed))
        depth_errors, depth_signals = _check_expect_debug_depth(expect, ed, str(req.get("selected_file") or ""))
        errors.extend(contract_errors)
        errors.extend(depth_errors)
        ok_body = code == 200 and ("summary" in ed or "error" in ed)
        contract_pass = len(contract_errors) == 0 and ok_body
        depth_pass = len(depth_errors) == 0
        dev_snapshot = {
            "routing_mode": resp.get("routing_mode"),
            "summary": ed.get("summary"),
            "likely_bug_risk": ed.get("likely_bug_risk"),
            "logic_flow": ed.get("logic_flow"),
            "error": ed.get("error"),
            "contract_errors": contract_errors,
            "depth_errors": depth_errors,
            "depth_signals": depth_signals,
            "selected_method_hints": ((evidence.get("fusion_diagnostics") or {}).get("selected_method_hints") if isinstance(evidence, dict) else None),
            "selected_method_body_present": ((evidence.get("fusion_diagnostics") or {}).get("selected_method_body_present") if isinstance(evidence, dict) else None),
            "selected_method_grounding_tier": ((evidence.get("fusion_diagnostics") or {}).get("selected_method_grounding_tier") if isinstance(evidence, dict) else None),
            "selected_method_grounding_rationale": ((evidence.get("fusion_diagnostics") or {}).get("selected_method_grounding_rationale") if isinstance(evidence, dict) else None),
        }
        return {
            "id": sid,
            "capability": cap,
            "description": desc,
            "pass": contract_pass and depth_pass,
            "contract_pass": contract_pass,
            "depth_pass": depth_pass,
            "errors": errors,
            "expect": expect,
            "actual_summary": {
                "http": code,
                "routing_mode": resp.get("routing_mode"),
                "has_summary": bool(ed.get("summary")),
                "contract_pass": contract_pass,
                "depth_pass": depth_pass,
                "depth_signals": depth_signals,
                "selected_method_hints": ((evidence.get("fusion_diagnostics") or {}).get("selected_method_hints") if isinstance(evidence, dict) else None),
                "selected_method_body_present": ((evidence.get("fusion_diagnostics") or {}).get("selected_method_body_present") if isinstance(evidence, dict) else None),
                "selected_method_grounding_tier": ((evidence.get("fusion_diagnostics") or {}).get("selected_method_grounding_tier") if isinstance(evidence, dict) else None),
            },
            "dev_snapshot": dev_snapshot,
        }

    if cap == "plan":
        plan_req: dict[str, Any] = {
            "schema_version": "plan_request.v0.1",
            "request_id": str(uuid.uuid4()),
            "timestamp_utc": _utc_now(),
            "mode": "shadow",
            "ide_event": {
                "schema_version": "ide_event.v0.1",
                "event_id": f"evt-scenario-{sid}",
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
                "evidence_refs": [{"type": "note", "ref": sid}],
            },
            "requested_capabilities": ["plan_and_decide"],
            "client_policy": {"fail_closed_if_gate_unreachable": True},
        }
        code, plan_resp = _post(f"{plan_gate_url}/v0/plan", plan_req)
        if _scenario_flag(scenario, "requires_playbook") and not plan_resp.get("decision"):
            errors.append("requires_playbook: plan response must include a decision")
        if expect.get("schema_version") and plan_resp.get("schema_version") != expect["schema_version"]:
            errors.append(f"schema_version want {expect['schema_version']} got {plan_resp.get('schema_version')}")
        if expect.get("decision_present") and not plan_resp.get("decision"):
            errors.append("decision missing")
        if "decision_any_of" in expect:
            allowed = expect.get("decision_any_of")
            if isinstance(allowed, list) and plan_resp.get("decision") not in allowed:
                errors.append(f"decision want one of {allowed} got {plan_resp.get('decision')}")
        return {
            "id": sid,
            "capability": cap,
            "description": desc,
            "pass": len(errors) == 0 and code == 200,
            "errors": errors,
            "expect": expect,
            "actual_summary": {
                "http": code,
                "decision": plan_resp.get("decision"),
                "decision_present": bool(plan_resp.get("decision")),
                "schema_version": plan_resp.get("schema_version"),
            },
        }

    if cap == "code":
        cmd = str(scenario.get("command") or "echo motadata-execute-probe")
        execute_repo_root = _execute_repo_root_for_plan_gate(workspace_root)
        execute_req = {
            "schema_version": "execute_request.v0.1",
            "request_id": str(uuid.uuid4()),
            "repo_root": execute_repo_root,
            "command": cmd,
        }
        code, execute_resp = _post(f"{plan_gate_url}/v0/execute", execute_req)
        if expect.get("schema_version") and execute_resp.get("schema_version") != expect["schema_version"]:
            errors.append(f"schema_version want {expect['schema_version']} got {execute_resp.get('schema_version')}")
        if "outcome" in expect and execute_resp.get("outcome") != expect["outcome"]:
            errors.append(f"outcome want {expect['outcome']} got {execute_resp.get('outcome')}")
        if "outcome_any_of" in expect:
            allowed_outcomes = expect.get("outcome_any_of")
            if isinstance(allowed_outcomes, list) and execute_resp.get("outcome") not in allowed_outcomes:
                errors.append(f"outcome want one of {allowed_outcomes} got {execute_resp.get('outcome')}")
        if "executed" in expect and execute_resp.get("executed") != expect["executed"]:
            errors.append(f"executed want {expect['executed']} got {execute_resp.get('executed')}")
        if "executed_any_of" in expect:
            allowed_executed = expect.get("executed_any_of")
            if isinstance(allowed_executed, list) and execute_resp.get("executed") not in allowed_executed:
                errors.append(f"executed want one of {allowed_executed} got {execute_resp.get('executed')}")
        if "posture" in expect and execute_resp.get("posture") != expect["posture"]:
            errors.append(f"posture want {expect['posture']} got {execute_resp.get('posture')}")
        if _bool_gate_enabled(expect.get("coherent_executed")):
            o = str(execute_resp.get("outcome") or "")
            ex = bool(execute_resp.get("executed"))
            if o == "EXECUTED" and not ex:
                errors.append("coherent_executed: outcome EXECUTED requires executed=True")
            if o in ("REFUSED", "BLOCKED") and ex:
                errors.append(f"coherent_executed: outcome {o} requires executed=False")
        return {
            "id": sid,
            "capability": cap,
            "description": desc,
            "pass": len(errors) == 0 and code == 200,
            "errors": errors,
            "expect": expect,
            "actual_summary": {
                "http": code,
                "command": cmd,
                "repo_root": execute_repo_root,
                "outcome": execute_resp.get("outcome"),
                "executed": execute_resp.get("executed"),
                "posture": execute_resp.get("posture"),
            },
        }

    if cap == "agent":
        aq = str(scenario.get("query") or "How does alert correlation and enrichment work?")
        code_a, evidence = _post(
            f"{context_url}/v1/export_evidence",
            _export_evidence_payload(workspace_root, aq, top_k, enable_stage_a_v2=export_stage_a),
            timeout=300,
        )
        entries = evidence.get("entries") if isinstance(evidence.get("entries"), list) else []
        assist = False
        if code_a == 200 and entries:
            req = {
                "schema_version": "ask_request.v1.0",
                "request_id": str(uuid.uuid4()),
                "timestamp_utc": _utc_now(),
                "query": str(scenario.get("query") or "smoke"),
                "evidence_bundle": evidence,
            }
            if evidence.get("workspace_identity_hash"):
                req["expected_workspace_identity_hash"] = evidence["workspace_identity_hash"]
            _, resp = _post(f"{plan_gate_url}/v1/ask", req)
            assist = "assist_layer" in resp
        code_probe, _ = _post(
            f"{plan_gate_url}/v0/agent",
            {"request_id": "agent-probe"},
            timeout=20,
            raise_for_status=False,
        )
        no_route = code_probe == 404
        if expect.get("agent_route_404") and not no_route:
            errors.append("expected /v0/agent 404")
        if expect.get("assist_layer_on_ask") and not assist:
            errors.append("expected assist_layer on ask response")
        return {
            "id": sid,
            "capability": cap,
            "description": desc,
            "pass": len(errors) == 0,
            "errors": errors,
            "expect": expect,
            "actual_summary": {"agent_route_404": no_route, "assist_layer": assist},
        }

    return {
        "id": sid,
        "capability": cap,
        "description": desc,
        "pass": False,
        "errors": [f"unknown capability: {cap}"],
        "expect": expect,
        "actual_summary": None,
    }


def _skipped_scenario_result(
    scenario: dict[str, Any],
    *,
    reason: str,
) -> dict[str, Any]:
    sid = str(scenario.get("id") or "unknown")
    cap = str(scenario.get("capability") or "")
    desc = scenario.get("description")
    expect = scenario.get("expect") if isinstance(scenario.get("expect"), dict) else {}
    return {
        "id": sid,
        "capability": cap,
        "description": desc,
        "pass": True,
        "skipped": True,
        "skip_reason": reason,
        "errors": [],
        "expect": expect,
        "actual_summary": {"skipped": True, "reason": reason},
    }


def run_scenario_suite(
    scenarios_path: Path,
    workspace_root: str,
    context_url: str,
    plan_gate_url: str,
    top_k: int,
    *,
    export_stage_a: Optional[bool] = None,
    quality_policy: dict[str, Any] | None = None,
    scenario_ids: Optional[set[str]] = None,
) -> dict[str, Any]:
    data = json.loads(scenarios_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "motadata_aiops_behavior_scenarios.v1":
        return {
            "file": str(scenarios_path),
            "all_pass": False,
            "error": "unsupported schema_version",
            "results": [],
        }
    defaults = data.get("defaults") if isinstance(data.get("defaults"), dict) else {}
    tk = int(defaults.get("top_k", top_k))
    preflight = _graph_preflight()
    if preflight.get("state") == "UNREACHABLE":
        return {
            "file": str(scenarios_path),
            "all_pass": False,
            "error": f"graph preflight failed: {preflight.get('reason')}",
            "graph_preflight": preflight,
            "results": [],
        }
    results: list[dict[str, Any]] = []
    file_ids: set[str] = set()
    for sc in data.get("scenarios") or []:
        if isinstance(sc, dict) and sc.get("id"):
            file_ids.add(str(sc["id"]))
    if scenario_ids:
        unknown = scenario_ids - file_ids
        if unknown:
            print(
                f"WARNING: --scenario-id not found in {scenarios_path}: {sorted(unknown)}",
                file=sys.stderr,
            )
    for sc in data.get("scenarios") or []:
        if not isinstance(sc, dict):
            continue
        sid = str(sc.get("id") or "")
        if scenario_ids is not None and sid not in scenario_ids:
            continue
        if preflight.get("state") == "INCOMPLETE" and _scenario_flag(sc, "requires_graph_path"):
            results.append(
                _skipped_scenario_result(
                    sc,
                    reason=(
                        "requires_graph_path skipped because Neo4j ingest is INCOMPLETE: "
                        f"{preflight.get('anchor_counts')}"
                    ),
                )
            )
            continue
        results.append(
            _run_scenario_row(
                sc,
                workspace_root,
                context_url,
                plan_gate_url,
                tk,
                export_stage_a=export_stage_a,
                quality_policy=quality_policy,
            )
        )
    all_pass = all(r.get("pass") for r in results) if results else False
    out: dict[str, Any] = {
        "file": str(scenarios_path),
        "all_pass": all_pass,
        "graph_preflight": preflight,
        "results": results,
    }
    if scenario_ids is not None:
        out["scenario_id_filter"] = sorted(scenario_ids)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Motadata AIOps behaviors end-to-end.")
    parser.add_argument("--workspace-root", required=True, help="Absolute path to Motadata workspace")
    parser.add_argument("--context-url", default="http://127.0.0.1:8091")
    parser.add_argument("--plan-gate-url", default="http://127.0.0.1:8089")
    parser.add_argument("--vllm-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--query",
        default="How does alert correlation and enrichment work?",
        help="Ask query for smoke run (align with production verification guide)",
    )
    parser.add_argument(
        "--debug-query",
        default="Debug why incident enrichment might be skipped",
        help="EXPLAIN_DEBUG query for smoke run",
    )
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--repeat", type=int, default=1, help="Number of repeated smoke runs for stability check")
    parser.add_argument(
        "--print",
        dest="print_mode",
        choices=["concise", "dev", "plain", "json"],
        default="concise",
        help="stdout: concise | dev (full answer + evidence) | plain (readable for any audience) | json",
    )
    parser.add_argument(
        "--scenarios",
        default="",
        help="Path to motadata_aiops_behavior_scenarios.v1.json (optional)",
    )
    parser.add_argument(
        "--scenario-id",
        action="append",
        default=None,
        metavar="ID",
        help=(
            "Run only scenario row(s) with this id from --scenarios (repeatable). "
            "Example: --scenario-id ask_broad_correlation --scenario-id code_echo_probe"
        ),
    )
    parser.add_argument(
        "--scenarios-only",
        action="store_true",
        help="Run only scenario suite(s) (skip smoke pipeline); requires --scenarios and/or --utility-scenarios",
    )
    parser.add_argument(
        "--utility-scenarios",
        default="",
        help="Path to motadata_developer_utility_scenarios.v1.json (developer usefulness / heuristic track)",
    )
    parser.add_argument(
        "--out",
        default="runtime/.run/motadata_behavior_validation.json",
        help="Output JSON report path",
    )
    parser.add_argument(
        "--plain-language",
        default="",
        help=(
            "Optional path to motadata_aiops_behavior_scenario_plain_language.v1.json. "
            "When omitted, the verifier uses docs/validation/... next to the m-coder repo root if that file exists."
        ),
    )
    parser.add_argument(
        "--export-stage-a",
        choices=["default", "on", "off"],
        default="default",
        help="POST /v1/export_evidence: set enable_stage_a_v2 true/false; default = omit (server uses env/LexicalRetrievalConfig)",
    )
    parser.add_argument(
        "--quality-policy",
        default="docs/validation/motadata_evidence_quality_policy.v1.json",
        help=(
            "Optional policy JSON for ask retrieval/evidence gates in scenario mode "
            "(set empty string to disable)."
        ),
    )
    args = parser.parse_args()
    ws_arg = str(args.workspace_root or "").strip()
    if not ws_arg:
        print(
            "ERROR: --workspace-root is empty. "
            "Set an absolute path to your Motadata checkout, e.g.\n"
            '  export MOTADATA_REPO_ROOT="/home/you/Projects/Motadata"\n'
            "then pass --workspace-root \"${MOTADATA_REPO_ROOT}\"",
            file=sys.stderr,
        )
        return 2
    if not Path(ws_arg).is_dir():
        print(
            f"ERROR: --workspace-root is not a directory: {ws_arg!r}",
            file=sys.stderr,
        )
        return 2
    args.workspace_root = ws_arg  # normalized
    export_stage_a = _export_stage_a_from_arg(args.export_stage_a)
    quality_policy: dict[str, Any] | None = None
    if str(args.quality_policy).strip():
        qp = Path(args.quality_policy)
        if not qp.is_file():
            print(f"ERROR: quality policy file not found: {qp}", file=sys.stderr)
            return 2
        try:
            quality_policy = _load_quality_policy(qp)
        except Exception as exc:
            print(f"ERROR: invalid quality policy file {qp}: {exc}", file=sys.stderr)
            return 2

    if args.scenarios_only and not str(args.scenarios).strip() and not str(args.utility_scenarios).strip():
        print(
            "ERROR: --scenarios-only requires --scenarios PATH and/or --utility-scenarios PATH",
            file=sys.stderr,
        )
        return 2

    context_url = args.context_url.rstrip("/")
    plan_gate_url = args.plan_gate_url.rstrip("/")
    vllm_url = args.vllm_url.rstrip("/")

    smoke_runs: list[dict[str, Any]] = []
    stable = True
    smoke_all = True
    if not args.scenarios_only:
        for _ in range(max(1, args.repeat)):
            smoke_runs.append(
                run_once(
                    workspace_root=args.workspace_root,
                    context_url=context_url,
                    plan_gate_url=plan_gate_url,
                    vllm_url=vllm_url,
                    query=args.query,
                    debug_query=args.debug_query,
                    top_k=args.top_k,
                    export_stage_a=export_stage_a,
                )
            )
        stable = len({_stable_signature(r) for r in smoke_runs}) == 1
        smoke_all = all(r.get("all_pass") for r in smoke_runs) and stable

    scenario_suite: dict[str, Any] | None = None
    if args.scenarios.strip():
        sp = Path(args.scenarios)
        if not sp.is_file():
            print(f"ERROR: scenarios file not found: {sp}", file=sys.stderr)
            return 2
        scenario_id_filter: Optional[set[str]] = None
        if getattr(args, "scenario_id", None):
            scenario_id_filter = {str(x) for x in args.scenario_id if str(x).strip()}
        scenario_suite = run_scenario_suite(
            sp,
            args.workspace_root,
            context_url,
            plan_gate_url,
            args.top_k,
            export_stage_a=export_stage_a,
            quality_policy=quality_policy,
            scenario_ids=scenario_id_filter,
        )
        plain_path, plain_err = _resolve_plain_language_path(str(args.plain_language or ""))
        if plain_err:
            print(f"ERROR: {plain_err}", file=sys.stderr)
            return 2
        narratives: dict[str, dict[str, str]] = {}
        if plain_path:
            try:
                narratives = _load_plain_narratives_file(plain_path)
            except Exception as exc:
                print(f"ERROR: invalid plain-language file {plain_path}: {exc}", file=sys.stderr)
                return 2
        if scenario_suite is not None:
            src = (
                str(plain_path.resolve())
                if plain_path
                else "fallback (built-in summaries only; add docs/validation/motadata_aiops_behavior_scenario_plain_language.v1.json in the m-coder repo)"
            )
            _enrich_scenario_suite_with_plain_language(scenario_suite, narratives, source=src)

    developer_utility_suite: dict[str, Any] | None = None
    if args.utility_scenarios.strip():
        up = Path(args.utility_scenarios)
        if not up.is_file():
            print(f"ERROR: utility scenarios file not found: {up}", file=sys.stderr)
            return 2
        developer_utility_suite = run_utility_scenario_suite(
            up,
            args.workspace_root,
            context_url,
            plan_gate_url,
            args.top_k,
            export_stage_a=export_stage_a,
        )

    smoke_payload: dict[str, Any] | None = None
    if not args.scenarios_only:
        smoke_payload = {
            "repeat": max(1, args.repeat),
            "stable": stable,
            "runs": [
                {"checks": r["checks"], "all_pass": r["all_pass"], "summary": _build_run_summary(r)} for r in smoke_runs
            ],
            "all_pass": smoke_all,
        }

    if args.scenarios_only:
        parts: list[bool] = []
        if scenario_suite is not None:
            parts.append(bool(scenario_suite.get("all_pass")))
        if developer_utility_suite is not None:
            parts.append(bool(developer_utility_suite.get("all_pass")))
        all_pass = bool(parts) and all(parts)
    else:
        all_pass = smoke_all
        if scenario_suite is not None:
            all_pass = all_pass and bool(scenario_suite.get("all_pass"))
        if developer_utility_suite is not None:
            all_pass = all_pass and bool(developer_utility_suite.get("all_pass"))

    final: dict[str, Any] = {
        "timestamp_utc": _utc_now(),
        "workspace_root": args.workspace_root,
        "all_pass": all_pass,
        "smoke": smoke_payload,
        "scenario_suite": scenario_suite,
        "developer_utility_suite": developer_utility_suite,
        "quality_policy": str(args.quality_policy).strip() or None,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(final, indent=2), encoding="utf-8")

    if args.print_mode == "json":
        print(json.dumps(final, indent=2))
    elif args.print_mode == "plain":
        _print_plain_report(
            final,
            workspace_root=args.workspace_root,
            out_path=out_path,
            scenarios_only=args.scenarios_only,
        )
    elif args.print_mode == "dev" and smoke_payload:
        dev_final = {
            "workspace_root": args.workspace_root,
            "repeat": smoke_payload["repeat"],
            "stable": smoke_payload["stable"],
            "all_pass": smoke_payload["all_pass"],
            "runs": smoke_payload["runs"],
        }
        _print_dev(dev_final)
    elif args.print_mode == "dev" and args.scenarios_only and (scenario_suite or developer_utility_suite):
        print("")
        print("=== Developer view: scenarios only (no smoke pipeline) ===")
        print(f"workspace: {args.workspace_root}")
        print(f"all_pass: {final.get('all_pass')}")
    elif not args.scenarios_only:
        dev_final = {
            "workspace_root": args.workspace_root,
            "repeat": smoke_payload["repeat"] if smoke_payload else 1,
            "stable": smoke_payload["stable"] if smoke_payload else True,
            "all_pass": smoke_payload["all_pass"] if smoke_payload else True,
            "runs": smoke_payload["runs"] if smoke_payload else [],
        }
        _print_concise(dev_final)

    if scenario_suite and args.print_mode not in ("json", "plain"):
        _print_scenario_results(scenario_suite, dev=args.print_mode == "dev")

    if developer_utility_suite and args.print_mode not in ("json", "plain"):
        _print_utility_scenario_results(developer_utility_suite, dev=args.print_mode == "dev")

    print(f"\nSaved: {out_path}")
    return 0 if final["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

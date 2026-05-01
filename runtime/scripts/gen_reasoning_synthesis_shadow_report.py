#!/usr/bin/env python3
"""
Offline shadow report: legacy Ask/Debug narration vs metadata.reasoning_synthesis.

Does not call governed Ask vLLM or ExplainDebug vLLM (mocked).

Usage (repo root):
  PYTHONPATH=. python3 runtime/scripts/gen_reasoning_synthesis_shadow_report.py
  PYTHONPATH=. python3 runtime/scripts/gen_reasoning_synthesis_shadow_report.py --extended

Outputs:
  docs/validation/REASONING_SYNTHESIS_SHADOW_REPORT.md (default)
  docs/validation/REASONING_SYNTHESIS_EXTENDED_SHADOW_REPORT.md (--extended)
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.ask_service.debug_narration_gate import DebugNarrationGateResult
from runtime.ask_service.reasoner import ExplainDebugResult
from runtime.ask_service.reasoning_synthesis import compute_shadow_rubric
from runtime.ask_service.v1_ingest import handle_ask_v1_request, validate_ask_v1_request

_GOLDEN = ROOT / "runtime" / "layer5" / "evidence" / "golden" / "evidence_bundle.v1.masked.json"
ASK_LIST = ROOT / "docs" / "validation" / "scenario_lists" / "ask_scenarios.txt"
DEBUG_LIST = ROOT / "docs" / "validation" / "scenario_lists" / "debug_scenarios.txt"
ADVERSARIAL_LIST = ROOT / "docs" / "validation" / "scenario_lists" / "reasoning_synthesis_adversarial_prompts.txt"
OUT_MD = ROOT / "docs" / "validation" / "REASONING_SYNTHESIS_SHADOW_REPORT.md"
OUT_EXTENDED = ROOT / "docs" / "validation" / "REASONING_SYNTHESIS_EXTENDED_SHADOW_REPORT.md"


def _load_evidence() -> dict:
    with open(_GOLDEN, encoding="utf-8") as f:
        return json.load(f)


def _legacy_text(resp: dict) -> str:
    aa = resp.get("articulated_answer") or {}
    paras = aa.get("paragraphs") if isinstance(aa, dict) else None
    if isinstance(paras, list) and paras:
        return "\n\n".join(str(p) for p in paras)
    ed = resp.get("explain_debug") or {}
    if isinstance(ed, dict) and not ed.get("error"):
        parts = []
        for k in ("summary", "logic_flow"):
            if ed.get(k):
                parts.append(str(ed[k]))
        return "\n\n".join(parts) if parts else ""
    return "(no articulated_answer or explain_debug body)"


def _stub_explain_debug(**_kwargs: object) -> ExplainDebugResult:
    return ExplainDebugResult(
        summary="Shadow stub: inspect branching and validation near the selected anchor.",
        logic_flow="Shadow stub: trace callers from the snippet outward.",
        likely_bug_risk="Shadow stub: compare runtime config vs persisted store when relevant.",
        evidence=["stub_evidence_line"],
        confidence_limits="Shadow stub: widen excerpt if hypothesis stays vague.",
    )


def _pass_debug_gate(
    result: ExplainDebugResult,
    *,
    selected_file: str,
    bundle: object,
) -> DebugNarrationGateResult:
    return DebugNarrationGateResult(curated=result, quality="STUB_PASS", issues=[])


def _one_row(
    *,
    suite: str,
    seq_id: int,
    query: str,
    resp: dict,
    selected_file: str = "",
) -> dict[str, Any]:
    md = resp.get("metadata") or {}
    syn = md.get("reasoning_synthesis") or {}
    legacy = _legacy_text(resp)
    rub = compute_shadow_rubric(
        legacy_answer_text=legacy,
        synthesis=syn if isinstance(syn, dict) else {},
        evidence_quality=str(md.get("evidence_quality") or ""),
    )
    mcr = syn.get("method_collapse_risk") if isinstance(syn, dict) else {}
    summary = str(syn.get("system_summary") or "") if isinstance(syn, dict) else ""
    row: dict[str, Any] = {
        "suite": suite,
        "id": seq_id,
        "query": query,
        "legacy_excerpt": legacy[:280].replace("\n", " ") + ("…" if len(legacy) > 280 else ""),
        "synthesis_summary": summary[:360].replace("\n", " ") + ("…" if len(summary) > 360 else ""),
        "subsystem": (syn.get("subsystem") or {}).get("label") if isinstance(syn, dict) else None,
        "collapse": mcr.get("detected") if isinstance(mcr, dict) else None,
        "distinct": (syn.get("synthesis_metrics") or {}).get("distinct_grounded_components")
        if isinstance(syn, dict)
        else None,
        "rubric": rub,
    }
    if selected_file:
        row["selected_file"] = selected_file
    return row


def _run_ask_file(
    evidence: dict,
    path: Path,
    suite: str,
    seq: int,
    rows: list[dict],
    notes: list[str],
) -> int:
    if not path.is_file():
        notes.append(f"missing file: {path}")
        return seq
    for line in path.read_text(encoding="utf-8").splitlines():
        q = line.strip()
        if not q or q.startswith("#"):
            continue
        seq += 1
        req = {
            "schema_version": "ask_request.v1.0",
            "request_id": f"shadow-{suite}-{seq}",
            "timestamp_utc": "2026-04-30T00:00:00Z",
            "query": q,
            "evidence_bundle": evidence,
            "revision": "shadow-report",
        }
        errs = validate_ask_v1_request(req)
        if errs:
            notes.append(f"{suite} scenario {seq} validation: {errs}")
            continue
        resp = handle_ask_v1_request(req)
        rows.append(_one_row(suite=suite, seq_id=seq, query=q, resp=resp))
    return seq


def _run_debug_file(evidence: dict, seq: int, rows: list[dict], notes: list[str]) -> int:
    if not DEBUG_LIST.is_file():
        return seq
    for line in DEBUG_LIST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" not in line:
            notes.append(f"debug skip (no pipe): {line[:80]}")
            continue
        path_part, qry = line.split("|", 1)
        path_part, qry = path_part.strip(), qry.strip()
        if not path_part or not qry:
            continue
        seq += 1
        req = {
            "schema_version": "ask_request.v1.0",
            "request_id": f"shadow-debug-{seq}",
            "timestamp_utc": "2026-04-30T00:00:00Z",
            "query": qry,
            "task_type": "EXPLAIN_DEBUG",
            "selected_file": path_part,
            "evidence_bundle": evidence,
            "revision": "shadow-report",
            "client_context": {"selection": "// shadow stub selection"},
        }
        errs = validate_ask_v1_request(req)
        if errs:
            notes.append(f"debug scenario {seq} validation: {errs}")
            continue
        resp = handle_ask_v1_request(req)
        rows.append(
            _one_row(
                suite="debug",
                seq_id=seq,
                query=qry,
                resp=resp,
                selected_file=path_part,
            )
        )
    return seq


def _run_scenarios(evidence: dict, *, extended: bool) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    notes: list[str] = []
    seq = 0
    with patch("runtime.ask_service.v1_ingest.try_governed_ask_narration", return_value=None):
        with patch("runtime.ask_service.v1_ingest.explain_debug", side_effect=_stub_explain_debug):
            with patch(
                "runtime.ask_service.v1_ingest.apply_debug_narration_gate",
                side_effect=_pass_debug_gate,
            ):
                seq = _run_ask_file(evidence, ASK_LIST, "ask", seq, rows, notes)
                if extended:
                    seq = _run_ask_file(evidence, ADVERSARIAL_LIST, "adversarial", seq, rows, notes)
                seq = _run_debug_file(evidence, seq, rows, notes)
    return rows, notes


def _rollup(rows: list[dict]) -> dict[str, Any]:
    if not rows:
        return {}
    rubs = [r.get("rubric") or {} for r in rows]
    depths = [int(x.get("depth_score") or 0) for x in rubs]
    fl = [int(x.get("fluency_score") or 0) for x in rubs]
    gr = [int(x.get("grounding_score") or 0) for x in rubs]
    oc = [int(x.get("overclaim_risk") or 0) for x in rubs]
    mc = sum(1 for x in rubs if x.get("method_collapse_detected"))
    oc_hist: dict[int, int] = {}
    for v in oc:
        oc_hist[v] = oc_hist.get(v, 0) + 1
    collapse_syn = sum(1 for r in rows if r.get("collapse") is True)
    return {
        "n": len(rows),
        "avg_depth": statistics.mean(depths) if depths else 0,
        "avg_fluency": statistics.mean(fl) if fl else 0,
        "avg_grounding": statistics.mean(gr) if gr else 0,
        "method_collapse_rubric_true": mc,
        "method_collapse_synthesis_true": collapse_syn,
        "overclaim_histogram": oc_hist,
    }


def _markdown(rows: list[dict], notes: list[str]) -> str:
    iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stat = _rollup(rows)
    lines = [
        "# Reasoning synthesis shadow report",
        "",
        f"Generated: {iso}",
        "",
        "Compares **legacy narration** (`articulated_answer` or `explain_debug` stub) with "
        "**metadata.reasoning_synthesis** (Phase A/B only; Ask prose unchanged). "
        "Explain/Debug calls are **stubbed** to avoid vLLM.",
        "",
        "## Summary rollup",
        "",
    ]
    if not rows:
        lines.append("(no scenario rows)")
    else:
        lines.append(f"- Scenarios: **{stat.get('n', 0)}**")
        lines.append(
            f"- Synthesis `method_collapse_risk.detected` true: **{stat.get('method_collapse_synthesis_true', 0)}**"
        )
        lines.append(
            f"- Rubric `method_collapse_detected` true: **{stat.get('method_collapse_rubric_true', 0)}**"
        )
        lines.append(f"- Avg depth / fluency / grounding: **{stat.get('avg_depth', 0):.2f}** / **{stat.get('avg_fluency', 0):.2f}** / **{stat.get('avg_grounding', 0):.2f}**")
        oh = stat.get("overclaim_histogram") or {}
        lines.append(f"- Overclaim histogram: `{oh}`")
        lines.append("")
    if notes:
        lines.extend(["## Notes", ""])
        lines.extend(f"- {n}" for n in notes[:20])
        lines.append("")
    lines.extend(
        [
            "## Per scenario",
            "",
            "| Suite | # | Subsystem | Collapse | Distinct | depth | fluency | grounding | overclaim | m-collapse | Legacy (excerpt) |",
            "|-------|---|-----------|----------|----------|-------|---------|-----------|-----------|------------|------------------|",
        ]
    )
    for r in rows:
        rub = r.get("rubric") or {}
        lines.append(
            "| {suite} | {id} | {sub} | {col} | {dist} | {d} | {f} | {g} | {o} | {mc} | {leg} |".format(
                suite=r.get("suite", ""),
                id=r.get("id", ""),
                sub=r.get("subsystem") or "",
                col=r.get("collapse"),
                dist=r.get("distinct"),
                d=rub.get("depth_score"),
                f=rub.get("fluency_score"),
                g=rub.get("grounding_score"),
                o=rub.get("overclaim_risk"),
                mc=rub.get("method_collapse_detected"),
                leg=str(r.get("legacy_excerpt") or "").replace("|", "\\|"),
            )
        )
    lines.extend(
        [
            "",
            "## Regenerate",
            "",
            "```bash",
            "PYTHONPATH=. python3 runtime/scripts/gen_reasoning_synthesis_shadow_report.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _markdown_extended(rows: list[dict], notes: list[str]) -> str:
    iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stat = _rollup(rows)
    lines = [
        "# Reasoning synthesis **extended** shadow report",
        "",
        f"Generated: {iso}",
        "",
        "Includes **ask_scenarios**, **debug_scenarios**, and **reasoning_synthesis_adversarial_prompts**. "
        "Legacy narration unchanged; Explain/Debug **stubbed**. "
        "Use for taxonomy stress — not for production debug quality.",
        "",
        "## Aggregate stats",
        "",
        f"- Total rows: **{stat.get('n', 0)}**",
        f"- `method_collapse_risk.detected` true: **{stat.get('method_collapse_synthesis_true', 0)}**",
        f"- Rubric `method_collapse_detected` true: **{stat.get('method_collapse_rubric_true', 0)}**",
        f"- Avg **depth** / **fluency** / **grounding**: **{stat.get('avg_depth', 0):.2f}** / **{stat.get('avg_fluency', 0):.2f}** / **{stat.get('avg_grounding', 0):.2f}**",
        f"- **overclaim_risk** histogram: `{stat.get('overclaim_histogram', {})}`",
        "",
    ]
    if notes:
        lines.extend(["## Notes", ""])
        lines.extend(f"- {n}" for n in notes[:30])
        lines.append("")
    lines.extend(
        [
            "## Per scenario",
            "",
            "| Suite | # | Subsystem | Collapse | Distinct | D | F | G | OC | MCol | Legacy (excerpt) | Synthesis `system_summary` (excerpt) |",
            "|-------|---|-----------|----------|----------|---|---|---|---|------|------------------|--------------------------------------|",
        ]
    )
    for r in rows:
        rub = r.get("rubric") or {}
        lines.append(
            "| {suite} | {id} | {sub} | {col} | {dist} | {d} | {f} | {g} | {o} | {mc} | {leg} | {syn} |".format(
                suite=r.get("suite", ""),
                id=r.get("id", ""),
                sub=str(r.get("subsystem") or "").replace("|", "\\|"),
                col=r.get("collapse"),
                dist=r.get("distinct"),
                d=rub.get("depth_score"),
                f=rub.get("fluency_score"),
                g=rub.get("grounding_score"),
                o=rub.get("overclaim_risk"),
                mc=rub.get("method_collapse_detected"),
                leg=str(r.get("legacy_excerpt") or "").replace("|", "\\|"),
                syn=str(r.get("synthesis_summary") or "").replace("|", "\\|"),
            )
        )
    lines.extend(
        [
            "",
            "## Regenerate",
            "",
            "```bash",
            "PYTHONPATH=. python3 runtime/scripts/gen_reasoning_synthesis_shadow_report.py --extended",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate reasoning synthesis shadow reports.")
    ap.add_argument(
        "--extended",
        action="store_true",
        help=f"Include adversarial prompts; write {OUT_EXTENDED.name}",
    )
    args = ap.parse_args()
    ev = _load_evidence()
    rows, notes = _run_scenarios(ev, extended=bool(args.extended))
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    if args.extended:
        OUT_EXTENDED.write_text(_markdown_extended(rows, notes), encoding="utf-8")
        print(f"Wrote {OUT_EXTENDED} ({len(rows)} rows)")
    else:
        OUT_MD.write_text(_markdown(rows, notes), encoding="utf-8")
        print(f"Wrote {OUT_MD} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

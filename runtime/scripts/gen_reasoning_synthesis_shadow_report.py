#!/usr/bin/env python3
"""
Offline shadow report: legacy Ask/Debug narration vs metadata.reasoning_synthesis.

Does not call governed Ask vLLM or ExplainDebug vLLM (mocked).
Writes docs/validation/REASONING_SYNTHESIS_SHADOW_REPORT.md

Usage (repo root):
  PYTHONPATH=. python3 runtime/scripts/gen_reasoning_synthesis_shadow_report.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
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
OUT_MD = ROOT / "docs" / "validation" / "REASONING_SYNTHESIS_SHADOW_REPORT.md"


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


def _run_scenarios(evidence: dict) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    notes: list[str] = []
    i = 0
    with patch("runtime.ask_service.v1_ingest.try_governed_ask_narration", return_value=None):
        with patch("runtime.ask_service.v1_ingest.explain_debug", side_effect=_stub_explain_debug):
            with patch(
                "runtime.ask_service.v1_ingest.apply_debug_narration_gate",
                side_effect=_pass_debug_gate,
            ):
                if ASK_LIST.is_file():
                    for line in ASK_LIST.read_text(encoding="utf-8").splitlines():
                        q = line.strip()
                        if not q or q.startswith("#"):
                            continue
                        i += 1
                        req = {
                            "schema_version": "ask_request.v1.0",
                            "request_id": f"shadow-ask-{i}",
                            "timestamp_utc": "2026-04-30T00:00:00Z",
                            "query": q,
                            "evidence_bundle": evidence,
                            "revision": "shadow-report",
                        }
                        errs = validate_ask_v1_request(req)
                        if errs:
                            notes.append(f"ask scenario {i} validation: {errs}")
                            continue
                        resp = handle_ask_v1_request(req)
                        md = resp.get("metadata") or {}
                        syn = md.get("reasoning_synthesis") or {}
                        legacy = _legacy_text(resp)
                        rub = compute_shadow_rubric(
                            legacy_answer_text=legacy,
                            synthesis=syn if isinstance(syn, dict) else {},
                            evidence_quality=str(md.get("evidence_quality") or ""),
                        )
                        mcr = syn.get("method_collapse_risk") if isinstance(syn, dict) else {}
                        rows.append(
                            {
                                "suite": "ask",
                                "id": i,
                                "query": q,
                                "legacy_excerpt": legacy[:280].replace("\n", " ") + ("…" if len(legacy) > 280 else ""),
                                "subsystem": (syn.get("subsystem") or {}).get("label"),
                                "collapse": mcr.get("detected") if isinstance(mcr, dict) else None,
                                "distinct": (syn.get("synthesis_metrics") or {}).get(
                                    "distinct_grounded_components"
                                ),
                                "rubric": rub,
                            }
                        )

                if DEBUG_LIST.is_file():
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
                        i += 1
                        req = {
                            "schema_version": "ask_request.v1.0",
                            "request_id": f"shadow-debug-{i}",
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
                            notes.append(f"debug scenario {i} validation: {errs}")
                            continue
                        resp = handle_ask_v1_request(req)
                        md = resp.get("metadata") or {}
                        syn = md.get("reasoning_synthesis") or {}
                        legacy = _legacy_text(resp)
                        rub = compute_shadow_rubric(
                            legacy_answer_text=legacy,
                            synthesis=syn if isinstance(syn, dict) else {},
                            evidence_quality=str(md.get("evidence_quality") or ""),
                        )
                        mcr = syn.get("method_collapse_risk") if isinstance(syn, dict) else {}
                        rows.append(
                            {
                                "suite": "debug",
                                "id": i,
                                "query": qry,
                                "selected_file": path_part,
                                "legacy_excerpt": legacy[:280].replace("\n", " ") + ("…" if len(legacy) > 280 else ""),
                                "subsystem": (syn.get("subsystem") or {}).get("label"),
                                "collapse": mcr.get("detected") if isinstance(mcr, dict) else None,
                                "distinct": (syn.get("synthesis_metrics") or {}).get(
                                    "distinct_grounded_components"
                                ),
                                "rubric": rub,
                            }
                        )

    return rows, notes


def _markdown(rows: list[dict], notes: list[str]) -> str:
    iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
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
        collapse_true = sum(1 for r in rows if r.get("collapse") is True)
        lines.append(f"- Scenarios: **{len(rows)}**")
        lines.append(f"- Synthesis `method_collapse_risk.detected` true: **{collapse_true}**")
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
    lines.extend(["", "## Regenerate", "", "```bash", "PYTHONPATH=. python3 runtime/scripts/gen_reasoning_synthesis_shadow_report.py", "```", ""])
    return "\n".join(lines)


def main() -> int:
    ev = _load_evidence()
    rows, notes = _run_scenarios(ev)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(_markdown(rows, notes), encoding="utf-8")
    print(f"Wrote {OUT_MD} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

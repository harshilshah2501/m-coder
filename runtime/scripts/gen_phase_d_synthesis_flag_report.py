#!/usr/bin/env python3
"""
Compare Ask articulated_answer with MCODER_REASONING_SYNTHESIS_V1 off vs on.

Uses golden evidence_bundle and ask_scenarios.txt + adversarial prompts (Ask rows only).
Writes docs/validation/PHASE_D_SYNTHESIS_FLAG_REPORT.md

Usage:
  PYTHONPATH=. python3 runtime/scripts/gen_phase_d_synthesis_flag_report.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_GOLDEN = ROOT / "runtime" / "layer5" / "evidence" / "golden" / "evidence_bundle.v1.masked.json"
ASK_LIST = ROOT / "docs" / "validation" / "scenario_lists" / "ask_scenarios.txt"
ADV_LIST = ROOT / "docs" / "validation" / "scenario_lists" / "reasoning_synthesis_adversarial_prompts.txt"
OUT = ROOT / "docs" / "validation" / "PHASE_D_SYNTHESIS_FLAG_REPORT.md"


def _load_evidence() -> dict:
    with open(_GOLDEN, encoding="utf-8") as f:
        return json.load(f)


def _paragraphs(resp: dict) -> str:
    aa = resp.get("articulated_answer") or {}
    paras = aa.get("paragraphs") if isinstance(aa, dict) else []
    if not isinstance(paras, list):
        return ""
    return "\n\n".join(str(p) for p in paras)


def _shape(resp: dict) -> str:
    aa = resp.get("articulated_answer") or {}
    return str(aa.get("shape") or "") if isinstance(aa, dict) else ""


def _run(evidence: dict, rows: list[tuple[str, str]]) -> list[dict]:
    from runtime.ask_service.v1_ingest import handle_ask_v1_request, validate_ask_v1_request

    out: list[dict] = []
    with patch("runtime.ask_service.v1_ingest.try_governed_ask_narration", return_value=None):
        for label, query in rows:
            req = {
                "schema_version": "ask_request.v1.0",
                "request_id": f"phase-d-{label}",
                "timestamp_utc": "2026-05-01T00:00:00Z",
                "query": query,
                "evidence_bundle": evidence,
                "revision": "phase-d-report",
            }
            errs = validate_ask_v1_request(req)
            if errs:
                continue

            os.environ.pop("MCODER_REASONING_SYNTHESIS_V1", None)
            legacy = handle_ask_v1_request(req)
            os.environ["MCODER_REASONING_SYNTHESIS_V1"] = "1"
            synth = handle_ask_v1_request(req)
            os.environ.pop("MCODER_REASONING_SYNTHESIS_V1", None)

            lt = _paragraphs(legacy)
            st = _paragraphs(synth)
            out.append(
                {
                    "label": label,
                    "query": query,
                    "legacy_shape": _shape(legacy),
                    "synth_shape": _shape(synth),
                    "legacy_excerpt": lt[:400].replace("\n", " ") + ("…" if len(lt) > 400 else ""),
                    "synth_excerpt": st[:400].replace("\n", " ") + ("…" if len(st) > 400 else ""),
                    "synthesis_on": _shape(synth) == "synthesis_first_v1",
                }
            )
    return out


def _collect_queries() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for path, prefix in ((ASK_LIST, "ask"), (ADV_LIST, "adv")):
        if not path.is_file():
            continue
        i = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            q = line.strip()
            if not q or q.startswith("#"):
                continue
            i += 1
            rows.append((f"{prefix}-{i}", q))
    return rows


def _markdown(data: list[dict]) -> str:
    iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    syn_rows = sum(1 for d in data if d.get("synthesis_on"))
    lines = [
        "# Phase D — synthesis flag comparison (`MCODER_REASONING_SYNTHESIS_V1`)",
        "",
        f"Generated: {iso}",
        "",
        "For each Ask query: **`legacy`** = flag unset; **`synthesis`** = `MCODER_REASONING_SYNTHESIS_V1=1`. "
        "Governed Ask narration stubbed off. Explain/Debug not used.",
        "",
        "## Rollup",
        "",
        f"- Rows: **{len(data)}**",
        f"- Rows using `shape=synthesis_first_v1` when flag on: **{syn_rows}**",
        "",
        "Banned phrases checked on synthesis excerpts: `distinct grounded`, `Multi-hop elaboration`, `Primary authority anchor` (should be absent).",
        "",
        "## Per query",
        "",
        "| Label | synthesis_first_v1? | Legacy (excerpt) | Synthesis flag (excerpt) |",
        "|-------|----------------------|------------------|----------------------------|",
    ]
    banned = ("distinct grounded", "multi-hop elaboration", "primary authority anchor")
    for d in data:
        se = d.get("synth_excerpt") or ""
        bad = any(b in se.lower() for b in banned)
        flag = "✓" if d.get("synthesis_on") else ""
        lines.append(
            "| {label} | {fl} | {leg} | {syn} |".format(
                label=d.get("label", ""),
                fl=flag,
                leg=str(d.get("legacy_excerpt") or "").replace("|", "\\|")[:200],
                syn=(str(se).replace("|", "\\|")[:200]) + (" **BANNED**" if bad else ""),
            )
        )
    lines.extend(
        [
            "",
            "## Regenerate",
            "",
            "```bash",
            "PYTHONPATH=. python3 runtime/scripts/gen_phase_d_synthesis_flag_report.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    ev = _load_evidence()
    rows = _collect_queries()
    data = _run(ev, rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(_markdown(data), encoding="utf-8")
    print(f"Wrote {OUT} ({len(data)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

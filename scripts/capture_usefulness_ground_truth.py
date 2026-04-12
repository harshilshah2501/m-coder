#!/usr/bin/env python3
"""
Emit markdown: ground-truth usefulness table from AIOps MVP artifact dirs.

For each scenario_*/export_response.json + ask_response.json:
  - quality_reasons, dominance core_code_in_top_k_pct from ask_response (if present)
  - operator_hints + usefulness_metrics recomputed via runtime (matches Plan-Gate @ usefulness metadata commit)

Usage:
  PYTHONPATH=. python3 scripts/capture_usefulness_ground_truth.py /path/to/aiops_mvp
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.layer5.evidence.usefulness_metrics import bundle_usefulness_metrics  # noqa: E402
from runtime.layer5.retrieval.quality_gate import (  # noqa: E402
    assess_evidence_quality,
    operator_hints_for_assessment,
)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: capture_usefulness_ground_truth.py <aiops_mvp_root>", file=sys.stderr)
        sys.exit(2)
    root = Path(sys.argv[1]).resolve()
    scenarios = sorted(root.glob("scenario_*"))
    if not scenarios:
        print(f"No scenario_* under {root}", file=sys.stderr)
        sys.exit(1)

    print("# Ground truth capture — usefulness failure modes\n")
    print(f"**Artifact root:** `{root}`\n")
    print(
        "**Note:** If `ask_response.json` predates Plan-Gate build with `metadata.operator_hints` / "
        "`metadata.usefulness_metrics`, those columns are **recomputed** from `export_response.json` "
        "using this repo’s `assess_evidence_quality`, `operator_hints_for_assessment`, and "
        "`bundle_usefulness_metrics` (same logic as v1 ingest).\n"
    )
    print("## Summary table\n")
    print(
        "| ID | evidence_quality | quality_reasons | core_code_in_top_k_pct | anchor / non-anchor | "
        "operator_hints (recomputed) |"
    )
    print("|----|------------------|-----------------|------------------------|---------------------|------------------------------|")

    for d in scenarios:
        exp_path = d / "export_response.json"
        ask_path = d / "ask_response.json"
        if not exp_path.exists():
            continue
        sid = d.name.replace("scenario_", "")
        with open(exp_path, encoding="utf-8") as f:
            bundle = json.load(f)
        meta = {}
        if ask_path.exists():
            with open(ask_path, encoding="utf-8") as f:
                meta = (json.load(f).get("metadata")) or {}

        query = str(bundle.get("query_raw") or "")
        paths = [str(e.get("relative_path") or "") for e in (bundle.get("entries") or []) if isinstance(e, dict)]
        qa = assess_evidence_quality(query, paths)
        hints = operator_hints_for_assessment(qa)
        um = bundle_usefulness_metrics(bundle.get("entries") or [])

        eq = meta.get("evidence_quality", qa.evidence_quality)
        reasons = meta.get("quality_reasons")
        if reasons is None:
            reasons = list(qa.quality_reasons)
        dm = meta.get("dominance_metrics") or qa.dominance_metrics
        core = dm.get("core_code_in_top_k_pct", "")

        reasons_s = ", ".join(reasons) if isinstance(reasons, list) else str(reasons)
        hints_s = " ".join(hints).replace("|", "\\|")
        if len(hints_s) > 120:
            hints_s = hints_s[:117] + "…"
        print(
            f"| {sid} | {eq} | {reasons_s} | {core} | "
            f"{um['snippet_anchor_hits']} / {um['snippet_non_anchor_hits']} | {hints_s} |"
        )

    print("\n## Per-scenario detail\n")
    for d in scenarios:
        exp_path = d / "export_response.json"
        if not exp_path.exists():
            continue
        sid = d.name.replace("scenario_", "")
        with open(exp_path, encoding="utf-8") as f:
            bundle = json.load(f)
        query = str(bundle.get("query_raw") or "")
        paths = [str(e.get("relative_path") or "") for e in (bundle.get("entries") or []) if isinstance(e, dict)]
        qa = assess_evidence_quality(query, paths)
        hints = operator_hints_for_assessment(qa)
        um = bundle_usefulness_metrics(bundle.get("entries") or [])
        entries = bundle.get("entries") or []
        first_txt = ""
        if entries and isinstance(entries[0], dict):
            sn = entries[0].get("snippet") or {}
            first_txt = (sn.get("text") or "")[:200].replace("\n", " ").strip()

        print(f"### {sid}\n")
        print(f"- **quality_reasons:** `{list(qa.quality_reasons)}`")
        print(f"- **operator_hints (recomputed):**")
        for h in hints:
            print(f"  - {h}")
        print(f"- **core_code_in_top_k_pct:** `{qa.dominance_metrics.get('core_code_in_top_k_pct')}`")
        print(
            f"- **snippet_anchor_hits / snippet_non_anchor_hits:** "
            f"`{um['snippet_anchor_hits']}` / `{um['snippet_non_anchor_hits']}` "
            f"(from bundle `snippet.selection_reason`)"
        )
        print(f"- **Rank-0 snippet preview (first ~200 chars):** `{first_txt}`")
        print(
            "- **Visible snippet quality (human judgment):** "
            "*Edit after review — template default: see rank-0 preview above.*\n"
        )


if __name__ == "__main__":
    main()

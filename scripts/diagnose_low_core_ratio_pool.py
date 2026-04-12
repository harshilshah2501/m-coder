#!/usr/bin/env python3
"""
Proof harness for LOW_CORE_RATIO: count core_aiops_code files in global lexical top-20,
full ranked list, and top-12 after the same pipeline as export. Optionally runs
``assess_evidence_quality`` (same gate as Plan-Gate ingest uses for paths).

Decision (see docs/validation/LOW_CORE_RATIO_DECISION.md):
- global_core_total < 4 → not fixable by reordering alone.
- global_core_total ≥ 4 but top-20 count < 4 → head-sparse only; composition pulls from full list.

Usage:
  export MOTADATA_ROOT=/path/to/Motadata
  export PYTHONPATH=/path/to/m-coder
  python3 scripts/diagnose_low_core_ratio_pool.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval.config import LexicalRetrievalConfig
from runtime.layer5.retrieval.lexical import global_lexical_sorted_hits, retrieve_lexical
from runtime.layer5.retrieval.policy import classify_file
from runtime.layer5.retrieval.quality_gate import assess_evidence_quality
from runtime.layer5.workspace.resolver import ResolverConfig, WorkspaceResolver


def _is_core(rel: str) -> bool:
    return classify_file(rel).file_class == "core_aiops_code"


def main() -> int:
    root = (os.environ.get("MOTADATA_ROOT") or "").strip()
    if not root or not Path(root).is_dir():
        print("ERROR: set MOTADATA_ROOT to a Motadata workspace root.", file=sys.stderr)
        return 2

    scenarios_path = REPO / "docs" / "validation" / "aiops_mvp_scenarios.v1.json"
    doc = json.loads(scenarios_path.read_text(encoding="utf-8"))
    scenarios = doc["scenarios"]
    cfg = LexicalRetrievalConfig()

    resolver = WorkspaceResolver(ResolverConfig())
    identity, err = resolver.resolve(root)
    if err or not identity:
        print(f"ERROR: resolve failed: {err}", file=sys.stderr)
        return 2
    idx = build_file_index(identity)

    print(
        "scenario | core_top20 | global_core_total | core_top12 | LOW_CORE_RATIO? | gate_reasons"
    )
    print("--- | ---: | ---: | ---: | :--- | ---")

    for s in scenarios:
        sid = s["id"]
        q = s["query"]
        ranked = global_lexical_sorted_hits(idx, q, cfg)
        top20 = ranked[:20]
        n20 = sum(1 for h in top20 if _is_core(h.relative_path))
        gtotal = sum(1 for h in ranked if _is_core(h.relative_path))
        res = retrieve_lexical(idx, q, top_k=12, config=cfg)
        paths = [h.relative_path for h in res.hits]
        n12 = sum(1 for p in paths if _is_core(p))
        a = assess_evidence_quality(q, paths)
        low = "LOW_CORE_RATIO" in a.quality_reasons
        reasons = ",".join(a.quality_reasons) if a.quality_reasons else "—"
        print(f"{sid} | {n20} | {gtotal} | {n12} | {low} | {reasons}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

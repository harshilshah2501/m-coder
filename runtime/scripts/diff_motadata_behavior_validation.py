#!/usr/bin/env python3
"""
Compare two motadata_behavior_validation.json (or compatible) reports.

Focus: ask scenarios — context_bundle paths, retrieval_metrics, Stage A lane_counts / pool_paths.

Usage:
  python3 runtime/scripts/diff_motadata_behavior_validation.py \\
    runtime/.run/baseline.json runtime/.run/motadata_behavior_validation.json

Exit 1 if any ask scenario differs on paths or metrics (use --soft for exit 0).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _scenario_results(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize scenario suite shape from verifier output."""
    ss = doc.get("scenario_suite")
    if isinstance(ss, dict) and isinstance(ss.get("results"), list):
        return [x for x in ss["results"] if isinstance(x, dict)]
    # Alternate: top-level results only
    r = doc.get("results")
    if isinstance(r, list):
        return [x for x in r if isinstance(x, dict)]
    return []


def _cb_paths_from_dev(dev: dict[str, Any]) -> list[str]:
    rows = dev.get("context_bundle_files") or []
    out: list[str] = []
    for row in rows:
        if isinstance(row, dict) and row.get("path"):
            out.append(str(row["path"]))
    return out


def _diff_ask(a: dict[str, Any], b: dict[str, Any], *, soft: bool) -> list[str]:
    lines: list[str] = []
    sid = str(a.get("id") or b.get("id") or "?")
    da = a.get("dev_snapshot") if isinstance(a.get("dev_snapshot"), dict) else {}
    db = b.get("dev_snapshot") if isinstance(b.get("dev_snapshot"), dict) else {}
    pa = _cb_paths_from_dev(da)
    pb = _cb_paths_from_dev(db)
    if pa != pb:
        lines.append(f"  [{sid}] context_bundle.files CHANGED")
        lines.append(f"    A ({len(pa)}): {pa[:12]}{'...' if len(pa) > 12 else ''}")
        lines.append(f"    B ({len(pb)}): {pb[:12]}{'...' if len(pb) > 12 else ''}")

    ma = (a.get("actual_summary") or {}).get("retrieval_metrics") or {}
    mb = (b.get("actual_summary") or {}).get("retrieval_metrics") or {}
    if isinstance(ma, dict) and isinstance(mb, dict):
        keys = (
            "generic_infra_ratio",
            "owner_in_top1",
            "owner_in_top3",
            "anchor_hit_rate_at_k",
            "distractor_count_at_k",
        )
        for k in keys:
            if ma.get(k) != mb.get(k):
                lines.append(f"  [{sid}] retrieval_metrics.{k}: {ma.get(k)} -> {mb.get(k)}")

    sa = da.get("stage_a") if isinstance(da.get("stage_a"), dict) else {}
    sb = db.get("stage_a") if isinstance(db.get("stage_a"), dict) else {}
    if sa or sb:
        if (sa.get("lane_counts") or {}) != (sb.get("lane_counts") or {}):
            lines.append(f"  [{sid}] stage_a.lane_counts: {sa.get('lane_counts')} -> {sb.get('lane_counts')}")
        ppa = sa.get("pool_paths") or []
        ppb = sb.get("pool_paths") or []
        if isinstance(ppa, list) and isinstance(ppb, list) and ppa != ppb:
            lines.append(f"  [{sid}] stage_a.pool_paths differ (A={len(ppa)} B={len(ppb)} paths)")
            # Show first divergence
            for i, (xa, xb) in enumerate(zip(ppa, ppb)):
                if xa != xb:
                    lines.append(f"    first_diff_index={i}: {xa!r} vs {xb!r}")
                    break
            else:
                if len(ppa) != len(ppb):
                    lines.append(f"    length_mismatch: {len(ppa)} vs {len(ppb)}")
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description="Diff two Motadata behavior validation JSON reports.")
    ap.add_argument("baseline", type=Path, help="Earlier run JSON (e.g. pre–Stage A)")
    ap.add_argument("candidate", type=Path, help="Newer run JSON")
    ap.add_argument(
        "--soft",
        action="store_true",
        help="Always exit 0 (still print diffs)",
    )
    args = ap.parse_args()

    doc_a = _load(args.baseline)
    doc_b = _load(args.candidate)
    ra = _scenario_results(doc_a)
    rb = _scenario_results(doc_b)
    by_id_a = {str(x.get("id")): x for x in ra}
    by_id_b = {str(x.get("id")): x for x in rb}
    ids = sorted(set(by_id_a.keys()) | set(by_id_b.keys()))

    all_lines: list[str] = []
    print(f"baseline:  {args.baseline}")
    print(f"candidate: {args.candidate}")
    print("")

    for sid in ids:
        a, b = by_id_a.get(sid), by_id_b.get(sid)
        if a is None or b is None:
            all_lines.append(f"  [missing] scenario id only in one file: {sid}")
            continue
        ca = str(a.get("capability") or "")
        if ca != "ask":
            continue
        all_lines.extend(_diff_ask(a, b, soft=bool(args.soft)))

    if not all_lines:
        print("No ask-scenario diffs on context_bundle.files, retrieval_metrics, or stage_a.")
        return 0

    print("=== Diffs (ask scenarios) ===")
    for line in all_lines:
        print(line)
    return 0 if args.soft else 1


if __name__ == "__main__":
    sys.exit(main())

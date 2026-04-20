#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import List

# Allow direct script execution without requiring PYTHONPATH exports.
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from runtime.learning.governed_sft_dataset import (
    collect_events_from_files,
    filter_events_by_eligibility,
)


def _expand_inputs(paths_or_globs: List[str]) -> List[Path]:
    out: List[Path] = []
    seen = set()
    for item in paths_or_globs:
        p = Path(item)
        if p.exists() and p.is_file():
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                out.append(rp)
            continue
        matches = [Path(x).resolve() for x in sorted(glob.glob(item, recursive=True))]
        for m in matches:
            if m.is_file() and m not in seen:
                seen.add(m)
                out.append(m)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build governed SFT dataset rows from Ask/assist artifacts."
    )
    ap.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="File paths and/or glob patterns to artifact JSON files.",
    )
    ap.add_argument("--out", required=True, help="Output JSONL path")
    ap.add_argument(
        "--summary-out",
        default="",
        help="Optional summary JSON output path",
    )
    ap.add_argument(
        "--allow-eligibility",
        nargs="+",
        default=["gold", "silver"],
        help="Eligibility labels to include (default: gold silver)",
    )
    ap.add_argument(
        "--default-assist-delta",
        choices=["improved", "same", "degraded_minor", "degraded_major"],
        default="same",
        help="Assist delta for plain Ask responses without assist eval envelope.",
    )
    args = ap.parse_args()

    files = _expand_inputs(args.inputs)
    if not files:
        raise SystemExit("No input files matched.")

    events, stats = collect_events_from_files(
        files,
        default_assist_delta=args.default_assist_delta,
    )
    filtered = filter_events_by_eligibility(events, args.allow_eligibility)
    eligibility_counts: dict[str, int] = {}
    hard_violation_counts: dict[str, int] = {}
    for ev in events:
        eg = str(ev.reward.get("eligibility") or "unknown")
        eligibility_counts[eg] = eligibility_counts.get(eg, 0) + 1
        for hv in ev.reward.get("hard_violations", []):
            h = str(hv)
            hard_violation_counts[h] = hard_violation_counts.get(h, 0) + 1

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8") as f:
        for ev in filtered:
            f.write(json.dumps(ev.to_dict(), ensure_ascii=True) + "\n")

    summary = {
        **stats,
        "eligibility_counts": eligibility_counts,
        "hard_violation_counts": hard_violation_counts,
        "events_after_filter": len(filtered),
        "allowed_eligibility": args.allow_eligibility,
        "output_jsonl": str(outp),
    }
    print(json.dumps(summary, indent=2))

    if args.summary_out.strip():
        sp = Path(args.summary_out)
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


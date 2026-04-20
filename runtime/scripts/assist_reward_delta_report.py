#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from runtime.learning.governed_reward import score_governed_response


def _infer_assist_delta(payload: Dict[str, Any]) -> str:
    verdict = str(payload.get("final_verdict", "")).strip().lower()
    if verdict in {"improved", "same", "degraded_minor", "degraded_major"}:
        return verdict
    if verdict != "degraded":
        return "same"
    core = ((payload.get("comparison") or {}).get("core_flags") or {})
    stable = all(
        bool(core.get(k, True))
        for k in ("governance_posture_equal", "execution_equal", "routing_mode_equal")
    )
    return "degraded_minor" if stable else "degraded_major"


def _is_plan_only_response(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    if "governance_posture" in obj and "plan_summary" in obj:
        return True
    sv = str(obj.get("schema_version", "")).strip().lower()
    return sv.startswith("plan_only_response")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compute baseline vs candidate governed reward deltas for assist-v2 artifacts."
    )
    ap.add_argument(
        "--inputs",
        default="docs/validation/artifacts/assist_layer_v2_eval/assist_v2_batch_*.json",
        help="Glob pattern for assist eval JSON files.",
    )
    ap.add_argument("--out", required=True, help="Output JSON report path")
    args = ap.parse_args()

    rows: List[Dict[str, Any]] = []
    hv_counts: Dict[str, int] = {}
    for fp in sorted(glob.glob(args.inputs)):
        payload = json.loads(Path(fp).read_text(encoding="utf-8"))
        baseline = payload.get("path_a_baseline_original")
        candidate = payload.get("path_b_candidate_augmented")
        if not _is_plan_only_response(baseline) or not _is_plan_only_response(candidate):
            continue
        assist_delta = _infer_assist_delta(payload)
        rb = score_governed_response(baseline, assist_delta="same").to_dict()
        rc = score_governed_response(candidate, assist_delta=assist_delta).to_dict()
        for hv in rc.get("hard_violations", []):
            hv_counts[str(hv)] = hv_counts.get(str(hv), 0) + 1
        rows.append(
            {
                "file": fp,
                "request_id": payload.get("request_id", ""),
                "final_verdict": payload.get("final_verdict", "unknown"),
                "assist_delta_used": assist_delta,
                "baseline_total": rb["total_reward"],
                "candidate_total": rc["total_reward"],
                "delta": rc["total_reward"] - rb["total_reward"],
                "baseline_eligibility": rb["eligibility"],
                "candidate_eligibility": rc["eligibility"],
                "candidate_hard_violations": rc.get("hard_violations", []),
            }
        )

    summary = {
        "count": len(rows),
        "delta_positive": sum(1 for r in rows if r["delta"] > 0),
        "delta_zero": sum(1 for r in rows if r["delta"] == 0),
        "delta_negative": sum(1 for r in rows if r["delta"] < 0),
        "mean_delta": round(sum(r["delta"] for r in rows) / len(rows), 4) if rows else 0.0,
        "eligibility_transitions": {},
        "candidate_hard_violation_counts": hv_counts,
        "top_positive": sorted(rows, key=lambda r: r["delta"], reverse=True)[:5],
        "top_negative": sorted(rows, key=lambda r: r["delta"])[:5],
    }
    for r in rows:
        key = f"{r['baseline_eligibility']}->{r['candidate_eligibility']}"
        summary["eligibility_transitions"][key] = summary["eligibility_transitions"].get(key, 0) + 1

    out = {"schema_version": "assist_reward_delta_summary.v1", "summary": summary, "rows": rows}
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"saved: {outp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


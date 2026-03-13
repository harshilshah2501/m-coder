"""Plan-Gate Stub Runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .rules import stub_decide
from .validate import validate_all, validate_schemas


def main() -> int:
    ap = argparse.ArgumentParser(description="Plan-Gate Stub Runner (protocol plumbing)")
    ap.add_argument("--input", required=True, help="Path to plan_request.json")
    ap.add_argument("--outdir", required=True, help="Output directory")
    ap.add_argument("--mode", default="shadow", choices=["shadow", "live"])
    ap.add_argument("--fixed-time", default=None, help="Fixed timestamp for determinism")
    ap.add_argument("--lineage-index", default=None, help="Path to lineage index (optional)")
    ap.add_argument("--validate", type=bool, default=True, help="Validate outputs (default True)")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        plan_request = json.load(f)
    if args.fixed_time:
        plan_request["timestamp_utc"] = args.fixed_time

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    lineage_path = Path(args.lineage_index) if args.lineage_index else None
    artifacts = stub_decide(plan_request, args.mode, args.fixed_time, repo_root, lineage_path)

    if args.validate:
        schema_errs = validate_schemas(
            artifacts["plan"],
            artifacts["decision_response"],
            artifacts["ledger_row"],
            artifacts["shadow_run_record"],
            artifacts["ingestion_batch"],
        )
        if schema_errs:
            for e in schema_errs:
                print(f"schema error: {e}", file=sys.stderr)
            return 1
        rule_errs = validate_all(
            artifacts["plan"],
            artifacts["decision_response"],
            artifacts["ledger_row"],
            artifacts["shadow_run_record"],
            artifacts["ingestion_batch"],
        )
        if rule_errs:
            for e in rule_errs:
                print(f"rule violation: {e}", file=sys.stderr)
            return 1

    (outdir / "plan.json").write_text(json.dumps(artifacts["plan"], indent=2), encoding="utf-8")
    (outdir / "decision_response.json").write_text(
        json.dumps(artifacts["decision_response"], indent=2), encoding="utf-8"
    )
    (outdir / "ledger_row.json").write_text(
        json.dumps(artifacts["ledger_row"], indent=2), encoding="utf-8"
    )
    (outdir / "shadow_run_record.json").write_text(
        json.dumps(artifacts["shadow_run_record"], indent=2), encoding="utf-8"
    )
    (outdir / "ingestion_batch.json").write_text(
        json.dumps(artifacts["ingestion_batch"], indent=2), encoding="utf-8"
    )

    batch_path = outdir / "ingestion_batch.jsonl"
    batch_path.write_text(json.dumps(artifacts["ingestion_batch"]) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

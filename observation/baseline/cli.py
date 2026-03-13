"""Shadow Baseline Runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from observation.ingest.reconcile import reconcile_items
from observation.ingest.validate import validate_item_rules, validate_item_schemas

from .compare import DEFAULT_THRESHOLDS, compare
from .load import load_all
from .metrics import compute_metrics
from .report import baseline_report_to_md, build_baseline_report, build_drift_report, drift_report_to_md


def main() -> int:
    ap = argparse.ArgumentParser(description="Shadow Baseline Runner")
    ap.add_argument("--inputs", action="append", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--mode", required=True, choices=["baseline", "compare"])
    ap.add_argument("--baseline", default=None)
    ap.add_argument("--fixed-time", default=None)
    ap.add_argument("--strict", action="store_true", default=True)
    ap.add_argument("--no-strict", dest="strict", action="store_false")
    ap.add_argument("--drift-thresholds", default=None)
    args = ap.parse_args()

    paths = [Path(p) for p in args.inputs]
    items, files, batch_errors = load_all(paths)
    if not items and not batch_errors:
        print("error: no ingestion batches found", file=sys.stderr)
        return 2

    schema_errors = list(batch_errors)
    rule_errors = []
    for i, item in enumerate(items):
        for e in validate_item_schemas(item):
            schema_errors.append(f"item {i}: {e}")
        for v in validate_item_rules(item):
            rule_errors.append(f"item {i}: {v}")
    if args.strict and (schema_errors or rule_errors):
        for e in schema_errors + rule_errors:
            print(e, file=sys.stderr)
        return 2

    reconcile_errors = reconcile_items(items)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    fixed_time = args.fixed_time or "2026-03-01T00:00:00Z"

    if args.mode == "baseline":
        report = build_baseline_report(items, files, reconcile_errors, fixed_time)
        (outdir / "baseline_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        (outdir / "baseline_report.md").write_text(baseline_report_to_md(report), encoding="utf-8")
        return 0

    if args.mode == "compare":
        if not args.baseline:
            print("error: --baseline required in compare mode", file=sys.stderr)
            return 2
        baseline_path = Path(args.baseline)
        if not baseline_path.exists():
            print(f"error: baseline not found: {baseline_path}", file=sys.stderr)
            return 2
        baseline_report = json.loads(baseline_path.read_text())
        current_metrics = compute_metrics(items)
        thresholds = DEFAULT_THRESHOLDS.copy()
        if args.drift_thresholds:
            if Path(args.drift_thresholds).exists():
                thresholds.update(json.loads(Path(args.drift_thresholds).read_text()))
            else:
                thresholds.update(json.loads(args.drift_thresholds))
        drift_flags, severity, rec = compare(
            baseline_report.get("metrics", {}), current_metrics, thresholds
        )
        report = build_drift_report(
            baseline_report, current_metrics, drift_flags, severity, rec, fixed_time
        )
        (outdir / "drift_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        (outdir / "drift_report.md").write_text(drift_report_to_md(report), encoding="utf-8")
        return 1 if severity in ("WARN", "ALERT") else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Observation ingest CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .reconcile import reconcile_items
from .report import build_report, report_to_md
from .validate import load_json, validate_batch_schema, validate_item_rules, validate_item_schemas

REPO = Path(__file__).resolve().parents[2]
SHADOW_SCHEMAS = REPO / "runtime" / "shadow" / "schemas"


def load_batches(path: Path) -> tuple[list[dict], list[str], list[str]]:
    """Load items from JSON or JSONL. Returns (items, input_files, batch_errors)."""
    items = []
    files = [str(path)]
    batch_errors = []
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        for i, line in enumerate(raw.strip().split("\n")):
            if line.strip():
                batch = json.loads(line)
                if batch.get("schema_version") == "ingestion_batch.v0.1":
                    for e in validate_batch_schema(batch):
                        batch_errors.append(f"line {i + 1}: {e}")
                    items.extend(batch.get("items", []))
    else:
        batch = json.loads(raw)
        if batch.get("schema_version") == "ingestion_batch.v0.1":
            batch_errors = validate_batch_schema(batch)
            items = batch.get("items", [])
    return items, files, batch_errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Observation ingest")
    ap.add_argument("--input", required=True, help="Path to .json or .jsonl")
    ap.add_argument("--outdir", required=True, help="Output directory")
    ap.add_argument("--fixed-time", default=None)
    ap.add_argument("--format", choices=["json", "jsonl"], default=None)
    ap.add_argument(
        "--no-strict",
        action="store_true",
        help="Continue on validation errors (default: strict; errors stop run)",
    )
    args = ap.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"error: {path} not found", file=sys.stderr)
        return 1

    items, input_files, batch_errors = load_batches(path)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    schema_errors = list(batch_errors)
    rule_errors = []
    for i, item in enumerate(items):
        for e in validate_item_schemas(item):
            schema_errors.append(f"item {i}: {e}")
        for v in validate_item_rules(item):
            rule_errors.append(f"item {i}: {v}")
    strict = not args.no_strict
    if strict and (schema_errors or rule_errors):
        for e in schema_errors + rule_errors:
            print(e, file=sys.stderr)
        return 1

    reconcile_errors = reconcile_items(items)
    report = build_report(items, input_files, reconcile_errors, args.fixed_time)

    (outdir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (outdir / "report.md").write_text(report_to_md(report), encoding="utf-8")
    if reconcile_errors:
        (outdir / "reconciliation_errors.json").write_text(
            json.dumps(reconcile_errors, indent=2), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

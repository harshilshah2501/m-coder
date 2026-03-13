"""Load ingestion batches from files/directories."""

from __future__ import annotations

import json
from pathlib import Path

from observation.ingest.validate import validate_batch_schema


def collect_inputs(paths: list[Path]) -> list[Path]:
    out = []
    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        if p.is_file():
            if p.suffix.lower() in (".json", ".jsonl"):
                out.append(p)
        else:
            for f in sorted(p.rglob("*.json")) + sorted(p.rglob("*.jsonl")):
                out.append(f)
    return sorted(set(out))


def load_items_from_file(path: Path) -> tuple[list[dict], list[str]]:
    items, errors = [], []
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        for i, line in enumerate(raw.strip().split("\n")):
            if line.strip():
                batch = json.loads(line)
                if batch.get("schema_version") == "ingestion_batch.v0.1":
                    for e in validate_batch_schema(batch):
                        errors.append(f"line {i + 1}: {e}")
                    items.extend(batch.get("items", []))
    else:
        batch = json.loads(raw)
        if batch.get("schema_version") == "ingestion_batch.v0.1":
            errors = validate_batch_schema(batch)
            items = batch.get("items", [])
    return items, errors


def load_all(paths: list[Path]) -> tuple[list[dict], list[str], list[str]]:
    files = collect_inputs(paths)
    all_items, all_errors = [], []
    for f in files:
        items, errs = load_items_from_file(f)
        all_items.extend(items)
        all_errors.extend(errs)
    return all_items, [str(p) for p in files], all_errors

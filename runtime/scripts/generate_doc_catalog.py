#!/usr/bin/env python3
"""Generate docs/index/doc_catalog.json from curated source.

Usage:
  python3 runtime/scripts/generate_doc_catalog.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = REPO_ROOT / "docs/index/doc_catalog.source.json"
OUTPUT_PATH = REPO_ROOT / "docs/index/doc_catalog.json"

VALID_ROLES = {
    "canonical",
    "index",
    "runbook",
    "operations",
    "reference",
    "validation",
}


def _load_source() -> dict[str, Any]:
    raw = SOURCE_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Source must be a JSON object.")
    return data


def _validate_entry(entry: dict[str, Any], seen_ids: set[str]) -> dict[str, Any]:
    required = {"id", "title", "path", "role", "tags"}
    missing = required - set(entry.keys())
    if missing:
        raise ValueError(f"Entry missing fields {sorted(missing)}: {entry}")

    entry_id = str(entry["id"]).strip()
    if not entry_id:
        raise ValueError(f"Entry has empty id: {entry}")
    if entry_id in seen_ids:
        raise ValueError(f"Duplicate entry id: {entry_id}")
    seen_ids.add(entry_id)

    title = str(entry["title"]).strip()
    path = str(entry["path"]).strip()
    role = str(entry["role"]).strip()
    tags = entry["tags"]

    if not title:
        raise ValueError(f"Entry '{entry_id}' has empty title.")
    if not path.startswith("docs/"):
        raise ValueError(f"Entry '{entry_id}' path must start with 'docs/': {path}")
    if role not in VALID_ROLES:
        raise ValueError(f"Entry '{entry_id}' has invalid role '{role}'.")
    if not isinstance(tags, list) or not tags:
        raise ValueError(f"Entry '{entry_id}' tags must be a non-empty list.")
    if any(not str(tag).strip() for tag in tags):
        raise ValueError(f"Entry '{entry_id}' has an empty tag.")

    full_path = REPO_ROOT / path
    if not full_path.exists():
        raise ValueError(f"Entry '{entry_id}' path not found: {path}")

    return {
        "id": entry_id,
        "title": title,
        "path": path,
        "role": role,
        "tags": [str(tag).strip() for tag in tags],
    }


def build_catalog(source: dict[str, Any]) -> dict[str, Any]:
    entries = source.get("entrypoints")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Source entrypoints must be a non-empty list.")

    seen_ids: set[str] = set()
    normalized_entries: list[dict[str, Any]] = []
    for raw in entries:
        if not isinstance(raw, dict):
            raise ValueError(f"Entry must be an object: {raw}")
        normalized_entries.append(_validate_entry(raw, seen_ids))

    return {
        "schema_version": "docs.catalog.v1",
        "generated_by": "runtime/scripts/generate_doc_catalog.py",
        "description": str(
            source.get(
                "description",
                "Compact documentation routing index for operators, developers, and validators.",
            )
        ).strip(),
        "entrypoints": normalized_entries,
    }


def main() -> None:
    source = _load_source()
    catalog = build_catalog(source)
    OUTPUT_PATH.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} ({len(catalog['entrypoints'])} entries)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Compute SHA256 hashes for candidate duplicate groups.
Only runs when EXECUTE=1 in repo_reorg_plan/config.
Source: repo_audit/DUPLICATES_EXACT.md
"""
import hashlib
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "repo_reorg_plan" / "config"
EXECUTE = "0"

def load_config():
    global EXECUTE
    if CONFIG.exists():
        for line in CONFIG.read_text().splitlines():
            if line.startswith("EXECUTE="):
                EXECUTE = line.split("=", 1)[1].strip()
                break

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

PHASE6C = REPO_ROOT / "ml" / "training" / "src" / "sources" / "Motadata" / "phase6" / "phase6c"
CANDIDATE_GROUPS = [
    [
        str(PHASE6C / "out" / "smoke_traces.jsonl"),
        str(PHASE6C / "out_m3" / "smoke_traces.jsonl"),
        str(PHASE6C / "out_m4" / "smoke_traces.jsonl"),
    ],
    [
        str(REPO_ROOT / "archive" / "okr" / "supporting-docs" / "EXEMPLAR_AUTHORING_GUIDE.md"),
        str(REPO_ROOT / "ml" / "training" / "sft" / "exemplars" / "guides" / "archives" / "engineering-first-regrounding" / "EXEMPLAR_AUTHORING_GUIDE.md"),
    ],
]

def main():
    load_config()
    if EXECUTE != "1":
        print("EXECUTE != 1. Skipping hash computation. Set EXECUTE=1 in repo_reorg_plan/config to run.")
        return 0

    results = []
    for paths in CANDIDATE_GROUPS:
        group = []
        for p in paths:
            path = Path(p)
            if path.exists():
                rel = str(path.relative_to(REPO_ROOT))
                group.append((rel, sha256(path)))
        if group:
            results.append({"group": paths, "hashes": dict(group)})

    print(json.dumps(results, indent=2))
    return 0

if __name__ == "__main__":
    exit(main())

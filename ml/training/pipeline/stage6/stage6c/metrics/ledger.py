"""Append and read ledger rows (JSONL). One row per run."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def append_ledger_row(row: Dict[str, Any], path: str | Path) -> None:
    """Append one ledger row as a JSON line. path can be to existing or new file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_ledger_rows(path: str | Path) -> List[Dict[str, Any]]:
    """Read all ledger rows from a JSONL file."""
    path = Path(path)
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out

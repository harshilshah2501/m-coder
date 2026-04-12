from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.layer5.audit.l58_dataset import load_golden_cases


_AUDIT_DIR = Path(__file__).resolve().parents[1] / "audit"
_DATASET = _AUDIT_DIR / "fixtures" / "l58_golden_queries.v1.json"


def test_l58_dataset_loads_and_is_deterministic() -> None:
    rows = load_golden_cases(_DATASET)
    assert rows
    ids = [r.id for r in rows]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))


def test_l58_dataset_rejects_duplicate_ids(tmp_path: Path) -> None:
    raw = json.loads(_DATASET.read_text(encoding="utf-8"))
    assert len(raw["cases"]) >= 2
    raw["cases"][1]["id"] = raw["cases"][0]["id"]
    path = tmp_path / "dup.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate case IDs"):
        load_golden_cases(path)

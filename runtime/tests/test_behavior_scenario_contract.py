from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_PATH = REPO_ROOT / "docs" / "validation" / "motadata_aiops_behavior_scenarios.v1.json"


def test_scenario_contract_has_balanced_20_slice() -> None:
    data = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "motadata_aiops_behavior_scenarios.v1"

    scenarios = data.get("scenarios")
    assert isinstance(scenarios, list)
    assert len(scenarios) == 20

    counts = Counter(str(row.get("capability") or "") for row in scenarios if isinstance(row, dict))
    assert counts == {"ask": 5, "debug": 5, "plan": 5, "code": 5}


def test_scenario_contract_includes_expect_actual_keys() -> None:
    data = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    scenarios = data.get("scenarios") if isinstance(data.get("scenarios"), list) else []
    for row in scenarios:
        assert isinstance(row, dict)
        assert isinstance(row.get("id"), str) and row["id"].strip()
        assert row.get("capability") in {"ask", "debug", "plan", "code"}
        expect = row.get("expect")
        assert isinstance(expect, dict), f"scenario {row.get('id')} must include expect mapping"

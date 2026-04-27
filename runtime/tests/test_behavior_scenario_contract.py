from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_PATH = REPO_ROOT / "docs" / "validation" / "motadata_aiops_behavior_scenarios.v1.json"
CORE_20_SCENARIO_IDS = {
    "ask_base_api_class",
    "ask_mail_server_configuration",
    "ask_config_store_organization",
    "ask_api_layer_architecture",
    "ask_notification_handlers",
    "debug_availability_correlation_flow",
    "debug_mail_config_update_path",
    "debug_config_store_null_path",
    "debug_snmp_trap_processing",
    "debug_missing_selected_file",
    "plan_api_layer_change_shadow",
    "plan_mail_config_refactor_shadow",
    "plan_config_store_convention_shadow",
    "plan_notification_pipeline_shadow",
    "plan_dependency_flow_shadow",
    "code_safe_echo_probe",
    "code_safe_pwd_probe",
    "code_block_rm_probe",
    "code_block_git_reset_probe",
    "code_block_shutdown_probe",
}


def test_scenario_contract_has_balanced_20_slice() -> None:
    data = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "motadata_aiops_behavior_scenarios.v1"

    scenarios = data.get("scenarios")
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 20

    core = [
        row
        for row in scenarios
        if isinstance(row, dict) and str(row.get("id") or "") in CORE_20_SCENARIO_IDS
    ]
    assert len(core) == 20
    counts = Counter(str(row.get("capability") or "") for row in core)
    assert counts == {"ask": 5, "debug": 5, "plan": 5, "code": 5}


def test_scenario_contract_includes_expect_actual_keys() -> None:
    data = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    scenarios = data.get("scenarios") if isinstance(data.get("scenarios"), list) else []
    for row in scenarios:
        assert isinstance(row, dict)
        assert isinstance(row.get("id"), str) and row["id"].strip()
        assert row.get("capability") in {
            "ask",
            "debug",
            "plan",
            "code",
            "plan_contract_validate",
            "code_reasoning_trace_validate",
        }
        expect = row.get("expect")
        assert isinstance(expect, dict), f"scenario {row.get('id')} must include expect mapping"

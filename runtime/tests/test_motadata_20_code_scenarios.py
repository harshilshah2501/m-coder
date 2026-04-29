"""
Offline enforcement of the five **code** rows from docs/guides/MOTADATA_20_SCENARIO_PRIMER.md.

These mirror `motadata_behavior_verify.py` code-scenario `expect` checks against the local
`handle_execute_request` implementation (no HTTP Plan-Gate). Full-stack verification remains:
  python3 runtime/scripts/motadata_behavior_verify.py ... --scenarios-only
"""

from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path
from typing import Any

import pytest

from runtime.execute_service.handlers import handle_execute_request

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_PATH = REPO_ROOT / "docs" / "validation" / "motadata_aiops_behavior_scenarios.v1.json"

CODE_SCENARIO_IDS_20 = frozenset(
    {
        "code_safe_echo_probe",
        "code_safe_pwd_probe",
        "code_block_rm_probe",
        "code_block_git_reset_probe",
        "code_block_shutdown_probe",
    }
)


def _bool_gate_enabled(v: Any) -> bool:
    return bool(v) is True


def _errors_for_code_expect(expect: dict[str, Any], resp: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if expect.get("schema_version") and resp.get("schema_version") != expect["schema_version"]:
        errors.append(f"schema_version want {expect['schema_version']} got {resp.get('schema_version')}")
    if "outcome" in expect and resp.get("outcome") != expect["outcome"]:
        errors.append(f"outcome want {expect['outcome']} got {resp.get('outcome')}")
    if "outcome_any_of" in expect:
        allowed = expect.get("outcome_any_of")
        if isinstance(allowed, list) and resp.get("outcome") not in allowed:
            errors.append(f"outcome want one of {allowed} got {resp.get('outcome')}")
    if "executed" in expect and resp.get("executed") != expect["executed"]:
        errors.append(f"executed want {expect['executed']} got {resp.get('executed')}")
    if "executed_any_of" in expect:
        allowed = expect.get("executed_any_of")
        if isinstance(allowed, list) and resp.get("executed") not in allowed:
            errors.append(f"executed want one of {allowed} got {resp.get('executed')}")
    if _bool_gate_enabled(expect.get("coherent_executed")):
        o = str(resp.get("outcome") or "")
        ex = bool(resp.get("executed"))
        if o == "EXECUTED" and not ex:
            errors.append("coherent_executed: outcome EXECUTED requires executed=True")
        if o in ("REFUSED", "BLOCKED") and ex:
            errors.append(f"coherent_executed: outcome {o} requires executed=False")
    return errors


def _load_code_scenarios_20() -> list[dict[str, Any]]:
    data = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    rows = [s for s in data.get("scenarios") or [] if isinstance(s, dict)]
    out = []
    for row in rows:
        sid = str(row.get("id") or "")
        if sid in CODE_SCENARIO_IDS_20 and str(row.get("capability") or "") == "code":
            out.append(row)
    assert len(out) == 5, f"expected 5 primer code scenarios in JSON, got {len(out)}"
    return out


@pytest.mark.parametrize("scenario", _load_code_scenarios_20(), ids=lambda s: str(s.get("id")))
def test_primer_code_scenario_contract_against_execute_handler(scenario: dict[str, Any]) -> None:
    expect = scenario.get("expect")
    assert isinstance(expect, dict), scenario.get("id")
    cmd = str(scenario.get("command") or "echo motadata-execute-probe")

    with tempfile.TemporaryDirectory() as tmp:
        req = {
            "schema_version": "execute_request.v0.1",
            "request_id": str(uuid.uuid4()),
            "repo_root": tmp,
            "command": cmd,
        }
        resp = handle_execute_request(req)

    errs = _errors_for_code_expect(expect, resp)
    assert not errs, f"id={scenario.get('id')} errors={errs} outcome={resp.get('outcome')} executed={resp.get('executed')}"

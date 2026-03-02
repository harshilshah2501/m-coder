"""Request handling for plan-gate service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.plan_gate_stub.rules import stub_decide

from . import config

REPO = Path(__file__).resolve().parents[2]  # runtime/
IDE_SCHEMAS = REPO / "runtime" / "ide" / "schemas"


def load_schema(name: str) -> dict:
    with open(IDE_SCHEMAS / name, encoding="utf-8") as f:
        return json.load(f)


def validate_plan_request(data: dict) -> list[str]:
    """Validate against plan_request.v0.1.schema.json. Returns list of errors."""
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema not installed"]
    schema = load_schema("plan_request.v0.1.schema.json")
    errs = []
    for e in jsonschema.Draft7Validator(schema).iter_errors(data):
        errs.append(e.message)
    return errs


def handle_plan_request(
    plan_request: dict,
    mode: str,
    fixed_time: str | None,
    spool_root: Path,
    date_or_id: str,
) -> tuple[dict, Path]:
    """
    Process PlanRequest, emit artifacts, return (decision_response, spool_dir).
    """
    if fixed_time:
        plan_request = dict(plan_request)
        plan_request["timestamp_utc"] = fixed_time

    lineage_path = config.get_lineage_index()
    artifacts = stub_decide(
        plan_request, mode, fixed_time, REPO,
        lineage_index_path=str(lineage_path) if lineage_path else None,
    )
    req_id = artifacts["plan"]["request"]["request_id"]

    outdir = spool_root / date_or_id / req_id
    from .spool import write_artifacts

    write_artifacts(
        spool_root,
        date_or_id,
        req_id,
        artifacts["plan"],
        artifacts["decision_response"],
        artifacts["ledger_row"],
        artifacts["shadow_run_record"],
        artifacts["ingestion_batch"],
    )
    return artifacts["decision_response"], outdir

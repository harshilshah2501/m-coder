"""Spool writer for plan-gate artifacts. Matches stub format for byte-for-byte determinism."""

from __future__ import annotations

import json
from pathlib import Path


def _dumps(obj: object) -> str:
    """Match stub CLI exactly: indent=2, same defaults."""
    return json.dumps(obj, indent=2)


def _dumps_compact(obj: object) -> str:
    """Single-line for JSONL, matches stub."""
    return json.dumps(obj)


def write_artifacts(
    spool_root: Path,
    date_or_id: str,
    request_id: str,
    plan: dict,
    decision_response: dict,
    ledger_row: dict,
    shadow_run_record: dict,
    ingestion_batch: dict,
) -> Path:
    """
    Write artifacts to spool/<date_or_id>/<request_id>/.
    Returns the directory path.
    """
    outdir = spool_root / date_or_id / request_id
    outdir.mkdir(parents=True, exist_ok=True)

    (outdir / "plan.json").write_text(_dumps(plan), encoding="utf-8")
    (outdir / "decision_response.json").write_text(
        _dumps(decision_response), encoding="utf-8"
    )
    (outdir / "ledger_row.json").write_text(
        _dumps(ledger_row), encoding="utf-8"
    )
    (outdir / "shadow_run_record.json").write_text(
        _dumps(shadow_run_record), encoding="utf-8"
    )
    (outdir / "ingestion_batch.json").write_text(
        _dumps(ingestion_batch), encoding="utf-8"
    )
    (outdir / "ingestion_batch.jsonl").write_text(
        _dumps_compact(ingestion_batch) + "\n", encoding="utf-8"
    )
    return outdir

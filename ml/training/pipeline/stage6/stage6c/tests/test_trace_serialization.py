"""
Test JSONL roundtrip: write RunTrace then read back and compare.
Also test ledger run metadata roundtrip.
"""
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from stage6.stage6c.trace.types import RunSpec, StepRecord, RunTrace
from stage6.stage6c.trace.serialization import (
    write_run_trace_jsonl,
    read_run_trace_jsonl,
    read_run_traces_jsonl,
    append_run_trace_jsonl,
)


def test_roundtrip_single_trace():
    spec = RunSpec(
        run_id="run-1",
        seed_id="BASE-001-V2",
        horizon_N=3,
        shape="linear",
        carryover_mode="cold_start",
        injection_profile_id="none",
        created_at=datetime(2025, 2, 24, 12, 0, 0, tzinfo=timezone.utc),
    )
    step = StepRecord(
        run_id="run-1",
        step_index=0,
        step_role="rehydrate",
        prompt_messages=[{"role": "user", "content": "test", "origin": "step_query"}],
        response={
            "content": "ok",
            "model": "dummy",
            "tokens": 0,
            "sanitized": True,
            "sanitize_reasons": ["step_number"],
        },
        metadata={},
        phase_dom_decision_t=None,
        phase_dom_rhetoric_t=None,
    )
    trace = RunTrace(
        spec=spec,
        steps=[step],
        started_at=datetime(2025, 2, 24, 12, 0, 0, tzinfo=timezone.utc),
        completed_at=datetime(2025, 2, 24, 12, 1, 0, tzinfo=timezone.utc),
    )
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = Path(f.name)
    try:
        write_run_trace_jsonl(trace, path)
        back = read_run_trace_jsonl(path)
        assert back.spec.run_id == trace.spec.run_id
        assert back.spec.seed_id == trace.spec.seed_id
        assert back.spec.horizon_N == trace.spec.horizon_N
        assert back.spec.shape == trace.spec.shape
        assert back.spec.carryover_mode == trace.spec.carryover_mode
        assert len(back.steps) == len(trace.steps)
        assert back.steps[0].step_index == trace.steps[0].step_index
        assert back.steps[0].step_role == trace.steps[0].step_role
        assert back.steps[0].prompt_messages[0]["origin"] == "step_query"
        assert back.steps[0].response["content"] == "ok"
        assert back.steps[0].response["sanitized"] is True
        assert back.steps[0].response["sanitize_reasons"] == ["step_number"]
        assert back.started_at == trace.started_at
        assert back.completed_at == trace.completed_at
    finally:
        path.unlink(missing_ok=True)


def test_roundtrip_iso8601():
    spec = RunSpec(
        run_id="r2",
        seed_id="BASE-002-V1",
        horizon_N=4,
        shape="retry_biased",
        carryover_mode="full_transcript",
        injection_profile_id="none",
    )
    trace = RunTrace(spec=spec, steps=[], started_at=datetime.now(timezone.utc), completed_at=None)
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = Path(f.name)
    try:
        write_run_trace_jsonl(trace, path)
        back = read_run_trace_jsonl(path)
        assert back.spec.run_id == "r2"
        assert back.completed_at is None
    finally:
        path.unlink(missing_ok=True)


def test_ledger_run_metadata_roundtrip():
    """Ledger rows must preserve run-level determinism metadata."""
    from stage6.stage6c.metrics.ledger import append_ledger_row, read_ledger_rows
    row = {
        "run_id": "run-meta-001",
        "seed_id": "BASE-001",
        "harness_version": "stage6c-v1",
        "config_digest": "abc123",
        "seeds_digest": "def456",
        "started_at_utc": "2025-02-25T12:00:00+00:00",
        "finished_at_utc": "2025-02-25T12:01:00+00:00",
        "horizon_N": 3,
        "shape": "linear",
        "severity": "S0",
    }
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = Path(f.name)
    try:
        append_ledger_row(row, path)
        rows = read_ledger_rows(path)
        assert len(rows) == 1
        r = rows[0]
        assert r.get("run_id") == "run-meta-001"
        assert r.get("config_digest") == "abc123"
        assert r.get("seeds_digest") == "def456"
        assert r.get("harness_version") == "stage6c-v1"
    finally:
        path.unlink(missing_ok=True)


def test_append_and_read_multi():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = Path(f.name)
    try:
        for i in range(3):
            spec = RunSpec(
                run_id=f"run-{i}",
                seed_id="BASE-001",
                horizon_N=3,
                shape="linear",
                carryover_mode="cold_start",
                injection_profile_id="none",
            )
            trace = RunTrace(spec=spec, steps=[], started_at=datetime.now(timezone.utc), completed_at=None)
            append_run_trace_jsonl(trace, path)
        traces = read_run_traces_jsonl(path)
        assert len(traces) == 3
        assert [t.spec.run_id for t in traces] == ["run-0", "run-1", "run-2"]
    finally:
        path.unlink(missing_ok=True)

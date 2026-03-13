"""Tests for canonical_hash indexed column and get_by_canonical_hash lookup."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from runtime.sandbox.sandbox_ledger_store import (
    EVENT_EXECUTED,
    EVENT_PLANGATE_SAFE_EXECUTE,
    SandboxLedgerStore,
)


def test_get_by_canonical_hash_returns_correct_rows() -> None:
    """Append two rows with same canonical_hash, one with different; get_by_canonical_hash returns correct rows."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ledger.db"
        store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")

        ch_shared = "hash-abc123"
        ch_other = "hash-other"

        store.append(
            ledger_row_id="row-1",
            event_type=EVENT_PLANGATE_SAFE_EXECUTE,
            outcome_type="safe_execute",
            request_id="req-1",
            plan_hash="ph",
            sandbox_id="",
            payload={"canonical_hash": ch_shared, "request_id": "req-1", "decision_posture": "safe_execute"},
        )
        store.append(
            ledger_row_id="row-2",
            event_type=EVENT_EXECUTED,
            outcome_type="executed",
            request_id="req-1",
            plan_hash="ph",
            sandbox_id="sbx-1",
            payload={"canonical_hash": ch_shared, "request_id": "req-1"},
        )
        store.append(
            ledger_row_id="row-3",
            event_type=EVENT_EXECUTED,
            outcome_type="executed",
            request_id="req-2",
            plan_hash="ph2",
            sandbox_id="sbx-2",
            payload={"canonical_hash": ch_other, "request_id": "req-2"},
        )

        rows_shared = store.get_by_canonical_hash(ch_shared)
        rows_other = store.get_by_canonical_hash(ch_other)
        rows_missing = store.get_by_canonical_hash("nonexistent")

        assert len(rows_shared) == 2
        assert {r.ledger_row_id for r in rows_shared} == {"row-1", "row-2"}
        assert rows_shared[0].event_type == EVENT_PLANGATE_SAFE_EXECUTE
        assert rows_shared[1].event_type == EVENT_EXECUTED

        assert len(rows_other) == 1
        assert rows_other[0].ledger_row_id == "row-3"
        assert rows_other[0].payload.get("canonical_hash") == ch_other

        assert len(rows_missing) == 0

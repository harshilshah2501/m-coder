"""
Tests for M3.2 local ledger persistence and unified result contract.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from runtime.sandbox.sandbox_ledger_store import (
    EVENT_BLOCKED,
    EVENT_EXECUTED,
    EVENT_REFUSED,
    LedgerStoreError,
    SandboxLedgerStore,
)
from runtime.sandbox.sandbox_result import GovernedExecutionResult


class TestGovernedExecutionResultContract:
    """Unified result contract has all required fields and deterministic serialization."""

    def test_refused_result_has_required_fields(self) -> None:
        r = GovernedExecutionResult(
            outcome_type="refused",
            request_id="req-1",
            plan_hash="ph",
            sandbox_id="",
            success=False,
            final_status="refused",
            refusal_reason="executor not configured",
            ledger_row_id="refused-req-1-abc",
        )
        d = r.to_dict()
        assert d["outcome_type"] == "refused"
        assert d["request_id"] == "req-1"
        assert d["ledger_row_id"] == "refused-req-1-abc"
        assert d["refusal_reason"] == "executor not configured"
        assert "blocked_reason" in d
        assert "commands_executed" in d
        assert "commands_blocked" in d

    def test_blocked_result_has_required_fields(self) -> None:
        r = GovernedExecutionResult(
            outcome_type="blocked",
            request_id="req-2",
            plan_hash="ph",
            sandbox_id="sbx-2",
            success=False,
            final_status="blocked",
            blocked_reason="Command not in allowed list",
            policy_violation_type="command_or_path",
            commands_blocked=["curl http://x.com"],
            ledger_row_id="blocked-req-2",
        )
        d = r.to_dict()
        assert d["outcome_type"] == "blocked"
        assert d["blocked_reason"]
        assert d["ledger_row_id"] == "blocked-req-2"

    def test_executed_result_has_required_fields(self) -> None:
        r = GovernedExecutionResult(
            outcome_type="executed",
            request_id="req-3",
            plan_hash="ph",
            sandbox_id="sbx-3",
            success=True,
            final_status="executed_ok",
            commands_executed=["echo hello"],
            artifacts=["out.txt"],
            ledger_row_id="sbx-abc",
            duration_ms=10,
            exit_code=0,
            stdout_summary="hello",
        )
        d = r.to_dict()
        assert d["outcome_type"] == "executed"
        assert d["success"] is True
        assert d["artifacts"] == ["out.txt"]
        assert d["ledger_row_id"] == "sbx-abc"
        assert d["duration_ms"] == 10
        assert d["exit_code"] == 0

    def test_from_dict_roundtrip(self) -> None:
        r = GovernedExecutionResult(
            outcome_type="executed",
            request_id="r",
            plan_hash="p",
            sandbox_id="s",
            success=True,
            final_status="executed_ok",
            ledger_row_id="lid",
        )
        r2 = GovernedExecutionResult.from_dict(r.to_dict())
        assert r2.outcome_type == r.outcome_type
        assert r2.request_id == r.request_id
        assert r2.ledger_row_id == r.ledger_row_id


class TestSandboxLedgerStore:
    """Local ledger persistence: append, read, linkage."""

    def test_append_and_get_by_ledger_row_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path, fixed_time="2026-03-12T12:00:00Z")
            store.append(
                ledger_row_id="row-1",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-1",
                plan_hash="ph",
                sandbox_id="sbx-1",
                payload={"outcome_type": "executed", "request_id": "req-1"},
            )
            row = store.get_by_ledger_row_id("row-1")
            assert row is not None
            assert row.ledger_row_id == "row-1"
            assert row.outcome_type == "executed"
            assert row.request_id == "req-1"

    def test_append_and_get_by_request_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path)
            store.append(
                ledger_row_id="a1",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-x",
                plan_hash="",
                sandbox_id="",
                payload={"request_id": "req-x"},
            )
            store.append(
                ledger_row_id="a2",
                event_type=EVENT_BLOCKED,
                outcome_type="blocked",
                request_id="req-x",
                plan_hash="",
                sandbox_id="",
                payload={"request_id": "req-x"},
            )
            rows = store.get_by_request_id("req-x")
            assert len(rows) == 2
            assert {r.ledger_row_id for r in rows} == {"a1", "a2"}

    def test_list_all(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path)
            store.append(
                ledger_row_id="r1",
                event_type=EVENT_REFUSED,
                outcome_type="refused",
                request_id="req-1",
                plan_hash="",
                sandbox_id="",
                payload={},
            )
            store.append(
                ledger_row_id="r2",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-2",
                plan_hash="",
                sandbox_id="",
                payload={},
            )
            all_rows = store.list_all()
            assert len(all_rows) == 2
            assert {r.ledger_row_id for r in all_rows} == {"r1", "r2"}

    def test_persistence_failure_raises(self) -> None:
        """Duplicate ledger_row_id causes append to raise (fail-closed semantics)."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path)
            store.append(
                ledger_row_id="dup",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req",
                plan_hash="",
                sandbox_id="",
                payload={},
            )
            with pytest.raises(LedgerStoreError):
                store.append(
                    ledger_row_id="dup",
                    event_type=EVENT_EXECUTED,
                    outcome_type="executed",
                    request_id="req",
                    plan_hash="",
                    sandbox_id="",
                    payload={},
                )

    def test_append_and_get_by_canonical_hash_full_schema(self) -> None:
        """Store with top-level canonical_hash column: get_by_canonical_hash works."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path, fixed_time="2026-03-12T12:00:00Z")
            store.append(
                ledger_row_id="r1",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-a",
                plan_hash="ph",
                sandbox_id="",
                payload={"canonical_hash": "ch-123", "request_id": "req-a"},
            )
            store.append(
                ledger_row_id="r2",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-b",
                plan_hash="ph",
                sandbox_id="",
                payload={"canonical_hash": "ch-123", "request_id": "req-b"},
            )
            rows = store.get_by_canonical_hash("ch-123")
            assert len(rows) == 2
            assert {r.request_id for r in rows} == {"req-a", "req-b"}
            assert all(r.payload.get("canonical_hash") == "ch-123" for r in rows)


def _create_legacy_ledger_db(path: Path) -> None:
    """Create a DB with legacy schema (no canonical_hash column)."""
    legacy_schema = """
    CREATE TABLE sandbox_ledger (
        ledger_row_id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        outcome_type TEXT NOT NULL,
        request_id TEXT NOT NULL,
        plan_hash TEXT NOT NULL,
        sandbox_id TEXT NOT NULL,
        timestamp_utc TEXT NOT NULL,
        payload TEXT NOT NULL,
        artifact_manifest_ref TEXT NOT NULL DEFAULT ''
    );
    """
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(legacy_schema)
        conn.execute(
            """INSERT INTO sandbox_ledger (
                ledger_row_id, event_type, outcome_type, request_id, plan_hash,
                sandbox_id, timestamp_utc, payload, artifact_manifest_ref
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "leg-1",
                "plangate_safe_execute",
                "safe_execute",
                "demo-runtime",
                "plan-1",
                "",
                "2026-03-13T13:27:00.669969+00:00",
                json.dumps({"canonical_hash": "4b6a08e37bfed4a502029c1b8b1b9500122ff86cc45b15339ac1ff29d6218837"}),
                "",
            ),
        )
        conn.execute(
            """INSERT INTO sandbox_ledger (
                ledger_row_id, event_type, outcome_type, request_id, plan_hash,
                sandbox_id, timestamp_utc, payload, artifact_manifest_ref
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "leg-2",
                "sandbox_executed",
                "executed",
                "demo-runtime",
                "plan-1",
                "",
                "2026-03-13T13:27:02.074337+00:00",
                json.dumps({
                    "canonical_hash": "4b6a08e37bfed4a502029c1b8b1b9500122ff86cc45b15339ac1ff29d6218837",
                    "backend": "local_process",
                    "exit_code": 0,
                }),
                "",
            ),
        )


class TestSandboxLedgerStoreLegacySchema:
    """Read compatibility when canonical_hash exists only in payload (no column)."""

    def test_store_opens_without_canonical_hash_column(self) -> None:
        """Initialization does not fail when table has no canonical_hash column."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.db"
            _create_legacy_ledger_db(path)
            store = SandboxLedgerStore(path)
            assert store._has_canonical_hash_column is False

    def test_get_by_request_id_returns_rows_with_canonical_hash_in_payload(self) -> None:
        """get_by_request_id returns rows; canonical_hash comes from payload."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.db"
            _create_legacy_ledger_db(path)
            store = SandboxLedgerStore(path)
            rows = store.get_by_request_id("demo-runtime")
            assert len(rows) == 2
            for r in rows:
                assert r.payload.get("canonical_hash") == "4b6a08e37bfed4a502029c1b8b1b9500122ff86cc45b15339ac1ff29d6218837"

    def test_get_by_canonical_hash_works_via_json_extract(self) -> None:
        """get_by_canonical_hash works using json_extract(payload, '$.canonical_hash')."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.db"
            _create_legacy_ledger_db(path)
            store = SandboxLedgerStore(path)
            hash_val = "4b6a08e37bfed4a502029c1b8b1b9500122ff86cc45b15339ac1ff29d6218837"
            rows = store.get_by_canonical_hash(hash_val)
            assert len(rows) == 2
            assert {r.ledger_row_id for r in rows} == {"leg-1", "leg-2"}
            assert all(r.payload.get("canonical_hash") == hash_val for r in rows)

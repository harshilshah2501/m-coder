"""M4.1 Slice 3 — Ledger identity propagation tests.

Verify that canonical_hash and intent_id propagate from CanonicalExecutionIntent
into Plan-Gate decision rows and sandbox execution rows, and that backward
compatibility is preserved for rows without these fields.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from runtime.execute_service.handlers import handle_execute_request
from runtime.sandbox.sandbox_executor import SandboxAction, SandboxExecutor
from runtime.sandbox.sandbox_ledger_store import (
    EVENT_EXECUTED,
    EVENT_PLANGATE_SAFE_EXECUTE,
    SandboxLedgerStore,
)


class TestPlangateDecisionContainsCanonicalHash:
    """Plan-Gate decision rows include canonical_hash when intent exists."""

    def test_plangate_decision_contains_canonical_hash(self) -> None:
        """After handle_execute_request with ledger_path, Plan-Gate decision row has canonical_hash and intent_id."""
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.db"
            data = {
                "request_id": "req-pg-identity",
                "repo_root": tmp,
                "command": "echo ok",
                "ledger_path": str(ledger_path),
            }
            response = handle_execute_request(data)
            assert response["outcome"] == "EXECUTED"
            store = SandboxLedgerStore(ledger_path)
            all_rows = store.list_all()
            plangate_rows = [r for r in all_rows if r.event_type == EVENT_PLANGATE_SAFE_EXECUTE]
            assert len(plangate_rows) >= 1, "expected at least one Plan-Gate decision row"
            row = plangate_rows[0]
            assert "canonical_hash" in row.payload, "Plan-Gate decision row must include canonical_hash"
            assert "intent_id" in row.payload, "Plan-Gate decision row must include intent_id"
            assert row.payload["canonical_hash"], "canonical_hash must be non-empty"
            assert row.payload["intent_id"], "intent_id must be non-empty"
            assert row.payload.get("request_id") == "req-pg-identity"
            assert row.payload.get("decision_posture") == "safe_execute"


class TestSandboxExecutionContainsCanonicalHash:
    """Sandbox execution ledger rows include canonical_hash when metadata provides it."""

    def test_sandbox_execution_contains_canonical_hash(self) -> None:
        """Execution row includes canonical_hash, intent_id, backend when action.metadata has them."""
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(ledger_path)
            executor = SandboxExecutor(ledger_store=store)
            action = SandboxAction(
                task_id="t1",
                command=["echo", "hello"],
                working_dir=tmp,
                request_id="req-exec-identity",
                plan_hash="ph1",
                metadata={
                    "canonical_hash": "ch-abc123",
                    "intent_id": "intent-uuid-1",
                    "request_id": "req-exec-identity",
                    "plan_hash": "ph1",
                },
            )
            result = executor.execute_sandbox_action(action)
            assert result.outcome_type == "executed"
            rows = store.get_by_request_id("req-exec-identity")
            assert len(rows) >= 1
            executed_rows = [r for r in rows if r.event_type == EVENT_EXECUTED]
            assert len(executed_rows) >= 1
            row = executed_rows[0]
            assert row.payload.get("canonical_hash") == "ch-abc123"
            assert row.payload.get("intent_id") == "intent-uuid-1"
            assert "backend" in row.payload
            assert row.payload.get("request_id") == "req-exec-identity"
            assert row.payload.get("plan_hash") == "ph1"


class TestIdentityConsistency:
    """Decision and execution rows for the same request share identical canonical_hash."""

    def test_identity_consistency(self) -> None:
        """One request through Plan-Gate (safe_execute) and sandbox yields same canonical_hash in both rows."""
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.db"
            request_id = "req-consistency"
            data = {
                "request_id": request_id,
                "repo_root": tmp,
                "command": "echo consistent",
                "ledger_path": str(ledger_path),
            }
            response = handle_execute_request(data)
            assert response["outcome"] == "EXECUTED"
            store = SandboxLedgerStore(ledger_path)
            rows = store.get_by_request_id(request_id)
            plangate_rows = [r for r in rows if r.event_type == EVENT_PLANGATE_SAFE_EXECUTE]
            executed_rows = [r for r in rows if r.event_type == EVENT_EXECUTED]
            assert len(plangate_rows) >= 1
            assert len(executed_rows) >= 1
            ch_pg = plangate_rows[0].payload.get("canonical_hash")
            ch_ex = executed_rows[0].payload.get("canonical_hash")
            assert ch_pg is not None, "Plan-Gate row must have canonical_hash"
            assert ch_ex is not None, "Execution row must have canonical_hash"
            assert ch_pg == ch_ex, "Decision and execution rows must share the same canonical_hash"


class TestLedgerBackwardCompatibility:
    """Rows without canonical_hash still load and list correctly."""

    def test_ledger_backward_compatibility(self) -> None:
        """Append and read rows that do not contain canonical_hash; get_by_request_id and list_all work."""
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(ledger_path, fixed_time="2026-03-13T12:00:00Z")
            # Legacy-style payload (no canonical_hash / intent_id)
            store.append(
                ledger_row_id="legacy-1",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-legacy",
                plan_hash="ph",
                sandbox_id="",
                payload={
                    "request_id": "req-legacy",
                    "plan_hash": "ph",
                    "outcome_type": "executed",
                    "success": True,
                },
            )
            store.append(
                ledger_row_id="legacy-2",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-legacy",
                plan_hash="ph",
                sandbox_id="",
                payload={
                    "request_id": "req-legacy",
                    "outcome_type": "executed",
                },
            )
            by_id = store.get_by_ledger_row_id("legacy-1")
            assert by_id is not None
            assert by_id.payload.get("request_id") == "req-legacy"
            assert "canonical_hash" not in by_id.payload
            by_request = store.get_by_request_id("req-legacy")
            assert len(by_request) == 2
            all_rows = store.list_all()
            assert len(all_rows) == 2
            for r in all_rows:
                assert r.ledger_row_id in ("legacy-1", "legacy-2")
                assert r.payload is not None

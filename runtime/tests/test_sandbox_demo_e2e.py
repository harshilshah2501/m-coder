"""
E2E tests for M3.2 canonical demo — REFUSED / BLOCKED / EXECUTED.

Proves: refusal does not start sandbox; blocked does not execute command;
executed runs allowed command; all three outcomes persist ledger rows.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from runtime.sandbox.demo_governed_execution import (
    run_all_cases,
    run_case_blocked,
    run_case_bounded_allow,
    run_case_deferred,
    run_case_executed,
    run_case_refused,
)
from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore


class TestDemoExecuted:
    """CASE A — EXECUTED."""

    def test_executed_runs_allowed_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            work = Path(tmp)
            result = run_case_executed(ledger, work)
        assert result["outcome_type"] == "executed"
        assert result["success"] is True
        assert result["ledger_row_id"]

    def test_executed_persists_ledger_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            work = Path(tmp)
            run_case_executed(ledger, work)
            store = SandboxLedgerStore(ledger)
            rows = store.list_all()
        assert len(rows) >= 1
        assert any(r.outcome_type == "executed" for r in rows)


class TestDemoBlocked:
    """CASE B — BLOCKED."""

    def test_blocked_does_not_execute_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            work = Path(tmp)
            result = run_case_blocked(ledger, work)
        assert result["outcome_type"] == "refused"
        assert result["ledger_row_id"]
        assert result["success"] is False

    def test_blocked_persists_ledger_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            work = Path(tmp)
            run_case_blocked(ledger, work)
            store = SandboxLedgerStore(ledger)
            rows = store.list_all()
        assert any(r.event_type == "plangate_refused" or r.outcome_type == "refused" for r in rows)


class TestDemoRefused:
    """CASE C — REFUSED."""

    def test_refused_does_not_launch_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            work = Path(tmp)
            valid, reason, lid = run_case_refused(ledger, work)
        assert valid is False
        assert "Plan-Gate not configured" in reason or "not configured" in reason
        assert lid

    def test_refused_persists_ledger_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            work = Path(tmp)
            run_case_refused(ledger, work)
            store = SandboxLedgerStore(ledger)
            rows = store.list_all()
        assert any(r.outcome_type == "refused" for r in rows)


class TestDemoDeferred:
    """CASE D — DEFER."""

    def test_deferred_does_not_run_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            work = Path(tmp)
            result = run_case_deferred(ledger, work)
        assert result["outcome_type"] == "deferred"
        assert result["valid"] is False
        assert result.get("ledger_row_id")

    def test_deferred_persists_plangate_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            work = Path(tmp)
            run_case_deferred(ledger, work)
            store = SandboxLedgerStore(ledger)
            rows = store.list_all()
        assert any(r.event_type == "plangate_deferred" for r in rows)


class TestDemoBoundedAllow:
    """CASE E — BOUNDED_ALLOW."""

    def test_bounded_allow_does_not_run_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            work = Path(tmp)
            result = run_case_bounded_allow(ledger, work)
        assert result["outcome_type"] == "bounded_allow"
        assert result["valid"] is False
        assert result.get("ledger_row_id")

    def test_bounded_allow_persists_plangate_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            work = Path(tmp)
            run_case_bounded_allow(ledger, work)
            store = SandboxLedgerStore(ledger)
            rows = store.list_all()
        assert any(r.event_type == "plangate_bounded_allow" for r in rows)

    def test_bounded_allow_distinct_from_defer(self) -> None:
        """bounded_allow must have stop_reason bounded_allow, not deferred."""
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            work = Path(tmp)
            result = run_case_bounded_allow(ledger, work)
        assert result["outcome_type"] == "bounded_allow"
        # Demo runs through controller; run_case_bounded_allow asserts stop_reason == "bounded_allow" internally
        assert "bounded_allow" in (result.get("reason") or "").lower()


class TestDemoAllCases:
    """All cases in one run."""

    def test_run_all_cases_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            work = Path(tmp)
            summary = run_all_cases(ledger_path=ledger, work_dir=work)
        assert summary["executed"]["outcome_type"] == "executed"
        assert summary["blocked"]["outcome_type"] == "refused"
        assert summary["refused"]["valid"] is False
        assert summary["refused"]["ledger_row_id"]
        assert summary["deferred"]["outcome_type"] == "deferred"
        assert summary["bounded_allow"]["outcome_type"] == "bounded_allow"
        assert summary["ledger_row_count"] >= 5
        assert len(summary["ledger_rows"]) >= 5
        assert any(r["event_type"] == "plangate_bounded_allow" for r in summary["ledger_rows"])

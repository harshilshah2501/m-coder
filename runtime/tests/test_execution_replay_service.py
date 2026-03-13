"""Tests for M4.1 Slice-4 Execution Replay Service."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from runtime.replay.execution_replay_service import ExecutionReplayService
from runtime.sandbox.sandbox_executor import SandboxExecutor
from runtime.sandbox.sandbox_ledger_store import EVENT_EXECUTED, SandboxLedgerStore


def test_reconstruct_intent_from_ledger() -> None:
    """Append ledger row with canonical_hash; verify intent reconstruction."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ledger.db"
        store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")
        executor = SandboxExecutor()
        service = ExecutionReplayService(ledger_store=store, sandbox_executor=executor)

        canonical_hash = "ch-reconstruct-test"
        store.append(
            ledger_row_id="exec-1",
            event_type=EVENT_EXECUTED,
            outcome_type="executed",
            request_id="req-1",
            plan_hash="ph1",
            sandbox_id="sbx-1",
            payload={
                "command": ["echo", "hello"],
                "working_dir": tmp,
                "request_id": "req-1",
                "plan_hash": "ph1",
                "canonical_hash": canonical_hash,
                "intent_id": "intent-1",
            },
        )

        intent = service.reconstruct_intent(canonical_hash)
        assert intent["canonical_hash"] == canonical_hash
        assert intent["intent_id"] == "intent-1"
        assert intent["request_id"] == "req-1"
        assert intent["plan_hash"] == "ph1"
        assert intent["command"] == ["echo", "hello"]
        assert intent["working_dir"] == tmp


def test_replay_execution_success() -> None:
    """Append ledger entry; replay execution; verify sandbox result."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ledger.db"
        store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")
        executor = SandboxExecutor(ledger_store=store)
        service = ExecutionReplayService(ledger_store=store, sandbox_executor=executor)

        canonical_hash = "ch-replay-test"
        store.append(
            ledger_row_id="exec-replay",
            event_type=EVENT_EXECUTED,
            outcome_type="executed",
            request_id="req-replay",
            plan_hash="ph-replay",
            sandbox_id="",
            payload={
                "command": ["echo", "replayed"],
                "working_dir": tmp,
                "request_id": "req-replay",
                "plan_hash": "ph-replay",
                "canonical_hash": canonical_hash,
                "intent_id": "intent-replay",
            },
        )

        result = service.replay_execution(canonical_hash)
        assert result.outcome_type == "executed"
        assert result.success is True


def test_missing_hash_raises_error() -> None:
    """Missing canonical_hash raises ValueError."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ledger.db"
        store = SandboxLedgerStore(path)
        executor = SandboxExecutor()
        service = ExecutionReplayService(ledger_store=store, sandbox_executor=executor)

        with pytest.raises(ValueError, match="canonical_hash does not exist"):
            service.reconstruct_intent("nonexistent-hash")

        with pytest.raises(ValueError, match="canonical_hash does not exist"):
            service.replay_execution("nonexistent-hash")

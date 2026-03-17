"""
M4.1 TraceBuilder Tests — C1 Execution Trace Builder.

Tests:
- build_by_request_id / build_from_request_id: deterministic ordering, started_at, ended_at, is_replay
- build_by_canonical_hash / build_from_canonical_hash: latest request group only (v1)
- C1 vocabulary mapping (REFUSED, PLAN_APPROVED, EXECUTION_COMPLETED, etc.)
- Replay detection via payload.execution_surface == "replay"
- Unknown event -> UNKNOWN_EVENT with metadata.raw_event_type
- Ordering: timestamp_utc ascending, tie-breaker by event_id
"""

import tempfile
from pathlib import Path

import pytest

from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore
from runtime.observation.trace_builder import TraceBuilder, UNKNOWN_EVENT
from runtime.observation.models import ExecutionTrace, TraceEvent


@pytest.fixture
def ledger_store():
    """Create a temporary ledger store with test data (SandboxLedgerStore row shape)."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = Path(f.name)

    store = SandboxLedgerStore(path, fixed_time="2026-03-13T10:00:00Z")

    # Request 1: Plan-Gate refused
    store.append(
        ledger_row_id="row-1",
        event_type="plangate_refused",
        outcome_type="refused",
        request_id="req-001",
        plan_hash="plan-abc",
        payload={
            "reason": "protected branch mutation",
            "canonical_hash": "hash-xyz-123",
            "intent_id": "intent-001",
        },
    )

    # Request 2: Plan-Gate safe_execute + sandbox executed
    store.append(
        ledger_row_id="row-2",
        event_type="plangate_safe_execute",
        outcome_type="safe_execute",
        request_id="req-002",
        plan_hash="plan-def",
        payload={
            "canonical_hash": "hash-xyz-456",
            "intent_id": "intent-002",
        },
    )

    store.append(
        ledger_row_id="row-3",
        event_type="sandbox_executed",
        outcome_type="executed",
        request_id="req-002",
        plan_hash="plan-def",
        payload={
            "canonical_hash": "hash-xyz-456",
            "intent_id": "intent-002",
            "backend": "local_process",
            "exit_code": 0,
            "duration_ms": 150,
        },
    )

    # Request 3: Same canonical_hash as request 2 (replay scenario)
    store.append(
        ledger_row_id="row-4",
        event_type="plangate_safe_execute",
        outcome_type="safe_execute",
        request_id="req-003",
        plan_hash="plan-ghi",
        payload={
            "canonical_hash": "hash-xyz-456",
            "intent_id": "intent-003",
        },
    )

    store.append(
        ledger_row_id="row-5",
        event_type="sandbox_executed",
        outcome_type="executed",
        request_id="req-003",
        plan_hash="plan-ghi",
        payload={
            "canonical_hash": "hash-xyz-456",
            "intent_id": "intent-003",
            "backend": "container",
            "exit_code": 1,
            "duration_ms": 200,
        },
    )

    # Request 4: Legacy row without canonical_hash
    store.append(
        ledger_row_id="row-6",
        event_type="sandbox_blocked",
        outcome_type="blocked",
        request_id="req-004",
        plan_hash="plan-jkl",
        payload={
            "blocked_reason": "command not allowed",
        },
    )

    yield store

    path.unlink(missing_ok=True)


class TestTraceBuilder:
    """Tests for TraceBuilder (C1 Execution Trace Builder)."""

    def test_build_by_request_id_single_event(self, ledger_store):
        """Test building trace for request with single event (C1 vocabulary)."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_request_id("req-001")

        assert trace.trace_id == "req-001"
        assert trace.lookup_type == "request_id"
        assert trace.request_id == "req-001"
        assert trace.total_events == 1
        assert len(trace.events) == 1
        assert trace.started_at == "2026-03-13T10:00:00Z"
        assert trace.ended_at == "2026-03-13T10:00:00Z"
        assert trace.is_replay is False

        event = trace.events[0]
        assert event.event_type == "REFUSED"
        assert event.metadata.get("raw_event_type") == "plangate_refused"
        assert event.posture == "refused"
        assert event.reason == "protected branch mutation"
        assert event.canonical_hash == "hash-xyz-123"
        assert event.execution_surface == "normal"

    def test_build_by_request_id_multiple_events(self, ledger_store):
        """Test building trace for request with multiple events (plan approve + execution)."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_request_id("req-002")

        assert trace.trace_id == "req-002"
        assert trace.request_id == "req-002"
        assert trace.total_events == 2
        assert len(trace.events) == 2
        assert trace.started_at == trace.first_event_time
        assert trace.ended_at == trace.last_event_time

        assert trace.events[0].event_type == "PLAN_APPROVED"
        assert trace.events[0].metadata.get("raw_event_type") == "plangate_safe_execute"
        assert trace.events[1].event_type == "EXECUTION_COMPLETED"
        assert trace.events[1].metadata.get("raw_event_type") == "sandbox_executed"
        assert trace.final_posture == "executed"
        assert trace.canonical_hash == "hash-xyz-456"

    def test_build_from_request_id(self, ledger_store):
        """C1: build_from_request_id returns same as build_by_request_id with C1 fields."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_from_request_id("req-002")
        assert trace.request_id == "req-002"
        assert trace.started_at
        assert trace.ended_at
        assert trace.total_events == 2

    def test_build_by_request_id_not_found(self, ledger_store):
        """Test building trace for non-existent request."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_request_id("req-nonexistent")

        assert trace.trace_id == "req-nonexistent"
        assert trace.request_id == "req-nonexistent"
        assert trace.total_events == 0
        assert len(trace.events) == 0
        assert trace.final_posture == ""
        assert trace.started_at == ""
        assert trace.ended_at == ""
        assert trace.is_replay is False

    def test_build_by_canonical_hash_latest_request_group_only(self, ledger_store):
        """C1: build_by_canonical_hash returns latest request group only (v1), not merged."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_canonical_hash("hash-xyz-456")

        assert trace.trace_id == "hash-xyz-456"
        assert trace.lookup_type == "canonical_hash"
        assert trace.canonical_hash == "hash-xyz-456"
        # Same fixed_time for all rows -> tie-break by request_id; one group chosen
        assert trace.total_events == 2
        assert len(trace.request_ids) == 1
        assert trace.request_id in ("req-002", "req-003")
        assert trace.request_ids[0] == trace.request_id

    def test_build_from_canonical_hash(self, ledger_store):
        """C1: build_from_canonical_hash same as build_by_canonical_hash."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_from_canonical_hash("hash-xyz-456")
        assert trace.canonical_hash == "hash-xyz-456"
        assert trace.total_events == 2
        assert len(trace.request_ids) == 1

    def test_build_by_canonical_hash_not_found(self, ledger_store):
        """Test building trace for non-existent canonical_hash."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_canonical_hash("hash-nonexistent")

        assert trace.trace_id == "hash-nonexistent"
        assert trace.total_events == 0
        assert len(trace.events) == 0
        assert trace.request_ids == []

    def test_backward_compatibility_missing_canonical_hash(self, ledger_store):
        """Test that rows without canonical_hash are handled gracefully."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_request_id("req-004")

        assert trace.total_events == 1
        event = trace.events[0]
        assert event.canonical_hash == ""
        assert event.event_type == "EXECUTION_BLOCKED"
        assert event.posture == "blocked"
        assert event.reason == "command not allowed"
        assert event.execution_surface == "normal"

    def test_deterministic_ordering(self, ledger_store):
        """Test that events are always ordered by timestamp then event_id."""
        builder = TraceBuilder(ledger_store)
        trace1 = builder.build_by_request_id("req-002")
        trace2 = builder.build_by_request_id("req-002")
        assert [e.event_id for e in trace1.events] == [e.event_id for e in trace2.events]

    def test_trace_event_to_dict(self, ledger_store):
        """Test TraceEvent serialization (C1 vocabulary in event_type)."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_request_id("req-002")
        event = trace.events[1]
        event_dict = event.to_dict()

        assert event_dict["event_type"] == "EXECUTION_COMPLETED"
        assert event_dict["metadata"].get("raw_event_type") == "sandbox_executed"
        assert event_dict["posture"] == "executed"
        assert event_dict["backend"] == "local_process"
        assert event_dict["exit_code"] == 0
        assert event_dict["duration_ms"] == 150

    def test_execution_trace_to_dict(self, ledger_store):
        """Test ExecutionTrace serialization includes C1 fields."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_request_id("req-002")
        trace_dict = trace.to_dict()

        assert trace_dict["trace_id"] == "req-002"
        assert trace_dict["lookup_type"] == "request_id"
        assert trace_dict["request_id"] == "req-002"
        assert trace_dict["total_events"] == 2
        assert len(trace_dict["events"]) == 2
        assert trace_dict["final_posture"] == "executed"
        assert "started_at" in trace_dict
        assert "ended_at" in trace_dict
        assert "is_replay" in trace_dict

    def test_build_all_traces(self, ledger_store):
        """Test building all traces."""
        builder = TraceBuilder(ledger_store)
        traces = builder.build_all_traces(limit=10)
        assert len(traces) == 4
        for trace in traces:
            assert trace.lookup_type == "request_id"


class TestC1RefusalPath:
    """C1: Refusal path — single REFUSED event."""

    def test_refusal_trace(self, ledger_store):
        trace = TraceBuilder(ledger_store).build_from_request_id("req-001")
        assert trace.total_events == 1
        assert trace.events[0].event_type == "REFUSED"
        assert trace.final_posture == "refused"
        assert trace.started_at == trace.ended_at


class TestC1ReplayFlagged:
    """C1: Replay trace flagged via payload.execution_surface == 'replay'."""

    def test_replay_trace_is_replay_true(self, ledger_store):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = Path(f.name)
        try:
            store = SandboxLedgerStore(path, fixed_time="2026-03-13T11:00:00Z")
            store.append(
                ledger_row_id="replay-row-1",
                event_type="plangate_safe_execute",
                outcome_type="safe_execute",
                request_id="req-replay",
                plan_hash="plan-r",
                payload={"canonical_hash": "ch-replay", "execution_surface": "replay"},
            )
            store.append(
                ledger_row_id="replay-row-2",
                event_type="sandbox_executed",
                outcome_type="executed",
                request_id="req-replay",
                plan_hash="plan-r",
                payload={
                    "canonical_hash": "ch-replay",
                    "execution_surface": "replay",
                    "exit_code": 0,
                },
            )
            trace = TraceBuilder(store).build_from_request_id("req-replay")
            assert trace.is_replay is True
            assert trace.events[0].execution_surface == "replay"
            assert trace.events[1].execution_surface == "replay"
        finally:
            path.unlink(missing_ok=True)

    def test_normal_trace_is_replay_false(self, ledger_store):
        trace = TraceBuilder(ledger_store).build_from_request_id("req-001")
        assert trace.is_replay is False
        assert trace.events[0].execution_surface == "normal"


class TestC1Ordering:
    """C1: Ordering correctness — timestamp_utc ascending, tie-breaker."""

    def test_ordering_timestamp_ascending(self, ledger_store):
        trace = TraceBuilder(ledger_store).build_from_request_id("req-002")
        timestamps = [e.timestamp_utc for e in trace.events]
        assert timestamps == sorted(timestamps)
        assert [e.event_type for e in trace.events] == ["PLAN_APPROVED", "EXECUTION_COMPLETED"]


class TestC1CanonicalHashLatestGroup:
    """C1: canonical_hash lookup chooses latest request group."""

    def test_canonical_hash_returns_one_request_group(self, ledger_store):
        trace = TraceBuilder(ledger_store).build_from_canonical_hash("hash-xyz-456")
        assert len(trace.request_ids) == 1
        assert trace.request_id == trace.request_ids[0]
        assert trace.total_events == 2

    def test_canonical_hash_latest_by_max_timestamp(self, ledger_store):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = Path(f.name)
        try:
            store = SandboxLedgerStore(path)
            store.append(
                ledger_row_id="old-1",
                event_type="sandbox_executed",
                outcome_type="executed",
                request_id="req-old",
                plan_hash="p",
                payload={"canonical_hash": "ch"},
            )
            store.append(
                ledger_row_id="new-1",
                event_type="plangate_safe_execute",
                outcome_type="safe_execute",
                request_id="req-new",
                plan_hash="p",
                payload={"canonical_hash": "ch"},
            )
            store.append(
                ledger_row_id="new-2",
                event_type="sandbox_executed",
                outcome_type="executed",
                request_id="req-new",
                plan_hash="p",
                payload={"canonical_hash": "ch"},
            )
            trace = TraceBuilder(store).build_from_canonical_hash("ch")
            assert trace.request_id == "req-new"
            assert trace.total_events == 2
        finally:
            path.unlink(missing_ok=True)


class TestC1UnknownEventFallback:
    """C1: Unknown raw event maps to UNKNOWN_EVENT with metadata.raw_event_type."""

    def test_unknown_event_maps_to_unknown_event(self, ledger_store):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = Path(f.name)
        try:
            store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")
            store.append(
                ledger_row_id="unk-1",
                event_type="custom_unknown_type",
                outcome_type="custom",
                request_id="req-unk",
                plan_hash="p",
                payload={},
            )
            trace = TraceBuilder(store).build_from_request_id("req-unk")
            assert trace.total_events == 1
            event = trace.events[0]
            assert event.event_type == UNKNOWN_EVENT
            assert event.metadata.get("raw_event_type") == "custom_unknown_type"
            assert event.posture == "custom"
        finally:
            path.unlink(missing_ok=True)


class TestTraceBuilderFromPath:
    """Tests for TraceBuilder.from_path factory method."""
    
    def test_from_path(self):
        """Test creating TraceBuilder from path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = Path(f.name)
        
        try:
            # Create store to initialize schema
            SandboxLedgerStore(path)
            
            # Create builder from path
            builder = TraceBuilder.from_path(path)
            
            # Should be able to query
            trace = builder.build_by_request_id("test")
            assert trace.total_events == 0
        finally:
            path.unlink(missing_ok=True)

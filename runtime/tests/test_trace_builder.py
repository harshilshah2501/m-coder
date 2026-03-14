"""
M4.1 TraceBuilder Tests — Verify trace building by request_id and canonical_hash.

Tests:
- build_by_request_id returns deterministic ordering
- build_by_canonical_hash aggregates multiple requests
- Backward compatibility with rows missing canonical_hash or intent_id
"""

import tempfile
from pathlib import Path

import pytest

from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore
from runtime.observation.trace_builder import TraceBuilder
from runtime.observation.models import ExecutionTrace, TraceEvent


@pytest.fixture
def ledger_store():
    """Create a temporary ledger store with test data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = Path(f.name)
    
    store = SandboxLedgerStore(path, fixed_time="2026-03-13T10:00:00Z")
    
    # Add some test events
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
    
    # Cleanup
    path.unlink(missing_ok=True)


class TestTraceBuilder:
    """Tests for TraceBuilder."""
    
    def test_build_by_request_id_single_event(self, ledger_store):
        """Test building trace for request with single event."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_request_id("req-001")
        
        assert trace.trace_id == "req-001"
        assert trace.lookup_type == "request_id"
        assert trace.total_events == 1
        assert len(trace.events) == 1
        
        event = trace.events[0]
        assert event.event_type == "plangate_refused"
        assert event.posture == "refused"
        assert event.reason == "protected branch mutation"
        assert event.canonical_hash == "hash-xyz-123"
    
    def test_build_by_request_id_multiple_events(self, ledger_store):
        """Test building trace for request with multiple events."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_request_id("req-002")
        
        assert trace.trace_id == "req-002"
        assert trace.total_events == 2
        assert len(trace.events) == 2
        
        # Events should be in chronological order
        assert trace.events[0].event_type == "plangate_safe_execute"
        assert trace.events[1].event_type == "sandbox_executed"
        
        # Final posture should be from last event
        assert trace.final_posture == "executed"
        
        # Canonical hash should be extracted
        assert trace.canonical_hash == "hash-xyz-456"
    
    def test_build_by_request_id_not_found(self, ledger_store):
        """Test building trace for non-existent request."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_request_id("req-nonexistent")
        
        assert trace.trace_id == "req-nonexistent"
        assert trace.total_events == 0
        assert len(trace.events) == 0
        assert trace.final_posture == ""
    
    def test_build_by_canonical_hash(self, ledger_store):
        """Test building trace by canonical_hash aggregates multiple requests."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_canonical_hash("hash-xyz-456")
        
        assert trace.trace_id == "hash-xyz-456"
        assert trace.lookup_type == "canonical_hash"
        assert trace.canonical_hash == "hash-xyz-456"
        
        # Should find events from req-002 and req-003
        assert trace.total_events == 4
        assert len(trace.request_ids) == 2
        assert "req-002" in trace.request_ids
        assert "req-003" in trace.request_ids
    
    def test_build_by_canonical_hash_not_found(self, ledger_store):
        """Test building trace for non-existent canonical_hash."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_canonical_hash("hash-nonexistent")
        
        assert trace.trace_id == "hash-nonexistent"
        assert trace.total_events == 0
        assert len(trace.events) == 0
    
    def test_backward_compatibility_missing_canonical_hash(self, ledger_store):
        """Test that rows without canonical_hash are handled gracefully."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_request_id("req-004")
        
        assert trace.total_events == 1
        event = trace.events[0]
        assert event.canonical_hash == ""
        assert event.posture == "blocked"
        assert event.reason == "command not allowed"
    
    def test_deterministic_ordering(self, ledger_store):
        """Test that events are always ordered by timestamp."""
        builder = TraceBuilder(ledger_store)
        
        # Build trace multiple times
        trace1 = builder.build_by_request_id("req-002")
        trace2 = builder.build_by_request_id("req-002")
        
        # Order should be deterministic
        assert [e.event_id for e in trace1.events] == [e.event_id for e in trace2.events]
    
    def test_trace_event_to_dict(self, ledger_store):
        """Test TraceEvent serialization."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_request_id("req-002")
        
        event = trace.events[1]  # sandbox_executed event
        event_dict = event.to_dict()
        
        assert event_dict["event_type"] == "sandbox_executed"
        assert event_dict["posture"] == "executed"
        assert event_dict["backend"] == "local_process"
        assert event_dict["exit_code"] == 0
        assert event_dict["duration_ms"] == 150
    
    def test_execution_trace_to_dict(self, ledger_store):
        """Test ExecutionTrace serialization."""
        builder = TraceBuilder(ledger_store)
        trace = builder.build_by_request_id("req-002")
        
        trace_dict = trace.to_dict()
        
        assert trace_dict["trace_id"] == "req-002"
        assert trace_dict["lookup_type"] == "request_id"
        assert trace_dict["total_events"] == 2
        assert len(trace_dict["events"]) == 2
        assert trace_dict["final_posture"] == "executed"
    
    def test_build_all_traces(self, ledger_store):
        """Test building all traces."""
        builder = TraceBuilder(ledger_store)
        traces = builder.build_all_traces(limit=10)
        
        # Should have 4 unique request_ids
        assert len(traces) == 4
        
        # All traces should have correct lookup_type
        for trace in traces:
            assert trace.lookup_type == "request_id"


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

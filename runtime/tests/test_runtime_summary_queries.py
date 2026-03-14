"""
M4.1 RuntimeSummaryQueries Tests — Verify aggregate statistics.

Tests:
- Total requests counting
- Posture distribution
- Top refusal reasons
- Backend distribution
- Replay count
- Unique canonical hashes
- Recent events
"""

import tempfile
from pathlib import Path

import pytest

from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore
from runtime.observation.summary_queries import RuntimeSummaryQueries
from runtime.observation.models import RuntimeSummary, PostureDistribution


@pytest.fixture
def ledger_store():
    """Create a temporary ledger store with test data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = Path(f.name)
    
    store = SandboxLedgerStore(path, fixed_time="2026-03-13T10:00:00Z")
    
    # Add varied test events
    
    # Refused events with different reasons
    store.append(
        ledger_row_id="row-1",
        event_type="plangate_refused",
        outcome_type="refused",
        request_id="req-001",
        plan_hash="plan-001",
        payload={"reason": "protected branch mutation"},
    )
    
    store.append(
        ledger_row_id="row-2",
        event_type="plangate_refused",
        outcome_type="refused",
        request_id="req-002",
        plan_hash="plan-002",
        payload={"reason": "destructive filesystem command"},
    )
    
    store.append(
        ledger_row_id="row-3",
        event_type="plangate_refused",
        outcome_type="refused",
        request_id="req-003",
        plan_hash="plan-003",
        payload={"reason": "protected branch mutation"},
    )
    
    # Deferred event
    store.append(
        ledger_row_id="row-4",
        event_type="plangate_deferred",
        outcome_type="deferred",
        request_id="req-004",
        plan_hash="plan-004",
        payload={"reason": "requires human review"},
    )
    
    # Bounded allow event
    store.append(
        ledger_row_id="row-5",
        event_type="plangate_bounded_allow",
        outcome_type="bounded_allow",
        request_id="req-005",
        plan_hash="plan-005",
        payload={"reason": "read-only allowed"},
    )
    
    # Safe execute + executed events (different backends)
    store.append(
        ledger_row_id="row-6",
        event_type="plangate_safe_execute",
        outcome_type="safe_execute",
        request_id="req-006",
        plan_hash="plan-006",
        payload={"canonical_hash": "hash-aaa"},
    )
    
    store.append(
        ledger_row_id="row-7",
        event_type="sandbox_executed",
        outcome_type="executed",
        request_id="req-006",
        plan_hash="plan-006",
        payload={
            "canonical_hash": "hash-aaa",
            "backend": "local_process",
            "exit_code": 0,
        },
    )
    
    # Another successful execution
    store.append(
        ledger_row_id="row-8",
        event_type="plangate_safe_execute",
        outcome_type="safe_execute",
        request_id="req-007",
        plan_hash="plan-007",
        payload={"canonical_hash": "hash-bbb"},
    )
    
    store.append(
        ledger_row_id="row-9",
        event_type="sandbox_executed",
        outcome_type="executed",
        request_id="req-007",
        plan_hash="plan-007",
        payload={
            "canonical_hash": "hash-bbb",
            "backend": "container",
            "exit_code": 0,
        },
    )
    
    # Failed execution
    store.append(
        ledger_row_id="row-10",
        event_type="plangate_safe_execute",
        outcome_type="safe_execute",
        request_id="req-008",
        plan_hash="plan-008",
        payload={"canonical_hash": "hash-ccc"},
    )
    
    store.append(
        ledger_row_id="row-11",
        event_type="sandbox_executed",
        outcome_type="executed",
        request_id="req-008",
        plan_hash="plan-008",
        payload={
            "canonical_hash": "hash-ccc",
            "backend": "local_process",
            "exit_code": 1,
        },
    )
    
    # Blocked event
    store.append(
        ledger_row_id="row-12",
        event_type="sandbox_blocked",
        outcome_type="blocked",
        request_id="req-009",
        plan_hash="plan-009",
        payload={"blocked_reason": "timeout exceeded"},
    )
    
    # Replay scenario: same canonical_hash, different request_id
    store.append(
        ledger_row_id="row-13",
        event_type="plangate_safe_execute",
        outcome_type="safe_execute",
        request_id="req-010",
        plan_hash="plan-010",
        payload={"canonical_hash": "hash-aaa"},  # Same as req-006
    )
    
    store.append(
        ledger_row_id="row-14",
        event_type="sandbox_executed",
        outcome_type="executed",
        request_id="req-010",
        plan_hash="plan-010",
        payload={
            "canonical_hash": "hash-aaa",  # Same as req-006
            "backend": "local_process",
            "exit_code": 0,
        },
    )
    
    yield store
    
    path.unlink(missing_ok=True)


class TestRuntimeSummaryQueries:
    """Tests for RuntimeSummaryQueries."""
    
    def test_get_summary_totals(self, ledger_store):
        """Test total request and event counts."""
        queries = RuntimeSummaryQueries(ledger_store)
        summary = queries.get_summary()
        
        # 10 unique request_ids
        assert summary.total_requests == 10
        # 14 total events
        assert summary.total_events == 14
    
    def test_posture_distribution(self, ledger_store):
        """Test posture distribution counts."""
        queries = RuntimeSummaryQueries(ledger_store)
        summary = queries.get_summary()
        
        postures = summary.postures
        assert postures.refused == 3
        assert postures.deferred == 1
        assert postures.bounded_allow == 1
        assert postures.safe_execute == 4
        assert postures.executed == 4
        assert postures.blocked == 1
    
    def test_posture_distribution_total(self, ledger_store):
        """Test posture total calculation."""
        queries = RuntimeSummaryQueries(ledger_store)
        postures = queries.get_posture_distribution()
        
        assert postures.total == 14
    
    def test_top_refusal_reasons(self, ledger_store):
        """Test top refusal reasons ordering."""
        queries = RuntimeSummaryQueries(ledger_store)
        summary = queries.get_summary()
        
        top_refusals = summary.top_refusal_reasons
        assert len(top_refusals) >= 2
        
        # Most common refusal should be first
        assert top_refusals[0].reason == "protected branch mutation"
        assert top_refusals[0].count == 2
        
        # Second most common
        assert top_refusals[1].reason == "destructive filesystem command"
        assert top_refusals[1].count == 1
        
        # Should have example request_id
        assert top_refusals[0].example_request_id in ("req-001", "req-003")
    
    def test_backend_distribution(self, ledger_store):
        """Test backend distribution counts."""
        queries = RuntimeSummaryQueries(ledger_store)
        summary = queries.get_summary()
        
        backend_dist = summary.backend_distribution
        
        # Should have local_process and container
        backends = {b.backend: b for b in backend_dist}
        
        assert "local_process" in backends
        assert backends["local_process"].count == 3
        assert backends["local_process"].success_count == 2
        assert backends["local_process"].failure_count == 1
        
        assert "container" in backends
        assert backends["container"].count == 1
        assert backends["container"].success_count == 1
    
    def test_unique_canonical_hashes(self, ledger_store):
        """Test unique canonical hash counting."""
        queries = RuntimeSummaryQueries(ledger_store)
        summary = queries.get_summary()
        
        # hash-aaa, hash-bbb, hash-ccc
        assert summary.unique_canonical_hashes == 3
    
    def test_replay_count(self, ledger_store):
        """Test replay detection."""
        queries = RuntimeSummaryQueries(ledger_store)
        summary = queries.get_summary()
        
        # hash-aaa appears in req-006 and req-010
        assert summary.replay_count == 1
    
    def test_time_range(self, ledger_store):
        """Test time range extraction."""
        queries = RuntimeSummaryQueries(ledger_store)
        summary = queries.get_summary()
        
        # All events have fixed time in test
        assert summary.earliest_event == "2026-03-13T10:00:00Z"
        assert summary.latest_event == "2026-03-13T10:00:00Z"
    
    def test_recent_events(self, ledger_store):
        """Test recent events extraction."""
        queries = RuntimeSummaryQueries(ledger_store)
        summary = queries.get_summary(recent_events_limit=5)
        
        recent = summary.recent_events
        assert len(recent) <= 5
        
        # All should be TraceEvent objects
        for event in recent:
            assert hasattr(event, "event_type")
            assert hasattr(event, "posture")
    
    def test_empty_ledger(self):
        """Test summary with empty ledger."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = Path(f.name)
        
        try:
            store = SandboxLedgerStore(path)
            queries = RuntimeSummaryQueries(store)
            summary = queries.get_summary()
            
            assert summary.total_requests == 0
            assert summary.total_events == 0
            assert summary.postures.total == 0
            assert len(summary.top_refusal_reasons) == 0
            assert len(summary.backend_distribution) == 0
        finally:
            path.unlink(missing_ok=True)
    
    def test_count_total_requests(self, ledger_store):
        """Test direct request count method."""
        queries = RuntimeSummaryQueries(ledger_store)
        count = queries.count_total_requests()
        
        assert count == 10
    
    def test_count_unique_canonical_hashes(self, ledger_store):
        """Test direct canonical hash count method."""
        queries = RuntimeSummaryQueries(ledger_store)
        count = queries.count_unique_canonical_hashes()
        
        assert count == 3
    
    def test_get_recent_events(self, ledger_store):
        """Test get_recent_events method."""
        queries = RuntimeSummaryQueries(ledger_store)
        events = queries.get_recent_events(limit=3)
        
        assert len(events) == 3
        # Most recent first
        for event in events:
            assert event.timestamp_utc == "2026-03-13T10:00:00Z"
    
    def test_summary_to_dict(self, ledger_store):
        """Test RuntimeSummary serialization."""
        queries = RuntimeSummaryQueries(ledger_store)
        summary = queries.get_summary()
        
        summary_dict = summary.to_dict()
        
        assert "total_requests" in summary_dict
        assert "total_events" in summary_dict
        assert "postures" in summary_dict
        assert "top_refusal_reasons" in summary_dict
        assert "backend_distribution" in summary_dict
        assert "recent_events" in summary_dict


class TestRuntimeSummaryQueriesFromPath:
    """Tests for RuntimeSummaryQueries.from_path factory method."""
    
    def test_from_path(self):
        """Test creating queries from path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = Path(f.name)
        
        try:
            SandboxLedgerStore(path)
            queries = RuntimeSummaryQueries.from_path(path)
            
            summary = queries.get_summary()
            assert summary.total_requests == 0
        finally:
            path.unlink(missing_ok=True)

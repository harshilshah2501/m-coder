"""
M4.1 ExplanationBuilder Tests — Verify human-readable explanation payloads.

Tests:
- Build from TraceEvent
- Build from ledger row
- Build from GovernedExecutionResult
- Build from individual fields
- All decision types produce appropriate explanations
- C2: explain_trace, explain_from_request_id, explain_from_canonical_hash (ExecutionExplanation)
"""

import tempfile
from pathlib import Path

import pytest

from runtime.observation.explanation_builder import ExplanationBuilder
from runtime.observation.models import (
    ExecutionExplanation,
    ExecutionTrace,
    ExplanationNotFoundError,
    ExplanationPayload,
    TraceEvent,
)
from runtime.observation.trace_builder import TraceBuilder
from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore


class TestExplanationBuilder:
    """Tests for ExplanationBuilder."""
    
    @pytest.fixture
    def builder(self):
        """Create ExplanationBuilder instance."""
        return ExplanationBuilder()
    
    def test_build_from_trace_event_refused(self, builder):
        """Test explanation for refused event."""
        event = TraceEvent(
            event_id="evt-1",
            event_type="plangate_refused",
            timestamp_utc="2026-03-13T10:00:00Z",
            request_id="req-001",
            plan_hash="plan-001",
            posture="refused",
            reason="protected branch mutation",
            canonical_hash="hash-abc",
        )
        
        explanation = builder.build_from_trace_event(event)
        
        assert explanation.decision == "refused"
        assert "refused" in explanation.outcome.lower()
        assert explanation.reason == "protected branch mutation"
        assert explanation.canonical_hash == "hash-abc"
        assert "protected branch mutation" in explanation.explanation
    
    def test_build_from_trace_event_deferred(self, builder):
        """Test explanation for deferred event."""
        event = TraceEvent(
            event_id="evt-2",
            event_type="plangate_deferred",
            timestamp_utc="2026-03-13T10:00:00Z",
            request_id="req-002",
            plan_hash="plan-002",
            posture="deferred",
            reason="requires human review",
        )
        
        explanation = builder.build_from_trace_event(event)
        
        assert explanation.decision == "deferred"
        assert "deferred" in explanation.outcome.lower()
        assert "human review" in explanation.explanation
    
    def test_build_from_trace_event_bounded_allow(self, builder):
        """Test explanation for bounded_allow event."""
        event = TraceEvent(
            event_id="evt-3",
            event_type="plangate_bounded_allow",
            timestamp_utc="2026-03-13T10:00:00Z",
            request_id="req-003",
            plan_hash="plan-003",
            posture="bounded_allow",
            reason="read-only operations only",
        )
        
        explanation = builder.build_from_trace_event(event)
        
        assert explanation.decision == "bounded_allow"
        assert "conditionally allowed" in explanation.outcome.lower()
        assert "read-only" in explanation.explanation
    
    def test_build_from_trace_event_safe_execute(self, builder):
        """Test explanation for safe_execute event."""
        event = TraceEvent(
            event_id="evt-4",
            event_type="plangate_safe_execute",
            timestamp_utc="2026-03-13T10:00:00Z",
            request_id="req-004",
            plan_hash="plan-004",
            posture="safe_execute",
            reason="",
        )
        
        explanation = builder.build_from_trace_event(event)
        
        assert explanation.decision == "safe_execute"
        assert "approved" in explanation.outcome.lower()
    
    def test_build_from_trace_event_executed(self, builder):
        """Test explanation for executed event."""
        event = TraceEvent(
            event_id="evt-5",
            event_type="sandbox_executed",
            timestamp_utc="2026-03-13T10:00:00Z",
            request_id="req-005",
            plan_hash="plan-005",
            posture="executed",
            reason="",
            exit_code=0,
            duration_ms=150,
            backend="local_process",
        )
        
        explanation = builder.build_from_trace_event(event)
        
        assert explanation.decision == "executed"
        assert "executed" in explanation.outcome.lower() or "successfully" in explanation.outcome.lower()
        assert explanation.exit_code == 0
        assert explanation.duration_ms == 150
        assert explanation.backend == "local_process"
        assert "exit code 0" in explanation.explanation
    
    def test_build_from_trace_event_blocked(self, builder):
        """Test explanation for blocked event."""
        event = TraceEvent(
            event_id="evt-6",
            event_type="sandbox_blocked",
            timestamp_utc="2026-03-13T10:00:00Z",
            request_id="req-006",
            plan_hash="plan-006",
            posture="blocked",
            reason="command not in allowlist",
        )
        
        explanation = builder.build_from_trace_event(event)
        
        assert explanation.decision == "blocked"
        assert "blocked" in explanation.outcome.lower()
        assert "allowlist" in explanation.explanation
    
    def test_build_from_dict(self, builder):
        """Test explanation from dictionary."""
        data = {
            "posture": "executed",
            "reason": "",
            "canonical_hash": "hash-xyz",
            "request_id": "req-007",
            "backend": "container",
            "exit_code": 1,
            "duration_ms": 200,
        }
        
        explanation = builder.build_from_trace_event(data)
        
        assert explanation.decision == "executed"
        assert explanation.exit_code == 1
        assert explanation.backend == "container"
    
    def test_build_from_ledger_row(self, builder):
        """Test explanation from mock ledger row."""
        class MockRow:
            event_type = "plangate_refused"
            request_id = "req-008"
            payload = {
                "reason": "authority mismatch",
                "canonical_hash": "hash-123",
            }
        
        explanation = builder.build_from_ledger_row(MockRow())
        
        assert explanation.decision == "refused"
        assert explanation.reason == "authority mismatch"
        assert explanation.canonical_hash == "hash-123"
        assert explanation.request_id == "req-008"
    
    def test_build_from_ledger_row_with_refusal_reason(self, builder):
        """Test explanation with refusal_reason in payload."""
        class MockRow:
            event_type = "sandbox_refused"
            request_id = "req-009"
            payload = {
                "refusal_reason": "policy violation",
            }
        
        explanation = builder.build_from_ledger_row(MockRow())
        
        assert explanation.decision == "refused"
        assert explanation.reason == "policy violation"
    
    def test_build_from_ledger_row_with_blocked_reason(self, builder):
        """Test explanation with blocked_reason in payload."""
        class MockRow:
            event_type = "sandbox_blocked"
            request_id = "req-010"
            payload = {
                "blocked_reason": "timeout exceeded",
            }
        
        explanation = builder.build_from_ledger_row(MockRow())
        
        assert explanation.decision == "blocked"
        assert explanation.reason == "timeout exceeded"
    
    def test_build_from_governed_result(self, builder):
        """Test explanation from GovernedExecutionResult-like object."""
        class MockResult:
            def to_dict(self):
                return {
                    "outcome_type": "executed",
                    "exit_code": 0,
                    "duration_ms": 100,
                    "backend": "local_process",
                    "canonical_hash": "hash-ghi",
                    "request_id": "req-011",
                }
        
        explanation = builder.build_from_governed_result(MockResult())
        
        assert explanation.decision == "executed"
        assert explanation.exit_code == 0
        assert explanation.backend == "local_process"
    
    def test_build_from_governed_result_blocked(self, builder):
        """Test explanation from blocked GovernedExecutionResult."""
        result = {
            "outcome_type": "blocked",
            "blocked_reason": "command not allowed",
            "request_id": "req-012",
        }
        
        explanation = builder.build_from_governed_result(result)
        
        assert explanation.decision == "blocked"
        assert explanation.reason == "command not allowed"
    
    def test_build_summary_explanation(self, builder):
        """Test building explanation from individual fields."""
        explanation = builder.build_summary_explanation(
            decision="executed",
            reason="",
            canonical_hash="hash-jkl",
            request_id="req-013",
            backend="container",
            execution_surface="execute_service",
            exit_code=0,
            duration_ms=50,
        )
        
        assert explanation.decision == "executed"
        assert explanation.canonical_hash == "hash-jkl"
        assert explanation.backend == "container"
        assert explanation.execution_surface == "execute_service"
        assert explanation.exit_code == 0
        assert explanation.duration_ms == 50
    
    def test_explanation_payload_to_dict(self, builder):
        """Test ExplanationPayload serialization."""
        explanation = builder.build_summary_explanation(
            decision="refused",
            reason="protected branch",
            canonical_hash="hash-mno",
            request_id="req-014",
        )
        
        payload_dict = explanation.to_dict()
        
        assert payload_dict["decision"] == "refused"
        assert payload_dict["reason"] == "protected branch"
        assert payload_dict["canonical_hash"] == "hash-mno"
        assert "explanation" in payload_dict
        assert "outcome" in payload_dict


class TestEventTypeMapping:
    """Tests for event type to decision mapping."""
    
    def test_event_type_to_decision_mapping(self):
        """Test all event type mappings."""
        mapping = {
            "plangate_refused": "refused",
            "plangate_deferred": "deferred",
            "plangate_bounded_allow": "bounded_allow",
            "plangate_safe_execute": "safe_execute",
            "sandbox_refused": "refused",
            "sandbox_blocked": "blocked",
            "sandbox_executed": "executed",
        }
        
        for event_type, expected_decision in mapping.items():
            result = ExplanationBuilder._event_type_to_decision(event_type)
            assert result == expected_decision, f"{event_type} should map to {expected_decision}"
    
    def test_outcome_type_to_decision_mapping(self):
        """Test outcome type mappings."""
        mapping = {
            "refused": "refused",
            "blocked": "blocked",
            "executed": "executed",
        }

        for outcome_type, expected_decision in mapping.items():
            result = ExplanationBuilder._outcome_type_to_decision(outcome_type)
            assert result == expected_decision


# -----------------------------------------------------------------------------
# C2 ExecutionExplanation tests (TraceBuilder + ExplanationBuilder)
# -----------------------------------------------------------------------------


@pytest.fixture
def c2_ledger_store():
    """SandboxLedgerStore with C1-compatible rows for C2 explanation tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = Path(f.name)
    store = SandboxLedgerStore(path, fixed_time="2026-03-13T10:00:00Z")
    store.append(
        ledger_row_id="row-1",
        event_type="plangate_refused",
        outcome_type="refused",
        request_id="req-001",
        plan_hash="plan-abc",
        payload={"reason": "protected branch", "canonical_hash": "ch-001"},
    )
    store.append(
        ledger_row_id="row-2",
        event_type="plangate_safe_execute",
        outcome_type="safe_execute",
        request_id="req-002",
        plan_hash="plan-def",
        payload={"canonical_hash": "ch-002"},
    )
    store.append(
        ledger_row_id="row-3",
        event_type="sandbox_executed",
        outcome_type="executed",
        request_id="req-002",
        plan_hash="plan-def",
        payload={"canonical_hash": "ch-002", "exit_code": 0},
    )
    store.append(
        ledger_row_id="row-4",
        event_type="plangate_deferred",
        outcome_type="deferred",
        request_id="req-003",
        plan_hash="plan-ghi",
        payload={"reason": "needs review", "canonical_hash": "ch-003"},
    )
    store.append(
        ledger_row_id="row-5",
        event_type="plangate_bounded_allow",
        outcome_type="bounded_allow",
        request_id="req-004",
        plan_hash="plan-jkl",
        payload={"reason": "read-only", "canonical_hash": "ch-004"},
    )
    store.append(
        ledger_row_id="row-6",
        event_type="sandbox_blocked",
        outcome_type="blocked",
        request_id="req-005",
        plan_hash="plan-mno",
        payload={"blocked_reason": "command not allowed", "canonical_hash": "ch-005"},
    )
    yield store
    path.unlink(missing_ok=True)


@pytest.fixture
def c2_explainer(c2_ledger_store):
    """ExplanationBuilder with TraceBuilder for C2 tests."""
    trace_builder = TraceBuilder(c2_ledger_store)
    return ExplanationBuilder(trace_builder=trace_builder)


class TestC2ExecutionExplanation:
    """C2: ExecutionExplanation from C1 trace."""

    def test_refused_explanation(self, c2_explainer):
        """Refused: final_outcome REFUSED, summary and decisive_factors include refusal."""
        expl = c2_explainer.explain_from_request_id("req-001")
        assert isinstance(expl, ExecutionExplanation)
        assert expl.final_outcome == "REFUSED"
        assert "plan gate refused request" in expl.decisive_factors
        assert expl.summary.startswith("REFUSED because")
        assert expl.request_id == "req-001"
        assert expl.is_replay is False
        assert expl.evidence_refs == ("event[0]",)

    def test_deferred_explanation(self, c2_explainer):
        """Deferred: final_outcome PLAN_DEFERRED."""
        expl = c2_explainer.explain_from_request_id("req-003")
        assert expl.final_outcome == "PLAN_DEFERRED"
        assert "plan gate deferred execution" in expl.decisive_factors

    def test_bounded_explanation(self, c2_explainer):
        """Bounded: final_outcome PLAN_BOUNDED."""
        expl = c2_explainer.explain_from_request_id("req-004")
        assert expl.final_outcome == "PLAN_BOUNDED"
        assert "bounded allowance issued" in expl.decisive_factors

    def test_completed_execution_explanation(self, c2_explainer):
        """Completed: final_outcome EXECUTION_COMPLETED, factors include approval + completion."""
        expl = c2_explainer.explain_from_request_id("req-002")
        assert expl.final_outcome == "EXECUTION_COMPLETED"
        assert "plan gate approved execution" in expl.decisive_factors
        assert "sandbox completed execution" in expl.decisive_factors
        assert expl.evidence_refs == ("event[0]", "event[1]")

    def test_blocked_execution_explanation(self, c2_explainer):
        """Blocked: final_outcome EXECUTION_BLOCKED."""
        expl = c2_explainer.explain_from_request_id("req-005")
        assert expl.final_outcome == "EXECUTION_BLOCKED"
        assert "execution was blocked in sandbox" in expl.decisive_factors

    def test_replay_explanation(self, c2_ledger_store, c2_explainer):
        """Replay: is_replay True, decisive_factors include replay note."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = Path(f.name)
        try:
            store = SandboxLedgerStore(path, fixed_time="2026-03-13T11:00:00Z")
            store.append(
                ledger_row_id="replay-1",
                event_type="plangate_safe_execute",
                outcome_type="safe_execute",
                request_id="req-replay",
                plan_hash="p",
                payload={"canonical_hash": "ch-r", "execution_surface": "replay"},
            )
            store.append(
                ledger_row_id="replay-2",
                event_type="sandbox_executed",
                outcome_type="executed",
                request_id="req-replay",
                plan_hash="p",
                payload={"canonical_hash": "ch-r", "execution_surface": "replay", "exit_code": 0},
            )
            tb = TraceBuilder(store)
            explainer = ExplanationBuilder(trace_builder=tb)
            expl = explainer.explain_from_request_id("req-replay")
            assert expl.is_replay is True
            assert "request was replayed" in expl.decisive_factors
        finally:
            path.unlink(missing_ok=True)

    def test_explanation_by_canonical_hash(self, c2_explainer):
        """Explain by canonical_hash uses C1 latest request group only."""
        expl = c2_explainer.explain_from_canonical_hash("ch-002")
        assert expl.canonical_hash == "ch-002"
        assert expl.request_id == "req-002"
        assert expl.final_outcome == "EXECUTION_COMPLETED"

    def test_explain_trace_direct(self, c2_explainer):
        """explain_trace(trace) produces same result as explain_from_request_id."""
        trace_builder = c2_explainer._trace_builder
        trace = trace_builder.build_from_request_id("req-001")
        expl = c2_explainer.explain_trace(trace)
        assert expl.final_outcome == "REFUSED"
        assert expl.request_id == "req-001"

    def test_explain_trace_empty_raises(self, c2_explainer):
        """Empty trace raises ExplanationNotFoundError."""
        trace = ExecutionTrace(
            trace_id="empty",
            lookup_type="request_id",
            events=[],
            total_events=0,
            request_id="empty",
        )
        with pytest.raises(ExplanationNotFoundError) as exc_info:
            c2_explainer.explain_trace(trace)
        assert "No events" in str(exc_info.value)

    def test_explain_from_request_id_no_trace_raises(self, c2_explainer):
        """Request with no ledger rows raises ExplanationNotFoundError."""
        with pytest.raises(ExplanationNotFoundError):
            c2_explainer.explain_from_request_id("req-nonexistent")

    def test_explain_from_canonical_hash_no_trace_raises(self, c2_explainer):
        """Canonical hash with no rows raises ExplanationNotFoundError."""
        with pytest.raises(ExplanationNotFoundError):
            c2_explainer.explain_from_canonical_hash("ch-nonexistent")

    def test_explain_without_trace_builder_raises(self, c2_ledger_store):
        """explain_from_request_id without TraceBuilder raises ValueError."""
        explainer = ExplanationBuilder()
        with pytest.raises(ValueError, match="TraceBuilder required"):
            explainer.explain_from_request_id("req-001")

    def test_unknown_event_fallback(self, c2_ledger_store):
        """Unknown event type maps to UNKNOWN_EVENT and decisive factor."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = Path(f.name)
        try:
            store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")
            store.append(
                ledger_row_id="unk-1",
                event_type="custom_unknown",
                outcome_type="custom",
                request_id="req-unk",
                plan_hash="p",
                payload={},
            )
            tb = TraceBuilder(store)
            explainer = ExplanationBuilder(trace_builder=tb)
            expl = explainer.explain_from_request_id("req-unk")
            assert expl.final_outcome == "UNKNOWN_EVENT"
            assert "unknown event in trace" in expl.decisive_factors
        finally:
            path.unlink(missing_ok=True)

    def test_execution_explanation_to_dict(self, c2_explainer):
        """ExecutionExplanation.to_dict is deterministic."""
        expl = c2_explainer.explain_from_request_id("req-001")
        d = expl.to_dict()
        assert d["final_outcome"] == "REFUSED"
        assert "decisive_factors" in d
        assert "evidence_refs" in d
        assert d["is_replay"] is False

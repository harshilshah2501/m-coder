"""
M4.1 ExplanationBuilder Tests — Verify human-readable explanation payloads.

Tests:
- Build from TraceEvent
- Build from ledger row
- Build from GovernedExecutionResult
- Build from individual fields
- All decision types produce appropriate explanations
"""

import pytest

from runtime.observation.explanation_builder import ExplanationBuilder
from runtime.observation.models import TraceEvent, ExplanationPayload


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

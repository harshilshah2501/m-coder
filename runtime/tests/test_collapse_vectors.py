"""
Tests for M4.3 Collapse Vector Tracking.

Tests collapse event models, classifier, and query service.
Verifies deterministic detection of collapse classes from runtime evidence.
"""

import json
import pytest
from datetime import datetime, timezone

from runtime.observation.collapse_models import (
    CollapseClass,
    CollapseEvent,
    CollapseEvidence,
    CollapseSeverity,
    CollapseSummary,
    create_collapse_event,
)
from runtime.observation.collapse_vectors import (
    CollapseClassifier,
    ClassificationResult,
)
from runtime.observation.collapse_queries import (
    CollapseQueryService,
    CollapseFilter,
    find_related_collapses,
    build_collapse_chain,
)


class TestCollapseModels:
    """Tests for collapse event models."""
    
    def test_collapse_evidence_creation(self):
        """CollapseEvidence can be created with required fields."""
        evidence = CollapseEvidence(
            evidence_type="ledger_row",
            source_artifact="ledger:req-123",
            field_path="payload.canonical_hash",
            expected_value="<non-empty>",
            actual_value=None,
        )
        assert evidence.evidence_type == "ledger_row"
        assert evidence.source_artifact == "ledger:req-123"
        assert evidence.expected_value == "<non-empty>"
        assert evidence.actual_value is None
    
    def test_collapse_evidence_to_dict(self):
        """CollapseEvidence serializes to dictionary."""
        evidence = CollapseEvidence(
            evidence_type="ledger_row",
            source_artifact="ledger:req-123",
            field_path="payload.canonical_hash",
            expected_value="<non-empty>",
            actual_value=None,
            context={"event_type": "sandbox_executed"},
        )
        d = evidence.to_dict()
        assert d["evidence_type"] == "ledger_row"
        assert d["context"]["event_type"] == "sandbox_executed"
    
    def test_create_collapse_event_deterministic_id(self):
        """create_collapse_event generates deterministic event_id."""
        evidence = CollapseEvidence(
            evidence_type="ledger_row",
            source_artifact="ledger:req-123",
            field_path="payload.canonical_hash",
            expected_value="<non-empty>",
            actual_value=None,
        )
        
        event1 = create_collapse_event(
            collapse_class=CollapseClass.IDENTITY_PROPAGATION_MISSING,
            request_id="req-123",
            plan_hash="plan-abc",
            description="Test collapse",
            evidence=[evidence],
            timestamp_utc="2026-03-13T12:00:00Z",
        )
        
        event2 = create_collapse_event(
            collapse_class=CollapseClass.IDENTITY_PROPAGATION_MISSING,
            request_id="req-123",
            plan_hash="plan-abc",
            description="Test collapse",
            evidence=[evidence],
            timestamp_utc="2026-03-13T12:00:00Z",
        )
        
        assert event1.event_id == event2.event_id
        assert event1.event_id.startswith("collapse-")
    
    def test_collapse_event_to_dict(self):
        """CollapseEvent serializes to schema-compliant dictionary."""
        evidence = CollapseEvidence(
            evidence_type="ledger_row",
            source_artifact="ledger:req-123",
            field_path="payload.canonical_hash",
            expected_value="<non-empty>",
            actual_value=None,
        )
        
        event = create_collapse_event(
            collapse_class=CollapseClass.IDENTITY_PROPAGATION_MISSING,
            request_id="req-123",
            plan_hash="plan-abc",
            description="Test collapse",
            evidence=[evidence],
        )
        
        d = event.to_dict()
        assert d["schema_version"] == "collapse_event.v0.1"
        assert d["collapse_class"] == "identity_propagation_missing"
        assert d["severity"] == "high"
        assert d["request_id"] == "req-123"
        assert len(d["evidence"]) == 1
    
    def test_collapse_event_validate(self):
        """CollapseEvent.validate detects missing required fields."""
        evidence = CollapseEvidence(
            evidence_type="test",
            source_artifact="test",
            field_path="test",
            expected_value=None,
            actual_value=None,
        )
        
        event = CollapseEvent(
            event_id="",
            timestamp_utc="",
            collapse_class=CollapseClass.IDENTITY_PROPAGATION_MISSING,
            severity=CollapseSeverity.HIGH,
            request_id="",
            plan_hash="",
            description="Test",
            evidence=tuple(),
        )
        
        errors = event.validate()
        assert "event_id required" in errors
        assert "timestamp_utc required" in errors
        assert "at least one evidence item required" in errors
    
    def test_collapse_summary_from_events(self):
        """CollapseSummary.from_events aggregates correctly."""
        evidence = CollapseEvidence(
            evidence_type="test",
            source_artifact="test",
            field_path="test",
            expected_value=None,
            actual_value=None,
        )
        
        events = [
            create_collapse_event(
                collapse_class=CollapseClass.IDENTITY_PROPAGATION_MISSING,
                request_id="req-1",
                plan_hash="plan-1",
                description="Test 1",
                evidence=[evidence],
            ),
            create_collapse_event(
                collapse_class=CollapseClass.DECISION_EXECUTION_MISMATCH,
                request_id="req-2",
                plan_hash="plan-2",
                description="Test 2",
                evidence=[evidence],
                severity=CollapseSeverity.CRITICAL,
            ),
            create_collapse_event(
                collapse_class=CollapseClass.IDENTITY_PROPAGATION_MISSING,
                request_id="req-3",
                plan_hash="plan-3",
                description="Test 3",
                evidence=[evidence],
            ),
        ]
        
        summary = CollapseSummary.from_events(events)
        
        assert summary.total_events == 3
        assert summary.by_class["identity_propagation_missing"] == 2
        assert summary.by_class["decision_execution_mismatch"] == 1
        assert summary.by_severity["high"] == 2
        assert summary.by_severity["critical"] == 1
        assert summary.has_critical()
    
    def test_default_severity_mapping(self):
        """Collapse classes have expected default severities."""
        evidence = CollapseEvidence(
            evidence_type="test",
            source_artifact="test",
            field_path="test",
            expected_value=None,
            actual_value=None,
        )
        
        event = create_collapse_event(
            collapse_class=CollapseClass.DECISION_EXECUTION_MISMATCH,
            request_id="req-1",
            plan_hash="plan-1",
            description="Test",
            evidence=[evidence],
        )
        assert event.severity == CollapseSeverity.CRITICAL
        
        event = create_collapse_event(
            collapse_class=CollapseClass.IDENTITY_PROPAGATION_MISSING,
            request_id="req-1",
            plan_hash="plan-1",
            description="Test",
            evidence=[evidence],
        )
        assert event.severity == CollapseSeverity.HIGH
        
        event = create_collapse_event(
            collapse_class=CollapseClass.MISSING_TRACE_LINKAGE,
            request_id="req-1",
            plan_hash="plan-1",
            description="Test",
            evidence=[evidence],
        )
        assert event.severity == CollapseSeverity.MEDIUM


class TestCollapseClassifier:
    """Tests for collapse vector classifier."""
    
    def test_classify_ledger_row_missing_canonical_hash(self):
        """Classifier detects missing canonical_hash in execution rows."""
        classifier = CollapseClassifier(require_canonical_hash=True)
        
        row = {
            "event_type": "sandbox_executed",
            "event": {"request_id": "req-123"},
            "plan_link": {"plan_hash": "plan-abc"},
            "payload": {},
        }
        
        events = classifier.classify_ledger_row(row)
        
        assert len(events) == 1
        assert events[0].collapse_class == CollapseClass.IDENTITY_PROPAGATION_MISSING
        assert "canonical_hash missing" in events[0].description
    
    def test_classify_ledger_row_with_canonical_hash(self):
        """Classifier does not flag rows with canonical_hash present."""
        classifier = CollapseClassifier(require_canonical_hash=True)
        
        row = {
            "event_type": "sandbox_executed",
            "event": {"request_id": "req-123"},
            "plan_link": {"plan_hash": "plan-abc"},
            "payload": {"canonical_hash": "abc123"},
        }
        
        events = classifier.classify_ledger_row(row)
        
        assert len(events) == 0
    
    def test_classify_ledger_row_missing_linkage(self):
        """Classifier detects missing trace linkage."""
        classifier = CollapseClassifier()
        
        row = {
            "event_type": "sandbox_executed",
            "event": {},
            "plan_link": {},
            "payload": {"canonical_hash": "abc123"},
        }
        
        events = classifier.classify_ledger_row(row)
        
        assert any(e.collapse_class == CollapseClass.MISSING_TRACE_LINKAGE for e in events)
    
    def test_classify_decision_execution_mismatch_canonical_hash(self):
        """Classifier detects canonical_hash mismatch between decision and execution."""
        classifier = CollapseClassifier()
        
        decision_row = {
            "event": {"request_id": "req-123"},
            "plan_link": {"plan_hash": "plan-abc"},
            "payload": {
                "canonical_hash": "hash-1",
                "decision_posture": "safe_execute",
            },
        }
        
        execution_row = {
            "event": {"request_id": "req-123"},
            "plan_link": {"plan_hash": "plan-abc"},
            "payload": {
                "canonical_hash": "hash-2",
                "execution_outcome": "success",
            },
        }
        
        events = classifier.classify_decision_execution_pair(decision_row, execution_row)
        
        assert len(events) >= 1
        assert any(
            e.collapse_class == CollapseClass.DECISION_EXECUTION_MISMATCH
            and "canonical_hash" in e.description
            for e in events
        )
    
    def test_classify_decision_execution_mismatch_posture_outcome(self):
        """Classifier detects posture/outcome conflict."""
        classifier = CollapseClassifier()
        
        decision_row = {
            "event": {"request_id": "req-123"},
            "plan_link": {"plan_hash": "plan-abc"},
            "payload": {
                "canonical_hash": "hash-1",
                "decision_posture": "refuse",
            },
        }
        
        execution_row = {
            "event": {"request_id": "req-123"},
            "plan_link": {"plan_hash": "plan-abc"},
            "payload": {
                "canonical_hash": "hash-1",
                "execution_outcome": "success",
            },
        }
        
        events = classifier.classify_decision_execution_pair(decision_row, execution_row)
        
        assert any(
            e.collapse_class == CollapseClass.DECISION_EXECUTION_MISMATCH
            and "refuse" in e.description
            for e in events
        )
    
    def test_classify_decision_execution_request_id_mismatch(self):
        """Classifier detects request_id mismatch between decision and execution."""
        classifier = CollapseClassifier()
        
        decision_row = {
            "event": {"request_id": "req-123"},
            "plan_link": {"plan_hash": "plan-abc"},
            "payload": {"decision_posture": "safe_execute"},
        }
        
        execution_row = {
            "event": {"request_id": "req-456"},
            "plan_link": {"plan_hash": "plan-abc"},
            "payload": {"execution_outcome": "success"},
        }
        
        events = classifier.classify_decision_execution_pair(decision_row, execution_row)
        
        assert any(e.collapse_class == CollapseClass.MISSING_EVIDENCE_JOIN for e in events)
    
    def test_classify_replay_mismatch_canonical_hash(self):
        """Classifier detects replay canonical_hash mismatch."""
        classifier = CollapseClassifier()
        
        original = {
            "request_id": "req-123",
            "plan_hash": "plan-abc",
            "canonical_hash": "hash-1",
            "terminal_posture": "safe_execute",
        }
        
        replayed = {
            "request_id": "req-123",
            "plan_hash": "plan-abc",
            "canonical_hash": "hash-2",
            "terminal_posture": "safe_execute",
        }
        
        events = classifier.classify_replay_comparison(original, replayed)
        
        assert len(events) >= 1
        assert any(
            e.collapse_class == CollapseClass.REPLAY_MISMATCH
            and "canonical_hash" in e.description
            for e in events
        )
    
    def test_classify_replay_mismatch_posture(self):
        """Classifier detects replay posture mismatch."""
        classifier = CollapseClassifier()
        
        original = {
            "request_id": "req-123",
            "plan_hash": "plan-abc",
            "terminal_posture": "safe_execute",
        }
        
        replayed = {
            "request_id": "req-123",
            "plan_hash": "plan-abc",
            "terminal_posture": "refuse",
        }
        
        events = classifier.classify_replay_comparison(original, replayed)
        
        assert any(
            e.collapse_class == CollapseClass.REPLAY_MISMATCH
            and "posture" in e.description
            for e in events
        )
    
    def test_classify_baseline_drift_refusal_rate(self):
        """Classifier detects refusal rate drift."""
        classifier = CollapseClassifier(refusal_drift_threshold=0.02)
        
        baseline = {"refusal_rate": 0.05, "crossed_count": 0}
        current = {"refusal_rate": 0.10, "crossed_count": 0}
        
        events = classifier.classify_baseline_drift(baseline, current)
        
        assert len(events) >= 1
        assert any(
            e.collapse_class == CollapseClass.UNEXPECTED_REFUSAL_DISTRIBUTION_DRIFT
            and "refusal" in e.description.lower()
            for e in events
        )
    
    def test_classify_baseline_drift_crossed_increase(self):
        """Classifier detects boundary crossed count increase."""
        classifier = CollapseClassifier()
        
        baseline = {"refusal_rate": 0.05, "crossed_count": 0}
        current = {"refusal_rate": 0.05, "crossed_count": 1}
        
        events = classifier.classify_baseline_drift(baseline, current)
        
        assert any(
            e.collapse_class == CollapseClass.UNEXPECTED_REFUSAL_DISTRIBUTION_DRIFT
            and "crossed" in e.description.lower()
            for e in events
        )
    
    def test_classify_trace_summary_missing_linkage(self):
        """Classifier detects missing trace linkage."""
        classifier = CollapseClassifier()
        
        trace = {
            "session_id": "sess-123",
            "has_plan": True,
            "has_decision": True,
        }
        
        events = classifier.classify_trace_summary(trace)
        
        assert any(e.collapse_class == CollapseClass.MISSING_TRACE_LINKAGE for e in events)
    
    def test_classify_trace_summary_missing_execution(self):
        """Classifier detects missing execution for safe_execute."""
        classifier = CollapseClassifier()
        
        trace = {
            "request_id": "req-123",
            "plan_hash": "plan-abc",
            "has_decision": True,
            "final_posture": "safe_execute",
            "has_execution": False,
        }
        
        events = classifier.classify_trace_summary(trace)
        
        assert any(
            e.collapse_class == CollapseClass.MISSING_EVIDENCE_JOIN
            and "safe_execute" in e.description
            for e in events
        )
    
    def test_classify_trace_summary_execution_without_decision(self):
        """Classifier detects execution without decision (bypass risk)."""
        classifier = CollapseClassifier()
        
        trace = {
            "request_id": "req-123",
            "plan_hash": "plan-abc",
            "has_decision": False,
            "has_execution": True,
        }
        
        events = classifier.classify_trace_summary(trace)
        
        assert any(
            e.collapse_class == CollapseClass.MISSING_EVIDENCE_JOIN
            and "bypass" in e.description.lower()
            for e in events
        )
    
    def test_classify_batch(self):
        """Classifier processes batch of evidence."""
        classifier = CollapseClassifier()
        
        ledger_rows = [
            {
                "event_type": "sandbox_executed",
                "event": {"request_id": "req-1"},
                "plan_link": {"plan_hash": "plan-1"},
                "payload": {},
            },
            {
                "event_type": "sandbox_executed",
                "event": {"request_id": "req-2"},
                "plan_link": {"plan_hash": "plan-2"},
                "payload": {"canonical_hash": "hash-2"},
            },
        ]
        
        trace_summaries = [
            {
                "request_id": "req-3",
                "plan_hash": "plan-3",
                "has_decision": False,
                "has_execution": True,
            },
        ]
        
        result = classifier.classify_batch(
            ledger_rows=ledger_rows,
            trace_summaries=trace_summaries,
        )
        
        assert result.items_processed == 3
        assert result.has_collapses()
        assert len(result.errors) == 0


class TestCollapseQueryService:
    """Tests for collapse query service."""
    
    def _make_event(
        self,
        collapse_class: CollapseClass,
        request_id: str,
        plan_hash: str,
        severity: CollapseSeverity = CollapseSeverity.MEDIUM,
        timestamp: str = "2026-03-13T12:00:00Z",
    ) -> CollapseEvent:
        """Helper to create test events."""
        evidence = CollapseEvidence(
            evidence_type="test",
            source_artifact="test",
            field_path="test",
            expected_value=None,
            actual_value=None,
        )
        return create_collapse_event(
            collapse_class=collapse_class,
            request_id=request_id,
            plan_hash=plan_hash,
            description="Test event",
            evidence=[evidence],
            severity=severity,
            timestamp_utc=timestamp,
        )
    
    def test_add_and_query_events(self):
        """Service stores and retrieves events."""
        service = CollapseQueryService()
        
        event = self._make_event(
            CollapseClass.IDENTITY_PROPAGATION_MISSING,
            "req-1",
            "plan-1",
        )
        service.add_event(event)
        
        events = service.query()
        assert len(events) == 1
        assert events[0].request_id == "req-1"
    
    def test_query_with_filter(self):
        """Service filters events by criteria."""
        service = CollapseQueryService()
        
        service.add_events([
            self._make_event(CollapseClass.IDENTITY_PROPAGATION_MISSING, "req-1", "plan-1"),
            self._make_event(CollapseClass.DECISION_EXECUTION_MISMATCH, "req-2", "plan-2"),
            self._make_event(CollapseClass.IDENTITY_PROPAGATION_MISSING, "req-3", "plan-3"),
        ])
        
        filter_ = CollapseFilter(
            collapse_classes=[CollapseClass.IDENTITY_PROPAGATION_MISSING]
        )
        events = service.query(filter_)
        
        assert len(events) == 2
        assert all(e.collapse_class == CollapseClass.IDENTITY_PROPAGATION_MISSING for e in events)
    
    def test_query_with_severity_filter(self):
        """Service filters events by severity."""
        service = CollapseQueryService()
        
        service.add_events([
            self._make_event(
                CollapseClass.IDENTITY_PROPAGATION_MISSING,
                "req-1",
                "plan-1",
                severity=CollapseSeverity.LOW,
            ),
            self._make_event(
                CollapseClass.DECISION_EXECUTION_MISMATCH,
                "req-2",
                "plan-2",
                severity=CollapseSeverity.CRITICAL,
            ),
            self._make_event(
                CollapseClass.REPLAY_MISMATCH,
                "req-3",
                "plan-3",
                severity=CollapseSeverity.HIGH,
            ),
        ])
        
        filter_ = CollapseFilter(min_severity=CollapseSeverity.HIGH)
        events = service.query(filter_)
        
        assert len(events) == 2
        assert all(
            e.severity in (CollapseSeverity.HIGH, CollapseSeverity.CRITICAL)
            for e in events
        )
    
    def test_query_with_time_range(self):
        """Service filters events by time range."""
        service = CollapseQueryService()
        
        service.add_events([
            self._make_event(
                CollapseClass.IDENTITY_PROPAGATION_MISSING,
                "req-1",
                "plan-1",
                timestamp="2026-03-13T10:00:00Z",
            ),
            self._make_event(
                CollapseClass.IDENTITY_PROPAGATION_MISSING,
                "req-2",
                "plan-2",
                timestamp="2026-03-13T12:00:00Z",
            ),
            self._make_event(
                CollapseClass.IDENTITY_PROPAGATION_MISSING,
                "req-3",
                "plan-3",
                timestamp="2026-03-13T14:00:00Z",
            ),
        ])
        
        filter_ = CollapseFilter(
            start_time="2026-03-13T11:00:00Z",
            end_time="2026-03-13T13:00:00Z",
        )
        events = service.query(filter_)
        
        assert len(events) == 1
        assert events[0].request_id == "req-2"
    
    def test_get_by_request_id(self):
        """Service retrieves events by request_id."""
        service = CollapseQueryService()
        
        service.add_events([
            self._make_event(CollapseClass.IDENTITY_PROPAGATION_MISSING, "req-1", "plan-1"),
            self._make_event(CollapseClass.DECISION_EXECUTION_MISMATCH, "req-1", "plan-2"),
            self._make_event(CollapseClass.REPLAY_MISMATCH, "req-2", "plan-3"),
        ])
        
        events = service.get_by_request_id("req-1")
        
        assert len(events) == 2
        assert all(e.request_id == "req-1" for e in events)
    
    def test_get_critical(self):
        """Service retrieves critical events."""
        service = CollapseQueryService()
        
        service.add_events([
            self._make_event(
                CollapseClass.IDENTITY_PROPAGATION_MISSING,
                "req-1",
                "plan-1",
                severity=CollapseSeverity.HIGH,
            ),
            self._make_event(
                CollapseClass.DECISION_EXECUTION_MISMATCH,
                "req-2",
                "plan-2",
                severity=CollapseSeverity.CRITICAL,
            ),
        ])
        
        events = service.get_critical()
        
        assert len(events) == 1
        assert events[0].severity == CollapseSeverity.CRITICAL
    
    def test_summarize(self):
        """Service generates summary from events."""
        service = CollapseQueryService()
        
        service.add_events([
            self._make_event(CollapseClass.IDENTITY_PROPAGATION_MISSING, "req-1", "plan-1"),
            self._make_event(CollapseClass.DECISION_EXECUTION_MISMATCH, "req-2", "plan-2"),
            self._make_event(CollapseClass.IDENTITY_PROPAGATION_MISSING, "req-3", "plan-3"),
        ])
        
        summary = service.summarize()
        
        assert summary.total_events == 3
        assert summary.by_class["identity_propagation_missing"] == 2
    
    def test_group_by_class(self):
        """Service groups events by collapse class."""
        service = CollapseQueryService()
        
        service.add_events([
            self._make_event(CollapseClass.IDENTITY_PROPAGATION_MISSING, "req-1", "plan-1"),
            self._make_event(CollapseClass.DECISION_EXECUTION_MISMATCH, "req-2", "plan-2"),
            self._make_event(CollapseClass.IDENTITY_PROPAGATION_MISSING, "req-3", "plan-3"),
        ])
        
        groups = service.group_by_class()
        
        assert len(groups[CollapseClass.IDENTITY_PROPAGATION_MISSING]) == 2
        assert len(groups[CollapseClass.DECISION_EXECUTION_MISMATCH]) == 1
    
    def test_find_related_collapses(self):
        """find_related_collapses finds events sharing linkage keys."""
        service = CollapseQueryService()
        
        event1 = self._make_event(CollapseClass.IDENTITY_PROPAGATION_MISSING, "req-1", "plan-1")
        event2 = self._make_event(CollapseClass.DECISION_EXECUTION_MISMATCH, "req-1", "plan-2")
        event3 = self._make_event(CollapseClass.REPLAY_MISMATCH, "req-2", "plan-1")
        event4 = self._make_event(CollapseClass.MISSING_TRACE_LINKAGE, "req-3", "plan-3")
        
        service.add_events([event1, event2, event3, event4])
        
        related = find_related_collapses(service, event1)
        
        assert len(related) == 2
        related_ids = {e.event_id for e in related}
        assert event2.event_id in related_ids
        assert event3.event_id in related_ids
        assert event4.event_id not in related_ids
    
    def test_build_collapse_chain(self):
        """build_collapse_chain returns chronological events for request."""
        service = CollapseQueryService()
        
        service.add_events([
            self._make_event(
                CollapseClass.IDENTITY_PROPAGATION_MISSING,
                "req-1",
                "plan-1",
                timestamp="2026-03-13T12:00:00Z",
            ),
            self._make_event(
                CollapseClass.DECISION_EXECUTION_MISMATCH,
                "req-1",
                "plan-1",
                timestamp="2026-03-13T10:00:00Z",
            ),
            self._make_event(
                CollapseClass.REPLAY_MISMATCH,
                "req-2",
                "plan-2",
                timestamp="2026-03-13T11:00:00Z",
            ),
        ])
        
        chain = build_collapse_chain(service, "req-1")
        
        assert len(chain) == 2
        assert chain[0].timestamp_utc < chain[1].timestamp_utc


class TestCollapseFilter:
    """Tests for collapse filter."""
    
    def test_filter_matches_all_criteria(self):
        """Filter requires all criteria to match."""
        evidence = CollapseEvidence(
            evidence_type="test",
            source_artifact="test",
            field_path="test",
            expected_value=None,
            actual_value=None,
        )
        
        event = create_collapse_event(
            collapse_class=CollapseClass.IDENTITY_PROPAGATION_MISSING,
            request_id="req-1",
            plan_hash="plan-1",
            description="Test",
            evidence=[evidence],
            severity=CollapseSeverity.HIGH,
            timestamp_utc="2026-03-13T12:00:00Z",
        )
        
        filter_ = CollapseFilter(
            collapse_classes=[CollapseClass.IDENTITY_PROPAGATION_MISSING],
            request_ids=["req-1"],
        )
        assert filter_.matches(event)
        
        filter_ = CollapseFilter(
            collapse_classes=[CollapseClass.DECISION_EXECUTION_MISMATCH],
            request_ids=["req-1"],
        )
        assert not filter_.matches(event)
    
    def test_filter_to_dict(self):
        """Filter serializes to dictionary."""
        filter_ = CollapseFilter(
            collapse_classes=[CollapseClass.IDENTITY_PROPAGATION_MISSING],
            severities=[CollapseSeverity.HIGH, CollapseSeverity.CRITICAL],
            min_severity=CollapseSeverity.MEDIUM,
        )
        
        d = filter_.to_dict()
        
        assert d["collapse_classes"] == ["identity_propagation_missing"]
        assert "high" in d["severities"]
        assert d["min_severity"] == "medium"


class TestClassificationResult:
    """Tests for classification result."""
    
    def test_result_to_dict(self):
        """ClassificationResult serializes to dictionary."""
        evidence = CollapseEvidence(
            evidence_type="test",
            source_artifact="test",
            field_path="test",
            expected_value=None,
            actual_value=None,
        )
        
        event = create_collapse_event(
            collapse_class=CollapseClass.IDENTITY_PROPAGATION_MISSING,
            request_id="req-1",
            plan_hash="plan-1",
            description="Test",
            evidence=[evidence],
        )
        
        result = ClassificationResult(
            events=[event],
            items_processed=1,
            errors=[],
        )
        
        d = result.to_dict()
        
        assert d["events_count"] == 1
        assert d["items_processed"] == 1
        assert len(d["errors"]) == 0
    
    def test_result_has_critical(self):
        """ClassificationResult.has_critical detects critical events."""
        evidence = CollapseEvidence(
            evidence_type="test",
            source_artifact="test",
            field_path="test",
            expected_value=None,
            actual_value=None,
        )
        
        result = ClassificationResult(
            events=[
                create_collapse_event(
                    collapse_class=CollapseClass.IDENTITY_PROPAGATION_MISSING,
                    request_id="req-1",
                    plan_hash="plan-1",
                    description="Test",
                    evidence=[evidence],
                    severity=CollapseSeverity.HIGH,
                ),
            ],
            items_processed=1,
        )
        assert not result.has_critical()
        
        result.events.append(
            create_collapse_event(
                collapse_class=CollapseClass.DECISION_EXECUTION_MISMATCH,
                request_id="req-2",
                plan_hash="plan-2",
                description="Test",
                evidence=[evidence],
                severity=CollapseSeverity.CRITICAL,
            )
        )
        assert result.has_critical()

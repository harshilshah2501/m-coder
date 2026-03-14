"""
Tests for M4.5 GREG Escalation.

Covers:
- EscalationPolicy threshold evaluation
- EscalationDecision determinism
- GREGBundle serialization
- BundleBuilder construction
- Evidence classification
- Ledger reference preservation
"""

import json
import pytest
from datetime import datetime, timezone

from runtime.observation.greg_escalation import (
    CollapseType,
    EscalationDecision,
    EscalationPolicy,
    EscalationSeverity,
    EscalationThresholds,
    EscalationType,
    EscalationTrigger,
    ObservationInput,
)
from runtime.observation.greg_bundle import (
    BundleSummary,
    CollapseClassification,
    CollapseEvidence,
    DriftEvidence,
    EscalationEvidence,
    EscalationMismatchType,
    GREGBundle,
    IntegrityEvidence,
    LedgerReference,
    MismatchEvidence,
)
from runtime.observation.bundle_builder import (
    BundleBuilder,
    BundleInputs,
    RawCollapse,
    RawDrift,
    RawIntegrityViolation,
    RawMismatch,
)


# ============================================================================
# EscalationPolicy Tests
# ============================================================================


class TestEscalationThresholds:
    """Tests for EscalationThresholds configuration."""
    
    def test_default_thresholds(self) -> None:
        """Default thresholds have expected values."""
        t = EscalationThresholds()
        assert t.mismatch_count_low == 5
        assert t.mismatch_count_critical == 50
        assert t.collapse_count_low == 1
        assert t.drift_percentage_low == 0.05
        assert t.integrity_violation_immediate is True
    
    def test_custom_thresholds(self) -> None:
        """Custom thresholds are respected."""
        t = EscalationThresholds(
            mismatch_count_low=10,
            mismatch_count_critical=100,
        )
        assert t.mismatch_count_low == 10
        assert t.mismatch_count_critical == 100
    
    def test_thresholds_to_dict(self) -> None:
        """Thresholds serialize to dict correctly."""
        t = EscalationThresholds()
        d = t.to_dict()
        assert "mismatch_count_low" in d
        assert "collapse_count_critical" in d
        assert d["integrity_violation_immediate"] is True


class TestEscalationPolicy:
    """Tests for EscalationPolicy evaluation."""
    
    @pytest.fixture
    def policy(self) -> EscalationPolicy:
        return EscalationPolicy(fixed_time="2026-03-13T12:00:00Z")
    
    def test_no_triggers_no_escalation(self, policy: EscalationPolicy) -> None:
        """Empty observation produces no escalation."""
        obs = ObservationInput()
        decision = policy.evaluate(obs)
        assert decision.should_escalate is False
        assert len(decision.triggers) == 0
        assert decision.overall_severity == EscalationSeverity.LOW
    
    def test_mismatch_threshold_low(self, policy: EscalationPolicy) -> None:
        """Mismatch count at low threshold triggers low severity."""
        obs = ObservationInput(
            mismatch_count=5,
            mismatch_request_ids=["req-1", "req-2", "req-3", "req-4", "req-5"],
        )
        decision = policy.evaluate(obs)
        assert decision.should_escalate is True
        assert len(decision.triggers) == 1
        assert decision.triggers[0].escalation_type == EscalationType.MISMATCH_THRESHOLD
        assert decision.triggers[0].severity == EscalationSeverity.LOW
        assert decision.overall_severity == EscalationSeverity.LOW
    
    def test_mismatch_threshold_critical(self, policy: EscalationPolicy) -> None:
        """Mismatch count at critical threshold triggers critical severity."""
        obs = ObservationInput(mismatch_count=50)
        decision = policy.evaluate(obs)
        assert decision.should_escalate is True
        assert decision.triggers[0].severity == EscalationSeverity.CRITICAL
        assert decision.overall_severity == EscalationSeverity.CRITICAL
    
    def test_collapse_vector_single(self, policy: EscalationPolicy) -> None:
        """Single collapse vector triggers low severity."""
        obs = ObservationInput(
            collapse_vectors=[
                {"request_id": "req-1", "collapse_type": "REF_SOFTENING"},
            ],
        )
        decision = policy.evaluate(obs)
        assert decision.should_escalate is True
        assert decision.triggers[0].escalation_type == EscalationType.COLLAPSE_VECTOR
        assert decision.triggers[0].severity == EscalationSeverity.LOW
    
    def test_collapse_vector_critical(self, policy: EscalationPolicy) -> None:
        """Many collapse vectors trigger critical severity."""
        obs = ObservationInput(
            collapse_vectors=[{"request_id": f"req-{i}"} for i in range(10)],
        )
        decision = policy.evaluate(obs)
        assert decision.should_escalate is True
        assert decision.triggers[0].severity == EscalationSeverity.CRITICAL
    
    def test_drift_percentage_low(self, policy: EscalationPolicy) -> None:
        """Drift at 5% triggers low severity."""
        obs = ObservationInput(
            drift_percentage=0.05,
            drift_request_ids=["req-1"],
        )
        decision = policy.evaluate(obs)
        assert decision.should_escalate is True
        assert decision.triggers[0].escalation_type == EscalationType.DRIFT_BREACH
        assert decision.triggers[0].severity == EscalationSeverity.LOW
    
    def test_drift_percentage_critical(self, policy: EscalationPolicy) -> None:
        """Drift at 35%+ triggers critical severity."""
        obs = ObservationInput(drift_percentage=0.35)
        decision = policy.evaluate(obs)
        assert decision.should_escalate is True
        assert decision.triggers[0].severity == EscalationSeverity.CRITICAL
    
    def test_authority_failure_medium(self, policy: EscalationPolicy) -> None:
        """Authority failures at 10+ trigger medium severity."""
        obs = ObservationInput(
            authority_failure_count=10,
            authority_failure_request_ids=[f"req-{i}" for i in range(10)],
        )
        decision = policy.evaluate(obs)
        assert decision.should_escalate is True
        assert decision.triggers[0].escalation_type == EscalationType.AUTHORITY_FAILURE_SPIKE
        assert decision.triggers[0].severity == EscalationSeverity.MEDIUM
    
    def test_boundary_anomaly_high(self, policy: EscalationPolicy) -> None:
        """Boundary anomalies at 5+ trigger high severity."""
        obs = ObservationInput(
            boundary_anomaly_count=5,
            boundary_anomaly_request_ids=["req-1", "req-2", "req-3", "req-4", "req-5"],
        )
        decision = policy.evaluate(obs)
        assert decision.should_escalate is True
        assert decision.triggers[0].escalation_type == EscalationType.BOUNDARY_ANOMALY
        assert decision.triggers[0].severity == EscalationSeverity.HIGH
    
    def test_integrity_violation_always_critical(self, policy: EscalationPolicy) -> None:
        """Any integrity violation triggers critical severity."""
        obs = ObservationInput(
            integrity_violations=[
                {"request_id": "req-1", "violation_type": "hash_mismatch"},
            ],
        )
        decision = policy.evaluate(obs)
        assert decision.should_escalate is True
        assert decision.triggers[0].escalation_type == EscalationType.INTEGRITY_VIOLATION
        assert decision.triggers[0].severity == EscalationSeverity.CRITICAL
        assert decision.overall_severity == EscalationSeverity.CRITICAL
    
    def test_multiple_triggers_max_severity(self, policy: EscalationPolicy) -> None:
        """Multiple triggers use max severity for overall."""
        obs = ObservationInput(
            mismatch_count=5,  # low
            collapse_vectors=[{"request_id": f"req-{i}"} for i in range(5)],  # high
        )
        decision = policy.evaluate(obs)
        assert decision.should_escalate is True
        assert len(decision.triggers) == 2
        assert decision.overall_severity == EscalationSeverity.HIGH
    
    def test_deterministic_evaluation(self, policy: EscalationPolicy) -> None:
        """Same input produces same decision."""
        obs = ObservationInput(
            mismatch_count=15,
            mismatch_request_ids=["req-1"],
        )
        decision1 = policy.evaluate(obs)
        decision2 = policy.evaluate(obs)
        assert decision1.to_dict() == decision2.to_dict()
    
    def test_affected_ids_limited(self, policy: EscalationPolicy) -> None:
        """Affected IDs are limited to 50."""
        obs = ObservationInput(
            mismatch_count=100,
            mismatch_request_ids=[f"req-{i}" for i in range(100)],
        )
        decision = policy.evaluate(obs)
        assert len(decision.triggers[0].affected_request_ids) == 50


class TestEscalationDecision:
    """Tests for EscalationDecision data structure."""
    
    def test_decision_to_dict(self) -> None:
        """Decision serializes correctly."""
        trigger = EscalationTrigger(
            escalation_type=EscalationType.MISMATCH_THRESHOLD,
            severity=EscalationSeverity.MEDIUM,
            count=15,
            threshold_breached=15,
            affected_request_ids=["req-1"],
        )
        decision = EscalationDecision(
            should_escalate=True,
            overall_severity=EscalationSeverity.MEDIUM,
            triggers=[trigger],
            evaluation_timestamp="2026-03-13T12:00:00Z",
        )
        d = decision.to_dict()
        assert d["should_escalate"] is True
        assert d["overall_severity"] == "medium"
        assert len(d["triggers"]) == 1
        assert d["triggers"][0]["escalation_type"] == "mismatch_threshold"
    
    def test_evaluation_id_generated(self) -> None:
        """Evaluation ID is auto-generated."""
        decision = EscalationDecision(
            should_escalate=False,
            overall_severity=EscalationSeverity.LOW,
        )
        assert decision.evaluation_id.startswith("eval-")
        assert len(decision.evaluation_id) == 29  # "eval-" + 24 hex chars


# ============================================================================
# GREGBundle Tests
# ============================================================================


class TestLedgerReference:
    """Tests for LedgerReference data structure."""
    
    def test_ledger_ref_round_trip(self) -> None:
        """LedgerReference serializes and deserializes correctly."""
        ref = LedgerReference(
            event_id="evt-123",
            event_type="plangate_refused",
            request_id="req-456",
            plan_hash="abc123",
            timestamp_utc="2026-03-13T12:00:00Z",
            canonical_hash="def789",
        )
        d = ref.to_dict()
        ref2 = LedgerReference.from_dict(d)
        assert ref2.event_id == ref.event_id
        assert ref2.canonical_hash == ref.canonical_hash


class TestMismatchEvidence:
    """Tests for MismatchEvidence data structure."""
    
    def test_mismatch_evidence_round_trip(self) -> None:
        """MismatchEvidence serializes and deserializes correctly."""
        ledger_ref = LedgerReference(
            event_id="evt-1",
            event_type="decision_emitted",
            request_id="req-1",
            plan_hash="hash-1",
            timestamp_utc="2026-03-13T12:00:00Z",
        )
        evidence = MismatchEvidence(
            request_id="req-1",
            canonical_hash="can-hash-1",
            classification=EscalationMismatchType.PHASE_MISMATCH,
            expected_value="REF",
            actual_value="DES",
            context={"note": "unexpected phase"},
            ledger_refs=[ledger_ref],
        )
        d = evidence.to_dict()
        evidence2 = MismatchEvidence.from_dict(d)
        assert evidence2.classification == EscalationMismatchType.PHASE_MISMATCH
        assert evidence2.expected_value == "REF"
        assert len(evidence2.ledger_refs) == 1


class TestCollapseEvidence:
    """Tests for CollapseEvidence data structure."""
    
    def test_collapse_classifications(self) -> None:
        """All collapse classifications are valid."""
        for cls in CollapseClassification:
            evidence = CollapseEvidence(
                request_id="req-1",
                canonical_hash="hash-1",
                classification=cls,
                description=f"Test {cls.value}",
                severity="medium",
            )
            d = evidence.to_dict()
            assert d["classification"] == cls.value


class TestEscalationEvidence:
    """Tests for EscalationEvidence aggregation."""
    
    def test_total_count(self) -> None:
        """Total count sums all evidence types."""
        evidence = EscalationEvidence(
            mismatches=[
                MismatchEvidence(
                    request_id="req-1",
                    canonical_hash="",
                    classification=EscalationMismatchType.PHASE_MISMATCH,
                    expected_value="",
                    actual_value="",
                ),
            ],
            collapses=[
                CollapseEvidence(
                    request_id="req-2",
                    canonical_hash="",
                    classification=CollapseClassification.REF_SOFTENING,
                    description="",
                    severity="low",
                ),
            ],
        )
        assert evidence.total_count() == 2
    
    def test_affected_request_ids_unique(self) -> None:
        """Affected request IDs are unique and sorted."""
        evidence = EscalationEvidence(
            mismatches=[
                MismatchEvidence(
                    request_id="req-2",
                    canonical_hash="",
                    classification=EscalationMismatchType.PHASE_MISMATCH,
                    expected_value="",
                    actual_value="",
                ),
                MismatchEvidence(
                    request_id="req-1",
                    canonical_hash="",
                    classification=EscalationMismatchType.PHASE_MISMATCH,
                    expected_value="",
                    actual_value="",
                ),
                MismatchEvidence(
                    request_id="req-2",
                    canonical_hash="",
                    classification=EscalationMismatchType.POSTURE_MISMATCH,
                    expected_value="",
                    actual_value="",
                ),
            ],
        )
        ids = evidence.affected_request_ids()
        assert ids == ["req-1", "req-2"]


class TestGREGBundle:
    """Tests for GREGBundle serialization."""
    
    def test_bundle_to_json(self) -> None:
        """Bundle serializes to valid JSON."""
        summary = BundleSummary(
            mismatch_count=1,
            collapse_count=0,
            drift_count=0,
            integrity_violation_count=0,
            total_count=1,
            affected_request_count=1,
            affected_hash_count=1,
            severity="low",
        )
        evidence = EscalationEvidence(
            mismatches=[
                MismatchEvidence(
                    request_id="req-1",
                    canonical_hash="hash-1",
                    classification=EscalationMismatchType.PHASE_MISMATCH,
                    expected_value="REF",
                    actual_value="DES",
                ),
            ],
        )
        bundle = GREGBundle(
            bundle_id="greg-test123",
            created_at="2026-03-13T12:00:00Z",
            severity="low",
            summary=summary,
            evidence=evidence,
            affected_request_ids=["req-1"],
            affected_canonical_hashes=["hash-1"],
        )
        
        json_str = bundle.to_json()
        parsed = json.loads(json_str)
        assert parsed["bundle_id"] == "greg-test123"
        assert parsed["severity"] == "low"
        assert len(parsed["evidence"]["mismatches"]) == 1
    
    def test_bundle_round_trip(self) -> None:
        """Bundle serializes and deserializes correctly."""
        summary = BundleSummary(
            mismatch_count=2,
            total_count=2,
            severity="medium",
        )
        evidence = EscalationEvidence()
        bundle = GREGBundle(
            bundle_id="greg-abc123",
            created_at="2026-03-13T12:00:00Z",
            severity="medium",
            summary=summary,
            evidence=evidence,
            runtime_version="0.1.0",
            evaluation_id="eval-xyz",
        )
        
        json_str = bundle.to_json()
        bundle2 = GREGBundle.from_json(json_str)
        assert bundle2.bundle_id == bundle.bundle_id
        assert bundle2.severity == bundle.severity
        assert bundle2.evaluation_id == bundle.evaluation_id
    
    def test_content_hash_deterministic(self) -> None:
        """Content hash is deterministic."""
        summary = BundleSummary(total_count=1, severity="low")
        evidence = EscalationEvidence()
        bundle1 = GREGBundle(
            bundle_id="greg-1",
            created_at="2026-03-13T12:00:00Z",
            severity="low",
            summary=summary,
            evidence=evidence,
        )
        bundle2 = GREGBundle(
            bundle_id="greg-2",  # Different ID
            created_at="2026-03-13T13:00:00Z",  # Different time
            severity="low",
            summary=summary,
            evidence=evidence,
        )
        # Content hash excludes bundle_id and created_at
        assert bundle1.content_hash() == bundle2.content_hash()


# ============================================================================
# BundleBuilder Tests
# ============================================================================


class TestBundleBuilder:
    """Tests for BundleBuilder construction."""
    
    @pytest.fixture
    def builder(self) -> BundleBuilder:
        return BundleBuilder(
            runtime_version="test-0.1.0",
            fixed_time="2026-03-13T12:00:00Z",
        )
    
    def test_empty_inputs_no_escalation(self, builder: BundleBuilder) -> None:
        """Empty inputs produce non-escalation bundle."""
        inputs = BundleInputs()
        bundle, decision = builder.build(inputs)
        
        assert decision.should_escalate is False
        assert bundle.severity == "low"
        assert bundle.summary.total_count == 0
    
    def test_mismatch_inputs_produce_bundle(self, builder: BundleBuilder) -> None:
        """Mismatch inputs produce proper bundle."""
        inputs = BundleInputs(
            mismatches=[
                RawMismatch(
                    request_id="req-1",
                    canonical_hash="hash-1",
                    classification="phase_mismatch",
                    expected_value="REF",
                    actual_value="DES",
                    ledger_refs_raw=[
                        {
                            "event_id": "evt-1",
                            "event_type": "decision_emitted",
                            "request_id": "req-1",
                            "plan_hash": "plan-1",
                            "timestamp_utc": "2026-03-13T11:00:00Z",
                        },
                    ],
                ),
                RawMismatch(
                    request_id="req-2",
                    canonical_hash="hash-2",
                    classification="posture_mismatch",
                    expected_value="refuse",
                    actual_value="safe_execute",
                ),
            ] * 3,  # 6 mismatches total
        )
        bundle, decision = builder.build(inputs)
        
        assert decision.should_escalate is True
        assert bundle.summary.mismatch_count == 6
        assert "req-1" in bundle.affected_request_ids
        assert "hash-1" in bundle.affected_canonical_hashes
        assert len(bundle.evidence.mismatches[0].ledger_refs) == 1
    
    def test_collapse_inputs_produce_bundle(self, builder: BundleBuilder) -> None:
        """Collapse inputs produce proper bundle."""
        inputs = BundleInputs(
            collapses=[
                RawCollapse(
                    request_id="req-1",
                    canonical_hash="hash-1",
                    collapse_type="REF_SOFTENING",
                    description="REF boundary softened to CONF",
                    severity="high",
                ),
            ],
        )
        bundle, decision = builder.build(inputs)
        
        assert decision.should_escalate is True
        assert bundle.summary.collapse_count == 1
        assert bundle.evidence.collapses[0].classification == CollapseClassification.REF_SOFTENING
    
    def test_drift_inputs_produce_bundle(self, builder: BundleBuilder) -> None:
        """Drift inputs produce proper bundle with correct severity."""
        inputs = BundleInputs(
            drifts=[
                RawDrift(
                    request_id="req-1",
                    canonical_hash="hash-1",
                    baseline_value="REF",
                    observed_value="DES",
                    drift_percentage=0.15,  # 15% drift = medium
                    drift_type="phase_drift",
                ),
            ],
        )
        bundle, decision = builder.build(inputs)
        
        assert decision.should_escalate is True
        assert bundle.summary.drift_count == 1
        assert decision.overall_severity == EscalationSeverity.MEDIUM
    
    def test_integrity_violation_critical(self, builder: BundleBuilder) -> None:
        """Integrity violation always produces critical severity."""
        inputs = BundleInputs(
            integrity_violations=[
                RawIntegrityViolation(
                    request_id="req-1",
                    canonical_hash="hash-1",
                    violation_type="canonical_hash_mismatch",
                    description="Execution hash differs from decision hash",
                    expected_hash="abc123",
                    actual_hash="def456",
                ),
            ],
        )
        bundle, decision = builder.build(inputs)
        
        assert decision.should_escalate is True
        assert decision.overall_severity == EscalationSeverity.CRITICAL
        assert bundle.severity == "critical"
        assert bundle.summary.integrity_violation_count == 1
    
    def test_bundle_id_deterministic(self, builder: BundleBuilder) -> None:
        """Same inputs produce same bundle ID."""
        inputs = BundleInputs(
            mismatches=[
                RawMismatch(
                    request_id="req-1",
                    canonical_hash="hash-1",
                    classification="phase_mismatch",
                    expected_value="REF",
                    actual_value="DES",
                ),
            ] * 5,
        )
        bundle1, _ = builder.build(inputs)
        bundle2, _ = builder.build(inputs)
        
        assert bundle1.bundle_id == bundle2.bundle_id
    
    def test_observation_window_preserved(self, builder: BundleBuilder) -> None:
        """Observation window metadata is preserved."""
        inputs = BundleInputs(
            observation_window_start="2026-03-13T00:00:00Z",
            observation_window_end="2026-03-13T12:00:00Z",
            mismatches=[
                RawMismatch(
                    request_id="req-1",
                    classification="phase_mismatch",
                ),
            ] * 5,
        )
        bundle, _ = builder.build(inputs)
        
        assert bundle.observation_window_start == "2026-03-13T00:00:00Z"
        assert bundle.observation_window_end == "2026-03-13T12:00:00Z"
    
    def test_thresholds_snapshot_included(self, builder: BundleBuilder) -> None:
        """Thresholds snapshot is included in bundle."""
        inputs = BundleInputs()
        bundle, _ = builder.build(inputs)
        
        assert "mismatch_count_low" in bundle.thresholds_snapshot
        assert bundle.thresholds_snapshot["mismatch_count_low"] == 5
    
    def test_build_from_decision(self, builder: BundleBuilder) -> None:
        """build_from_decision creates bundle from existing decision."""
        decision = EscalationDecision(
            should_escalate=True,
            overall_severity=EscalationSeverity.HIGH,
            evaluation_timestamp="2026-03-13T12:00:00Z",
        )
        evidence = EscalationEvidence(
            collapses=[
                CollapseEvidence(
                    request_id="req-1",
                    canonical_hash="hash-1",
                    classification=CollapseClassification.CONF_TO_DES,
                    description="CONF treated as DES",
                    severity="high",
                ),
            ],
        )
        bundle = builder.build_from_decision(
            decision,
            evidence,
            observation_window_start="2026-03-13T00:00:00Z",
        )
        
        assert bundle.severity == "high"
        assert bundle.evaluation_id == decision.evaluation_id
        assert bundle.summary.collapse_count == 1
    
    def test_summary_classification_breakdown(self, builder: BundleBuilder) -> None:
        """Summary includes classification breakdown."""
        inputs = BundleInputs(
            mismatches=[
                RawMismatch(request_id="req-1", classification="phase_mismatch"),
                RawMismatch(request_id="req-2", classification="phase_mismatch"),
                RawMismatch(request_id="req-3", classification="posture_mismatch"),
                RawMismatch(request_id="req-4", classification="boundary_mismatch"),
                RawMismatch(request_id="req-5", classification="phase_mismatch"),
            ],
            collapses=[
                RawCollapse(request_id="req-1", collapse_type="REF_SOFTENING"),
                RawCollapse(request_id="req-2", collapse_type="REF_SOFTENING"),
                RawCollapse(request_id="req-3", collapse_type="CONF_TO_DES"),
            ],
        )
        bundle, _ = builder.build(inputs)
        
        assert bundle.summary.mismatch_by_type["phase_mismatch"] == 3
        assert bundle.summary.mismatch_by_type["posture_mismatch"] == 1
        assert bundle.summary.mismatch_by_type["boundary_mismatch"] == 1
        assert bundle.summary.collapse_by_type["REF_SOFTENING"] == 2
        assert bundle.summary.collapse_by_type["CONF_TO_DES"] == 1


class TestBundleInputsConversion:
    """Tests for BundleInputs to ObservationInput conversion."""
    
    def test_to_observation_input_mismatches(self) -> None:
        """Mismatch data converts correctly."""
        inputs = BundleInputs(
            mismatches=[
                RawMismatch(request_id="req-1", canonical_hash="hash-1"),
                RawMismatch(request_id="req-2", canonical_hash="hash-2"),
            ],
        )
        obs = inputs.to_observation_input()
        assert obs.mismatch_count == 2
        assert "req-1" in obs.mismatch_request_ids
        assert "hash-1" in obs.mismatch_canonical_hashes
    
    def test_to_observation_input_drift(self) -> None:
        """Drift data takes max percentage."""
        inputs = BundleInputs(
            drifts=[
                RawDrift(request_id="req-1", drift_percentage=0.05),
                RawDrift(request_id="req-2", drift_percentage=0.15),
                RawDrift(request_id="req-3", drift_percentage=0.10),
            ],
        )
        obs = inputs.to_observation_input()
        assert obs.drift_percentage == 0.15  # max


# ============================================================================
# Integration Tests
# ============================================================================


class TestEscalationIntegration:
    """Integration tests for full escalation flow."""
    
    def test_full_escalation_flow(self) -> None:
        """Full flow from raw inputs to serialized bundle."""
        builder = BundleBuilder(
            runtime_version="test-0.1.0",
            fixed_time="2026-03-13T12:00:00Z",
        )
        
        inputs = BundleInputs(
            mismatches=[
                RawMismatch(
                    request_id=f"req-{i}",
                    canonical_hash=f"hash-{i}",
                    classification="phase_mismatch",
                    expected_value="REF",
                    actual_value="DES",
                    ledger_refs_raw=[
                        {
                            "event_id": f"evt-{i}",
                            "event_type": "plangate_refused",
                            "request_id": f"req-{i}",
                            "plan_hash": f"plan-{i}",
                            "timestamp_utc": f"2026-03-13T11:{i:02d}:00Z",
                        },
                    ],
                )
                for i in range(30)  # 30 mismatches = high severity
            ],
            collapses=[
                RawCollapse(
                    request_id="req-collapse-1",
                    canonical_hash="hash-collapse-1",
                    collapse_type="REF_SOFTENING",
                    description="REF boundary softened",
                    severity="high",
                ),
            ],
            observation_window_start="2026-03-13T00:00:00Z",
            observation_window_end="2026-03-13T12:00:00Z",
        )
        
        bundle, decision = builder.build(inputs)
        
        # Verify decision
        assert decision.should_escalate is True
        assert decision.overall_severity == EscalationSeverity.HIGH
        assert len(decision.triggers) == 2  # mismatch + collapse
        
        # Verify bundle
        assert bundle.severity == "high"
        assert bundle.summary.mismatch_count == 30
        assert bundle.summary.collapse_count == 1
        assert bundle.summary.total_count == 31
        assert len(bundle.affected_request_ids) == 31
        
        # Verify ledger references preserved
        assert len(bundle.evidence.mismatches[0].ledger_refs) == 1
        assert bundle.evidence.mismatches[0].ledger_refs[0].event_type == "plangate_refused"
        
        # Verify serialization
        json_str = bundle.to_json()
        bundle2 = GREGBundle.from_json(json_str)
        assert bundle2.bundle_id == bundle.bundle_id
        assert bundle2.summary.mismatch_count == 30
    
    def test_custom_thresholds_integration(self) -> None:
        """Custom thresholds affect escalation decisions."""
        # Strict thresholds
        strict_thresholds = EscalationThresholds(
            mismatch_count_low=1,
            mismatch_count_critical=5,
        )
        strict_builder = BundleBuilder(
            thresholds=strict_thresholds,
            fixed_time="2026-03-13T12:00:00Z",
        )
        
        # Lenient thresholds
        lenient_thresholds = EscalationThresholds(
            mismatch_count_low=100,
            mismatch_count_critical=500,
        )
        lenient_builder = BundleBuilder(
            thresholds=lenient_thresholds,
            fixed_time="2026-03-13T12:00:00Z",
        )
        
        inputs = BundleInputs(
            mismatches=[
                RawMismatch(request_id=f"req-{i}", classification="phase_mismatch")
                for i in range(10)
            ],
        )
        
        strict_bundle, strict_decision = strict_builder.build(inputs)
        lenient_bundle, lenient_decision = lenient_builder.build(inputs)
        
        # Strict thresholds: 10 mismatches = critical
        assert strict_decision.should_escalate is True
        assert strict_decision.overall_severity == EscalationSeverity.CRITICAL
        
        # Lenient thresholds: 10 mismatches = no escalation
        assert lenient_decision.should_escalate is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

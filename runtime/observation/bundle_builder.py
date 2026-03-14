"""
Bundle Builder — M4.5 evidence bundle construction.

Builds GREG escalation bundles from observation inputs, ledger references,
and escalation decisions. Deterministic construction with complete evidence
chain preservation.

Invariants:
- Deterministic: same inputs → same bundle (except timestamp if not fixed)
- No external calls
- No modification of runtime decisions
- Complete ledger reference chain
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from runtime.observation.greg_escalation import (
    EscalationDecision,
    EscalationPolicy,
    EscalationSeverity,
    EscalationThresholds,
    EscalationType,
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


@dataclass
class RawMismatch:
    """Raw mismatch input for bundle building."""
    
    request_id: str
    canonical_hash: str = ""
    classification: str = "phase_mismatch"
    expected_value: str = ""
    actual_value: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    ledger_event_ids: list[str] = field(default_factory=list)
    ledger_refs_raw: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RawCollapse:
    """Raw collapse vector input for bundle building."""
    
    request_id: str
    canonical_hash: str = ""
    collapse_type: str = "UNCLASSIFIED"
    description: str = ""
    severity: str = "low"
    context: dict[str, Any] = field(default_factory=dict)
    ledger_event_ids: list[str] = field(default_factory=list)
    ledger_refs_raw: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RawDrift:
    """Raw drift evidence input for bundle building."""
    
    request_id: str
    canonical_hash: str = ""
    baseline_value: str = ""
    observed_value: str = ""
    drift_percentage: float = 0.0
    drift_type: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    ledger_event_ids: list[str] = field(default_factory=list)
    ledger_refs_raw: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RawIntegrityViolation:
    """Raw integrity violation input for bundle building."""
    
    request_id: str
    canonical_hash: str = ""
    violation_type: str = ""
    description: str = ""
    expected_hash: str = ""
    actual_hash: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    ledger_event_ids: list[str] = field(default_factory=list)
    ledger_refs_raw: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class BundleInputs:
    """Aggregated inputs for bundle construction."""
    
    mismatches: list[RawMismatch] = field(default_factory=list)
    collapses: list[RawCollapse] = field(default_factory=list)
    drifts: list[RawDrift] = field(default_factory=list)
    integrity_violations: list[RawIntegrityViolation] = field(default_factory=list)
    
    # Metadata
    observation_window_start: str = ""
    observation_window_end: str = ""
    runtime_version: str = ""
    
    def to_observation_input(self) -> ObservationInput:
        """Convert to ObservationInput for policy evaluation."""
        mismatch_ids = [m.request_id for m in self.mismatches if m.request_id]
        mismatch_hashes = [m.canonical_hash for m in self.mismatches if m.canonical_hash]
        
        # Convert collapse vectors to dict format
        collapse_vectors = []
        for c in self.collapses:
            collapse_vectors.append({
                "request_id": c.request_id,
                "canonical_hash": c.canonical_hash,
                "collapse_type": c.collapse_type,
            })
        
        # Calculate drift percentage as max drift observed
        drift_percentage = 0.0
        drift_ids = []
        drift_hashes = []
        for d in self.drifts:
            if d.drift_percentage > drift_percentage:
                drift_percentage = d.drift_percentage
            if d.request_id:
                drift_ids.append(d.request_id)
            if d.canonical_hash:
                drift_hashes.append(d.canonical_hash)
        
        # Convert integrity violations
        integrity_list = []
        for iv in self.integrity_violations:
            integrity_list.append({
                "request_id": iv.request_id,
                "canonical_hash": iv.canonical_hash,
                "violation_type": iv.violation_type,
            })
        
        return ObservationInput(
            mismatch_count=len(self.mismatches),
            mismatch_request_ids=mismatch_ids,
            mismatch_canonical_hashes=mismatch_hashes,
            collapse_vectors=collapse_vectors,
            drift_percentage=drift_percentage,
            drift_request_ids=drift_ids,
            drift_canonical_hashes=drift_hashes,
            integrity_violations=integrity_list,
        )


class BundleBuilder:
    """
    Builds GREG escalation bundles from observation data.
    
    Deterministic construction with complete evidence chain. Uses
    EscalationPolicy for severity determination.
    """
    
    def __init__(
        self,
        *,
        thresholds: EscalationThresholds | None = None,
        runtime_version: str = "0.1.0",
        fixed_time: str | None = None,
    ):
        """
        Initialize bundle builder.
        
        Args:
            thresholds: Custom escalation thresholds
            runtime_version: Runtime version for bundle metadata
            fixed_time: Fixed timestamp for deterministic tests
        """
        self.thresholds = thresholds or EscalationThresholds()
        self.runtime_version = runtime_version
        self.fixed_time = fixed_time
        self.policy = EscalationPolicy(thresholds=self.thresholds, fixed_time=fixed_time)
    
    def _timestamp(self) -> str:
        """Get current timestamp or fixed time for tests."""
        return self.fixed_time or datetime.now(timezone.utc).isoformat()
    
    def _compute_bundle_id(self, content: dict[str, Any]) -> str:
        """Compute deterministic bundle ID from content."""
        content_bytes = json.dumps(content, sort_keys=True, ensure_ascii=False).encode("utf-8")
        hash_hex = hashlib.sha256(content_bytes).hexdigest()
        return f"greg-{hash_hex[:24]}"
    
    def _raw_to_ledger_ref(self, raw: dict[str, Any]) -> LedgerReference:
        """Convert raw ledger reference dict to LedgerReference."""
        return LedgerReference(
            event_id=raw.get("event_id", ""),
            event_type=raw.get("event_type", ""),
            request_id=raw.get("request_id", ""),
            plan_hash=raw.get("plan_hash", ""),
            timestamp_utc=raw.get("timestamp_utc", ""),
            canonical_hash=raw.get("canonical_hash", ""),
        )
    
    def _classification_to_enum(self, cls_str: str) -> EscalationMismatchType:
        """Convert classification string to enum."""
        try:
            return EscalationMismatchType(cls_str)
        except ValueError:
            return EscalationMismatchType.PHASE_MISMATCH
    
    def _collapse_to_enum(self, cls_str: str) -> CollapseClassification:
        """Convert collapse type string to enum."""
        try:
            return CollapseClassification(cls_str)
        except ValueError:
            return CollapseClassification.UNCLASSIFIED
    
    def _build_mismatch_evidence(self, raw: RawMismatch) -> MismatchEvidence:
        """Build MismatchEvidence from raw input."""
        ledger_refs = [self._raw_to_ledger_ref(r) for r in raw.ledger_refs_raw]
        return MismatchEvidence(
            request_id=raw.request_id,
            canonical_hash=raw.canonical_hash,
            classification=self._classification_to_enum(raw.classification),
            expected_value=raw.expected_value,
            actual_value=raw.actual_value,
            context=raw.context,
            ledger_refs=ledger_refs,
        )
    
    def _build_collapse_evidence(self, raw: RawCollapse) -> CollapseEvidence:
        """Build CollapseEvidence from raw input."""
        ledger_refs = [self._raw_to_ledger_ref(r) for r in raw.ledger_refs_raw]
        return CollapseEvidence(
            request_id=raw.request_id,
            canonical_hash=raw.canonical_hash,
            classification=self._collapse_to_enum(raw.collapse_type),
            description=raw.description,
            severity=raw.severity,
            context=raw.context,
            ledger_refs=ledger_refs,
        )
    
    def _build_drift_evidence(self, raw: RawDrift) -> DriftEvidence:
        """Build DriftEvidence from raw input."""
        ledger_refs = [self._raw_to_ledger_ref(r) for r in raw.ledger_refs_raw]
        return DriftEvidence(
            request_id=raw.request_id,
            canonical_hash=raw.canonical_hash,
            baseline_value=raw.baseline_value,
            observed_value=raw.observed_value,
            drift_percentage=raw.drift_percentage,
            drift_type=raw.drift_type,
            context=raw.context,
            ledger_refs=ledger_refs,
        )
    
    def _build_integrity_evidence(self, raw: RawIntegrityViolation) -> IntegrityEvidence:
        """Build IntegrityEvidence from raw input."""
        ledger_refs = [self._raw_to_ledger_ref(r) for r in raw.ledger_refs_raw]
        return IntegrityEvidence(
            request_id=raw.request_id,
            canonical_hash=raw.canonical_hash,
            violation_type=raw.violation_type,
            description=raw.description,
            expected_hash=raw.expected_hash,
            actual_hash=raw.actual_hash,
            context=raw.context,
            ledger_refs=ledger_refs,
        )
    
    def _build_summary(
        self,
        evidence: EscalationEvidence,
        severity: str,
    ) -> BundleSummary:
        """Build summary statistics from evidence."""
        # Mismatch breakdown by type
        mismatch_by_type: dict[str, int] = {}
        for m in evidence.mismatches:
            key = m.classification.value
            mismatch_by_type[key] = mismatch_by_type.get(key, 0) + 1
        
        # Collapse breakdown by type
        collapse_by_type: dict[str, int] = {}
        for c in evidence.collapses:
            key = c.classification.value
            collapse_by_type[key] = collapse_by_type.get(key, 0) + 1
        
        return BundleSummary(
            mismatch_count=len(evidence.mismatches),
            collapse_count=len(evidence.collapses),
            drift_count=len(evidence.drifts),
            integrity_violation_count=len(evidence.integrity_violations),
            total_count=evidence.total_count(),
            affected_request_count=len(evidence.affected_request_ids()),
            affected_hash_count=len(evidence.affected_canonical_hashes()),
            severity=severity,
            mismatch_by_type=mismatch_by_type,
            collapse_by_type=collapse_by_type,
        )
    
    def build(self, inputs: BundleInputs) -> tuple[GREGBundle, EscalationDecision]:
        """
        Build a GREG bundle from inputs.
        
        Args:
            inputs: Bundle inputs with raw evidence data
            
        Returns:
            Tuple of (GREGBundle, EscalationDecision)
        """
        # Evaluate escalation policy
        obs_input = inputs.to_observation_input()
        decision = self.policy.evaluate(obs_input)
        
        # Build evidence structures
        mismatches = [self._build_mismatch_evidence(m) for m in inputs.mismatches]
        collapses = [self._build_collapse_evidence(c) for c in inputs.collapses]
        drifts = [self._build_drift_evidence(d) for d in inputs.drifts]
        integrity_violations = [self._build_integrity_evidence(iv) for iv in inputs.integrity_violations]
        
        evidence = EscalationEvidence(
            mismatches=mismatches,
            collapses=collapses,
            drifts=drifts,
            integrity_violations=integrity_violations,
        )
        
        # Build summary
        severity = decision.overall_severity.value
        summary = self._build_summary(evidence, severity)
        
        # Compute affected IDs
        affected_request_ids = evidence.affected_request_ids()
        affected_canonical_hashes = evidence.affected_canonical_hashes()
        
        # Compute bundle ID from content
        created_at = self._timestamp()
        content_for_id = {
            "created_at": created_at,
            "severity": severity,
            "affected_request_ids": affected_request_ids,
            "affected_canonical_hashes": affected_canonical_hashes,
            "evidence_hash": hashlib.sha256(
                json.dumps(evidence.to_dict(), sort_keys=True).encode()
            ).hexdigest()[:16],
        }
        bundle_id = self._compute_bundle_id(content_for_id)
        
        bundle = GREGBundle(
            bundle_id=bundle_id,
            created_at=created_at,
            severity=severity,
            summary=summary,
            evidence=evidence,
            runtime_version=self.runtime_version,
            evaluation_id=decision.evaluation_id,
            observation_window_start=inputs.observation_window_start,
            observation_window_end=inputs.observation_window_end,
            thresholds_snapshot=self.thresholds.to_dict(),
            affected_request_ids=affected_request_ids,
            affected_canonical_hashes=affected_canonical_hashes,
        )
        
        return bundle, decision
    
    def build_from_decision(
        self,
        decision: EscalationDecision,
        evidence: EscalationEvidence,
        *,
        observation_window_start: str = "",
        observation_window_end: str = "",
    ) -> GREGBundle:
        """
        Build a GREG bundle from an existing escalation decision and evidence.
        
        Use when evidence is already structured.
        
        Args:
            decision: Existing escalation decision
            evidence: Structured evidence
            observation_window_start: Window start timestamp
            observation_window_end: Window end timestamp
            
        Returns:
            GREGBundle
        """
        severity = decision.overall_severity.value
        summary = self._build_summary(evidence, severity)
        
        affected_request_ids = evidence.affected_request_ids()
        affected_canonical_hashes = evidence.affected_canonical_hashes()
        
        created_at = self._timestamp()
        content_for_id = {
            "created_at": created_at,
            "severity": severity,
            "evaluation_id": decision.evaluation_id,
            "affected_request_ids": affected_request_ids,
        }
        bundle_id = self._compute_bundle_id(content_for_id)
        
        return GREGBundle(
            bundle_id=bundle_id,
            created_at=created_at,
            severity=severity,
            summary=summary,
            evidence=evidence,
            runtime_version=self.runtime_version,
            evaluation_id=decision.evaluation_id,
            observation_window_start=observation_window_start,
            observation_window_end=observation_window_end,
            thresholds_snapshot=self.thresholds.to_dict(),
            affected_request_ids=affected_request_ids,
            affected_canonical_hashes=affected_canonical_hashes,
        )

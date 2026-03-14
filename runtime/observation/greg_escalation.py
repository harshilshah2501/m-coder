"""
GREG Escalation Policy — M4.5 escalation decision logic.

Deterministic policy evaluation for governance escalation. Turns drift signals,
mismatch counts, and collapse evidence into escalation decisions. No external
calls, no modification of runtime decisions — evidence packaging only.

Invariants:
- Deterministic: same inputs → same decision
- No external calls
- No modification of runtime decisions
- Builds evidence packages only
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EscalationType(str, Enum):
    """Types of escalation triggers."""
    
    MISMATCH_THRESHOLD = "mismatch_threshold"
    COLLAPSE_VECTOR = "collapse_vector"
    DRIFT_BREACH = "drift_breach"
    INTEGRITY_VIOLATION = "integrity_violation"
    BOUNDARY_ANOMALY = "boundary_anomaly"
    AUTHORITY_FAILURE_SPIKE = "authority_failure_spike"


class EscalationSeverity(str, Enum):
    """Severity levels for escalations."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CollapseType(str, Enum):
    """Collapse vector types from Layer-1 doctrine."""
    
    REF_SOFTENING = "REF_SOFTENING"
    CONF_TO_DES = "CONF_TO_DES"
    BOUNDARY_RELOCATION = "BOUNDARY_RELOCATION"
    AUTHORITY_EROSION = "AUTHORITY_EROSION"
    PHASE_DRIFT = "PHASE_DRIFT"
    POSTURE_INFLATION = "POSTURE_INFLATION"


@dataclass(frozen=True)
class EscalationThresholds:
    """
    Configurable thresholds for escalation triggers.
    
    All thresholds are inclusive (>=) except where noted.
    """
    
    # Mismatch thresholds
    mismatch_count_low: int = 5
    mismatch_count_medium: int = 15
    mismatch_count_high: int = 30
    mismatch_count_critical: int = 50
    
    # Collapse vector thresholds
    collapse_count_low: int = 1
    collapse_count_medium: int = 3
    collapse_count_high: int = 5
    collapse_count_critical: int = 10
    
    # Drift percentage thresholds (0.0 to 1.0)
    drift_percentage_low: float = 0.05
    drift_percentage_medium: float = 0.10
    drift_percentage_high: float = 0.20
    drift_percentage_critical: float = 0.35
    
    # Authority failure thresholds
    authority_failure_count_low: int = 3
    authority_failure_count_medium: int = 10
    authority_failure_count_high: int = 20
    authority_failure_count_critical: int = 40
    
    # Boundary anomaly thresholds
    boundary_anomaly_count_low: int = 1
    boundary_anomaly_count_medium: int = 3
    boundary_anomaly_count_high: int = 5
    boundary_anomaly_count_critical: int = 10
    
    # Integrity violation always critical
    integrity_violation_immediate: bool = True
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "mismatch_count_low": self.mismatch_count_low,
            "mismatch_count_medium": self.mismatch_count_medium,
            "mismatch_count_high": self.mismatch_count_high,
            "mismatch_count_critical": self.mismatch_count_critical,
            "collapse_count_low": self.collapse_count_low,
            "collapse_count_medium": self.collapse_count_medium,
            "collapse_count_high": self.collapse_count_high,
            "collapse_count_critical": self.collapse_count_critical,
            "drift_percentage_low": self.drift_percentage_low,
            "drift_percentage_medium": self.drift_percentage_medium,
            "drift_percentage_high": self.drift_percentage_high,
            "drift_percentage_critical": self.drift_percentage_critical,
            "authority_failure_count_low": self.authority_failure_count_low,
            "authority_failure_count_medium": self.authority_failure_count_medium,
            "authority_failure_count_high": self.authority_failure_count_high,
            "authority_failure_count_critical": self.authority_failure_count_critical,
            "boundary_anomaly_count_low": self.boundary_anomaly_count_low,
            "boundary_anomaly_count_medium": self.boundary_anomaly_count_medium,
            "boundary_anomaly_count_high": self.boundary_anomaly_count_high,
            "boundary_anomaly_count_critical": self.boundary_anomaly_count_critical,
            "integrity_violation_immediate": self.integrity_violation_immediate,
        }


@dataclass
class EscalationTrigger:
    """A single trigger that contributed to escalation."""
    
    escalation_type: EscalationType
    severity: EscalationSeverity
    count: int
    threshold_breached: int | float
    affected_request_ids: list[str] = field(default_factory=list)
    affected_canonical_hashes: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "escalation_type": self.escalation_type.value,
            "severity": self.severity.value,
            "count": self.count,
            "threshold_breached": self.threshold_breached,
            "affected_request_ids": self.affected_request_ids,
            "affected_canonical_hashes": self.affected_canonical_hashes,
            "details": self.details,
        }


@dataclass
class EscalationDecision:
    """
    Result of escalation policy evaluation.
    
    Includes all triggers, maximum severity, and whether escalation is required.
    """
    
    should_escalate: bool
    overall_severity: EscalationSeverity
    triggers: list[EscalationTrigger] = field(default_factory=list)
    evaluation_timestamp: str = ""
    evaluation_id: str = ""
    thresholds_used: EscalationThresholds | None = None
    
    def __post_init__(self) -> None:
        if not self.evaluation_timestamp:
            self.evaluation_timestamp = datetime.now(timezone.utc).isoformat()
        if not self.evaluation_id:
            self.evaluation_id = self._compute_evaluation_id()
    
    def _compute_evaluation_id(self) -> str:
        """Deterministic ID from evaluation content."""
        content = json.dumps({
            "timestamp": self.evaluation_timestamp,
            "should_escalate": self.should_escalate,
            "severity": self.overall_severity.value,
            "trigger_count": len(self.triggers),
        }, sort_keys=True)
        return f"eval-{hashlib.sha256(content.encode()).hexdigest()[:24]}"
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "should_escalate": self.should_escalate,
            "overall_severity": self.overall_severity.value,
            "triggers": [t.to_dict() for t in self.triggers],
            "evaluation_timestamp": self.evaluation_timestamp,
            "evaluation_id": self.evaluation_id,
            "thresholds_used": self.thresholds_used.to_dict() if self.thresholds_used else None,
        }


@dataclass
class ObservationInput:
    """Input data for escalation policy evaluation."""
    
    # Mismatch counts
    mismatch_count: int = 0
    mismatch_request_ids: list[str] = field(default_factory=list)
    mismatch_canonical_hashes: list[str] = field(default_factory=list)
    
    # Collapse vectors
    collapse_vectors: list[dict[str, Any]] = field(default_factory=list)
    
    # Drift metrics
    drift_percentage: float = 0.0
    drift_request_ids: list[str] = field(default_factory=list)
    drift_canonical_hashes: list[str] = field(default_factory=list)
    
    # Authority failures
    authority_failure_count: int = 0
    authority_failure_request_ids: list[str] = field(default_factory=list)
    
    # Boundary anomalies
    boundary_anomaly_count: int = 0
    boundary_anomaly_request_ids: list[str] = field(default_factory=list)
    
    # Integrity violations
    integrity_violations: list[dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "mismatch_count": self.mismatch_count,
            "mismatch_request_ids": self.mismatch_request_ids,
            "mismatch_canonical_hashes": self.mismatch_canonical_hashes,
            "collapse_vectors": self.collapse_vectors,
            "drift_percentage": self.drift_percentage,
            "drift_request_ids": self.drift_request_ids,
            "drift_canonical_hashes": self.drift_canonical_hashes,
            "authority_failure_count": self.authority_failure_count,
            "authority_failure_request_ids": self.authority_failure_request_ids,
            "boundary_anomaly_count": self.boundary_anomaly_count,
            "boundary_anomaly_request_ids": self.boundary_anomaly_request_ids,
            "integrity_violations": self.integrity_violations,
        }


class EscalationPolicy:
    """
    Deterministic escalation policy evaluator.
    
    Evaluates observation inputs against thresholds and produces escalation
    decisions. No external calls, no side effects, deterministic behavior.
    """
    
    def __init__(
        self,
        thresholds: EscalationThresholds | None = None,
        *,
        fixed_time: str | None = None,
    ):
        """
        Initialize policy with thresholds.
        
        Args:
            thresholds: Custom thresholds or default
            fixed_time: Fixed timestamp for deterministic tests
        """
        self.thresholds = thresholds or EscalationThresholds()
        self.fixed_time = fixed_time
    
    def _timestamp(self) -> str:
        """Get current timestamp or fixed time for tests."""
        return self.fixed_time or datetime.now(timezone.utc).isoformat()
    
    def _severity_from_count(
        self,
        count: int,
        low: int,
        medium: int,
        high: int,
        critical: int,
    ) -> tuple[EscalationSeverity, int] | None:
        """
        Determine severity and threshold from count.
        
        Returns (severity, threshold_breached) or None if below all thresholds.
        """
        if count >= critical:
            return (EscalationSeverity.CRITICAL, critical)
        if count >= high:
            return (EscalationSeverity.HIGH, high)
        if count >= medium:
            return (EscalationSeverity.MEDIUM, medium)
        if count >= low:
            return (EscalationSeverity.LOW, low)
        return None
    
    def _severity_from_percentage(
        self,
        percentage: float,
        low: float,
        medium: float,
        high: float,
        critical: float,
    ) -> tuple[EscalationSeverity, float] | None:
        """
        Determine severity and threshold from percentage.
        
        Returns (severity, threshold_breached) or None if below all thresholds.
        """
        if percentage >= critical:
            return (EscalationSeverity.CRITICAL, critical)
        if percentage >= high:
            return (EscalationSeverity.HIGH, high)
        if percentage >= medium:
            return (EscalationSeverity.MEDIUM, medium)
        if percentage >= low:
            return (EscalationSeverity.LOW, low)
        return None
    
    def _evaluate_mismatches(self, obs: ObservationInput) -> EscalationTrigger | None:
        """Evaluate mismatch count against thresholds."""
        result = self._severity_from_count(
            obs.mismatch_count,
            self.thresholds.mismatch_count_low,
            self.thresholds.mismatch_count_medium,
            self.thresholds.mismatch_count_high,
            self.thresholds.mismatch_count_critical,
        )
        if result is None:
            return None
        severity, threshold = result
        return EscalationTrigger(
            escalation_type=EscalationType.MISMATCH_THRESHOLD,
            severity=severity,
            count=obs.mismatch_count,
            threshold_breached=threshold,
            affected_request_ids=obs.mismatch_request_ids[:50],
            affected_canonical_hashes=obs.mismatch_canonical_hashes[:50],
            details={"mismatch_count": obs.mismatch_count},
        )
    
    def _evaluate_collapse_vectors(self, obs: ObservationInput) -> EscalationTrigger | None:
        """Evaluate collapse vector count against thresholds."""
        count = len(obs.collapse_vectors)
        result = self._severity_from_count(
            count,
            self.thresholds.collapse_count_low,
            self.thresholds.collapse_count_medium,
            self.thresholds.collapse_count_high,
            self.thresholds.collapse_count_critical,
        )
        if result is None:
            return None
        severity, threshold = result
        
        affected_ids = []
        affected_hashes = []
        collapse_types = []
        for cv in obs.collapse_vectors:
            if "request_id" in cv:
                affected_ids.append(cv["request_id"])
            if "canonical_hash" in cv:
                affected_hashes.append(cv["canonical_hash"])
            if "collapse_type" in cv:
                collapse_types.append(cv["collapse_type"])
        
        return EscalationTrigger(
            escalation_type=EscalationType.COLLAPSE_VECTOR,
            severity=severity,
            count=count,
            threshold_breached=threshold,
            affected_request_ids=affected_ids[:50],
            affected_canonical_hashes=affected_hashes[:50],
            details={
                "collapse_count": count,
                "collapse_types": list(set(collapse_types)),
            },
        )
    
    def _evaluate_drift(self, obs: ObservationInput) -> EscalationTrigger | None:
        """Evaluate drift percentage against thresholds."""
        result = self._severity_from_percentage(
            obs.drift_percentage,
            self.thresholds.drift_percentage_low,
            self.thresholds.drift_percentage_medium,
            self.thresholds.drift_percentage_high,
            self.thresholds.drift_percentage_critical,
        )
        if result is None:
            return None
        severity, threshold = result
        return EscalationTrigger(
            escalation_type=EscalationType.DRIFT_BREACH,
            severity=severity,
            count=len(obs.drift_request_ids),
            threshold_breached=threshold,
            affected_request_ids=obs.drift_request_ids[:50],
            affected_canonical_hashes=obs.drift_canonical_hashes[:50],
            details={"drift_percentage": obs.drift_percentage},
        )
    
    def _evaluate_authority_failures(self, obs: ObservationInput) -> EscalationTrigger | None:
        """Evaluate authority failure count against thresholds."""
        result = self._severity_from_count(
            obs.authority_failure_count,
            self.thresholds.authority_failure_count_low,
            self.thresholds.authority_failure_count_medium,
            self.thresholds.authority_failure_count_high,
            self.thresholds.authority_failure_count_critical,
        )
        if result is None:
            return None
        severity, threshold = result
        return EscalationTrigger(
            escalation_type=EscalationType.AUTHORITY_FAILURE_SPIKE,
            severity=severity,
            count=obs.authority_failure_count,
            threshold_breached=threshold,
            affected_request_ids=obs.authority_failure_request_ids[:50],
            affected_canonical_hashes=[],
            details={"authority_failure_count": obs.authority_failure_count},
        )
    
    def _evaluate_boundary_anomalies(self, obs: ObservationInput) -> EscalationTrigger | None:
        """Evaluate boundary anomaly count against thresholds."""
        result = self._severity_from_count(
            obs.boundary_anomaly_count,
            self.thresholds.boundary_anomaly_count_low,
            self.thresholds.boundary_anomaly_count_medium,
            self.thresholds.boundary_anomaly_count_high,
            self.thresholds.boundary_anomaly_count_critical,
        )
        if result is None:
            return None
        severity, threshold = result
        return EscalationTrigger(
            escalation_type=EscalationType.BOUNDARY_ANOMALY,
            severity=severity,
            count=obs.boundary_anomaly_count,
            threshold_breached=threshold,
            affected_request_ids=obs.boundary_anomaly_request_ids[:50],
            affected_canonical_hashes=[],
            details={"boundary_anomaly_count": obs.boundary_anomaly_count},
        )
    
    def _evaluate_integrity_violations(self, obs: ObservationInput) -> EscalationTrigger | None:
        """Evaluate integrity violations — always critical if present."""
        if not obs.integrity_violations:
            return None
        
        affected_ids = []
        affected_hashes = []
        violation_types = []
        for iv in obs.integrity_violations:
            if "request_id" in iv:
                affected_ids.append(iv["request_id"])
            if "canonical_hash" in iv:
                affected_hashes.append(iv["canonical_hash"])
            if "violation_type" in iv:
                violation_types.append(iv["violation_type"])
        
        return EscalationTrigger(
            escalation_type=EscalationType.INTEGRITY_VIOLATION,
            severity=EscalationSeverity.CRITICAL,
            count=len(obs.integrity_violations),
            threshold_breached=1,
            affected_request_ids=affected_ids[:50],
            affected_canonical_hashes=affected_hashes[:50],
            details={
                "violation_count": len(obs.integrity_violations),
                "violation_types": list(set(violation_types)),
            },
        )
    
    def evaluate(self, observation: ObservationInput) -> EscalationDecision:
        """
        Evaluate observation input against escalation policy.
        
        Deterministic: same observation → same decision (modulo timestamp if not fixed).
        
        Args:
            observation: Observation data to evaluate
            
        Returns:
            EscalationDecision with triggers and severity
        """
        triggers: list[EscalationTrigger] = []
        
        # Evaluate each category
        mismatch_trigger = self._evaluate_mismatches(observation)
        if mismatch_trigger:
            triggers.append(mismatch_trigger)
        
        collapse_trigger = self._evaluate_collapse_vectors(observation)
        if collapse_trigger:
            triggers.append(collapse_trigger)
        
        drift_trigger = self._evaluate_drift(observation)
        if drift_trigger:
            triggers.append(drift_trigger)
        
        authority_trigger = self._evaluate_authority_failures(observation)
        if authority_trigger:
            triggers.append(authority_trigger)
        
        boundary_trigger = self._evaluate_boundary_anomalies(observation)
        if boundary_trigger:
            triggers.append(boundary_trigger)
        
        integrity_trigger = self._evaluate_integrity_violations(observation)
        if integrity_trigger:
            triggers.append(integrity_trigger)
        
        # Determine overall severity (max of all triggers)
        if not triggers:
            overall_severity = EscalationSeverity.LOW
            should_escalate = False
        else:
            severity_order = [
                EscalationSeverity.LOW,
                EscalationSeverity.MEDIUM,
                EscalationSeverity.HIGH,
                EscalationSeverity.CRITICAL,
            ]
            max_severity_idx = max(
                severity_order.index(t.severity) for t in triggers
            )
            overall_severity = severity_order[max_severity_idx]
            should_escalate = True
        
        return EscalationDecision(
            should_escalate=should_escalate,
            overall_severity=overall_severity,
            triggers=triggers,
            evaluation_timestamp=self._timestamp(),
            thresholds_used=self.thresholds,
        )

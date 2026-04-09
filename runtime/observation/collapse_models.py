"""
Collapse Event Models — M4.3 data structures for collapse vector tracking.

Defines collapse classes, events, evidence, and summaries. All models are
immutable after creation and support deterministic serialization.

Collapse classes (from M4.3 spec):
- identity_propagation_missing: canonical_hash absent where required
- decision_execution_mismatch: decision posture vs execution outcome conflict
- replay_mismatch: replayed execution differs from original
- missing_trace_linkage: trace lacks required join keys
- unexpected_refusal_distribution_drift: refusal rate exceeds baseline threshold
- missing_evidence_join: plan/decision/execution cannot be linked
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class CollapseClass(str, Enum):
    """
    Collapse vector classification.
    
    Each class represents a distinct governance/runtime integrity failure mode.
    """
    
    IDENTITY_PROPAGATION_MISSING = "identity_propagation_missing"
    DECISION_EXECUTION_MISMATCH = "decision_execution_mismatch"
    REPLAY_MISMATCH = "replay_mismatch"
    MISSING_TRACE_LINKAGE = "missing_trace_linkage"
    UNEXPECTED_REFUSAL_DISTRIBUTION_DRIFT = "unexpected_refusal_distribution_drift"
    MISSING_EVIDENCE_JOIN = "missing_evidence_join"


class CollapseSeverity(str, Enum):
    """
    Severity level for collapse events.
    
    - CRITICAL: Governance invariant violated; requires immediate attention
    - HIGH: Significant integrity concern; may indicate bypass risk
    - MEDIUM: Notable anomaly; warrants investigation
    - LOW: Minor deviation; informational
    """
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Severity mapping per collapse class (default)
_DEFAULT_SEVERITY: dict[CollapseClass, CollapseSeverity] = {
    CollapseClass.IDENTITY_PROPAGATION_MISSING: CollapseSeverity.HIGH,
    CollapseClass.DECISION_EXECUTION_MISMATCH: CollapseSeverity.CRITICAL,
    CollapseClass.REPLAY_MISMATCH: CollapseSeverity.HIGH,
    CollapseClass.MISSING_TRACE_LINKAGE: CollapseSeverity.MEDIUM,
    CollapseClass.UNEXPECTED_REFUSAL_DISTRIBUTION_DRIFT: CollapseSeverity.MEDIUM,
    CollapseClass.MISSING_EVIDENCE_JOIN: CollapseSeverity.HIGH,
}


def _canonical_json(obj: Any) -> bytes:
    """Stable JSON serialization: sorted keys, UTF-8."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _derive_hash(content: bytes) -> str:
    """SHA-256 hash of content, hex-encoded."""
    return hashlib.sha256(content).hexdigest()


def _utc_now() -> str:
    """Current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class CollapseEvidence:
    """
    Evidence supporting a collapse event detection.
    
    Contains the specific runtime artifacts that triggered the classification.
    Immutable after creation.
    """
    
    evidence_type: str
    source_artifact: str
    field_path: str
    expected_value: str | None
    actual_value: str | None
    context: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "evidence_type": self.evidence_type,
            "source_artifact": self.source_artifact,
            "field_path": self.field_path,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "context": dict(self.context),
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CollapseEvidence":
        """Reconstruct from dictionary."""
        ctx = d.get("context", {})
        return cls(
            evidence_type=d["evidence_type"],
            source_artifact=d["source_artifact"],
            field_path=d["field_path"],
            expected_value=d.get("expected_value"),
            actual_value=d.get("actual_value"),
            context=tuple(sorted(ctx.items())) if isinstance(ctx, dict) else ctx,
        )


@dataclass(frozen=True)
class CollapseEvent:
    """
    A detected collapse vector event.
    
    Represents a single instance of a collapse class detected from runtime
    evidence. Immutable after creation; event_id is deterministically derived.
    """
    
    event_id: str
    timestamp_utc: str
    collapse_class: CollapseClass
    severity: CollapseSeverity
    request_id: str
    plan_hash: str
    description: str
    evidence: tuple[CollapseEvidence, ...]
    canonical_hash: str | None = None
    session_id: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization/ledger."""
        return {
            "schema_version": "collapse_event.v0.1",
            "event_id": self.event_id,
            "timestamp_utc": self.timestamp_utc,
            "collapse_class": self.collapse_class.value,
            "severity": self.severity.value,
            "request_id": self.request_id,
            "plan_hash": self.plan_hash,
            "canonical_hash": self.canonical_hash,
            "session_id": self.session_id,
            "description": self.description,
            "evidence": [e.to_dict() for e in self.evidence],
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CollapseEvent":
        """Reconstruct from dictionary."""
        evidence = tuple(
            CollapseEvidence.from_dict(e) for e in d.get("evidence", [])
        )
        return cls(
            event_id=d["event_id"],
            timestamp_utc=d["timestamp_utc"],
            collapse_class=CollapseClass(d["collapse_class"]),
            severity=CollapseSeverity(d["severity"]),
            request_id=d["request_id"],
            plan_hash=d["plan_hash"],
            canonical_hash=d.get("canonical_hash"),
            session_id=d.get("session_id", ""),
            description=d["description"],
            evidence=evidence,
        )
    
    def validate(self) -> list[str]:
        """
        Validate event structure.
        
        Returns list of validation errors, empty if valid.
        """
        errors: list[str] = []
        if not self.event_id:
            errors.append("event_id required")
        if not self.timestamp_utc:
            errors.append("timestamp_utc required")
        if not self.request_id and not self.plan_hash:
            errors.append("request_id or plan_hash required for linkage")
        if not self.evidence:
            errors.append("at least one evidence item required")
        return errors


def create_collapse_event(
    collapse_class: CollapseClass,
    request_id: str,
    plan_hash: str,
    description: str,
    evidence: list[CollapseEvidence],
    canonical_hash: str | None = None,
    session_id: str = "",
    severity: CollapseSeverity | None = None,
    timestamp_utc: str | None = None,
) -> CollapseEvent:
    """
    Factory function to create a CollapseEvent with deterministic event_id.
    
    Event ID is derived from (collapse_class, request_id, plan_hash, evidence_hash)
    so that the same collapse detected twice yields the same event_id.
    """
    ts = timestamp_utc or _utc_now()
    sev = severity or _DEFAULT_SEVERITY.get(collapse_class, CollapseSeverity.MEDIUM)
    
    evidence_tuple = tuple(evidence)
    evidence_data = [e.to_dict() for e in evidence_tuple]
    
    id_content = {
        "collapse_class": collapse_class.value,
        "request_id": request_id,
        "plan_hash": plan_hash,
        "evidence": evidence_data,
    }
    event_id = f"collapse-{_derive_hash(_canonical_json(id_content))[:24]}"
    
    return CollapseEvent(
        event_id=event_id,
        timestamp_utc=ts,
        collapse_class=collapse_class,
        severity=sev,
        request_id=request_id,
        plan_hash=plan_hash,
        canonical_hash=canonical_hash,
        session_id=session_id,
        description=description,
        evidence=evidence_tuple,
    )


@dataclass
class CollapseSummary:
    """
    Summary of collapse events for a time window or batch.
    
    Aggregates counts by class and severity for reporting.
    """
    
    window_start: str
    window_end: str
    total_events: int
    by_class: dict[str, int]
    by_severity: dict[str, int]
    events: list[CollapseEvent]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "schema_version": "collapse_summary.v0.1",
            "window_start": self.window_start,
            "window_end": self.window_end,
            "total_events": self.total_events,
            "by_class": self.by_class,
            "by_severity": self.by_severity,
            "events": [e.to_dict() for e in self.events],
        }
    
    @classmethod
    def from_events(
        cls,
        events: list[CollapseEvent],
        window_start: str | None = None,
        window_end: str | None = None,
    ) -> "CollapseSummary":
        """Build summary from list of events."""
        by_class: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        
        for e in events:
            by_class[e.collapse_class.value] = by_class.get(e.collapse_class.value, 0) + 1
            by_severity[e.severity.value] = by_severity.get(e.severity.value, 0) + 1
        
        timestamps = [e.timestamp_utc for e in events if e.timestamp_utc]
        ws = window_start or (min(timestamps) if timestamps else _utc_now())
        we = window_end or (max(timestamps) if timestamps else _utc_now())
        
        return cls(
            window_start=ws,
            window_end=we,
            total_events=len(events),
            by_class=by_class,
            by_severity=by_severity,
            events=events,
        )
    
    def has_critical(self) -> bool:
        """Check if any critical severity events exist."""
        return self.by_severity.get(CollapseSeverity.CRITICAL.value, 0) > 0
    
    def has_high_or_above(self) -> bool:
        """Check if any high or critical severity events exist."""
        return (
            self.by_severity.get(CollapseSeverity.CRITICAL.value, 0) > 0
            or self.by_severity.get(CollapseSeverity.HIGH.value, 0) > 0
        )

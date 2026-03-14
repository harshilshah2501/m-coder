"""
GREG Bundle — M4.5 evidence bundle for governance escalation.

Structures escalation evidence into a deterministic, serializable bundle
for GREG (Governance Review and Escalation Group) review. No external
calls, no runtime decision modification.

Invariants:
- Deterministic serialization
- Immutable after creation
- Complete evidence chain
- Ledger references preserved
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EscalationMismatchType(str, Enum):
    """Classification of mismatches for GREG escalation (distinct from M4.4 reconciliation)."""
    
    PHASE_MISMATCH = "phase_mismatch"
    POSTURE_MISMATCH = "posture_mismatch"
    BOUNDARY_MISMATCH = "boundary_mismatch"
    AUTHORITY_MISMATCH = "authority_mismatch"
    HASH_MISMATCH = "hash_mismatch"
    EXECUTION_MISMATCH = "execution_mismatch"


class CollapseClassification(str, Enum):
    """Classification of collapse vectors per Layer-1 taxonomy."""
    
    REF_SOFTENING = "REF_SOFTENING"
    CONF_TO_DES = "CONF_TO_DES"
    BOUNDARY_RELOCATION = "BOUNDARY_RELOCATION"
    AUTHORITY_EROSION = "AUTHORITY_EROSION"
    PHASE_DRIFT = "PHASE_DRIFT"
    POSTURE_INFLATION = "POSTURE_INFLATION"
    UNCLASSIFIED = "UNCLASSIFIED"


@dataclass
class LedgerReference:
    """Reference to a ledger row for evidence chain."""
    
    event_id: str
    event_type: str
    request_id: str
    plan_hash: str
    timestamp_utc: str
    canonical_hash: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "request_id": self.request_id,
            "plan_hash": self.plan_hash,
            "timestamp_utc": self.timestamp_utc,
            "canonical_hash": self.canonical_hash,
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "LedgerReference":
        return cls(
            event_id=d.get("event_id", ""),
            event_type=d.get("event_type", ""),
            request_id=d.get("request_id", ""),
            plan_hash=d.get("plan_hash", ""),
            timestamp_utc=d.get("timestamp_utc", ""),
            canonical_hash=d.get("canonical_hash", ""),
        )


@dataclass
class MismatchEvidence:
    """Evidence record for a single mismatch."""
    
    request_id: str
    canonical_hash: str
    classification: EscalationMismatchType
    expected_value: str
    actual_value: str
    context: dict[str, Any] = field(default_factory=dict)
    ledger_refs: list[LedgerReference] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "canonical_hash": self.canonical_hash,
            "classification": self.classification.value,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "context": self.context,
            "ledger_refs": [r.to_dict() for r in self.ledger_refs],
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MismatchEvidence":
        return cls(
            request_id=d.get("request_id", ""),
            canonical_hash=d.get("canonical_hash", ""),
            classification=EscalationMismatchType(d.get("classification", "phase_mismatch")),
            expected_value=d.get("expected_value", ""),
            actual_value=d.get("actual_value", ""),
            context=d.get("context", {}),
            ledger_refs=[LedgerReference.from_dict(r) for r in d.get("ledger_refs", [])],
        )


@dataclass
class CollapseEvidence:
    """Evidence record for a collapse vector."""
    
    request_id: str
    canonical_hash: str
    classification: CollapseClassification
    description: str
    severity: str
    context: dict[str, Any] = field(default_factory=dict)
    ledger_refs: list[LedgerReference] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "canonical_hash": self.canonical_hash,
            "classification": self.classification.value,
            "description": self.description,
            "severity": self.severity,
            "context": self.context,
            "ledger_refs": [r.to_dict() for r in self.ledger_refs],
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CollapseEvidence":
        return cls(
            request_id=d.get("request_id", ""),
            canonical_hash=d.get("canonical_hash", ""),
            classification=CollapseClassification(d.get("classification", "UNCLASSIFIED")),
            description=d.get("description", ""),
            severity=d.get("severity", "low"),
            context=d.get("context", {}),
            ledger_refs=[LedgerReference.from_dict(r) for r in d.get("ledger_refs", [])],
        )


@dataclass
class DriftEvidence:
    """Evidence record for drift detection."""
    
    request_id: str
    canonical_hash: str
    baseline_value: str
    observed_value: str
    drift_percentage: float
    drift_type: str
    context: dict[str, Any] = field(default_factory=dict)
    ledger_refs: list[LedgerReference] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "canonical_hash": self.canonical_hash,
            "baseline_value": self.baseline_value,
            "observed_value": self.observed_value,
            "drift_percentage": self.drift_percentage,
            "drift_type": self.drift_type,
            "context": self.context,
            "ledger_refs": [r.to_dict() for r in self.ledger_refs],
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "DriftEvidence":
        return cls(
            request_id=d.get("request_id", ""),
            canonical_hash=d.get("canonical_hash", ""),
            baseline_value=d.get("baseline_value", ""),
            observed_value=d.get("observed_value", ""),
            drift_percentage=d.get("drift_percentage", 0.0),
            drift_type=d.get("drift_type", ""),
            context=d.get("context", {}),
            ledger_refs=[LedgerReference.from_dict(r) for r in d.get("ledger_refs", [])],
        )


@dataclass
class IntegrityEvidence:
    """Evidence record for integrity violations."""
    
    request_id: str
    canonical_hash: str
    violation_type: str
    description: str
    expected_hash: str
    actual_hash: str
    context: dict[str, Any] = field(default_factory=dict)
    ledger_refs: list[LedgerReference] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "canonical_hash": self.canonical_hash,
            "violation_type": self.violation_type,
            "description": self.description,
            "expected_hash": self.expected_hash,
            "actual_hash": self.actual_hash,
            "context": self.context,
            "ledger_refs": [r.to_dict() for r in self.ledger_refs],
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "IntegrityEvidence":
        return cls(
            request_id=d.get("request_id", ""),
            canonical_hash=d.get("canonical_hash", ""),
            violation_type=d.get("violation_type", ""),
            description=d.get("description", ""),
            expected_hash=d.get("expected_hash", ""),
            actual_hash=d.get("actual_hash", ""),
            context=d.get("context", {}),
            ledger_refs=[LedgerReference.from_dict(r) for r in d.get("ledger_refs", [])],
        )


@dataclass
class EscalationEvidence:
    """Aggregated evidence for a single escalation bundle."""
    
    mismatches: list[MismatchEvidence] = field(default_factory=list)
    collapses: list[CollapseEvidence] = field(default_factory=list)
    drifts: list[DriftEvidence] = field(default_factory=list)
    integrity_violations: list[IntegrityEvidence] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "mismatches": [m.to_dict() for m in self.mismatches],
            "collapses": [c.to_dict() for c in self.collapses],
            "drifts": [d.to_dict() for d in self.drifts],
            "integrity_violations": [i.to_dict() for i in self.integrity_violations],
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EscalationEvidence":
        return cls(
            mismatches=[MismatchEvidence.from_dict(m) for m in d.get("mismatches", [])],
            collapses=[CollapseEvidence.from_dict(c) for c in d.get("collapses", [])],
            drifts=[DriftEvidence.from_dict(dr) for dr in d.get("drifts", [])],
            integrity_violations=[IntegrityEvidence.from_dict(i) for i in d.get("integrity_violations", [])],
        )
    
    def total_count(self) -> int:
        """Total number of evidence items."""
        return (
            len(self.mismatches)
            + len(self.collapses)
            + len(self.drifts)
            + len(self.integrity_violations)
        )
    
    def affected_request_ids(self) -> list[str]:
        """Unique request IDs across all evidence."""
        ids: set[str] = set()
        for m in self.mismatches:
            if m.request_id:
                ids.add(m.request_id)
        for c in self.collapses:
            if c.request_id:
                ids.add(c.request_id)
        for d in self.drifts:
            if d.request_id:
                ids.add(d.request_id)
        for i in self.integrity_violations:
            if i.request_id:
                ids.add(i.request_id)
        return sorted(ids)
    
    def affected_canonical_hashes(self) -> list[str]:
        """Unique canonical hashes across all evidence."""
        hashes: set[str] = set()
        for m in self.mismatches:
            if m.canonical_hash:
                hashes.add(m.canonical_hash)
        for c in self.collapses:
            if c.canonical_hash:
                hashes.add(c.canonical_hash)
        for d in self.drifts:
            if d.canonical_hash:
                hashes.add(d.canonical_hash)
        for i in self.integrity_violations:
            if i.canonical_hash:
                hashes.add(i.canonical_hash)
        return sorted(hashes)


@dataclass
class BundleSummary:
    """Summary statistics for escalation bundle."""
    
    mismatch_count: int = 0
    collapse_count: int = 0
    drift_count: int = 0
    integrity_violation_count: int = 0
    total_count: int = 0
    affected_request_count: int = 0
    affected_hash_count: int = 0
    severity: str = "low"
    
    # Classification breakdowns
    mismatch_by_type: dict[str, int] = field(default_factory=dict)
    collapse_by_type: dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "mismatch_count": self.mismatch_count,
            "collapse_count": self.collapse_count,
            "drift_count": self.drift_count,
            "integrity_violation_count": self.integrity_violation_count,
            "total_count": self.total_count,
            "affected_request_count": self.affected_request_count,
            "affected_hash_count": self.affected_hash_count,
            "severity": self.severity,
            "mismatch_by_type": self.mismatch_by_type,
            "collapse_by_type": self.collapse_by_type,
        }


@dataclass
class GREGBundle:
    """
    Complete evidence bundle for GREG escalation.
    
    Immutable after creation. Contains all evidence, summary, and metadata
    for governance review. Deterministic bundle_id from content.
    """
    
    bundle_id: str
    created_at: str
    severity: str
    summary: BundleSummary
    evidence: EscalationEvidence
    
    # Metadata
    runtime_version: str = ""
    evaluation_id: str = ""
    observation_window_start: str = ""
    observation_window_end: str = ""
    thresholds_snapshot: dict[str, Any] = field(default_factory=dict)
    
    # All affected IDs for quick lookup
    affected_request_ids: list[str] = field(default_factory=list)
    affected_canonical_hashes: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "created_at": self.created_at,
            "severity": self.severity,
            "summary": self.summary.to_dict(),
            "evidence": self.evidence.to_dict(),
            "runtime_version": self.runtime_version,
            "evaluation_id": self.evaluation_id,
            "observation_window_start": self.observation_window_start,
            "observation_window_end": self.observation_window_end,
            "thresholds_snapshot": self.thresholds_snapshot,
            "affected_request_ids": self.affected_request_ids,
            "affected_canonical_hashes": self.affected_canonical_hashes,
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GREGBundle":
        return cls(
            bundle_id=d.get("bundle_id", ""),
            created_at=d.get("created_at", ""),
            severity=d.get("severity", "low"),
            summary=BundleSummary(**d.get("summary", {})),
            evidence=EscalationEvidence.from_dict(d.get("evidence", {})),
            runtime_version=d.get("runtime_version", ""),
            evaluation_id=d.get("evaluation_id", ""),
            observation_window_start=d.get("observation_window_start", ""),
            observation_window_end=d.get("observation_window_end", ""),
            thresholds_snapshot=d.get("thresholds_snapshot", {}),
            affected_request_ids=d.get("affected_request_ids", []),
            affected_canonical_hashes=d.get("affected_canonical_hashes", []),
        )
    
    def to_json(self, *, indent: int | None = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> "GREGBundle":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def content_hash(self) -> str:
        """
        Compute deterministic hash of bundle content.
        
        Excludes bundle_id and created_at for content-based comparison.
        """
        content = {
            "severity": self.severity,
            "summary": self.summary.to_dict(),
            "evidence": self.evidence.to_dict(),
            "affected_request_ids": self.affected_request_ids,
            "affected_canonical_hashes": self.affected_canonical_hashes,
        }
        content_bytes = json.dumps(content, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(content_bytes).hexdigest()

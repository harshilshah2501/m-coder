"""
Reconciliation Models — M4.4 Ledger Reconciliation.

Defines the data models for ledger reconciliation including mismatch
classifications, severity levels, and reconciliation results.

Read-only over evidence. No mutation of existing ledger rows.
Backward compatible with older rows missing identity fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MismatchSeverity(str, Enum):
    """Severity level for reconciliation mismatches."""
    
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MismatchClassification(str, Enum):
    """Classification of reconciliation mismatches.
    
    Deterministic classifications for consistency checks:
    - MISSING_DECISION: No decision row for a request that has execution
    - MISSING_EXECUTION: Decision with safe_execute but no execution row
    - MISSING_REPLAY_LINK: Replay row without linkage to original execution
    - CANONICAL_HASH_MISMATCH: Different canonical_hash between decision and execution
    - PLAN_HASH_MISMATCH: Different plan_hash between related rows
    - REQUEST_ID_ORPHAN: Row with request_id that has no other linked rows
    - INTENT_ID_MISMATCH: Different intent_id between decision and execution
    - DUPLICATE_DECISION: Multiple decision rows for same canonical_hash
    - DUPLICATE_EXECUTION: Multiple execution rows for same canonical_hash
    - BOUNDARY_PHRASE_INCONSISTENT: Different boundary phrases across rows
    - INVARIANT_VIOLATION: Ledger row invariant L1-L4 violated
    - LEGACY_ROW_NO_IDENTITY: Row missing canonical_hash (backward compatibility)
    """
    
    MISSING_DECISION = "missing_decision"
    MISSING_EXECUTION = "missing_execution"
    MISSING_REPLAY_LINK = "missing_replay_link"
    CANONICAL_HASH_MISMATCH = "canonical_hash_mismatch"
    PLAN_HASH_MISMATCH = "plan_hash_mismatch"
    REQUEST_ID_ORPHAN = "request_id_orphan"
    INTENT_ID_MISMATCH = "intent_id_mismatch"
    DUPLICATE_DECISION = "duplicate_decision"
    DUPLICATE_EXECUTION = "duplicate_execution"
    BOUNDARY_PHRASE_INCONSISTENT = "boundary_phrase_inconsistent"
    INVARIANT_VIOLATION = "invariant_violation"
    LEGACY_ROW_NO_IDENTITY = "legacy_row_no_identity"


class ReconciliationStatus(str, Enum):
    """Overall reconciliation status."""
    
    CONSISTENT = "consistent"
    WARNINGS_ONLY = "warnings_only"
    MISMATCHES_FOUND = "mismatches_found"
    CRITICAL_MISMATCHES = "critical_mismatches"


@dataclass
class RowLinkage:
    """Linkage evidence for a ledger row.
    
    Captures the identity fields used for reconciliation:
    - request_id: Links all rows for a request
    - plan_hash: Links decision to plan
    - canonical_hash: Links decision to execution to replay
    - intent_id: Unique intent instance identifier
    """
    
    ledger_row_id: str
    event_type: str
    request_id: str
    plan_hash: str = ""
    canonical_hash: str = ""
    intent_id: str = ""
    timestamp_utc: str = ""
    has_canonical_hash: bool = False
    has_intent_id: bool = False
    
    @classmethod
    def from_sandbox_row(cls, row: Any) -> RowLinkage:
        """Create linkage from SandboxLedgerStore row."""
        payload = row.payload or {}
        canonical_hash = payload.get("canonical_hash", "") or ""
        intent_id = payload.get("intent_id", "") or ""
        plan_hash = payload.get("plan_hash", "") or row.plan_hash or ""
        
        return cls(
            ledger_row_id=row.ledger_row_id,
            event_type=row.event_type,
            request_id=row.request_id,
            plan_hash=plan_hash,
            canonical_hash=canonical_hash,
            intent_id=intent_id,
            timestamp_utc=row.timestamp_utc,
            has_canonical_hash=bool(canonical_hash),
            has_intent_id=bool(intent_id),
        )
    
    @classmethod
    def from_ledger_row_v1(cls, row: Any) -> RowLinkage:
        """Create linkage from LedgerRowV1."""
        return cls(
            ledger_row_id=row.event_id,
            event_type="ledger_v1",
            request_id=row.request_id,
            plan_hash=row.plan_hash or "",
            canonical_hash="",
            intent_id="",
            timestamp_utc=row.timestamp_utc,
            has_canonical_hash=False,
            has_intent_id=False,
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "ledger_row_id": self.ledger_row_id,
            "event_type": self.event_type,
            "request_id": self.request_id,
            "plan_hash": self.plan_hash,
            "canonical_hash": self.canonical_hash,
            "intent_id": self.intent_id,
            "timestamp_utc": self.timestamp_utc,
            "has_canonical_hash": self.has_canonical_hash,
            "has_intent_id": self.has_intent_id,
        }


@dataclass
class ReconciliationMismatch:
    """A single reconciliation mismatch with classification.
    
    Classifications are deterministic based on observed evidence.
    Severity reflects impact on audit confidence.
    """
    
    classification: MismatchClassification
    severity: MismatchSeverity
    description: str
    request_id: str
    affected_rows: list[str] = field(default_factory=list)
    expected_value: str = ""
    actual_value: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification.value,
            "severity": self.severity.value,
            "description": self.description,
            "request_id": self.request_id,
            "affected_rows": self.affected_rows,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "context": self.context,
        }


@dataclass
class ReconciliationResult:
    """Result of ledger reconciliation for a scope.
    
    Contains:
    - Status summary
    - All linkage evidence found
    - All mismatches detected (deterministic)
    - Statistics for monitoring
    """
    
    status: ReconciliationStatus
    scope_request_id: str = ""
    scope_canonical_hash: str = ""
    scope_plan_hash: str = ""
    total_rows_examined: int = 0
    decision_rows_found: int = 0
    execution_rows_found: int = 0
    replay_rows_found: int = 0
    legacy_rows_found: int = 0
    linkages: list[RowLinkage] = field(default_factory=list)
    mismatches: list[ReconciliationMismatch] = field(default_factory=list)
    
    def is_consistent(self) -> bool:
        """Check if reconciliation found no issues."""
        return self.status == ReconciliationStatus.CONSISTENT
    
    def has_critical_mismatches(self) -> bool:
        """Check if any critical mismatches were found."""
        return any(
            m.severity == MismatchSeverity.CRITICAL
            for m in self.mismatches
        )
    
    def get_mismatches_by_severity(
        self, severity: MismatchSeverity
    ) -> list[ReconciliationMismatch]:
        """Get all mismatches of a specific severity."""
        return [m for m in self.mismatches if m.severity == severity]
    
    def get_mismatches_by_classification(
        self, classification: MismatchClassification
    ) -> list[ReconciliationMismatch]:
        """Get all mismatches of a specific classification."""
        return [m for m in self.mismatches if m.classification == classification]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "scope": {
                "request_id": self.scope_request_id,
                "canonical_hash": self.scope_canonical_hash,
                "plan_hash": self.scope_plan_hash,
            },
            "statistics": {
                "total_rows_examined": self.total_rows_examined,
                "decision_rows_found": self.decision_rows_found,
                "execution_rows_found": self.execution_rows_found,
                "replay_rows_found": self.replay_rows_found,
                "legacy_rows_found": self.legacy_rows_found,
            },
            "linkages": [l.to_dict() for l in self.linkages],
            "mismatches": [m.to_dict() for m in self.mismatches],
            "is_consistent": self.is_consistent(),
            "has_critical_mismatches": self.has_critical_mismatches(),
        }
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Reconciliation Status: {self.status.value}",
            f"Scope: request_id={self.scope_request_id or 'all'}, "
            f"canonical_hash={self.scope_canonical_hash or 'any'}, "
            f"plan_hash={self.scope_plan_hash or 'any'}",
            f"Rows examined: {self.total_rows_examined}",
            f"  Decision rows: {self.decision_rows_found}",
            f"  Execution rows: {self.execution_rows_found}",
            f"  Replay rows: {self.replay_rows_found}",
            f"  Legacy rows (no identity): {self.legacy_rows_found}",
        ]
        
        if self.mismatches:
            lines.append(f"\nMismatches found: {len(self.mismatches)}")
            by_severity = {}
            for m in self.mismatches:
                sev = m.severity.value
                by_severity[sev] = by_severity.get(sev, 0) + 1
            for sev, count in sorted(by_severity.items()):
                lines.append(f"  {sev}: {count}")
        else:
            lines.append("\nNo mismatches found.")
        
        return "\n".join(lines)

"""
Ledger Replay — M3.5 deterministic session reconstruction from ledger.

Reconstructs runtime sessions from ledger rows for audit and debugging.
Supports join/reconciliation operations.

Invariants:
- Replay produces identical session state given same ledger
- Join key (request_id, plan_hash) links all related records
- Boundary phrase exact match verified during replay
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from runtime.ledger.contracts import (
    DecisionEvent,
    ExecutionEvent,
    LedgerEventType,
    LedgerRowV1,
    PlanEvent,
    ReplaySession,
)
from runtime.ledger.store import LedgerStore


@dataclass
class ReplayResult:
    """Result of a replay operation."""
    
    sessions: list[ReplaySession] = field(default_factory=list)
    total_rows: int = 0
    total_sessions: int = 0
    incomplete_sessions: int = 0
    validation_errors: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "sessions": [s.to_dict() for s in self.sessions],
            "total_rows": self.total_rows,
            "total_sessions": self.total_sessions,
            "incomplete_sessions": self.incomplete_sessions,
            "validation_errors": self.validation_errors,
        }


@dataclass
class ReconciliationResult:
    """Result of ledger reconciliation operation."""
    
    request_id: str
    plan_hash: str
    rows: list[LedgerRowV1] = field(default_factory=list)
    plan_events: list[dict[str, Any]] = field(default_factory=list)
    decision_events: list[dict[str, Any]] = field(default_factory=list)
    execution_events: list[dict[str, Any]] = field(default_factory=list)
    boundary_phrase_match: bool = True
    invariant_violations: list[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """Check if reconciliation found no issues."""
        return self.boundary_phrase_match and len(self.invariant_violations) == 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "plan_hash": self.plan_hash,
            "row_count": len(self.rows),
            "plan_events": self.plan_events,
            "decision_events": self.decision_events,
            "execution_events": self.execution_events,
            "boundary_phrase_match": self.boundary_phrase_match,
            "invariant_violations": self.invariant_violations,
            "is_valid": self.is_valid(),
        }


class LedgerReplay:
    """
    Deterministic ledger replay and reconciliation.
    
    Features:
    - Session reconstruction from ledger rows
    - Join/reconciliation by (request_id, plan_hash)
    - Boundary phrase verification
    - Invariant validation
    """
    
    def __init__(self, store: LedgerStore):
        """
        Initialize replay with ledger store.
        
        Args:
            store: LedgerStore to replay from
        """
        self.store = store
    
    def reconstruct_session(self, request_id: str) -> ReplaySession:
        """
        Reconstruct a complete session from ledger rows.
        
        Args:
            request_id: The request to reconstruct
            
        Returns:
            ReplaySession with all events and ledger rows
        """
        rows = self.store.get_by_request_id(request_id)
        
        if not rows:
            return ReplaySession(
                request_id=request_id,
                session_id="",
                plan_hash="",
            )
        
        first_row = rows[0]
        session = ReplaySession(
            request_id=request_id,
            session_id=first_row.session_id,
            plan_hash=first_row.plan_hash,
            ledger_rows=rows,
        )
        
        for row in rows:
            event_dict = row.to_dict()
            session.events.append(event_dict)
            
            terminal_posture = row.terminal_posture
            phase = row.phase_emitted
            
            if phase in ("REF", "CONF", "DES") and terminal_posture:
                if session.decision_event is None:
                    session.decision_event = DecisionEvent(
                        request_id=row.request_id,
                        session_id=row.session_id,
                        plan_hash=row.plan_hash,
                        timestamp_utc=row.timestamp_utc,
                        decision_posture=terminal_posture,
                        phase_emitted=phase,
                        authority_verdict=row.authority_verdict,
                        boundary_verdict=row.boundary_verdict,
                        boundary_crossed=row.boundary_crossed,
                        reason_codes=row.reason_codes,
                        mode=row.mode,
                    )
                    
                    session.plan_event = PlanEvent(
                        request_id=row.request_id,
                        session_id=row.session_id,
                        plan_hash=row.plan_hash,
                        timestamp_utc=row.timestamp_utc,
                        constitutional_phase_expected=phase,
                        boundary_phrase=row.irreversible_boundary_phrase,
                        authority_verdict=row.authority_verdict,
                        terminal_posture=terminal_posture,
                        mode=row.mode,
                    )
            
            if phase == "CODE" and terminal_posture == "safe_execute":
                if session.execution_event is None:
                    commands_executed = []
                    commands_blocked = []
                    for intent in row.execution_intents:
                        if intent.blocked:
                            commands_blocked.append(intent.intent)
                        else:
                            commands_executed.append(intent.intent)
                    
                    session.execution_event = ExecutionEvent(
                        request_id=row.request_id,
                        session_id=row.session_id,
                        plan_hash=row.plan_hash,
                        timestamp_utc=row.timestamp_utc,
                        execution_outcome="executed",
                        sandbox_id="",
                        commands_executed=commands_executed,
                        commands_blocked=commands_blocked,
                        exit_code=None,
                        duration_ms=row.latency_ms or 0,
                        artifacts=[],
                        mode=row.mode,
                    )
        
        return session
    
    def reconstruct_all_sessions(self) -> ReplayResult:
        """
        Reconstruct all sessions from ledger.
        
        Returns:
            ReplayResult with all sessions and statistics
        """
        result = ReplayResult()
        
        request_ids = self.store.get_unique_request_ids()
        result.total_rows = self.store.count()
        result.total_sessions = len(request_ids)
        
        for request_id in request_ids:
            session = self.reconstruct_session(request_id)
            result.sessions.append(session)
            
            if not session.is_complete():
                result.incomplete_sessions += 1
            
            for row in session.ledger_rows:
                violations = row.validate_invariants()
                for v in violations:
                    result.validation_errors.append(
                        f"Request {request_id}: invariant {v} violated"
                    )
        
        return result
    
    def reconcile(self, request_id: str, plan_hash: str) -> ReconciliationResult:
        """
        Reconcile ledger rows by join key (request_id, plan_hash).
        
        Verifies boundary phrase consistency and invariants across
        all related records.
        
        Args:
            request_id: Request identifier
            plan_hash: Plan hash for join
            
        Returns:
            ReconciliationResult with validation status
        """
        result = ReconciliationResult(
            request_id=request_id,
            plan_hash=plan_hash,
        )
        
        rows = self.store.get_by_join_key(request_id, plan_hash)
        result.rows = rows
        
        if not rows:
            return result
        
        boundary_phrases: set[str] = set()
        
        for row in rows:
            event_type = self._infer_event_type(row)
            event_dict = {
                "event_id": row.event_id,
                "timestamp_utc": row.timestamp_utc,
                "terminal_posture": row.terminal_posture,
                "phase_emitted": row.phase_emitted,
            }
            
            if event_type in ("plan_emitted", "decision_emitted"):
                result.decision_events.append(event_dict)
                result.plan_events.append({
                    "event_id": row.event_id,
                    "plan_hash": row.plan_hash,
                    "boundary_phrase": row.irreversible_boundary_phrase,
                    "phase": row.phase_emitted,
                })
            elif event_type in ("execution_completed", "execution_blocked", "execution_refused"):
                result.execution_events.append(event_dict)
            
            if row.irreversible_boundary_phrase:
                boundary_phrases.add(row.irreversible_boundary_phrase)
            
            violations = row.validate_invariants()
            for v in violations:
                result.invariant_violations.append(f"{row.event_id}: {v}")
        
        if len(boundary_phrases) > 1:
            result.boundary_phrase_match = False
            result.invariant_violations.append(
                f"Multiple boundary phrases detected: {boundary_phrases}"
            )
        
        return result
    
    def _infer_event_type(self, row: LedgerRowV1) -> str:
        """Infer event type from ledger row content."""
        if row.phase_emitted == "CODE":
            if row.terminal_posture == "safe_execute":
                return "execution_completed"
            elif row.terminal_posture == "refuse":
                return "execution_refused"
            else:
                return "execution_blocked"
        elif row.terminal_posture in ("refuse", "defer", "bounded_allow"):
            return "decision_emitted"
        else:
            return "plan_emitted"
    
    def verify_boundary_phrase_match(
        self,
        request_id: str,
        expected_phrase: str,
    ) -> bool:
        """
        Verify that all ledger rows for a request have matching boundary phrase.
        
        Args:
            request_id: Request to verify
            expected_phrase: Expected boundary phrase
            
        Returns:
            True if all boundary phrases match (or are empty), False otherwise
        """
        rows = self.store.get_by_request_id(request_id)
        
        for row in rows:
            if row.irreversible_boundary_phrase:
                if row.irreversible_boundary_phrase != expected_phrase:
                    return False
        
        return True
    
    def get_session_timeline(self, request_id: str) -> list[dict[str, Any]]:
        """
        Get chronological timeline of events for a request.
        
        Useful for debugging and visualization.
        """
        rows = self.store.get_by_request_id(request_id)
        
        timeline = []
        for row in rows:
            timeline.append({
                "timestamp_utc": row.timestamp_utc,
                "event_id": row.event_id,
                "phase": row.phase_emitted,
                "posture": row.terminal_posture,
                "authority": row.authority_verdict,
                "boundary": row.boundary_verdict,
                "reason_codes": row.reason_codes,
            })
        
        return timeline
    
    def export_session_json(self, request_id: str) -> str:
        """
        Export session as JSON for external audit tools.
        """
        session = self.reconstruct_session(request_id)
        return json.dumps(session.to_dict(), indent=2, sort_keys=True)
    
    def validate_no_duplicate_emissions(self, request_id: str) -> list[str]:
        """
        Verify no duplicate ledger emissions for a request.
        
        A simple REF refusal should produce exactly one ledger row.
        
        Returns:
            List of validation errors (empty if valid)
        """
        rows = self.store.get_by_request_id(request_id)
        errors: list[str] = []
        
        if not rows:
            return errors
        
        decision_rows = [
            r for r in rows
            if r.phase_emitted in ("REF", "CONF", "DES")
            and r.terminal_posture in ("refuse", "defer", "bounded_allow", "safe_execute")
        ]
        
        ref_refusals = [
            r for r in decision_rows
            if r.phase_emitted == "REF" and r.terminal_posture == "refuse"
        ]
        
        if len(ref_refusals) > 1:
            event_ids = [r.event_id for r in ref_refusals]
            errors.append(
                f"Multiple REF refusal ledger rows for request {request_id}: {event_ids}"
            )
        
        event_ids = [r.event_id for r in rows]
        if len(event_ids) != len(set(event_ids)):
            errors.append(f"Duplicate event_ids detected for request {request_id}")
        
        return errors
    
    def get_statistics(self) -> dict[str, Any]:
        """
        Get ledger statistics for monitoring/observation.
        """
        all_rows = list(self.store.iter_all())
        
        stats: dict[str, Any] = {
            "total_rows": len(all_rows),
            "unique_requests": len(self.store.get_unique_request_ids()),
            "unique_sessions": len(self.store.get_unique_session_ids()),
            "by_phase": {},
            "by_posture": {},
            "by_authority": {},
            "invariant_violations": 0,
        }
        
        for row in all_rows:
            phase = row.phase_emitted
            stats["by_phase"][phase] = stats["by_phase"].get(phase, 0) + 1
            
            posture = row.terminal_posture
            stats["by_posture"][posture] = stats["by_posture"].get(posture, 0) + 1
            
            auth = row.authority_verdict
            stats["by_authority"][auth] = stats["by_authority"].get(auth, 0) + 1
            
            violations = row.validate_invariants()
            stats["invariant_violations"] += len(violations)
        
        return stats

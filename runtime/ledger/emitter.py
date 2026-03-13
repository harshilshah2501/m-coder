"""
Ledger Emitter — M3.5 deterministic ledger emission for runtime decisions.

Emits ledger_row.v0.1 compliant records for every runtime decision.
Deterministic hashing for event_id and plan linkage.

Invariants:
- Every decision produces exactly one ledger row
- Deterministic: same inputs produce identical outputs
- No mutation after emission
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from runtime.ledger.contracts import (
    AuthorityVerdict,
    BoundaryVerdict,
    DecisionEvent,
    ExecutionEvent,
    ExecutionIntent,
    LedgerEventType,
    LedgerRowV1,
    PhaseEmitted,
    PlanEvent,
    TerminalPosture,
    ToolCallAttempt,
)
from runtime.ledger.store import LedgerStore

if TYPE_CHECKING:
    from runtime.plangate.plangate_decision import PlanGateDecision


def _canonical_json(obj: Any) -> bytes:
    """Stable JSON: sorted keys, UTF-8."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _derive_hash(content: bytes) -> str:
    """SHA-256 hash of content."""
    return hashlib.sha256(content).hexdigest()


def _derive_event_id(prefix: str, content: bytes) -> str:
    """Deterministic event ID from content hash."""
    return f"{prefix}-{_derive_hash(content)[:32]}"


def compute_plan_hash(plan: dict[str, Any]) -> str:
    """
    Compute deterministic hash of a plan object.
    
    Uses canonical JSON serialization for stability.
    """
    return _derive_hash(_canonical_json(plan))


def compute_boundary_phrase_hash(boundary_phrase: str) -> str:
    """
    Compute deterministic hash of boundary phrase.
    
    Used to verify exact match between plan and ledger.
    """
    return _derive_hash(boundary_phrase.encode("utf-8"))


class LedgerEmitterV1:
    """
    Deterministic ledger emitter producing ledger_row.v0.1 records.
    
    Features:
    - Deterministic event_id generation
    - Schema-compliant output
    - Optional persistence via LedgerStore
    - Invariant validation
    """
    
    def __init__(
        self,
        *,
        store: LedgerStore | None = None,
        fixed_time: str | None = None,
        runtime_version: str = "0.1.0",
        model_adapter_version: str | None = None,
    ):
        """
        Initialize emitter.
        
        Args:
            store: Optional LedgerStore for persistence
            fixed_time: Optional fixed timestamp for deterministic testing
            runtime_version: Runtime version for ledger rows
            model_adapter_version: Optional model adapter version
        """
        self.store = store
        self.fixed_time = fixed_time
        self.runtime_version = runtime_version
        self.model_adapter_version = model_adapter_version
        self._emitted: list[LedgerRowV1] = []
    
    def _timestamp(self) -> str:
        """Get current timestamp or fixed time."""
        return self.fixed_time or datetime.now(timezone.utc).isoformat()
    
    def emit_decision(
        self,
        *,
        request_id: str,
        session_id: str,
        plan: dict[str, Any],
        phase_emitted: str | PhaseEmitted,
        terminal_posture: str | TerminalPosture,
        authority_verdict: str | AuthorityVerdict,
        boundary_verdict: str | BoundaryVerdict,
        ref_enforced: bool,
        irreversible_boundary_phrase: str,
        boundary_cross_attempted: bool,
        boundary_crossed: bool,
        reason_codes: list[str],
        mode: str = "shadow",
        tool_calls_attempted: list[ToolCallAttempt] | None = None,
        execution_intents: list[ExecutionIntent] | None = None,
        latency_ms: int | None = None,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
        legitimacy_state: str | None = None,
        irreversibility_state: str | None = None,
        ambiguity_state: str | None = None,
        dominance_applied: str | None = None,
    ) -> LedgerRowV1:
        """
        Emit a ledger row for a runtime decision.
        
        Creates schema-compliant ledger_row.v0.1 record with deterministic
        event_id derived from plan content and timestamp.
        
        Args:
            request_id: Request identifier
            session_id: Session identifier
            plan: Plan object (used for plan_hash computation)
            phase_emitted: Constitutional phase
            terminal_posture: Decision posture
            authority_verdict: Authority validation result
            boundary_verdict: Boundary detection result
            ref_enforced: Whether REF was enforced
            irreversible_boundary_phrase: Exact boundary phrase from plan
            boundary_cross_attempted: Whether crossing was attempted
            boundary_crossed: Whether boundary was actually crossed
            reason_codes: List of reason codes
            mode: Execution mode (shadow/live)
            tool_calls_attempted: Tool call records
            execution_intents: Execution intent records
            latency_ms: Optional latency metric
            tokens_in: Optional input tokens metric
            tokens_out: Optional output tokens metric
            legitimacy_state: Optional routing invariant
            irreversibility_state: Optional routing invariant
            ambiguity_state: Optional routing invariant
            dominance_applied: Optional routing invariant
            
        Returns:
            LedgerRowV1 with all fields populated
        """
        timestamp = self._timestamp()
        plan_hash = compute_plan_hash(plan)
        
        if isinstance(phase_emitted, PhaseEmitted):
            phase_emitted = phase_emitted.value
        if isinstance(terminal_posture, TerminalPosture):
            terminal_posture = terminal_posture.value
        if isinstance(authority_verdict, AuthorityVerdict):
            authority_verdict = authority_verdict.value
        if isinstance(boundary_verdict, BoundaryVerdict):
            boundary_verdict = boundary_verdict.value
        
        event_content = _canonical_json({
            "request_id": request_id,
            "session_id": session_id,
            "plan_hash": plan_hash,
            "timestamp": timestamp,
        })
        event_id = _derive_event_id("ldg", event_content)
        
        row = LedgerRowV1(
            event_id=event_id,
            timestamp_utc=timestamp,
            request_id=request_id,
            session_id=session_id,
            mode=mode,
            runtime_version=self.runtime_version,
            model_adapter_version=self.model_adapter_version,
            plan_hash=plan_hash,
            plan_schema_version="plan.v0.1",
            phase_emitted=phase_emitted,
            terminal_posture=terminal_posture,
            authority_verdict=authority_verdict,
            boundary_verdict=boundary_verdict,
            ref_enforced=ref_enforced,
            irreversible_boundary_phrase=irreversible_boundary_phrase,
            boundary_cross_attempted=boundary_cross_attempted,
            boundary_crossed=boundary_crossed,
            reason_codes=reason_codes,
            tool_calls_attempted=tool_calls_attempted or [],
            execution_intents=execution_intents or [],
            latency_ms=latency_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            legitimacy_state=legitimacy_state,
            irreversibility_state=irreversibility_state,
            ambiguity_state=ambiguity_state,
            dominance_applied=dominance_applied,
        )
        
        violations = row.validate_invariants()
        if violations:
            raise ValueError(f"Ledger invariant violations: {violations}")
        
        self._emitted.append(row)
        
        if self.store:
            self.store.append_row(row, LedgerEventType.DECISION_EMITTED)
        
        return row
    
    def emit_from_plan_decision(
        self,
        *,
        event: dict[str, Any],
        decision: Any,
        plan: dict[str, Any],
        mode: str = "shadow",
    ) -> LedgerRowV1:
        """
        Emit ledger row from a PlanDecision (compatibility with emulator).
        
        Converts PlanDecision fields to ledger_row.v0.1 format.
        """
        posture_map = {
            "REFUSAL": "refuse",
            "BOUNDED_ALLOW": "bounded_allow",
            "SAFE_EXECUTE": "safe_execute",
        }
        terminal_posture = posture_map.get(
            getattr(decision.decision, "value", str(decision.decision)),
            "refuse",
        )
        
        return self.emit_decision(
            request_id=event.get("request_id", "req-unknown"),
            session_id=event.get("session_id", "sess-unknown"),
            plan=plan,
            phase_emitted=getattr(decision.phase, "value", str(decision.phase)),
            terminal_posture=terminal_posture,
            authority_verdict=getattr(decision.authority_verdict, "value", str(decision.authority_verdict)),
            boundary_verdict=getattr(decision.boundary_verdict, "value", str(decision.boundary_verdict)),
            ref_enforced=getattr(decision.phase, "value", "") == "REF",
            irreversible_boundary_phrase=event.get("boundary_phrase", ""),
            boundary_cross_attempted=getattr(decision.boundary_verdict, "value", "") in ("detected", "crossed"),
            boundary_crossed=getattr(decision.boundary_verdict, "value", "") == "crossed",
            reason_codes=decision.reason_codes,
            mode=mode,
        )
    
    def emit_plangate_decision(
        self,
        *,
        request_id: str,
        session_id: str,
        plan_hash: str,
        decision: "PlanGateDecision",
        mode: str = "shadow",
    ) -> LedgerRowV1:
        """
        Emit ledger row for a PlanGate decision.
        
        Maps PlanGateDecision posture to terminal_posture and event type.
        """
        posture = getattr(decision, "posture", "refuse")
        
        posture_to_terminal = {
            "refuse": "refuse",
            "defer": "defer",
            "bounded_allow": "bounded_allow",
            "safe_execute": "safe_execute",
        }
        terminal_posture = posture_to_terminal.get(posture, "refuse")
        
        posture_to_boundary = {
            "refuse": "blocked",
            "defer": "not_reached",
            "bounded_allow": "allowed_pre_boundary_only",
            "safe_execute": "not_reached",
        }
        boundary_verdict = posture_to_boundary.get(posture, "blocked")
        
        authority_ok = getattr(decision, "authority_ok", False)
        authority_verdict = "pass" if authority_ok else "fail"
        
        ref_enforced = posture == "refuse" and not authority_ok
        
        reason = getattr(decision, "reason", "")
        reason_codes = []
        if not authority_ok:
            reason_codes.append("MISSING_AUTHORITY")
        if posture == "refuse":
            reason_codes.append("REF_ENFORCED")
        elif posture == "bounded_allow":
            reason_codes.append("SAFE_PREBOUNDARY_ONLY")
        
        irreversible = getattr(decision, "irreversible", False)
        boundary_detected = getattr(decision, "boundary_detected", False)
        boundary_phrase = ""
        
        timestamp = self._timestamp()
        
        event_content = _canonical_json({
            "request_id": request_id,
            "session_id": session_id,
            "plan_hash": plan_hash,
            "posture": posture,
            "timestamp": timestamp,
        })
        event_id = _derive_event_id("pg", event_content)
        
        row = LedgerRowV1(
            event_id=event_id,
            timestamp_utc=timestamp,
            request_id=request_id,
            session_id=session_id,
            mode=mode,
            runtime_version=self.runtime_version,
            model_adapter_version=self.model_adapter_version,
            plan_hash=plan_hash,
            plan_schema_version="plan.v0.1",
            phase_emitted="CODE" if posture == "safe_execute" else ("CONF" if posture == "bounded_allow" else "REF"),
            terminal_posture=terminal_posture,
            authority_verdict=authority_verdict,
            boundary_verdict=boundary_verdict,
            ref_enforced=ref_enforced,
            irreversible_boundary_phrase=boundary_phrase,
            boundary_cross_attempted=boundary_detected and posture not in ("refuse", "defer"),
            boundary_crossed=False,
            reason_codes=reason_codes,
        )
        
        self._emitted.append(row)
        
        if self.store:
            event_type = {
                "refuse": LedgerEventType.PLANGATE_REFUSED,
                "defer": LedgerEventType.PLANGATE_DEFERRED,
                "bounded_allow": LedgerEventType.PLANGATE_BOUNDED_ALLOW,
                "safe_execute": LedgerEventType.PLANGATE_SAFE_EXECUTE,
            }.get(posture, LedgerEventType.PLANGATE_REFUSED)
            self.store.append_row(row, event_type)
        
        return row
    
    def emit_execution(
        self,
        *,
        request_id: str,
        session_id: str,
        plan_hash: str,
        sandbox_id: str,
        outcome: str,
        commands_executed: list[str],
        commands_blocked: list[str],
        exit_code: int | None,
        duration_ms: int,
        artifacts: list[str],
        mode: str = "shadow",
    ) -> LedgerRowV1:
        """
        Emit ledger row for execution completion.
        
        Maps execution outcome to appropriate terminal posture.
        """
        timestamp = self._timestamp()
        
        outcome_to_posture = {
            "executed": "safe_execute",
            "blocked": "bounded_allow",
            "refused": "refuse",
        }
        terminal_posture = outcome_to_posture.get(outcome, "refuse")
        
        execution_intents = []
        for cmd in commands_executed:
            execution_intents.append(ExecutionIntent(
                intent=cmd,
                blocked=False,
                reason_code="",
            ))
        for cmd in commands_blocked:
            execution_intents.append(ExecutionIntent(
                intent=cmd,
                blocked=True,
                reason_code="TOOL_NOT_PERMITTED",
            ))
        
        reason_codes = []
        if outcome == "refused":
            reason_codes.append("REF_ENFORCED")
        elif outcome == "blocked":
            reason_codes.append("TOOL_NOT_PERMITTED")
        
        event_content = _canonical_json({
            "request_id": request_id,
            "session_id": session_id,
            "plan_hash": plan_hash,
            "sandbox_id": sandbox_id,
            "timestamp": timestamp,
        })
        event_id = _derive_event_id("exec", event_content)
        
        row = LedgerRowV1(
            event_id=event_id,
            timestamp_utc=timestamp,
            request_id=request_id,
            session_id=session_id,
            mode=mode,
            runtime_version=self.runtime_version,
            model_adapter_version=self.model_adapter_version,
            plan_hash=plan_hash,
            plan_schema_version="plan.v0.1",
            phase_emitted="CODE",
            terminal_posture=terminal_posture,
            authority_verdict="pass" if outcome == "executed" else "fail",
            boundary_verdict="not_reached" if outcome == "executed" else "blocked",
            ref_enforced=outcome == "refused",
            irreversible_boundary_phrase="",
            boundary_cross_attempted=False,
            boundary_crossed=False,
            reason_codes=reason_codes,
            execution_intents=execution_intents,
            latency_ms=duration_ms,
        )
        
        self._emitted.append(row)
        
        if self.store:
            event_type = {
                "executed": LedgerEventType.EXECUTION_COMPLETED,
                "blocked": LedgerEventType.EXECUTION_BLOCKED,
                "refused": LedgerEventType.EXECUTION_REFUSED,
            }.get(outcome, LedgerEventType.EXECUTION_REFUSED)
            self.store.append_row(row, event_type)
        
        return row
    
    def emit_transition(
        self,
        *,
        request_id: str,
        session_id: str,
        plan_hash: str,
        transition_id: str,
        from_state: str,
        to_state: str,
        mode: str = "shadow",
    ) -> LedgerRowV1:
        """
        Emit ledger row for state transition (for replay support).
        """
        timestamp = self._timestamp()
        
        event_content = _canonical_json({
            "request_id": request_id,
            "session_id": session_id,
            "plan_hash": plan_hash,
            "transition_id": transition_id,
            "from_state": from_state,
            "to_state": to_state,
            "timestamp": timestamp,
        })
        event_id = _derive_event_id("trans", event_content)
        
        row = LedgerRowV1(
            event_id=event_id,
            timestamp_utc=timestamp,
            request_id=request_id,
            session_id=session_id,
            mode=mode,
            runtime_version=self.runtime_version,
            model_adapter_version=self.model_adapter_version,
            plan_hash=plan_hash,
            plan_schema_version="plan.v0.1",
            phase_emitted="CODE",
            terminal_posture="safe_execute",
            authority_verdict="pass",
            boundary_verdict="not_reached",
            ref_enforced=False,
            irreversible_boundary_phrase="",
            boundary_cross_attempted=False,
            boundary_crossed=False,
            reason_codes=[],
        )
        
        self._emitted.append(row)
        
        if self.store:
            self.store.append_row(row, LedgerEventType.TRANSITION_APPLIED)
        
        return row
    
    def get_emitted(self) -> list[LedgerRowV1]:
        """Return all emitted rows for this emitter instance."""
        return list(self._emitted)
    
    def get_emitted_for_request(self, request_id: str) -> list[LedgerRowV1]:
        """Return emitted rows for a specific request_id."""
        return [r for r in self._emitted if r.request_id == request_id]
    
    def clear_emitted(self) -> None:
        """Clear in-memory emitted rows (for testing)."""
        self._emitted.clear()

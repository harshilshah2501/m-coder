"""
Ledger Contracts — M3.5 data structures for ledger emission and replay.

Implements ledger_row.v0.1 schema compliance with full field coverage.

Invariants:
- All fields deterministic
- plan_hash links to source plan
- boundary_phrase exact match required
- No mutation after creation
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class LedgerEventType(str, Enum):
    """Event types for ledger rows."""
    
    PLAN_EMITTED = "plan_emitted"
    DECISION_EMITTED = "decision_emitted"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_REFUSED = "execution_refused"
    EXECUTION_BLOCKED = "execution_blocked"
    PLANGATE_REFUSED = "plangate_refused"
    PLANGATE_DEFERRED = "plangate_deferred"
    PLANGATE_BOUNDED_ALLOW = "plangate_bounded_allow"
    PLANGATE_SAFE_EXECUTE = "plangate_safe_execute"
    TRANSITION_APPLIED = "transition_applied"
    BOUNDARY_BLOCKED = "boundary_blocked"


class TerminalPosture(str, Enum):
    """Terminal posture values from ledger_row.v0.1 schema."""
    
    REFUSE = "refuse"
    DEFER = "defer"
    BOUNDED_ALLOW = "bounded_allow"
    SAFE_EXECUTE = "safe_execute"


class AuthorityVerdict(str, Enum):
    """Authority verdict values from ledger_row.v0.1 schema."""
    
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class BoundaryVerdict(str, Enum):
    """Boundary verdict values from ledger_row.v0.1 schema."""
    
    BLOCKED = "blocked"
    NOT_REACHED = "not_reached"
    ALLOWED_PRE_BOUNDARY_ONLY = "allowed_pre_boundary_only"
    CROSSED = "crossed"


class PhaseEmitted(str, Enum):
    """Constitutional phase values."""
    
    REF = "REF"
    CONF = "CONF"
    DES = "DES"
    MIX = "MIX"
    CODE = "CODE"


def _canonical_json(obj: Any) -> bytes:
    """Stable JSON serialization: sorted keys, UTF-8."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _derive_hash(content: bytes) -> str:
    """SHA-256 hash of content, hex-encoded."""
    return hashlib.sha256(content).hexdigest()


def _derive_event_id(prefix: str, content: bytes) -> str:
    """Deterministic event ID from content hash."""
    return f"{prefix}-{_derive_hash(content)[:32]}"


@dataclass
class ToolCallAttempt:
    """Record of a tool call attempt for ledger."""
    
    tool: str
    intent: str
    blocked: bool
    reason_code: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "intent": self.intent,
            "blocked": self.blocked,
            "reason_code": self.reason_code,
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ToolCallAttempt":
        return cls(
            tool=d["tool"],
            intent=d["intent"],
            blocked=d["blocked"],
            reason_code=d["reason_code"],
        )


@dataclass
class ExecutionIntent:
    """Record of an execution intent for ledger."""
    
    intent: str
    blocked: bool
    reason_code: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "blocked": self.blocked,
            "reason_code": self.reason_code,
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ExecutionIntent":
        return cls(
            intent=d["intent"],
            blocked=d["blocked"],
            reason_code=d["reason_code"],
        )


@dataclass
class LedgerRowV1:
    """
    Ledger row conforming to ledger_row.v0.1 schema.
    
    Immutable after creation. All fields required for audit/replay.
    Join key: (request_id, plan_hash)
    """
    
    event_id: str
    timestamp_utc: str
    request_id: str
    session_id: str
    mode: str
    runtime_version: str
    plan_hash: str
    plan_schema_version: str
    phase_emitted: str
    terminal_posture: str
    authority_verdict: str
    boundary_verdict: str
    ref_enforced: bool
    irreversible_boundary_phrase: str
    boundary_cross_attempted: bool
    boundary_crossed: bool
    reason_codes: list[str]
    tool_calls_attempted: list[ToolCallAttempt] = field(default_factory=list)
    execution_intents: list[ExecutionIntent] = field(default_factory=list)
    latency_ms: int | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    model_adapter_version: str | None = None
    legitimacy_state: str | None = None
    irreversibility_state: str | None = None
    ambiguity_state: str | None = None
    dominance_applied: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to ledger_row.v0.1 schema-compliant dictionary."""
        d: dict[str, Any] = {
            "schema_version": "ledger_row.v0.1",
            "event": {
                "event_id": self.event_id,
                "timestamp_utc": self.timestamp_utc,
                "request_id": self.request_id,
                "session_id": self.session_id,
                "mode": self.mode,
                "runtime_version": self.runtime_version,
            },
            "plan_link": {
                "plan_hash": self.plan_hash,
                "plan_schema_version": self.plan_schema_version,
            },
            "verdicts": {
                "phase_emitted": self.phase_emitted,
                "terminal_posture": self.terminal_posture,
                "authority_verdict": self.authority_verdict,
                "boundary_verdict": self.boundary_verdict,
                "ref_enforced": self.ref_enforced,
            },
            "boundary": {
                "irreversible_boundary_phrase": self.irreversible_boundary_phrase,
                "boundary_cross_attempted": self.boundary_cross_attempted,
                "boundary_crossed": self.boundary_crossed,
            },
            "actions": {
                "tool_calls_attempted": [t.to_dict() for t in self.tool_calls_attempted],
                "execution_intents": [e.to_dict() for e in self.execution_intents],
            },
            "reason_codes": self.reason_codes,
        }
        
        if self.model_adapter_version:
            d["event"]["model_adapter_version"] = self.model_adapter_version
        
        if self.latency_ms is not None or self.tokens_in is not None or self.tokens_out is not None:
            d["metrics"] = {}
            if self.latency_ms is not None:
                d["metrics"]["latency_ms"] = self.latency_ms
            if self.tokens_in is not None:
                d["metrics"]["tokens_in"] = self.tokens_in
            if self.tokens_out is not None:
                d["metrics"]["tokens_out"] = self.tokens_out
        
        if any([self.legitimacy_state, self.irreversibility_state, 
                self.ambiguity_state, self.dominance_applied]):
            d["routing_invariants"] = {}
            if self.legitimacy_state:
                d["routing_invariants"]["legitimacy_state"] = self.legitimacy_state
            if self.irreversibility_state:
                d["routing_invariants"]["irreversibility_state"] = self.irreversibility_state
            if self.ambiguity_state:
                d["routing_invariants"]["ambiguity_state"] = self.ambiguity_state
            if self.dominance_applied:
                d["routing_invariants"]["dominance_applied"] = self.dominance_applied
        
        return d
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "LedgerRowV1":
        """Reconstruct LedgerRowV1 from dictionary."""
        event = d.get("event", {})
        plan_link = d.get("plan_link", {})
        verdicts = d.get("verdicts", {})
        boundary = d.get("boundary", {})
        actions = d.get("actions", {})
        metrics = d.get("metrics", {})
        routing = d.get("routing_invariants", {})
        
        return cls(
            event_id=event.get("event_id", ""),
            timestamp_utc=event.get("timestamp_utc", ""),
            request_id=event.get("request_id", ""),
            session_id=event.get("session_id", ""),
            mode=event.get("mode", "shadow"),
            runtime_version=event.get("runtime_version", ""),
            model_adapter_version=event.get("model_adapter_version"),
            plan_hash=plan_link.get("plan_hash", ""),
            plan_schema_version=plan_link.get("plan_schema_version", "plan.v0.1"),
            phase_emitted=verdicts.get("phase_emitted", ""),
            terminal_posture=verdicts.get("terminal_posture", ""),
            authority_verdict=verdicts.get("authority_verdict", ""),
            boundary_verdict=verdicts.get("boundary_verdict", ""),
            ref_enforced=verdicts.get("ref_enforced", False),
            irreversible_boundary_phrase=boundary.get("irreversible_boundary_phrase", ""),
            boundary_cross_attempted=boundary.get("boundary_cross_attempted", False),
            boundary_crossed=boundary.get("boundary_crossed", False),
            tool_calls_attempted=[
                ToolCallAttempt.from_dict(t) for t in actions.get("tool_calls_attempted", [])
            ],
            execution_intents=[
                ExecutionIntent.from_dict(e) for e in actions.get("execution_intents", [])
            ],
            reason_codes=d.get("reason_codes", []),
            latency_ms=metrics.get("latency_ms"),
            tokens_in=metrics.get("tokens_in"),
            tokens_out=metrics.get("tokens_out"),
            legitimacy_state=routing.get("legitimacy_state"),
            irreversibility_state=routing.get("irreversibility_state"),
            ambiguity_state=routing.get("ambiguity_state"),
            dominance_applied=routing.get("dominance_applied"),
        )
    
    def validate_invariants(self) -> list[str]:
        """
        Validate runtime invariants (L1-L5 from ledger schema).
        
        Returns list of violated rule identifiers, empty if valid.
        """
        violations: list[str] = []
        
        if self.ref_enforced:
            if self.phase_emitted not in ("REF", "MIX"):
                violations.append("L1")
        
        if self.boundary_crossed:
            if self.boundary_verdict != "crossed":
                violations.append("L2")
        
        if self.boundary_cross_attempted and not self.boundary_crossed:
            if self.boundary_verdict != "blocked":
                violations.append("L3")
        
        if self.authority_verdict != "pass" and self.boundary_verdict == "crossed":
            violations.append("L4")
        
        return violations


@dataclass
class PlanEvent:
    """Captures plan emission event for ledger linkage."""
    
    request_id: str
    session_id: str
    plan_hash: str
    timestamp_utc: str
    constitutional_phase_expected: str
    boundary_phrase: str
    authority_verdict: str
    terminal_posture: str
    mode: str = "shadow"
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": LedgerEventType.PLAN_EMITTED.value,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "plan_hash": self.plan_hash,
            "timestamp_utc": self.timestamp_utc,
            "constitutional_phase_expected": self.constitutional_phase_expected,
            "boundary_phrase": self.boundary_phrase,
            "authority_verdict": self.authority_verdict,
            "terminal_posture": self.terminal_posture,
            "mode": self.mode,
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PlanEvent":
        return cls(
            request_id=d["request_id"],
            session_id=d["session_id"],
            plan_hash=d["plan_hash"],
            timestamp_utc=d["timestamp_utc"],
            constitutional_phase_expected=d["constitutional_phase_expected"],
            boundary_phrase=d["boundary_phrase"],
            authority_verdict=d["authority_verdict"],
            terminal_posture=d["terminal_posture"],
            mode=d.get("mode", "shadow"),
        )


@dataclass
class DecisionEvent:
    """Captures decision emission event for ledger linkage."""
    
    request_id: str
    session_id: str
    plan_hash: str
    timestamp_utc: str
    decision_posture: str
    phase_emitted: str
    authority_verdict: str
    boundary_verdict: str
    boundary_crossed: bool
    reason_codes: list[str]
    mode: str = "shadow"
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": LedgerEventType.DECISION_EMITTED.value,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "plan_hash": self.plan_hash,
            "timestamp_utc": self.timestamp_utc,
            "decision_posture": self.decision_posture,
            "phase_emitted": self.phase_emitted,
            "authority_verdict": self.authority_verdict,
            "boundary_verdict": self.boundary_verdict,
            "boundary_crossed": self.boundary_crossed,
            "reason_codes": self.reason_codes,
            "mode": self.mode,
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "DecisionEvent":
        return cls(
            request_id=d["request_id"],
            session_id=d["session_id"],
            plan_hash=d["plan_hash"],
            timestamp_utc=d["timestamp_utc"],
            decision_posture=d["decision_posture"],
            phase_emitted=d["phase_emitted"],
            authority_verdict=d["authority_verdict"],
            boundary_verdict=d["boundary_verdict"],
            boundary_crossed=d["boundary_crossed"],
            reason_codes=d["reason_codes"],
            mode=d.get("mode", "shadow"),
        )


@dataclass
class ExecutionEvent:
    """Captures execution event for ledger linkage."""
    
    request_id: str
    session_id: str
    plan_hash: str
    timestamp_utc: str
    execution_outcome: str
    sandbox_id: str
    commands_executed: list[str]
    commands_blocked: list[str]
    exit_code: int | None
    duration_ms: int
    artifacts: list[str]
    mode: str = "shadow"
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": LedgerEventType.EXECUTION_COMPLETED.value,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "plan_hash": self.plan_hash,
            "timestamp_utc": self.timestamp_utc,
            "execution_outcome": self.execution_outcome,
            "sandbox_id": self.sandbox_id,
            "commands_executed": self.commands_executed,
            "commands_blocked": self.commands_blocked,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "artifacts": self.artifacts,
            "mode": self.mode,
        }
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ExecutionEvent":
        return cls(
            request_id=d["request_id"],
            session_id=d["session_id"],
            plan_hash=d["plan_hash"],
            timestamp_utc=d["timestamp_utc"],
            execution_outcome=d["execution_outcome"],
            sandbox_id=d["sandbox_id"],
            commands_executed=d["commands_executed"],
            commands_blocked=d["commands_blocked"],
            exit_code=d.get("exit_code"),
            duration_ms=d["duration_ms"],
            artifacts=d["artifacts"],
            mode=d.get("mode", "shadow"),
        )


@dataclass
class ReplaySession:
    """
    Reconstructed session from ledger rows for audit/replay.
    
    Contains all events for a single request_id in chronological order.
    """
    
    request_id: str
    session_id: str
    plan_hash: str
    events: list[dict[str, Any]] = field(default_factory=list)
    ledger_rows: list[LedgerRowV1] = field(default_factory=list)
    plan_event: PlanEvent | None = None
    decision_event: DecisionEvent | None = None
    execution_event: ExecutionEvent | None = None
    
    def is_complete(self) -> bool:
        """Check if session has plan + decision (minimum for complete session)."""
        return self.plan_event is not None and self.decision_event is not None
    
    def has_execution(self) -> bool:
        """Check if session includes execution phase."""
        return self.execution_event is not None
    
    def get_final_posture(self) -> str | None:
        """Get terminal posture from decision event."""
        if self.decision_event:
            return self.decision_event.decision_posture
        return None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "plan_hash": self.plan_hash,
            "events": self.events,
            "ledger_rows": [row.to_dict() for row in self.ledger_rows],
            "plan_event": self.plan_event.to_dict() if self.plan_event else None,
            "decision_event": self.decision_event.to_dict() if self.decision_event else None,
            "execution_event": self.execution_event.to_dict() if self.execution_event else None,
            "is_complete": self.is_complete(),
            "has_execution": self.has_execution(),
            "final_posture": self.get_final_posture(),
        }

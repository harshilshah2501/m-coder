"""
Deterministic Ledger Emitter — Runtime Emulator (M3.E0).

Emits ledger records for every runtime decision.
Append-only semantics. Deterministic field values.

Invariant: Every decision has a corresponding ledger row.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from runtime.plan_gate_stub.plan_gate import PlanDecision


@dataclass
class LedgerRow:
    """
    Ledger row record (ledger_row.v0.1 schema).
    
    Fields:
        event_id: Unique event identifier (deterministic hash)
        timestamp_utc: ISO-8601 timestamp
        request_id: Request identifier from event
        session_id: Session identifier
        mode: Execution mode (shadow/live)
        plan_hash: Hash linking to the plan
        phase_emitted: Constitutional phase (REF/CONF/DES)
        terminal_posture: Decision posture (refuse/bounded_allow/safe_execute)
        authority_verdict: pass/fail
        boundary_verdict: none/present/detected/crossed
        boundary_phrase: The boundary phrase (if any)
        boundary_crossed: Whether boundary was actually crossed
        reason_codes: List of reason codes for the decision
    """
    event_id: str
    timestamp_utc: str
    request_id: str
    session_id: str
    mode: str
    plan_hash: str
    phase_emitted: str
    terminal_posture: str
    authority_verdict: str
    boundary_verdict: str
    boundary_phrase: str
    boundary_crossed: bool
    reason_codes: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "schema_version": "ledger_row.v0.1",
            "event": {
                "event_id": self.event_id,
                "timestamp_utc": self.timestamp_utc,
                "request_id": self.request_id,
                "session_id": self.session_id,
                "mode": self.mode,
            },
            "plan_link": {
                "plan_hash": self.plan_hash,
            },
            "verdicts": {
                "phase_emitted": self.phase_emitted,
                "terminal_posture": self.terminal_posture,
                "authority_verdict": self.authority_verdict,
                "boundary_verdict": self.boundary_verdict,
            },
            "boundary": {
                "irreversible_boundary_phrase": self.boundary_phrase,
                "boundary_crossed": self.boundary_crossed,
            },
            "reason_codes": self.reason_codes,
        }


def _canonical_json(obj: Any) -> bytes:
    """Stable JSON: sorted keys, UTF-8."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _derive_id(prefix: str, content: bytes) -> str:
    """Deterministic ID from content hash."""
    return f"{prefix}-{hashlib.sha256(content).hexdigest()[:32]}"


class LedgerEmitter:
    """
    Deterministic ledger emitter.
    
    Emits a ledger row for every decision.
    Uses deterministic hashing for event_id.
    """
    
    def __init__(self, fixed_time: str | None = None):
        """
        Initialize emitter.
        
        Args:
            fixed_time: Optional fixed timestamp for deterministic testing
        """
        self.fixed_time = fixed_time
    
    def emit(
        self,
        event: dict[str, Any],
        decision: "PlanDecision",
        plan: dict[str, Any],
    ) -> LedgerRow:
        """
        Emit a ledger row for the decision.
        
        Args:
            event: The original IDE event
            decision: The PlanDecision produced
            plan: The plan object
        
        Returns:
            LedgerRow with all fields populated
        """
        timestamp = self.fixed_time or datetime.now(timezone.utc).isoformat()
        
        request_id = event.get("request_id", "req-unknown")
        session_id = event.get("session_id", "sess-unknown")
        mode = event.get("mode", "shadow")
        
        event_content = _canonical_json({
            "event": event,
            "timestamp": timestamp,
        })
        event_id = _derive_id("evt", event_content)
        
        posture_map = {
            "REFUSAL": "refuse",
            "BOUNDED_ALLOW": "bounded_allow",
            "SAFE_EXECUTE": "safe_execute",
        }
        terminal_posture = posture_map.get(decision.decision.value, "refuse")
        
        boundary_crossed = decision.boundary_verdict.value == "crossed"
        
        return LedgerRow(
            event_id=event_id,
            timestamp_utc=timestamp,
            request_id=request_id,
            session_id=session_id,
            mode=mode,
            plan_hash=decision.plan_hash,
            phase_emitted=decision.phase.value,
            terminal_posture=terminal_posture,
            authority_verdict=decision.authority_verdict.value,
            boundary_verdict=decision.boundary_verdict.value,
            boundary_phrase=event.get("boundary_phrase", ""),
            boundary_crossed=boundary_crossed,
            reason_codes=decision.reason_codes,
        )

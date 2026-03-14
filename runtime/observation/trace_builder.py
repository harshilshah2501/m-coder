"""
M4.1 TraceBuilder — Build execution traces from ledger evidence.

Requirements:
- build_by_request_id(request_id) → ExecutionTrace
- build_by_canonical_hash(canonical_hash) → ExecutionTrace
- Deterministic ordering by timestamp_utc
- Backward compatible with older rows missing canonical_hash or intent_id
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from runtime.observation.models import (
    ExecutionTrace,
    TraceEvent,
)

if TYPE_CHECKING:
    from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore


# Event type to posture mapping
_EVENT_TYPE_TO_POSTURE = {
    "plangate_refused": "refused",
    "plangate_deferred": "deferred",
    "plangate_bounded_allow": "bounded_allow",
    "plangate_safe_execute": "safe_execute",
    "sandbox_refused": "refused",
    "sandbox_blocked": "blocked",
    "sandbox_executed": "executed",
}


def _extract_reason(payload: dict) -> str:
    """Extract reason from payload, falling back to empty string."""
    if "reason" in payload:
        return str(payload["reason"])
    if "refusal_reason" in payload:
        return str(payload["refusal_reason"])
    if "blocked_reason" in payload:
        return str(payload["blocked_reason"])
    if "decision_posture" in payload:
        return f"decision: {payload['decision_posture']}"
    return ""


def _row_to_trace_event(row) -> TraceEvent:
    """Convert a SandboxLedgerStore LedgerRow to TraceEvent."""
    payload = row.payload or {}
    
    posture = _EVENT_TYPE_TO_POSTURE.get(row.event_type, row.outcome_type)
    reason = _extract_reason(payload)
    
    canonical_hash = payload.get("canonical_hash", "")
    intent_id = payload.get("intent_id", "")
    backend = payload.get("backend", "")
    execution_surface = payload.get("execution_surface", "")
    exit_code = payload.get("exit_code")
    duration_ms = payload.get("duration_ms")
    
    return TraceEvent(
        event_id=row.ledger_row_id,
        event_type=row.event_type,
        timestamp_utc=row.timestamp_utc,
        request_id=row.request_id,
        plan_hash=row.plan_hash,
        posture=posture,
        reason=reason,
        canonical_hash=canonical_hash,
        intent_id=intent_id,
        backend=backend,
        execution_surface=execution_surface,
        exit_code=exit_code,
        duration_ms=duration_ms,
        payload=payload,
    )


class TraceBuilder:
    """
    Build execution traces from ledger evidence.
    
    Supports lookup by request_id or canonical_hash for auditing,
    debugging, and observability dashboards.
    """
    
    def __init__(self, ledger_store: "SandboxLedgerStore"):
        """
        Initialize TraceBuilder with a ledger store.
        
        Args:
            ledger_store: SandboxLedgerStore instance for ledger queries
        """
        self._store = ledger_store
    
    @classmethod
    def from_path(cls, ledger_path: Path | str) -> "TraceBuilder":
        """
        Create TraceBuilder from ledger database path.
        
        Args:
            ledger_path: Path to the SQLite ledger database
        """
        from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore
        store = SandboxLedgerStore(ledger_path)
        return cls(store)
    
    def build_by_request_id(self, request_id: str) -> ExecutionTrace:
        """
        Build execution trace for a single request_id.
        
        Events are ordered by timestamp_utc (deterministic).
        
        Args:
            request_id: The request identifier to trace
            
        Returns:
            ExecutionTrace containing all events for this request
        """
        rows = self._store.get_by_request_id(request_id)
        events = [_row_to_trace_event(row) for row in rows]
        
        # Sort by timestamp (deterministic ordering)
        events.sort(key=lambda e: e.timestamp_utc)
        
        # Build trace
        trace = ExecutionTrace(
            trace_id=request_id,
            lookup_type="request_id",
            events=events,
            total_events=len(events),
        )
        
        if events:
            trace.first_event_time = events[0].timestamp_utc
            trace.last_event_time = events[-1].timestamp_utc
            trace.final_posture = events[-1].posture
            
            # Extract canonical_hash if present in any event
            for event in events:
                if event.canonical_hash:
                    trace.canonical_hash = event.canonical_hash
                    break
        
        trace.request_ids = [request_id]
        return trace
    
    def build_by_canonical_hash(self, canonical_hash: str) -> ExecutionTrace:
        """
        Build execution trace for all events with a given canonical_hash.
        
        This may span multiple request_ids if the same canonical execution
        was replayed or retried.
        
        Events are ordered by timestamp_utc (deterministic).
        
        Args:
            canonical_hash: The canonical execution hash to trace
            
        Returns:
            ExecutionTrace containing all events with this canonical_hash
        """
        rows = self._store.get_by_canonical_hash(canonical_hash)
        events = [_row_to_trace_event(row) for row in rows]
        
        # Sort by timestamp (deterministic ordering)
        events.sort(key=lambda e: e.timestamp_utc)
        
        # Collect unique request_ids
        request_ids = list(dict.fromkeys(e.request_id for e in events))
        
        # Build trace
        trace = ExecutionTrace(
            trace_id=canonical_hash,
            lookup_type="canonical_hash",
            events=events,
            total_events=len(events),
            canonical_hash=canonical_hash,
            request_ids=request_ids,
        )
        
        if events:
            trace.first_event_time = events[0].timestamp_utc
            trace.last_event_time = events[-1].timestamp_utc
            trace.final_posture = events[-1].posture
        
        return trace
    
    def build_all_traces(self, limit: int = 100) -> list[ExecutionTrace]:
        """
        Build traces for all recent unique request_ids.
        
        Args:
            limit: Maximum number of traces to return
            
        Returns:
            List of ExecutionTraces, most recent first
        """
        rows = self._store.list_all()
        
        # Group by request_id
        request_ids_seen: dict[str, list] = {}
        for row in rows:
            if row.request_id not in request_ids_seen:
                request_ids_seen[row.request_id] = []
            request_ids_seen[row.request_id].append(row)
        
        # Build traces for each request_id
        traces = []
        for request_id in list(request_ids_seen.keys())[:limit]:
            trace = self.build_by_request_id(request_id)
            traces.append(trace)
        
        # Sort by latest event time (most recent first)
        traces.sort(key=lambda t: t.last_event_time or "", reverse=True)
        
        return traces[:limit]

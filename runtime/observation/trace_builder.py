"""
M4.1 TraceBuilder — Build execution traces from ledger evidence (C1 Execution Trace Builder).

Uses SandboxLedgerStore only. Deterministic ordering by timestamp_utc with tie-breaker.
C1 vocabulary: REFUSED, PLAN_DEFERRED, PLAN_BOUNDED, PLAN_APPROVED, EXECUTION_BLOCKED, EXECUTION_COMPLETED, UNKNOWN_EVENT.
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


# C1: raw production event type -> normalized trace vocabulary
_RAW_TO_NORMALIZED_EVENT = {
    "plangate_refused": "REFUSED",
    "plangate_deferred": "PLAN_DEFERRED",
    "plangate_bounded_allow": "PLAN_BOUNDED",
    "plangate_safe_execute": "PLAN_APPROVED",
    "sandbox_refused": "REFUSED",
    "sandbox_blocked": "EXECUTION_BLOCKED",
    "sandbox_executed": "EXECUTION_COMPLETED",
}
UNKNOWN_EVENT = "UNKNOWN_EVENT"

# Posture / outcome (lowercase) for backward compatibility
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
    """Convert a SandboxLedgerStore LedgerRow to TraceEvent (C1 vocabulary + metadata)."""
    payload = row.payload or {}
    raw_event = row.event_type

    normalized_event = _RAW_TO_NORMALIZED_EVENT.get(raw_event, UNKNOWN_EVENT)
    metadata: dict = {"raw_event_type": raw_event}
    if normalized_event == UNKNOWN_EVENT:
        metadata["raw_event_type"] = raw_event

    posture = _EVENT_TYPE_TO_POSTURE.get(raw_event, row.outcome_type)
    reason = _extract_reason(payload)

    canonical_hash = payload.get("canonical_hash", "")
    intent_id = payload.get("intent_id", "")
    backend = payload.get("backend", "")
    execution_surface = payload.get("execution_surface", "normal")
    exit_code = payload.get("exit_code")
    duration_ms = payload.get("duration_ms")

    return TraceEvent(
        event_id=row.ledger_row_id,
        event_type=normalized_event,
        timestamp_utc=row.timestamp_utc,
        request_id=row.request_id,
        plan_hash=row.plan_hash or "",
        posture=posture,
        reason=reason,
        canonical_hash=canonical_hash,
        intent_id=intent_id,
        task_id=row.request_id,
        backend=backend,
        execution_surface=execution_surface,
        exit_code=exit_code,
        duration_ms=duration_ms,
        metadata=metadata,
        payload=payload,
    )


def _sort_events_deterministic(events: list[TraceEvent]) -> None:
    """Sort by timestamp_utc ascending, then event_id as tie-breaker (in-place)."""
    events.sort(key=lambda e: (e.timestamp_utc, e.event_id))


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

        Events ordered by timestamp_utc ascending, then event_id tie-breaker.
        Sets started_at, ended_at, is_replay from payload.execution_surface.
        """
        return self.build_from_request_id(request_id)

    def build_from_request_id(self, request_id: str) -> ExecutionTrace:
        """
        C1: Build execution trace for a single request_id.

        Fetches rows from SandboxLedgerStore, sorts deterministically,
        maps to trace events, derives started_at, ended_at, canonical_hash, is_replay.
        """
        rows = self._store.get_by_request_id(request_id)
        events = [_row_to_trace_event(row) for row in rows]
        _sort_events_deterministic(events)

        trace = ExecutionTrace(
            trace_id=request_id,
            lookup_type="request_id",
            events=events,
            total_events=len(events),
            request_id=request_id,
            request_ids=[request_id],
        )
        if events:
            trace.first_event_time = events[0].timestamp_utc
            trace.last_event_time = events[-1].timestamp_utc
            trace.started_at = events[0].timestamp_utc
            trace.ended_at = events[-1].timestamp_utc
            trace.final_posture = events[-1].posture
            trace.is_replay = any(e.execution_surface == "replay" for e in events)
            for event in events:
                if event.canonical_hash:
                    trace.canonical_hash = event.canonical_hash
                    break
        return trace

    def build_by_canonical_hash(self, canonical_hash: str) -> ExecutionTrace:
        """
        Build execution trace by canonical_hash.

        C1 v1: When multiple request groups exist, selects the latest request group only.
        Does not merge original + replay. Events ordered deterministically.
        """
        return self.build_from_canonical_hash(canonical_hash)

    def build_from_canonical_hash(self, canonical_hash: str) -> ExecutionTrace:
        """
        C1: Build execution trace by canonical_hash.

        Fetches rows by canonical_hash. If multiple request_ids exist, selects
        the latest request group only (by max timestamp_utc in that group).
        Sets is_replay if any selected row has payload.execution_surface == "replay".
        """
        rows = self._store.get_by_canonical_hash(canonical_hash)
        if not rows:
            return ExecutionTrace(
                trace_id=canonical_hash,
                lookup_type="canonical_hash",
                events=[],
                total_events=0,
                canonical_hash=canonical_hash,
                request_ids=[],
            )

        # Group by request_id; pick latest request group (max last timestamp)
        by_request: dict[str, list] = {}
        for row in rows:
            by_request.setdefault(row.request_id, []).append(row)
        latest_request_id = max(
            by_request.keys(),
            key=lambda rid: max(r.timestamp_utc for r in by_request[rid]),
        )
        selected_rows = by_request[latest_request_id]
        events = [_row_to_trace_event(row) for row in selected_rows]
        _sort_events_deterministic(events)

        trace = ExecutionTrace(
            trace_id=canonical_hash,
            lookup_type="canonical_hash",
            events=events,
            total_events=len(events),
            request_id=latest_request_id,
            canonical_hash=canonical_hash,
            request_ids=[latest_request_id],
        )
        if events:
            trace.first_event_time = events[0].timestamp_utc
            trace.last_event_time = events[-1].timestamp_utc
            trace.started_at = events[0].timestamp_utc
            trace.ended_at = events[-1].timestamp_utc
            trace.final_posture = events[-1].posture
            trace.is_replay = any(e.execution_surface == "replay" for e in events)
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

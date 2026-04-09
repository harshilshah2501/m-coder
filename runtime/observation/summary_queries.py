"""
M4.1 Runtime Summary Queries — Aggregate statistics for observability.

Requirements:
- Total requests
- Refused / deferred / bounded_allow / executed distribution
- Top refusal reasons
- Backend distribution
- Replay count
- Unique canonical hashes
- Recent events

NOTE: Posture counts are EVENT-BASED, not request-final-state based.
A single request may emit multiple events (e.g., plangate_safe_execute + sandbox_executed),
so the posture distribution reflects event occurrences, not finalized request outcomes.
For request outcome distribution, group by request_id and take the final event per request.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from runtime.observation.models import (
    RuntimeSummary,
    PostureDistribution,
    RefusalSummary,
    BackendDistribution,
    TraceEvent,
)
from runtime.observation.trace_builder import _row_to_trace_event

if TYPE_CHECKING:
    from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore


# Event types that indicate refusal
_REFUSAL_EVENT_TYPES = {"plangate_refused", "sandbox_refused"}

# Event types that indicate execution
_EXECUTION_EVENT_TYPES = {"sandbox_executed"}


class RuntimeSummaryQueries:
    """
    Aggregate query interface for runtime observability.
    
    Provides statistical summaries of runtime behavior for dashboards,
    audits, and drift detection.
    """
    
    def __init__(self, ledger_store: "SandboxLedgerStore"):
        """
        Initialize with a ledger store.
        
        Args:
            ledger_store: SandboxLedgerStore instance
        """
        self._store = ledger_store
    
    @classmethod
    def from_path(cls, ledger_path: Path | str) -> "RuntimeSummaryQueries":
        """
        Create from ledger database path.
        
        Args:
            ledger_path: Path to the SQLite ledger database
        """
        from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore
        store = SandboxLedgerStore(ledger_path)
        return cls(store)
    
    def get_summary(
        self,
        top_refusals_limit: int = 10,
        recent_events_limit: int = 20,
    ) -> RuntimeSummary:
        """
        Get comprehensive runtime summary.
        
        Args:
            top_refusals_limit: Max number of top refusal reasons to return
            recent_events_limit: Max number of recent events to return
            
        Returns:
            RuntimeSummary with aggregated statistics
        """
        rows = self._store.list_all()
        
        if not rows:
            return RuntimeSummary()
        
        # Counters
        request_ids: set[str] = set()
        canonical_hashes: set[str] = set()
        posture_counts: Counter[str] = Counter()
        refusal_reasons: Counter[str] = Counter()
        refusal_examples: dict[str, str] = {}
        backend_counts: Counter[str] = Counter()
        backend_success: Counter[str] = Counter()
        backend_failure: Counter[str] = Counter()
        
        # Track events for time range and recent
        events: list[TraceEvent] = []
        
        for row in rows:
            request_ids.add(row.request_id)
            payload = row.payload or {}
            
            # Canonical hash tracking
            canonical_hash = payload.get("canonical_hash", "")
            if canonical_hash:
                canonical_hashes.add(canonical_hash)
            
            # Posture counting
            event_type = row.event_type
            if event_type == "plangate_refused":
                posture_counts["refused"] += 1
            elif event_type == "plangate_deferred":
                posture_counts["deferred"] += 1
            elif event_type == "plangate_bounded_allow":
                posture_counts["bounded_allow"] += 1
            elif event_type == "plangate_safe_execute":
                posture_counts["safe_execute"] += 1
            elif event_type == "sandbox_executed":
                posture_counts["executed"] += 1
            elif event_type == "sandbox_blocked":
                posture_counts["blocked"] += 1
            elif event_type == "sandbox_refused":
                posture_counts["refused"] += 1
            
            # Refusal reason tracking
            if event_type in _REFUSAL_EVENT_TYPES:
                reason = payload.get("reason", "") or payload.get("refusal_reason", "") or "unknown"
                refusal_reasons[reason] += 1
                if reason not in refusal_examples:
                    refusal_examples[reason] = row.request_id
            
            # Backend tracking
            if event_type in _EXECUTION_EVENT_TYPES:
                backend = payload.get("backend", "local_process")
                backend_counts[backend] += 1
                exit_code = payload.get("exit_code")
                if exit_code == 0:
                    backend_success[backend] += 1
                elif exit_code is not None:
                    backend_failure[backend] += 1
            
            # Convert to TraceEvent for recent events
            events.append(_row_to_trace_event(row))
        
        # Sort events by timestamp
        events.sort(key=lambda e: e.timestamp_utc)
        
        # Calculate replay count (canonical_hashes with multiple request_ids)
        replay_count = self._calculate_replay_count(rows)
        
        # Build posture distribution
        postures = PostureDistribution(
            refused=posture_counts.get("refused", 0),
            deferred=posture_counts.get("deferred", 0),
            bounded_allow=posture_counts.get("bounded_allow", 0),
            safe_execute=posture_counts.get("safe_execute", 0),
            executed=posture_counts.get("executed", 0),
            blocked=posture_counts.get("blocked", 0),
        )
        
        # Build top refusal reasons
        top_refusals = [
            RefusalSummary(
                reason=reason,
                count=count,
                example_request_id=refusal_examples.get(reason, ""),
            )
            for reason, count in refusal_reasons.most_common(top_refusals_limit)
        ]
        
        # Build backend distribution
        backend_dist = [
            BackendDistribution(
                backend=backend,
                count=count,
                success_count=backend_success.get(backend, 0),
                failure_count=backend_failure.get(backend, 0),
            )
            for backend, count in backend_counts.most_common()
        ]
        
        # Recent events (most recent first)
        recent_events = list(reversed(events[-recent_events_limit:]))
        
        return RuntimeSummary(
            total_requests=len(request_ids),
            total_events=len(rows),
            unique_canonical_hashes=len(canonical_hashes),
            replay_count=replay_count,
            postures=postures,
            top_refusal_reasons=top_refusals,
            backend_distribution=backend_dist,
            earliest_event=events[0].timestamp_utc if events else "",
            latest_event=events[-1].timestamp_utc if events else "",
            recent_events=recent_events,
        )
    
    def _calculate_replay_count(self, rows) -> int:
        """
        Calculate number of replayed executions.
        
        A replay is when the same canonical_hash appears with different request_ids.
        """
        hash_to_requests: dict[str, set[str]] = {}
        
        for row in rows:
            payload = row.payload or {}
            canonical_hash = payload.get("canonical_hash", "")
            if canonical_hash:
                if canonical_hash not in hash_to_requests:
                    hash_to_requests[canonical_hash] = set()
                hash_to_requests[canonical_hash].add(row.request_id)
        
        # Count hashes that have more than one request_id
        return sum(1 for requests in hash_to_requests.values() if len(requests) > 1)
    
    def get_posture_distribution(self) -> PostureDistribution:
        """Get just the posture distribution."""
        summary = self.get_summary(top_refusals_limit=0, recent_events_limit=0)
        return summary.postures
    
    def get_top_refusal_reasons(self, limit: int = 10) -> list[RefusalSummary]:
        """Get top refusal reasons."""
        summary = self.get_summary(top_refusals_limit=limit, recent_events_limit=0)
        return summary.top_refusal_reasons
    
    def get_backend_distribution(self) -> list[BackendDistribution]:
        """Get backend distribution."""
        summary = self.get_summary(top_refusals_limit=0, recent_events_limit=0)
        return summary.backend_distribution
    
    def get_recent_events(self, limit: int = 20) -> list[TraceEvent]:
        """Get most recent events."""
        summary = self.get_summary(top_refusals_limit=0, recent_events_limit=limit)
        return summary.recent_events
    
    def count_total_requests(self) -> int:
        """Get total unique request count."""
        rows = self._store.list_all()
        return len(set(row.request_id for row in rows))
    
    def count_unique_canonical_hashes(self) -> int:
        """Get count of unique canonical hashes."""
        rows = self._store.list_all()
        hashes = set()
        for row in rows:
            payload = row.payload or {}
            h = payload.get("canonical_hash", "")
            if h:
                hashes.add(h)
        return len(hashes)

"""
M4.1 Observability Models — Data structures for traces, summaries, and explanations.

Invariants:
- TraceEvent and ExplanationPayload are frozen (immutable after creation)
- ExecutionTrace and RuntimeSummary are mutable containers for building results
- Timestamps in UTC ISO-8601 format
- Deterministic serialization for comparison
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TraceEvent:
    """
    Single event in an execution trace.

    Unified representation covering Plan-Gate decisions and sandbox outcomes.
    event_type uses C1 normalized vocabulary (REFUSED, PLAN_APPROVED, etc.).
    Raw ledger event type is in metadata["raw_event_type"] when needed.
    """

    event_id: str
    event_type: str  # C1 vocabulary: REFUSED, PLAN_DEFERRED, PLAN_BOUNDED, PLAN_APPROVED, EXECUTION_BLOCKED, EXECUTION_COMPLETED, UNKNOWN_EVENT
    timestamp_utc: str
    request_id: str
    plan_hash: str

    # Posture / outcome (lowercase for backward compat)
    posture: str  # refuse, defer, bounded_allow, safe_execute, executed, blocked
    reason: str

    # Execution identity (M4.1 canonical intent)
    canonical_hash: str = ""
    intent_id: str = ""

    # Optional task id (same as request_id when single-request trace)
    task_id: str = ""

    # Backend / execution surface (default "normal"; "replay" when replay)
    backend: str = ""
    execution_surface: str = ""

    # Outcome details
    exit_code: int | None = None
    duration_ms: int | None = None

    # Minimal metadata (e.g. raw_event_type for unknown events)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Full payload for detailed inspection
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp_utc": self.timestamp_utc,
            "request_id": self.request_id,
            "plan_hash": self.plan_hash,
            "posture": self.posture,
            "reason": self.reason,
            "canonical_hash": self.canonical_hash,
            "intent_id": self.intent_id,
            "task_id": self.task_id,
            "backend": self.backend,
            "execution_surface": self.execution_surface,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "payload": self.payload,
        }


@dataclass
class ExecutionTrace:
    """
    Complete execution trace for a single request or canonical execution.

    Events are ordered by timestamp_utc (deterministic).
    C1: request_id, started_at, ended_at, is_replay; first_event_time/last_event_time kept for backward compat.
    """

    trace_id: str  # request_id or canonical_hash used for lookup
    lookup_type: str  # "request_id" or "canonical_hash"
    events: list[TraceEvent] = field(default_factory=list)

    # Derived summary
    total_events: int = 0
    first_event_time: str = ""
    last_event_time: str = ""
    final_posture: str = ""

    # C1: primary request and time range
    request_id: str = ""
    started_at: str = ""
    ended_at: str = ""
    is_replay: bool = False

    # Execution identity if available
    canonical_hash: str = ""
    request_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "lookup_type": self.lookup_type,
            "events": [e.to_dict() for e in self.events],
            "total_events": self.total_events,
            "first_event_time": self.first_event_time,
            "last_event_time": self.last_event_time,
            "final_posture": self.final_posture,
            "request_id": self.request_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "is_replay": self.is_replay,
            "canonical_hash": self.canonical_hash,
            "request_ids": self.request_ids,
        }


@dataclass(frozen=True)
class PostureDistribution:
    """Distribution of postures across requests."""
    
    refused: int = 0
    deferred: int = 0
    bounded_allow: int = 0
    safe_execute: int = 0
    executed: int = 0
    blocked: int = 0
    
    def to_dict(self) -> dict[str, int]:
        return {
            "refused": self.refused,
            "deferred": self.deferred,
            "bounded_allow": self.bounded_allow,
            "safe_execute": self.safe_execute,
            "executed": self.executed,
            "blocked": self.blocked,
        }
    
    @property
    def total(self) -> int:
        return (
            self.refused + self.deferred + self.bounded_allow +
            self.safe_execute + self.executed + self.blocked
        )


@dataclass(frozen=True)
class RefusalSummary:
    """Summary of a single refusal reason."""
    
    reason: str
    count: int
    example_request_id: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "reason": self.reason,
            "count": self.count,
            "example_request_id": self.example_request_id,
        }


@dataclass(frozen=True)
class BackendDistribution:
    """Distribution of executions by backend."""
    
    backend: str
    count: int
    success_count: int = 0
    failure_count: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "count": self.count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }


@dataclass
class RuntimeSummary:
    """
    Aggregate runtime summary for observability dashboards.
    
    Captures totals, posture distribution, top refusals, and backend usage.
    """
    
    # Totals
    total_requests: int = 0
    total_events: int = 0
    unique_canonical_hashes: int = 0
    replay_count: int = 0
    
    # Posture distribution
    postures: PostureDistribution = field(default_factory=PostureDistribution)
    
    # Top refusal reasons (sorted by count desc)
    top_refusal_reasons: list[RefusalSummary] = field(default_factory=list)
    
    # Backend distribution
    backend_distribution: list[BackendDistribution] = field(default_factory=list)
    
    # Time range
    earliest_event: str = ""
    latest_event: str = ""
    
    # Recent events (for dashboard preview)
    recent_events: list[TraceEvent] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "total_events": self.total_events,
            "unique_canonical_hashes": self.unique_canonical_hashes,
            "replay_count": self.replay_count,
            "postures": self.postures.to_dict(),
            "top_refusal_reasons": [r.to_dict() for r in self.top_refusal_reasons],
            "backend_distribution": [b.to_dict() for b in self.backend_distribution],
            "earliest_event": self.earliest_event,
            "latest_event": self.latest_event,
            "recent_events": [e.to_dict() for e in self.recent_events],
        }


class ExplanationNotFoundError(Exception):
    """Raised when an explanation is requested but no trace evidence exists."""

    pass


@dataclass(frozen=True)
class ExecutionExplanation:
    """
    C2: Deterministic execution explanation derived from C1 trace evidence only.

    Answers: What was the final outcome? What factors caused it? Was this replay?
    """

    request_id: str | None
    canonical_hash: str | None
    final_outcome: str  # REFUSED, PLAN_DEFERRED, PLAN_BOUNDED, EXECUTION_BLOCKED, EXECUTION_COMPLETED, UNKNOWN_EVENT
    summary: str
    decisive_factors: tuple[str, ...]
    evidence_refs: tuple[str, ...]  # e.g. ("event[0]", "event[1]")
    is_replay: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "canonical_hash": self.canonical_hash,
            "final_outcome": self.final_outcome,
            "summary": self.summary,
            "decisive_factors": list(self.decisive_factors),
            "evidence_refs": list(self.evidence_refs),
            "is_replay": self.is_replay,
        }


@dataclass(frozen=True)
class ExplanationPayload:
    """
    Human-readable explanation payload for plugin / UI consumption.
    
    Provides concise explanation of what happened and why.
    """
    
    # Decision summary
    decision: str  # "refused", "deferred", "bounded_allow", "safe_execute", "executed", "blocked"
    outcome: str  # Human-readable outcome description
    reason: str  # Why this decision was made
    
    # Execution identity
    canonical_hash: str = ""
    request_id: str = ""
    
    # Backend and surface
    backend: str = ""
    execution_surface: str = ""
    
    # Concise human-readable explanation (one sentence)
    explanation: str = ""
    
    # Additional context (optional)
    exit_code: int | None = None
    duration_ms: int | None = None
    artifacts: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "outcome": self.outcome,
            "reason": self.reason,
            "canonical_hash": self.canonical_hash,
            "request_id": self.request_id,
            "backend": self.backend,
            "execution_surface": self.execution_surface,
            "explanation": self.explanation,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "artifacts": list(self.artifacts),
        }

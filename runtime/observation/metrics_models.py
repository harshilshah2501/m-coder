"""
Metrics Models — M4.6 data structures for runtime performance metrics.

Deterministic, read-only report structures for runtime health and invariance behavior.
All fields derived from ledger evidence. No side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PostureCounts:
    """
    Counts of Plan-Gate posture decisions.
    
    Reflects governance decision distribution over the ledger.
    """
    
    refuse: int = 0
    defer: int = 0
    bounded_allow: int = 0
    safe_execute: int = 0
    
    @property
    def total(self) -> int:
        """Total Plan-Gate decisions."""
        return self.refuse + self.defer + self.bounded_allow + self.safe_execute
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "refuse": self.refuse,
            "defer": self.defer,
            "bounded_allow": self.bounded_allow,
            "safe_execute": self.safe_execute,
            "total": self.total,
        }


@dataclass
class ExecutionCounts:
    """
    Counts of sandbox execution outcomes.
    
    executed: sandbox ran to completion (success or error exit)
    blocked: sandbox refused to run (policy violation, missing runtime)
    refused: Plan-Gate refused before sandbox (overlaps with posture.refuse)
    """
    
    executed: int = 0
    blocked: int = 0
    refused: int = 0
    
    @property
    def total(self) -> int:
        """Total execution attempts."""
        return self.executed + self.blocked + self.refused
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "executed": self.executed,
            "blocked": self.blocked,
            "refused": self.refused,
            "total": self.total,
        }


@dataclass
class BackendDistribution:
    """
    Distribution of execution across sandbox backends.
    
    Tracks which backend (local_process, container, etc.) handled each execution.
    """
    
    counts: dict[str, int] = field(default_factory=dict)
    
    def increment(self, backend: str) -> None:
        """Increment count for a backend."""
        self.counts[backend] = self.counts.get(backend, 0) + 1
    
    @property
    def total(self) -> int:
        """Total executions across all backends."""
        return sum(self.counts.values())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "counts": dict(self.counts),
            "total": self.total,
        }


@dataclass
class CanonicalHashReuse:
    """
    Metrics on canonical_hash reuse for replay and deduplication.
    
    unique_hashes: number of distinct canonical_hash values
    reused_hashes: number of canonical_hash values seen more than once
    total_rows_with_hash: total rows that have a canonical_hash
    max_reuse_count: maximum times a single canonical_hash was seen
    """
    
    unique_hashes: int = 0
    reused_hashes: int = 0
    total_rows_with_hash: int = 0
    max_reuse_count: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "unique_hashes": self.unique_hashes,
            "reused_hashes": self.reused_hashes,
            "total_rows_with_hash": self.total_rows_with_hash,
            "max_reuse_count": self.max_reuse_count,
        }


@dataclass
class LatencySummary:
    """
    Summary statistics for latency (when available from ledger).
    
    All values in milliseconds. None if no data available.
    """
    
    count: int = 0
    min_ms: int | None = None
    max_ms: int | None = None
    avg_ms: float | None = None
    p50_ms: int | None = None
    p95_ms: int | None = None
    p99_ms: int | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "avg_ms": round(self.avg_ms, 2) if self.avg_ms is not None else None,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
        }


@dataclass
class ReplayCounts:
    """
    Counts related to execution replay.
    
    replay_requests: total replay attempts
    replay_succeeded: replays that completed successfully
    replay_failed: replays that failed (intent not found, policy blocked)
    """
    
    replay_requests: int = 0
    replay_succeeded: int = 0
    replay_failed: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "replay_requests": self.replay_requests,
            "replay_succeeded": self.replay_succeeded,
            "replay_failed": self.replay_failed,
        }


@dataclass
class CollapseSummary:
    """
    Summary of mismatch/collapse events (if tracked by M4.3).
    
    mismatch_count: times canonical_hash mismatch was detected
    collapse_count: times execution collapsed due to invariant violation
    boundary_blocked: times boundary crossing was blocked
    """
    
    mismatch_count: int = 0
    collapse_count: int = 0
    boundary_blocked: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "mismatch_count": self.mismatch_count,
            "collapse_count": self.collapse_count,
            "boundary_blocked": self.boundary_blocked,
        }


@dataclass
class InvariantHealth:
    """
    Health metrics for runtime invariants.
    
    violations_detected: count of invariant violations found in ledger
    violation_types: breakdown by violation type (L1, L2, L3, L4, etc.)
    ref_enforced_count: times REF dominance was enforced
    boundary_cross_attempted: times boundary cross was attempted
    boundary_cross_blocked: times boundary cross was blocked (should equal attempted)
    """
    
    violations_detected: int = 0
    violation_types: dict[str, int] = field(default_factory=dict)
    ref_enforced_count: int = 0
    boundary_cross_attempted: int = 0
    boundary_cross_blocked: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "violations_detected": self.violations_detected,
            "violation_types": dict(self.violation_types),
            "ref_enforced_count": self.ref_enforced_count,
            "boundary_cross_attempted": self.boundary_cross_attempted,
            "boundary_cross_blocked": self.boundary_cross_blocked,
        }


@dataclass
class RuntimeMetricsReport:
    """
    Complete runtime performance metrics report.
    
    Aggregates all metrics from ledger evidence. Deterministic and read-only.
    """
    
    total_requests: int = 0
    unique_sessions: int = 0
    unique_request_ids: int = 0
    posture_counts: PostureCounts = field(default_factory=PostureCounts)
    execution_counts: ExecutionCounts = field(default_factory=ExecutionCounts)
    backend_distribution: BackendDistribution = field(default_factory=BackendDistribution)
    canonical_hash_reuse: CanonicalHashReuse = field(default_factory=CanonicalHashReuse)
    latency_summary: LatencySummary = field(default_factory=LatencySummary)
    replay_counts: ReplayCounts = field(default_factory=ReplayCounts)
    collapse_summary: CollapseSummary = field(default_factory=CollapseSummary)
    invariant_health: InvariantHealth = field(default_factory=InvariantHealth)
    ledger_row_count: int = 0
    report_timestamp_utc: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "unique_sessions": self.unique_sessions,
            "unique_request_ids": self.unique_request_ids,
            "posture_counts": self.posture_counts.to_dict(),
            "execution_counts": self.execution_counts.to_dict(),
            "backend_distribution": self.backend_distribution.to_dict(),
            "canonical_hash_reuse": self.canonical_hash_reuse.to_dict(),
            "latency_summary": self.latency_summary.to_dict(),
            "replay_counts": self.replay_counts.to_dict(),
            "collapse_summary": self.collapse_summary.to_dict(),
            "invariant_health": self.invariant_health.to_dict(),
            "ledger_row_count": self.ledger_row_count,
            "report_timestamp_utc": self.report_timestamp_utc,
        }

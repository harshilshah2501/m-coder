"""
Runtime Metrics Service — M4.6 deterministic metrics query layer.

Provides operational visibility into runtime health and invariance behavior.
Read-only over ledger evidence. No external telemetry pipelines. No side effects.

Dependencies:
- M4.1: canonical_hash indexed column, ledger identity propagation
- Ledger stores: SandboxLedgerStore, LedgerStore
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from runtime.observation.metrics_models import (
    BackendDistribution,
    CanonicalHashReuse,
    CollapseSummary,
    ExecutionCounts,
    InvariantHealth,
    LatencySummary,
    PostureCounts,
    ReplayCounts,
    RuntimeMetricsReport,
)

if TYPE_CHECKING:
    from runtime.ledger.store import LedgerStore
    from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore


class RuntimeMetricsService:
    """
    Deterministic metrics query service over ledger evidence.
    
    Reads from SandboxLedgerStore and optionally LedgerStore to compute
    runtime performance metrics. All operations are read-only.
    """
    
    def __init__(
        self,
        sandbox_ledger_store: SandboxLedgerStore | None = None,
        ledger_store: LedgerStore | None = None,
        sandbox_ledger_path: Path | str | None = None,
        ledger_path: Path | str | None = None,
    ) -> None:
        """
        Initialize metrics service with ledger stores or paths.
        
        Args:
            sandbox_ledger_store: Optional SandboxLedgerStore instance.
            ledger_store: Optional LedgerStore instance.
            sandbox_ledger_path: Path to sandbox ledger SQLite file (fallback).
            ledger_path: Path to general ledger SQLite file (fallback).
        """
        self._sandbox_store = sandbox_ledger_store
        self._ledger_store = ledger_store
        self._sandbox_path = Path(sandbox_ledger_path) if sandbox_ledger_path else None
        self._ledger_path = Path(ledger_path) if ledger_path else None
    
    def _get_sandbox_connection(self) -> sqlite3.Connection | None:
        """Get connection to sandbox ledger, preferring store then path."""
        if self._sandbox_store is not None:
            return sqlite3.connect(self._sandbox_store.path)
        if self._sandbox_path is not None and self._sandbox_path.exists():
            return sqlite3.connect(self._sandbox_path)
        return None
    
    def _get_ledger_connection(self) -> sqlite3.Connection | None:
        """Get connection to general ledger, preferring store then path."""
        if self._ledger_store is not None:
            return sqlite3.connect(self._ledger_store.path)
        if self._ledger_path is not None and self._ledger_path.exists():
            return sqlite3.connect(self._ledger_path)
        return None
    
    def generate_report(self) -> RuntimeMetricsReport:
        """
        Generate complete runtime metrics report from ledger evidence.
        
        Reads from available ledger stores and computes all metrics.
        Deterministic: same ledger state produces same report.
        """
        report = RuntimeMetricsReport(
            report_timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        
        sandbox_conn = self._get_sandbox_connection()
        if sandbox_conn:
            try:
                self._populate_from_sandbox_ledger(sandbox_conn, report)
            finally:
                sandbox_conn.close()
        
        ledger_conn = self._get_ledger_connection()
        if ledger_conn:
            try:
                self._populate_from_general_ledger(ledger_conn, report)
            finally:
                ledger_conn.close()
        
        return report
    
    def _populate_from_sandbox_ledger(
        self,
        conn: sqlite3.Connection,
        report: RuntimeMetricsReport,
    ) -> None:
        """Populate metrics from sandbox_ledger table."""
        conn.row_factory = sqlite3.Row
        
        report.ledger_row_count += self._count_rows(conn, "sandbox_ledger")
        
        self._compute_posture_counts(conn, report)
        self._compute_execution_counts(conn, report)
        self._compute_backend_distribution(conn, report)
        self._compute_canonical_hash_reuse(conn, report)
        self._compute_replay_counts(conn, report)
        self._compute_unique_identifiers(conn, report)
    
    def _populate_from_general_ledger(
        self,
        conn: sqlite3.Connection,
        report: RuntimeMetricsReport,
    ) -> None:
        """Populate metrics from ledger_rows table."""
        conn.row_factory = sqlite3.Row
        
        report.ledger_row_count += self._count_rows(conn, "ledger_rows")
        
        self._compute_latency_summary(conn, report)
        self._compute_invariant_health(conn, report)
        self._compute_collapse_summary(conn, report)
    
    def _count_rows(self, conn: sqlite3.Connection, table: str) -> int:
        """Count total rows in a table."""
        try:
            cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
            return cur.fetchone()[0]
        except sqlite3.Error:
            return 0
    
    def _compute_posture_counts(
        self,
        conn: sqlite3.Connection,
        report: RuntimeMetricsReport,
    ) -> None:
        """Compute Plan-Gate posture distribution."""
        posture_map = {
            "plangate_refused": "refuse",
            "plangate_deferred": "defer",
            "plangate_bounded_allow": "bounded_allow",
            "plangate_safe_execute": "safe_execute",
        }
        
        try:
            cur = conn.execute(
                """
                SELECT event_type, COUNT(*) as cnt
                FROM sandbox_ledger
                WHERE event_type IN ('plangate_refused', 'plangate_deferred', 
                                     'plangate_bounded_allow', 'plangate_safe_execute')
                GROUP BY event_type
                """
            )
            for row in cur.fetchall():
                event_type = row[0]
                count = row[1]
                posture = posture_map.get(event_type)
                if posture == "refuse":
                    report.posture_counts.refuse = count
                elif posture == "defer":
                    report.posture_counts.defer = count
                elif posture == "bounded_allow":
                    report.posture_counts.bounded_allow = count
                elif posture == "safe_execute":
                    report.posture_counts.safe_execute = count
        except sqlite3.Error:
            pass
    
    def _compute_execution_counts(
        self,
        conn: sqlite3.Connection,
        report: RuntimeMetricsReport,
    ) -> None:
        """Compute sandbox execution outcome distribution."""
        try:
            cur = conn.execute(
                """
                SELECT outcome_type, COUNT(*) as cnt
                FROM sandbox_ledger
                WHERE event_type IN ('sandbox_refused', 'sandbox_blocked', 'sandbox_executed')
                GROUP BY outcome_type
                """
            )
            for row in cur.fetchall():
                outcome = row[0]
                count = row[1]
                if outcome == "executed":
                    report.execution_counts.executed = count
                elif outcome == "blocked":
                    report.execution_counts.blocked = count
                elif outcome == "refused":
                    report.execution_counts.refused = count
        except sqlite3.Error:
            pass
    
    def _compute_backend_distribution(
        self,
        conn: sqlite3.Connection,
        report: RuntimeMetricsReport,
    ) -> None:
        """Compute execution distribution across backends."""
        try:
            cur = conn.execute(
                """
                SELECT payload FROM sandbox_ledger
                WHERE event_type = 'sandbox_executed'
                """
            )
            for row in cur.fetchall():
                try:
                    payload = json.loads(row[0])
                    backend = payload.get("backend", "unknown")
                    if backend:
                        report.backend_distribution.increment(backend)
                except (json.JSONDecodeError, TypeError):
                    report.backend_distribution.increment("unknown")
        except sqlite3.Error:
            pass
    
    def _compute_canonical_hash_reuse(
        self,
        conn: sqlite3.Connection,
        report: RuntimeMetricsReport,
    ) -> None:
        """Compute canonical_hash reuse statistics."""
        try:
            cur = conn.execute(
                """
                SELECT canonical_hash, COUNT(*) as cnt
                FROM sandbox_ledger
                WHERE canonical_hash != '' AND canonical_hash IS NOT NULL
                GROUP BY canonical_hash
                """
            )
            hash_counts: list[int] = []
            for row in cur.fetchall():
                count = row[1]
                hash_counts.append(count)
            
            if hash_counts:
                report.canonical_hash_reuse.unique_hashes = len(hash_counts)
                report.canonical_hash_reuse.reused_hashes = sum(1 for c in hash_counts if c > 1)
                report.canonical_hash_reuse.total_rows_with_hash = sum(hash_counts)
                report.canonical_hash_reuse.max_reuse_count = max(hash_counts)
        except sqlite3.Error:
            pass
    
    def _compute_replay_counts(
        self,
        conn: sqlite3.Connection,
        report: RuntimeMetricsReport,
    ) -> None:
        """Compute replay-related metrics from payload metadata."""
        try:
            cur = conn.execute(
                """
                SELECT payload FROM sandbox_ledger
                WHERE event_type = 'sandbox_executed'
                """
            )
            for row in cur.fetchall():
                try:
                    payload = json.loads(row[0])
                    execution_surface = payload.get("execution_surface", "")
                    if execution_surface == "replay":
                        report.replay_counts.replay_requests += 1
                        exit_code = payload.get("exit_code")
                        if exit_code == 0:
                            report.replay_counts.replay_succeeded += 1
                        else:
                            report.replay_counts.replay_failed += 1
                except (json.JSONDecodeError, TypeError):
                    pass
        except sqlite3.Error:
            pass
    
    def _compute_unique_identifiers(
        self,
        conn: sqlite3.Connection,
        report: RuntimeMetricsReport,
    ) -> None:
        """Compute unique session and request counts."""
        try:
            cur = conn.execute(
                "SELECT COUNT(DISTINCT request_id) FROM sandbox_ledger"
            )
            result = cur.fetchone()
            if result:
                report.unique_request_ids = result[0]
                report.total_requests = result[0]
            
            cur = conn.execute(
                "SELECT COUNT(DISTINCT sandbox_id) FROM sandbox_ledger WHERE sandbox_id != ''"
            )
            result = cur.fetchone()
            if result:
                report.unique_sessions = result[0]
        except sqlite3.Error:
            pass
    
    def _compute_latency_summary(
        self,
        conn: sqlite3.Connection,
        report: RuntimeMetricsReport,
    ) -> None:
        """Compute latency statistics from ledger_rows payload."""
        latencies: list[int] = []
        try:
            cur = conn.execute("SELECT payload FROM ledger_rows")
            for row in cur.fetchall():
                try:
                    payload = json.loads(row[0])
                    metrics = payload.get("metrics", {})
                    latency = metrics.get("latency_ms")
                    if latency is not None and isinstance(latency, (int, float)):
                        latencies.append(int(latency))
                except (json.JSONDecodeError, TypeError, KeyError):
                    pass
        except sqlite3.Error:
            pass
        
        if latencies:
            latencies.sort()
            n = len(latencies)
            report.latency_summary.count = n
            report.latency_summary.min_ms = latencies[0]
            report.latency_summary.max_ms = latencies[-1]
            report.latency_summary.avg_ms = sum(latencies) / n
            report.latency_summary.p50_ms = latencies[n // 2]
            report.latency_summary.p95_ms = latencies[int(n * 0.95)] if n >= 20 else latencies[-1]
            report.latency_summary.p99_ms = latencies[int(n * 0.99)] if n >= 100 else latencies[-1]
    
    def _compute_invariant_health(
        self,
        conn: sqlite3.Connection,
        report: RuntimeMetricsReport,
    ) -> None:
        """Compute invariant health metrics from ledger_rows."""
        try:
            cur = conn.execute("SELECT payload FROM ledger_rows")
            for row in cur.fetchall():
                try:
                    payload = json.loads(row[0])
                    verdicts = payload.get("verdicts", {})
                    boundary = payload.get("boundary", {})
                    
                    if verdicts.get("ref_enforced"):
                        report.invariant_health.ref_enforced_count += 1
                    
                    if boundary.get("boundary_cross_attempted"):
                        report.invariant_health.boundary_cross_attempted += 1
                        if not boundary.get("boundary_crossed"):
                            report.invariant_health.boundary_cross_blocked += 1
                    
                    routing = payload.get("routing_invariants", {})
                    if routing:
                        pass
                except (json.JSONDecodeError, TypeError):
                    pass
        except sqlite3.Error:
            pass
    
    def _compute_collapse_summary(
        self,
        conn: sqlite3.Connection,
        report: RuntimeMetricsReport,
    ) -> None:
        """Compute collapse/mismatch metrics from ledger_rows."""
        try:
            cur = conn.execute(
                """
                SELECT event_type, COUNT(*) as cnt
                FROM ledger_rows
                WHERE event_type IN ('boundary_blocked', 'execution_blocked')
                GROUP BY event_type
                """
            )
            for row in cur.fetchall():
                event_type = row[0]
                count = row[1]
                if event_type == "boundary_blocked":
                    report.collapse_summary.boundary_blocked = count
        except sqlite3.Error:
            pass
    
    def get_posture_distribution(self) -> PostureCounts:
        """Get Plan-Gate posture distribution only."""
        report = RuntimeMetricsReport()
        sandbox_conn = self._get_sandbox_connection()
        if sandbox_conn:
            try:
                self._compute_posture_counts(sandbox_conn, report)
            finally:
                sandbox_conn.close()
        return report.posture_counts
    
    def get_execution_distribution(self) -> ExecutionCounts:
        """Get sandbox execution outcome distribution only."""
        report = RuntimeMetricsReport()
        sandbox_conn = self._get_sandbox_connection()
        if sandbox_conn:
            try:
                self._compute_execution_counts(sandbox_conn, report)
            finally:
                sandbox_conn.close()
        return report.execution_counts
    
    def get_backend_distribution(self) -> BackendDistribution:
        """Get backend distribution only."""
        report = RuntimeMetricsReport()
        sandbox_conn = self._get_sandbox_connection()
        if sandbox_conn:
            try:
                self._compute_backend_distribution(sandbox_conn, report)
            finally:
                sandbox_conn.close()
        return report.backend_distribution
    
    def get_canonical_hash_metrics(self) -> CanonicalHashReuse:
        """Get canonical_hash reuse metrics only."""
        report = RuntimeMetricsReport()
        sandbox_conn = self._get_sandbox_connection()
        if sandbox_conn:
            try:
                self._compute_canonical_hash_reuse(sandbox_conn, report)
            finally:
                sandbox_conn.close()
        return report.canonical_hash_reuse
    
    def get_latency_summary(self) -> LatencySummary:
        """Get latency summary only."""
        report = RuntimeMetricsReport()
        ledger_conn = self._get_ledger_connection()
        if ledger_conn:
            try:
                self._compute_latency_summary(ledger_conn, report)
            finally:
                ledger_conn.close()
        return report.latency_summary
    
    def get_invariant_health(self) -> InvariantHealth:
        """Get invariant health metrics only."""
        report = RuntimeMetricsReport()
        ledger_conn = self._get_ledger_connection()
        if ledger_conn:
            try:
                self._compute_invariant_health(ledger_conn, report)
            finally:
                ledger_conn.close()
        return report.invariant_health
    
    def count_by_event_type(self, event_type: str) -> int:
        """Count ledger rows by event type in sandbox_ledger."""
        sandbox_conn = self._get_sandbox_connection()
        if not sandbox_conn:
            return 0
        try:
            cur = sandbox_conn.execute(
                "SELECT COUNT(*) FROM sandbox_ledger WHERE event_type = ?",
                (event_type,),
            )
            result = cur.fetchone()
            return result[0] if result else 0
        except sqlite3.Error:
            return 0
        finally:
            sandbox_conn.close()
    
    def count_by_outcome_type(self, outcome_type: str) -> int:
        """Count ledger rows by outcome type in sandbox_ledger."""
        sandbox_conn = self._get_sandbox_connection()
        if not sandbox_conn:
            return 0
        try:
            cur = sandbox_conn.execute(
                "SELECT COUNT(*) FROM sandbox_ledger WHERE outcome_type = ?",
                (outcome_type,),
            )
            result = cur.fetchone()
            return result[0] if result else 0
        except sqlite3.Error:
            return 0
        finally:
            sandbox_conn.close()
    
    def count_by_canonical_hash(self, canonical_hash: str) -> int:
        """Count ledger rows with specific canonical_hash."""
        sandbox_conn = self._get_sandbox_connection()
        if not sandbox_conn:
            return 0
        try:
            cur = sandbox_conn.execute(
                "SELECT COUNT(*) FROM sandbox_ledger WHERE canonical_hash = ?",
                (canonical_hash,),
            )
            result = cur.fetchone()
            return result[0] if result else 0
        except sqlite3.Error:
            return 0
        finally:
            sandbox_conn.close()

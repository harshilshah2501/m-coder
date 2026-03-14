"""
Tests for M4.6 runtime performance metrics.

Validates RuntimeMetricsService query layer and metrics report structures.
Uses deterministic test data with fixed timestamps.
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from runtime.observation.metrics_models import (
    MetricsBackendDistribution,
    CanonicalHashReuse,
    MetricsCollapseSummary,
    ExecutionCounts,
    InvariantHealth,
    LatencySummary,
    PostureCounts,
    ReplayCounts,
    RuntimeMetricsReport,
)
from runtime.observation.runtime_metrics import RuntimeMetricsService
from runtime.sandbox.sandbox_ledger_store import (
    EVENT_BLOCKED,
    EVENT_EXECUTED,
    EVENT_PLANGATE_BOUNDED_ALLOW,
    EVENT_PLANGATE_DEFERRED,
    EVENT_PLANGATE_REFUSED,
    EVENT_PLANGATE_SAFE_EXECUTE,
    EVENT_REFUSED,
    SandboxLedgerStore,
)


class TestPostureCounts:
    """Tests for PostureCounts model."""
    
    def test_empty_posture_counts(self) -> None:
        """Empty PostureCounts has zero total."""
        pc = PostureCounts()
        assert pc.total == 0
        assert pc.refuse == 0
        assert pc.safe_execute == 0
    
    def test_posture_counts_total(self) -> None:
        """PostureCounts.total sums all postures."""
        pc = PostureCounts(refuse=5, defer=3, bounded_allow=2, safe_execute=10)
        assert pc.total == 20
    
    def test_posture_counts_to_dict(self) -> None:
        """PostureCounts.to_dict includes all fields and total."""
        pc = PostureCounts(refuse=1, defer=2, bounded_allow=3, safe_execute=4)
        d = pc.to_dict()
        assert d["refuse"] == 1
        assert d["defer"] == 2
        assert d["bounded_allow"] == 3
        assert d["safe_execute"] == 4
        assert d["total"] == 10


class TestExecutionCounts:
    """Tests for ExecutionCounts model."""
    
    def test_execution_counts_total(self) -> None:
        """ExecutionCounts.total sums all outcomes."""
        ec = ExecutionCounts(executed=10, blocked=5, refused=3)
        assert ec.total == 18
    
    def test_execution_counts_to_dict(self) -> None:
        """ExecutionCounts.to_dict includes all fields."""
        ec = ExecutionCounts(executed=7, blocked=2, refused=1)
        d = ec.to_dict()
        assert d["executed"] == 7
        assert d["blocked"] == 2
        assert d["refused"] == 1
        assert d["total"] == 10


class TestMetricsBackendDistribution:
    """Tests for MetricsBackendDistribution model."""
    
    def test_empty_backend_distribution(self) -> None:
        """Empty MetricsBackendDistribution has zero total."""
        bd = MetricsBackendDistribution()
        assert bd.total == 0
        assert bd.counts == {}
    
    def test_backend_distribution_increment(self) -> None:
        """MetricsBackendDistribution.increment updates counts."""
        bd = MetricsBackendDistribution()
        bd.increment("local_process")
        bd.increment("local_process")
        bd.increment("container")
        assert bd.counts["local_process"] == 2
        assert bd.counts["container"] == 1
        assert bd.total == 3
    
    def test_backend_distribution_to_dict(self) -> None:
        """MetricsBackendDistribution.to_dict includes counts and total."""
        bd = MetricsBackendDistribution(counts={"local_process": 5, "container": 3})
        d = bd.to_dict()
        assert d["counts"]["local_process"] == 5
        assert d["counts"]["container"] == 3
        assert d["total"] == 8


class TestCanonicalHashReuse:
    """Tests for CanonicalHashReuse model."""
    
    def test_canonical_hash_reuse_to_dict(self) -> None:
        """CanonicalHashReuse.to_dict includes all fields."""
        chr = CanonicalHashReuse(
            unique_hashes=100,
            reused_hashes=10,
            total_rows_with_hash=150,
            max_reuse_count=5,
        )
        d = chr.to_dict()
        assert d["unique_hashes"] == 100
        assert d["reused_hashes"] == 10
        assert d["total_rows_with_hash"] == 150
        assert d["max_reuse_count"] == 5


class TestLatencySummary:
    """Tests for LatencySummary model."""
    
    def test_empty_latency_summary(self) -> None:
        """Empty LatencySummary has None values."""
        ls = LatencySummary()
        assert ls.count == 0
        assert ls.min_ms is None
        assert ls.avg_ms is None
    
    def test_latency_summary_to_dict_rounds_avg(self) -> None:
        """LatencySummary.to_dict rounds avg_ms to 2 decimals."""
        ls = LatencySummary(
            count=3,
            min_ms=10,
            max_ms=100,
            avg_ms=33.3333333,
            p50_ms=30,
            p95_ms=95,
            p99_ms=99,
        )
        d = ls.to_dict()
        assert d["avg_ms"] == 33.33


class TestRuntimeMetricsReport:
    """Tests for RuntimeMetricsReport model."""
    
    def test_empty_report(self) -> None:
        """Empty RuntimeMetricsReport has sensible defaults."""
        report = RuntimeMetricsReport()
        assert report.total_requests == 0
        assert report.ledger_row_count == 0
        assert report.posture_counts.total == 0
    
    def test_report_to_dict(self) -> None:
        """RuntimeMetricsReport.to_dict includes all sections."""
        report = RuntimeMetricsReport(
            total_requests=50,
            unique_sessions=10,
            unique_request_ids=45,
            ledger_row_count=100,
            report_timestamp_utc="2026-03-13T12:00:00Z",
        )
        report.posture_counts.safe_execute = 40
        report.posture_counts.refuse = 10
        
        d = report.to_dict()
        assert d["total_requests"] == 50
        assert d["unique_sessions"] == 10
        assert d["unique_request_ids"] == 45
        assert d["ledger_row_count"] == 100
        assert d["report_timestamp_utc"] == "2026-03-13T12:00:00Z"
        assert d["posture_counts"]["safe_execute"] == 40
        assert d["posture_counts"]["refuse"] == 10
        assert "execution_counts" in d
        assert "backend_distribution" in d
        assert "canonical_hash_reuse" in d


class TestRuntimeMetricsService:
    """Tests for RuntimeMetricsService query layer."""
    
    def test_service_with_empty_ledger(self) -> None:
        """Service returns empty report when ledger is empty."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")
            
            service = RuntimeMetricsService(sandbox_ledger_store=store)
            report = service.generate_report()
            
            assert report.ledger_row_count == 0
            assert report.posture_counts.total == 0
            assert report.execution_counts.total == 0
    
    def test_posture_counts_from_ledger(self) -> None:
        """Service correctly counts Plan-Gate postures."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")
            
            for i in range(3):
                store.append(
                    ledger_row_id=f"row-refuse-{i}",
                    event_type=EVENT_PLANGATE_REFUSED,
                    outcome_type="refused",
                    request_id=f"req-refuse-{i}",
                    payload={"decision_posture": "refuse"},
                )
            for i in range(2):
                store.append(
                    ledger_row_id=f"row-defer-{i}",
                    event_type=EVENT_PLANGATE_DEFERRED,
                    outcome_type="deferred",
                    request_id=f"req-defer-{i}",
                    payload={"decision_posture": "defer"},
                )
            for i in range(5):
                store.append(
                    ledger_row_id=f"row-safe-{i}",
                    event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                    outcome_type="safe_execute",
                    request_id=f"req-safe-{i}",
                    payload={"decision_posture": "safe_execute"},
                )
            
            service = RuntimeMetricsService(sandbox_ledger_store=store)
            postures = service.get_posture_distribution()
            
            assert postures.refuse == 3
            assert postures.defer == 2
            assert postures.bounded_allow == 0
            assert postures.safe_execute == 5
            assert postures.total == 10
    
    def test_execution_counts_from_ledger(self) -> None:
        """Service correctly counts execution outcomes."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")
            
            for i in range(4):
                store.append(
                    ledger_row_id=f"row-exec-{i}",
                    event_type=EVENT_EXECUTED,
                    outcome_type="executed",
                    request_id=f"req-{i}",
                    sandbox_id=f"sbx-{i}",
                    payload={"exit_code": 0, "backend": "local_process"},
                )
            for i in range(2):
                store.append(
                    ledger_row_id=f"row-blocked-{i}",
                    event_type=EVENT_BLOCKED,
                    outcome_type="blocked",
                    request_id=f"req-blocked-{i}",
                    payload={"reason": "policy_violation"},
                )
            store.append(
                ledger_row_id="row-refused-1",
                event_type=EVENT_REFUSED,
                outcome_type="refused",
                request_id="req-refused-1",
                payload={"reason": "authority_fail"},
            )
            
            service = RuntimeMetricsService(sandbox_ledger_store=store)
            exec_counts = service.get_execution_distribution()
            
            assert exec_counts.executed == 4
            assert exec_counts.blocked == 2
            assert exec_counts.refused == 1
            assert exec_counts.total == 7
    
    def test_backend_distribution_from_ledger(self) -> None:
        """Service correctly computes backend distribution."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")
            
            for i in range(3):
                store.append(
                    ledger_row_id=f"row-local-{i}",
                    event_type=EVENT_EXECUTED,
                    outcome_type="executed",
                    request_id=f"req-local-{i}",
                    sandbox_id=f"sbx-{i}",
                    payload={"backend": "local_process", "exit_code": 0},
                )
            for i in range(2):
                store.append(
                    ledger_row_id=f"row-container-{i}",
                    event_type=EVENT_EXECUTED,
                    outcome_type="executed",
                    request_id=f"req-container-{i}",
                    sandbox_id=f"sbx-c-{i}",
                    payload={"backend": "container", "exit_code": 0},
                )
            
            service = RuntimeMetricsService(sandbox_ledger_store=store)
            backend_dist = service.get_backend_distribution()
            
            assert backend_dist.counts["local_process"] == 3
            assert backend_dist.counts["container"] == 2
            assert backend_dist.total == 5
    
    def test_canonical_hash_reuse_from_ledger(self) -> None:
        """Service correctly computes canonical_hash reuse metrics."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")
            
            ch_reused = "hash-abc123"
            ch_unique1 = "hash-unique1"
            ch_unique2 = "hash-unique2"
            
            for i in range(3):
                store.append(
                    ledger_row_id=f"row-reused-{i}",
                    event_type=EVENT_EXECUTED,
                    outcome_type="executed",
                    request_id=f"req-reused-{i}",
                    sandbox_id=f"sbx-{i}",
                    payload={"canonical_hash": ch_reused, "exit_code": 0},
                )
            store.append(
                ledger_row_id="row-unique1",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-unique1",
                sandbox_id="sbx-u1",
                payload={"canonical_hash": ch_unique1, "exit_code": 0},
            )
            store.append(
                ledger_row_id="row-unique2",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-unique2",
                sandbox_id="sbx-u2",
                payload={"canonical_hash": ch_unique2, "exit_code": 0},
            )
            
            service = RuntimeMetricsService(sandbox_ledger_store=store)
            hash_metrics = service.get_canonical_hash_metrics()
            
            assert hash_metrics.unique_hashes == 3
            assert hash_metrics.reused_hashes == 1
            assert hash_metrics.total_rows_with_hash == 5
            assert hash_metrics.max_reuse_count == 3
    
    def test_replay_counts_from_ledger(self) -> None:
        """Service correctly counts replay executions."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")
            
            for i in range(2):
                store.append(
                    ledger_row_id=f"row-replay-ok-{i}",
                    event_type=EVENT_EXECUTED,
                    outcome_type="executed",
                    request_id=f"req-replay-ok-{i}",
                    sandbox_id=f"sbx-r-{i}",
                    payload={"execution_surface": "replay", "exit_code": 0},
                )
            store.append(
                ledger_row_id="row-replay-fail",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-replay-fail",
                sandbox_id="sbx-rf",
                payload={"execution_surface": "replay", "exit_code": 1},
            )
            store.append(
                ledger_row_id="row-normal",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-normal",
                sandbox_id="sbx-n",
                payload={"execution_surface": "execute_service", "exit_code": 0},
            )
            
            service = RuntimeMetricsService(sandbox_ledger_store=store)
            report = service.generate_report()
            
            assert report.replay_counts.replay_requests == 3
            assert report.replay_counts.replay_succeeded == 2
            assert report.replay_counts.replay_failed == 1
    
    def test_count_by_event_type(self) -> None:
        """Service.count_by_event_type returns correct count."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")
            
            for i in range(5):
                store.append(
                    ledger_row_id=f"row-{i}",
                    event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                    outcome_type="safe_execute",
                    request_id=f"req-{i}",
                    payload={"decision_posture": "safe_execute"},
                )
            
            service = RuntimeMetricsService(sandbox_ledger_store=store)
            count = service.count_by_event_type(EVENT_PLANGATE_SAFE_EXECUTE)
            
            assert count == 5
    
    def test_count_by_canonical_hash(self) -> None:
        """Service.count_by_canonical_hash returns correct count."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")
            
            ch = "hash-target"
            for i in range(3):
                store.append(
                    ledger_row_id=f"row-{i}",
                    event_type=EVENT_EXECUTED,
                    outcome_type="executed",
                    request_id=f"req-{i}",
                    sandbox_id=f"sbx-{i}",
                    payload={"canonical_hash": ch, "exit_code": 0},
                )
            
            service = RuntimeMetricsService(sandbox_ledger_store=store)
            count = service.count_by_canonical_hash(ch)
            
            assert count == 3
    
    def test_service_with_path_fallback(self) -> None:
        """Service works with path fallback when store not provided."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")
            store.append(
                ledger_row_id="row-1",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-1",
                payload={"decision_posture": "safe_execute"},
            )
            
            service = RuntimeMetricsService(sandbox_ledger_path=path)
            report = service.generate_report()
            
            assert report.posture_counts.safe_execute == 1
    
    def test_full_report_generation(self) -> None:
        """Service generates complete report with all sections."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(path, fixed_time="2026-03-13T12:00:00Z")
            
            store.append(
                ledger_row_id="row-pg-1",
                event_type=EVENT_PLANGATE_SAFE_EXECUTE,
                outcome_type="safe_execute",
                request_id="req-1",
                payload={"canonical_hash": "hash-1", "decision_posture": "safe_execute"},
            )
            store.append(
                ledger_row_id="row-exec-1",
                event_type=EVENT_EXECUTED,
                outcome_type="executed",
                request_id="req-1",
                sandbox_id="sbx-1",
                payload={
                    "canonical_hash": "hash-1",
                    "backend": "local_process",
                    "exit_code": 0,
                    "execution_surface": "execute_service",
                },
            )
            store.append(
                ledger_row_id="row-pg-2",
                event_type=EVENT_PLANGATE_REFUSED,
                outcome_type="refused",
                request_id="req-2",
                payload={"decision_posture": "refuse"},
            )
            
            service = RuntimeMetricsService(sandbox_ledger_store=store)
            report = service.generate_report()
            
            assert report.ledger_row_count == 3
            assert report.posture_counts.safe_execute == 1
            assert report.posture_counts.refuse == 1
            assert report.execution_counts.executed == 1
            assert report.backend_distribution.counts.get("local_process") == 1
            assert report.canonical_hash_reuse.unique_hashes >= 1
            assert report.report_timestamp_utc != ""
            
            d = report.to_dict()
            assert "posture_counts" in d
            assert "execution_counts" in d
            assert "backend_distribution" in d
            assert "canonical_hash_reuse" in d
            assert "latency_summary" in d


class TestInvariantHealth:
    """Tests for InvariantHealth model."""
    
    def test_invariant_health_defaults(self) -> None:
        """InvariantHealth has zero defaults."""
        ih = InvariantHealth()
        assert ih.violations_detected == 0
        assert ih.ref_enforced_count == 0
        assert ih.boundary_cross_attempted == 0
        assert ih.boundary_cross_blocked == 0
        assert ih.violation_types == {}
    
    def test_invariant_health_to_dict(self) -> None:
        """InvariantHealth.to_dict includes all fields."""
        ih = InvariantHealth(
            violations_detected=2,
            violation_types={"L1": 1, "L2": 1},
            ref_enforced_count=5,
            boundary_cross_attempted=3,
            boundary_cross_blocked=3,
        )
        d = ih.to_dict()
        assert d["violations_detected"] == 2
        assert d["violation_types"]["L1"] == 1
        assert d["ref_enforced_count"] == 5
        assert d["boundary_cross_attempted"] == 3
        assert d["boundary_cross_blocked"] == 3


class TestMetricsCollapseSummary:
    """Tests for MetricsCollapseSummary model."""
    
    def test_collapse_summary_defaults(self) -> None:
        """MetricsCollapseSummary has zero defaults."""
        cs = MetricsCollapseSummary()
        assert cs.mismatch_count == 0
        assert cs.collapse_count == 0
        assert cs.boundary_blocked == 0
    
    def test_collapse_summary_to_dict(self) -> None:
        """MetricsCollapseSummary.to_dict includes all fields."""
        cs = MetricsCollapseSummary(
            mismatch_count=2,
            collapse_count=1,
            boundary_blocked=3,
        )
        d = cs.to_dict()
        assert d["mismatch_count"] == 2
        assert d["collapse_count"] == 1
        assert d["boundary_blocked"] == 3


class TestReplayCounts:
    """Tests for ReplayCounts model."""
    
    def test_replay_counts_to_dict(self) -> None:
        """ReplayCounts.to_dict includes all fields."""
        rc = ReplayCounts(
            replay_requests=10,
            replay_succeeded=8,
            replay_failed=2,
        )
        d = rc.to_dict()
        assert d["replay_requests"] == 10
        assert d["replay_succeeded"] == 8
        assert d["replay_failed"] == 2

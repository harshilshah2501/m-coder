# M4.6 Runtime Performance Metrics — Implementation Note

**Milestone:** M4.6  
**Branch:** feature/m4.6-runtime-metrics  
**Status:** Implementation complete  
**Base commit:** cd2e74df7bb8174881e9957daa8582f231780c10 (M4.1 Slice-4)

## Purpose

Provide deterministic operational visibility into runtime health and invariance behavior through a metrics query layer over ledger evidence.

**Constraints:**
- Deterministic only (same ledger state → same metrics)
- Read-only over evidence (no mutations, no side effects)
- No UI
- No external telemetry pipelines

## Dependencies

| Milestone | Dependency Type | Description |
|-----------|-----------------|-------------|
| M4.1 | Required | canonical_hash indexed column, ledger identity propagation |
| M3.2 | Required | SandboxLedgerStore append-only persistence |
| M3.5 | Required | LedgerStore with ledger_row.v0.1 schema |
| M4.2 | Optional | Drift baseline metrics (not yet implemented) |
| M4.3 | Optional | Collapse tracking metrics (not yet implemented) |
| M4.4 | Optional | Ledger reconciliation metrics (not yet implemented) |

## Files Changed

| File | Change |
|------|--------|
| `runtime/observation/__init__.py` | **New.** Module init; exports all metrics types and service. |
| `runtime/observation/metrics_models.py` | **New.** Data structures for metrics reports: PostureCounts, ExecutionCounts, BackendDistribution, CanonicalHashReuse, LatencySummary, ReplayCounts, CollapseSummary, InvariantHealth, RuntimeMetricsReport. |
| `runtime/observation/runtime_metrics.py` | **New.** RuntimeMetricsService query layer; reads from SandboxLedgerStore and LedgerStore. |
| `runtime/tests/test_runtime_metrics.py` | **New.** Comprehensive tests for metrics models and service. |
| `docs/runtime/milestones/M4_6_RUNTIME_METRICS.md` | **New.** This implementation note. |

## Metrics Provided

### From SandboxLedgerStore (sandbox_ledger)

| Metric | Description |
|--------|-------------|
| **Posture counts** | Distribution of Plan-Gate decisions: refuse, defer, bounded_allow, safe_execute |
| **Execution counts** | Sandbox outcomes: executed, blocked, refused |
| **Backend distribution** | Execution counts by backend (local_process, container, etc.) |
| **Canonical hash reuse** | Unique hashes, reused hashes, max reuse count |
| **Replay counts** | Replay requests, succeeded, failed (from execution_surface metadata) |
| **Unique identifiers** | Unique request_ids, unique sandbox_ids (sessions) |

### From LedgerStore (ledger_rows)

| Metric | Description |
|--------|-------------|
| **Latency summary** | min, max, avg, p50, p95, p99 (from payload.metrics.latency_ms) |
| **Invariant health** | REF enforced count, boundary cross attempted/blocked |
| **Collapse summary** | boundary_blocked event counts (M4.3 integration point) |

## API

### RuntimeMetricsService

```python
from runtime.observation import RuntimeMetricsService

# Initialize with stores or paths
service = RuntimeMetricsService(
    sandbox_ledger_store=store,  # or sandbox_ledger_path=Path("...")
    ledger_store=ledger,         # or ledger_path=Path("...")
)

# Full report
report = service.generate_report()
print(report.to_dict())

# Individual metrics
postures = service.get_posture_distribution()
executions = service.get_execution_distribution()
backends = service.get_backend_distribution()
hash_metrics = service.get_canonical_hash_metrics()
latency = service.get_latency_summary()
health = service.get_invariant_health()

# Counts
count = service.count_by_event_type("plangate_safe_execute")
count = service.count_by_canonical_hash("hash-abc123")
```

### RuntimeMetricsReport

```python
report = RuntimeMetricsReport(
    total_requests=100,
    unique_sessions=25,
    unique_request_ids=95,
    ledger_row_count=200,
    report_timestamp_utc="2026-03-13T12:00:00Z",
)
report.posture_counts.safe_execute = 80
report.posture_counts.refuse = 20
report.to_dict()  # JSON-serializable dictionary
```

## Invariants Preserved

- **No bypass:** Metrics are read-only; no execution paths created.
- **Fail-closed:** If ledger unavailable, metrics return empty/zero values.
- **Governance boundary:** No mutations to ledger or runtime state.
- **Append-only ledger:** Only reads from ledger; never writes.
- **Replay compatibility:** canonical_hash metrics support replay validation.

## Tests

| Test | Description |
|------|-------------|
| test_posture_counts_from_ledger | Verifies correct Plan-Gate posture counting |
| test_execution_counts_from_ledger | Verifies correct execution outcome counting |
| test_backend_distribution_from_ledger | Verifies backend distribution computation |
| test_canonical_hash_reuse_from_ledger | Verifies hash reuse metrics |
| test_replay_counts_from_ledger | Verifies replay execution counting |
| test_full_report_generation | Verifies complete report with all sections |
| test_service_with_path_fallback | Verifies path-based initialization |
| test_count_by_event_type | Verifies event type counting |
| test_count_by_canonical_hash | Verifies canonical hash counting |

## Known Limitations

1. **Latency data availability:** Latency metrics depend on payload.metrics.latency_ms being populated in ledger_rows. If not present, latency summary will be empty.

2. **M4.3 collapse metrics:** Collapse/mismatch counting is prepared but depends on M4.3 implementation to populate the relevant event types.

3. **M4.4 reconciliation:** Ledger reconciliation metrics are not yet implemented; awaits M4.4.

4. **No streaming:** Metrics are computed on-demand via full scan. For large ledgers, consider pagination or incremental updates in future.

## Merge Readiness

| Criterion | Status |
|-----------|--------|
| Tests pass | ✅ |
| No protected file changes | ✅ |
| No architecture changes | ✅ |
| No bypass paths introduced | ✅ |
| Append-only preserved | ✅ |
| Documentation complete | ✅ |

**Merge dependencies:** None. M4.6 is read-only over M4.1 outputs and can merge independently.

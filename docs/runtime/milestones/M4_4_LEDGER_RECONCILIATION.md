# M4.4 Ledger Reconciliation — Implementation Note

**Milestone:** M4.4 Ledger Reconciliation  
**Status:** Complete  
**Dependencies:** M4.1 (canonical_hash identity propagation)

---

## Purpose

Reconcile plan, decision, execution, and replay evidence using `request_id`, `plan_hash`, and `canonical_hash` linkage. Provide deterministic mismatch detection for audit confidence.

This milestone implements read-only verification of ledger consistency without mutating existing ledger rows.

---

## Scope

### In Scope

1. **Reconciliation Service** — `LedgerReconciliationService` for verifying linkage consistency
2. **Reconciliation Models** — Data models for mismatches, severity, and results
3. **Mismatch Detection** — Deterministic classification of inconsistencies
4. **Backward Compatibility** — Handle legacy rows missing identity fields
5. **Tests** — Comprehensive test suite for all reconciliation paths

### Out of Scope

- Ledger mutation or correction
- Drift baseline tracking (M4.2)
- Collapse tracking (M4.3)
- Runtime metrics (M4.6)
- GREG escalation (M4.5)

---

## Files Added

| File | Purpose |
|------|---------|
| `runtime/observation/__init__.py` | Package init; exports M4.4 reconciliation API (forward-compatible with M4.1 exports) |
| `runtime/observation/reconciliation_models.py` | Data models: MismatchClassification, ReconciliationResult, RowLinkage |
| `runtime/observation/reconciliation.py` | LedgerReconciliationService with all reconciliation methods |
| `runtime/tests/test_reconciliation.py` | 28 tests covering all reconciliation paths |
| `docs/runtime/milestones/M4_4_LEDGER_RECONCILIATION.md` | This implementation note |

### Integration Compatibility

The `runtime/observation/__init__.py` is structured to:
- **Always export** M4.4 reconciliation symbols
- **Conditionally import** M4.1 observability symbols when available (TraceEvent, ExecutionTrace, PostureDistribution, RefusalSummary, BackendDistribution, RuntimeSummary, ExplanationPayload, TraceBuilder, RuntimeSummaryQueries, ExplanationBuilder)
- Maintain backward and forward compatibility across M4.x milestone integration

---

## Key Symbols

### Reconciliation Models (`reconciliation_models.py`)

- `MismatchSeverity` — Enum: info, warning, error, critical
- `MismatchClassification` — Enum: 12 deterministic mismatch types
- `ReconciliationStatus` — Enum: consistent, warnings_only, mismatches_found, critical_mismatches
- `RowLinkage` — Dataclass capturing identity fields from ledger row
- `ReconciliationMismatch` — Dataclass for a single mismatch with classification
- `ReconciliationResult` — Dataclass for full reconciliation result

### Reconciliation Service (`reconciliation.py`)

- `ReconciliationConfig` — Configuration for reconciliation behavior
- `LedgerReconciliationService` — Main service class
  - `reconcile_by_request_id(request_id)` — Reconcile all rows for a request
  - `reconcile_by_canonical_hash(canonical_hash)` — Reconcile by canonical execution identity
  - `reconcile_by_plan_hash(plan_hash)` — Reconcile by plan identity
  - `reconcile_all()` — Full ledger reconciliation
  - `reconcile_replay_linkage(original_canonical_hash, replay_request_id)` — Verify replay linkage

---

## Mismatch Classifications

| Classification | Severity | Description |
|---------------|----------|-------------|
| `missing_decision` | ERROR | Execution row without matching decision |
| `missing_execution` | ERROR | safe_execute decision without execution row |
| `missing_replay_link` | WARNING | Replay execution missing execution_surface=replay |
| `canonical_hash_mismatch` | ERROR | Different canonical_hash between decision and execution |
| `plan_hash_mismatch` | WARNING | Different plan_hash across rows for same request |
| `request_id_orphan` | INFO | Single row with unique request_id |
| `intent_id_mismatch` | WARNING | Different intent_id for same canonical_hash |
| `duplicate_decision` | WARNING | Multiple decision rows for same canonical_hash |
| `duplicate_execution` | WARNING | Multiple execution rows for same canonical_hash |
| `boundary_phrase_inconsistent` | ERROR | Different boundary phrases across rows |
| `invariant_violation` | CRITICAL | Ledger row invariant L1-L4 violated |
| `legacy_row_no_identity` | INFO | Row missing canonical_hash (backward compatible) |

---

## Reconciliation Logic

### Linkage Verification

1. **request_id linkage**: All rows for a request should form a coherent session
2. **plan_hash linkage**: Decision rows should reference consistent plan_hash
3. **canonical_hash linkage**: Decision and execution rows should share canonical_hash
4. **intent_id consistency**: Same canonical_hash should have same intent_id

### Decision-Execution Linkage

- `safe_execute` decision requires matching execution row
- `refuse`, `defer`, `bounded_allow` do NOT require execution row
- Execution row should have matching decision row

### Replay Verification

- Replay execution should have `execution_surface: "replay"` in metadata
- Replay canonical_hash should match original canonical_hash

---

## Constraints Respected

- **Read-only**: No mutation of existing ledger rows
- **Backward compatible**: Legacy rows without canonical_hash handled as INFO-level warnings
- **Deterministic**: Same input produces same classification output
- **No execution bypass**: Does not modify runtime execution paths
- **Fail-closed**: Service does not suppress errors or exceptions

---

## Dependencies on M4.1

This milestone depends on M4.1 Slice 3 (ledger identity propagation):

- `canonical_hash` in decision row payload
- `canonical_hash` in execution row payload
- `intent_id` in payloads for identity tracking
- `get_by_canonical_hash()` method on SandboxLedgerStore

Legacy rows without these fields are handled gracefully with `LEGACY_ROW_NO_IDENTITY` classification.

---

## Test Evidence

28 tests covering:

| Test Class | Tests | Coverage |
|------------|-------|----------|
| TestRowLinkage | 3 | Linkage extraction from rows |
| TestReconciliationResult | 4 | Result model behavior |
| TestLedgerReconciliationByRequestId | 5 | request_id reconciliation |
| TestLedgerReconciliationByCanonicalHash | 2 | canonical_hash reconciliation |
| TestLedgerReconciliationByPlanHash | 1 | plan_hash reconciliation |
| TestLedgerReconciliationAll | 2 | Full ledger reconciliation |
| TestReplayLinkageReconciliation | 2 | Replay linkage verification |
| TestDuplicateDetection | 2 | Duplicate decision/execution detection |
| TestReconciliationConfig | 2 | Configuration options |
| TestMismatchClassificationDeterminism | 2 | Deterministic classification |
| TestBackwardCompatibility | 3 | Legacy row handling |

```
$ python3 -m pytest runtime/tests/test_reconciliation.py -v
============================= 28 passed in 0.17s ==============================
```

---

## Usage Example

```python
from runtime.observation import (
    LedgerReconciliationService,
    ReconciliationConfig,
)
from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore

# Initialize
store = SandboxLedgerStore("ledger.db")
service = LedgerReconciliationService(store)

# Reconcile by request_id
result = service.reconcile_by_request_id("req-123")
if result.is_consistent():
    print("All linkages verified")
else:
    for mismatch in result.mismatches:
        print(f"{mismatch.classification}: {mismatch.description}")

# Reconcile by canonical_hash
result = service.reconcile_by_canonical_hash("ch-abc123...")
print(result.summary())

# Full ledger reconciliation
result = service.reconcile_all()
print(f"Examined {result.total_rows_examined} rows")
print(f"Found {len(result.mismatches)} mismatches")
```

---

## Invariants Preserved

- **No bypass**: Reconciliation is read-only observation; no execution path changes
- **Fail-closed**: Errors in reconciliation surface as exceptions, not silent failures
- **Governance boundary**: Reconciliation does not modify ledger or affect runtime governance
- **Shadow isolation**: Reconciliation operates on production ledger evidence only
- **Append-only ledger**: No ledger mutations; read-only verification
- **Replay compatibility**: Replay linkage verification supports canonical_hash matching

---

## Merge Readiness

| Criterion | Status |
|-----------|--------|
| Tests pass | ✅ 28/28 |
| No protected files modified | ✅ |
| Backward compatible | ✅ |
| Invariants preserved | ✅ |
| Documentation complete | ✅ |
| Dependencies satisfied (M4.1) | ✅ |

**Merge order**: After M4.1 (canonical_hash propagation is required)

---

## Known Limitations

1. **Ledger V1 rows**: LedgerRowV1 from `runtime/ledger/` module not directly supported (different schema); use `from_ledger_row_v1` adapter if needed
2. **Replay via ExecutionReplayService**: Replay service creates new request_id; replay linkage verification requires explicit check
3. **Performance**: `reconcile_all()` loads entire ledger; use scoped methods for large ledgers

---

## Follow-up Milestones

- **M4.2 Drift Baseline**: Track baseline distributions for mismatch frequency
- **M4.3 Collapse Tracking**: Detect collapse patterns in reconciliation results
- **M4.5 GREG Escalation**: Escalate critical mismatches to governance review
- **M4.6 Runtime Metrics**: Expose reconciliation statistics for monitoring

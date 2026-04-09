# M4.2 Drift Baseline — Implementation Note

**Milestone:** M4.2 Drift Baseline  
**Branch:** `feature/m4.2-drift-baseline`  
**Status:** Implementation complete  
**Date:** 2026-03-13

---

## 1. Purpose

Establish deterministic baseline distributions for runtime behavior so future drift can be detected. This milestone provides the foundation for behavioral observability over the governed runtime.

The baseline captures behavioral patterns from ledger evidence without modifying runtime behavior or introducing non-deterministic dependencies.

---

## 2. Scope

### In Scope
- Baseline data models (dimensions, distributions, snapshots)
- Baseline builder (read-only over ledger evidence)
- Baseline persistence (file and SQLite storage)
- Deterministic comparison between baselines
- Comprehensive test suite

### Out of Scope
- Dashboards or visualization
- External telemetry infrastructure
- LLM-based analysis
- Real-time drift alerting
- Mutation of runtime behavior

---

## 3. Baseline Dimensions

The following dimensions are tracked for behavioral baselining:

| Dimension | Description | Source |
|-----------|-------------|--------|
| `event_type` | Distribution of ledger event types | `ledger_rows.event_type`, `sandbox_ledger.event_type` |
| `outcome_type` | Distribution of sandbox outcomes (refused/blocked/executed) | `sandbox_ledger.outcome_type` |
| `decision_posture` | Distribution of Plan-Gate postures | Event type inference or payload |
| `refusal_reason` | Distribution of refusal reason codes | Payload `reason` or `reason_codes` |
| `backend` | Distribution of execution backends | Payload `backend` |
| `execution_surface` | Distribution of execution surfaces | Payload `execution_surface` |
| `replay_frequency` | Distribution of request replays (same request_id count) | Bucketed: single, two, 3-5, 6-10, 10+ |
| `canonical_hash_reuse` | Distribution of canonical_hash reuse patterns | Bucketed: unique, reused_once, reused_2-4, reused_5-9, reused_10+ |

---

## 4. Files Changed

### New Files

| File | Purpose |
|------|---------|
| `runtime/observation/baseline_models.py` | `BaselineDimension`, `DimensionDistribution`, `BaselineSnapshot`, `BaselineMetadata` |
| `runtime/observation/drift_baseline.py` | `BaselineBuilder`, `BaselineBuildError` |
| `runtime/observation/baseline_store.py` | `BaselineStore`, `BaselineStoreError` |
| `runtime/tests/test_drift_baseline.py` | Comprehensive test suite |
| `docs/runtime/milestones/M4_2_DRIFT_BASELINE.md` | This milestone note |

### Modified Files

| File | Change |
|------|--------|
| `runtime/observation/__init__.py` | Added M4.2 exports additively to existing M4.1 and M4.4 exports |

M4.2 exports added:
- `BaselineDimension`, `DimensionDistribution`, `BaselineSnapshot`, `BaselineMetadata`
- `BaselineBuilder`, `BaselineBuildError`
- `BaselineStore`, `BaselineStoreError`

Preserved exports from M4.1 and M4.4 unchanged.

---

## 5. Data Structures

### BaselineDimension (Enum)
```python
class BaselineDimension(str, Enum):
    EVENT_TYPE = "event_type"
    OUTCOME_TYPE = "outcome_type"
    DECISION_POSTURE = "decision_posture"
    REFUSAL_REASON = "refusal_reason"
    BACKEND = "backend"
    EXECUTION_SURFACE = "execution_surface"
    REPLAY_FREQUENCY = "replay_frequency"
    CANONICAL_HASH_REUSE = "canonical_hash_reuse"
```

### DimensionDistribution
- Stores counts per value
- Computes normalized frequencies
- Deterministic serialization (sorted keys)

### BaselineSnapshot
- Contains `BaselineMetadata` (provenance)
- Contains per-dimension distributions
- Computes `baseline_hash` (SHA-256 of normalized distributions)
- Supports deterministic comparison with drift scoring

### BaselineMetadata
- `baseline_id`: Unique identifier
- `created_utc`: Creation timestamp
- `ledger_path`: Source ledger path
- `row_count`: Number of evidence rows
- `time_range_start`, `time_range_end`: Evidence time bounds
- `runtime_version`: Runtime version at build time
- `schema_version`: Always `baseline.v0.1`

---

## 6. Usage

### Building a Baseline
```python
from runtime.observation import BaselineBuilder

builder = BaselineBuilder(ledger_path="/path/to/ledger.db")
snapshot = builder.build_baseline()

# With time range filter
snapshot = builder.build_baseline(
    time_range_start="2026-01-01T00:00:00Z",
    time_range_end="2026-03-01T00:00:00Z",
)
```

### Storing a Baseline
```python
from runtime.observation import BaselineStore

store = BaselineStore("/path/to/baselines.db", mode="sqlite")
baseline_id = store.save(snapshot)

# Load later
loaded = store.load(baseline_id)
latest = store.load_latest()
```

### Comparing Baselines
```python
drift = baseline_v1.compare(baseline_v2)

print(drift["hash_match"])           # bool
print(drift["overall_drift_score"])  # float, 0.0 = no drift
print(drift["dimension_drifts"])     # per-dimension drift scores
print(drift["new_values"])           # values in v2 but not v1
print(drift["missing_values"])       # values in v1 but not v2
```

---

## 7. Invariants Preserved

| Invariant | Status |
|-----------|--------|
| No bypass path | ✅ Not applicable (read-only) |
| Fail-closed | ✅ Errors raised, not swallowed |
| Governance boundary | ✅ No governance logic modified |
| Shadow isolation | ✅ Not modified |
| Append-only ledger | ✅ Ledger read-only; no mutations |
| Replay compatibility | ✅ Uses existing ledger schema |

---

## 8. Dependencies

### M4.1 Observability Closure
M4.2 depends on M4.1 for:
- `canonical_hash` field in ledger rows (Slice 3)
- Execution identity propagation

Without M4.1:
- `canonical_hash_reuse` dimension will have no data
- Other dimensions work from existing event_type, outcome_type, etc.

The baseline builder gracefully handles missing fields by producing empty distributions for unavailable dimensions.

---

## 9. Tests

### Test Suite: `runtime/tests/test_drift_baseline.py`

| Test Class | Tests |
|------------|-------|
| `TestDimensionDistribution` | 7 tests: counts, frequencies, serialization |
| `TestBaselineSnapshot` | 8 tests: hash computation, comparison, drift detection |
| `TestBaselineBuilder` | 10 tests: ledger extraction, determinism, time ranges |
| `TestBaselineStore` | 10 tests: file/sqlite modes, load/save, queries |
| `TestEndToEnd` | 2 tests: full workflow, cross-session determinism |

### Run Tests
```bash
pytest runtime/tests/test_drift_baseline.py -v
```

---

## 10. Merge Readiness

| Criterion | Status |
|-----------|--------|
| Implementation complete | ✅ |
| Tests passing | ✅ |
| Documentation complete | ✅ |
| No architecture changes | ✅ |
| No protected file changes | ✅ |
| Additive only | ✅ |
| Dependencies documented | ✅ |

### Merge Order
1. M4.1 Observability Closure (provides canonical_hash)
2. **M4.2 Drift Baseline** (this milestone)
3. M4.3 Collapse Tracking (may consume baselines)

---

## 11. Known Limitations

1. **No real-time streaming**: Baselines are built on-demand from persisted ledger, not from live event streams.

2. **Bucket granularity**: Replay frequency and hash reuse are bucketed; exact counts require ledger queries.

3. **Single-ledger scope**: Each baseline is built from one ledger path at a time. Cross-ledger baselines require separate builds and comparison.

4. **No automatic scheduling**: Baseline builds must be triggered explicitly; no cron or scheduler integration.

---

## 12. Future Work (Out of Scope)

- M4.3 may use baselines for collapse detection thresholds
- Alerting integration for drift above threshold
- Historical baseline trend analysis
- Cross-repo baseline comparison

---

*End of M4.2 implementation note.*

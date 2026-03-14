# M4.3 Collapse Vector Tracking — Implementation Note

**Milestone:** M4.3  
**Branch:** `feature/m4.3-collapse-tracking`  
**Status:** Implementation complete  
**Date:** 2026-03-13

---

## 1. Purpose

Detect and classify governance/runtime collapse vectors deterministically from runtime evidence. Collapse tracking operates on existing evidence artifacts (ledger rows, trace summaries, baseline comparisons) without mutating runtime state.

---

## 2. Scope

### In Scope

- Collapse event model (schema, evidence, severity)
- Collapse classifier (deterministic detection)
- Query helpers (filtering, aggregation)
- Tests for all collapse classes

### Out of Scope

- Dashboards or alerting infrastructure
- Runtime mutation
- Architectural reinterpretation
- GREG escalation (M4.5)
- Ledger reconciliation (M4.4)

---

## 3. Collapse Classes

| Class | Description | Default Severity |
|-------|-------------|------------------|
| `identity_propagation_missing` | `canonical_hash` absent in decision/execution rows where required | HIGH |
| `decision_execution_mismatch` | Decision posture conflicts with execution outcome | CRITICAL |
| `replay_mismatch` | Replayed execution differs from original | HIGH |
| `missing_trace_linkage` | Trace lacks required join keys (`request_id`, `plan_hash`) | MEDIUM |
| `unexpected_refusal_distribution_drift` | Refusal rate exceeds baseline threshold | MEDIUM |
| `missing_evidence_join` | Plan/decision/execution cannot be linked | HIGH |

---

## 4. Files Changed

| File | Change Type | Purpose |
|------|-------------|---------|
| `runtime/observation/__init__.py` | Updated | Added M4.3 exports to existing package (preserves M4.1, M4.2, M4.4 exports) |
| `runtime/observation/collapse_models.py` | Added | `CollapseClass`, `CollapseEvent`, `CollapseEvidence`, `CollapseSeverity`, `CollapseSummary` |
| `runtime/observation/collapse_vectors.py` | Added | `CollapseClassifier`, `ClassificationResult` |
| `runtime/observation/collapse_queries.py` | Added | `CollapseQueryService`, `CollapseFilter`, query helpers |
| `runtime/tests/test_collapse_vectors.py` | Added | Comprehensive tests for all components |

---

## 5. Key Design Decisions

### 5.1 Deterministic Event IDs

Event IDs are derived from `(collapse_class, request_id, plan_hash, evidence_hash)` so that the same collapse detected twice yields the same `event_id`. This supports idempotent detection and deduplication.

### 5.2 Evidence-Based Only

All collapse detection operates on existing evidence artifacts:
- Ledger rows (from M3.5 ledger)
- Trace summaries (from replay/shadow)
- Baseline metrics (from M4.2 drift baseline)

No runtime state is mutated by collapse tracking.

### 5.3 Severity Mapping

Each collapse class has a default severity based on governance risk:
- **CRITICAL**: Governance invariant violated (e.g., decision/execution mismatch, execution without decision)
- **HIGH**: Significant integrity concern (e.g., identity propagation missing, evidence join failure)
- **MEDIUM**: Notable anomaly (e.g., trace linkage issues, refusal drift)
- **LOW**: Minor deviation (informational)

### 5.4 Linkage Keys

Collapse events use the same linkage keys as ledger rows:
- `request_id` — primary request identifier
- `plan_hash` — links to source plan
- `canonical_hash` — execution artifact identity (M4.1)
- `session_id` — session grouping

---

## 6. Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| M4.1 (Observability closure) | Complete | Uses `canonical_hash` for identity propagation checks |
| M4.2 (Drift baseline) | Partial | Uses baseline metrics for drift detection; baseline artifacts optional |
| M3.5 (Ledger) | Complete | Uses ledger row schema for classification |

---

## 7. Invariants Preserved

- **No execution bypass**: Collapse tracking is read-only; does not affect execution path
- **Fail-closed behavior**: Classification errors are captured in result; do not block
- **Governance boundary**: Collapse tracking operates in observation layer (Layer-4)
- **Shadow isolation**: Does not cross irreversible boundaries
- **Append-only ledger**: Does not modify ledger; only reads
- **Replay compatibility**: Uses same linkage keys as replay

---

## 8. Test Evidence

### Tests Added

- `test_collapse_models.py` — 8 tests for event models
- `test_collapse_classifier.py` — 14 tests for classifier
- `test_collapse_queries.py` — 10 tests for query service
- `test_collapse_filter.py` — 2 tests for filter

### Test Coverage

| Collapse Class | Test Coverage |
|----------------|---------------|
| `identity_propagation_missing` | ✓ Ledger row classification |
| `decision_execution_mismatch` | ✓ Posture/outcome conflict, canonical_hash mismatch |
| `replay_mismatch` | ✓ Hash, posture, exit_code mismatch |
| `missing_trace_linkage` | ✓ Missing join keys |
| `unexpected_refusal_distribution_drift` | ✓ Refusal rate, crossed count |
| `missing_evidence_join` | ✓ Incomplete chain, execution without decision |

---

## 9. Usage Examples

### Classify Ledger Rows

```python
from runtime.observation import CollapseClassifier

classifier = CollapseClassifier(require_canonical_hash=True)
events = classifier.classify_ledger_row(ledger_row)

for event in events:
    print(f"{event.collapse_class.value}: {event.description}")
```

### Classify Batch

```python
result = classifier.classify_batch(
    ledger_rows=rows,
    trace_summaries=traces,
    baseline_metrics=baseline,
    current_metrics=current,
)

if result.has_critical():
    print("Critical collapse detected!")
```

### Query Events

```python
from runtime.observation import CollapseQueryService, CollapseFilter

service = CollapseQueryService.from_events(events)

# Get critical events
critical = service.get_critical()

# Filter by class and time
filter_ = CollapseFilter(
    collapse_classes=[CollapseClass.DECISION_EXECUTION_MISMATCH],
    start_time="2026-03-13T00:00:00Z",
)
matching = service.query(filter_)
```

---

## 10. Known Limitations

1. **No persistent storage**: Events are in-memory only; persistence requires external store
2. **No real-time streaming**: Batch classification only; no streaming interface
3. **Baseline metrics optional**: Drift detection requires baseline; gracefully skips if absent
4. **No automatic GREG escalation**: Escalation is M4.5 scope

---

## 11. Merge Readiness

| Criterion | Status |
|-----------|--------|
| Implementation complete | ✓ |
| Tests passing | ✓ |
| No protected files modified | ✓ |
| No architecture changes | ✓ |
| Invariants preserved | ✓ |
| Documentation complete | ✓ |

**Merge dependencies:**
- M4.1 (Observability closure) — for `canonical_hash` identity checks (already merged)
- M4.2 (Drift baseline) — for baseline drift detection (already merged)
- M4.4 (Ledger reconciliation) — coexists in observation package (already merged)

**Integration notes:**
- M4.1, M4.2, and M4.4 are already merged into `integration/m4x-program`
- M4.3 exports are additive over existing observation package
- All existing exports preserved; no breaking changes

---

## 12. Follow-up Work

- **M4.5 (GREG escalation)**: Trigger GREG audit on critical collapses
- **M4.6 (Runtime metrics)**: Include collapse counts in metrics

---

*End of M4.3 implementation note.*

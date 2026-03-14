# Branch Execution Note: feature/m4.1-observability-closure

## Objective

Implement M4.1 observability closure: runtime evidence reconstruction, aggregate queries, CLI reports, and plugin explanation payloads.

## Boundaries

- **In scope**: TraceBuilder, RuntimeSummaryQueries, CLI report, ExplanationBuilder, tests, milestone note
- **Out of scope**: Architecture changes, doctrine modifications, Plan-Gate logic, DeterministicGuard logic, ledger schema changes

## Files Changed

### New Files (runtime/observation/)

| File | Purpose |
|------|---------|
| `runtime/observation/__init__.py` | Package exports |
| `runtime/observation/models.py` | Data models (TraceEvent, ExecutionTrace, RuntimeSummary, ExplanationPayload) |
| `runtime/observation/trace_builder.py` | TraceBuilder class |
| `runtime/observation/summary_queries.py` | RuntimeSummaryQueries class |
| `runtime/observation/explanation_builder.py` | ExplanationBuilder class |
| `runtime/observation/report_runtime_summary.py` | CLI entry point |

### New Test Files

| File | Test Count |
|------|------------|
| `runtime/tests/test_trace_builder.py` | 11 tests |
| `runtime/tests/test_runtime_summary_queries.py` | 16 tests |
| `runtime/tests/test_report_runtime_summary.py` | 17 tests |
| `runtime/tests/test_explanation_builder.py` | 15 tests |

### Documentation

| File | Purpose |
|------|---------|
| `docs/runtime/milestones/M4_1_OBSERVABILITY_CLOSURE.md` | Milestone note |
| `docs/runtime/branch_execution_notes/feature-m4.1-observability-closure.md` | This file |

## Tests Run

```
python3 -m pytest runtime/tests/test_trace_builder.py \
                  runtime/tests/test_runtime_summary_queries.py \
                  runtime/tests/test_report_runtime_summary.py \
                  runtime/tests/test_explanation_builder.py -v

Result: 59 passed in 0.89s
```

## Evidence Summary

1. **TraceBuilder**: Builds execution traces by request_id or canonical_hash with deterministic timestamp ordering; backward compatible with legacy rows
2. **RuntimeSummaryQueries**: Aggregates totals, posture distribution, top refusals, backend stats, replay count, canonical hashes
3. **CLI Report**: Three modes (--summary, --request-id, --canonical-hash) with text and JSON output
4. **ExplanationBuilder**: Human-readable payloads from TraceEvent, LedgerRow, or GovernedExecutionResult
5. **Tests**: 59 tests covering all components, edge cases, and serialization

## Known Limitations

- Observation layer is read-only; does not emit any ledger rows
- CLI requires --ledger-path or MOTADATA_EXECUTE_LEDGER_PATH env var
- Replay count heuristic based on canonical_hash appearing with multiple request_ids

## Merge Risks

- **Low risk**: Additive-only changes; new package does not modify existing code
- **No regression risk**: Prior M4.1 slices (1-4) remain unchanged
- **No architecture drift**: Observation reads ledger, does not alter execution flow

## Invariants Preserved

- ✅ No execution bypass
- ✅ Fail-closed behavior
- ✅ Governance boundary
- ✅ Shadow isolation
- ✅ Append-only ledger
- ✅ Replay compatibility

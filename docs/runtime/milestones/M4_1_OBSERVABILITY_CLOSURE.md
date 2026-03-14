# M4.1 Observability Closure — Milestone Note

**Status:** COMPLETE  
**Branch:** `feature/m4.1-observability-closure`  
**Date:** 2026-03-13

## Objective

Close the M4.1 observability surface so runtime evidence becomes reconstructable, explainable, and demo-ready. This milestone provides the observability layer needed for Layer-4 drift detection and GREG escalation.

## Scope

1. **TraceBuilder** — Build execution traces from ledger evidence
2. **Runtime Summary Queries** — Aggregate statistics for dashboards
3. **CLI Runtime Report** — Command-line observability interface
4. **Explanation Builder** — Human-readable payloads for plugin/UI

## Artifacts

### Core Implementation

| File | Purpose |
|------|---------|
| `runtime/observation/__init__.py` | Package exports |
| `runtime/observation/models.py` | TraceEvent, ExecutionTrace, RuntimeSummary, ExplanationPayload dataclasses |
| `runtime/observation/trace_builder.py` | TraceBuilder: build_by_request_id, build_by_canonical_hash |
| `runtime/observation/summary_queries.py` | RuntimeSummaryQueries: totals, postures, refusals, backends |
| `runtime/observation/explanation_builder.py` | ExplanationBuilder: human-readable payloads |
| `runtime/observation/report_runtime_summary.py` | CLI for --summary, --request-id, --canonical-hash |

### Tests

| File | Purpose |
|------|---------|
| `runtime/tests/test_trace_builder.py` | 11 tests: request_id lookup, canonical_hash lookup, deterministic ordering, backward compatibility |
| `runtime/tests/test_runtime_summary_queries.py` | 16 tests: totals, postures, refusals, backends, replay count, canonical hashes |
| `runtime/tests/test_report_runtime_summary.py` | 17 tests: CLI modes, text/JSON output, error handling |
| `runtime/tests/test_explanation_builder.py` | 15 tests: all decision types, event mappings, serialization |

## Requirements Satisfied

### TraceBuilder

- ✅ `build_by_request_id(request_id)` returns ExecutionTrace with all events
- ✅ `build_by_canonical_hash(canonical_hash)` aggregates events across multiple requests
- ✅ Deterministic ordering by timestamp_utc
- ✅ Backward compatible with older rows missing canonical_hash or intent_id

### Runtime Summary Queries

- ✅ Total requests
- ✅ Refused / deferred / bounded_allow / executed posture distribution
- ✅ Top refusal reasons with counts and example request_ids
- ✅ Backend distribution with success/failure rates
- ✅ Replay count (same canonical_hash, different request_ids)
- ✅ Unique canonical hashes
- ✅ Recent events (most recent first)
- ✅ Time range (earliest/latest events)

### CLI Runtime Report

- ✅ `--summary` mode: aggregate statistics
- ✅ `--request-id <id>` mode: trace by request_id
- ✅ `--canonical-hash <hash>` mode: trace by canonical_hash
- ✅ `--json` flag: JSON output for programmatic consumption
- ✅ `--ledger-path` or `MOTADATA_EXECUTE_LEDGER_PATH` env var

### Plugin Explanation Payload

- ✅ `decision`: refused / deferred / bounded_allow / safe_execute / executed / blocked
- ✅ `outcome`: human-readable outcome description
- ✅ `reason`: why this decision was made
- ✅ `canonical_hash`: execution identity
- ✅ `backend`: local_process / container
- ✅ `execution_surface`: execute_service / orchestrator
- ✅ `explanation`: concise human-readable one-sentence explanation
- ✅ Serialization via `to_dict()`

## Invariants Preserved

- ✅ No execution bypass — observation layer reads from ledger, does not modify execution flow
- ✅ Fail-closed behavior — missing data handled gracefully (empty traces, zero counts)
- ✅ Governance boundary — observation does not emit governance decisions
- ✅ Shadow isolation — observation compatible with shadow mode rows
- ✅ Append-only ledger — observation only reads, never writes ledger
- ✅ Replay compatibility — canonical_hash traces support replay analysis

## Integration Points

### Ledger Stores

- Reads from `SandboxLedgerStore` (SQLite, append-only)
- Compatible with existing schema including `canonical_hash` index (M4.1 Slice-4)
- Backward compatible with pre-canonical_hash rows

### Prior M4.1 Slices

- **Slice 1**: CanonicalExecutionIntent, CommandNormalizer
- **Slice 2**: DeterministicGuard, Plan-Gate integration
- **Slice 3**: Ledger identity propagation (canonical_hash in payloads)
- **Slice 4**: canonical_hash indexed column, get_by_canonical_hash

### Layer-4 Ready

- RuntimeSummaryQueries provides data for M4.2 Drift Baseline
- TraceBuilder enables M4.3 Collapse Vector Tracking
- Explanation payloads support M4.5 GREG Escalation evidence bundles

## CLI Usage

```bash
# Summary mode
python -m runtime.observation.report_runtime_summary --ledger-path /path/to/ledger.db --summary

# Request trace mode
python -m runtime.observation.report_runtime_summary --ledger-path /path/to/ledger.db --request-id req-001

# Canonical hash trace mode
python -m runtime.observation.report_runtime_summary --ledger-path /path/to/ledger.db --canonical-hash abc123...

# JSON output
python -m runtime.observation.report_runtime_summary --ledger-path /path/to/ledger.db --summary --json
```

## Test Evidence

```
59 passed in 0.89s

runtime/tests/test_trace_builder.py .................... 11 passed
runtime/tests/test_runtime_summary_queries.py .......... 16 passed
runtime/tests/test_report_runtime_summary.py ........... 17 passed
runtime/tests/test_explanation_builder.py .............. 15 passed
```

## Dependencies

- M3.8 Ledger Emission (COMPLETE)
- M4.1 Slice 1-4 (COMPLETE)

## Follow-up

- M4.2: Use RuntimeSummaryQueries for drift baseline establishment
- M4.3: Use TraceBuilder for collapse vector identification
- M4.6: Integrate RuntimeSummary into runtime metrics dashboards

## Merge Readiness

- ✅ All tests passing (59/59)
- ✅ No architecture changes
- ✅ Backward compatible with existing ledger
- ✅ Documentation complete
- ✅ Ready for merge to `main` after M4.1 branch integration

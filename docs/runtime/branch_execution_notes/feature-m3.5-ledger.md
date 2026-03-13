# Branch Execution Notes — feature/m3.5-ledger

## Branch Information

- **Branch name**: `feature/m3.5-ledger`
- **Baseline tag**: `layer3-runtime-baseline`
- **Created from**: `0283a2e` (Merge integration/layer3-runtime-stack into main — Layer-3 baseline)

## Milestone Objective

**M3.5 — Ledger Completeness and Replay**

Ensure that every governed runtime decision produces a deterministic append-only ledger record that supports:

1. **Deterministic replay**: Same inputs produce identical ledger outputs
2. **Plan ↔ Decision ↔ Execution linkage**: Full traceability via `(request_id, plan_hash)`
3. **Audit join**: Reconciliation between plan, decision, and ledger rows

## Allowed Files

### Primary Implementation
- `runtime/ledger/**` (new directory for ledger core)
- `runtime/emulator/ledger.py` (existing emulator ledger)
- `runtime/sandbox/sandbox_ledger.py` (existing sandbox ledger)
- `runtime/tests/ledger_*` (new ledger tests)

### Minimal Edits (for emission hooks)
- `runtime/orchestrator/**` (narrow hooks for ledger emission)
- `runtime/state/**` (replay metadata support)

### Documentation
- `docs/runtime/ledger/**` (new ledger documentation)
- `docs/runtime/branch_execution_notes/feature-m3.5-ledger.md` (this file)

## Forbidden Files

- `runtime/shadow/**`
- `runtime/context/**`
- `jetbrains-plugin/**`
- `runtime/ask_service/**`
- `governance/**`
- `ml/**`
- Schema files in `runtime/schemas/` (already defined)

## Mandatory Invariants

1. **Append-only ledger**: No record mutation or deletion
2. **Exact boundary phrase match**: `irreversible_boundary_phrase` must match plan exactly
3. **Join key**: Must remain `(request_id, plan_hash)`
4. **Invalid combinations rejected**: e.g., `authority_fail + boundary_crossed` is impossible

## Planned Tests

### Existing Tests (must pass)
- `test_sandbox_ledger_store.py` — existing ledger store tests
- `test_emulator_invariants.py` — emulator invariant tests

### New Tests
1. **Append-only enforcement**: Verify no mutation/delete operations exist
2. **Deterministic event_id/plan_hash linkage**: Same input → same hash
3. **Replay of traced runtime session**: Full session reconstruction
4. **No duplicate ledger emission**: Simple REF refusal produces single ledger row
5. **Invalid ledger combinations rejected**: Authority fail + crossed blocked
6. **Plan-hash linkage test**: Verify plan_hash links ledger to plan
7. **Sandbox execution ledger row**: Execution produces proper ledger

## Deliverables Checklist

- [x] **Ledger emission hooks**: Unified ledger emission from all runtime decision points
- [x] **Replay utility**: Tool to reconstruct runtime session from ledger
- [x] **Ledger reconciliation helpers**: Join utilities for audit
- [x] **Replay example trace**: Sample traced session with full linkage
- [x] **Ledger completeness report**: Documentation of coverage
- [x] **Transition-to-ledger mapping note**: How transitions map to ledger rows
- [x] **Replay/join contract note**: API contract for replay/join operations

## Completion Checklist

- [x] Branch created from `layer3-runtime-baseline`
- [x] Only assigned milestone implemented
- [x] Allowed file boundaries respected
- [x] Protected files untouched
- [x] Tests added/updated
- [x] All relevant tests pass
- [x] Branch execution note completed
- [x] PR description prepared with evidence
- [x] No doctrine drift
- [x] No fail-open path introduced
- [x] No sandbox/ledger semantic regression introduced

## Evidence Summary

### Artifacts Implemented (7/7)

1. **runtime/ledger/__init__.py** — Module exports
2. **runtime/ledger/contracts.py** — LedgerRowV1, event types, replay session contracts
3. **runtime/ledger/emitter.py** — LedgerEmitterV1 with deterministic emission
4. **runtime/ledger/store.py** — LedgerStore with append-only SQLite persistence
5. **runtime/ledger/replay.py** — LedgerReplay with session reconstruction and reconciliation
6. **runtime/ledger/demo_trace.py** — Sample traced session demonstrating linkage
7. **runtime/tests/test_ledger_completeness.py** — 33 comprehensive tests

### Documentation (3/3)

1. **docs/runtime/ledger/LEDGER_REPLAY_JOIN_CONTRACT.md** — Replay/join API contract
2. **docs/runtime/ledger/TRANSITION_TO_LEDGER_MAPPING.md** — Transition-to-ledger mapping
3. **docs/runtime/branch_execution_notes/feature-m3.5-ledger.md** — This file

### Test Results

```
runtime/tests/test_ledger_completeness.py: 33 passed
runtime/tests/test_emulator_invariants.py: 28 passed (regression)
runtime/tests/test_sandbox_ledger_store.py: 8 passed (regression)
runtime/tests/test_transition_executor.py: 26 passed (regression)
```

### Demo Trace Output

- REF refusal: Single ledger row, authority=fail, posture=refuse
- CONF bounded_allow: Single ledger row, authority=pass, boundary=allowed_pre_boundary_only
- DES safe_execute with execution: Two ledger rows (decision + execution)
- Replay reconstruction: Complete sessions with plan/decision/execution events
- Join key reconciliation: Verified (request_id, plan_hash) linkage
- No duplicate emissions: Validated

### Invariants Verified

- L1: ref_enforced → phase_emitted in (REF, MIX)
- L2: boundary_crossed → boundary_verdict == "crossed"
- L3: attempted but not crossed → boundary_verdict == "blocked"
- L4: authority_fail + crossed is INVALID
- Append-only: No delete/update methods on LedgerStore
- Deterministic: Same inputs produce identical event_id and plan_hash

## Known Limitations / Follow-ups

1. **Layer-4 Integration**: Ledger is ready for L4 observation ingestion but bridge not wired
2. **Production Persistence**: SQLite suitable for MVP; production may need distributed store
3. **Shadow Mode**: Full shadow mode validation is M3.6 scope

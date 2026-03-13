# Branch Execution Notes — feature/m3.1-orchestrator

## Branch Metadata

| Field | Value |
|-------|-------|
| **Branch name** | `feature/m3.1-orchestrator` |
| **Baseline tag** | `layer3-runtime-baseline` |
| **Milestone** | M3.1 — Agent Loop Orchestrator |
| **Created** | 2026-03-13 |

## Milestone Objective

Complete the **Agent Loop Orchestrator** as the runtime governor path, implementing:

1. **Loop Controller** — Deterministic transition executor with state machine semantics
2. **Transition Executor** — Execute transitions with guard evaluation and context wiring
3. **Retry/Iteration Budget** — Enforced limits on retries and loop iterations
4. **Stop Conditions** — Explicit terminal conditions and forced termination paths
5. **Sandbox Invocation** — Integration seam for sandbox execution
6. **Ledger Linkage** — Minimal interface for ledger emission hooks

Core design rule: **The model proposes; the runtime decides.**

## Allowed Files

### Primary (full ownership)

- `runtime/orchestrator/**`
- `runtime/state/**`
- `runtime/tests/test_transition_executor.py`
- `runtime/tests/orchestrator_*`

### Touch Only If Strictly Necessary

- `runtime/context/**` — interface consumption, not redesign
- `runtime/sandbox/**` — orchestrator invocation seam only

## Forbidden Files

- `runtime/ledger/**`
- `runtime/shadow/**`
- `jetbrains-plugin/**`
- `schemas/**`
- `governance/**`
- `ml/**`
- `docs/CONSTITUTION*`
- `docs/governance/**`
- `docs/MASTER_SYSTEM_SPEC.md`
- `runtime/ide/schemas/plan_request.v0.1.schema.json`
- `runtime/ide/schemas/decision_response.v0.1.schema.json`
- `runtime/schemas/plan.v0.1.schema.json`
- `runtime/schemas/ledger_row.v0.1.schema.json`

## Planned Tests

### Transition Executor Tests

- [ ] Valid transitions succeed
- [ ] Invalid transitions rejected
- [ ] Terminal states non-escaping
- [ ] Guards evaluated correctly

### Loop Controller Tests

- [ ] Iteration cap enforced
- [ ] Retry logic correct
- [ ] Consecutive repetition guard
- [ ] Context-fetch failure is fail-closed

### Orchestrator Integration Tests

- [ ] Sandbox handoff path works
- [ ] Plan-Gate integration correct
- [ ] Deterministic replay from task state history
- [ ] Terminal non-escaping states enforced

## Completion Checklist

- [x] Branch created from `layer3-runtime-baseline`
- [x] Only assigned milestone implemented
- [x] Allowed file boundaries respected
- [x] Protected files untouched
- [x] Loop controller spec completion
- [x] Transition executor design completion
- [x] Retry/iteration budget rules documented
- [x] Stop condition rules documented
- [x] Tests added/updated
- [x] All relevant tests pass
- [x] Branch execution note completed
- [x] PR description prepared with evidence
- [x] No doctrine drift
- [x] No fail-open path introduced
- [x] No sandbox/ledger semantic regression

## Evidence Summary

### Test Results

```
runtime/tests/orchestrator_test_suite.py: 48 passed
runtime/tests/test_transition_executor.py: 26 passed
runtime/tests/ (full suite): 253 passed, 10 skipped
```

### Artifacts Created

| Artifact | Purpose |
|----------|---------|
| `runtime/orchestrator/stop_conditions.py` | Stop condition policy with all reason categories |
| `runtime/orchestrator/budget_policy.py` | Retry/iteration budget enforcement |
| `runtime/orchestrator/transition_executor.py` | Transition execution with handlers and hooks |
| `runtime/orchestrator/replay.py` | Deterministic replay utilities |
| `runtime/tests/orchestrator_test_suite.py` | Comprehensive orchestrator test suite (48 tests) |
| `docs/runtime/milestones/M3.1_AGENT_LOOP_ORCHESTRATOR.md` | Loop controller spec and design |

### Key Capabilities Implemented

1. **Stop Condition Policy**: 11 stop reasons mapped to 4 terminal states
2. **Budget Policy**: Iteration and repetition budgets with warnings
3. **Transition Executor**: Handler registration, pre/post hooks
4. **Replay Engine**: Deterministic replay with validation
5. **Full Integration**: All components wired through LoopController

## Known Limitations / Follow-ups

1. **Token budget**: Configured but not fully wired (requires model integration)
2. **Time budget**: Configured but optional (requires task timing)
3. **Forced terminal transitions**: Policy exists but not auto-applied in LoopController
4. **Ledger emission hooks**: Use existing ledger_store interface, not direct emission

## Files Changed

### New Files (6)

- `runtime/orchestrator/stop_conditions.py`
- `runtime/orchestrator/budget_policy.py`
- `runtime/orchestrator/transition_executor.py`
- `runtime/orchestrator/replay.py`
- `runtime/tests/orchestrator_test_suite.py`
- `docs/runtime/milestones/M3.1_AGENT_LOOP_ORCHESTRATOR.md`

### Modified Files (2)

- `runtime/orchestrator/__init__.py` — Added exports for new modules
- `docs/runtime/branch_execution_notes/feature-m3.1-orchestrator.md` — This file

# [M3.6] Implement Shadow Mode Validation — PR description

## Milestone goal

Implement shadow mode execution that runs the full governed runtime pipeline without crossing irreversible boundaries. Shadow mode emits plan, runs the decision engine, emits ledger, never crosses irreversible boundaries, and produces ingestion artifacts (log-only enforcement).

## Files changed

### Added
- `docs/runtime/branch_execution_notes/feature-m3.6-shadow.md`
- `docs/runtime/branch_execution_notes/PR_M3_6_SHADOW.md`
- `docs/runtime/shadow/M3_6_SHADOW_PROTOCOL_IMPLEMENTATION_NOTE.md`
- `docs/runtime/shadow/M3_6_BASELINE_SCENARIOS.md`
- `docs/runtime/shadow/M3_6_SHADOW_VALIDATION_REPORT.md`
- `runtime/shadow/__init__.py`
- `runtime/shadow/baseline_scenarios.py`
- `runtime/shadow/ingestion_batch.py`
- `runtime/shadow/runner.py`
- `runtime/shadow/harness.py`
- `runtime/tests/shadow_runner_test.py`
- `runtime/tests/shadow_harness_test.py`

### Modified (minimal)
- `runtime/plan_gate_stub/plan_gate.py` — `evaluate_plan()` returns `(PlanDecision, LedgerRow, plan_dict)` for shadow artifact plumbing.
- `runtime/shadow_runner/run_demo.py` — unpack third return value from `evaluate_plan()`.
- `runtime/tests/test_emulator_invariants.py` — unpack third return value from `evaluate_plan()` in all call sites.

## Tests run

- `runtime/tests/shadow_runner_test.py` — 11 tests (plan emission, ledger emission, no boundary crossed, REF/CONF/DES).
- `runtime/tests/shadow_harness_test.py` — 11 tests (harness pass, S-1/S-2/S-3/S-6, ingestion batch structure).
- `runtime/shadow/tests/test_shadow_protocol_v0_1.py` — 11 tests (schemas and shadow rules).
- `runtime/tests/test_emulator_invariants.py` — 28 tests (regression).
- `python3 -m runtime.shadow_runner.run_demo` — 3 scenarios, all invariants held.

## Evidence summary

- All 33 shadow-related tests pass; 28 emulator invariant tests pass.
- Shadow runner demo: merge_without_approval → REF/refuse, commit_prod_change → CONF/bounded_allow, safe_commit → DES/safe_execute; no boundary_verdict=crossed.

## Known limitations

- Ledger normalization (for full schema compliance in ingestion batch) is done in `runtime/shadow/ingestion_batch.py`; emulator ledger output remains minimal.
- Observation ingest CLI validation (e.g. plan/ledger runtime rules) may be run separately on produced batches.

## Merge risk

- **Low.** Changes are additive under `runtime/shadow/**` and `runtime/tests/shadow_*.py`. Only narrow edits in `plan_gate_stub/plan_gate.py` (return value), `shadow_runner/run_demo.py`, and `test_emulator_invariants.py` (unpacking). No doctrine or schema file changes.

## Dependency on prior PRs

- None. Branch is from `layer3-runtime-baseline`. Can merge independently; recommended merge order remains M3.1 → M3.5 → M3.6.

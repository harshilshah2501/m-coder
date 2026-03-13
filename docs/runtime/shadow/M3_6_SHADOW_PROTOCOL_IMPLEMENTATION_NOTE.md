# M3.6 Shadow Mode Protocol — Implementation Note

## Purpose

Shadow mode is **log-only enforcement**: the full governed runtime pipeline runs without crossing irreversible boundaries. Every intercepted action emits plan, decision, and ledger; `boundary_verdict` is never `crossed` and `boundary_crossed` is always false.

## Implementation Summary

- **Shadow runner** (`runtime/shadow/runner.py`): Runs baseline scenarios through `PlanGate(mode="shadow")`, produces `ShadowRunResult` (plan, ledger, shadow run record) per scenario, and can build an `ingestion_batch.v0.1` from results.
- **Baseline scenarios** (`runtime/shadow/baseline_scenarios.py`): Corpus of REF, CONF, and DES scenarios (e.g. merge_without_approval → REF/refuse, commit_prod_change → CONF/bounded_allow, safe_commit → DES/safe_execute).
- **Validation harness** (`runtime/shadow/harness.py`): Runs scenarios and asserts S-1 (no crossed), S-2 (plan + ledger emitted), S-3 (plan_hash linkage), S-6 (ingestion batch structure).
- **Ingestion batch** (`runtime/shadow/ingestion_batch.py`): Builds `ingestion_batch.v0.1` from run results; normalizes emulator ledger output to full `ledger_row.v0.1` schema (adds `runtime_version`, `plan_schema_version`, `ref_enforced`, `boundary_cross_attempted`, `actions`).

## Invariants Enforced

| Rule | Constraint |
|------|------------|
| S-1 | In shadow, `boundary_verdict` ≠ crossed; `boundary_crossed` = false |
| S-2 | Every run emits plan AND ledger |
| S-3 | `decision_response.plan_hash` == `plan_hash`; ledger `plan_link.plan_hash` matches |
| S-6 | Ingestion batch items include `request_id`, `plan`, `ledger_row` |

## Plan-Gate Plumbing

To support shadow artifact emission, `PlanGate.evaluate_plan()` was extended to return a third value, the **plan dict**, so the shadow layer can include it in ingestion batches without reconstructing it. Call sites (shadow_runner, tests) were updated to unpack `(decision, ledger_row, plan)`.

## Usage

- Run baseline scenarios and validate:  
  `from runtime.shadow.harness import ShadowValidationHarness; r = ShadowValidationHarness().run(); assert r.passed`
- Run shadow runner demo:  
  `python3 -m runtime.shadow_runner.run_demo`
- Run M3.6 tests:  
  `pytest runtime/tests/shadow_runner_test.py runtime/tests/shadow_harness_test.py runtime/shadow/tests/`

## Dependencies

- M3.6 is implemented on top of the existing PlanGate emulator and ledger; it does not depend on M3.5 ledger completeness. If M3.5 adds broader ledger persistence, shadow can feed the same ingestion batch format.

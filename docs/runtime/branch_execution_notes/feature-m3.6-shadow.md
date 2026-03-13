# Branch Execution Notes: feature/m3.6-shadow

## Branch identity

- **Branch name:** `feature/m3.6-shadow`
- **Baseline tag:** `layer3-runtime-baseline`
- **Milestone:** M3.6 — Shadow Mode Validation

## Milestone objective

Implement shadow mode execution that runs the full governed runtime pipeline without crossing irreversible boundaries. Shadow mode must:

- Emit plan
- Run decision engine
- Emit ledger
- Never cross irreversible boundaries
- Produce ingestion artifacts

Shadow is **log-only enforcement**.

## Allowed files

- `runtime/shadow/**` (runner, harness, ingestion batch builder, baseline scenarios)
- `runtime/shadow_runner/**` (expand demo / harness integration only)
- `runtime/plan_gate_stub/**` only if required for shadow artifact plumbing
- `runtime/plan_gate_service/**` only for shadow artifact plumbing
- `runtime/tests/**` for shadow tests (`shadow_*`)
- `observation/ingest/**` only if required to support ingestion batch validation
- `docs/runtime/**` and `docs/runtime/**`
- `docs/runtime/branch_execution_notes/feature-m3.6-shadow.md`

## Forbidden files

- `runtime/context/**`
- `runtime/orchestrator/**` (core state machine semantics)
- `runtime/ledger/**`
- `jetbrains-plugin/**`
- `governance/**`, `ml/**`
- Schema files under `runtime/schemas/`, `runtime/ide/schemas/`

## Mandatory invariants

- In shadow, `boundary_verdict` must never be `crossed`; `boundary_crossed` must remain false.
- Every run must emit plan and ledger (even on error).
- Semantic resolution must be lineage-based or unresolved, never guessed.
- If gate unreachable and client fail-closed policy is true, block rather than bypass.

## Planned tests

- Shadow plan emission
- Shadow ledger emission
- No boundary crossed assertion (S-1)
- Ingestion batch structure (request_id, plan, ledger_row; S-6)
- decision_response.plan_hash matches plan_hash and ledger linkage (S-3)
- Representative REF / CONF / DES safe-shadow scenarios

## Completion checklist

- [x] Branch created from `layer3-runtime-baseline`
- [x] Only M3.6 milestone implemented
- [x] Allowed file boundaries respected
- [x] Protected files untouched
- [x] Tests added/updated; all relevant tests pass
- [x] Branch execution note completed
- [x] Shadow protocol implementation note written
- [x] Baseline scenario list documented
- [x] Shadow validation report produced
- [x] PR description prepared with evidence
- [x] No doctrine drift; no fail-open path

## Evidence summary

- **Commands run:**
  - `python3 -m pytest runtime/tests/shadow_runner_test.py runtime/tests/shadow_harness_test.py runtime/shadow/tests/test_shadow_protocol_v0_1.py -v`
  - `python3 -m pytest runtime/tests/test_emulator_invariants.py -v`
  - `python3 -m runtime.shadow_runner.run_demo`
- **Pass/fail:** All 33 shadow-related tests PASS; 28 emulator invariant tests PASS; demo PASS (3 scenarios, invariants held).
- **Known limitations / follow-ups:**
  - Emulator ledger `to_dict()` does not include `event.runtime_version`, `plan_link.plan_schema_version`, `verdicts.ref_enforced`, `boundary.boundary_cross_attempted`, `actions`; normalization in `runtime/shadow/ingestion_batch.py` adds these for ingestion batch only.
  - Prefer merging M3.5 (ledger completeness) before or after M3.6; shadow does not depend on it but ingestion batch format aligns with observation/ingest.

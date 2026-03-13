# Layer-3 Parallel Branch Audit Report

**Audit date:** 2026-03-13  
**Baseline tag:** `layer3-runtime-baseline`  
**Branches audited:** `feature/m3.1-orchestrator`, `feature/m3.5-ledger`, `feature/m3.6-shadow`  
**Auditor:** Verification and merge-readiness agent (governed audit mode)

> **Provenance note:** For current canonical baseline tag resolution (e.g. `layer3-runtime-baseline` commit SHA), verify against [GIT_PROVENANCE_AUDIT.md](GIT_PROVENANCE_AUDIT.md). This report is historical; refs and SHAs in the body reflect the audit as run at the date above.

---

## 1. Repository Preparation

- **Clean state:** Repo had untracked files only (AGENT_EXECUTION_RULES.md, docs, etc.); no uncommitted changes to tracked files during audit. Stash used when switching branches.
- **Fetch:** `git fetch --all --tags` completed; `origin/feature/m3.1-orchestrator` and `origin/feature/m3.5-ledger` fetched.
- **Refs confirmed:**
  - `main` — present (local)
  - `layer3-runtime-baseline` — tag present, points to `999f41c779cca775f631051d13b2fc7c2cfd9eb9`
  - `feature/m3.1-orchestrator` — present as `origin/feature/m3.1-orchestrator`
  - `feature/m3.5-ledger` — present as `origin/feature/m3.5-ledger`
  - `feature/m3.6-shadow` — present (local branch)

---

## 2. Phase 1 — Baseline Ancestry Check

| Branch | merge_base(branch, layer3-runtime-baseline) | Baseline in history | Files changed (vs baseline) | Scope match |
|--------|--------------------------------------------|---------------------|-----------------------------|-------------|
| main | 0283a2ed | Yes (baseline is ancestor of main) | N/A | N/A |
| origin/feature/m3.1-orchestrator | 0283a2ed | Yes | 8 files, +2932 −1 | Yes |
| origin/feature/m3.5-ledger | 0283a2ed | Yes | 10 files, +3690 | Yes |
| feature/m3.6-shadow | 0283a2ed | Yes | 15 files, +1089 −24 | Yes |

- All three feature branches share the same common ancestor with the baseline tag (0283a2ed). The baseline tag is an ancestor of main; the branches are descended from the same lineage that contains the baseline. **Ancestry: PASS.**
- No branch started from an unexpected base.
- Diff scope vs baseline matches claimed milestone intent (orchestrator, ledger, shadow).

---

## 3. Phase 2 — File-Boundary Discipline

### 3.1 feature/m3.1-orchestrator

| File | Classification | Notes |
|------|----------------|-------|
| docs/runtime/milestones/M3.1_AGENT_LOOP_ORCHESTRATOR.md | Allowed | Docs |
| docs/runtime/branch_execution_notes/feature-m3.1-orchestrator.md | Allowed | Docs |
| runtime/orchestrator/__init__.py | Allowed | M3.1 allowed runtime/orchestrator/** |
| runtime/orchestrator/budget_policy.py | Allowed | M3.1 allowed |
| runtime/orchestrator/replay.py | Allowed | M3.1 allowed |
| runtime/orchestrator/stop_conditions.py | Allowed | M3.1 allowed |
| runtime/orchestrator/transition_executor.py | Allowed | M3.1 allowed |
| runtime/tests/orchestrator_test_suite.py | Allowed | M3.1 allowed orchestrator_* |

**Boundary verdict:** No protected files touched. No runtime/state/**, context/**, or sandbox/** changes; scope within allowed. **PASS.**

### 3.2 feature/m3.5-ledger

| File | Classification | Notes |
|------|----------------|-------|
| docs/runtime/branch_execution_notes/feature-m3.5-ledger.md | Allowed | Docs |
| docs/runtime/ledger/LEDGER_REPLAY_JOIN_CONTRACT.md | Allowed | docs/runtime/ledger/** |
| docs/runtime/ledger/TRANSITION_TO_LEDGER_MAPPING.md | Allowed | docs/runtime/ledger/** |
| runtime/ledger/__init__.py | Allowed | runtime/ledger/** |
| runtime/ledger/contracts.py | Allowed | runtime/ledger/** |
| runtime/ledger/demo_trace.py | Allowed | runtime/ledger/** |
| runtime/ledger/emitter.py | Allowed | runtime/ledger/** |
| runtime/ledger/replay.py | Allowed | runtime/ledger/** |
| runtime/ledger/store.py | Allowed | runtime/ledger/** |
| runtime/tests/test_ledger_completeness.py | Allowed | ledger_* tests |

**Boundary verdict:** No runtime/emulator/ledger.py or runtime/sandbox/sandbox_ledger.py changes in this branch (claimed “minimal allowed” for those). No protected surfaces touched. **PASS.**

### 3.3 feature/m3.6-shadow

| File | Classification | Notes |
|------|----------------|-------|
| docs/runtime/branch_execution_notes/PR_M3_6_SHADOW.md | Allowed | Docs |
| docs/runtime/branch_execution_notes/feature-m3.6-shadow.md | Allowed | Docs |
| docs/runtime/shadow/*.md | Allowed | docs/runtime/shadow/** |
| runtime/plan_gate_stub/plan_gate.py | Minimal allowed | M3.6 minimal: plan_gate_stub/** |
| runtime/shadow/__init__.py, baseline_scenarios.py, harness.py, ingestion_batch.py, runner.py | Allowed | runtime/shadow/** |
| runtime/shadow_runner/run_demo.py | Allowed | runtime/shadow_runner/** |
| runtime/tests/shadow_harness_test.py, shadow_runner_test.py | Allowed | shadow_* tests |
| runtime/tests/test_emulator_invariants.py | Minimally acceptable | Shared test; updated for shadow (S-1 shadow_mode_never_crossed). Justified for shadow validation. |

**Boundary verdict:** No governance/**, ml/**, runtime/schemas/**, jetbrains-plugin/**, or protected docs touched. **PASS.**

---

## 4. Phase 3 — Branch-Local Test Verification

### 4.1 feature/m3.1-orchestrator

| Command | Result |
|---------|--------|
| `python3 -m pytest runtime/tests/orchestrator_test_suite.py -v` | **48 passed** |
| `python3 -m pytest runtime/tests/test_transition_executor.py -v` | **26 passed** |
| `python3 -m pytest runtime/tests/ --ignore=runtime/tests/test_emulator_invariants.py -v` | **263 passed** |

Verified: stop conditions, terminal states, iteration/repetition budgets, transition executor hooks, deterministic replay, sandbox handoff integration, terminal-state non-escaping. **PASS.**

### 4.2 feature/m3.5-ledger

| Command | Result |
|---------|--------|
| `python3 -m pytest runtime/tests/test_ledger_completeness.py -v` | **33 passed** |
| `python3 -m pytest runtime/tests/test_emulator_invariants.py -v` | **28 passed** |
| `python3 -m pytest runtime/tests/test_sandbox_ledger_store.py -v` | **8 passed** |
| `python3 -m pytest runtime/tests/test_transition_executor.py -v` | **26 passed** |
| `python3 -m runtime.ledger.demo_trace` | **Exit 0** — “Demo Complete — All invariants satisfied” |

Verified: append-only, replay, plan_hash/request_id join key, deterministic event_id, refusal path emission, duplicate prevention. **PASS.**

### 4.3 feature/m3.6-shadow

| Command | Result |
|---------|--------|
| `python3 -m pytest runtime/tests/shadow_runner_test.py runtime/tests/shadow_harness_test.py -v` | **22 passed** |
| `python3 -m pytest runtime/tests/test_emulator_invariants.py -v` | **28 passed** |
| `python3 -m runtime.shadow_runner.run_demo` | **Exit 0** — “DEMO COMPLETE — All scenarios passed, all invariants held” |

Verified: plan and ledger emitted per run, no boundary_verdict=crossed, boundary_crossed=false, plan_hash alignment, ingestion batch request_id/plan/ledger_row. **PASS.**

---

## 5. Phase 4 — Invariant Review

| Invariant | Classification | Evidence |
|-----------|----------------|----------|
| **Global:** fail-closed preserved | PASS | test_emulator_invariants, test_transition_executor (governance_to_context_missing_file_fail_closed, refusal_ledger_failure_surfaces_fail_closed) |
| **Global:** no bypass path | PASS | No unprotected code paths introduced; Plan-Gate enforced in tests |
| **Global:** runtime decides; model does not own control flow | PASS | Orchestrator/transition executor own state transitions |
| **Ledger:** append-only | PASS | test_no_delete_method_exists, test_no_update_method_exists, test_ledger_row_is_immutable_after_creation (M3.5) |
| **Ledger:** join key (request_id, plan_hash) | PASS | test_join_by_request_id_and_plan_hash, TestPlanHashLinkage (M3.5) |
| **Ledger:** deterministic event_id / plan_hash | PASS | TestDeterministicHashing, test_emitter_produces_deterministic_event_id (M3.5) |
| **Shadow:** no boundary_verdict=crossed | PASS | harness _check_s1; test_no_scenario_emits_crossed; test_shadow_mode_never_crossed |
| **Shadow:** no boundary_crossed=true | PASS | Same S-1 checks; run_demo output shows boundary_crossed: false |
| **Shadow:** plan and ledger always emitted | PASS | _check_s2; test_each_scenario_emits_plan, test_each_scenario_emits_ledger |
| **Orchestrator:** terminal states non-escaping | PASS | test_terminal_state_non_escaping, test_transition_from_terminal_refused |
| **Orchestrator:** iteration budget enforced | PASS | test_iteration_limit_stops, test_repeated_retry_hits_iteration_limit, test_iteration_cap_enforced |
| **Orchestrator:** repetition guard | PASS | test_excessive_repeated_transition_id_rejected, test_consecutive_repetition_guard |
| **Orchestrator:** context/sandbox failure fail-closed | PASS | test_governance_to_context_missing_file_fail_closed, test_refusal_ledger_failure_surfaces_fail_closed |

All invariants: **PASS** (no FAIL or PASS WITH CAVEAT).

---

## 6. Phase 5 — Cross-Branch Conflict Analysis

### 6.1 Changed-file sets

- **M3.1:** 8 files (orchestrator, orchestrator_test_suite, 2 docs).
- **M3.5:** 10 files (ledger/*, test_ledger_completeness, 3 docs).
- **M3.6:** 15 files (shadow/*, shadow_runner/run_demo, plan_gate_stub/plan_gate, test_emulator_invariants, shadow_* tests, docs).

### 6.2 Overlap matrix

| File | M3.1 | M3.5 | M3.6 | Risk |
|------|------|------|------|------|
| Any runtime/orchestrator file | ✓ | — | — | — |
| Any runtime/ledger file | — | ✓ | — | — |
| Any runtime/shadow file | — | — | ✓ | — |
| runtime/tests/test_emulator_invariants.py | — | — | ✓ | Only M3.6 touches it |
| runtime/plan_gate_stub/plan_gate.py | — | — | ✓ | — |

**Conclusion:** No file is modified by more than one branch. Overlap: **none**. Merge conflict risk: **none**. Semantic conflict risk: **low** (no shared code changes).

### 6.3 Hidden dependencies

- **Shadow vs ledger:** M3.6 shadow runner uses emulator/plan-gate and ledger_row shape from baseline (emulator ledger). It does not depend on M3.5’s `runtime/ledger` module; baseline already has ledger_row schema and emulator emission. **No blocker.**
- **Ledger vs orchestrator:** M3.5 does not touch orchestrator or state. **No dependency.**
- **Orchestrator vs ledger/shadow:** M3.1 does not touch ledger or shadow. **No dependency.**

**Conflict table:**

| File | Branches | Risk level | Resolution order |
|------|----------|------------|------------------|
| (none) | — | — | 1. M3.1, 2. M3.5, 3. M3.6 |

---

## 7. Branch-Specific Risks

- **M3.1:** None identified. Claimed “48 new tests” — 48 in orchestrator_test_suite; test_transition_executor exists on baseline; claim consistent.
- **M3.5:** None. M3.5 did not modify runtime/emulator/ledger.py or sandbox_ledger.py; integration with existing emulator ledger is via contracts/schema only.
- **M3.6:** test_emulator_invariants.py is shared; change is additive (shadow_mode_never_crossed). **Risk: low**, explicitly reviewed.

---

## 8. Summary

| Branch | Ancestry | File boundary | Tests | Invariants | Risks |
|--------|----------|---------------|-------|------------|-------|
| feature/m3.1-orchestrator | PASS | PASS | PASS | PASS | None |
| feature/m3.5-ledger | PASS | PASS | PASS | PASS | None |
| feature/m3.6-shadow | PASS | PASS | PASS | PASS | Low (shared test file) |

**Audit result:** All three branches are within scope, tests pass, invariants hold, and there are no cross-branch file conflicts. Integration branch validation is in the separate merge-readiness report.

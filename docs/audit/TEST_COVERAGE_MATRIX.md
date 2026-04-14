# TEST_COVERAGE_MATRIX — Phase 2

**Status:** living document  
**Last updated:** 2026-04-13  
**Companion:** [REPO_LAYOUT_INVENTORY.md](REPO_LAYOUT_INVENTORY.md), [HUMAN_WHOLE_REPO_REVIEW.md](HUMAN_WHOLE_REPO_REVIEW.md)

## Column legend

| Column | Meaning |
|--------|---------|
| **in_product_slice** | `yes` / `partial` / `no` |
| **closure_gate** | Tracker / charter bar this row primarily supports (or `none`) |
| **validation_artifact** | Proof dir/file under `docs/validation/` or `none` |
| **runbook** | Primary operator doc, if any |
| **test_signal** | `strong` = direct invariant / contract tests; `partial` = indirect; `weak` = adjacent only |
| **gap** | Known missing or manual-only coverage |

**Principle:** “Has pytest” ≠ “closure-credible.” This matrix ties tests to **artifacts** and **gates** where the program requires them.

---

## 1. Where tests live

| Location | ~count | Role |
|----------|--------|------|
| [`runtime/tests/`](../../runtime/tests/) | 58 `test_*.py` | **Primary** Python regression suite |
| [`runtime/plan_gate_service/tests/`](../../runtime/plan_gate_service/tests/) | 2 | HTTP Plan-Gate **service** (compatibility / CI surface) |
| [`runtime/plan_gate_stub/tests/`](../../runtime/plan_gate_stub/tests/) | 1 | Stub CLI / schema pressure |
| [`observation/tests/`](../../observation/tests/) | 6 `test_*.py` | Root observation package |
| [`tests/`](../../tests/) | `test_dvc_artifacts_acceptance.sh` only | DVC acceptance (shell) |
| `jetbrains-plugin/**/src/test` | (Gradle) | Plugin unit tests — run `./gradlew test` from plugin dir when env allows |

Most coverage is **`runtime/tests/`**; repo-root [`tests/`](../../tests/) is **not** the main pytest tree.

---

## 2. Baseline run commands (tiers)

```bash
# Tier 1 — fast governed core (CI-friendly)
python3 -m pytest runtime/tests/test_stage3_loop.py runtime/tests/test_plangate_integration.py \
  runtime/tests/test_execute_service.py runtime/tests/test_m41_slice2_integration.py -q --tb=short

# Tier 2 — full runtime test package
python3 -m pytest runtime/tests/ -q --tb=short

# Tier 3 — optional extras
python3 -m pytest runtime/plan_gate_service/tests/ runtime/plan_gate_stub/tests/ -q --tb=short
python3 -m pytest observation/tests/ -q --tb=short
```

**Last full Tier 2 fingerprint (2026-04-13):** `1062 passed, 2 skipped` in ~40s (machine-dependent).

---

## 3. Module → tests → closure / artifacts (aggregated)

Rows are **runtime packages** (in-slice first). **Test files** lists primary `runtime/tests/` modules; add `+ pgs` / `+ stub` for nested package tests.

| runtime package / concern | in_product_slice | Key test files | closure_gate | validation_artifact (example) | runbook | test_signal | gap |
|---------------------------|------------------|----------------|--------------|-----------------------------|---------|-------------|-----|
| **`runtime/plangate/`** | yes | `test_plangate_*.py`, `test_plangate_integration.py`, `test_deterministic_guard.py`, `test_authority_validator.py`, `test_irreversibility_detector.py`, `test_canonical_intent.py`, `test_command_normalizer.py` | Gate-before-sandbox, M3.3 | Action 14 suite; plangate rows in ledger tests | demo runbooks | strong | — |
| **`runtime/orchestrator/`** | yes | `test_plangate_integration.py`, `test_transition_executor.py`, `test_task_wiring.py`, `test_m41_slice2_integration.py` | Loop + validated_to_sandbox | `docs/validation/artifacts/action14_final_acceptance/` | `docs/MOTADATA_DEMO_SETUP_RUNBOOK.md` | strong | Ledger persist edge (Batch A A-1) |
| **`runtime/loop/`** (Stage 3) | yes | `test_stage3_loop.py` | Stage 3 invariants | Action 14; stage3 tests | `docs/guides/STAGE3_BURN_IN_AND_E2E_DEMO.md` | strong | Synthetic Plan-Gate input vs argv (Batch A A-2) |
| **`runtime/state/`** | yes | `test_stage3_loop.py`, `test_task_contracts.py`, `test_task_bridge.py`, `test_transition_executor.py` | Task envelope / transitions | validation harnesses | — | partial | — |
| **`runtime/execute_service/`** | yes | `test_execute_service.py`, `test_execute_service_plan_gate_boundary.py`, `test_m41_slice2_integration.py` | Execute honesty, M4.1 | Action 14; plugin truth proof (cross) | plugin demo guide | strong | — |
| **`runtime/sandbox/`** | yes | `test_sandbox_ledger_store.py`, `test_sandbox_driver.py`, `test_sandbox_runner.py`, `test_container_sandbox_driver.py`, `test_sandbox_demo_e2e.py` | No silent host escape | ledger + sandbox tests | — | strong | Container skips if no runtime |
| **`runtime/ledger/`** (incl. sandbox store) | yes | `test_sandbox_ledger_store.py`, `test_ledger_*.py`, `test_m41_slice3_ledger_identity.py` | Ledger integrity | Action 14 | — | strong | — |
| **`runtime/ask_service/`** | yes | `test_ask_service.py`, `test_ask_v1_ingest.py`, `test_aiops_mvp_scenario_pack.py`, `test_authority_*.py`, `test_explain_debug*.py`, `test_m312_demo_scenarios.py` | Ask v1, authority, PLAN_ONLY | `docs/validation/artifacts/plugin_phase1_truth_proof/` (cross) | `docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md` | strong | B3 residual surfaces manual |
| **`runtime/context_layer_service/`** | yes | `test_context_layer_service.py`, `test_context_layer_logging_helpers.py`, `test_workspace_index_cache.py` | L5 export, health | B5; packaging validation | `docs/archive/guides/TEMP_MOTADATA_REPO_INTEGRATION_GUIDE.md` | strong | — |
| **`runtime/layer5/`** | yes | `test_authority_*.py`, `test_workspace_index_cache.py`, `test_ask_validation_harness.py`, `test_context_layer_service.py` (index) | B1/B2 retrieval, L5.8 | `docs/validation/artifacts/` L5 / assist eval | layer5 docs | strong | RET expansion = follow-on track |
| **`runtime/context/`** | yes | `test_context_engine.py`, `test_m312_*.py` | Context fetch, M3.12 manifest | M3.12 demo tests | — | partial | — |
| **`runtime/assist_layer/`** | partial | `test_assist_layer_v1.py`, `test_assist_layer_v2_evaluation.py` | Advisory-only; Actions 15–17 | `docs/validation/artifacts/assist_layer_v2_eval/` | — | strong | Policy is eval, not “improve retrieval” |
| **`runtime/observation/`** (runtime pkg) | yes | `test_trace_builder.py`, `test_explanation_builder.py`, `test_action5_observability.py`, `test_report_runtime_summary.py`, `test_runtime_metrics.py`, `test_reconciliation.py`, `test_drift_baseline.py`, `test_greg_escalation.py`, `test_collapse_vectors.py`, `test_runtime_summary_queries.py` | B4 trace reconstruction | B4 artifacts; closure tracker §1.1 | `docs/OBSERVATION/` | strong | Ops follow-through L5-OBS-1 |
| **`runtime/plan_gate_service/`** | no (compat) | `runtime/plan_gate_service/tests/` + `test_ask_service.py` (subprocess) | CI / HTTP v0.1 | stub golden refs | — | partial | Not M3.3 execution gate |
| **`runtime/plan_gate_stub/`** | no | `runtime/plan_gate_stub/tests/` | Protocol / schema | stub golden dirs | — | partial | — |
| **`runtime/emulator/`** | partial | `test_emulator_invariants.py` | Shadow/emulator | — | — | weak | Experimental |
| **`runtime/replay/`** | partial | `test_execution_replay_service.py` | Replay | — | — | partial | — |
| `runtime/intake/` | — | **removed** 2026-04-14 (orphan `__pycache__` only; no sources) | — | — | — | — | — |
| **`runtime/rag/`** | partial | Collateral via L5 / context tests | B1 closed | B1 refs in tracker | — | partial | Not full hot-path isolation in one file |

---

## 4. Closure-gate crosswalk (tracker §1.3)

Source: [`docs/LIVE_ROADMAP_TRACKER.md`](../LIVE_ROADMAP_TRACKER.md) §1.3.

| Gate (production) | Primary automated tests | validation_artifact | gap / manual |
|-------------------|-------------------------|---------------------|--------------|
| Plugin v1 evidence-first path (intent) | `test_ask_v1_ingest.py`, `test_context_layer_service.py`, plugin Gradle | `PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md`, `plugin_phase1_truth_proof/` | Plugin UI: Gradle env |
| Evidence visibility + insufficiency honesty | `test_aiops_mvp_scenario_pack.py`, `test_explain_debug_action6_proof.py`, quality gate tests | Action 14; plugin proof pack | Residual B3 checklist |
| `ask_path` truthfulness | Ask v1 + ingest tests; plugin proof | same | IDE parity residual |
| `plan_summary.notes` / operator context | Authority / planner tests; `test_authority_phase4_plan_gate.py` | closure scope per tracker | B3 residual |
| `POST /v0/execute` outcome honesty | `test_execute_service.py`, `test_execute_service_plan_gate_boundary.py` | Action 14 | — |
| Request tracing (Context Layer ↔ Plan-Gate ↔ execution) | `test_trace_builder.py`, `test_action5_observability.py`, `test_reconciliation.py` | B4; `docs/validation/` traces | Log packaging ops |
| Action 14 final acceptance | `test_stage3_loop.py`, execute/plangate integration suite | `docs/validation/artifacts/action14_final_acceptance/ACTION14_FINAL_ACCEPTANCE_REPORT.md` | Re-run script in report |

---

## 5. Alphabetical test file index (`runtime/tests/`)

Use for quick lookup; **closure** see §3–4.

| Test file | Primary modules touched |
|-----------|-------------------------|
| `test_action5_observability.py` | observation |
| `test_aiops_mvp_scenario_pack.py` | ask_service, v1_ingest |
| `test_ask_service.py` | ask_service handlers |
| `test_ask_validation_harness.py` | ask_validation |
| `test_ask_v1_ingest.py` | ask_service v1 |
| `test_assist_layer_v1.py` | assist_layer, plan_gate_service (payload helper) |
| `test_assist_layer_v2_evaluation.py` | assist_layer evaluation |
| `test_authority_code_index_phase2.py` | layer5 authority |
| `test_authority_code_reasoning_phase5.py` | layer5 authority, ask_service |
| `test_authority_foundation.py` | layer5 authority |
| `test_authority_phase4_plan_gate.py` | layer5 authority, ask_service planner |
| `test_authority_ranking_phase3.py` | layer5 authority |
| `test_canonical_intent.py` | integrity |
| `test_command_normalizer.py` | integrity |
| `test_container_sandbox_driver.py` | sandbox |
| `test_context_engine.py` | context |
| `test_context_layer_logging_helpers.py` | context_layer_service |
| `test_context_layer_service.py` | context_layer_service, layer5 |
| `test_collapse_vectors.py` | observation |
| `test_deterministic_guard.py` | plangate pre_gate |
| `test_drift_baseline.py` | observation |
| `test_emulator_invariants.py` | plan_gate_stub |
| `test_execute_service_plan_gate_boundary.py` | execute_service |
| `test_execute_service.py` | execute_service |
| `test_explain_debug_action6_proof.py` | ask_service, layer5 |
| `test_explanation_builder.py` | observation |
| `test_execution_replay_service.py` | replay |
| `test_greg_escalation.py` | observation |
| `test_irreversibility_detector.py` | plangate |
| `test_ledger_canonical_hash_lookup.py` | ledger usage |
| `test_ledger_completeness.py` | ledger |
| `test_m312_demo_scenarios.py` | ask_service, M3.12 |
| `test_m312_doc_selector.py` | context doc_selector |
| `test_m312_manifest.py` | context manifest |
| `test_m41_slice2_integration.py` | orchestrator, execute, plangate, sandbox |
| `test_m41_slice3_ledger_identity.py` | ledger identity |
| `test_plangate_authority_validator.py` | plangate |
| `test_plangate_integration.py` | orchestrator, plangate |
| `test_plangate_irreversibility_detector.py` | plangate |
| `test_plangate_judge_gate.py` | plangate |
| `test_reasoner_explain_debug_logging.py` | ask_service reasoner |
| `test_reconciliation.py` | observation |
| `test_report_runtime_summary.py` | observation |
| `test_runtime_metrics.py` | observation |
| `test_runtime_summary_queries.py` | observation |
| `test_sandbox_demo_e2e.py` | sandbox demo |
| `test_sandbox_driver.py` | sandbox |
| `test_sandbox_ledger_store.py` | sandbox ledger store |
| `test_sandbox_runner.py` | sandbox |
| `test_schemas_v0_1.py` | schemas |
| `test_stage3_loop.py` | loop, adapters, tools, obs ledger |
| `test_task_bridge.py` | task |
| `test_task_contracts.py` | task |
| `test_task_wiring.py` | orchestrator, state |
| `test_trace_builder.py` | observation |
| `test_transition_executor.py` | orchestrator |
| `test_workspace_index_cache.py` | context_layer_service, layer5 |

---

## 6. Known gaps (honest)

1. **Repo-root `tests/`** — almost no Python; main suite is **`runtime/tests/`** (documented in §1).
2. **JetBrains** — coverage is Gradle-side; matrix cannot assert green without Android Studio / JVM setup.
3. **Batch A** — orchestrator ledger persist on append failure: **no dedicated test** yet (finding A-1).
4. **End-to-end IDE → WSL** — partially **manual** per tracker (operator demo vs Stage 3 burn-in doc).

---

## 7. Next steps (Phase 3–4)

1. **`WORKFLOW_SCENARIO_MATRIX.md`** — map §4 gates to **steps** + **manual vs automated**.
2. **`SYNTHESIS_REPORT.md`** — five buckets from [multi-phase plan](~/.cursor/plans/multi-phase_layout_and_test_review_7bd5a487.plan.md).

---

## References

- [`docs/LIVE_ROADMAP_TRACKER.md`](../LIVE_ROADMAP_TRACKER.md)
- [`docs/audit/REPO_LAYOUT_INVENTORY.md`](REPO_LAYOUT_INVENTORY.md)
- [`docs/audit/BATCH_A_GOVERNED_RUNTIME_CORE.md`](BATCH_A_GOVERNED_RUNTIME_CORE.md)

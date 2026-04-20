# Layer-3 Runtime Integration Report

> **Current Layer-3 truth:** For **`main`** milestone status, HTTP contracts, and closure evidence, use [`LAYER3_RUNTIME_SPEC.md`](LAYER3_RUNTIME_SPEC.md) and [`LIVE_ROADMAP_TRACKER.md`](LIVE_ROADMAP_TRACKER.md) §4.3.1. This report is a **historical integration-branch** record only.

**Integration branch:** `integration/layer3-runtime-stack`  
**Report date:** 2026-03-13  
**Scope:** Consolidation of Layer-3 runtime lineage for architect review. No merge to main was performed.

---

## 1. Integration branch identity

| Item | Value |
|------|--------|
| **Branch name** | `integration/layer3-runtime-stack` |
| **Base main commit** | `aa3a094` (Feb10-Commit) |
| **Merged branches** | 1. `layer3-runtime-docs-emulator` 2. `layer3-plugin-runtime-bridge` |
| **Resulting HEAD** | `7afbb54` (Merge layer3-plugin-runtime-bridge into integration/layer3-runtime-stack) |

Merge commit history on the integration branch:

- `489a2c0` — Merge layer3-runtime-docs-emulator (Layer-3 base)
- `7afbb54` — Merge layer3-plugin-runtime-bridge (M3.4 + fail-closed)

---

## 2. Merge summary

### First merge: layer3-runtime-docs-emulator

- **Result:** Succeeded cleanly (no conflicts).
- **Strategy:** Normal merge commit (`--no-ff`).
- **Conflict files:** None.

### Second merge: layer3-plugin-runtime-bridge

- **Result:** Succeeded cleanly (no conflicts).
- **Strategy:** `ort` merge strategy; normal merge commit.
- **Conflict files:** None.
- **Files brought in (representative):**  
  `runtime/execute_service/handlers.py`, `runtime/ide/schemas/execute_request.v0.1.schema.json`, `runtime/ide/schemas/execute_response.v0.1.schema.json`, `runtime/plangate/` (authority_validator, command_utils, contracts, irreversibility_detector, judge_gate), `runtime/tests/test_execute_service.py`, `runtime/tests/test_plangate_*.py`, `jetbrains-plugin/.../bridge/*`, `jetbrains-plugin/.../actions/SubmitToRuntimeAction.kt`, `docs/runtime/JETBRAINS_PLUGIN_RUNTIME_BRIDGE.md`, `docs/runtime/milestones/M3.4_IDE_PLUGIN_INTEGRATION.md`, `docs/LIVE_ROADMAP_TRACKER.md`, and related updates.

**Conflict resolution:** N/A — both merges were conflict-free.

---

## 3. Validation summary

### Commands run

| Command | Result | Notes |
|--------|--------|-------|
| `python3 -m pytest runtime/tests/ -v --tb=short` | **291 passed** in ~1.94s | Full runtime test suite |
| `python3 -m runtime.sandbox.demo_governed_execution` | **Passed** | All 5 cases (SAFE_EXECUTE, REFUSE, REFUSED no-gate, DEFER, BOUNDED_ALLOW); 7 ledger rows |
| `python3 -m runtime.shadow_runner.run_demo` | **Passed** | 3 scenarios; invariant checks PASS |
| `./gradlew test` (jetbrains-plugin) | **Not runnable** | JAVA_HOME not set; no `java` in PATH in this environment |

### Tests covered by `runtime/tests/`

- Execute service (request validation, parse command, handle execute, decision ledgering, integration)
- Plan-Gate (integration, authority validator, irreversibility detector, judge gate)
- Sandbox (demo e2e, ledger store, runner, policy, executor)
- Transition executor (validator, loop controller, sandbox integration, persistence)
- Ask service, context engine, emulator invariants, schemas v0.1, and related

### Commands not runnable and why

- **JetBrains plugin Kotlin tests:** Java toolchain not available in the environment used for this integration run (`JAVA_HOME` not set, no `java` in PATH). Plugin tests were not executed. Recommendation: run `./gradlew test` in a Java 17+ environment before merging to main.

---

## 4. Architectural invariant check

Spot-check of hotspot files and behavior on `integration/layer3-runtime-stack`:

| Invariant | Status | Evidence |
|-----------|--------|----------|
| **Plan-Gate mandatory before sandbox** | Preserved | `loop_controller.py`: `validated_to_sandbox` requires `plan_gate_service`; evaluates decision; only `safe_execute` proceeds to `_run_sandbox_and_persist`. |
| **Posture separation** | Preserved | `refuse` / `defer` / `bounded_allow` each return `TransitionResult(valid=False, ...)` with distinct `stop_reason`; only `safe_execute` runs sandbox. |
| **Fail-closed behavior** | Preserved | `execute_service/handlers.py`: When `ledger_path` is set and store creation or `_persist_plangate_decision` fails, handler returns `outcome="BLOCKED"`, `executed=False`, reason "Plan-Gate decision could not be persisted; execution blocked." |
| **Decision ledger vs execution ledger separation** | Preserved | Handler persists Plan-Gate decision and returns `decision_ledger_row_id`; sandbox execution (when allowed) persists and returns `ledger_row_id`. Both in response schema. |
| **Plugin-as-client doctrine** | Preserved | Plugin calls `/v0/ask` (plan-only) and `/v0/execute`; runtime owns Plan-Gate and sandbox decisions. `RuntimeBridge.kt`: `requestPlanOnly` → Ask endpoint; `requestExecution` → execute endpoint. |
| **Plan-only Ask flow** | Preserved | `AskMotadataAiAction`: "Ask Motadata AI — Plan-only"; `RuntimeBridge.callAskEndpoint` for plan-only; no execution in Ask path. |
| **No outcome collapsing in plugin bridge** | Preserved | `RuntimeOutcome.kt`: distinct enum values REFUSED, DEFERRED, BOUNDED_ALLOW, BLOCKED, EXECUTED, RUNTIME_UNAVAILABLE, UNKNOWN; comment states plugin MUST NOT collapse to generic SUCCESS/FAILURE. |

---

## 5. Remaining risks

- **Plugin tests not compiled/run:** Kotlin/JVM tests for the JetBrains plugin were not run in this environment. Regression in bridge or outcome mapping could exist; should be validated in a Java 17+ environment before merge to main.
- **E2E IDE ↔ runtime:** No end-to-end test was run with a live IDE instance and a running runtime server; only unit/integration tests and CLI demos.
- **Docs:** `LIVE_ROADMAP_TRACKER.md` and milestone docs reflect M3.4 COMPLETE and next M3.5/M3.6; no further doc cleanup was performed as part of this integration.
- **ML branch not integrated:** `Layer-2-ML-Compilation-Stage-8-Controlled-SFT` and other branches were not part of this integration; only Layer-3 runtime lineage was consolidated.

---

## 6. Merge recommendation

**READY FOR ARCHITECT REVIEW**

- Both merges completed without conflicts.
- Full runtime test suite (291 tests) passed.
- Sandbox governed execution demo and shadow runner demo passed.
- Spot-check of hotspot files and documented invariants (Plan-Gate mandatory, posture separation, fail-closed, decision vs execution ledger, plugin-as-client, plan-only Ask, no outcome collapsing) is consistent with the intended architecture.

**Before merge to main:**

1. Run JetBrains plugin tests in a Java 17+ environment (`./gradlew test` in `jetbrains-plugin/`).
2. Optional: run a manual E2E check (IDE + runtime) if available.
3. Architect sign-off on branch `integration/layer3-runtime-stack` and this report.

**Do not merge `integration/layer3-runtime-stack` into main until the above are satisfied and an explicit decision to merge has been made.**

---

*End of report. Integration branch created and validated; no merge to main was performed.*

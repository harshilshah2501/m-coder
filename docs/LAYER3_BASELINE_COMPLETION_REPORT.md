# Layer-3 Baseline Completion Report

**Date:** 2026-03-13  
**Status:** Layer-3 baseline integration complete on `main`.

---

## 1. What was finalized

The following Layer-3 runtime milestones are now represented on `main` and tagged as the stable baseline:

- **M3.2 Execution Sandbox** — Governed execution contract, sandbox executor, ledger store, demo (REFUSED / BLOCKED / EXECUTED).
- **M3.3 Plan-Gate Integration** — Plan-Gate mandatory before sandbox; postures refuse, defer, bounded_allow, safe_execute; ledger events for all postures.
- **M3.3B Internal Plan-Gate Decomposition** — command_utils, authority_validator, irreversibility_detector, judge_gate; unit tests for subcomponents.
- **M3.4 IDE Plugin Integration** — RuntimeBridge, /v0/execute, execute/ask request-response schemas, Submit-to-Runtime action, decision ledgering, fail-closed when ledger persistence required and fails.

---

## 2. Validation evidence

| Validation | Result |
|------------|--------|
| **Runtime test suite** | 291 tests passed (`python3 -m pytest runtime/tests/ -v`). |
| **Sandbox demo** | Passed — all 5 cases (SAFE_EXECUTE, REFUSE, REFUSED no-gate, DEFER, BOUNDED_ALLOW); 7 ledger rows. |
| **Shadow runner demo** | Passed — 3 scenarios; invariant checks PASS. |
| **Plugin `./gradlew test`** | BUILD SUCCESSFUL (Gradle 8.13, Temurin 23; 13 actionable tasks). |
| **Plugin `./gradlew build -x test`** | BUILD SUCCESSFUL. |

---

## 3. Merge details

| Item | Value |
|------|--------|
| **Source branch** | `integration/layer3-runtime-stack` |
| **Target branch** | `main` |
| **Resulting main commit SHA** | `0283a2e` (Merge integration/layer3-runtime-stack into main — Layer-3 baseline (M3.2–M3.4)) |
| **Tag created** | `layer3-runtime-baseline` (annotated, pointing at the merge commit) |

---

## 4. Remaining non-blocking warnings

- **Kotlin stdlib (IntelliJ plugin):** The Gradle IntelliJ plugin reports that the Kotlin Standard Library dependency may conflict with the version provided by the IntelliJ Platform. Known configuration note; non-blocking.
- **Deprecated Gradle features:** Build uses some deprecated Gradle features (Gradle 9.0 incompatible). Use `--warning-mode all` to inspect; non-blocking for this release.

---

## 5. Next recommended milestone

**M3.5 Ledger completeness / replay** — Next active engineering focus for Layer-3 (ledger completeness, replay, and related governance evidence).

---

## 6. Final statement

Layer-3 baseline integration is complete. `main` now reflects the current governed runtime architecture:

- Plan-Gate is mandatory before any sandbox execution.
- Postures (refuse, defer, bounded_allow, safe_execute) are distinct and ledgered.
- IDE plugin is a client only; RuntimeBridge is the single integration point; Ask is plan-only; Submit-to-Runtime uses /v0/execute with fail-closed semantics when decision persistence is required and fails.
- M3.2, M3.3, M3.3B, and M3.4 deliverables are validated and merged.

The tag `layer3-runtime-baseline` marks this state for future reference.

---

*End of report.*

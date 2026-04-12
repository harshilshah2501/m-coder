# Plugin Phase-1 truth proof — closure authority

**Status:** **LOCKED** for Stage 2 MVP closure chronology (item 1). Do not reopen as a design thread; regenerate artifacts only when intentionally refreshing proof after backend/plugin contract changes, then re-lock this section and the frozen matrix.

## What is proven

- **Scenarios S1–S8** cover Ask (v1 / v0 / controlled fallback), weak and NO_MATCH evidence honesty, and execute outcomes **BLOCKED**, **REFUSED**, **EXECUTED_FAILED** with plugin-visible copy derived from the same routing and message builders as production.
- **Frozen contract:** `docs/validation/artifacts/plugin_phase1_truth_proof/proof_matrix.json` — every row has **`exact_match`: true**; human table in `proof_matrix.md`.
- **Per-scenario captures:** `docs/validation/artifacts/plugin_phase1_truth_proof/scenario_S*/` (request/response JSON where applicable, `plugin_full_dialog.txt`, summaries where recorded), plus `host_contract_check.json`.

## Automation

| Surface | Role |
|--------|------|
| `scripts/verify_plugin_phase1_proof_matrix.sh` | **Preferred offline verifier** — `python3` only; no IntelliJ Gradle test sandbox. |
| `jetbrains-plugin/src/test/kotlin/ai/motadata/plugin/ask/Phase1TruthProofHarnessTest.kt` | **`phase1ProofMatrixFrozenContract`** — same assertions as the script; runs in default `./gradlew :jetbrains-plugin:test` when the IntelliJ Gradle plugin test task works in your environment (excludes `live` tag). |
| Same class, **`generatePhase1ProofPack`** | Tagged **`live`** — regenerates matrix and scenario dirs against **running** Context Layer + Plan-Gate; excluded from default Gradle test. Run explicitly when refreshing proof: `./gradlew :jetbrains-plugin:test --tests 'ai.motadata.plugin.ask.Phase1TruthProofHarnessTest.generatePhase1ProofPack'`. |

## Tracker cross-reference

Canonical program status: `docs/LIVE_ROADMAP_TRACKER.md` **§6.22** (evidence log) and **§7.1** pillar row.

## Scope boundary

This closure is **Phase-1 plugin truth alignment** (backend JSON → operator-visible plugin text and routing metadata). It does **not** replace **§B3** residual product gates (for example `plan_summary.notes` on every surface) or **L5-RET-VALIDATION** generalization work.

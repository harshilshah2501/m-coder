# Main Merge Readiness Report — Layer-3 Integration

**Report date:** 2026-03-13  
**Purpose:** Determine whether `integration/layer3-runtime-stack` is ready to merge into `main` after plugin validation.  
**Outcome:** Plugin Kotlin/Gradle tests and build validation have been run successfully. All validation evidence is complete.

---

## 1. Branch under review

| Item | Value |
|------|--------|
| **Branch name** | `integration/layer3-runtime-stack` |
| **HEAD commit** | `7fd691f` — docs: add Layer-3 integration report (validation + invariant check) |
| **Relationship** | This branch is the consolidated Layer-3 runtime stack. It was created from `main` (aa3a094), then had `layer3-runtime-docs-emulator` and `layer3-plugin-runtime-bridge` merged in. Runtime tests, demos, and plugin validation have all passed. |

---

## 2. Validation environment

| Check | Result |
|-------|--------|
| **java -version** | OpenJDK 23.0.2 (Eclipse Temurin 23.0.2+7) |
| **javac -version** | javac 23.0.2 |
| **JAVA_HOME** | Set to `$HOME/.jdks/temurin-23.0.2` |
| **Gradle wrapper** | Present. `jetbrains-plugin/gradlew` — Gradle 8.13 (Kotlin 2.0.21, Groovy 3.0.22). |

---

## 3. Commands executed

| Command | Purpose | Result |
|---------|---------|--------|
| `cd jetbrains-plugin && ./gradlew test` | Run plugin unit tests | **BUILD SUCCESSFUL** (8s; 13 actionable tasks: 7 executed, 6 up-to-date) |
| `cd jetbrains-plugin && ./gradlew build -x test` | Plugin build without tests | **BUILD SUCCESSFUL** (6s; 13 actionable tasks: 5 executed, 8 up-to-date) |

---

## 4. Results

| Area | Result | Notes |
|------|--------|-------|
| **Plugin tests** | **Passed** | `./gradlew test` completed successfully. |
| **Plugin build** | **Passed** | `./gradlew build -x test` completed successfully. |
| **Runtime tests** | **Passed** | 291 tests (from prior integration report). |
| **Sandbox demo** | **Passed** | All 5 cases; 7 ledger rows. |
| **Shadow runner demo** | **Passed** | 3 scenarios; invariants validated. |

**Non-blocking warnings (noted truthfully):**

- **Kotlin stdlib:** The Gradle IntelliJ plugin reports that the dependency on the Kotlin Standard Library (stdlib) is automatically added when using the Gradle Kotlin plugin and may conflict with the version provided with the IntelliJ Platform. This is a known configuration note; non-blocking for merge.
- **Deprecated Gradle features:** Build used deprecated Gradle features, making it incompatible with Gradle 9.0. Use `--warning-mode all` to see individual deprecations. Non-blocking for merge.

---

## 5. Remaining architectural invariants

Spot-check of the integrated plugin/runtime surfaces on `integration/layer3-runtime-stack` (code inspection):

| Invariant | Status | Evidence |
|-----------|--------|----------|
| **Plugin is a client, not a governor** | Preserved | `RuntimeBridge.kt` doc: "The plugin is a client, NOT a governor"; no governance logic in plugin. |
| **RuntimeBridge is the single integration point** | Preserved | All runtime calls go through `RuntimeBridge`: `evaluateCommit`, `askPlan`, `requestExecution`, `validateAction`. |
| **Commit interception routes through runtime** | Preserved | `MotadataCheckinHandler` uses `bridge.evaluateCommit(request)` → `callPlanEndpoint` → `/v0/plan`. |
| **Ask remains PLAN ONLY / no execution** | Preserved | `AskMotadataAiAction`: "PLAN ONLY, no execution"; `bridge.askPlan` → `/v0/ask`. |
| **Submit-to-Runtime uses /v0/execute** | Preserved | `SubmitToRuntimeAction` → `bridge.requestExecution` → `callExecuteEndpoint` → `/v0/execute`. |
| **Outcomes remain distinct** | Preserved | `RuntimeOutcome` enum: REFUSED, DEFERRED, BOUNDED_ALLOW, BLOCKED, EXECUTED, RUNTIME_UNAVAILABLE, UNKNOWN. |
| **No plugin-side local fallback** | Preserved | Bridge returns `RuntimeResponse.runtimeUnavailable` when runtime unreachable; no silent local execution. |
| **Fail-closed semantics** | Preserved | `client_policy.failClosedIfUnreachable` passed in requests. |

---

## 6. Blocking issues

**None.** All validations have passed. Non-blocking warnings are documented in §4.

---

## 7. Final recommendation

**READY TO MERGE INTO MAIN**

- Runtime test suite, sandbox demo, and shadow runner demo passed (prior integration report).
- Plugin `./gradlew test` and `./gradlew build -x test` passed in a Java 17+ environment (Temurin 23, Gradle 8.13).
- M3.4 architectural invariants preserved by code inspection and test execution.
- No blocking issues. Non-blocking warnings (Kotlin stdlib note, Gradle deprecations) do not block merge.

---

*End of report.*

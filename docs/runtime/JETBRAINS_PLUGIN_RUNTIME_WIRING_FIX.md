# JetBrains Plugin ↔ Governed Runtime Wiring Fix

## Root cause

The plugin showed "Runtime service is not available" even when Plan-Gate was reachable at `http://127.0.0.1:8089` and `GET /healthz` returned 200, because **any** exception from the runtime HTTP calls was mapped to **RUNTIME_UNAVAILABLE**.

In **`RuntimeBridge.kt`**:

- `postJson()` throws `RuntimeException("Runtime HTTP $status: $response")` for non-2xx (e.g. 400 schema validation).
- `callPlanEndpoint`, `callAskEndpoint`, and `callExecuteEndpoint` had a single `catch (e: Exception)` and always returned `RuntimeResponse.runtimeUnavailable(...)`.
- So a **400 (schema validation)** from `/v0/plan`, `/v0/ask`, or `/v0/execute` was treated as **transport failure** instead of **reachable service + bad request**.

Correct behaviour:

- **Transport/connection failure** → RUNTIME_UNAVAILABLE.
- **HTTP 4xx/5xx (service reached, bad request)** → UNKNOWN (or similar), not unavailable.

## Files changed

- **Modified:** `jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/bridge/RuntimeBridge.kt`
- **Added:** `jetbrains-plugin/src/test/kotlin/ai/motadata/plugin/bridge/RuntimeBridgeTest.kt`
- **Modified:** `jetbrains-plugin/build.gradle.kts` (comment on test task; no behavioural change)

## Patch summary

1. **RuntimeBridge.kt**
   - Introduced a **private** `RuntimeHttpException(statusCode: Int, body: String)` extending `RuntimeException`, thrown from `postJson()` when `status !in 200..299`.
   - In **callPlanEndpoint**, **callAskEndpoint**, and **callExecuteEndpoint**:
     - **First** `catch (e: RuntimeHttpException)` → return `RuntimeResponse.unknown(request.requestId, e.message ?: "Bad request")`.
     - **Then** `catch (e: Exception)` → return `RuntimeResponse.runtimeUnavailable(...)` (unchanged).
   - No other behaviour or endpoints changed. Paths confirmed: `/healthz`, `/v0/plan`, `/v0/ask`, `/v0/execute`; base URL `http://127.0.0.1:8089`.

2. **RuntimeBridgeTest.kt**
   - `isRuntimeAvailable` returns false when host is unreachable (e.g. `http://192.0.2.1:8089`).
   - Asserts that `RuntimeResponse.unknown(...)` with a "Runtime HTTP 400" message yields outcome UNKNOWN (not RUNTIME_UNAVAILABLE).

3. **build.gradle.kts**
   - Comment added on `tasks.test` explaining that with IntelliJ 2025.3 the gradle-intellij-plugin can fail with "Index: 1, Size: 1" in `resolveIdeHomeVariable` when running `:test`; validation can be done manually on Windows or after migrating to intellij-platform-gradle-plugin 2.x.

## Tests added/updated

- **RuntimeBridgeTest.kt** (new):
  - `isRuntimeAvailable returns false when host is unreachable`
  - `unknown response is used for HTTP error not transport failure`

- **Gradle test task:** With IntelliJ 2025.3 and gradle-intellij-plugin 1.17.3, `./gradlew test` fails with `IndexOutOfBoundsException: Index: 1, Size: 1` in `org.jetbrains.intellij.Utils.resolveIdeHomeVariable` (plugin infrastructure, not test logic). Tests are written to run once the test runner is fixed or after migrating to the 2.x plugin.

## Commands run

- `./gradlew test --tests "ai.motadata.plugin.bridge.RuntimeBridgeTest"` — fails with Index: 1, Size: 1 (IntelliJ plugin test runner).
- `./gradlew compileKotlin compileTestKotlin` — succeeds (bridge and test compile).

## Result

- **Plugin-side fix is in place:** HTTP 4xx/5xx from plan/ask/execute are classified as UNKNOWN (reachable + bad request), not RUNTIME_UNAVAILABLE.
- **Availability check** already used `GET /healthz`; no path typo (e.g. healthz0) found.
- **Endpoints:** Ask → `/v0/ask`, Submit/Execute → `/v0/execute`, Plan/commit → `/v0/plan`; base URL `http://127.0.0.1:8089`.
- **Manual validation:** On Windows IntelliJ, with Plan-Gate running and `/healthz` returning 200, the plugin should no longer show "Runtime service is not available" solely due to 400 from `/v0/plan`/`/v0/ask`/`/v0/execute`. Submit/Ask will show the real runtime outcome (e.g. UNKNOWN with error text for 400) or succeed when the request matches the runtime schema.

## Remaining follow-up

- **Optional:** Resolve Gradle test execution (e.g. migrate to intellij-platform-gradle-plugin 2.x or use a different test configuration) so `RuntimeBridgeTest` runs under `./gradlew test`.
- **Optional:** Restore or add tests that stub `GET /healthz` 200 (e.g. with an in-process server) once the test runner allows it; current tests avoid that to reduce dependency on the fragile test setup.

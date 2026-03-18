# Phase-2 Result: JetBrains Plugin Golden Demo Path

**Branch:** `feature/jetbrains-plugin-golden-demo-path`

---

## 1. Real backend path chosen

- **Chosen:** Upgrade Ask path with an optional real-reasoning path for `task_type=EXPLAIN_DEBUG`.
- **Rejected for demo:** [PlanOnlyPlanner](runtime/ask_service/planner.py) — template-only; not used when task is EXPLAIN_DEBUG with selection.
- **Implemented:** [runtime/ask_service/reasoner.py](runtime/ask_service/reasoner.py) — `ExplainDebugReasoner`:
  - Invoked only when `task_type == "EXPLAIN_DEBUG"` and `selected_file` + (selection or bundle items) are present.
  - Builds a prompt from ContextBundle + selected code + query; calls vLLM-compatible HTTP endpoint (env `MOTADATA_EXPLAIN_VLLM_URL`, default `http://127.0.0.1:8000`).
  - Returns structured `ExplainDebugResult` (summary, logic_flow, likely_bug_risk, evidence, confidence_limits) or `error` when service is unavailable.
  - When reasoner returns error, handler does **not** substitute template steps; response includes `explain_debug.error` and a single step string explaining unavailability.

---

## 2. Files inspected

- **Plugin:** [AskMotadataAiAction.kt](jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/ask/AskMotadataAiAction.kt), [RuntimeBridge.kt](jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/bridge/RuntimeBridge.kt), [RuntimeRequest.kt](jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/bridge/RuntimeRequest.kt), [SubmitToRuntimeAction.kt](jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/actions/SubmitToRuntimeAction.kt).
- **Backend:** [runtime/plan_gate_service/app.py](runtime/plan_gate_service/app.py), [runtime/ask_service/handlers.py](runtime/ask_service/handlers.py), [runtime/ask_service/planner.py](runtime/ask_service/planner.py), [runtime/context/engine.py](runtime/context/engine.py), [runtime/context/contracts.py](runtime/context/contracts.py), [runtime/ide/schemas/ask_request.v0.1.schema.json](runtime/ide/schemas/ask_request.v0.1.schema.json), [runtime/ide/schemas/plan_only_response.v0.1.schema.json](runtime/ide/schemas/plan_only_response.v0.1.schema.json).
- **Tests:** [runtime/tests/test_ask_service.py](runtime/tests/test_ask_service.py), [jetbrains-plugin/src/test/.../RuntimeRequestTest.kt](jetbrains-plugin/src/test/kotlin/ai/motadata/plugin/bridge/RuntimeRequestTest.kt).

---

## 3. Implementation plan (executed)

| Step | Done | What was done |
|------|------|----------------|
| 1 — Selection-aware request | Yes | Editor selection and current file path captured via `CommonDataKeys.EDITOR` / `VIRTUAL_FILE`; repo-relative path computed; `RuntimeRequest` extended with `selectedFile`, `selection`, `taskType`; `RuntimeBridge.buildAskRequest` sends `selected_file`, `client_context.selection`, `task_type`. |
| 2 — Task mode | Yes | `task_type` sent as `EXPLAIN_DEBUG` when user has selection and file; otherwise omitted (general path). |
| 3 — Backend reasoning path | Yes | `reasoner.explain_debug()` added; handlers call it when `task_type == "EXPLAIN_DEBUG"` and selection/file context present; no PlanOnlyPlanner for that branch. |
| 4 — Minimal repo context | Yes | `selected_file` and `client_context.selection` passed; existing ContextEngine used with `files=[selected_file]` + symbol_hints. |
| 5 — Structured response rendering | Yes | Response schema extended with optional `explain_debug`; plugin parses and renders Summary, Logic flow, Likely bug/risk, Evidence, Confidence/limitations; when `explain_debug.error` present, shows error and no template steps. |

---

## 4. Files changed

- **Plugin**
  - [jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/ask/AskMotadataAiAction.kt](jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/ask/AskMotadataAiAction.kt) — selection/file capture, task type, structured explain_debug rendering.
  - [jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/bridge/RuntimeRequest.kt](jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/bridge/RuntimeRequest.kt) — added `selectedFile`, `selection`, `taskType`.
  - [jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/bridge/RuntimeBridge.kt](jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/bridge/RuntimeBridge.kt) — `buildAskRequest` includes `selected_file`, `client_context`, `task_type`; `parseAskResponse` parses `explain_debug` into metadata.
- **Backend**
  - [runtime/ask_service/reasoner.py](runtime/ask_service/reasoner.py) — **new**: ExplainDebugReasoner (sync HTTP to vLLM, structured parse).
  - [runtime/ask_service/handlers.py](runtime/ask_service/handlers.py) — task_type/client_context/selection; branch to reasoner; `_build_plan_only_response(..., explain_debug=)`.
  - [runtime/ide/schemas/ask_request.v0.1.schema.json](runtime/ide/schemas/ask_request.v0.1.schema.json) — optional `task_type` (EXPLAIN_DEBUG | general), `client_context` description.
  - [runtime/ide/schemas/plan_only_response.v0.1.schema.json](runtime/ide/schemas/plan_only_response.v0.1.schema.json) — optional `explain_debug` object (summary, logic_flow, likely_bug_risk, evidence, confidence_limits, error).
- **Tests**
  - [runtime/tests/test_ask_service.py](runtime/tests/test_ask_service.py) — added `test_handle_ask_request_explain_debug_uses_reasoner_and_returns_structured`.
- **Docs**
  - [docs/demo/PHASE2_JETBRAINS_GOLDEN_DEMO_PLAN.md](docs/demo/PHASE2_JETBRAINS_GOLDEN_DEMO_PLAN.md) — plan.
  - [docs/demo/PHASE2_JETBRAINS_GOLDEN_DEMO_RESULT.md](docs/demo/PHASE2_JETBRAINS_GOLDEN_DEMO_RESULT.md) — this file.

---

## 5. What is now real and demo-usable

- **Selection + file:** User can select code in the editor and trigger "Ask Motadata AI"; plugin sends that selection and repo-relative file path.
- **Task mode:** Explicit `EXPLAIN_DEBUG` when selection is present; backend uses real reasoner instead of template planner.
- **Real reasoning:** When vLLM (or configured endpoint) is available at `MOTADATA_EXPLAIN_VLLM_URL`, the backend performs real code reasoning and returns structured Summary, Logic flow, Likely bug/risk, Evidence, Confidence/limitations.
- **Structured output:** Plugin shows these sections in a dialog when `explain_debug` is present; when the reasoner is unavailable, it shows a clear error and does not substitute template steps.
- **No fake intelligence:** Template planner is not used for EXPLAIN_DEBUG; if reasoning fails, the response is explicitly "Reasoning service unavailable" (or similar).

---

## 6. What is intentionally out of scope

- **Bounded fix:** Deferred. No suggest-fix or patch flow; no write path.
- **Tool window:** Output remains dialog-based.
- **Pre-filled query when selection exists:** Avoided to prevent overload resolution issues with `Messages.showInputDialog`; prompt text still explains Explain/Debug when there is selection.

---

## 7. Validation summary

- **Backend:** `python3 -m pytest runtime/tests/test_ask_service.py -v` — 2 tests passed (existing plan-only + new EXPLAIN_DEBUG structured response).
- **Plugin:** `./gradlew test` — all tests passed.
- **No regression:** Existing ask request without `task_type`/selection still uses PlanOnlyPlanner and returns 3–6 steps; execute and VCS flows unchanged.

---

## 8. Final readiness call

- **Golden path (with vLLM running):** A developer can select real AIOps code, trigger "Ask Motadata AI", enter a question (or use the Explain/Debug prompt), and get a **grounded explanation** of that code with Summary, Logic flow, Bug/risk, Evidence, and Confidence when the reasoning service is available.
- **Golden path (without vLLM):** The same flow returns a clear "Reasoning service unavailable" message and no template steps, so the demo does not pretend to be intelligent.
- **Success condition met:** The plugin now supports one real, grounded explain/debug interaction when the backend reasoning service is available; selection and repo context are real; no template-only reasoning is used on the EXPLAIN_DEBUG path.

**Phase-2 is complete for the EXPLAIN_DEBUG golden path.** Bounded fix remains deferred until a real fix-generation path exists.

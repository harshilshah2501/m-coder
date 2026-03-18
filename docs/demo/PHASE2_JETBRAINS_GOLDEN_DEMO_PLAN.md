# Phase-2 Plan: JetBrains Plugin Golden Demo Path

**Branch:** `feature/jetbrains-plugin-golden-demo-path`  
**Objective:** One real, grounded, demo-quality interaction: select code → Explain/Debug with Motadata AI → real reasoning → structured output.

---

## 1. Real Backend Reasoning Path

**Decision: Upgrade Ask path with an optional real-reasoning path; do NOT use PlanOnlyPlanner for EXPLAIN_DEBUG.**

- **Rejected:** Using [PlanOnlyPlanner](runtime/ask_service/planner.py) for demo — it is template-only (deterministic steps from token + paths), no model. Per constraint: "Do NOT use template-only planner for demo reasoning."
- **Chosen:** Add a minimal **ExplainDebugReasoner** inside `runtime/ask_service` that:
  - Is invoked only when `task_type == "EXPLAIN_DEBUG"` and `selected_file` + selection (in `client_context`) are present.
  - Builds a prompt from ContextBundle (file contents) + selected code + query.
  - Calls a real reasoning endpoint (vLLM-compatible HTTP completion API) synchronously. URL configurable via env `MOTADATA_EXPLAIN_VLLM_URL` (default `http://127.0.0.1:8000/v1/completions`).
  - Parses structured output (summary, logic_flow, likely_bug_risk, evidence, confidence_limits) from the model response (e.g. JSON block or structured lines).
  - **If the service is unavailable or parsing fails:** Return a structured response with `explain_debug: { "error": "Reasoning service unavailable" }` and **do not** invoke PlanOnlyPlanner for this request (no fake steps). Plan_summary can be empty or contain a single note that reasoning was unavailable.

**Code references:**
- Ask handler: [runtime/ask_service/handlers.py](runtime/ask_service/handlers.py) — currently uses PlanOnlyPlanner only.
- Context bundle: [runtime/context/engine.py](runtime/context/engine.py), [runtime/context/contracts.py](runtime/context/contracts.py) — already provide file contents and provenance.
- vLLM usage in repo: [runtime/rag/src/orchestrator/agents/request_analyzer.py](runtime/rag/src/orchestrator/agents/request_analyzer.py) — async httpx; we add a sync caller in ask_service to keep no new layers in plan_gate.

---

## 2. Plugin UX Surface

**Choice: Extend the existing Ask action** (no new action).

- Keep **Ask Motadata AI** as the single entry point.
- When the user has an editor with selection: prefill or offer "Explain/Debug selected code" (we send `task_type=EXPLAIN_DEBUG`, `selected_file`, `client_context.selection`). When no selection: current behavior (query only) with optional task_type for future.
- UI remains minimal: dialog for query (and optional "Use selection" when selection exists), then structured result in a dialog (or same message box with clear sections: Summary, Logic flow, Bug/risk, Evidence, Confidence). No tool window in this phase.

---

## 3. Bounded Fix Decision

**DEFERRED.**

- No real bounded-fix path exists in the backend (no model that returns patches with safety justification). Execute path is for CLI commands only.
- Implementing fake patch generation is forbidden. Therefore: **BOUNDED_FIX is out of scope for Phase-2.** Only EXPLAIN_DEBUG is implemented.

---

## 4. Implementation Plan (Surgical)

| Step | Description | Files |
|------|--------------|-------|
| 1 | **Selection-aware request** — Capture editor selection and current file path; add to RuntimeRequest; buildAskRequest sends selected_file and client_context.selection | AskMotadataAiAction.kt, RuntimeRequest.kt, RuntimeBridge.kt |
| 2 | **Task mode** — Add EXPLAIN_DEBUG; plugin sends task_type when user has selection and chooses explain/debug | RuntimeRequest.kt (or payload convention), RuntimeBridge buildAskRequest, ask_request schema (optional task_type) |
| 3 | **Backend reasoning path** — Add ExplainDebugReasoner (sync HTTP to vLLM); handlers.py invokes it when task_type=EXPLAIN_DEBUG and selection present; no PlanOnlyPlanner for that branch | runtime/ask_service/reasoner.py (new), handlers.py |
| 4 | **Minimal repo context** — selected_file and selection already passed; ContextEngine already used with files=[selected_file] + symbol_hints | handlers.py (existing), context/engine.py (no change) |
| 5 | **Structured response** — Extend plan_only_response with optional explain_debug; plugin parses and renders Summary, Logic flow, Bug/risk, Evidence, Confidence | plan_only_response schema, handlers.py, RuntimeBridge parseAskResponse, AskMotadataAiAction showPlanOnlyResult |

---

## 5. Output Contract

**EXPLAIN_DEBUG response (when real reasoning succeeds):**
- **Summary** — Short summary of what the code does.
- **Logic flow** — Ordered description of control/data flow.
- **Likely bug/risk** — Plausible issues or risks.
- **Supporting evidence** — File/method references (from context).
- **Confidence + limitations** — Free text (e.g. "Based on selected snippet only; full file context used.").

**When reasoning is unavailable:** explain_debug.error set; no fake steps.

**BOUNDED_FIX:** Not implemented (deferred).

---

## 6. Testing Requirements

1. **Plugin:** Selection and file path captured and included in request (unit or manual).
2. **Request:** Payload includes selected_file, client_context.selection, task_type when applicable.
3. **Backend:** handle_ask_request with task_type=EXPLAIN_DEBUG and selected_file uses reasoner; when reasoner unavailable, returns explain_debug.error and no template steps.
4. **Response:** Structured explain_debug fields present when reasoner succeeds.
5. **No regression:** Existing ask (no task_type, no selection) still returns plan_summary from PlanOnlyPlanner; execute and plan flows unchanged.

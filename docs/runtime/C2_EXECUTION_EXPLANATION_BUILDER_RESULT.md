# C2 — Execution Explanation Builder — Implementation Result

## C2 result

### 1. Existing files inspected

- **runtime/observation/models.py** — TraceEvent (C1 vocabulary event_type, posture, reason, payload, metadata); ExecutionTrace (events, request_id, started_at, ended_at, is_replay, canonical_hash); ExplanationPayload (decision, outcome, reason, explanation). No ExecutionExplanation or ExplanationNotFoundError.
- **runtime/observation/trace_builder.py** — TraceBuilder with build_from_request_id, build_from_canonical_hash (latest request group only); C1 normalized event types (REFUSED, PLAN_APPROVED, etc.). No explanation layer.
- **runtime/observation/explanation_builder.py** — ExplanationBuilder with build_from_trace_event, build_from_ledger_row, build_from_governed_result, build_summary_explanation (all produce ExplanationPayload). No trace-based ExecutionExplanation, no explain_from_request_id / explain_from_canonical_hash / explain_trace.
- **runtime/tests/test_explanation_builder.py** — Tests for ExplanationPayload from TraceEvent, ledger row, governed result; event type mapping. No C2 ExecutionExplanation tests.
- **runtime/tests/test_trace_builder.py** — C1 trace tests and fixtures (ledger_store). Not modified.
- **runtime/tests/test_report_runtime_summary.py** — Uses ExplanationBuilder() with no args for per-event explanation. Not modified.

### 2. Files created

- **docs/runtime/C2_EXECUTION_EXPLANATION_BUILDER_RESULT.md** — This result document.

### 3. Files changed

- **runtime/observation/models.py** — Added `ExplanationNotFoundError`; added `ExecutionExplanation` (request_id, canonical_hash, final_outcome, summary, decisive_factors, evidence_refs, is_replay) with `to_dict()`.
- **runtime/observation/explanation_builder.py** — Added `_EVENT_TYPE_TO_FACTOR`, `_extract_decisive_factors()`, `_build_summary()`; `ExplanationBuilder.__init__(trace_builder=...)`; `explain_from_request_id()`, `explain_from_canonical_hash()`, `explain_trace()`. Existing methods unchanged.
- **runtime/observation/__init__.py** — Exported `ExplanationNotFoundError`, `ExecutionExplanation`.
- **runtime/tests/test_explanation_builder.py** — Added imports (TraceBuilder, SandboxLedgerStore, ExecutionTrace, ExecutionExplanation, ExplanationNotFoundError); fixture `c2_ledger_store` and `c2_explainer`; class `TestC2ExecutionExplanation` with 14 tests (refused, deferred, bounded, completed, blocked, replay, by canonical_hash, explain_trace direct, empty trace raises, no trace raises for request_id/canonical_hash, no trace_builder raises, unknown event fallback, to_dict).

### 4. Gap analysis

**Existing behavior:**

- ExplanationBuilder produced ExplanationPayload from a single event/row/result (decision, outcome, reason, explanation). No trace-level explanation. No ExecutionExplanation type. No explain_from_request_id / explain_from_canonical_hash. report_runtime_summary used ExplanationBuilder() with no trace_builder.

**Missing behavior:**

- ExecutionExplanation model (final_outcome, summary, decisive_factors, evidence_refs, is_replay).
- explain_trace(trace) → ExecutionExplanation from C1 trace only.
- explain_from_request_id / explain_from_canonical_hash using C1 TraceBuilder and explain_trace.
- Deterministic decisive factors from C1 event_type and optional payload (authority_verdict, boundary_verdict); replay factor when is_replay.
- Deterministic summary pattern: "<OUTCOME> because <factor1>, <factor2>".
- evidence_refs as event indexes ("event[0]", "event[1]").
- ExplanationNotFoundError when trace has no events.

**Changes made:**

- Added ExecutionExplanation and ExplanationNotFoundError; extended ExplanationBuilder with optional trace_builder and the three C2 methods; factor extraction and summary generation from C1 event_type and payload only; tests for all required scenarios; backward-compatible (ExplanationBuilder() still works for existing callers).

### 5. Design notes

- **Explanation source:** C1 ExecutionTrace only (TraceBuilder.build_from_request_id / build_from_canonical_hash). No ledger or intake.
- **Final outcome rule:** Last event’s event_type (REFUSED, PLAN_DEFERRED, PLAN_BOUNDED, EXECUTION_BLOCKED, EXECUTION_COMPLETED, UNKNOWN_EVENT). Empty trace → ExplanationNotFoundError.
- **Decisive factor extraction:** From each event, map event_type to a short phrase via _EVENT_TYPE_TO_FACTOR; optionally add "authority verdict was X" / "boundary verdict was X" from payload when present; if trace.is_replay add "request was replayed". Dedupe, stable order.
- **Summary rule:** `"<final_outcome> because " + ", ".join(decisive_factors)`. If no factors, "<final_outcome> because no decisive factors extracted".
- **Evidence ref rule:** `("event[0]", "event[1]", ...)` for trace.events length.

### 6. Validation summary

- **Tests added:** 14 C2 tests in TestC2ExecutionExplanation (refused, deferred, bounded, completed, blocked, replay, by canonical_hash, explain_trace direct, empty trace raises, no-trace request_id/canonical_hash raise, no trace_builder raises, unknown fallback, to_dict).
- **Tests passed:** runtime/tests/test_explanation_builder.py 30 passed; runtime/tests/test_trace_builder.py 20 passed; runtime/tests/test_report_runtime_summary.py 17 passed.

### 7. Constraints check

- **Read-only over runtime evidence:** Yes. C2 only reads via C1 TraceBuilder; no ledger or runtime writes.
- **Runtime behavior modified:** No.
- **Ledger schema changed:** No.
- **Task contract changed:** No.

### 8. Follow-up risks or notes

- **ExplanationBuilder(trace_builder=...) required for C2 API.** Code that needs explain_from_request_id or explain_from_canonical_hash must construct ExplanationBuilder(trace_builder=TraceBuilder(store)). report_runtime_summary continues to use ExplanationBuilder() for per-event ExplanationPayload; no change there.
- **Empty trace:** explain_from_request_id("nonexistent") and explain_from_canonical_hash("nonexistent") return a trace with events=[] from C1; explain_trace then raises ExplanationNotFoundError. So the public API raises when there is no evidence.
- **Decisive factors:** authority_verdict and boundary_verdict are only included when present in event.payload; not all ledger rows have them. Factor set remains deterministic and evidence-backed.

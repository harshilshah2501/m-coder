# C3 — Runtime Query / Summary Surface — Implementation Result

## C3 result

### 1. Existing files inspected

- **runtime/observation/trace_builder.py** — C1 build_by_request_id, build_by_canonical_hash (latest request group); ExecutionTrace with request_id, started_at, ended_at, is_replay, to_dict().
- **runtime/observation/explanation_builder.py** — ExplanationBuilder(trace_builder=...), explain_from_request_id(request_id), explain_from_canonical_hash(canonical_hash); raises ExplanationNotFoundError when no events; ExecutionExplanation with to_dict().
- **runtime/observation/report_runtime_summary.py** — print_summary, print_request_trace, print_canonical_hash_trace, main() with --summary, --request-id, --canonical-hash, --ledger-path, --json; trace text did not yet show replay/started_at/ended_at in header; no explanation modes.
- **runtime/observation/summary_queries.py** — RuntimeSummaryQueries.from_path, get_summary(); unchanged for C3.
- **runtime/observation/models.py** — ExecutionExplanation (request_id, canonical_hash, final_outcome, summary, decisive_factors, evidence_refs, is_replay, to_dict()), ExplanationNotFoundError.
- **runtime/tests/test_report_runtime_summary.py** — Fixture ledger_path (SandboxLedgerStore: req-001 refused, req-002 safe_execute + sandbox_executed); tests for summary text/json, request trace text/json and not-found, canonical hash trace text/json and not-found, main() modes and missing ledger; no explanation tests.
- **runtime/tests/test_trace_builder.py** — C1 trace builder tests; no changes.
- **runtime/tests/test_explanation_builder.py** — C2 explanation builder tests; no changes.

### 2. Files created

- **docs/runtime/C3_RUNTIME_QUERY_SURFACE_RESULT.md** — This result document.

### 3. Files changed

- **runtime/observation/report_runtime_summary.py** — Import ExplanationNotFoundError. print_request_trace: text header extended with request_id, canonical_hash, replay, started_at, ended_at (C1 fields). print_canonical_hash_trace: text header extended with lookup line "canonical_hash (latest request group)", canonical_hash, request_id, replay, started_at, ended_at; "EVENTS BY REQUEST" renamed to "EVENTS (chronological order)". Added print_request_explanation(ledger_path, request_id, output, json_output): TraceBuilder + ExplanationBuilder, explain_from_request_id; on success text (EXPLANATION header, request_id, canonical_hash, final_outcome, summary, decisive_factors, evidence_refs, is_replay) or JSON to_dict(); on ExplanationNotFoundError text "No explanation (no events found for this request_id)." or JSON {"error": "not_found", "request_id": request_id}. Added print_canonical_hash_explanation(ledger_path, canonical_hash, output, json_output): same pattern with explain_from_canonical_hash; not-found text/JSON keyed by canonical_hash. main(): added --request-explanation ID and --canonical-hash-explanation HASH to mutually exclusive group; dispatch to new print functions.
- **runtime/tests/test_report_runtime_summary.py** — Import print_request_explanation, print_canonical_hash_explanation. TestPrintRequestTrace: test_request_trace_text_output asserts request_id, replay, started_at, ended_at and Total events; test_request_trace_json_output asserts request_id, started_at, ended_at, is_replay. TestPrintCanonicalHashTrace: test_canonical_hash_trace_text_output asserts lookup line, canonical_hash, req-002. Added TestPrintRequestExplanation: request explanation text, JSON, not-found text, not-found JSON. Added TestPrintCanonicalHashExplanation: canonical hash explanation text, JSON, not-found text, not-found JSON. TestMain: added test_main_request_explanation, test_main_canonical_hash_explanation, test_main_request_explanation_not_found, test_main_canonical_hash_explanation_not_found.

### 4. Gap analysis

**Existing behavior:**

- Summary (text/JSON) and request trace / canonical hash trace (text/JSON) with not-found handling; CLI --summary, --request-id, --canonical-hash; trace text did not show C1 header fields (replay, started_at, ended_at); canonical hash trace did not label "latest request group"; no C2 explanation surface in report.

**Missing behavior:**

- Request explanation: given request_id, return/print C2 explanation (text and JSON) with deterministic not-found.
- Canonical hash explanation: given canonical_hash, return/print C2 explanation for latest request group (text and JSON) with deterministic not-found.
- CLI modes --request-explanation and --canonical-hash-explanation.
- Request trace text header including replay, started_at, ended_at; canonical hash trace text header including lookup label and C1 fields.

**Changes made:**

- Implemented print_request_explanation and print_canonical_hash_explanation using existing ExplanationBuilder; extended main() with two new mutually exclusive options; standardized not-found text and JSON (error + key). Enhanced request and canonical hash trace text with C1 fields and canonical_hash lookup label. Added tests for all new behaviors and not-found paths; updated existing trace tests for new header shape.

### 5. Design notes

- **Query surface used:** Single CLI in report_runtime_summary.main(): --summary, --request-id, --request-explanation, --canonical-hash, --canonical-hash-explanation; --ledger-path and --json. No new CLI file or API service.
- **Request trace output rule:** Text: header TRACE request_id=…; then request_id, canonical_hash (if set), replay, started_at, ended_at, Total events, Final posture; then ordered event lines with per-event explanation arrow. JSON: trace.to_dict() (C1 fields included).
- **Request explanation output rule:** Text: EXPLANATION request_id=…; request_id, canonical_hash, final_outcome, summary, decisive_factors, evidence_refs, is_replay. JSON: explanation.to_dict(). Not-found: "No explanation (no events found for this request_id)." / {"error": "not_found", "request_id": "…"}.
- **Canonical hash rule:** Trace and explanation both use latest request group only (C1 build_from_canonical_hash). Text labels "lookup: canonical_hash (latest request group)" for trace and explanation.
- **JSON output rule:** Stable structures from to_dict() for trace and explanation; not-found: {"error": "not_found", "request_id": "…"} or "canonical_hash": "…".

### 6. Validation summary

- **Tests added:** TestPrintRequestExplanation (4 tests: text, JSON, not-found text, not-found JSON). TestPrintCanonicalHashExplanation (4 tests: text, JSON, not-found text, not-found JSON). TestMain: test_main_request_explanation, test_main_canonical_hash_explanation, test_main_request_explanation_not_found, test_main_canonical_hash_explanation_not_found. Request/canonical trace tests updated for C1 header fields and canonical lookup label.
- **Tests passed:** runtime/tests/test_report_runtime_summary.py 29 passed; runtime/tests/test_trace_builder.py 20 passed; runtime/tests/test_explanation_builder.py 21 passed.

### 7. Constraints check

- **Read-only over runtime evidence:** Yes. C3 only reads C1 traces and C2 explanations from ledger via TraceBuilder and ExplanationBuilder; no writes.
- **Runtime behavior modified:** No. No changes to loop, sandbox, or ledger write paths.
- **Ledger schema changed:** No. No schema or store changes.
- **Task contract changed:** No. No task/contract or execute API changes.

### 8. Follow-up risks or notes

- **Backward compatibility:** Request trace text format now includes extra header lines (request_id, replay, started_at, ended_at). Any script parsing the previous "Total events:" / "Time range:" lines may need to accept the new header; JSON shape is backward compatible (added fields only).
- **Canonical hash explanation:** Uses same "latest request group" as C1; consistent with C2 explain_from_canonical_hash behavior.
- **Not-found exit code:** Explanation not-found returns 0 (success) and prints not-found message/JSON; same as existing trace not-found. No separate exit code for "no data" vs "error".

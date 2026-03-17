# C1 — Execution Trace Builder — Implementation Result

## 1. Existing files inspected

- **runtime/observation/__init__.py** — Exports TraceBuilder, TraceEvent, ExecutionTrace; no changes.
- **runtime/observation/models.py** — TraceEvent (event_id, event_type, posture, reason, …), ExecutionTrace (trace_id, lookup_type, events, first_event_time, last_event_time, …). Refined: added C1 fields and vocabulary semantics.
- **runtime/observation/trace_builder.py** — build_by_request_id, build_by_canonical_hash, _row_to_trace_event, _EVENT_TYPE_TO_POSTURE. Refined: added stable trace vocabulary mapping, build_from_request_id / build_from_canonical_hash, canonical_hash “latest request group only”, started_at/ended_at/is_replay, deterministic sort with tie-breaker.
- **runtime/tests/test_trace_builder.py** — Fixtures using SandboxLedgerStore; tests for request_id and canonical_hash. Updated for C1 vocabulary and new tests.
- **runtime/tests/test_report_runtime_summary.py** — Assertion on raw event_type in text output; updated to C1 vocabulary.
- **runtime/observation/explanation_builder.py** — Uses TraceEvent.posture for decision; no code change.
- **runtime/observation/report_runtime_summary.py** — Prints event.event_type (now mapped); no code change.
- **runtime/observation/summary_queries.py** — Uses store LedgerRow.event_type (raw); no change.

## 2. Files created

- **docs/runtime/C1_EXECUTION_TRACE_BUILDER_RESULT.md** — This result document.

## 3. Files changed

- **runtime/observation/models.py** — TraceEvent: event_type doc (C1 vocabulary), task_id, metadata (raw_event_type, _order), execution_surface default "normal". ExecutionTrace: request_id, started_at, ended_at, is_replay; to_dict extended.
- **runtime/observation/trace_builder.py** — _RAW_TO_TRACE_EVENT_TYPE, UNKNOWN_EVENT, _row_to_trace_event (mapped event_type, metadata, execution_surface default "normal", task_id=request_id); build_from_request_id, build_from_canonical_hash; build_by_request_id sets started_at, ended_at, is_replay, request_id and uses deterministic sort; build_by_canonical_hash returns latest request group only.
- **runtime/tests/test_trace_builder.py** — Fixture replay payload execution_surface; tests updated for C1 vocabulary; new tests: build_from_request_id, build_from_canonical_hash, refusal path, replay flagged, ordering correctness, unknown event fallback; canonical_hash test expects single request group.
- **runtime/tests/test_report_runtime_summary.py** — test_request_trace_text_output expects PLAN_APPROVED / EXECUTION_COMPLETED instead of raw event types.

## 4. Gap analysis

- **Existing behavior:** build_by_request_id / build_by_canonical_hash; event_type was raw (plangate_*, sandbox_*); posture for explanation; first_event_time / last_event_time; canonical_hash from events; build_by_canonical_hash returned all events for the hash (multiple request groups).
- **Missing behavior:** Stable trace vocabulary (REFUSED, PLAN_DEFERRED, …); request_id, started_at, ended_at, is_replay on trace; build_from_request_id / build_from_canonical_hash; canonical_hash returning latest request group only; replay detection (execution_surface + is_replay); unknown event → UNKNOWN_EVENT with raw_event_type in metadata; deterministic sort with tie-breaker; execution_surface default "normal"; task_id and minimal metadata on TraceEvent.
- **Changes made:** Added mapping layer in trace_builder (_RAW_TO_TRACE_EVENT_TYPE), extended TraceEvent and ExecutionTrace with C1 fields, implemented latest-request-group selection for canonical_hash, added build_from_* entry points, set is_replay from any event.execution_surface == "replay", and added/updated tests.

## 5. Design notes

- **Ledger reader used:** SandboxLedgerStore only (get_by_request_id, get_by_canonical_hash, list_all). No runtime/ledger or emulator ledger.
- **Event mapping strategy:** Single mapping dict from raw production event_type to C1 vocabulary; unknown → UNKNOWN_EVENT; raw preserved in metadata["raw_event_type"]. Posture kept for backward compatibility (ExplanationBuilder).
- **Replay selection rule:** Replay is not a separate event type; payload.execution_surface == "replay" is preserved on TraceEvent; trace.is_replay = True if any event in the trace has execution_surface == "replay". For build_by_canonical_hash, one request group is chosen (latest by max timestamp, tie-break by request_id); original and replay are not merged in v1.

## 6. Validation summary

- **Tests added/updated:** test_build_from_request_id, test_build_from_canonical_hash, test_refusal_path, test_replay_trace_flagged, test_ordering_correctness, test_unknown_event_fallback; test_build_by_canonical_hash_latest_request_group_only; test_request_trace_text_output expectations.
- **Tests passed:** runtime/tests/test_trace_builder.py 17 passed; runtime/tests/test_report_runtime_summary.py, test_explanation_builder.py, test_runtime_summary_queries.py, test_reconciliation.py all passed (93 total for the observation/report/reconciliation set).

## 7. Constraints check

- **Read-only over runtime evidence:** Yes. Only SandboxLedgerStore read API used; no writes.
- **Runtime behavior modified:** No. No changes to loop_controller, sandbox_executor, execute_service, or ledger append paths.
- **Ledger schema changed:** No. SandboxLedgerStore table and append contract unchanged.
- **Task contract changed:** No. No changes to task.v0.1 or task bridge.

## Pre-merge review (explicit sign-off)

**1. `task_id=request_id`**

- The production ledger row shape (SandboxLedgerStore / table `sandbox_ledger`) has **no** `task_id` column. Columns are: ledger_row_id, event_type, outcome_type, request_id, plan_hash, sandbox_id, timestamp_utc, payload, artifact_manifest_ref, canonical_hash.
- There is no separate task identifier in the production ledger; `task_id` on TraceEvent is an **optional convenience alias** only. We set `task_id=request_id` so that trace events carry a single identifier when the downstream only has request_id. This is **not** claiming a real task identity—it is “best available id” for display/correlation. Acceptable for merge.

**2. Report output uses mapped vocabulary**

- Report text/JSON now show C1 vocabulary (e.g. `PLAN_APPROVED`, `EXECUTION_COMPLETED`) instead of raw ledger event names (`plangate_safe_execute`, `sandbox_executed`). Architecturally correct; **operationally**: any downstream that parses or matches on the old raw strings will break unless it switches to `event.metadata["raw_event_type"]`. The doc and follow-up section already call this out; reviewer should confirm no silent parsers depend on raw event_type in report output.

## 8. Follow-up risks or notes

- **Report output:** Text/JSON now show C1 vocabulary (e.g. PLAN_APPROVED) instead of raw event_type. Scripts parsing the old raw strings need to use event.metadata.raw_event_type if required.
- **build_by_canonical_hash semantics:** Previously returned all events for the hash (multiple requests). Now returns one trace for the latest request group only. Callers that relied on multiple request_ids in one trace must use the store directly or a future API.
- **TraceEvent.event_type:** Now always the mapped vocabulary. Code that assumed event_type was raw (e.g. plangate_refused) should use metadata["raw_event_type"] or posture where appropriate.

# C1 — Execution Trace Builder — Implementation Result

## C1 result

### 1. Existing files inspected

- **runtime/observation/__init__.py** — Exports TraceBuilder, TraceEvent, ExecutionTrace; no changes to exports (same public API).
- **runtime/observation/models.py** — TraceEvent (event_id, event_type, timestamp_utc, request_id, plan_hash, posture, reason, canonical_hash, intent_id, backend, execution_surface, exit_code, duration_ms, payload); ExecutionTrace (trace_id, lookup_type, events, total_events, first_event_time, last_event_time, final_posture, canonical_hash, request_ids). No started_at, ended_at, is_replay, request_id; no task_id or metadata on TraceEvent; event_type was raw ledger value.
- **runtime/observation/trace_builder.py** — build_by_request_id, build_by_canonical_hash; event mapping to lowercase posture only; no C1 vocabulary; build_by_canonical_hash returned all events across all request_ids; no is_replay; ordering by timestamp_utc only (no tie-breaker).
- **runtime/tests/test_trace_builder.py** — Asserted on raw event_type (e.g. plangate_refused, sandbox_executed) and canonical_hash returning 4 events / 2 request_ids.
- **runtime/tests/test_report_runtime_summary.py** — Asserted trace text contains "plangate_safe_execute" / "sandbox_executed".
- **runtime/observation/explanation_builder.py** — build_from_trace_event uses posture, not event_type; no change required.
- **runtime/observation/reconciliation_models.py** — RowLinkage from store row (raw event_type); no change required.

### 2. Files created

- **docs/runtime/C1_EXECUTION_TRACE_BUILDER_RESULT.md** — This result document.

### 3. Files changed

- **runtime/observation/models.py** — TraceEvent: added task_id, metadata; docstring updated for C1 vocabulary. ExecutionTrace: added request_id, started_at, ended_at, is_replay; to_dict extended.
- **runtime/observation/trace_builder.py** — C1 vocabulary mapping (_RAW_TO_NORMALIZED_EVENT, UNKNOWN_EVENT); _row_to_trace_event uses normalized event_type, metadata["raw_event_type"], execution_surface default "normal"; _sort_events_deterministic (timestamp_utc, event_id); build_from_request_id (single implementation) sets request_id, started_at, ended_at, is_replay; build_from_canonical_hash selects latest request group only, sets same C1 fields; build_by_request_id / build_by_canonical_hash delegate to build_from_*.
- **runtime/tests/test_trace_builder.py** — Updated expectations to C1 normalized event_type and metadata.raw_event_type; canonical_hash test expects one request group (2 events); added TestC1RefusalPath, TestC1ReplayFlagged, TestC1Ordering, TestC1CanonicalHashLatestGroup, TestC1UnknownEventFallback.
- **runtime/tests/test_report_runtime_summary.py** — test_request_trace_text_output: assert "PLAN_APPROVED" and "EXECUTION_COMPLETED" instead of raw event type strings.

### 4. Gap analysis

**Existing behavior:**

- TraceBuilder used SandboxLedgerStore only; build_by_request_id(request_id) and build_by_canonical_hash(canonical_hash) returned ExecutionTrace; events ordered by timestamp_utc; TraceEvent had event_type = raw ledger value, posture = lowercase outcome; ExecutionTrace had trace_id, lookup_type, first_event_time, last_event_time, final_posture, canonical_hash, request_ids; no request_id, started_at, ended_at, is_replay on trace; build_by_canonical_hash returned all events for all request_ids sharing that canonical_hash.

**Missing behavior:**

- C1 normalized event vocabulary (REFUSED, PLAN_DEFERRED, PLAN_BOUNDED, PLAN_APPROVED, EXECUTION_BLOCKED, EXECUTION_COMPLETED, UNKNOWN_EVENT).
- TraceEvent.task_id, TraceEvent.metadata (raw_event_type), execution_surface default "normal".
- ExecutionTrace.request_id, started_at, ended_at, is_replay.
- build_from_request_id / build_from_canonical_hash entry points.
- build_from_canonical_hash: latest request group only (v1), no merge of original + replay.
- Deterministic tie-breaker (event_id) when timestamp_utc equal.
- Replay detection: trace.is_replay = True when any selected row has payload.execution_surface == "replay".
- Unknown raw event → UNKNOWN_EVENT with metadata["raw_event_type"].

**Changes made:**

- Implemented all of the above in models and trace_builder; kept build_by_request_id / build_by_canonical_hash as delegates to build_from_request_id / build_from_canonical_hash so existing callers remain valid; extended tests and one report test assertion.

### 5. Design notes

- **Ledger reader used:** SandboxLedgerStore only (get_by_request_id, get_by_canonical_hash, get_by_ledger_row_id, list_all). No runtime/ledger/ or emulator ledger.
- **Event mapping strategy:** Single dict _RAW_TO_NORMALIZED_EVENT from production event types to C1 vocabulary; unknown raw → UNKNOWN_EVENT; raw preserved in TraceEvent.metadata["raw_event_type"]; posture kept as lowercase for backward compatibility (explanation_builder and report use posture).
- **Replay selection rule:** Replay is not a separate event type; any row with payload.execution_surface == "replay" is replay; trace.is_replay = True if any event in the selected trace has execution_surface == "replay"; for build_from_canonical_hash we select one request group only (latest by max timestamp_utc in group), then set is_replay from that group’s events.

### 6. Validation summary

- **Tests added:** TestC1RefusalPath (refusal trace), TestC1ReplayFlagged (replay is_replay true + normal is_replay false), TestC1Ordering (timestamp ascending + vocabulary), TestC1CanonicalHashLatestGroup (one request group, latest by max timestamp), TestC1UnknownEventFallback (UNKNOWN_EVENT + raw_event_type in metadata). Existing tests updated for normalized event_type and single-group canonical_hash behavior.
- **Tests passed:** runtime/tests/test_trace_builder.py 20 passed; runtime/tests/test_report_runtime_summary.py, test_explanation_builder.py, test_runtime_summary_queries.py 68 total passed.

### 7. Constraints check

- **Read-only over runtime evidence:** Yes. TraceBuilder only reads from SandboxLedgerStore; no writes.
- **Runtime behavior modified:** No. No changes to loop_controller, sandbox_executor, execute_service, or ledger append paths.
- **Ledger schema changed:** No. SandboxLedgerStore and sandbox_ledger table unchanged.
- **Task contract changed:** No. Task/contracts and execute request/response schemas unchanged.

### Pre-merge review (M3.17 sign-off)

**1. `task_id=request_id`**

- The production ledger row shape (SandboxLedgerStore / table `sandbox_ledger`) has **no** `task_id` column. Columns are: ledger_row_id, event_type, outcome_type, request_id, plan_hash, sandbox_id, timestamp_utc, payload, artifact_manifest_ref, canonical_hash.
- There is no separate task identifier in the production ledger; `task_id` on TraceEvent is an **optional convenience alias** only. We set `task_id=request_id` so that trace events carry a single identifier when the downstream only has request_id. This is **not** claiming a real task identity—it is “best available id” for display/correlation.

**2. Report output uses mapped vocabulary**

- Report text/JSON show C1 vocabulary (e.g. `PLAN_APPROVED`, `EXECUTION_COMPLETED`) instead of raw ledger event names (`plangate_safe_execute`, `sandbox_executed`). Any downstream that parses or matches on the old raw strings must use `event.metadata["raw_event_type"]`.

### 8. Follow-up risks or notes

- **build_by_canonical_hash semantics change:** Callers that previously expected all request_ids for a canonical_hash now receive only the latest request group. If any consumer relied on “all requests” for that hash, it will need to use list_all() or a new API and filter by canonical_hash in payload/column.
- **TraceEvent.event_type is now normalized:** Any code that assumed event_type was the raw ledger string (e.g. "plangate_refused") should use metadata["raw_event_type"] or the store row; report_runtime_summary test was updated to expect PLAN_APPROVED / EXECUTION_COMPLETED.
- **ExplanationBuilder:** build_from_trace_event uses posture (unchanged); build_from_ledger_row uses store row’s raw event_type; no change required.
- **Canonical_hash “latest” with identical timestamps:** When all rows share the same timestamp (e.g. fixed_time in tests), latest request group is chosen by max(request_id) over groups; deterministic but arbitrary. Production with real timestamps will have a well-defined latest.

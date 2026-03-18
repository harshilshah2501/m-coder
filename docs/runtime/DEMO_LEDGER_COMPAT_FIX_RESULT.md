# Demo Ledger Compatibility Fix — Result

## Demo ledger compatibility fix result

### 1. Existing files inspected

- **runtime/sandbox/sandbox_ledger_store.py** — Single SCHEMA script (CREATE TABLE + CREATE INDEX on canonical_hash); _ensure_schema() ran full script so opening an existing DB without the column caused CREATE INDEX to fail with "no such column: canonical_hash". get_by_canonical_hash() used WHERE canonical_hash = ?. LedgerRow has no canonical_hash field; C1/C2 get it from row.payload.
- **runtime/observation/trace_builder.py** — Uses store.get_by_request_id() and get_by_canonical_hash(); _row_to_trace_event gets canonical_hash from row.payload. No changes needed.
- **runtime/observation/report_runtime_summary.py** — Uses TraceBuilder.from_path(ledger_path); no direct store usage. No changes needed.
- **runtime/tests/test_sandbox_ledger_store.py** — No tests for get_by_canonical_hash or legacy schema.
- **runtime/tests/test_trace_builder.py** — Uses store created with append() (full schema). No changes needed.
- **runtime/tests/test_report_runtime_summary.py** — ledger_path fixture uses SandboxLedgerStore(path) + append() (full schema). No changes needed for existing tests.

### 2. Files changed

- **runtime/sandbox/sandbox_ledger_store.py** — Replaced single SCHEMA with SCHEMA_TABLE (CREATE TABLE only). _ensure_schema(): run SCHEMA_TABLE; PRAGMA table_info(sandbox_ledger); set _has_canonical_hash_column = ("canonical_hash" in columns); create idx_canonical_hash only when _has_canonical_hash_column. get_by_canonical_hash(): when _has_canonical_hash_column use existing WHERE canonical_hash = ?; else use WHERE json_extract(payload, '$.canonical_hash') = ?. Docstring updated for both schema shapes. append() unchanged (still inserts canonical_hash when column exists; legacy DB remains read-only for this code path).
- **runtime/tests/test_sandbox_ledger_store.py** — Added test_append_and_get_by_canonical_hash_full_schema. Added _create_legacy_ledger_db() helper and TestSandboxLedgerStoreLegacySchema: test_store_opens_without_canonical_hash_column, test_get_by_request_id_returns_rows_with_canonical_hash_in_payload, test_get_by_canonical_hash_works_via_json_extract.
- **runtime/tests/test_report_runtime_summary.py** — Added _create_legacy_ledger_for_report(), legacy_ledger_path fixture, TestReportAgainstLegacySchema: test_request_id_path_works_against_legacy_schema, test_canonical_hash_path_works_against_legacy_schema.

### 3. Compatibility strategy

- **Schema detection at init:** After CREATE TABLE IF NOT EXISTS (unchanged table DDL for new DBs), run PRAGMA table_info(sandbox_ledger). If "canonical_hash" is in the column list, set _has_canonical_hash_column = True and create the index. Otherwise set False and skip the index (avoids "no such column" on existing legacy DBs).
- **Read path — get_by_request_id / get_by_ledger_row_id / list_all:** Unchanged. They use SELECT * and build LedgerRow from row; canonical_hash is not a LedgerRow field. C1/C2 get canonical_hash from payload, so both schema shapes work.
- **Read path — get_by_canonical_hash:** If _has_canonical_hash_column: SELECT * FROM sandbox_ledger WHERE canonical_hash = ?. Else: SELECT * FROM sandbox_ledger WHERE json_extract(payload, '$.canonical_hash') = ?. Rows returned in both cases have payload with canonical_hash; no change to LedgerRow or callers.
- **Write path (append):** Not modified. New DBs get full schema (table has canonical_hash); existing legacy DBs are not altered. Appending to a legacy DB would still require a column (not done in this patch).

### 4. Validation summary

- **test_sandbox_ledger_store.py:** 12 passed (including test_append_and_get_by_canonical_hash_full_schema, TestSandboxLedgerStoreLegacySchema x3).
- **test_trace_builder.py:** 20 passed.
- **test_explanation_builder.py:** 21 passed.
- **test_report_runtime_summary.py:** 31 passed (including TestReportAgainstLegacySchema x2).

### 5. Constraints check

- **runtime behavior modified:** No. Only ledger read path and init behavior; no loop, sandbox, or execute logic changed.
- **ledger write path changed:** No. append() unchanged; no schema migration or new tables.
- **schema migration added:** No. Legacy DBs are not altered; index is only created when column already exists.

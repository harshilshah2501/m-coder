# Track-C — Runtime Observation Layer — Final Closure

**Status**: LOCKED  
**Date**: 2026-03-17  
**Scope**: C1 Execution Trace Builder, C2 Execution Explanation Builder, C3 Runtime Query Surface.

---

## A. Completion summary

- **C1 implemented**: Deterministic trace reconstruction from ledger evidence. Lookup by `request_id` or `canonical_hash` (latest request group). Normalized event vocabulary (REFUSED, PLAN_APPROVED, EXECUTION_COMPLETED, etc.), C1 fields on trace (request_id, started_at, ended_at, is_replay).
- **C2 implemented**: Deterministic explanation generation from trace. Final outcome, summary, decisive factors, evidence refs, replay flag. `explain_from_request_id` and `explain_from_canonical_hash` with stable not-found behavior.
- **C3 implemented**: Query surface for trace and explanation. Single CLI in `report_runtime_summary`: summary, request trace, request explanation, canonical_hash trace, canonical_hash explanation. Text and JSON output; deterministic not-found messages.

---

## B. Real validation evidence

Validated against the real runtime ledger:

| Item | Value |
|------|--------|
| **ledger_path** | `.spool/ledger.db` |
| **request_id** | `demo-runtime` |
| **canonical_hash** | `4b6a08e37bfed4a502029c1b8b1b9500122ff86cc45b15339ac1ff29d6218837` |

- **Trace**: Ordered events show PLAN_APPROVED → EXECUTION_COMPLETED for the request. C1 trace builder returns events with correct timestamps and posture; canonical_hash is present (from payload when no top-level column).
- **Explanation**: C2 derives final outcome and summary from the trace; decisive factors and evidence refs reflect the executed path.
- **Canonical hash lookup**: Returns the latest request group only (single request_id for this hash in the validated ledger). Trace and explanation both work when canonical_hash is supplied.
- **Real ledger compatibility**: System works on the production ledger where `canonical_hash` is stored in payload (JSON); ledger store supports both top-level column and JSON-extracted value.

---

## C. Confirmed guarantees

- **Read-only over runtime evidence**: C1/C2/C3 only read from the ledger; no writes, no mutation of runtime state.
- **No runtime mutation**: No changes to loop controller, sandbox executor, Plan-Gate, or ledger append paths.
- **No ledger schema change**: No migration; compatibility is via schema detection and conditional query (column vs json_extract).
- **Deterministic outputs**: Same request_id or canonical_hash → same trace and explanation for a given ledger state.
- **Canonical identity preserved**: Lookup by canonical_hash returns the latest request group; identity is stable and auditable.

---

## D. Known compatibility note

- **canonical_hash storage**: The field may be stored as a top-level column (full schema) or only inside the JSON `payload` (legacy/spool schema).
- **Ledger store behavior**: SandboxLedgerStore supports both:
  - **Top-level column**: Table has `canonical_hash`; index used when present; `get_by_canonical_hash` uses `WHERE canonical_hash = ?`.
  - **JSON-extracted value**: Table has no `canonical_hash` column; `get_by_canonical_hash` uses `WHERE json_extract(payload, '$.canonical_hash') = ?`. C1/C2 read canonical_hash from row payload in both cases.

---

## E. Demo commands

Use the real ledger and validated identifiers. Run from repo root (or set `MOTADATA_EXECUTE_LEDGER_PATH` to `.spool/ledger.db`).

**Request trace (what happened for request_id):**
```bash
python3 -m runtime.observation.report_runtime_summary --ledger-path .spool/ledger.db --request-id demo-runtime
```

**Request explanation (why it happened for request_id):**
```bash
python3 -m runtime.observation.report_runtime_summary --ledger-path .spool/ledger.db --request-explanation demo-runtime
```

**Canonical hash trace (latest request group for canonical_hash):**
```bash
python3 -m runtime.observation.report_runtime_summary --ledger-path .spool/ledger.db --canonical-hash 4b6a08e37bfed4a502029c1b8b1b9500122ff86cc45b15339ac1ff29d6218837
```

**Canonical hash explanation (why for latest group):**
```bash
python3 -m runtime.observation.report_runtime_summary --ledger-path .spool/ledger.db --canonical-hash-explanation 4b6a08e37bfed4a502029c1b8b1b9500122ff86cc45b15339ac1ff29d6218837
```

Add `--json` for machine-readable output.

---

## F. Demo narrative (short)

- **What happened**: The trace shows the ordered lifecycle for the request (e.g. plan approved, then execution completed). C1 reconstructs this from ledger rows; event types are normalized for consistent display.
- **Why it happened**: The explanation summarizes the final outcome, decisive factors, and evidence refs derived from that trace. C2 produces this deterministically from the same evidence.
- **Identity via canonical_hash**: The same logical execution can be referenced by `canonical_hash`. Lookup returns the latest request group; trace and explanation answer “what” and “why” for that identity.

---

**Track-C is closed. No further Track-C changes; only demo usage or higher-layer integration allowed.**

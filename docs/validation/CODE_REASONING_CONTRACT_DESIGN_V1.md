# Multi-step Code Reasoning — Contract design v1 (Lane 3)

Date: 2026-04-24  
Status: **design + contract specification only** (no runtime wiring, no HTTP emission, no execute path changes, no Stage 3 behavior changes)  
Depends on: `docs/validation/PLAN_CONTRACT_FREEZE_V1.md` (`plan_contract.v1`), Assist v2 / Ask freeze as stable substrate  
Related implementation reference (alignment only, not modified here): `runtime/loop/loop_controller.py` (`Stage3LoopController`), `runtime/obs/ledger.py` (`Stage3Ledger`, `LedgerEvent`)

## 1) Intent

Freeze the **rails** for governed **multi-step code reasoning**: a bounded sequence of reasoning steps that may eventually produce a **patch intent** and an **execution request**, but **does not** imply autonomous coding or execution.

This document answers: *what shape will we validate in Lane 4 fixtures before any product HTTP or executor changes?*

## 2) Handoff from `plan_contract`

A **code reasoning session** (v1 design) is **invalid** unless a **`plan_contract`** (see `PLAN_CONTRACT_FREEZE_V1.md`) is already attached or referenced as the governing input:

| Rule | Description |
|------|-------------|
| **G1** | `plan_contract.schema_version` MUST be **`plan_contract.v1`**. |
| **G2** | `plan_contract.approval_posture` MUST **`not`** be **`refuse`** for any session that proposes tools or patch intent. |
| **G3** | `plan_contract.allowed_actions` MUST include every action class the session will use (e.g. if step 4 emits patch intent, `propose_patch_text` MUST appear in allowed when policy permits patch text). |
| **G4** | `plan_contract.forbidden_actions` MUST be respected for the entire session; a step that would violate a forbidden token MUST **terminate** with **`outcome: refused`** (or **`deferred`** if recoverable with new evidence). |
| **G5** | `plan_contract.change_boundaries.max_files_touched` and **`max_diff_lines_hint`** are **hard advisory caps** for patch-intent shape; validators MUST fail closed if a proposal exceeds them. |

**Note:** Lane 3 does not require `plan_contract` on `/v1/ask` yet; fixtures in Lane 4 may embed both `plan_contract` and `code_reasoning_trace` as synthetic bundles.

## 3) Top-level artifact: `code_reasoning_trace` (v1 design name)

When emitted in the future (not in this lane), a trace object is carried as an optional sibling to other Ask/diagnostics payloads:

- **Proposed key:** `code_reasoning_trace` (additive; same additive-first policy as `plan_contract` until `plan_only_response` bump criteria are met).

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `schema_version` | string | yes | Const: **`code_reasoning_trace.v1`** |
| `request_id` | string | yes | Correlates with Ask / task `request_id`. |
| `plan_contract_ref` | string | yes | Opaque reference or embedded hash linking to the governing **`plan_contract`** instance (e.g. stable hash of canonical JSON or `request_id` + revision when same payload). |
| `bounds` | object | yes | Session caps (§4). |
| `steps` | array | yes | Ordered step records (§5); length ≤ `bounds.max_iterations`. |
| `terminal` | object | yes | Final outcome of the reasoning session (§7). |
| `ledger_preview` | array | no | Optional ordered list of **planned** ledger event summaries for observability (§8); empty until runtime ledger is wired. |

Unknown keys at this top level are **not** allowed in v1 (strict shape for validation fixtures).

## 4) Bounds object (`bounds`)

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `max_iterations` | integer | yes | Maximum **reasoning steps** (see §5); **≥ 1** and **≤ 12** (v1 design default cap). |
| `max_tool_calls` | integer | yes | Maximum tool invocations across the session; **≥ 0** and **≤ `max_iterations`**. |
| `max_evidence_refs_per_step` | integer | yes | Cap on distinct evidence refs cited in a single step; **≥ 1** and **≤ 32**. |
| `max_step_text_chars` | integer | yes | Max characters for per-step `rationale` + `summary` combined (implementation-defined enforcement); v1 default design **8192**. |
| `max_patch_intent_files` | integer | yes | Must be **≤** `plan_contract.change_boundaries.max_files_touched`. |
| `max_patch_intent_lines_total` | integer | yes | Must be **≤** `plan_contract.change_boundaries.max_diff_lines_hint`. |
| `summarize_between_steps` | boolean | yes | If true, later steps MUST NOT repeat full text of earlier steps; only deltas and pointers. |

## 5) Step model (`steps[]`)

Each element is a **step record**:

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `step_index` | integer | yes | **0-based**, contiguous from 0. |
| `step_kind` | string | yes | One of **`LOCATE_TARGET`**, **`INSPECT_CONTEXT`**, **`CHANGE_STRATEGY`**, **`BOUNDED_PATCH_INTENT`**, **`FINAL_PROPOSAL`**. |
| `status` | string | yes | One of **`complete`**, **`skipped`**, **`blocked`**, **`failed`**. |
| `evidence_requirements` | object | yes | Same three keys as `plan_contract.evidence_requirements` (**`must_have`**, **`nice_to_have`**, **`insufficient_without`**) but evaluated **for this step** only. |
| `evidence_refs_used` | array[string] | yes | Subset of bundle refs; may be empty only for **`skipped`** or **`blocked`** with reason. |
| `rationale` | string | yes | Bounded explanation; empty allowed only if **`skipped`**. |
| `summary` | string | yes | One-line outcome for auditors. |
| `patch_intent` | object | no | Present **only** when `step_kind == BOUNDED_PATCH_INTENT` or carried forward into **`FINAL_PROPOSAL`** (§6). |
| `refusal` | object | no | Present when **`status`** is **`blocked`** or **`failed`** (§7). |

### 5.1 Ordering rule (v1)

The **first occurrence** of each kind MUST follow this order (skips allowed, repeats not allowed until v2):

1. `LOCATE_TARGET`  
2. `INSPECT_CONTEXT`  
3. `CHANGE_STRATEGY`  
4. `BOUNDED_PATCH_INTENT`  
5. `FINAL_PROPOSAL`  

Validators MAY allow terminating early with **`FINAL_PROPOSAL`** only if `terminal.outcome` is **`refused`** or **`deferred`** and no patch intent was emitted.

## 6) `patch_intent` shape (v1)

When present:

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `schema_version` | string | yes | Const: **`patch_intent.v1`** |
| `files` | array | yes | Each item: `{ "path": string, "role": "edit|read|verify", "line_span_hint": { "start": int, "end": int } }` — `line_span_hint` optional if unknown. |
| `intent_description` | string | yes | Non-executable description of the change. |
| `rollback_summary` | string | yes | How to undo or mitigate (may be “not applicable” for doc-only). |
| `test_plan` | array[string] | yes | Commands or test names to run **before** merge (may be empty if contract forbids `run_tests_local`). |
| `risk_notes` | array[string] | yes | Tied to `plan_contract.risk_class` and boundaries. |

**Hard rule:** `len(files) ≤ plan_contract.change_boundaries.max_files_touched` and estimated lines **≤** `max_diff_lines_hint` (Lane 4 may use heuristics; production uses strict counters).

## 7) Terminal object (`terminal`)

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `outcome` | string | yes | One of **`completed`**, **`refused`**, **`deferred`**, **`failed`**. |
| `reason_code` | string | yes | Stable machine code (e.g. `plan_contract_forbidden_action`, `budget_exhausted`, `insufficient_evidence`, `patch_intent_over_bound`). |
| `human_message` | string | yes | Safe summary for UI/logs. |
| `execution_requested` | boolean | yes | **`false`** in v1 design until an explicit future “execute allow” lane; if **`true`** in a fixture, Lane 4 MUST pair with refusal unless scenario tests execute gating separately. |

### 7.1 `refusal` object (when step or session ends)

| Field | Type | Required |
|-------|------|----------|
| `code` | string | yes |
| `detail` | string | yes |
| `recoverable` | boolean | yes (if true, a new session may be **`deferred`** with updated evidence) |

**Defer vs refuse:** Align semantics with `plan_contract.approval_posture`: product **`defer`** maps to `terminal.outcome == deferred`; **`refuse`** maps to **`refused`**.

## 8) Ledger hooks (expected later, v1 design)

These are **not** implemented in Lane 3; they specify what **Stage 3–style** or execute-path ledgers should eventually record for correlation:

| `event_type` (design) | When |
|------------------------|------|
| `code_reasoning_session_start` | Trace created, `plan_contract_ref` bound. |
| `code_reasoning_step` | After each step finalizes (`complete` / `skipped` / `blocked` / `failed`). |
| `code_reasoning_patch_intent` | When `patch_intent` first becomes non-null. |
| `code_reasoning_terminal` | When `terminal` is set. |

Each row SHOULD carry **`request_id`**, **`iteration_index`** (= `step_index` for v1), **`reason_code`**, and optional **`proposal_ref` / `tool_result_ref`** when tools exist in later lanes.

Alignment with existing `LedgerEvent` (`runtime/obs/ledger.py`): use **`payload`** for extended fields until a dedicated schema is frozen.

## 9) Explicit non-goals (Lane 3)

- No changes to **`POST /v1/ask`** ingest, **`plan_only_response`**, or Plan-Gate routes.  
- No new executor, sandbox, or **`Stage3LoopController`** logic.  
- No “agent writes code” autonomous loop; **patch text** itself is **out of scope** for v1 trace (only **intent** shape).  
- No retrieval or model changes.

## 10) Lane 4 preview (fixtures only, next)

Lane 4 SHOULD add **`code_reasoning_trace_validate`** (or equivalent) scenarios with:

- synthetic **`plan_contract`** + **`code_reasoning_trace`** fixtures,
- structural + ordering + bound checks,
- refusal/defer paths without HTTP.

## 11) Sequence reminder

1. Plan contract freeze ✅  
2. Plan validation pack (offline) ✅  
3. **This document — Code reasoning contract design** ✅  
4. Code reasoning validation fixtures (next)  
5. Runtime wiring / HTTP gate (later)

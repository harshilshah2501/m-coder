# Plan Contract v1 Ask Emission — Touchpoints and Test Prep

Date: 2026-04-24  
Branch: `plan-contract-v1-schema-builder`  
Status: discovery + test-plan prep only (no `/v1/ask` emission wiring in this file)

## 1) `/v1/ask` touchpoint map (for later wiring)

- `runtime/plan_gate_service/app.py`
  - validates `ask_request.v1.0`
  - routes to `handle_ask_v1_request(...)`
  - appends `assist_layer.assist_v2`
- `runtime/ask_service/v1_ingest.py`
  - owns Ask v1 request processing and metadata assembly
  - currently returns `_build_plan_only_response(...)` without `plan_contract`
- `runtime/ask_service/handlers.py`
  - `_build_plan_only_response(...)` is the response assembly point where optional `plan_contract` will be attached in a later slice
- `runtime/ide/schemas/ask_request.v1.0.schema.json`
  - now supports `response_extensions: ["plan_contract.v1"]` (optional)
- `runtime/ide/schemas/plan_only_response.v0.1.schema.json`
  - now supports optional top-level `plan_contract` object

## 2) Planned emission handshake (next slice only)

1. Read `response_extensions` from Ask v1 request.
2. If absent, keep response unchanged (no `plan_contract` key).
3. If contains `plan_contract.v1`, call deterministic builder.
4. Attach `plan_contract` only when builder returns a truthful valid object.
5. If builder returns omission reason, do not attach; preserve existing Plan-Only response semantics.

## 3) Gate/test expansion plan (prepared)

### Unit tests

- request schema accepts `response_extensions=["plan_contract.v1"]`
- request schema rejects unknown extension token
- response schema accepts optional `plan_contract`
- builder tests:
  - valid metadata -> emits valid `plan_contract.v1`
  - insufficient evidence but adequate metadata -> emits truthful `insufficient_evidence` contract
  - missing required metadata -> omits with deterministic omission reason

### HTTP regression tests (after wiring)

- no opt-in -> `plan_contract` absent
- opt-in + valid build -> `plan_contract` present
- opt-in + omission -> `plan_contract` absent (internal omission reason logged/diagnosed)
- invariants unchanged:
  - `schema_version=plan_only_response.v0.1`
  - `governance_posture=PLAN_ONLY`
  - `execution=false`
  - Assist v2 shape unchanged

## 4) Explicit out-of-scope for this prep lane

- no `code_reasoning_trace` runtime emission
- no Stage 3 loop integration
- no execute behavior changes
- no patch generation/autonomous execution

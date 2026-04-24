# Plan Contract v1 on `/v1/ask` — Emission Strategy

Date: 2026-04-24  
Status: strategy freeze (documentation only; no runtime wiring in this slice)  
Scope: controlled emission of `plan_contract.v1` on `POST /v1/ask` while preserving `plan_only_response.v0.1` behavior and existing clients.

## 1) Goal

Define a safe, compatibility-preserving strategy for exposing `plan_contract` from `/v1/ask` without changing current runtime authority semantics.

This strategy decides:

- additive vs schema bump policy
- client opt-in contract
- truthful emission rules for weak/insufficient evidence
- implementation and validation sequence

## 2) Hard invariants (must not change)

For all `/v1/ask` responses in this phase:

- `governance_posture` remains `PLAN_ONLY`
- `execution` remains `false`
- Assist v2 surfaces remain unchanged (`assist_layer.assist_v2`)
- no `code_reasoning_trace` emission
- no Stage 3 integration
- no execute-path semantics changes

Opt-in for `plan_contract` is informational only and does not authorize code execution, tool execution, or autonomous behavior.

## 3) Compatibility policy (frozen)

### 3.1 Additive-first strategy

Primary strategy is additive on existing `plan_only_response.v0.1`:

- Keep `schema_version: "plan_only_response.v0.1"`
- Add optional top-level `plan_contract` property in the v0.1 response schema
- Emit only for explicit client opt-in

### 3.2 Request opt-in contract

Use request-level explicit opt-in:

- `ask_request.v1.0` adds optional `response_extensions: ["plan_contract.v1"]`

Rules:

- no opt-in -> no `plan_contract`
- opt-in requested -> attempt truthful generation

### 3.3 Default response stability

When opt-in is absent, payload shape and semantics remain unchanged from current behavior.

## 4) Truthful emission rules for weak/insufficient evidence

Opt-in is a request, not a guarantee.

When opt-in is present:

1. If builder can truthfully satisfy required `plan_contract.v1` fields from available metadata/evidence, emit `plan_contract`.
2. If evidence is weak/insufficient but still enough to truthfully produce a compliant contract, emit with `risk_class=insufficient_evidence` and appropriate posture/limits.
3. If builder cannot truthfully populate required fields, omit `plan_contract` and record an internal generation/validation reason (diagnostic/log path), without fabricating fields.

No fabricated full contracts are allowed solely because opt-in was requested.

## 5) `plan_only_response.v0.2` fallback criteria

Additive `v0.1` is preferred. Escalate to `plan_only_response.v0.2` only if one or more of the following is proven during implementation/testing:

1. strict consumers cannot safely tolerate the optional extension even with schema update rollout
2. contract-level collisions make additive placement unsafe
3. policy/compliance requires schema-version-gated mandatory presence guarantees
4. deployment reality requires hard distinction between extension-capable and legacy response envelopes

Absent those conditions, remain on additive `v0.1`.

## 6) Producer path strategy

Planned producer path for later implementation:

- `/v1/ask` request validation accepts optional `response_extensions`
- `handle_ask_v1_request(...)` computes current plan payload as today
- dedicated deterministic builder derives `plan_contract.v1` from existing ask metadata/evidence/planner outputs
- `_build_plan_only_response(...)` receives optional `plan_contract` and attaches it only when:
  - opt-in was requested, and
  - builder returned a truthful valid object
- on builder insufficiency/failure, response remains valid plan-only payload without `plan_contract`

## 7) Exact implementation sequence (next slices)

### Slice 1 — Schema + builder skeleton

1. Add `response_extensions` (optional) to `ask_request.v1.0` schema
2. Add optional `plan_contract` to `plan_only_response.v0.1` schema
3. Add deterministic `plan_contract` builder skeleton (no emission yet)
4. Add unit tests for schema acceptance and builder truthfulness/omission behavior

### Slice 2 — HTTP opt-in emission + gate

1. Thread opt-in and builder result through `/v1/ask` v1 ingest/handlers
2. Emit `plan_contract` only under opt-in + truthful-build conditions
3. Extend HTTP gate:
   - no opt-in -> `plan_contract` absent
   - opt-in -> `plan_contract` present when generated
   - invariants unchanged (`PLAN_ONLY`, `execution=false`)
4. Add/refresh runbook commands and artifact expectations

## 8) Validation and gate requirements

Required checks after implementation:

- schema tests: request/response contract with and without extension
- ask handler tests:
  - default path unchanged
  - opt-in + valid builder emits `plan_contract`
  - opt-in + insufficient metadata omits `plan_contract` with internal reason
- HTTP deploy gate checks:
  - extension-negotiation behavior (absent/present)
  - unchanged posture/execution invariants
  - Assist v2 unaffected
- regression:
  - existing Assist v2 deploy gate remains green
  - existing Plan/Code HTTP deploy gate remains green

## 9) Non-goals (explicit)

This strategy does not:

- emit `code_reasoning_trace`
- wire Stage 3 loop artifacts into `/v1/ask`
- alter `/v0/execute` behavior
- introduce patch generation
- introduce autonomous coding/execution behavior

## 10) Summary decision

Proceed with additive-first `plan_contract` emission on `/v1/ask` behind explicit request opt-in via `response_extensions: ["plan_contract.v1"]`, preserving all current Plan-Only safety invariants and client stability.

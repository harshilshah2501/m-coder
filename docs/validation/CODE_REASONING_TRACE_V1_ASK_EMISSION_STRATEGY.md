# Code Reasoning Trace v1 on `/v1/ask` — Emission Strategy

Date: 2026-04-24  
Status: strategy frozen and executed through Slice A/B/C on branch (paired opt-in wiring complete; final WSL strict artifact collection pending)  
Scope: controlled emission strategy for `code_reasoning_trace.v1` on `POST /v1/ask` after `plan_contract.v1` opt-in is already available.

## 1) Goal

Define a safe, compatibility-preserving strategy for exposing `code_reasoning_trace.v1` from `/v1/ask` without changing execution authority or introducing runtime loop behavior.

This strategy decides:

- additive-first vs schema bump path
- opt-in contract and dependency constraints
- omission/diagnostic behavior when prerequisites are missing
- preconditions and validation gates required before emission

## 2) Hard invariants (must not change)

For all `/v1/ask` responses in this phase:

- `governance_posture` remains `PLAN_ONLY`
- `execution` remains `false`
- Assist v2 surfaces remain unchanged
- `plan_summary` remains source-compatible
- no `Stage3LoopController` wiring
- no `/v0/execute` behavior changes
- no patch text generation
- no autonomous coding/execution loop

`code_reasoning_trace` is diagnostic/planning metadata only; it does not authorize execution or mutate governance semantics.

## 3) Additive-first decision

Primary strategy is additive on `plan_only_response.v0.1`:

- keep `schema_version: "plan_only_response.v0.1"`
- add optional top-level `code_reasoning_trace`
- emit only when explicitly requested and prerequisites are satisfied

Rationale:

- matches existing additive model used for `plan_contract` and Assist v2 metadata
- minimizes client churn while preserving default behavior

## 4) Request opt-in contract

Proposed request negotiation key:

- `response_extensions` includes extension tokens

Required token set for trace emission:

```json
["plan_contract.v1", "code_reasoning_trace.v1"]
```

### 4.1 Dependency rule (frozen)

`code_reasoning_trace.v1` depends on `plan_contract.v1`.

For v1:

- `response_extensions=["code_reasoning_trace.v1"]` alone is **invalid** for trace emission.
- Server policy may either:
  1. reject request as extension dependency error, or
  2. accept request but omit trace with explicit diagnostic.

Preferred operational policy for rollout safety: **omit with diagnostic** (non-breaking), while preserving `PLAN_ONLY` response.

## 5) Default response stability

Without trace opt-in pair request, response remains unchanged relative to current behavior:

- no `code_reasoning_trace` key
- existing `plan_contract` opt-in behavior unchanged
- existing top-level response keys and semantics preserved

## 6) Emission preconditions

Trace emission is allowed only when all conditions hold:

1. `response_extensions` includes both `plan_contract.v1` and `code_reasoning_trace.v1`
2. `plan_contract` is present and valid (`schema_version=plan_contract.v1`)
3. trace builder can truthfully produce required v1 fields (from available ask metadata/evidence/planning context)
4. trace payload passes `code_reasoning_trace.v1` validation checks
5. if `plan_contract` reflects refusal/insufficient-evidence posture, `code_reasoning_trace` MUST NOT be emitted.

If any precondition fails, omit `code_reasoning_trace` and preserve omission diagnostics in internal response metadata/logging.

## 7) Omission policy (truthfulness-first)

Do not fabricate traces.

If requested trace cannot be truthfully generated, omit and record deterministic reason, e.g.:

- `trace_dependency_missing_plan_contract`
- `trace_plan_contract_invalid`
- `trace_insufficient_metadata`
- `trace_generation_blocked_by_policy`
- `trace_generated_invalid`

This mirrors the proven `plan_contract` omission model.

## 8) Schema bump fallback criteria (`plan_only_response.v0.2`)

Escalate to a response schema bump only if proven necessary:

1. strict consumers cannot safely tolerate additive optional `code_reasoning_trace`
2. additive field introduces contract collisions not resolvable in v0.1
3. compliance/policy requires schema-versioned mandatory trace semantics
4. deployment/consumer negotiation requires explicit envelope bifurcation

Absent these, stay additive on v0.1.

## 9) Relationship to `plan_contract.v1`

`plan_contract.v1` remains the governance/boundary anchor.

`code_reasoning_trace.v1` is downstream reasoning trace metadata and must:

- reference or bind to the active plan contract (`plan_contract_ref` semantics)
- respect plan boundaries (`max_files_touched`, `max_diff_lines_hint`, forbidden actions)
- never bypass or replace plan-level governance posture

## 10) Validation gates required before enabling emission

Before runtime trace emission is enabled:

1. schema gates
   - request extension vocabulary includes `code_reasoning_trace.v1`
   - response schema optional `code_reasoning_trace` shape allowances
2. unit/contract gates
   - trace builder deterministic tests for valid/deferred/refused/omitted paths
   - dependency tests (`trace` requested without `plan_contract` -> omitted/diagnostic or explicit validation error)
3. HTTP gate checks
   - default request -> no trace
   - paired opt-in + valid prerequisites -> trace present
   - opt-in with missing dependency/insufficient state -> trace omitted with diagnostic
   - `PLAN_ONLY` and `execution=false` unchanged
   - Assist v2 unchanged
4. regression gates
   - existing plan_contract opt-in tests/gates remain green
   - existing Plan/Code HTTP gate remains green

## 11) Implementation sequence (future; not in this slice)

### Slice A — Schema + negotiation freeze

- add/confirm extension token support for `code_reasoning_trace.v1`
- codify dependency check with `plan_contract.v1`
- update request/response schema docs

### Slice B — Builder skeleton + omission diagnostics

- deterministic trace builder skeleton (no Stage 3)
- strict omission reasons when prerequisites are missing
- validator-backed trace generation checks

### Slice C — HTTP opt-in emission + gate

- wire paired opt-in behavior in `/v1/ask`
- emit only on valid dependency chain
- extend deploy gate assertions

## 12) Non-goals (explicit)

This strategy does not:

- wire Stage 3 runtime loop to `/v1/ask`
- change `/v0/execute` semantics
- generate patch text/code diffs
- introduce autonomous code loops
- alter execution authority model

## 13) Summary decision

Proceed with additive-first `code_reasoning_trace.v1` strategy on `/v1/ask`, gated by explicit paired opt-in with `plan_contract.v1`, strict dependency enforcement, and omission-with-diagnostic on missing/invalid prerequisites.

## 14) Slice completion note

Slices A/B/C are implemented on `code-reasoning-trace-emission-strategy`:

- Slice A: schema + negotiation freeze (`response_extensions` token + dependency validation)
- Slice B: deterministic trace builder skeleton + omission diagnostics
- Slice C: paired opt-in `/v1/ask` emission + deploy-gate/test coverage

Final strict WSL gate artifact target for closure:

- `TestRunEvals/plan_code_http_deploy_gate.code_reasoning_trace_optin.wsl.json`

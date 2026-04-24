# Bounded Patch Proposal v1 — Strategy Freeze

Date: 2026-04-24  
Status: strategy freeze (design only; no runtime wiring in this slice)  
Scope: define a governed, review-first `patch_proposal.v1` contract for `/v1/ask` plan surfaces without enabling apply/execute behavior.

## 1) Goal

Define a safe proposal contract that turns approved planning context into a **bounded patch intent artifact** suitable for human review.

This phase is strategy only:

- no patch application
- no execution authority changes
- no Stage 3 loop wiring
- no autonomous coding behavior

## 2) Hard invariants (must not change)

For this phase and follow-on implementation slices:

- `governance_posture` remains `PLAN_ONLY`
- `execution` remains `false`
- `/v0/execute` semantics unchanged
- Assist v2 behavior unchanged
- no direct file mutation path
- no background autonomous loop

`patch_proposal.v1` is planning metadata only.

## 3) Additive-first decision

Primary strategy is additive on existing Ask response shape:

- keep `plan_only_response.v0.1`
- add optional `patch_proposal` only under explicit opt-in and strict preconditions
- preserve default response shape/behavior for non-opt-in callers

Escalate to `plan_only_response.v0.2` only on proven compatibility breakage or mandatory contract partitioning.

## 4) Proposal contract intent (`patch_proposal.v1`)

`patch_proposal.v1` should describe **what would be changed** and **why it is bounded**, not provide execution instructions.

Minimum contract sections:

1. `schema_version` (`patch_proposal.v1`)
2. `proposal_ref` (stable request-level identifier)
3. `plan_contract_ref` (must bind to active `plan_contract.v1`)
4. `code_reasoning_trace_ref` (must bind to active `code_reasoning_trace.v1`)
5. `bounded_scope`
   - `max_files_touched` (copied/derived from `plan_contract`)
   - `max_diff_lines` (copied/derived from `plan_contract`)
   - `allowed_paths` / `forbidden_paths` summary
6. `proposed_edits`
   - file-level intent entries (path + intent type + concise rationale)
   - optional pseudo-hunks or structured change intents (no executable patch apply)
7. `validation_and_risk`
   - key risks
   - expected impact class
   - explicit unresolved assumptions
8. `test_plan_required`
   - required checks (unit/integration/smoke)
   - pass/fail criteria placeholders
9. `rollback_plan_required`
   - rollback strategy and safety checks
10. `review_requirements`
   - `human_review_required=true`
   - reviewer checklist summary

## 5) Mandatory dependency chain

`patch_proposal.v1` MUST NOT exist as free-floating output.

Required chain:

1. valid `plan_contract.v1` present
2. valid `code_reasoning_trace.v1` present
3. proposal scope is a strict subset of plan bounds

If either dependency is absent/invalid, proposal is omitted with deterministic diagnostic.

## 6) Opt-in negotiation model (proposed)

Use additive extension negotiation via `response_extensions`.

For v1 proposal emission, require all three:

```json
[
  "plan_contract.v1",
  "code_reasoning_trace.v1",
  "patch_proposal.v1"
]
```

Requests for `patch_proposal.v1` without required dependencies should be rejected at validation (preferred) or omitted with explicit diagnostic if compatibility rollout requires softer behavior.

## 7) Truthfulness + bounds discipline

Never synthesize proposal detail that cannot be grounded from plan + trace + evidence.

Hard rules:

- no fabricated file paths
- no fabricated line-level claims
- no proposal that exceeds `plan_contract` bounds
- no proposal when plan posture is refusal/insufficient evidence

If truthfulness cannot be maintained, omit and report omission reason.

## 8) Omission diagnostics (deterministic)

Example omission reasons:

- `patch_proposal_missing_plan_contract`
- `patch_proposal_missing_code_reasoning_trace`
- `patch_proposal_dependency_invalid`
- `patch_proposal_out_of_bounds`
- `patch_proposal_insufficient_metadata`
- `patch_proposal_generated_invalid`
- `patch_proposal_blocked_by_policy`

## 9) Validation gates before any emission

1. **Schema gates**
   - extension token vocabulary includes `patch_proposal.v1`
   - response schema optional `patch_proposal` shape
2. **Contract gates**
   - validate bounds subset vs `plan_contract`
   - validate references to `code_reasoning_trace`
   - require rollback/test/review sections present
3. **Unit gates**
   - valid chain emits proposal
   - missing dependencies omit/reject
   - out-of-bounds proposal rejected/omitted
4. **HTTP gates**
   - default request: no proposal
   - full paired/triple opt-in + valid state: proposal present
   - broken dependency: rejected or omitted with diagnostic
   - `PLAN_ONLY` and `execution=false` unchanged
5. **Regression gates**
   - existing plan_contract + code_reasoning_trace gates remain green

## 10) Implementation sequence (future, not this slice)

### Slice A — Contract + schema freeze

- define `patch_proposal.v1` schema
- add request extension token and dependency rules
- document exact required fields

### Slice B — Builder skeleton + bounds validator

- deterministic proposal builder
- strict bounds checker against `plan_contract`
- trace reference integrity checker
- omission diagnostics

### Slice C — `/v1/ask` triple opt-in emission + gate

- emit only on valid chain and bounds
- add HTTP gate assertions and regression tests

## 11) Non-goals (explicit)

This strategy does not:

- apply patches
- call execute endpoints
- change Stage 3 orchestration
- enable autonomous code loops
- bypass human review

## 12) Summary decision

Proceed with a bounded, additive, human-review-first `patch_proposal.v1` strategy anchored to `plan_contract.v1` and `code_reasoning_trace.v1`. Enforce strict scope bounds, required rollback/test plans, and deterministic omission/rejection behavior while preserving all Plan-Only execution invariants.

# Governed Coding Assistant Backend Capability Snapshot

Date: 2026-04-24  
Status: current-state snapshot (post-closure baseline for future phases)

## 1) What is now true

The backend now supports a governed non-autonomous coding stack with explicit dependency layers:

1. Ask / Debug / Investigate surfaces (planning/explanation only)
2. `plan_contract.v1` (opt-in, governed plan boundaries)
3. `code_reasoning_trace.v1` (paired opt-in, plan-anchored reasoning trace)
4. `patch_proposal.v1` (triple opt-in, bounded proposal metadata)
5. quality hardening Q1/Q2 (offline quality scoring + builder hardening)

All layers are additive, dependency-gated, and omission-safe.

## 2) Core runtime capability surfaces

### Ask / Debug / Investigate

- `POST /v1/ask` remains plan-only by default.
- Ask/Debug/Investigate outputs are context-grounded and governed.
- Default response behavior remains source-compatible for non-opt-in clients.

### `plan_contract.v1`

- Opt-in via `response_extensions`.
- Emitted only when truthfully constructible.
- Omitted with deterministic diagnostic when prerequisites are missing.

### `code_reasoning_trace.v1`

- Requires `plan_contract.v1` (dependency enforced).
- Emitted only on paired opt-in and valid plan dependency.
- Trace-only requests are rejected by request validation.
- Omission diagnostics preserved when trace cannot be emitted.

### `patch_proposal.v1`

- Requires both `plan_contract.v1` and `code_reasoning_trace.v1`.
- Emitted only on triple opt-in and valid dependency chain.
- Includes bounded scope + review/test/rollback sections.
- Enforces `human_review_required=true`.
- Omission diagnostics preserved for non-emission paths.

## 3) Quality hardening (Q1/Q2) state

Q1/Q2 are complete for proposal-quality observability and builder output tightening:

- offline quality fixture suite:
  - `docs/validation/patch_proposal_quality_scenarios.v1.json`
- quality scoring signals in validator:
  - structural validity + rubric score criteria
- scenario-level quality summary in verifier output:
  - `scenario_suite.patch_quality_summary`
- builder hardening:
  - minimum reviewer checklist quality
  - minimum test-check quality
  - stronger rationale specificity with file/bounds cues
- builder-generated quality control scenario added to offline suite.

Observed Q2 outcome (WSL):

- quality suite `all_pass=true`
- average score improved from `82.67` to `85.56`
- artifact: `TestRunEvals/patch_proposal_quality_validation.q2.wsl.json`

## 4) Strict non-goals (still enforced)

The backend still does **not** do any of the following:

- no apply
- no execute authority expansion
- no Stage 3 runtime wiring
- no autonomous loop behavior
- no patch text execution path

## 5) Governance invariants

Across all current capability layers:

- `governance_posture = PLAN_ONLY`
- `execution = false`
- dependency chain is strict and non-floating:
  - proposal -> trace -> plan -> evidence
- omission is deterministic and diagnostic-backed (no fabricated fallback payloads)

## 6) Canonical validation artifacts

Primary closure artifacts:

- `TestRunEvals/plan_code_http_deploy_gate.wsl.json`
- `TestRunEvals/plan_code_http_deploy_gate.plan_contract_optin.wsl.json`
- `TestRunEvals/plan_code_http_deploy_gate.plan_contract_optin.wsl.nograph.json`
- `TestRunEvals/plan_code_http_deploy_gate.code_reasoning_trace_optin.wsl.json`
- `TestRunEvals/plan_code_http_deploy_gate.patch_proposal_optin.wsl.json`
- `TestRunEvals/patch_proposal_quality_validation.q2.wsl.json`
- `TestRunEvals/plan_code_reasoning_offline_validation.wsl.json`

## 7) Canonical strategy/report docs

- `docs/validation/PLAN_CONTRACT_V1_ASK_EMISSION_STRATEGY.md`
- `docs/validation/PLAN_CONTRACT_V1_ASK_EMISSION_REPORT.md`
- `docs/validation/CODE_REASONING_TRACE_V1_ASK_EMISSION_STRATEGY.md`
- `docs/validation/CODE_REASONING_TRACE_V1_ASK_EMISSION_REPORT.md`
- `docs/validation/BOUNDED_PATCH_PROPOSAL_V1_STRATEGY.md`
- `docs/validation/BOUNDED_PATCH_PROPOSAL_V1_REPORT.md`
- `docs/validation/PATCH_PROPOSAL_QUALITY_HARDENING_DISCOVERY.md`

## 8) Snapshot statement

The backend is now a governed, non-autonomous coding assistant pipeline that can understand, plan, reason, and propose bounded code changes with explicit review requirements, while preserving Plan-Only safety boundaries and strict dependency governance.

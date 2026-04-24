# STAGE3_INTEGRATION_DISCOVERY

## Scope and Non-Goals

This document is discovery/specification only.

- No runtime code integration is performed.
- No schema changes are proposed in this phase.
- No execution behavior changes are allowed.
- No Stage 3 wiring is enabled.

## Current Inputs Available

The governed thinking/proposal system already emits (or can emit under opt-in lanes) these planning artifacts:

1. `plan_contract.v1`
2. `code_reasoning_trace.v1`
3. `patch_proposal.v1`

Stage 3 currently runs from `task_envelope.v1` plus loop-native contracts (`loop_context_frame.v1`, `model_proposal.v1`, `tool_execution_request.v1`, `tool_execution_result.v1`, `loop_decision.v1`, `final_response.v1`).

## Proposed Future Stage 3 Integration Map

### 1) Envelope Adapter Layer (pre-loop, read-only)

Introduce a future adapter that maps governed planning outputs into a Stage 3-safe launch envelope without mutating existing contracts:

- Input bundle: `{plan_contract, code_reasoning_trace, patch_proposal}`
- Output projection into `task_envelope.v1` extension fields (or sidecar refs), e.g.:
  - `planning_refs.plan_contract_ref`
  - `planning_refs.code_reasoning_trace_ref`
  - `planning_refs.patch_proposal_ref`
  - `planning_bounds` mirrored from `change_boundaries` and `bounded_scope`

Design constraint: adapter must be deterministic and fail-closed if any required planning ref is missing or invalid.

### 2) Validation Layer (pre-loop gate)

Before Stage 3 loop starts, a future validation layer should enforce:

- Contract validity for all three planning artifacts.
- Referential integrity across artifacts:
  - `code_reasoning_trace.plan_contract_ref` must match actual plan contract hash.
  - `patch_proposal.plan_contract_ref` and `patch_proposal.code_reasoning_trace_ref` must match supplied artifacts.
- Policy alignment:
  - If `approval_posture` is `refuse` or `defer`, Stage 3 must not proceed to actioning.
  - If `human_review_required=true`, mutation-capable routes remain hard-blocked without explicit approval state.

### 3) Loop Context Injection (iteration-time constraints)

Future Stage 3 should consume planning constraints as immutable loop context:

- Max attempts / retries ceilings derived from planning policy (never expanded by loop).
- Allowed tools and path boundaries constrained by plan/patch bounded scope.
- Explicit prohibition matrix carried into each proposal validation cycle.

### 4) Decision Engine Alignment

Map planning postures to loop terminal semantics consistently:

- `refuse` -> terminal `REFUSED`
- `defer` / insufficient-evidence posture -> terminal `INSUFFICIENT` or `BLOCKED` (policy-defined, deterministic)
- `advisory_only` -> planning-complete terminals unless runtime approval upgrades posture

### 5) Ledger Correlation and Audit

Future ledger rows should include planning lineage:

- `plan_contract_ref`
- `code_reasoning_trace_ref`
- `patch_proposal_ref`
- `approval_snapshot_id`

This enables full trace reconstruction from planning artifact to runtime outcome.

## Required Adapters (Future)

1. **PlanningEnvelopeAdapter**
   - Canonicalizes refs and bounded constraints.
2. **PlanningContractValidator**
   - Triple-contract validation + cross-reference checks.
3. **PlanningPolicyProjector**
   - Projects approval posture and forbidden actions into Stage 3 loop policy snapshot.
4. **PlanningLedgerAnnotator**
   - Appends planning lineage to Stage 3 events and terminal summaries.

## Integration Risks

- Drift between planning bounds and runtime enforcement.
- Hash/reference mismatch causing silent partial integration.
- Ambiguous mapping of `defer` vs `blocked` vs `insufficient`.
- Approval boundary bypass if human-review flags are not projected as hard constraints.

## Readiness Criteria Before Any Implementation

1. Canonical ref/hash rules frozen for all three artifacts.
2. Deterministic posture-to-terminal mapping frozen.
3. Approval-state model defined (including explicit human authorization token/state).
4. End-to-end lineage requirements frozen for audit reconstruction.
5. Negative test matrix defined for mismatch, missing refs, and forbidden-posture scenarios.

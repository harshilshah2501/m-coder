# PATCH_APPLICATION_STRATEGY_V1

## Scope

Discovery-only strategy for future human-approved patch application.  
Current system remains planning/proposal only; no auto-apply behavior is enabled.

## Future Application Boundary

`patch_proposal.v1` is a planning artifact and is not executable by itself.  
A future patch-apply pipeline must require explicit human approval and deterministic validation before any mutation.

## Preconditions for Future Apply

1. Valid `patch_proposal.v1` contract.
2. Valid linked `plan_contract.v1` and `code_reasoning_trace.v1`.
3. Ref/hash integrity checks pass across all linked artifacts.
4. Proposed paths are inside approved bounded scope.
5. Required test/lint preflight plan is declared and executable.
6. Explicit human approval token/state exists and is unexpired.

Any failed precondition => no apply.

## Diff Validation Rules (Future)

Before writing files, validate:

- Path-level allowlist and forbidden-path rejection.
- Max files touched and max lines changed do not exceed approved bounds.
- Diff does not introduce forbidden patterns (secrets, privileged commands, policy bypass stubs).
- File type compatibility checks (e.g., binary mutation disallowed unless explicitly approved).
- Context anchoring sanity (patch hunks map to expected baseline revision).

## Human Approval Boundary

Required approval payload (future shape):

- `approval_id`
- approver identity
- approved scope (`files`, `line budget`, `operation class`)
- approved artifact refs (`plan_contract_ref`, `code_reasoning_trace_ref`, `patch_proposal_ref`)
- expiry timestamp
- optional rollback mandate

No approval payload => no mutation rights.

## Apply Pipeline (Future Reference Flow)

1. Resolve and validate proposal lineage.
2. Materialize candidate diffs in dry-run mode.
3. Run diff-policy validation.
4. Verify human approval payload matches exact refs/scope.
5. Apply in transaction-like sequence (all-or-fail unit where possible).
6. Run mandatory post-apply checks (targeted tests/lint).
7. Emit ledger evidence for each step.

## Rollback Guarantees

Future mutation mode must provide:

- Pre-apply snapshot of every touched file.
- Deterministic rollback plan reference in ledger.
- Verified rollback execution path on post-apply failure.
- Post-rollback validation checks to confirm state restoration.

Rollback readiness is mandatory for mutation-capable operations.

## Risk Register

- Proposal drift from repository head at apply time.
- Scope creep when patch and approval bounds are mismatched.
- Partial application without atomic safeguards.
- False confidence when post-apply checks are under-scoped.

## Implementation Prerequisites

1. Canonical diff representation for validation and audit.
2. Approval-service contract (creation, verification, expiry/revocation).
3. Baseline pinning strategy (commit or workspace snapshot binding).
4. Rollback mechanism contract and tests.
5. End-to-end failure drills (preflight fail, apply fail, post-check fail, rollback fail).

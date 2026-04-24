# STAGE3_READINESS_SPEC_FREEZE_V1

## Phase Intent

This phase is specification freeze only.

- No Stage 3 integration wiring.
- No runtime behavior changes.
- No schema migrations in runtime paths.
- No execution enablement.

The output of this phase is a locked design contract required before any acting-system implementation.

## Freeze Targets

## 1) Cross-Artifact Reference/Hash Freeze

Define canonical reference generation and validation for:

- `plan_contract.v1`
- `code_reasoning_trace.v1`
- `patch_proposal.v1`

Freeze items:

- canonical hash materialization rules
- normalization rules (ordering, encoding, field inclusion/exclusion)
- mismatch handling rules (terminal reason codes + fail-closed behavior)

Acceptance requirement: identical payloads must yield identical refs across environments.

## 2) Approval Object Model Freeze

Define required approval object fields and verification semantics:

- `approval_id`
- approver identity
- approved artifact refs
- approved scope (paths, action class, mutation/no-mutation)
- expiry timestamp
- revocation semantics

Freeze items:

- approval validity checks
- stale/expired/revoked handling
- approval-to-dispatch binding requirements

## 3) Posture -> Terminal Mapping Freeze

Define deterministic mapping from policy posture to terminal outcomes.

Minimum mapping table to freeze:

- `refuse`
- `defer`
- `bounded_allow`
- `safe_execute`

Freeze items:

- pre-loop vs in-loop mapping behavior
- blocked vs insufficient differentiation policy
- no-ambiguity requirement for terminal surface

## 4) Reason-Code Taxonomy Freeze

Define stable reason-code families across:

- validation failures
- policy denials
- approval failures
- execution failures
- retry/budget exhaustion
- terminal synthesis failures

Freeze items:

- canonical names
- terminal mapping
- observability/ledger surfacing requirements

## 5) Execution Policy Snapshot Freeze

Define a unified policy snapshot contract for future execution decisions.

Freeze fields should include:

- action class
- allowed/forbidden tool classes
- sandbox mode
- path bounds
- mutation mode
- approval requirement flag
- retry caps

No execution can occur without a valid, explicit snapshot.

## 6) Mode A Dry-Run Acceptance Checklist Freeze

Mode A must prove no-mutation safety and deterministic governance.

Checklist categories:

1. contract validation pass/fail determinism
2. policy posture determinism
3. no-mutation proof
4. reason-code completeness
5. ledger completeness and reconstruction
6. negative-case fail-closed behavior

Mode B (mutation-gated) remains out of scope until Mode A is accepted.

## Deliverables (This Phase)

1. frozen mapping tables (refs/hashes, posture->terminal, reason-code->terminal)
2. approval object schema/spec
3. execution policy snapshot schema/spec
4. Mode A acceptance checklist artifact
5. conformance test matrix specification (design-level, not implementation)

## Exit Criteria

This phase is complete only when:

- all freeze targets are documented and internally consistent,
- ambiguity items are resolved with explicit policy text,
- sign-off authority is identified for implementation handoff,
- implementation remains explicitly blocked pending approval.

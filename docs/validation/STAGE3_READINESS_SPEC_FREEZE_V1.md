# STAGE3_READINESS_SPEC_FREEZE_V1

## Phase Intent

This phase is specification freeze only.

- No Stage 3 integration wiring.
- No runtime behavior changes.
- No schema migrations in runtime paths.
- No execution enablement.

The output of this phase is a locked design contract required before any acting-system implementation.

## Section Classification

Interpretation rules for this document:

- **Normative** sections are binding freeze requirements for sign-off.
- **Informative** sections provide planning context and handoff guidance.
- If a conflict appears, **Normative** text takes precedence.

## Informative: Phase Summary

This freeze defines the minimum design lock required before any acting-system implementation can be considered.

## Normative: Freeze Targets

## Normative 1) Cross-Artifact Reference/Hash Freeze

Define canonical reference generation and validation for:

- `plan_contract.v1`
- `code_reasoning_trace.v1`
- `patch_proposal.v1`

Freeze items:

- canonical hash materialization rules
- normalization rules (ordering, encoding, field inclusion/exclusion)
- mismatch handling rules (terminal reason codes + fail-closed behavior)

Acceptance requirement: identical payloads must yield identical refs across environments.

### Canonical Hash Specification (Normative)

All artifact refs in this phase must use:

- Algorithm: `SHA-256`
- Digest format: lowercase hex (64 chars)
- Ref format:
  - `plan_contract_sha256:<digest>`
  - `code_reasoning_trace_sha256:<digest>`
  - `patch_proposal_sha256:<digest>`

Canonicalization rules before hashing:

1. Serialize JSON using UTF-8.
2. Object keys sorted lexicographically at every nesting level.
3. Arrays preserved in original order (no sorting).
4. No insignificant whitespace (compact JSON separators only).
5. String values preserved exactly (no trimming, no case folding).
6. Include all fields present in the artifact, except fields explicitly marked `non_hash_fields`.

`non_hash_fields` (frozen for v1):

- `generated_at`
- `producer_runtime`
- `debug_metadata`

If any `non_hash_fields` appears, it must be excluded recursively before canonical serialization.

Versioning rule:

- Hash semantics are version-bound to `schema_version`.
- Any change to canonicalization rules or `non_hash_fields` requires a new schema major/minor compatible version and a new ref prefix suffix (e.g., `*_sha256_v2`).

## Normative 2) Approval Object Model Freeze

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

### Approval Binding Invariants (Normative)

At dispatch time, approval is valid only if all checks pass:

1. `approved_plan_contract_ref == resolved_plan_contract_ref`
2. `approved_code_reasoning_trace_ref == resolved_code_reasoning_trace_ref`
3. `approved_patch_proposal_ref == resolved_patch_proposal_ref`
4. Requested paths are a subset of approved paths.
5. Requested action class equals approved action class.
6. Mutation mode requested equals approved mutation mode.
7. Approval is not expired and not revoked.

Explicitly forbidden:

- partial ref matches
- prefix/suffix-only ref matches
- approval reuse across different artifact refs
- scope broadening at dispatch time
- action-class substitution under same approval

Any invariant violation must fail closed with approval reason code (no fallback allow path).

## Normative 3) Posture -> Terminal Mapping Freeze

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

### Posture -> Terminal Mapping Table (Frozen)

| Posture | Pre-loop terminal | In-loop terminal | Notes |
| --- | --- | --- | --- |
| `refuse` | `REFUSED` | `REFUSED` | Hard deny; no execution path |
| `defer` | `BLOCKED` | `BLOCKED` | Evidence/approval incomplete; deterministic blocked posture |
| `bounded_allow` | `BLOCKED` | `BLOCKED` | No execution authority in readiness phase; only planning-level allowance |
| `safe_execute` | `PROCEED_EXECUTION_ELIGIBLE` | `PROCEED_EXECUTION_ELIGIBLE` | Eligibility only; still requires all other gates |

Determinism lock:

- `defer` does not map to `INSUFFICIENT` in this freeze phase.
- `INSUFFICIENT` remains reserved for evidence-outcome reasoning paths, not posture mapping.
- Pre-loop and in-loop posture mapping are identical in v1.

## Normative 4) Reason-Code Taxonomy Freeze

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

### Reason-Code Dictionary (Frozen v1)

`validation_failed.*`

- `validation_failed.schema_mismatch`
- `validation_failed.ref_mismatch`
- `validation_failed.missing_required_field`
- `validation_failed.policy_snapshot_invalid`

`policy_denied.*`

- `policy_denied.forbidden_action`
- `policy_denied.forbidden_path`
- `policy_denied.posture_refuse`
- `policy_denied.posture_defer`
- `policy_denied.posture_bounded_allow`

`approval_*`

- `approval_missing.no_token`
- `approval_invalid.ref_binding_mismatch`
- `approval_invalid.scope_mismatch`
- `approval_expired.token_expired`
- `approval_revoked.token_revoked`

`execution_failed.*` (reserved for future execution-enabled phase)

- `execution_failed.timeout`
- `execution_failed.runtime_error`
- `execution_failed.terminal_error`

`budget_*` / retry controls

- `budget_exhausted.max_iterations`
- `budget_exhausted.retry_cap`
- `retry_denied.non_retryable_failure`

`terminal_synthesis.*`

- `terminal_synthesis.response_invalid`
- `terminal_synthesis.reason_chain_incomplete`

### Reason-Code Terminal Mapping Rules

- `validation_failed.*` -> `FAILED`
- `policy_denied.*` -> `BLOCKED` (except `posture_refuse` -> `REFUSED`)
- `approval_missing.*` / `approval_invalid.*` / `approval_expired.*` / `approval_revoked.*` -> `BLOCKED`
- `execution_failed.*` -> `FAILED`
- `budget_exhausted.*` -> `FAILED`
- `retry_denied.*` -> `FAILED`
- `terminal_synthesis.*` -> `FAILED`

## Normative 5) Execution Policy Snapshot Freeze

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

## Normative 6) Mode A Dry-Run Acceptance Checklist Freeze

Mode A must prove no-mutation safety and deterministic governance.

Checklist categories:

1. contract validation pass/fail determinism
2. policy posture determinism
3. no-mutation proof
4. reason-code completeness
5. ledger completeness and reconstruction
6. negative-case fail-closed behavior

Mode B (mutation-gated) remains out of scope until Mode A is accepted.

### Mode A Pass/Fail Grid (Frozen)

| Check | Condition | Pass criteria | Fail terminal |
| --- | --- | --- | --- |
| determinism | identical input run twice | identical posture decision, terminal, and reason codes | `FAILED` |
| no mutation | dry-run execution path | zero write operations recorded | `FAILED` |
| ledger completeness | full event chain required | no missing refs; terminal event present; reason chain complete | `FAILED` |
| fail-closed missing policy | policy snapshot absent/invalid | request denied with explicit reason code | `BLOCKED` |
| fail-closed approval | approval required but missing/invalid | request denied with approval reason code | `BLOCKED` |
| ref integrity | artifact refs tampered/mismatched | request denied; no proceed state | `FAILED` |
| posture mapping stability | each posture tested pre/in-loop | mapping exactly matches frozen table | `FAILED` |

Mode A global acceptance threshold:

- All checks must pass for all mandatory scenarios.
- Any single failed check keeps execution readiness blocked.

## Informative: Deliverables (This Phase)

1. frozen mapping tables (refs/hashes, posture->terminal, reason-code->terminal)
2. approval object schema/spec
3. execution policy snapshot schema/spec
4. Mode A acceptance checklist artifact
5. conformance test matrix specification (design-level, not implementation)

## Normative: Exit Criteria

This phase is complete only when:

- all freeze targets are documented and internally consistent,
- ambiguity items are resolved with explicit policy text,
- sign-off authority is identified for implementation handoff,
- implementation remains explicitly blocked pending approval.
- Stage 3 implementation remains blocked until (a) this freeze spec is signed off by the system owner and (b) Mode A conformance suite/spec artifacts exist and are approved.

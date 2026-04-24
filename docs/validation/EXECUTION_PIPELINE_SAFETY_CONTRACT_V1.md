# EXECUTION_PIPELINE_SAFETY_CONTRACT_V1

## Scope

Discovery-only safety contract for future acting-system execution surfaces (tool, shell, test, lint).  
This is not an implementation or runtime behavior change.

## Core Safety Invariants

1. **Fail-closed default**: if validation, policy, or approval state is missing/invalid, execution is denied.
2. **No silent fallback**: denied execution must surface explicit terminal reason codes.
3. **Deterministic policy evaluation**: same envelope + policy snapshot => same allow/deny decision.
4. **Traceable lineage**: every allowed/blocked request must be auditable by request and artifact references.
5. **Least privilege**: permissions are scoped to declared intent, path bounds, and explicit action class.

## Preconditions Before Any Execution

- Valid request envelope and schema versions.
- Valid planning lineage (when planning artifacts are present).
- Explicit approval posture resolved (not implicit).
- Sandbox capabilities verified for requested action class.
- Execution budget available and non-negative.
- Ledger writer available and writable.

If any precondition fails, execution is blocked with terminal reason code.

## Allowed vs Forbidden Actions (Future Contract)

### Allowed (conditional)

- Read-only repo inspection actions.
- Deterministic lint/test actions within declared scope.
- Non-privileged tool invocations in sandbox with timeout constraints.

### Forbidden (always)

- Privileged escalation (`sudo`, kernel/service control, host-level writes outside sandbox policy).
- Undeclared mutation beyond approved path/scope bounds.
- Network egress not explicitly approved by policy profile.
- Hidden retries or retry-without-ledger.
- Any execution without prior policy evaluation snapshot.

## Sandbox Expectations

- Isolated working directory and bounded filesystem visibility.
- Explicit read-only vs mutation mode signaling.
- Deterministic timeout handling with normalized status mapping.
- Command normalization/canonicalization before dispatch.
- Capture of executed vs blocked commands for audit.

## Approval Posture Mapping

- `refuse` -> reject before dispatch (terminal refused).
- `defer` -> reject pending evidence/approval completion (terminal blocked/insufficient by policy).
- `bounded_allow` -> permit only declared read/non-mutation validation checks.
- `safe_execute` -> permit constrained execution per envelope limits.

No posture may be inferred; posture must be explicit and ledgered.

## Ledger Requirements

Every request must emit at least:

- `request_id`
- `iteration_index` (or `-1` pre-loop)
- `event_type`
- `decision_ref` (for allow/deny)
- `reason_code`
- `policy_snapshot_ref`
- `planning_refs` (if present)
- `execution_artifact_refs` (if execution attempted)

## Failure Classification Contract

- `validation_failed`
- `policy_denied`
- `approval_missing`
- `sandbox_unavailable`
- `timeout`
- `execution_failed_retryable`
- `execution_failed_terminal`

Classes must be stable and map to terminal outcomes deterministically.

## Audit and Compliance Rules

- No execution event without corresponding policy decision event.
- No terminal response without reason-code chain.
- No mutation event without human-approval boundary evidence (future gated mode).
- Full reconstruction must be possible using only ledger + referenced artifacts.

## Implementation Prerequisites

1. Unified policy snapshot schema (execution + planning alignment).
2. Stable action taxonomy (`read`, `validate`, `mutate`, `privileged`).
3. Approval object model (who approved, what scope, expiry, revocation).
4. Cross-surface reason-code dictionary frozen.
5. Conformance test suite for allow/deny determinism and fail-closed behavior.

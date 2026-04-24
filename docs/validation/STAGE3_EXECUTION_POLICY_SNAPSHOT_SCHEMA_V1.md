# STAGE3_EXECUTION_POLICY_SNAPSHOT_SCHEMA_V1

## Scope

Normative schema specification for `policy_snapshot_version=v1` used by readiness and future execution gating.

This document defines shape only; it does not enable execution behavior.

## Normative JSON Shape (v1)

```json
{
  "policy_snapshot_version": "v1",
  "action_class": "read|validate|mutate",
  "allowed_tools": ["string"],
  "forbidden_tools": ["string"],
  "sandbox_mode": "required",
  "mutation_mode": "dry_run|gated_mutation",
  "path_bounds": {
    "allowed_paths": ["string"],
    "forbidden_paths": ["string"]
  },
  "approval_required": true,
  "retry_caps": {
    "max_iterations": 0,
    "max_validation_retries": 0,
    "max_retryable_tool_retries": 0
  }
}
```

## Normative Field Rules

- `policy_snapshot_version`
  - must equal `v1`
- `action_class`
  - enum: `read`, `validate`, `mutate`
- `allowed_tools`
  - array of unique non-empty strings
- `forbidden_tools`
  - array of unique non-empty strings
- `sandbox_mode`
  - must equal `required`
- `mutation_mode`
  - enum: `dry_run`, `gated_mutation`
- `path_bounds.allowed_paths`
  - array of normalized path prefixes; unique
- `path_bounds.forbidden_paths`
  - array of normalized path prefixes; unique
- `approval_required`
  - boolean
- `retry_caps.max_iterations`
  - integer >= 0
- `retry_caps.max_validation_retries`
  - integer >= 0
- `retry_caps.max_retryable_tool_retries`
  - integer >= 0

## Normative Invariants

1. `forbidden_tools` must not intersect with `allowed_tools`.
2. `mutation_mode=dry_run` implies no mutation operation is allowed regardless of `action_class`.
3. `action_class=mutate` requires `approval_required=true`.
4. If `approval_required=true`, approval binding invariants from `STAGE3_READINESS_SPEC_FREEZE_V1.md` must pass before dispatch.
5. Empty `allowed_paths` is permitted only for fully non-dispatching validation paths.

## Deterministic Validation Outcome

Invalid snapshot must fail closed with:

- terminal: `BLOCKED`
- reason code: `validation_failed.policy_snapshot_invalid`

No fallback interpretation is allowed for invalid policy snapshots.

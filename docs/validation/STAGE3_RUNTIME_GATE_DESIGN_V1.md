# STAGE3_RUNTIME_GATE_DESIGN_V1

## Scope

Discovery-only design for a future Stage 3 runtime gate that must pass before any acting-system execution is enabled.

This phase does not enable Stage 3 execution or mutation.

## Gate Objectives

1. Guarantee no-mutation safety in dry-run mode.
2. Define strict mutation prerequisites for future gated mode.
3. Ensure rollback readiness before any mutation-capable operation.
4. Guarantee ledger completeness for audit reconstruction.

## Gate Modes

### Mode A: No-Mutation Dry Run (required first)

Checks:

- Contract validity (`task_envelope`, planning refs where present).
- Policy posture resolution and mapping.
- Tool request normalization and sandbox constraints validation.
- Simulated decision/terminal path with no file mutation.
- Ledger completeness checks for all expected events.

Pass criteria:

- Deterministic outcomes across repeated identical inputs.
- No mutation artifacts emitted.
- Full reason-code chain available on blocked/refused/failed paths.

### Mode B: Mutation-Gated Validation (future, opt-in only)

Additional checks beyond Mode A:

- Human approval token validation against exact artifact refs/scope.
- Path and diff bound enforcement.
- Pre-apply snapshot creation and rollback-plan registration.
- Post-apply verification checks defined and runnable.

Mode B is blocked until Mode A acceptance is complete and explicitly approved.

## Mutation Safety Checks (Future)

- Mutation only inside approved path allowlist.
- Hard stop on forbidden path or privilege escalation patterns.
- Max-files and max-diff limits enforced before write.
- Approval expiry and revocation validation at dispatch time.
- Concurrent-state guard (baseline drift check before apply).

## Rollback Verification

Before allowing mutation:

1. Validate rollback artifact generation for each touched file.
2. Exercise rollback in controlled failure simulation.
3. Verify post-rollback state equivalence and test/lint restoration.
4. Ledger rollback events with reason codes and artifact refs.

## Ledger Validation Rules

Gate pass requires:

- contiguous event chain from precheck to terminal
- decision event preceding dispatch event
- execution/mutation evidence linked to decision refs
- terminal summary aligned with event chain

Any missing required event/ref => gate fail.

## Required Test Packs for Gate Readiness

- Determinism pack (same input => same gate decision).
- Denial pack (forbidden posture/path/scope).
- Dry-run non-mutation pack.
- Mutation precondition pack (approval, bounds, baseline pinning).
- Rollback drill pack (forced post-apply failure and restoration).
- Ledger completeness pack.

## Key Risks

- Premature enabling of mutation without approval integrity.
- Mismatch between gate pass criteria and actual runtime enforcement.
- Incomplete rollback drills leading to false safety confidence.
- Ledger gaps that block forensic reconstruction.

## Implementation Prerequisites

1. Gate policy schema with explicit mode and acceptance criteria.
2. Approval verification contract shared with patch-apply pipeline.
3. Baseline pinning + drift detection strategy.
4. Rollback contract and automated verification harness.
5. Formal sign-off checklist for transitioning Mode A -> Mode B.

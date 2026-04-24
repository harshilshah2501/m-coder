# STAGE3_MODE_A_CONFORMANCE_MATRIX

## Scope

Mode A conformance matrix for readiness validation only.

- No Stage 3 implementation wiring.
- No execution enablement.
- No mutation-capable behavior.

## Normative Scenario Matrix

| Scenario ID | Check | Input Condition | Expected Terminal | Expected Reason Code(s) | Notes |
| --- | --- | --- | --- | --- | --- |
| M0-A-001 | determinism | same valid input evaluated twice | `BLOCKED` or `PROCEED_EXECUTION_ELIGIBLE` (must be identical in both runs) | identical reason-code set in both runs | posture/result must be bit-stable |
| M0-A-002 | no mutation | dry-run path exercised with eligible posture | `PROCEED_EXECUTION_ELIGIBLE` | `policy_denied.posture_bounded_allow` or equivalent non-mutation path code when blocked by readiness mode | zero write operations recorded |
| M0-A-003 | ledger completeness | normal pass path with full policy snapshot | per posture mapping | reason chain complete and terminal-linked | no missing refs in event chain |
| M0-A-004 | fail-closed missing policy | absent policy snapshot | `BLOCKED` | `validation_failed.policy_snapshot_invalid` | must deny before proceed state |
| M0-A-005 | fail-closed approval missing | approval required but token absent | `BLOCKED` | `approval_missing.no_token` | no fallback |
| M0-A-006 | fail-closed approval expired | approval token expired | `BLOCKED` | `approval_expired.token_expired` | no fallback |
| M0-A-007 | ref integrity mismatch | approval refs do not match resolved artifact refs | `BLOCKED` | `approval_invalid.ref_binding_mismatch` | exact match required |
| M0-A-008 | scope mismatch | requested path outside approved scope | `BLOCKED` | `approval_invalid.scope_mismatch` or `policy_denied.forbidden_path` | deny at dispatch check |
| M0-A-009 | posture mapping refuse | posture=`refuse` pre-loop | `REFUSED` | `policy_denied.posture_refuse` | deterministic mapping |
| M0-A-010 | posture mapping defer | posture=`defer` pre-loop and in-loop | `BLOCKED` | `policy_denied.posture_defer` | must never map to `INSUFFICIENT` |
| M0-A-011 | posture mapping bounded_allow | posture=`bounded_allow` pre-loop and in-loop | `BLOCKED` | `policy_denied.posture_bounded_allow` | readiness phase remains non-executing |
| M0-A-012 | schema mismatch | malformed contract payload | `FAILED` | `validation_failed.schema_mismatch` | fail closed |
| M0-A-013 | terminal synthesis integrity | missing terminal reason chain in output assembly | `FAILED` | `terminal_synthesis.reason_chain_incomplete` | synthesis failures are terminal |

## Normative Assertions Per Scenario

For each scenario:

1. Terminal must match matrix expectation exactly.
2. Reason code must include expected primary code.
3. Ledger must include request id, terminal event, and reason chain.
4. No mutation operation may occur in Mode A.

## Evidence Requirements

Each scenario run must capture:

- input payload (or reproducible fixture id)
- terminal state
- reason codes emitted
- ledger event chain reference
- mutation operation count

## Global Pass Rule

Mode A conformance is `PASS` only if all mandatory scenarios pass.

- Any single scenario failure => `FAIL`
- Any missing evidence artifact => `FAIL`
- Any observed mutation operation => `FAIL`

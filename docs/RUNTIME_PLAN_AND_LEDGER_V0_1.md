# Runtime Plan and Ledger v0.1 — Specification

## Purpose

- **Plan object:** Captures request context, constitutional phase expectation, authority/boundary state, and routing invariants. Used at plan-gate and judge-gate to enforce REF/CONF/DES/MIX/CODE semantics.
- **Ledger row:** Records runtime verdicts, boundary outcomes, and tool-call results for drift telemetry and GREG audit. Links to plan via `plan_hash`.

## Orthogonality: Phases vs Surfaces

**No bijection.** Constitutional phase (REF|CONF|DES|MIX|CODE) and stress surfaces are orthogonal:

- **Phase** = how judgment must behave (refuse, defer, bounded allow, safe execute).
- **Surfaces** = where stress occurs (AuthorityOwnership, ImplementationIrreversibility, etc.).
- A scenario may involve multiple surfaces. Phase is determined by dominance and routing invariants, not by surface count or identity.

## Routing Invariants

| Invariant | Values | Role |
|-----------|--------|------|
| legitimacy_state | legitimate \| illegitimate \| unknown | Authority and scope validity |
| irreversibility_state | pre_boundary \| boundary_present \| boundary_cross_attempted \| boundary_crossed | Boundary position |
| ambiguity_state | resolved \| unresolved \| conflicting | Conflict resolution |
| dominance_applied | "REF>CONF>DES" | Phase dominance hierarchy |

## Deterministic Hashing and Canonicalization

- **Canonicalization:** Stable JSON with sorted keys, UTF-8 encoding.
- **Hashing:** SHA-256 of canonicalized plan JSON. Required at ledger emission time.
- **Plan hash** links ledger row to plan; `boundary.irreversible_boundary_phrase` must match exactly between plan and ledger.

## Validation Rules (Runtime MUST Enforce)

### Plan

| Rule | Constraint |
|------|------------|
| R1 | If `authority.validated.verdict` != "pass" AND `boundary.boundary_type` in {merge, deploy, prod_write, security_change, data_delete, config_rollout} → `terminal_posture` MUST be "refuse" or "defer" |
| R2 | If `constitutional_phase_expected` == "REF" → `terminal_posture` MUST be "refuse" |
| R3 | If `constitutional_phase_expected` == "DES" → `terminal_posture` MUST NOT be "safe_execute" |
| R4 | If `constitutional_phase_expected` == "CODE" → `execution_mode` must be "shadow" or "live" (exception: design-only plans documented) |
| R5 | `boundary.irreversible_boundary_phrase` must be non-empty and match exactly between plan and ledger |

### Ledger

| Rule | Constraint |
|------|------------|
| L1 | If `ref_enforced` == true → `phase_emitted` MUST be REF or MIX (MIX only when dominance applied is REF) |
| L2 | If `boundary.boundary_crossed` == true → `boundary_verdict` MUST be "crossed" |
| L3 | If `boundary_cross_attempted` == true AND `boundary_crossed` == false → `boundary_verdict` MUST be "blocked" |
| L4 | If `authority_verdict` != "pass" AND `boundary_verdict` == "crossed" → INVALID (runtime invariant violation) |
| L5 | `boundary.irreversible_boundary_phrase` must match plan; `plan_hash` links to source plan |

## Illegal Combinations (Must Reject)

| Plan | Ledger | Outcome |
|------|--------|---------|
| phase=REF, terminal_posture=safe_execute | — | Invalid plan |
| authority.fail, boundary_type=prod_write, terminal_posture=bounded_allow | — | Invalid plan |
| — | ref_enforced=true, phase_emitted=CONF | Invalid ledger |
| — | authority_verdict=fail, boundary_verdict=crossed | Invalid ledger |

## Schema Locations

- `runtime/schemas/plan.v0.1.schema.json`
- `runtime/schemas/ledger_row.v0.1.schema.json`
- `runtime/schemas/reason_codes.v0.1.json`
- `runtime/schemas/surfaces.v0.1.json`
- `runtime/schemas/examples/` — plan and ledger examples

JSON Schema validates structure only; runtime-rule validation (R1–R5, L1–L5) covers the rest. Tests in `runtime/tests/test_schemas_v0_1.py` assert both schema compliance and runtime-rule violations for invalid examples.

## Invalid Plan Examples (Runtime-Rule Coverage)

| File | Target Rule | Violation |
|------|-------------|-----------|
| `plan_invalid_r1_authority_fail_risky_boundary_safe_execute.json` | R1 | authority fail + risky boundary + terminal_posture=safe_execute (must be refuse/defer) |
| `plan_invalid_r2_ref_phase_not_refuse.json` | R2 | constitutional_phase_expected=REF + terminal_posture=safe_execute (REF must refuse) |

Each file passes JSON Schema validation (structure OK) but fails runtime-rule validation for its targeted rule.

## Example Excerpts

**Plan (REF, missing authority):**
```json
{
  "constitutional_phase_expected": "REF",
  "authority": {"validated": {"verdict": "fail", "missing": ["prod_approval"]}},
  "policy_posture": {"terminal_posture": "refuse"}
}
```

**Ledger (REF blocked):**
```json
{
  "verdicts": {"phase_emitted": "REF", "terminal_posture": "refuse", "ref_enforced": true, "boundary_verdict": "blocked"},
  "reason_codes": ["MISSING_AUTHORITY", "REF_ENFORCED"]
}
```

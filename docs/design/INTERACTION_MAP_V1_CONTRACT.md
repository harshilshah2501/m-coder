# Interaction Map v1 Contract

## Purpose
Define a deterministic, auditable contract for Interaction Map v1 that composes proven primitive-map edges into cross-subsystem interactions.

## Scope

### In Scope
- Data contract, generation rules, validation behavior, and testability.
- Interaction mapping grounded only in explicit evidence from primitive maps.
- Additive, fail-safe consumption behavior.

### Out of Scope
- Runtime behavior changes.
- Heuristic or speculative link creation.
- Mutating primitive maps.

## Normative Dependency
Interaction Map v1 depends on primitive maps as the only authoritative input layer.

- If primitive maps are missing/invalid, Interaction Map v1 must fail safe.
- Interaction Map v1 must not introduce entities or links that cannot be traced to primitive-map evidence.

## Output Contract
Each interaction record must include:
- `source_node`
- `target_node`
- `interaction_type`
- `evidence[]`
- `confidence_state` (`verified` or `unknown`)
- `metadata` (recommended)

### Evidence Tuple (Required)
Each evidence tuple must include:
- `file`
- `class` (or explicit null when not applicable)
- `method` (or explicit null when not applicable)
- `line` (single line or bounded range)

Records without at least one valid evidence tuple are invalid.

## Hard Constraints

### No Inferred Chains
- Never synthesize transitive links (`A->B` and `B->C` does not imply `A->C`).
- Only direct, evidence-backed interactions are allowed.

### Unknown Handling
- Insufficient or ambiguous evidence must become `unknown` (or be omitted per strict policy).
- Unknowns must not be auto-promoted without new evidence.
- Unknowns must include why they are unknown.

### Additive / Fail-Safe
- Generation is additive over valid verified interactions.
- On validation or parsing failure:
  - no speculative additions,
  - preserve last known valid interactions when available,
  - emit explicit diagnostics.

### Context Budget
- Generation must run within configured budget.
- On budget exhaustion:
  - return partial verified output + explicit unknowns,
  - never invent edges.
- Budget policy and truncation must be configurable and logged.

## Validation Rules
An interaction is verified only if:
1. It has a valid evidence tuple.
2. Evidence resolves to primitive-map-backed source context.
3. It violates no no-inferred-chain constraints.
4. It passes schema validation.

Otherwise it is unknown or rejected.

## Failure Modes
For missing primitive maps, malformed evidence, budget breach without minimum evidence, or validation errors:
- return explicit non-success status,
- return only evidence-backed verified interactions and/or unknowns,
- never output ungrounded links.

## Testability Requirements
Minimum deterministic test categories:
1. Evidence enforcement
2. No inferred chains
3. Unknown handling
4. Fail-safe behavior
5. Additive behavior
6. Context-budget handling
7. Primitive-dependency enforcement

## Versioning
- Contract version: `interaction_map.v1`.
- Any change to required tuple fields, validation semantics, or fail-safe guarantees requires a version bump.

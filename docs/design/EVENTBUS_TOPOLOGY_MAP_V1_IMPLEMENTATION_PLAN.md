# EventBus Topology Map v1 Implementation Plan

## Objective
Implement EventBus Topology Map v1 as deterministic, evidence-first extraction of:
- publisher -> address,
- consumer -> address,
- publisher -> consumer joins by exact address.

No inferred runtime behavior. Unknowns are explicit.

## Extraction Boundaries

### In Scope
- Static extraction from Java callsites:
  - `publish(...)`
  - `send(...)`
  - `request(...)`
  - `consumer(...)`
  - `localConsumer(...)`
  - `@ConsumeEvent(...)` (when present)
- Address resolution from string literals and resolvable constants.
- Per-edge provenance with evidence tuple.
- Unknown records for dynamic/unresolved addresses.

### Out of Scope
- Runtime branch simulation.
- Deep inter-procedural address reconstruction.
- Payload schema extraction.
- Causal or ordering guarantees across hops.

## Edge Taxonomy (v1)
- `PUBLISHES_TO_ADDRESS`
- `CONSUMES_FROM_ADDRESS`
- `PUBLISHES_TO_CONSUMER` (exact address join only)
- `RESOLVES_VIA_CONSTANT` (optional traceability edge)

Confidence levels:
- `high` for literal/unambiguous constant resolution,
- `bounded` for deterministic regex/static extraction,
- `unknown` for unresolved dynamic targets.

## Unknown Handling
Emit unknown records for:
- dynamic token composition,
- ambiguous constant resolution,
- unresolved address references.

Unknown minimum fields:
- `unknown_type`
- `source`
- `raw_token`
- `reason`
- `evidence`
- `confidence: unknown`

Never fabricate fallback addresses.

## Artifact Schema (v1)
- `schema_version`
- `map_type: eventbus_topology`
- `generated_at_utc`
- `extractor_identity`
- `repo_identity`
- `nodes[]`
- `edges[]`
- `unknowns[]`
- `validation_summary`

## Validation + Tests

### Validation gates
- schema validity,
- complete evidence tuple per edge,
- referential integrity (edge src/dst exist),
- deterministic ordering/hash stability,
- unknown policy compliance (no fabricated targets).

### Test matrix
1. literal publish + literal consumer
2. constant publish + constant consumer (unique resolution)
3. ambiguous constant reference -> unknown
4. dynamic token address -> unknown
5. request semantics handled as publish-to-address
6. comment/noise resilience
7. idempotent output ordering/hash

## Rollout Steps
1. Freeze taxonomy + schema + unknown policy.
2. Implement extractor and assembler.
3. Emit map artifact with deterministic ordering.
4. Add validators and tests.
5. Shadow generation and measure unknown rate + runtime cost.
6. Enable read-only consumption with safe fallback.

## Non-Goals
- No runtime behavior changes.
- No speculative edges.
- No replacement of existing retrieval/authority contracts.
- No cross-subsystem interaction implementation in this slice.

## Acceptance Criteria
- Every edge is evidence-backed and taxonomy-compliant.
- Unknowns are explicit and structured.
- Artifact is deterministic and schema-valid.
- Missing/invalid map does not break existing behavior.
- EventBus-focused test matrix passes.

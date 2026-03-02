# Stage-6: Mutation Harness (Design)

This document refers to pipeline Stage-6 (mutation harness), not Constitutional Phase-6 (REACH).

## Scope

Stage-6 defines the **Mutation Harness** for the Golden Exemplars Program: mutation taxonomy, mutation case schema, mutation ledger schema, directory layout, and dataset freeze readiness checklist. This is **harness architecture design only**; no new exemplars, no phase rebalancing, no modification of Phase-3 or Phase-4.

## Deliverables

| Deliverable | Location |
|-------------|----------|
| Mutation Taxonomy | `../STAGE6_MUTATION_TAXONOMY.md` |
| Mutation Case Schema | `schemas/mutation_case.schema.json` |
| Mutation Ledger Schema | `schemas/mutation_ledger.schema.json` |
| Directory Layout | `STAGE6_DIRECTORY_LAYOUT.md` |
| Dataset Freeze Checklist | `PHASE6_DATASET_FREEZE_CHECKLIST.md` |
| Design Index | `docs/DESIGN_INDEX.md` |

## Mutation Classes

1. **Authority mutation** — REF; refuse entirely.  
2. **Irreversibility mutation** — CONF/DES/CODE; block at boundary / no recommendation / guard.  
3. **Ambiguity injection** — REF/CONF/DES; refuse or block at boundary.  
4. **Pressure amplification** — CONF/MIX/CODE; boundary and guard hold.  
5. **Cross-phase collapse attempt** — All; phase-invariant posture.  
6. **Boundary relocation attempt** — All; exact boundary phrase preserved.

## Workflow

1. **Case generation (design):** Produce mutation cases (JSON) from taxonomy + Phase-3/4 (read-only); validate against `mutation_case.schema.json`.  
2. **Harness run:** Execute mutation cases against model; record outcomes.  
3. **Ledger:** Populate `mutation_ledger.schema.json` (phase_coverage, mutation_coverage, guard_coverage, collapse_vector_flags).  
4. **Freeze gate:** Run Dataset Freeze Readiness Checklist; approve freeze only when all criteria pass.

## Invariants

- Phase definitions and dominance rules from Constitutional Manifest v1.0 are locked.  
- Boundary phrase and anchors are character-for-character from Phase-3.  
- No edits to PHASE3_BASE_EXEMPLAR_MAPPING.md or PHASE4_VARIANT_GENERATION.md from Stage-6.

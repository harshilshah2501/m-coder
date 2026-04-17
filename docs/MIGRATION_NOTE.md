# Documentation Refactor — Migration Note

**Date:** 2026-02-27

## What Moved Where

| New Location | Purpose |
|--------------|---------|
| [MASTER_SYSTEM_SPEC.md](MASTER_SYSTEM_SPEC.md) | Single entry point; TOC; Doctrine Immutability Clause |
| [GLOSSARY.md](GLOSSARY.md) | CIM term definitions and schema references |
| [NON_NEGOTIABLE_INVARIANTS.md](NON_NEGOTIABLE_INVARIANTS.md) | Fail-closed semantics (gate-down→block, append-only ledger, boundary invariance) |
| [governance/README.md](governance/README.md) | Layer-1 index |
| [COMPILATION/README.md](COMPILATION/README.md) | Layer-2 index |
| [runtime/README.md](runtime/README.md) | Layer-3 index |
| [OBSERVATION/README.md](OBSERVATION/README.md) | Layer-4 index |
| [CONTRACTS/README.md](CONTRACTS/README.md) | Contract and schema index |

## Modified Files

| File | Changes |
|------|---------|
| [guides/E2E-flow.md](guides/E2E-flow.md) | Non-canonical banner; removed phase↔stage bijection table; replaced unique contract definitions with links to canonical specs |
| [COMPILATION_DAG_AND_LINEAGE_V0_1.md](COMPILATION_DAG_AND_LINEAGE_V0_1.md) | Boundary hashing: explicit reference to boundary_hashing.v0.1.json |
| [ARCHITECTURE_4_LAYER.md](ARCHITECTURE_4_LAYER.md) | Link to MASTER_SYSTEM_SPEC |
| [archive/ROADMAP_L2_L3_L4.md](archive/ROADMAP_L2_L3_L4.md) | Archived (2026-04-18); was `docs/ROADMAP_L2_L3_L4.md`; link to MASTER_SYSTEM_SPEC |
| [guides/Dominance_Grammar.md](guides/Dominance_Grammar.md) | Non-canonical banner |
| [guides/Pre-GREG.md](guides/Pre-GREG.md) | Non-canonical banner |
| [guides/QnA.md](guides/QnA.md) | Non-canonical banner |
| [guides/ORCHESTRATOR_SERVICE_GUIDE.md](guides/ORCHESTRATOR_SERVICE_GUIDE.md) | Non-canonical banner |
| [guides/ORCHESTRATOR_GUIDE.md](guides/ORCHESTRATOR_GUIDE.md) | Non-canonical banner |
| [README.md](README.md) | Link to MASTER_SYSTEM_SPEC under 4-Layer Architecture |

## Unchanged (Doctrine Preserved)

- governance/CONSTITUTIONAL_MANIFEST_v1.0.md
- PHASE_ALIGNMENT_TABLE_V0_1.md
- RUNTIME_PLAN_AND_LEDGER_V0_1.md
- JETBRAINS_PLUGIN_FLOW_V0_1.md
- SHADOW_MODE_PROTOCOL_V0_1.md
- JSON schemas (no moves)

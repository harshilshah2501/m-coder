# Stage-6 Directory Layout Proposal

This document refers to pipeline Stage-6 (mutation harness), not Constitutional Phase-6 (REACH).

## Rationale

- **Alignment:** Phase 1–5 artifacts live under `ml/training/src/sources/Motadata/`. Stage-6 harness is part of the same Golden Exemplars pipeline (ML Compilation → Mutation Harness → Dataset Freeze → SFT).
- **Placement:** Harness is **training pipeline** (pre-SFT stress and coverage), not post-SFT evaluation. Therefore Stage-6 lives under **ml/training**, alongside Phase-3/4/5, not under a separate ml/evaluation root.
- **Production-grade:** Clear separation of schemas, config, cases, ledger, and docs; no modification of Phase-3 or Phase-4 files.

---

## Recommended Directory Tree

```
ml/training/src/sources/Motadata/
├── PHASE3_BASE_EXEMPLAR_MAPPING.md          # unchanged
├── PHASE4_VARIANT_GENERATION.md             # unchanged
├── PHASE5_VARIANT_STABILITY_REPORT.md      # unchanged
├── PHASE6_MUTATION_TAXONOMY.md             # Stage-6 design (root-level doc)
│
└── phase6/
    ├── README.md                            # Stage-6 overview and usage
    ├── STAGE6_DIRECTORY_LAYOUT.md           # this file
    ├── PHASE6_DATASET_FREEZE_CHECKLIST.md   # freeze criteria
    │
    ├── schemas/
    │   ├── mutation_case.schema.json        # mutation case schema
    │   └── mutation_ledger.schema.json      # ledger coverage schema
    │
    ├── config/
    │   └── harness_config.schema.json        # optional: harness run config
    │
    ├── cases/                               # generated mutation cases (design placeholder)
    │   └── .gitkeep
    │
    ├── ledger/                              # generated ledger outputs (design placeholder)
    │   └── .gitkeep
    │
    └── docs/
        └── DESIGN_INDEX.md                 # design index and cross-refs
```

---

## Alternative: ml/evaluation

If Stage-6 is later treated as **evaluation-only** (run after SFT to score model behavior), a parallel layout under `ml/evaluation/` could be:

```
ml/evaluation/
├── mutation_harness/
│   ├── schemas/
│   ├── config/
│   ├── cases/
│   └── ledger/
└── ...
```

**Recommendation:** Keep Stage-6 under **ml/training** for now so that:
1. Dataset freeze and SFT readiness are decided in one pipeline.
2. Harness runs **before** freeze as a gate (see Dataset Freeze Checklist).
3. Evaluation runs (post-SFT) can consume the same cases and ledger schema from a symlink or copy if needed.

---

## Directory Roles

| Path | Role |
|------|------|
| `phase6/schemas/` | JSON schemas for mutation cases and ledger; no executable logic. |
| `phase6/config/` | Harness run configuration (optional); e.g. phase balance thresholds, mutation counts per base. |
| `phase6/cases/` | Generated mutation case JSON files (MC-xxxx); populated by case generator, read-only for harness runs. |
| `phase6/ledger/` | Output ledger JSON and summary reports; populated by harness after run. |
| `phase6/docs/` | Design docs and index; no code. |

---

## Invariants

- **No edits** to `PHASE3_BASE_EXEMPLAR_MAPPING.md` or `PHASE4_VARIANT_GENERATION.md` from Stage-6.
- **Read-only** consumption of Phase-3 (base_id, phase, boundary phrase) and Phase-4 (variant_id, variant text) for case generation.
- **Production-grade:** Schemas and config are versioned; cases and ledger are generated artifacts with clear ownership.

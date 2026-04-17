# Layer-2 — ML Compilation

Base exemplars → variants → mutation → freeze → SFT pipeline. Constitutional semantics are read-only reference; this layer never redefines doctrine.

---

## Canonical Specifications

| Document | Description |
|----------|-------------|
| [COMPILATION_DAG_AND_LINEAGE_V0_1.md](../COMPILATION_DAG_AND_LINEAGE_V0_1.md) | DAG spec, lineage rules R-L1..R-L5, node types |
| [archive/ROADMAP_L2_L3_L4.md](../archive/ROADMAP_L2_L3_L4.md) | Archived milestone entry/exit/failure tables — use [`LIVE_ROADMAP_TRACKER.md`](../LIVE_ROADMAP_TRACKER.md) §4 for current status |
| [ml/training/pipeline/STAGE6_MUTATION_TAXONOMY.md](../../ml/training/pipeline/STAGE6_MUTATION_TAXONOMY.md) | Stage-6 mutation classes; doctrine-locked |
| [ARTIFACT_GOVERNANCE_LORA_CHECKPOINTS_AND_RUNTIME.md](../architecture/ARTIFACT_GOVERNANCE_LORA_CHECKPOINTS_AND_RUNTIME.md) | LoRA adapter, checkpoint, merged model, and runtime package governance (DVC/HF/Ollama) |

---

## Directory

- `ml/` — Compilation bases, variants, mutation harness (Stage-6A/6B/6C), dataset compiler, freeze artifacts, SFT

---

## Allowed / Forbidden

**Allowed:** Exemplar/variant mapping, Stage-6 mutation specs and code, dataset compiler, freeze checklists, SFT configs, generated outputs.

**Forbidden:** Redefining constitutional phase semantics; governance-locked doctrine (read-only); runtime enforcement code.

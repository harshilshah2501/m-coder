## ML Namespace

This directory contains all **model lifecycle** code and assets:

- `ml/datasets/` – dataset specifications, generation scripts, and versioned dataset artifacts.
- `ml/lineage/` – compilation DAG and provenance schemas (see [docs/COMPILATION_DAG_AND_LINEAGE_V0_1.md](../docs/COMPILATION_DAG_AND_LINEAGE_V0_1.md)). Lineage index is used by runtime plan-gate for R-L2 semantic resolution.
- `ml/training/` – training, finetuning, and evaluation pipelines that consume datasets and exemplar mirrors.
- `ml/evaluation/` – evaluation scripts and reports.
- `ml/scripts/` – shared ML-related utility and CI scripts.

The goal of the `ml/` namespace is to clearly separate **learning workflows** from:

- `governance/` (constitutional Golden Exemplars and schemas),
- `runtime/` (deployment and live services), and
- `docs/` (narrative documentation).

## Layer Boundaries

- **Allowed:** Exemplar/variant mapping, Stage-6 mutation specs and code, dataset compiler, freeze checklists, SFT configs.
- **Forbidden:** Redefining constitutional phase semantics; runtime enforcement code.

See [docs/ARCHITECTURE_4_LAYER.md](../docs/ARCHITECTURE_4_LAYER.md) for full 4-layer structure.


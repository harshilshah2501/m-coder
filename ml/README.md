## ML Namespace

This directory contains all **model lifecycle** code and assets:

- `ml/datasets/` – dataset specifications, generation scripts, and versioned dataset artifacts.
- `ml/training/` – training, finetuning, and evaluation pipelines that consume datasets and exemplar mirrors.
- `ml/evaluation/` – evaluation scripts and reports.
- `ml/scripts/` – shared ML-related utility and CI scripts.

The goal of the `ml/` namespace is to clearly separate **learning workflows** from:

- `governance/` (constitutional Golden Exemplars and schemas),
- `runtime/` (deployment and live services), and
- `docs/` (narrative documentation).


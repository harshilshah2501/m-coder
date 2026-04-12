# Artifact Governance — LoRA Adapters, Checkpoints, and Runtime Packages

**Status:** canonical-current. This document is the source of truth for LoRA adapter, checkpoint, merged model, and runtime package governance. Implementation details in §11 may evolve; this policy baseline remains in effect.

## 1. Objective

This document defines governance for model-related artifacts produced by the training/fine-tuning pipeline and consumed by downstream runtime/distribution surfaces. It establishes source-of-truth, storage rules, promotion flow, and anti-patterns so that adapters, checkpoints, merged models, and packaged runtime outputs are governed consistently rather than by ad hoc local conventions.

## 2. Scope

**In scope:**

- Base model references (e.g. Qwen/Qwen2.5-Coder-14B-Instruct).
- LoRA adapters (training outputs from SFT/DPO runs).
- Intermediate checkpoints (periodic saves during training).
- Merged models (base + adapter merged for inference).
- Evaluation outputs (scores, reports, diffs tied to a specific adapter/checkpoint).
- Training logs and metrics (run metadata, loss curves, config snapshots).
- Packaged runtime models (e.g. Ollama Modelfile, quantized inference bundles).
- Distinction between local developer/scratch outputs and governed artifact stores.

**Out of scope:**

- Dataset governance (covered by dataset/archive and path-resolution plans).
- Layer-2/Layer-3 architectural redesign.
- CI/CD or training-script implementation changes.
- Naming cleanup, branch strategy, or legacy containment.

## 3. Artifact classes

| Class | Purpose | Retention | Portability | Visibility |
|-------|---------|-----------|-------------|------------|
| **Base model reference** | Identifier and optional pointer (e.g. HF model id) for the pretrained model used as base. | Permanent as config. | Reference only; model fetched from HF/cache. | Public (HF) or internal. |
| **LoRA adapter** | Weights produced by fine-tuning (SFT/DPO) on top of base. | Governed; lineage required. | Must be storable in DVC and/or HF. | Private (DVC) or publishable (HF). |
| **Intermediate checkpoint** | Snapshot at a training step (e.g. checkpoint-1053). Used for resume and for selecting best step. | Governed for validated runs; ephemeral for scratch. | DVC or local-only. | Private/internal. |
| **Final training output** | Adapter or checkpoint chosen as the end of a training run (e.g. best loss or last step). | Governed. | DVC primary; may be promoted to HF. | Private → publishable after validation. |
| **Merged model** | Base + adapter merged into a single inference model. | Governed when tied to a released adapter. | Large; DVC or external blob; may be repackaged for Ollama. | Private or deployment-only. |
| **Evaluation artifact** | JSON/HTML/report from evaluating an adapter or merged model. | Retained for auditable lineage. | Small; Git or DVC. | Internal. |
| **Runtime package** | Artifact packaged for a runtime (e.g. Ollama Modelfile, GGUF, or container image). | Deployment lifecycle. | Produced from merged/adapter; not canonical lineage store. | Deployment target. |
| **Experimental local-only** | Scratch outputs on a developer machine, not yet validated or promoted. | Ephemeral. | Must not be treated as governed. | Local only. |

## 4. Source-of-truth policy

- **Git repo:** Source of truth for **code, config, metadata, and pointers**. It must **not** hold large model binaries (adapters, checkpoints, merged weights). It may hold: training configs, small manifest/pointer files that reference external artifact locations, evaluation report files (if small), and documentation.
- **DVC (local + remote):** Source of truth for **internal/private lineage-heavy artifacts**: LoRA adapters, checkpoints, merged models, and large evaluation outputs that need versioning and reproducibility. DVC tracks what was produced by which run and keeps a single canonical remote for private lineage.
- **Hugging Face Hub:** Source of truth for **publishable** adapters and, when desired, merged models intended for review, sharing, or release. Only validated, promotion-approved artifacts should be published. HF is not the store for scratch or unvalidated outputs.
- **Ollama (or other runtime packaging):** **Not** a source of truth for artifact lineage. It is a **runtime packaging and distribution target**. Packaged models (e.g. for Ollama) are produced from governed adapters/merged models and follow deployment conventions, not canonical artifact versioning.

**Rule:** Code/config/metadata live in Git; lineage-heavy private artifacts live in DVC remote; publishable adapters/checkpoints may be promoted to Hugging Face; runtime-consumable packages may be produced for Ollama; local scratch artifacts must never be confused with governed artifacts.

## 5. Storage rules

### Git

- **May:** Training and merge scripts, config files, small metadata/manifest files, pointer files (e.g. artifact id + storage location), small evaluation reports (e.g. JSON/MD under size limit), docs.
- **Must not:** LoRA adapter weights, full checkpoint directories, merged model binaries, large eval dumps, raw training logs (large). Use `.gitignore` and/or DVC for these.

### DVC remote

- **May:** LoRA adapters, intermediate checkpoints, merged models, large evaluation outputs, training logs/metrics that need lineage. Use DVC to track and push to a single configured remote.
- **Must not:** Treat as the place for publishable “released” artifacts only; both working and validated artifacts can live here. Must not be bypassed by committing large binaries to Git.

### Hugging Face

- **May:** Publishable adapters and (if policy allows) merged models that have passed validation and promotion criteria. Metadata (card, metrics, dataset reference) should accompany uploads.
- **Must not:** Upload unvalidated or scratch adapters as if they were canonical. Must not use HF as the only backup for internal lineage (DVC remains primary for private lineage).

### Ollama packaging layer

- **May:** Modelfiles, quantized or converted models produced **from** a governed adapter/merged model, for local or deployment use.
- **Must not:** Be used as the canonical artifact registry or source of truth for training lineage. Must not mix Ollama-only naming with DVC/HF versioning.

### Local workstation only

- **May:** Scratch training outputs, one-off merges, and experiments before they are validated or promoted. Clearly separate directory (e.g. `scratch/`, `experiments/`) from governed paths.
- **Must not:** Be treated as shared or reproducible without promoting to DVC (and optionally HF). Must not use the same paths as governed outputs so that scripts and docs do not conflate them.

## 6. Promotion flow

| Stage | Description | Gate / criteria | Metadata | Visibility |
|-------|-------------|------------------|----------|------------|
| **Local experiment output** | Training run writes adapter/checkpoint to local or scratch path. | None; ephemeral. | Run id, config path. | Local only. |
| **Governed internal artifact** | Artifact is registered in DVC and pushed to DVC remote. | DVC add + push; path under governed root. | Artifact type, run id, base model, dataset/freeze ref (see §8). | Private. |
| **Validated adapter/checkpoint** | Evaluation and/or review confirms artifact meets minimum bar. | Eval pass; optional manual review. | Eval status, eval run id, dataset ref. | Private (DVC). |
| **Publishable adapter** | Decision to share or release; upload to HF. | Explicit promotion decision; validated state. | HF card, dataset ref, base model, license. | Public or org-scoped. |
| **Runtime package** | Built from a governed (and optionally published) adapter/merged model for Ollama or other runtime. | Source artifact is governed; packaging recipe versioned. | Source adapter/merged id, Modelfile version. | Deployment. |

Transitions are one-way where appropriate: e.g. local scratch → DVC (governed); validated in DVC → HF (publishable). No automatic promotion from local scratch to HF.

## 7. Naming and versioning policy

- **Adapters / checkpoints:** Use a consistent, auditable label: e.g. `{model_family}-{variant}-{run_id}` or `v{version}_{run_id}` (e.g. `motadata-coder-v16_1-merged`, `v16_2-checkpoint-1053`). Run id or timestamp should be derivable from path or metadata so lineage is clear.
- **Merged outputs:** Name to reflect adapter and merge time (e.g. `motadata-coder-{run_id}-merged`). Avoid reusing the same name for different artifacts.
- **Eval artifacts:** Tie to adapter/run (e.g. `v16_1_test_results.json`, `evaluation_report_v16_1.html`). Include run id or date in filename when multiple evals exist.
- **Runtime packages:** Use a convention that links back to source adapter/version (e.g. Modelfile or image tag includes version). No over-engineering; enough to trace back to DVC/HF source.

## 8. Minimum metadata required

Each governed artifact (in DVC and, when published, in HF) should carry at least:

- **Artifact type:** adapter | checkpoint | merged_model | eval_artifact | runtime_package.
- **Lineage/source stage:** Training stage or pipeline stage that produced it (e.g. SFT v16_1, merge v16_2).
- **Training run identifier:** Unique run id or timestamp so logs and config can be found.
- **Dataset/freeze reference:** Dataset name or freeze id used for training (e.g. v16_1_fixed, v17_dpo).
- **Base model reference:** Exact base model id (e.g. Qwen/Qwen2.5-Coder-14B-Instruct).
- **Evaluation status:** not_evaluated | passed | failed | optional.
- **Promotion status:** scratch | governed | validated | published.
- **Storage location(s):** At least one canonical location (e.g. DVC path + remote, or HF repo + revision).

This can be implemented as a small manifest (e.g. JSON or YAML) next to the artifact or in a registry; the exact schema is a later implementation step.

## 9. Recommended operating model

- **DVC** is used for **internal/private lineage-heavy artifact management**: all LoRA adapters, checkpoints, and merged models that need reproducibility and auditability live in DVC remote; Git holds only code and pointers.
- **Hugging Face Hub** is used for **publishable/reviewable** adapters and checkpoints when the team decides to share or release; publication is after validation and with clear metadata.
- **Ollama** is used as a **downstream runtime packaging/import/distribution** target: build Modelfiles (or equivalent) from governed adapters/merged models; do not use Ollama as the canonical artifact registry.

**Why this hybrid:** No single system fits all needs. Git is poor for large binaries; DVC is good for private versioned lineage but not for public discovery; HF is good for discovery and sharing but not as the only internal backup; Ollama is for running models, not for training lineage. The split keeps lineage in DVC, sharing on HF, and deployment on Ollama without overloading one system.

## 10. Explicit anti-patterns

- **Storing large binary checkpoints or adapters directly in Git.** Use DVC (or another blob store) and keep Git for code/config/metadata/pointers only.
- **Using Ollama as the canonical artifact registry.** Ollama is a runtime packaging layer; source of truth for adapters/checkpoints is DVC and/or HF.
- **Publishing unvalidated adapters to HF as if they were canonical.** Only promote after validation and explicit promotion decision.
- **Mixing local scratch outputs with governed outputs.** Use separate paths and naming so scripts and docs do not treat scratch as reproducible.
- **Losing lineage between adapter, dataset, and evaluation result.** Every governed artifact should reference dataset/freeze and run id; eval artifacts should reference the adapter/checkpoint they evaluate.
- **Committing pointer files that point to local-only paths** without a DVC remote or shared location, so that others cannot resolve the artifact.
- **Treating “latest” or unversioned names as sufficient** for reproducibility; use run id or version in naming and metadata.

## 11. Recommended next implementation steps

1. **Artifact inventory:** List current adapter/checkpoint/merged locations (e.g. under `training/checkpoints/`, `models/`) and classify as governed vs scratch; document in a manifest or doc.
2. **DVC remote policy tightening:** Ensure a single DVC remote is configured for training outputs; add `.dvc` tracking for adapter/checkpoint/merged paths that should be governed; keep Git clean of large binaries.
3. **Metadata manifest template:** Define a minimal JSON/YAML schema for the fields in §8 and add a step in the training/merge pipeline to write it next to each governed artifact.
4. **HF publication criteria:** Document the exact criteria (e.g. eval pass, review) and steps (e.g. `huggingface_hub` upload, card template) for promoting an adapter from DVC to HF.
5. **Ollama packaging convention:** Document how to produce a Modelfile (or equivalent) from a governed adapter/merged model and how to tag images/artifacts with source version for traceability.

These steps are implementation work to be scheduled after this policy is adopted; this document does not perform them.

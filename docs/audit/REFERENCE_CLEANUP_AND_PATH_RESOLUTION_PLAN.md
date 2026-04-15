# Phase 14C — Reference Cleanup and Path Resolution Plan

**Repository:** m-coder  
**Phase:** 14C — Reference Cleanup / Path Resolution Plan (planning only)  
**Date:** 2026-03-16  
**Governing principle:** Reference truth before data movement; no execution in this phase.

**Prerequisites:** [V16_PRE_GOVERNANCE_DATA_SCRUB_PLAN.md](V16_PRE_GOVERNANCE_DATA_SCRUB_PLAN.md), [ARCHIVE_EXPORT_EXECUTION_PLAN.md](ARCHIVE_EXPORT_EXECUTION_PLAN.md), [PATH_SAFE_STRUCTURAL_RELOCATION_PLAN.md](PATH_SAFE_STRUCTURAL_RELOCATION_PLAN.md)

---

## 1. Purpose and scope

This document is **planning only** for reference cleanup and path resolution that must be in place before any archive/export execution batch touches `ml/datasets`, `ml/training/data/processed`, or `ml/evaluation/results`. It does **not** authorize or perform any of the following:

- Edit code, scripts, tests, or existing docs (except creating this plan)  
- Move, rename, export, or delete any file or directory  
- Rewrite Git history or update .gitignore  

Scope: (1) inventory and classify references to data paths that may leave active repo flow; (2) identify path assumptions that block archive/export; (3) recommend a durable data path contract and resolution strategy; (4) define the smallest safe future execution batches for reference cleanup. This is the missing bridge between the scrub/archive plans and safe export execution.

---

## 2. Executive assessment

- **Whether reference cleanup is required before export:** Yes. Archive/Export Batches 2 and 3 (datasets, processed data, evaluation results) cannot safely proceed until path assumptions are resolved. Dozens of scripts use hardcoded absolute paths (`/home/harshil/Harshil-PoCs/datasets/...`, `.../evaluation/results`, `.../training/checkpoints/...`, `.../models/...`). Those references are portability and archive/export blockers.

- **Biggest blocker:** **Absolute `/home/harshil/Harshil-PoCs/...` paths** used for datasets, evaluation results, training outputs, and models. They assume a single machine and a fixed workspace layout (siblings `datasets/`, `evaluation/`, `training/`, `models/` under a workspace root). The repo itself uses `ml/datasets`, `ml/evaluation/results` — so either the scripts target a **parent workspace** or the paths are wrong for repo-centric use. Until these are replaced by an env-based or config-based root (or repo-relative discovery), export cannot safely change where data lives.

- **Preferred future path strategy:** **Env-based data root + manifest/pointer for exported data.** Use a single environment variable (e.g. `MOTADATA_DATA_ROOT` or `MOTADATA_WORKSPACE_ROOT`) as the root for `datasets/`, `evaluation/`, `training/` (and optionally `models/`). For data that is exported out of the active repo, keep a **manifest or pointer file** in-repo (e.g. under `ml/datasets/` or `ml/training/data/`) that specifies retrieval URL or local path override. Default the env to repo-relative discovery (e.g. `Path(__file__).resolve().parents[n]` for repo root) when unset, so CI and single-repo clones work without extra setup. Prefer this over: (a) more hardcoded absolutes, (b) repo-relative-only (which breaks when data is exported), (c) config files in every script (fragmented). See §5 for full justification.

---

## 3. Reference inventory

| Reference location | Target data area | Reference style | Portability | Notes |
|--------------------|------------------|-----------------|-------------|-------|
| ml/training/src/finetuning/train_v16_1_surgical.py, validate_v16_1_fixed.py, test_v16_1_merged.py | ml/datasets (v16_1_fixed, v16_2) | Absolute path | Poor | DATASET_DIR = "/home/.../datasets/v16_*"; OUTPUT_DIR/CHECKPOINT_DIR also absolute |
| train_v16_2.py | *(removed from repo)* | — | — | — |
| ml/training/src/finetuning/merge_v16_1.py | models, checkpoints | Absolute path | Poor | ADAPTER_PATH, OUTPUT_PATH = "/home/.../models/..." |
| merge_v16_2.py | *(removed from repo)* | — | — | Use `VLLM_BASE_MODEL` + `runtime/scripts/governed_services.sh start` for serving |
| ml/training/src/finetuning/train_v17_dpo.py | ml/datasets (v17 DPO), models | BASE_DIR + relative | Poor | BASE_DIR = Path("/home/harshil/Harshil-PoCs"); then datasets/, models/ |
| ml/training/src/validation/validate_dpo_dataset.py | ml/datasets (v17) | BASE_DIR + relative | Poor | BASE_DIR = Path("/home/..."); TRAIN_FILE = BASE_DIR / "datasets/v17_dpo_pairs_train.jsonl" |
| ml/training/src/config/v17_training_config.py | ml/datasets, training artifacts | Absolute path | Poor | train_data_path, output_dir = "/home/.../datasets/...", "/home/.../training/artifacts/..." |
| ml/training/src/data/*.py (create_v16_1_splits, surgical_precision_fix, balance_v17_dataset, etc.) | ml/datasets | Absolute Path("/home/.../datasets/...") | Poor | Many INPUT_FILE, OUTPUT_FILE, DATASET_FILE, REPORT_FILE |
| ml/training/src/dataset_creation/v16_2/data_curation.py, surgical_fixer.py, final_polish.py | ml/datasets (v16_1, v16_2) | Absolute Path | Poor | INPUT_DIR, OUTPUT_DIR, LOG_DIR = Path("/home/.../datasets/..."), Path("/home/.../logs/...") |
| ml/training/scripts/fix_dataset_v16_1.py | ml/datasets (v16_1_splits, v16_1_fixed) | Absolute Path | Poor | INPUT_DIR, OUTPUT_DIR = Path("/home/.../datasets/...") |
| ml/training/train_cpt.py | ml/datasets/cpt | Absolute path (default) | Poor | dataset_path: str = "/home/.../datasets/cpt/cpt_dataset_chunked.jsonl" |
| ml/datasets/tools/chunk_cpt_dataset.py, generate_cpt_dataset.py | ml/datasets/cpt | Absolute path | Poor | input_path, output_path, output_dir = "/home/.../datasets/cpt/..." |
| ml/datasets/cpt/audit/cpt_audit.py, remove_secrets.py | ml/datasets/cpt | Absolute path | Poor | DATASET = "/home/.../datasets/cpt/..."; open("/home/.../datasets/cpt/...") |
| ml/datasets/generation/generate_dpo_pairs*.py, create_splits.py | ml/datasets (v17), evaluation/results | BASE_DIR + relative | Poor | BASE_DIR = Path("/home/..."); BASE_DIR / "datasets/...", "evaluation/results/..." |
| ml/datasets/tools/filter_dataset_by_judge.py, generate_clean_dpo_pairs*.py | ml/datasets (v17) | CWD-relative string | Weak | "datasets/v17_dpo_pairs_*.jsonl"; assumes CWD is repo root or parent |
| ml/training/src/evaluation/evaluate_v16_*.py, comprehensive_evaluation.py, etc. | evaluation/results, diffs, models | Absolute or BASE_DIR-relative | Poor | RESULTS_DIR = Path("/home/.../evaluation/results") or training/artifacts/results/...; DIFFS_DIR, LORA_ADAPTER |
| ml/evaluation/comprehensive_model_evaluation.py, kpi2_truncation_test.py, kpi3_coverage_test.py | ml/datasets (v16_1_fixed), evaluation/results | Absolute path | Poor | DATASET_DIR, OUTPUT_DIR, MERGED_MODEL_PATH = "/home/.../datasets/...", ".../evaluation/results", ".../models/..." |
| ml/evaluation/test_cpt_model.py, phase_c_completion_probe.py | evaluation/results, models | Absolute or default "./evaluation/results/phase_c" | Mixed | output_dir default repo-relative; cpt_adapter_path absolute |
| ml/training/src/finetuning/train_v14_multifile.py, train_v15_search_replace.py | processed data (v14, v15) | Bare filename / CWD-relative | Weak | DATASET_FILE = "v14_multifile_final.jsonl", "v15_search_replace.jsonl"; no path; actual data in ml/training/data/processed/ |
| ml/training/src/utils/remove_v15_duplicates.py; dataset_creation/create_v15_balanced_dataset.py, etc. | evaluation/finetuning (legacy path shape) | Repo/CWD-relative Path | Weak | Path("evaluation/finetuning/v14_multifile_final.jsonl"); path shape does not match ml/training/data/processed/ |
| ml/training/src/dataset_creation/convert_diff_to_search_replace.py | processed (v14→v15) | CLI args, default filenames | Weak | default='v14_multifile_final.jsonl', 'v15_search_replace.jsonl'; CWD-relative |
| ml/training/sft/stage7/tools/conf_drift_pipeline.py | repo root | Absolute path | Poor | lines.append("cd /home/harshil/Harshil-PoCs/m-coder") |
| ml/training/artifacts/store.py | artifact store | Absolute default | Poor | root = "/home/harshil/Harshil-PoCs/m-coder_artifacts" |
| archive/legacy_runtime_rag (tests, scripts, api, retrieval) | RAG-Datastore, workspace, logs | Absolute or getenv | Mixed | WORKSPACE_ROOT = "/home/.../Motadata/motadata"; some use os.getenv("WORKSPACE_ROOT", default) |
| docs/archive/status/TRAINING_MONITOR.md, docs/guides/ORCHESTRATOR_GUIDE.md, docs/reference/DIRECTORY_STRUCTURE_ANALYSIS.md | training/checkpoints, models, datasets | Absolute paths in examples | Weak | Instruct users to use /home/.../training/checkpoints/v16_1/, .../models/..., .../datasets/ |
| scripts/generate_v12_dataset.py, audit_legacy_datasets.py, analyze_*.py | RAG-Datastore/evaluation/finetuning | Absolute path | Poor | GOLD_FILE, OUTPUT_FILE = "/home/.../RAG-Datastore/evaluation/finetuning/..." |

---

## 4. Blocker matrix

| Cluster | Why it blocks or affects export | Severity | Recommended resolution | Notes |
|---------|---------------------------------|----------|-------------------------|-------|
| **Finetuning scripts (train_v16_*, validate_v16_*, merge_v16_*, train_v17_dpo)** | Assume datasets and model dirs at fixed absolute paths; if data is exported, scripts will fail unless path comes from env/config or manifest | **Blocking** | Introduce MOTADATA_DATA_ROOT (or similar); resolve DATASET_DIR, OUTPUT_DIR, CHECKPOINT_DIR, MODEL paths from root + relative key (e.g. root / "datasets" / "v16_1_fixed"); or read from a small config/manifest | Highest density of dataset and model paths |
| **ml/training/src/data/* and dataset_creation/v16_2/** | All Path("/home/.../datasets/...") or BASE_DIR / "datasets/..."; export would move these dirs or replace with pointer | **Blocking** | Same: data root from env; relative subpaths (e.g. "v16_1_fixed", "v17_dpo_pairs_train.jsonl"); for exported data, resolve via manifest (URL or local override) | Many files; repetitive pattern |
| **CPT (train_cpt.py, ml/datasets/cpt/audit, ml/datasets/tools)** | Hardcoded paths to cpt_dataset.jsonl, cpt_dataset_chunked.jsonl | **Blocking** | Data root + "cpt/cpt_dataset_chunked.jsonl"; or manifest entry for cpt with retrieval path | Smaller surface |
| **DPO generation (generate_dpo_pairs*.py, create_splits.py)** | BASE_DIR / "datasets/...", BASE_DIR / "evaluation/results/..."; evaluation results are input to DPO pipeline | **Blocking** | Data root for both datasets and evaluation/results; EVAL_RESULTS_FILE from root + "evaluation/results/..." or from manifest | DPO depends on evaluation JSON |
| **Evaluation scripts (evaluate_v16_*.py, comprehensive_evaluation.py, kpi2/kpi3, test_cpt_model, phase_c_completion_probe)** | RESULTS_DIR, OUTPUT_DIR, DIFFS_DIR, LORA_ADAPTER, MERGED_MODEL_PATH, DATASET_DIR all absolute or BASE_DIR-relative | **Blocking** | Same data root; results and reports under root / "evaluation/results" (or manifest when exported); model paths from root or MODEL_PATH env | Must work after evaluation results are exported |
| **Processed data (v14/v15)** | train_v14_multifile, train_v15_search_replace use bare filenames; other code uses Path("evaluation/finetuning/v14_multifile_final.jsonl"); actual files in ml/training/data/processed/ | **Blocking** | Unify path shape: single canonical location (e.g. data_root / "training/data/processed" or manifest); convert all refs to use data root + key or manifest lookup | Path shape inconsistency (evaluation/finetuning vs data/processed) |
| **conf_drift_pipeline.py, artifacts/store.py** | Hardcoded repo root and artifact store root | **Medium** | Repo root from env (e.g. MCODER_REPO_ROOT) or discovery; artifact store from env or config | Affects Stage-7 and artifact tooling only |
| **archive/legacy_runtime_rag** | WORKSPACE_ROOT, LOG_DIR, benchmark paths | **Medium** | Already partial getenv; standardize on env default; document for runbooks | Less directly tied to ml/datasets export |
| **Docs/runbooks** | Examples and instructions use /home/... paths | **Medium** | After code uses env, update docs to "set MOTADATA_DATA_ROOT (or run from repo with default)"; remove or generalize absolutes | Stale docs would mislead after export |

---

## 4a. Required planning questions (answers)

1. **Which references are the primary blockers for exporting ml/datasets?**  
   Finetuning scripts (train_v16_*, validate_v16_1_fixed, test_v16_1_merged, merge_v16_*, train_v17_dpo), ml/training/src/data/*, ml/training/src/dataset_creation/v16_2/*, ml/training/scripts/fix_dataset_v16_1.py, train_cpt.py, ml/datasets/cpt/audit and tools, ml/datasets/generation (generate_dpo_pairs*.py, create_splits), ml/datasets/tools (filter_dataset_by_judge, generate_clean_dpo_pairs*), validate_dpo_dataset.py, v17_training_config.py — all use absolute paths or BASE_DIR / "datasets/...".

2. **Which references are the primary blockers for exporting ml/training/data/processed?**  
   train_v14_multifile.py, train_v15_search_replace.py (bare filenames); remove_v15_duplicates.py, create_v15_balanced_dataset.py, convert_diff_to_search_replace.py, validate_v15_dataset.py, verify_v14_quality.py, and other refs to Path("evaluation/finetuning/v14_multifile_final.jsonl") or v15_balanced.jsonl — path shape does not match actual location ml/training/data/processed/.

3. **Which references are the primary blockers for exporting ml/evaluation/results?**  
   evaluate_v16_2_enriched.py, evaluate_v16_2_motadata_bench.py (RESULTS_DIR); comprehensive_evaluation.py, improved_evaluation_v2/v3, evaluate_v16_1_*, deep_quality_evaluation (RESULTS_DIR, DIFFS_DIR); kpi2_truncation_test.py, kpi3_coverage_test.py, comprehensive_model_evaluation.py (OUTPUT_DIR); generate_dpo_pairs_enhanced.py, generate_dpo_pairs_final.py (EVAL_RESULTS_FILE); phase_c_completion_probe.py (output_dir).

4. **Which areas already use acceptable path resolution?**  
   test_cpt_model.py uses default `"./evaluation/results/phase_c"` (repo-relative, weak). `archive/legacy_runtime_rag/` uses os.getenv("WORKSPACE_ROOT", default) in some places. No dataset or evaluation-result paths currently use a durable env-based contract.

5. **What should the future path contract be for large exported data?**  
   A single env-based data root (e.g. MOTADATA_DATA_ROOT) for datasets/, evaluation/, training/; relative keys under that root; optional manifest mapping keys to retrieval URL or local path override when data is exported.

6. **Should the future contract prefer env vars, config files, manifest/pointer, or repo-relative defaults?**  
   Prefer **env vars** for the root (one variable, easy CI and local override). Prefer **manifest/pointer** for exported data (key → URL or path). Use **repo-relative default** when env is unset (discover repo root so existing clones work without setup). Config files in every script are not preferred (fragmented).

7. **What is the smallest safe first execution batch for reference cleanup?**  
   Reference Cleanup Batch 1 — introduce data root (env + repo default) and convert finetuning + data/ + dataset_creation/v16_2 paths for datasets and model/checkpoint dirs; no processed-data or evaluation-results changes in Batch 1.

---

## 5. Path strategy decision

**Chosen strategy: env-based data root + manifest/pointer for exported data.**

- **Hardcoded absolute paths** — **Reject** for any new or refactored path. They block portability and export; they assume one machine and one layout.

- **Repo-relative paths only** — **Insufficient** for archive/export. Once data is in LFS or an external store, “repo-relative” no longer points to the payload; we need a way to resolve “v16_1_fixed” to a URL or an override path. Repo-relative is acceptable as the **default** when data root is unset (e.g. default MOTADATA_DATA_ROOT to repo root so `ml/datasets` is used).

- **Environment-variable–based resolution** — **Strong candidate.** A single root (e.g. `MOTADATA_DATA_ROOT`) for `datasets/`, `evaluation/`, `training/` (and optionally `models/`) keeps changes localized: scripts use `root / "datasets" / "v16_1_fixed"` instead of `/home/.../datasets/v16_1_fixed`. CI can set the env to repo root; export workflows can set it to a mount or sync dir; no per-script config files.

- **Manifest/pointer-based resolution** — **Strong candidate for exported data.** For assets that have left the active tree (e.g. after Archive/Export Batch 2), a manifest (e.g. `ml/datasets/DATA_MANIFEST.json` or `ml/training/data/processed/MANIFEST.json`) can map keys (e.g. "v16_1_fixed", "v15_search_replace") to a retrieval URL or a local path override. Scripts that support “exported” mode can check the manifest first, then fall back to data root. This preserves reproducibility without keeping large blobs in the repo.

- **Hybrid (recommended)** — **Default:** `MOTADATA_DATA_ROOT` (or `MOTADATA_WORKSPACE_ROOT`) env; if unset, default to repo root (discovered from `__file__` or `git rev-parse --show-toplevel`). For any key (dataset dir or file) that is listed in a manifest as exported, resolve via manifest (URL or override path). This gives: (1) one contract (data root + relative keys, with optional manifest), (2) no hardcoded `/home/...`, (3) export-friendly (point manifest at external store or LFS), (4) backward-friendly (existing clones can set env to current layout or rely on default).

**Concrete contract:**

- **Data root:** `MOTADATA_DATA_ROOT` (or `MOTADATA_WORKSPACE_ROOT`). When set, `datasets/`, `evaluation/`, `training/` (and optionally `models/`) are under this root. When unset, default to repo root (so `ml/datasets`, `ml/evaluation`, etc. are used).
- **Relative keys:** Scripts use logical keys (e.g. `datasets/v16_1_fixed`, `evaluation/results`, `training/data/processed/v15_search_replace_20251231.jsonl`), not full absolutes.
- **Manifest (optional):** For exported data, a manifest file in-repo maps key → retrieval URL or local path. Scripts that need exported payloads resolve via manifest when present.
- **Models:** Same root or a separate `MOTADATA_MODELS_ROOT` if models live outside the repo; document in runbooks.

---

## 6. Area-by-area assessment

### ml/datasets

- **Acceptable:** Repo-relative references from code that runs with CWD = repo root and uses `ml/datasets/...` or `datasets/...` (e.g. some tools using "datasets/v17_dpo_pairs_clean.jsonl") are at least runnable in-repo; they are **weak** because they assume CWD and do not support export.
- **Blocking:** All absolute `/home/.../datasets/...` and BASE_DIR / "datasets/..." usages block export. They must be converted to data-root + relative key (or manifest) before Batch 2.
- **Must change later:** Every script in the reference inventory that targets ml/datasets (finetuning, data/, dataset_creation/, cpt, generation/, tools/) should be updated to resolve paths via MOTADATA_DATA_ROOT + relative key (and manifest when applicable). No change to dataset contents; only path resolution.

### ml/training/data/processed

- **Acceptable:** None currently; path shapes are split between "evaluation/finetuning/..." and "v14_multifile_final.jsonl" (CWD-relative) and actual files in `ml/training/data/processed/`.
- **Blocking:** (1) Scripts that assume evaluation/finetuning/ or bare filenames must be aligned to a single canonical location (e.g. data_root / "training/data/processed" or a manifest key). (2) Any script that still uses absolute paths to processed files must switch to data root + key.
- **Must change later:** Unify on one path contract (e.g. `training/data/processed/v15_search_replace_20251231.jsonl` under data root); update train_v14_multifile, train_v15_search_replace, convert_diff_to_search_replace, create_v15_balanced_dataset, remove_v15_duplicates, verify_v14_quality, and any other refs to v14/v15 processed data to use that contract.

### ml/evaluation/results

- **Acceptable:** test_cpt_model default `"./evaluation/results/phase_c"` is repo-relative and weak but runnable when CWD is repo root.
- **Blocking:** All RESULTS_DIR, OUTPUT_DIR, EVAL_RESULTS_FILE pointing to `/home/.../evaluation/results` or BASE_DIR / "evaluation/results" block export. DPO generation and evaluation scripts must resolve via data root (and manifest when results are exported).
- **Must change later:** All evaluate_*.py, comprehensive_evaluation.py, kpi2/kpi3, generate_dpo_pairs*.py, phase_c_completion_probe to use data root + "evaluation/results/..." (or manifest). Docs that point to specific result files should reference the contract (env + key or manifest).

### docs/runbooks

- **Acceptable:** Generic references (e.g. “see datasets/”) are fine.
- **Blocking:** Any instruction that tells users to set or use a literal `/home/...` path becomes wrong after export or on another machine.
- **Must change later:** Replace absolute path examples with “set MOTADATA_DATA_ROOT (or use default from repo)” and document the contract; update TRAINING_MONITOR, ORCHESTRATOR_GUIDE, DIRECTORY_STRUCTURE_ANALYSIS, and similar docs that contain hardcoded paths.

---

## 7. Recommended future execution batches

### Reference Cleanup Batch 1 — Absolute path inventory and conversion targets

- **Name:** Reference Cleanup Batch 1 — Absolute path inventory and conversion  
- **Purpose:** Introduce the data root contract (env + default) and convert the highest-impact absolute paths so that dataset and evaluation paths are resolved from one root.  
- **Scope:** (1) Add a small shared helper or config module that resolves MOTADATA_DATA_ROOT (env or repo-root default). (2) Convert finetuning scripts (train_v16_1_surgical, validate_v16_1_fixed, test_v16_1_merged, merge_v16_1, train_v17_dpo) to use data root + relative keys for DATASET_DIR, OUTPUT_DIR, CHECKPOINT_DIR, MODEL paths. *(train_v16_2.py, merge_v16_2.py removed from repo.)* (3) Convert ml/training/src/data/* and dataset_creation/v16_2/* to use data root for all dataset paths. Do not change behavior of scripts beyond path resolution.  
- **Exclusions:** No export, no deletion, no change to processed-data path shape in this batch; no docs/runbook edits in Batch 1 if scope is large.  
- **Preconditions:** This plan approved; env name (e.g. MOTADATA_DATA_ROOT) and default (repo root) agreed; list of files to touch from this plan.  
- **Success criteria:** All touched scripts resolve dataset and model paths via data root; no remaining `/home/harshil/Harshil-PoCs/` literals in those files; existing tests or a smoke run (e.g. one training/eval step) still succeed with data root unset (repo default) or set to current layout.

### Reference Cleanup Batch 2 — Dataset and CPT resolution contract

- **Name:** Reference Cleanup Batch 2 — Dataset and CPT resolution  
- **Purpose:** Extend data root (or manifest) to all remaining dataset references: CPT (train_cpt, cpt/audit, tools), DPO generation (generate_dpo_pairs*.py, create_splits), ml/datasets/tools (filter_dataset_by_judge, generate_clean_dpo_pairs*), validation (validate_dpo_dataset), config (v17_training_config).  
- **Scope:** Same contract (data root + relative key); add manifest support only if Batch 2 is intended to run after an export (otherwise defer manifest to a later batch).  
- **Exclusions:** No change to evaluation/results path resolution (Batch 3); no processed-data path unification (can be same or separate batch).  
- **Preconditions:** Batch 1 done; data root used consistently for finetuning and data/ scripts.  
- **Success criteria:** No absolute dataset paths in listed files; CPT and DPO paths resolved via data root; tests or smoke run pass.

### Reference Cleanup Batch 3 — Evaluation-result path resolution

- **Name:** Reference Cleanup Batch 3 — Evaluation results path resolution  
- **Purpose:** Resolve all evaluation/results and evaluation/diffs paths via data root (and optional manifest) so that Archive/Export Batch 3 can move results without breaking DPO or evaluation scripts.  
- **Scope:** All evaluate_v16_*.py, comprehensive_evaluation.py, deep_quality_evaluation.py, improved_evaluation_v2/v3, kpi2_truncation_test, kpi3_coverage_test, test_cpt_model, phase_c_completion_probe; generate_dpo_pairs_enhanced, generate_dpo_pairs_final (EVAL_RESULTS_FILE).  
- **Exclusions:** No dataset path changes (already in Batch 1–2); no processed-data path unification.  
- **Preconditions:** Batch 1 (and ideally Batch 2) done so that data root is standard.  
- **Success criteria:** RESULTS_DIR, OUTPUT_DIR, EVAL_RESULTS_FILE, DIFFS_DIR resolved from data root (or manifest); no absolute evaluation paths; DPO pipeline and eval scripts run with data root unset or set.

### Reference Cleanup Batch 4 — Processed data path unification

- **Name:** Reference Cleanup Batch 4 — Processed data path unification  
- **Purpose:** Unify v14/v15 processed data path shape so that all references point to one canonical location under data root (e.g. training/data/processed/) and optionally to a manifest when exported.  
- **Scope:** train_v14_multifile, train_v15_search_replace, convert_diff_to_search_replace, create_v15_balanced_dataset, remove_v15_duplicates, validate_v15_dataset, verify_v14_quality, extract_additional_v15_examples, generate_missing_v15_examples; any other refs to evaluation/finetuning/ or bare v14/v15 filenames.  
- **Exclusions:** No change to dataset or evaluation/results resolution.  
- **Preconditions:** Data root contract in place (Batch 1).  
- **Success criteria:** Single canonical path shape for processed data (e.g. data_root / "training/data/processed" / filename); no evaluation/finetuning/ or ambiguous bare filenames; scripts run with data root default or set.

### Optional — Docs/runbook path cleanup batch

- **Name:** Docs/runbook path cleanup  
- **Purpose:** Replace absolute path examples and instructions with env-based contract and generic guidance.  
- **Scope:** docs/archive/status/TRAINING_MONITOR.md, docs/guides/ORCHESTRATOR_GUIDE.md, docs/reference/DIRECTORY_STRUCTURE_ANALYSIS.md, and any other doc that contains `/home/...` or machine-specific paths for datasets, models, or evaluation.  
- **Exclusions:** No code changes.  
- **Preconditions:** Code path contract (Batch 1–3) agreed and documented.  
- **Success criteria:** No misleading absolute paths; docs describe MOTADATA_DATA_ROOT (or chosen env) and default behavior.

---

## 8. Validation expectations

- **Validation approach:** (1) **Static:** Grep for `/home/harshil`, `Harshil-PoCs/datasets`, `Harshil-PoCs/evaluation`, `Harshil-PoCs/training`, `Harshil-PoCs/models` in code and scripts; after cleanup batches, only intentional exceptions (e.g. commented examples) or non-data paths (e.g. RAG workspace) should remain. (2) **Runtime:** With MOTADATA_DATA_ROOT unset (repo default), run a minimal training step (e.g. one script that reads from ml/datasets) and a minimal evaluation step that reads from ml/evaluation/results; both must succeed. (3) **Override:** Set MOTADATA_DATA_ROOT to a copy of data (or a symlink) and re-run; must still succeed.  
- **Export safety condition:** Archive/Export Batch 2 (datasets) and Batch 3 (evaluation results) are safe to execute only after: (a) the corresponding reference cleanup batches are done, and (b) the validation above passes (no blocking absolute data paths; runtime tests pass with default and override). Processed-data export (part of Batch 2) additionally requires Batch 4 (path unification) to be done so that all v14/v15 refs use the same canonical location.

---

## 9. Immediate conclusions

- **What must be fixed first:** **Reference Cleanup Batch 1** — introduce the data root contract and convert finetuning and data/dataset_creation paths (ml/datasets and related) so that no script assumes a hardcoded `/home/.../datasets` or `/home/.../training` or `/home/.../models`. This unblocks planning and execution of Archive/Export Batch 2 (datasets) once validation passes.

- **What is safe to leave for later:** (1) Manifest/pointer resolution for **exported** data can be added in a batch after data root is in place (or in parallel with Batch 2 if export is imminent). (2) Docs/runbook path cleanup can follow code cleanup. (3) `archive/legacy_runtime_rag/` and scripts under scripts/ that reference RAG-Datastore or legacy paths are lower priority for dataset/export blocking but should eventually use env or config.

- **When archive/export Batch 2 becomes safe:** After Reference Cleanup Batches 1 and 2 are complete and validation passes (no blocking absolute dataset paths; smoke run with data root default and override succeeds). Optionally, add manifest support so that after export, scripts can resolve dataset keys from a manifest (URL or local path). Batch 3 (evaluation results) becomes safe after Reference Cleanup Batch 3 and the same validation.

---

## 10. Non-goals

This phase did **not**:

- Edit any code, scripts, tests, or existing docs (except creating this plan).  
- Move, rename, export, or delete any file or directory.  
- Rewrite Git history or update .gitignore.  
- Implement the data root helper or manifest format.  
- Resolve the exact env variable name (MOTADATA_DATA_ROOT vs MOTADATA_WORKSPACE_ROOT) as mandatory; the plan recommends one and leaves final naming to the execution batch.  
- Propose broad refactors unrelated to path resolution (e.g. changing training logic or dataset formats).

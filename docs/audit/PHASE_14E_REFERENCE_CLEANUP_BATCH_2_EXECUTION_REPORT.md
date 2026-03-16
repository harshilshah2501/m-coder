# Phase 14E — Reference Cleanup Batch 2 Execution Report

**Repository:** m-coder  
**Phase:** 14E — Reference Cleanup Batch 2 (execution)  
**Date:** 2026-03-16  
**Governing plans:** [REFERENCE_CLEANUP_AND_PATH_RESOLUTION_PLAN.md](REFERENCE_CLEANUP_AND_PATH_RESOLUTION_PLAN.md), [PHASE_14D_REFERENCE_CLEANUP_BATCH_1_EXECUTION_REPORT.md](PHASE_14D_REFERENCE_CLEANUP_BATCH_1_EXECUTION_REPORT.md)

---

## 1. Acceptance baseline carried forward

- **Phase 14D is accepted** as structurally correct, intentionally incomplete, and sufficient to unblock the next absolute-path remediation cluster.
- **Phase 14E did not reopen or redesign Phase 14D.** No changes were made to `ml/training/src/config/data_root.py` contract semantics, env var name, or fallback behavior. All Batch 2 conversions reuse the existing `get_data_root()` and the same path shape (`root / "ml/datasets/..."`, `root / "training/..."`).
- **Caution recorded:** `MOTADATA_DATA_ROOT` currently behaves as a **workspace-root-shaped contract** rather than a pure external data-root contract. Resolved paths assume repo-like children (`ml/datasets/...`, `models/...`, `training/...`). This was not changed in Phase 14E; it remains for a later batch to address deliberately if a true externalized data-root or multi-root contract is desired.

---

## 2. Scope executed

### Exact files changed

- `ml/training/src/data/create_v16_1_splits.py`
- `ml/training/src/data/surgical_precision_fix.py`
- `ml/training/src/data/final_dataset_validation.py`
- `ml/training/src/data/balance_v17_dataset.py`
- `ml/training/src/data/deduplicate_v16_1.py`
- `ml/training/src/data/validate_v17_dataset.py`
- `ml/training/src/data/verify_category_consistency.py`
- `ml/training/src/data/create_v16_upgrade.py`
- `ml/training/src/data/validate_v16_1_surgical.py`
- `ml/training/src/data/fix_motadata_categories.py`
- `ml/training/src/data/deduplicate_dataset.py`
- `ml/training/src/data/prepare_v17_dataset.py`
- `ml/training/src/data/extract_motadata_examples.py` (OUTPUT_DIR only; MOTADATA_ROOT left as-is)
- `ml/training/src/data/extract_real_examples.py` (OUTPUT_DIR only; MOTADATA_ROOT left as-is)
- `ml/training/src/dataset_creation/v16_2/data_curation.py`
- `ml/training/src/dataset_creation/v16_2/surgical_fixer.py`
- `ml/training/src/dataset_creation/v16_2/final_polish.py`
- `ml/training/scripts/fix_dataset_v16_1.py`
- `ml/training/train_cpt.py`

### Exact files intentionally not changed

- **Evaluation scripts** (evaluate_v16_*.py, comprehensive_evaluation.py, kpi2/kpi3, etc.) — Batch 3.
- **Processed-data unification** — No v14/v15 path-shape or evaluation/finetuning refs touched.
- **dataset_creation/** other than v16_2 (split_train_test.py, create_v15_*.py, add_copyright_headers.py, etc.) — workspace_root / Finetuning paths deferred; ambiguous or mixed-purpose.
- **ml/datasets/tools, ml/datasets/generation, ml/datasets/cpt/audit** — Out of Batch 2 scope.
- **data_root.py** — Reused as-is; no extension.

### Why the chosen files were the Batch-2 target cluster

Per Phase 14C and the Phase 14E spec, Batch 2 is the next cluster after finetuning/merge/validation: (1) **data/** scripts that resolve dataset/model/processed-input roots, (2) **dataset_creation/v16_2** with high-impact absolute paths, (3) **fix_dataset_v16_1.py** and **train_cpt.py** explicitly listed. These files directly point to dataset roots or training outputs and materially block portability and future archive/export preparation.

---

## 3. Batch-2 absolute path conversions completed

| File | Old absolute path pattern | New resolution method | Path type |
|------|----------------------------|------------------------|-----------|
| create_v16_1_splits.py | `/home/.../datasets/v16_1_surgical.jsonl`, `.../v16_1_splits` | _ROOT / "ml/datasets/..." | dataset |
| surgical_precision_fix.py | `.../datasets/v16_1_final.jsonl`, `.../v16_1_surgical.jsonl` | _ROOT / "ml/datasets/..." | dataset |
| final_dataset_validation.py | `.../datasets/v16_1_surgical.jsonl`, `.../v16_1_final_validation_report.json` | _ROOT / "ml/datasets/..." | dataset |
| balance_v17_dataset.py | `.../datasets/v17_motadata_examples_dedup.jsonl`, `.../v17_training_data.jsonl` | _ROOT / "ml/datasets/..." | dataset |
| deduplicate_v16_1.py | `.../datasets/v16_1_upgraded.jsonl`, `.../v16_1_upgraded_dedup.jsonl` | _ROOT / "ml/datasets/..." | dataset |
| validate_v17_dataset.py | `.../datasets/v17_motadata_examples_dedup.jsonl`, `.../v17_consistency_report_final.json` | _ROOT / "ml/datasets/..." | dataset |
| verify_category_consistency.py | `.../datasets/v16_1_upgraded_dedup.jsonl`, `.../v16_1_category_consistency_report.json` | _ROOT / "ml/datasets/..." | dataset |
| create_v16_upgrade.py | `.../datasets/v15_gold.jsonl`, v17_motadata, v16_1_upgraded | _ROOT / "ml/datasets/..." | dataset |
| validate_v16_1_surgical.py | `.../datasets/v16_1_upgraded.jsonl`, `.../v16_1_validation_report.json` | _ROOT / "ml/datasets/..." | dataset |
| fix_motadata_categories.py | `.../datasets/v16_1_upgraded_dedup.jsonl`, `.../v16_1_final.jsonl` | _ROOT / "ml/datasets/..." | dataset |
| deduplicate_dataset.py | `.../datasets/v17_motadata_examples.jsonl`, `.../v17_motadata_examples_dedup.jsonl` | _ROOT / "ml/datasets/..." | dataset |
| prepare_v17_dataset.py | `.../datasets` | _ROOT / "ml/datasets" | dataset |
| extract_motadata_examples.py | `.../datasets` (OUTPUT_DIR) | _ROOT / "ml/datasets" | dataset |
| extract_real_examples.py | `.../datasets` (OUTPUT_DIR) | _ROOT / "ml/datasets" | dataset |
| v16_2/data_curation.py | `.../datasets/v16_1_fixed`, v16_2, `.../logs/data_curation` | _ROOT / "ml/datasets/...", _ROOT / "training/logs/data_curation" | dataset, training output |
| v16_2/surgical_fixer.py | `.../datasets/v16_2`, v16_2_surgical, `.../logs/data_curation` | same | dataset, training output |
| v16_2/final_polish.py | same | same | dataset, training output |
| fix_dataset_v16_1.py | `.../datasets/v16_1_splits`, `.../v16_1_fixed` | _ROOT / "ml/datasets/..." | dataset |
| train_cpt.py | `.../datasets/cpt/cpt_dataset_chunked.jsonl` | _DATA_ROOT / "ml/datasets/cpt/..." in __post_init__ | dataset |

---

## 4. Minimal contract reuse or extension

- **data_root.py was reused as-is.** No code changes were made to `ml/training/src/config/data_root.py`. No new env vars, no manifest logic, no compatibility layers.
- **No extension.** All Batch 2 call sites use the existing `get_data_root()` and build paths with the same conventions as Phase 14D (`ml/datasets`, `training/...`). Scripts under `ml/training/scripts/` and `ml/training/train_cpt.py` add repo to `sys.path` and call `get_data_root()` via `from ml.training.src.config.data_root import get_data_root` so that the same contract is used without modifying data_root.py.
- **Contract semantics were not redesigned.** Fallback and override behavior are unchanged.

---

## 5. Validation performed

- **Env override validation:** Existing test_data_root.py::test_get_data_root_env_override was run; **passed.** Batch 2 scripts use the same get_data_root(), so MOTADATA_DATA_ROOT override applies to all touched logic.
- **Fallback validation:** test_get_data_root_fallback_is_repo_root and test_repo_root_has_ml_and_docs were run; **passed.** Touched Batch 2 entrypoints resolve dataset/training paths under repo when env is unset.
- **Touched-entrypoint validation:** Grep for `/home/harshil` and `Harshil-PoCs` in all Batch 2–edited files. **No matches** except the intentional `MOTADATA_ROOT` in extract_motadata_examples.py and extract_real_examples.py (external codebase path; left unchanged and reported).
- **Test results:** `python3 -m pytest ml/training/src/config/test_data_root.py -v` — **4 passed.** No new tests were added; existing contract tests suffice.

---

## 6. Deferred items left untouched

- **Evaluation-result cleanup** — No evaluation scripts or RESULTS_DIR/EVAL_RESULTS_FILE paths changed.
- **Processed-data global unification** — No v14/v15 or evaluation/finetuning path-shape changes.
- **Export logic, manifest/pointer logic, archive/export execution** — Not implemented or run.
- **Broad repo-wide absolute-path cleanup** — dataset_creation (other than v16_2), ml/datasets/tools, ml/datasets/generation, ml/datasets/cpt/audit, split_train_test.py, create_v15_*.py, add_copyright_headers.py, and all evaluation scripts were not changed.
- **Ambiguous / low-confidence references:** MOTADATA_ROOT in extract_motadata_examples.py and extract_real_examples.py (external codebase path) left unchanged. split_train_test.py and create_v15_* workspace_root / Finetuning paths left unchanged.

---

## 7. Risks / follow-up notes

- **Remaining hardcoded paths (observed, not changed):** (1) MOTADATA_ROOT in extract_motadata_examples.py and extract_real_examples.py (`/home/harshil/TestMotadataProject/Motadata/motadata`) — external codebase root, not dataset root; left as-is. (2) split_train_test.py and several create_v15_* scripts use `workspace_root = Path('/home/harshil/Harshil-PoCs')` or Finetuning paths; deferred as mixed-purpose or layout-specific.
- **Unresolved blockers for Batch 3 / export preparation:** Evaluation scripts (evaluate_v16_*.py, comprehensive_evaluation.py, kpi2/kpi3, generate_dpo_pairs*.py, etc.) still use absolute or BASE_DIR-relative paths for evaluation/results and datasets. ml/datasets/tools and generation scripts still have absolute or CWD-relative dataset paths. These must be converted in a later batch before archive/export Batch 2/3.
- **Workspace-root-shaped contract:** The current MOTADATA_DATA_ROOT contract remains workspace-root-shaped (assumes repo-like children). Rationalization for a pure external data-root or multi-root contract is left for a later, deliberate change.

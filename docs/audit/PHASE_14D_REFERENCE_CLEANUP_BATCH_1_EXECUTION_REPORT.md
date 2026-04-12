# Phase 14D — Reference Cleanup Batch 1 Execution Report

**Repository:** m-coder  
**Phase:** 14D — Reference Cleanup Batch 1 (execution)  
**Date:** 2026-03-16  
**Governing plans:** [REFERENCE_CLEANUP_AND_PATH_RESOLUTION_PLAN.md](REFERENCE_CLEANUP_AND_PATH_RESOLUTION_PLAN.md), [ARCHIVE_EXPORT_EXECUTION_PLAN.md](ARCHIVE_EXPORT_EXECUTION_PLAN.md)

---

## 1. Scope executed

### Exact files changed

- `ml/training/src/config/data_root.py` — **new**: minimal data-root contract (get_data_root, get_repo_root).
- `ml/training/src/config/test_data_root.py` — **new**: minimal tests for env override and repo fallback.
- `ml/training/src/config/v17_training_config.py` — output_dir and train_data_path resolved from get_data_root().
- `ml/training/src/finetuning/train_v16_1_surgical.py` — DATASET_DIR, OUTPUT_DIR, CHECKPOINT_DIR converted.
- `ml/training/src/finetuning/train_v16_2.py` — **removed** from repo (obsolete).
- `ml/training/src/finetuning/validate_v16_1_fixed.py` — DATASET_DIR, OUTPUT_DIR converted.
- `ml/training/src/finetuning/test_v16_1_merged.py` — MERGED_MODEL_PATH, DATASET_DIR, results_file path converted.
- `ml/training/src/finetuning/merge_v16_1.py` — ADAPTER_PATH, OUTPUT_PATH converted.
- `ml/training/src/finetuning/merge_v16_2.py` — **removed** from repo (obsolete); serving uses `runtime/config/demo_stack.env` + `runtime/scripts/governed_services.sh`.
- `ml/training/src/finetuning/train_v17_dpo.py` — BASE_DIR replaced by get_data_root(); SFT_MODEL_PATH, DPO_DATASET_*, OUTPUT_DIR, LOGS_DIR converted.

### Exact files intentionally not changed

- All evaluation scripts (evaluate_v16_*.py, comprehensive_evaluation.py, kpi2/kpi3, etc.) — deferred to Batch 3.
- All ml/training/src/data/*.py — deferred to Batch 2.
- All ml/training/src/dataset_creation/v16_2/*.py — deferred to Batch 2.
- ml/training/scripts/fix_dataset_v16_1.py — deferred to Batch 2.
- ml/training/train_cpt.py — deferred to Batch 2.
- ml/datasets/** (tools, generation, cpt/audit) — out of Batch 1 scope.
- Docs, runbooks, CI, governance — not touched.

### Why the chosen files were the Batch-1 target cluster

Per Phase 14C, the first target cluster was (1) finetuning/training entrypoints, (2) then data/ and dataset_creation/ only where highest-impact. Batch 1 was limited to finetuning entrypoints and the single config module that carries dataset/training paths (v17_training_config). This gives the smallest safe contract and the highest-impact absolute path removal without touching data/ or dataset_creation/ scripts.

---

## 2. Data-root contract introduced

- **Where implemented:** `ml/training/src/config/data_root.py`.
- **Env var used:** `MOTADATA_DATA_ROOT`. When set, all data root paths resolve under this directory.
- **Repo-relative fallback behavior:** When `MOTADATA_DATA_ROOT` is unset, `get_data_root()` returns `get_repo_root()`, which is discovered by walking up from `__file__` until a directory containing both `ml/` and `docs/` is found (with a numeric fallback). Paths are then built as `root / "ml/datasets/..."`, `root / "models/..."`, `root / "training/..."` so that with env unset, repo-local layout is used (e.g. repo/ml/datasets, repo/models, repo/training).
- **Why this implementation is the smallest safe contract:** One module, two functions, no config files or framework. Call sites use `get_data_root()` and build Paths with explicit relative segments; no manifest or export logic. Override is a single env var; fallback is deterministic from repo layout.

---

## 3. Absolute path conversions completed

| File | Old absolute path pattern | New resolution method | Path type |
|------|----------------------------|------------------------|-----------|
| train_v16_1_surgical.py | `/home/harshil/Harshil-PoCs/datasets/v16_1_fixed`, `.../models/v16_1_finetuned`, `.../training/checkpoints/v16_1` | `_ROOT = get_data_root(); _ROOT / "ml/datasets/v16_1_fixed"`, `_ROOT / "models/v16_1_finetuned"`, `_ROOT / "training/checkpoints/v16_1"` | dataset, model, checkpoint |
| train_v16_2.py | *(file removed)* | Superseded / out of repo | — |
| validate_v16_1_fixed.py | `.../datasets/v16_1_fixed`, `.../training/checkpoints/v16_1_validation` | Same pattern | dataset, training output |
| test_v16_1_merged.py | `.../models/v16_1_merged`, `.../datasets/v16_1_fixed`, `.../training/results/v16_1_test_results.json` | Same pattern; results_file = _ROOT / "training/results/..." | model, dataset, training output |
| merge_v16_1.py | `.../models/v16_1_finetuned`, `.../models/v16_1_merged` | _ROOT / "models/v16_1_finetuned", _ROOT / "models/v16_1_merged" | model |
| merge_v16_2.py | *(file removed)* | Superseded by `runtime/config/demo_stack.env` (`VLLM_BASE_MODEL`) + governed scripts | — |
| train_v17_dpo.py | BASE_DIR = Path("/home/..."); BASE_DIR / "models/...", "datasets/...", "training/logs/..." | _ROOT = get_data_root(); _ROOT / "models/...", _ROOT / "ml/datasets/...", _ROOT / "training/logs/..." | model, dataset, training output |
| v17_training_config.py | output_dir and train_data_path defaulted to `/home/.../training/artifacts/...`, `.../datasets/v17_training_data.jsonl` | In __post_init__, get_data_root() and _root / "training/artifacts/...", _root / "ml/datasets/v17_training_data.jsonl" when None | training output, dataset |

---

## 4. Validation performed

- **Env override validation:** test_data_root.py::test_get_data_root_env_override sets MOTADATA_DATA_ROOT to /tmp/motadata_data_test and asserts get_data_root().resolve() equals that path. **Passed.**
- **Fallback validation:** test_get_data_root_fallback_is_repo_root asserts that when env is unset, get_data_root() equals get_repo_root(). test_repo_root_has_ml_and_docs asserts repo root has ml/ and docs/. **Passed.**
- **Touched-entrypoint validation:** Grep of all converted files for `/home/harshil` and `Harshil-PoCs` shows **no matches**; paths are built from get_data_root() only.
- **Test results:** `python3 -m pytest ml/training/src/config/test_data_root.py -v` — **4 passed.**

---

## 5. Deferred items left untouched

- **Evaluation-result cleanup** — No evaluation scripts or RESULTS_DIR/EVAL_RESULTS_FILE paths were changed.
- **Processed-data unification** — No v14/v15 or evaluation/finetuning path shape changes; no ml/training/data/processed references touched.
- **Export logic** — No export, LFS, or external store logic.
- **Manifest/pointer logic** — Not implemented.
- **Archive/export execution** — No archive or export batches run or prepared.
- **Broad absolute-path cleanup outside Batch 1** — data/, dataset_creation/, ml/datasets tools, fix_dataset_v16_1.py, train_cpt.py, and all evaluation scripts were intentionally not changed.

---

## 6. Risks / follow-up notes

- **Path layout when MOTADATA_DATA_ROOT is set:** Current contract uses subpaths `ml/datasets`, `models`, `training`. If users set MOTADATA_DATA_ROOT to a workspace that has top-level `datasets/` (no `ml`), paths would not match. Document that when using the env override, the workspace should mirror repo layout (e.g. have `ml/datasets`, `models`, `training`) or Batch 2 can introduce a small compatibility layer.
- **Running scripts as plain scripts:** Scripts use `from ..config.data_root import get_data_root`. They are intended to be run as modules (e.g. `python3 -m ml.training.src.finetuning.train_v16_1_surgical`) from repo root so that the package structure is correct. Running as `python3 ml/training/src/finetuning/train_v16_1_surgical.py` from repo root may fail on the relative import unless PYTHONPATH or package install is set.
- **Remaining blockers for Batch 2/3:** data/, dataset_creation/v16_2, fix_dataset_v16_1, train_cpt, and all evaluation scripts still contain hardcoded absolute paths or BASE_DIR; they must be converted in later batches before archive/export Batch 2 or 3.

# Phase 15E — Retained-Lineage Containment Execution Report

## 1. Objective

This pass executes minimal containment for retained v15 dataset-construction lineage only. It does **not** perform broad restructuring, archive execution, or naming normalization. ACTIVE surfaces were preserved.

## 2. Accepted baseline

- Phase 15B established ACTIVE SURFACE, RETAINED_LINEAGE SURFACE, and ARCHIVAL/HISTORICAL SURFACE; containment of retained v15 dataset-construction utilities was deferred due to import and path coupling.
- Phase 15C removed the primary import blocker in `remove_v15_duplicates.py` (package-qualified import from `create_v15_balanced_dataset`).
- Phase 15D neutralized CWD-relative path assumptions in `remove_v15_duplicates.py` (repo-root–relative resolution) and noted that repo-root depth would need updating if the file were moved.

## 3. Scope executed

- **Exact files moved:**  
  - `ml/training/src/dataset_creation/create_v15_balanced_dataset.py` → `ml/training/src/dataset_creation/retained_lineage/create_v15_balanced_dataset.py`  
  - `ml/training/src/utils/remove_v15_duplicates.py` → `ml/training/src/utils/retained_lineage/remove_v15_duplicates.py`
- **Exact files changed but not moved:** None. All updates were inside the two moved files (repo-root depth and import path in remove_v15_duplicates; create_v15_balanced_dataset was moved as-is, no path/import changes).
- **Exact files intentionally left in place:** All other create_v15_*, convert_v15_* in dataset_creation; survey_v15_balanced, final_v15_verification in utils; all ACTIVE v16_1/v16_2 pipeline files; all docs.
- **Why the chosen moved set was the smallest safe containment cluster:** Only the two files that (1) are clearly RETAINED_LINEAGE v15 dataset-construction utilities and (2) were already decoupled in Phase 15C/15D were moved. Moving more create_v15_* files would have required import/path updates across multiple callers and was deferred.

## 4. Containment changes completed

| Old path | New path | Classification basis | Supporting import/path changes required |
|----------|----------|------------------------|----------------------------------------|
| ml/training/src/dataset_creation/create_v15_balanced_dataset.py | ml/training/src/dataset_creation/retained_lineage/create_v15_balanced_dataset.py | Phase 15A RETAINED_LINEAGE; Phase 15B retained-lineage cluster; only caller was remove_v15_duplicates (updated). | None in this file. |
| ml/training/src/utils/remove_v15_duplicates.py | ml/training/src/utils/retained_lineage/remove_v15_duplicates.py | Phase 15A RETAINED_LINEAGE; Phase 15B retained-lineage cluster; imports create_v15_balanced_dataset. | _REPO_ROOT: `parents[4]` → `parents[5]` (one level deeper). Import: `from ml.training.src.dataset_creation.create_v15_balanced_dataset` → `from ml.training.src.dataset_creation.retained_lineage.create_v15_balanced_dataset`. Same adjustment for the inline _repo_root used at import time inside main(). |

## 5. Validation performed

- **Containment validation:** Both moved files were classified RETAINED_LINEAGE in Phase 15A; no ACTIVE items were moved. v16_2/, active finetuning, and active evaluation scripts were untouched.
- **Import/reference validation:** From repo root, `from ml.training.src.utils.retained_lineage.remove_v15_duplicates import main` and `from ml.training.src.dataset_creation.retained_lineage.create_v15_balanced_dataset import main` succeed. `python3 ml/training/src/utils/retained_lineage/remove_v15_duplicates.py` runs to completion (exit 0), including the backfill branch that imports create_v15_balanced_dataset from the new path.
- **Path-anchor validation:** remove_v15_duplicates uses `_REPO_ROOT = Path(__file__).resolve().parents[5]` (and the same inside main() for sys.path); with the file at utils/retained_lineage/remove_v15_duplicates.py, parents[5] is repo root. Output writes to repo-root–relative evaluation/finetuning/ and directory is created as in Phase 15D.
- **Behavior-preservation validation:** No logic changes beyond repo-root depth and import path. Dataset semantics and path intent unchanged.
- **Test/manual-run results:** No new tests. Manual: remove_v15_duplicates.py run from repo root completed successfully; create_v15_balanced_dataset.py import and run attempted—fails with FileNotFoundError on CWD-relative evaluation/finetuning/ paths (unchanged legacy path assumption; documented as deferred).

## 6. Items intentionally deferred

- **Retained-lineage files not moved:** create_v15_hybrid_search_replace, create_v15_corrected_dataset, create_v15_final_clean, create_v15_gold_dataset, convert_v15_balanced_to_search_replace, generate_missing_v15_examples, extract_additional_v15_examples (dataset_creation); survey_v15_balanced, final_v15_verification (utils). They are part of the same lineage but have additional callers or path assumptions; moving them would expand scope and risk.
- **Why deferred:** Smallest safe containment set was the two files already decoupled (create_v15_balanced_dataset + remove_v15_duplicates). Other create_v15_* have no in-repo Python import from remove_v15_duplicates; create_v15_gold_dataset is referenced by ACTIVE (create_v16_upgrade, prepare_v17) only by output path (v15_gold.jsonl), not by import, so moving it would require broader path/runbook updates.
- **Remaining mixed zones:** dataset_creation/ still has create_v15_* at top level alongside v16_2/ (ACTIVE). utils/ still has survey_v15_balanced, final_v15_verification at top level. Finetuning and evaluation mixed zones (ACTIVE + RETAINED) unchanged.

## 7. Risks / follow-up notes

- **Residual path assumptions:** create_v15_balanced_dataset in retained_lineage/ still uses CWD-relative Path("evaluation/finetuning/..."). A later path-assumption prep pass could apply the same repo-root pattern if needed.
- **Discoverability:** Runbooks or docs that point to the old paths (e.g. "run create_v15_balanced_dataset.py from dataset_creation/") should be updated to the new paths when touched; no doc changes were made in this pass.
- **Additional containment pass:** Optional; can move remaining create_v15_* and convert_v15_* into dataset_creation/retained_lineage/ and v15 utils into utils/retained_lineage/ with corresponding import/path updates.

## 8. Explicit non-actions

- No ACTIVE files were moved.
- No files were deleted (moved by copy-then-delete of originals; content preserved).
- No archive/export was executed.
- No naming normalization was executed.
- No broad restructuring was performed.

## 9. Recommendation for next pass

**Recommendation: no immediate action.** Minimal containment is done for the highest-coupling pair (create_v15_balanced_dataset + remove_v15_duplicates). Optional next: additional containment execution pass to move remaining create_v15_* and convert_v15_* into retained_lineage/ with minimal import/path updates, or a naming/nomenclature audit later. Active-surface tightening is independent and can proceed when desired.

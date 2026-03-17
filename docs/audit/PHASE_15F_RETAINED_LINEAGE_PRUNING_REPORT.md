# Phase 15F — Retained-Lineage Pruning Report

## 1. Objective

This pass prunes the remaining clearly retained v15 lineage off mixed active surfaces into existing `retained_lineage/` containment locations. It does **not** delete or archive lineage material. ACTIVE surfaces were preserved.

## 2. Accepted baseline

- Phase 15E executed minimal containment for create_v15_balanced_dataset and remove_v15_duplicates into dataset_creation/retained_lineage/ and utils/retained_lineage/ respectively, and deferred the remaining create_v15_*, convert_v15_*, and v15 utility files.
- This pass extends the same retained_lineage containment pattern to those deferred files.
- Forward-system active surfaces were not to be changed.

## 3. Scope executed

- **Exact files moved:**  
  - ml/training/src/dataset_creation/create_v15_hybrid_search_replace.py → ml/training/src/dataset_creation/retained_lineage/create_v15_hybrid_search_replace.py  
  - ml/training/src/dataset_creation/create_v15_corrected_dataset.py → ml/training/src/dataset_creation/retained_lineage/create_v15_corrected_dataset.py  
  - ml/training/src/dataset_creation/create_v15_final_clean.py → ml/training/src/dataset_creation/retained_lineage/create_v15_final_clean.py  
  - ml/training/src/dataset_creation/create_v15_gold_dataset.py → ml/training/src/dataset_creation/retained_lineage/create_v15_gold_dataset.py  
  - ml/training/src/dataset_creation/convert_v15_balanced_to_search_replace.py → ml/training/src/dataset_creation/retained_lineage/convert_v15_balanced_to_search_replace.py  
  - ml/training/src/dataset_creation/generate_missing_v15_examples.py → ml/training/src/dataset_creation/retained_lineage/generate_missing_v15_examples.py  
  - ml/training/src/dataset_creation/extract_additional_v15_examples.py → ml/training/src/dataset_creation/retained_lineage/extract_additional_v15_examples.py  
  - ml/training/src/utils/survey_v15_balanced.py → ml/training/src/utils/retained_lineage/survey_v15_balanced.py  
  - ml/training/src/utils/final_v15_verification.py → ml/training/src/utils/retained_lineage/final_v15_verification.py  

- **Exact files changed but not moved:**  
  - ml/training/src/dataset_creation/retained_lineage/extract_additional_v15_examples.py — updated one print hint from `evaluation/finetuning/create_v15_balanced_dataset.py` to `retained_lineage/create_v15_balanced_dataset.py`.  
  - ml/training/src/dataset_creation/retained_lineage/generate_missing_v15_examples.py — same print-hint update.  

- **Exact files intentionally left in place:** All ACTIVE v16_2, finetuning, evaluation, data-prep, and script files; all docs; convert_diff_to_search_replace.py and other non-v15 dataset_creation files; all other utils.  

- **Why the chosen moved set was the smallest safe pruning set:** Only files that are clearly RETAINED_LINEAGE (Phase 15A), have no in-repo importers except the already-contained remove_v15_duplicates (which only imports create_v15_balanced_dataset), and belong to the same v15 dataset-construction/utility cluster were moved. No ACTIVE code imports any of the moved files; path logic was left as-is except the two user-facing print hints.

## 4. Pruning changes completed

| Old path | New path | Retained-lineage basis | Supporting import/path changes required |
|----------|----------|------------------------|----------------------------------------|
| dataset_creation/create_v15_hybrid_search_replace.py | dataset_creation/retained_lineage/create_v15_hybrid_search_replace.py | Phase 15A RETAINED_LINEAGE; v15 dataset-construction cluster | None |
| dataset_creation/create_v15_corrected_dataset.py | dataset_creation/retained_lineage/create_v15_corrected_dataset.py | Phase 15A RETAINED_LINEAGE; v15 dataset-construction cluster | None |
| dataset_creation/create_v15_final_clean.py | dataset_creation/retained_lineage/create_v15_final_clean.py | Phase 15A RETAINED_LINEAGE; v15 dataset-construction cluster | None |
| dataset_creation/create_v15_gold_dataset.py | dataset_creation/retained_lineage/create_v15_gold_dataset.py | Phase 15A RETAINED_LINEAGE; v15 dataset-construction cluster | None |
| dataset_creation/convert_v15_balanced_to_search_replace.py | dataset_creation/retained_lineage/convert_v15_balanced_to_search_replace.py | Phase 15A RETAINED_LINEAGE; v15 dataset-construction cluster | None |
| dataset_creation/generate_missing_v15_examples.py | dataset_creation/retained_lineage/generate_missing_v15_examples.py | Phase 15A RETAINED_LINEAGE; v15 dataset-construction cluster | Print hint updated to retained_lineage/create_v15_balanced_dataset.py |
| dataset_creation/extract_additional_v15_examples.py | dataset_creation/retained_lineage/extract_additional_v15_examples.py | Phase 15A RETAINED_LINEAGE; v15 dataset-construction cluster | Print hint updated to retained_lineage/create_v15_balanced_dataset.py |
| utils/survey_v15_balanced.py | utils/retained_lineage/survey_v15_balanced.py | Phase 15A RETAINED_LINEAGE; v15 utility cluster | None |
| utils/final_v15_verification.py | utils/retained_lineage/final_v15_verification.py | Phase 15A RETAINED_LINEAGE; v15 utility cluster | None |

## 5. Marker notes added

- **ml/training/src/dataset_creation/retained_lineage/README.md** — Created. Content: preserved for lineage/provenance; non-canonical for the forward judgment-based system; not part of the active Layer-2 operational surface.  
- **ml/training/src/utils/retained_lineage/README.md** — Created. Same concise content as above for the utils retained-lineage folder.

## 6. Validation performed

- **Pruning validation:** All nine moved files are Phase 15A RETAINED_LINEAGE. No ACTIVE items were moved. dataset_creation/v16_2/, active finetuning, and active evaluation were untouched.  
- **Import/reference validation:** No in-repo code imports the newly moved files (only create_v15_balanced_dataset is imported, by remove_v15_duplicates, already in retained_lineage). Verified that `from ml.training.src.dataset_creation.retained_lineage import create_v15_gold_dataset` and `from ml.training.src.utils.retained_lineage import survey_v15_balanced` load successfully. remove_v15_duplicates (which imports create_v15_balanced_dataset from retained_lineage) was run and completed successfully.  
- **Path-anchor validation:** Moved files use CWD-relative or fixed path literals; no file-location-depth logic was changed. No path-anchor updates were required for the move.  
- **Active-surface validation:** Active dataset_creation/v16_2, active finetuning, and active evaluation surfaces were not modified.  
- **Test/manual-run results:** No new tests. Manual: import of two moved modules and run of remove_v15_duplicates from repo root — success.

## 7. Items intentionally deferred

- **Retained-lineage files not moved:** None remaining in the in-scope cluster. convert_diff_to_search_replace.py and create_v14_multifile_dataset.py, create_v13_dataset.py, etc. are in dataset_creation but are not part of the “create_v15_* / convert_v15_*” cluster; they were left in place.  
- **Why deferred:** Only the clearly retained v15 dataset-construction and v15 utility set was pruned; other legacy or versioned scripts were out of scope.  
- **Remaining mixed zones:** dataset_creation/ still has non-v15 scripts (e.g. convert_diff_to_search_replace, create_v14_multifile_dataset, split_train_test) alongside v16_2/ (ACTIVE). utils/ no longer has v15 files at top level. Finetuning and evaluation mixed zones (ACTIVE + RETAINED) were unchanged.

## 8. Risks / follow-up notes

- **Residual path/import assumptions:** Moved scripts still use CWD-relative or literal paths (e.g. evaluation/finetuning/, v15_balanced.jsonl). A later path-assumption pass could add repo-root resolution if desired.  
- **Discoverability:** Runbooks or docs that reference the old paths should be updated when touched; no broad docs cleanup was performed.  
- **Additional pruning:** No further v15 dataset-construction or v15 utility pruning is required for the defined cluster. Optional: contain other legacy dataset_creation or utils scripts in a later pass if desired.

## 9. Explicit non-actions

- No ACTIVE files were moved.  
- No files were deleted except the originals after copy to retained_lineage (content preserved).  
- No archive/export was executed.  
- No naming normalization was executed.  
- No broad restructuring was performed.

## 10. Recommendation for next pass

**Recommendation: no immediate action.** Retained v15 dataset-construction and v15 utility files are now contained under dataset_creation/retained_lineage/ and utils/retained_lineage/. Optional next: active-surface tightening pass, or naming/nomenclature audit later.

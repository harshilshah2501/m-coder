# Phase 15B — Legacy Lineage Containment Boundary Report

## 1. Objective

This pass defines containment boundaries only. It performs **no** moves, renames, deletions, or archive execution. Phase 15A is the accepted baseline. The goal is to specify how ACTIVE, RETAINED_LINEAGE, and ARCHIVAL/HISTORICAL legacy Layer-2 material should be conceptually contained so that future containment or archive actions can be executed safely.

## 2. Accepted baseline from Phase 15A

- **ACTIVE:** 26 items — v16_1/v16_2 dataset pipeline, training, merge, validation, and evaluation scripts; data-prep steps (create_v16_upgrade, create_v16_1_splits, surgical_precision_fix, fix_dataset_v16_1, etc.); prepare_v17_dataset (reads v15_gold). All in `ml/training/src/data/`, `ml/training/src/finetuning/`, `ml/training/scripts/`, `ml/training/src/dataset_creation/v16_2/`, and `ml/training/src/evaluation/` (evaluate_v16_* only).
- **RETAINED_LINEAGE:** 64 items — v15 training/eval/merge/utils and create_v15_* dataset_creation scripts; train_v16_enhanced, test_v16_inference; v15/v16 artifacts, specs, and docs under ml/training (artifacts, results, evaluation), ml/datasets, ml/evaluation, and docs (training, datasets, evaluation, status_reports, audit, benchmark).
- **ARCHIVE_CANDIDATE:** 13 items — all under `archive/` (v15 training logs, cleanup docs, V15 next-steps/merge/training-completed copies).
- **Pre-judgment origin** was **not** used as the classification criterion in Phase 15A; evidence (references, pipeline role, path-remediation) was used.

## 3. Containment surfaces defined

### ACTIVE SURFACE

- **Definition:** The live Layer-2 operational surface. Files and directories that are directly involved in active dataset preparation, freeze/SFT/retraining lineage, validation, merge, reproducibility, or path-remediation-relevant flows.
- **What belongs here:** The 26 Phase 15A ACTIVE items: v16_1/v16_2 data pipeline scripts (create_v16_upgrade, deduplicate_v16_1, create_v16_1_splits, surgical_precision_fix, final_dataset_validation, fix_motadata_categories, verify_category_consistency, validate_v16_1_surgical); v16_1/v16_2 finetuning and merge (train_v16_1_surgical, train_v16_2, validate_v16_1_fixed, test_v16_1_merged, merge_v16_1, merge_v16_2); scripts (fix_dataset_v16_1.py, train_v16_1.sh); dataset_creation/v16_2 (data_curation, surgical_fixer, final_polish); prepare_v17_dataset; and evaluate_v16_1_* / evaluate_v16_2_* evaluation scripts. These must remain on the active surface and be discoverable for current pipelines.

### RETAINED_LINEAGE SURFACE

- **Definition:** In-repo preserved material that is not part of the active operational surface but must remain available for provenance, auditability, lineage continuity, comparison baseline, rebuild/debug traceability, or ambiguous-yet-meaningful legacy context.
- **What belongs here:** The 64 Phase 15A RETAINED_LINEAGE items: v15 finetuning/merge/eval scripts (train_v15_*, merge_v15_model, finetune_v15_*, v15_* eval scripts); train_v16_enhanced, test_v16_inference; v15 utils (survey_v15_balanced, remove_v15_duplicates, final_v15_verification); create_v15_* and convert_v15_* in dataset_creation; v15 processed data and artifacts (v15_search_replace_20251231.jsonl, v15_* results/benchmark JSON); v16_1 results and plans (v16_1_test_results.json, v16_1_merged_model_analysis.md, v16_1_kpi_evaluation_plan.md); ml/datasets v15 specs and validation reports; ml/evaluation v16_1/v16_2 results and v16_1_RCA; and all legacy V15/V16/V16_1/V16_2 docs under docs/. They must stay in-repo and preserved; they may later be grouped under a dedicated retained-lineage area or remain co-located where coupling dictates.

### ARCHIVAL/HISTORICAL SURFACE

- **Definition:** Material already under `archive/` or future archive-oriented material that is historical-only and not needed on the active repo surface. This phase may identify future candidates but must not move anything.
- **What belongs here:** The 13 Phase 15A ARCHIVE_CANDIDATE items (all under `archive/`): archive/okr/supporting-docs/V15_FINAL_DATASET_SUMMARY.md; archive/docs/v15_training_logs/*; archive/docs/V15_VALIDATION_CONFIRMED_20251231.md; archive/docs/cleanup_20251231/V15_*; archive/docs/V15_NEXT_STEPS.md, V15_MERGE_COMPLETE.md, V15_TRAINING_COMPLETED.md. Already contained. No additional moves are proposed in this pass.

## 4. Containment mapping by cluster

| Path or cluster | Phase 15A basis | Containment surface | Why it belongs there | Immediate action status |
|-----------------|-----------------|---------------------|------------------------|-------------------------|
| ml/training/src/data/ (legacy-named only: validate_v16_1_surgical, create_v16_upgrade, deduplicate_v16_1, create_v16_1_splits, prepare_v17_dataset, surgical_precision_fix, final_dataset_validation, fix_motadata_categories, verify_category_consistency) | ACTIVE | ACTIVE SURFACE | Core v16_1/v17 data pipeline; consumed by fix_dataset_v16_1, train_v16_1_surgical, data_curation | keep in place |
| ml/training/src/finetuning/ — v16_1/v16_2 subset (train_v16_1_surgical, train_v16_2, validate_v16_1_fixed, test_v16_1_merged, merge_v16_1, merge_v16_2) | ACTIVE | ACTIVE SURFACE | Live training/merge/validation entrypoints; Phase 14D path contract | keep in place |
| ml/training/src/finetuning/ — v15/v16_enhanced subset (train_v16_enhanced, merge_v15_model, train_v15_*, finetune_v15_*) | RETAINED_LINEAGE | RETAINED_LINEAGE SURFACE | Provenance, rebuild traceability; no active callers | keep in place; later contain if a dedicated retained-lineage area is adopted |
| ml/training/scripts/ (fix_dataset_v16_1.py, train_v16_1.sh) | ACTIVE | ACTIVE SURFACE | Required for v16_1 splits→fixed and training entry | keep in place |
| ml/training/src/dataset_creation/v16_2/ (data_curation.py, surgical_fixer.py, final_polish.py) | ACTIVE | ACTIVE SURFACE | v16_2 dataset construction from v16_1_fixed; Phase 14E | keep in place |
| ml/training/src/dataset_creation/ — create_v15_*, convert_v15_* | RETAINED_LINEAGE | RETAINED_LINEAGE SURFACE | v15 dataset provenance; create_v15_gold produces v15_gold consumed by ACTIVE; remove_v15_duplicates imports create_v15_balanced_dataset | keep in place; defer relocation due to import coupling |
| ml/training/src/evaluation/ — evaluate_v16_1_*, evaluate_v16_2_* | ACTIVE | ACTIVE SURFACE | Current v16_1/v16_2 evaluation entrypoints | keep in place |
| ml/training/src/evaluation/ — test_v16_inference, v15_* eval scripts | RETAINED_LINEAGE | RETAINED_LINEAGE SURFACE | Lineage, methodology, comparison baseline | keep in place; later contain if evaluation is split by surface |
| ml/training/src/utils/ (survey_v15_balanced, remove_v15_duplicates, final_v15_verification) | RETAINED_LINEAGE | RETAINED_LINEAGE SURFACE | v15_balanced analysis; remove_v15_duplicates couples to dataset_creation | keep in place; defer relocation due to import coupling |
| ml/training/data/processed/v15_search_replace_20251231.jsonl | RETAINED_LINEAGE | RETAINED_LINEAGE SURFACE | Reproducibility for train_v15_search_replace | keep in place |
| ml/training/artifacts/v15_*.json | RETAINED_LINEAGE | RETAINED_LINEAGE SURFACE | Audit trail | keep in place |
| ml/training/results/v16_1_*.json, v16_1_merged_model_analysis.md | RETAINED_LINEAGE | RETAINED_LINEAGE SURFACE | Eval/merge outputs; forensic traceability | keep in place |
| ml/training/evaluation/v16_1_kpi_evaluation_plan.md | RETAINED_LINEAGE | RETAINED_LINEAGE SURFACE | Planning doc | keep in place |
| ml/datasets/ (v15_* validation reports, V15_* spec/summary .md) | RETAINED_LINEAGE | RETAINED_LINEAGE SURFACE | v15_gold spec and validation artifacts | keep in place |
| ml/evaluation/results/ (v16_2_*.json, evaluation_report_v16_1.html), ml/evaluation/analysis/v16_1_RCA.md | RETAINED_LINEAGE | RETAINED_LINEAGE SURFACE | Eval outputs and forensics | keep in place |
| docs/training/, docs/datasets/, docs/evaluation/, docs/status_reports/, docs/audit/, docs/benchmark/ (V15/V16/V16_1/V16_2 legacy docs and artifacts) | RETAINED_LINEAGE | RETAINED_LINEAGE SURFACE | Methodology, runbooks, audit | keep in place; later contain under docs/ retained-lineage subarea if desired |
| docs/v16_1eval.xml, docs/V16_1_MODEL_UPGRADE_HYPOTHESIS.md | RETAINED_LINEAGE | RETAINED_LINEAGE SURFACE | Eval artifact and hypothesis doc | keep in place |
| archive/ (all Phase 15A ARCHIVE_CANDIDATE items) | ARCHIVE_CANDIDATE | ARCHIVAL/HISTORICAL SURFACE | Historical-only; already under archive/ | already contained |

## 5. Mixed-zone findings

| Directory or cluster | Why it is mixed | What makes future containment hard | Separation plausible later? |
|----------------------|------------------|-------------------------------------|-----------------------------|
| **ml/training/src/finetuning/** | Contains both ACTIVE (v16_1/v16_2 train, merge, validate) and RETAINED_LINEAGE (train_v16_enhanced, merge_v15_model, train_v15_*, finetune_v15_*) in the same directory. | Scripts share the same package and are run as entrypoints; no import coupling between ACTIVE and RETAINED within finetuning. Moving RETAINED_LINEAGE to a subdir or sibling would require path/import consistency and runbook updates. | Yes, if a subdir (e.g. `finetuning/retained_lineage/` or `finetuning/legacy_v15/`) is introduced and runbooks/doc references updated. Risk: low if only grouping, no import changes. |
| **ml/training/src/evaluation/** | Contains both ACTIVE (evaluate_v16_1_*, evaluate_v16_2_*) and RETAINED_LINEAGE (test_v16_inference, v15_* eval scripts) in the same directory. | Same package; shared RESULTS_DIR and path assumptions in some scripts; docs reference both. | Yes, by subdir or naming convention; document which scripts are active vs retained to avoid confusion. |
| **ml/training/src/dataset_creation/** | Contains ACTIVE (v16_2/ subtree) and RETAINED_LINEAGE (create_v15_*, convert_v15_*) in the same tree. v16_2 is a dedicated subdir; create_v15_* are at top level. | remove_v15_duplicates.py (under utils/) imports `create_v15_balanced_dataset` (unqualified); moving dataset_creation scripts would break that import unless fixed. | Possible after import decoupling: e.g. qualified import from ml.training.src.dataset_creation or a shared module. Then a subdir such as `dataset_creation/legacy_v15/` could hold create_v15_* and convert_v15_*. |

## 6. Blockers to future containment

- **Import coupling:** `ml/training/src/utils/remove_v15_duplicates.py` does `from create_v15_balanced_dataset import classify_example, is_valid_example`. Relocating create_v15_balanced_dataset without updating to a package-qualified import (or extracting shared helpers) would break execution. Any containment that moves dataset_creation modules requires an import-decoupling prep pass first.
- **Script/path assumptions:** Many RETAINED_LINEAGE scripts use CWD-relative or legacy path shapes (e.g. `v15_balanced.jsonl`, `evaluation/finetuning/...`). Moving them without updating paths could break reproducibility runs. Containment execution would need to either keep paths valid or introduce a data-root contract for legacy paths.
- **Co-located mixed lineage:** finetuning/ and evaluation/ mix ACTIVE and RETAINED_LINEAGE in one directory. Moving only RETAINED_LINEAGE into a subdir is plausible but requires runbook and doc updates so operators know where to find legacy scripts.
- **Documentation/reference coupling:** docs/training (e.g. V16_2_TRAINING_STATUS.md) reference merge_v16_2.py and v16_1 flows; docs reference both active and retained scripts. Splitting or moving retained docs must preserve or update cross-references.
- **Reproducibility coupling:** v15_gold is produced by create_v15_gold_dataset (RETAINED_LINEAGE) and consumed by create_v16_upgrade and prepare_v17_dataset (ACTIVE). The data contract (ml/datasets/v15_gold.jsonl or equivalent) must remain resolvable; moving only scripts does not remove this coupling.
- **Unknown usage ambiguity:** train_v16_enhanced and test_v16_inference have no direct call sites in code; they may be run ad hoc. Containment that renames or relocates them could confuse operators who run them manually unless documented.

## 7. Recommended boundary policy

- **Must remain on active Layer-2 surface:** All 26 Phase 15A ACTIVE items; no demotion of these to RETAINED_LINEAGE without a formal reclassification and evidence that the pipeline no longer uses them.
- **Should not remain on the active surface long-term (conceptual):** RETAINED_LINEAGE material is not “active” by definition; it is acceptable for it to remain in place until containment execution, but the boundary between “run for current pipelines” vs “preserved for lineage” should be explicit (e.g. documented or grouped) so that active-surface tightening can eventually focus only on ACTIVE surface.
- **Must stay preserved in-repo even if later contained:** All 64 RETAINED_LINEAGE items must remain in the repository and discoverable; any future “containment” is grouping or relocation under a retained-lineage area, not deletion or archive-export unless separately agreed.
- **Belongs only under archive/historical surface:** The 13 ARCHIVE_CANDIDATE items are already under `archive/`; no other legacy material is designated ARCHIVAL/HISTORICAL in this pass. Future archive-planning may consider export of archive/ contents but is out of scope for boundary definition.

## 8. Conservative next-step recommendation

**Recommendation: import-decoupling prep pass next.** The containment mapping is clear (ACTIVE vs RETAINED_LINEAGE vs already-contained ARCHIVAL), but the main blocker to any relocation of RETAINED_LINEAGE code is the unqualified import in `remove_v15_duplicates.py` from `create_v15_balanced_dataset`. A focused pass that (1) replaces that with a package-qualified import (or extracts shared helpers into a small shared module) and (2) documents path assumptions for v15_balanced and evaluation/finetuning legacy paths would reduce risk before a later containment execution pass. Do not perform containment execution (moves/grouping) until import coupling is resolved and path contract for legacy data is explicit.

## 9. Explicit non-actions

- No files were moved.
- No files were renamed.
- No files were deleted.
- No archive or export was executed.
- No source code behavior was changed.

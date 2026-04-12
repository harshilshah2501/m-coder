# Phase 15A — Legacy Lineage Classification Report

## 1. Objective

This pass classifies legacy Layer-2 lineage material only. It performs **no** moves, deletions, renames, or cleanup. The goal is to produce a precise inventory and evidence-based classification (ACTIVE, RETAINED_LINEAGE, ARCHIVE_CANDIDATE) so that later containment or archive decisions can be made safely.

## 2. Classification rules used

- **ACTIVE** — File is clearly part of the current canonical or still-operational Layer-2 surface (referenced by active scripts/configs/pipelines; participates in dataset preparation, validation, freeze, SFT, merge, or reproducibility flows; needed for deterministic rebuilds or active audit/revalidation; part of path-remediation surface).
- **RETAINED_LINEAGE** — File is not clearly active but should remain preserved for provenance, lineage continuity, forensic traceability, comparison baseline, rebuild/debug context, or unresolved classification due to ambiguity.
- **ARCHIVE_CANDIDATE** — No evidence of active references or call sites; no meaningful role in current compilation/freeze/SFT/validation lineage; not required for reproducibility, auditability, or forensic history; appears historical residue only; recommendation for later containment, not permission to move now.
- **Ambiguity rule:** When classification is uncertain, the item is marked **RETAINED_LINEAGE**.

## 3. Scope inspected

- **Directories inspected:** `ml/training/src/data/`, `ml/training/src/dataset_creation/`, `ml/training/src/finetuning/`, `ml/training/src/evaluation/`, `ml/training/src/utils/`, `ml/training/scripts/`, `ml/training/data/processed/`, `ml/training/artifacts/`, `ml/training/results/`, `ml/training/evaluation/`, `ml/datasets/`, `ml/evaluation/`, `docs/training/`, `docs/datasets/`, `docs/evaluation/`, `docs/audit/`, `docs/benchmark/`, `archive/docs/`, `archive/okr/`. *(docs/status_reports/ removed from repo.)*
- **Patterns used:** Path or filename contains `v15`, `v16`, `v16_1`, or `v16_2`.
- **Intentionally excluded:** Files outside the above areas that do not match the version patterns; runtime/ and non–Layer-2 code not in the legacy lineage surface.

## 4. Classification results

| Path | Type | Classification | Current role summary | Evidence summary | Notes / ambiguity |
|------|------|----------------|----------------------|------------------|--------------------|
| ml/training/src/data/validate_v16_1_surgical.py | file | ACTIVE | Validates v16_1 upgraded dataset for surgical pipeline | Referenced by data pipeline; writes v16_1_validation_report.json; DATASET_FILE = v16_1_upgraded.jsonl | Part of v16_1 dataset chain |
| ml/training/src/data/create_v16_upgrade.py | file | ACTIVE | Builds v16_1_upgraded from v15_gold + v17 | V15_FILE, OUTPUT_FILE in ml/datasets; consumed by deduplicate_v16_1, validate_v16_1_surgical | Core v16_1 upgrade step |
| ml/training/src/data/deduplicate_v16_1.py | file | ACTIVE | Deduplicates v16_1_upgraded → v16_1_upgraded_dedup | INPUT/OUTPUT in ml/datasets; consumed by fix_motadata_categories, verify_category_consistency | Part of v16_1 chain |
| ml/training/src/data/create_v16_1_splits.py | file | ACTIVE | Splits v16_1_surgical into train/val/test | OUTPUT_DIR = ml/datasets/v16_1_splits; consumed by fix_dataset_v16_1; referenced in Phase 14E | In path-remediation surface |
| ml/training/src/finetuning/train_v16_1_surgical.py | file | ACTIVE | Trains v16_1 from v16_1_fixed splits | DATASET_DIR = ml/datasets/v16_1_fixed; Phase 14D converted to data root; docs/README status | Live training entrypoint |
| ml/training/src/finetuning/train_v16_2.py | file | **REMOVED** | *(deleted from repo — obsolete)* | Inference: `runtime/scripts/governed_services.sh` | — |
| ml/training/src/finetuning/validate_v16_1_fixed.py | file | ACTIVE | Validates v16_1_fixed dataset | DATASET_DIR = ml/datasets/v16_1_fixed; Phase 14D path contract | Validation for active pipeline |
| ml/training/src/finetuning/test_v16_1_merged.py | file | ACTIVE | Tests merged v16_1 model on v16_1_fixed | DATASET_DIR = v16_1_fixed; Phase 14D; part of merge validation | Post-merge validation |
| ml/training/src/finetuning/merge_v16_1.py | file | ACTIVE | Merges v16_1 LoRA into base model | ADAPTER_PATH, OUTPUT_PATH; Phase 14D converted | Merge step for v16_1 |
| ml/training/src/finetuning/merge_v16_2.py | file | **REMOVED** | *(deleted from repo — obsolete)* | Use external merge tooling + `VLLM_BASE_MODEL` in `runtime/config/demo_stack.env` | — |
| ml/training/scripts/fix_dataset_v16_1.py | file | ACTIVE | Fixes v16_1_splits → v16_1_fixed (chat template) | INPUT_DIR = v16_1_splits, OUTPUT_DIR = v16_1_fixed; consumed by train_v16_1_surgical, data_curation; Phase 14E | Required for v16_1 training |
| ml/training/scripts/train_v16_1.sh | file | ACTIVE | Shell entrypoint for v16_1 training | Wraps train_v16_1_surgical flow | Operational script |
| ml/training/src/dataset_creation/v16_2/data_curation.py | file | ACTIVE | Curates v16_1_fixed → v16_2 dataset | INPUT_DIR = v16_1_fixed, OUTPUT_DIR = v16_2; Phase 14E; feeds v16_2 pipeline | v16_2 dataset construction |
| ml/training/src/dataset_creation/v16_2/surgical_fixer.py | file | ACTIVE | Surgical fix v16_2 → v16_2_surgical | INPUT_DIR = v16_2, OUTPUT_DIR = v16_2_surgical; same pipeline | v16_2 pipeline |
| ml/training/src/dataset_creation/v16_2/final_polish.py | file | ACTIVE | Polishes v16_2 → v16_2_final | INPUT_DIR = v16_2, OUTPUT_DIR = v16_2_final | v16_2 pipeline |
| ml/training/src/data/prepare_v17_dataset.py | file | ACTIVE | Prepares v17 dataset; reads v15_gold | V15_GOLD = ml/datasets/v15_gold.jsonl; active v17 flow | References v15_gold |
| ml/training/src/data/surgical_precision_fix.py | file | ACTIVE | Produces v16_1_surgical.jsonl | OUTPUT_FILE = ml/datasets/v16_1_surgical.jsonl; consumed by create_v16_1_splits | v16_1 chain |
| ml/training/src/data/final_dataset_validation.py | file | ACTIVE | Validates v16_1_surgical | DATASET_FILE = v16_1_surgical.jsonl | v16_1 validation |
| ml/training/src/data/fix_motadata_categories.py | file | ACTIVE | v16_1_upgraded_dedup → v16_1_final | INPUT_FILE = v16_1_upgraded_dedup.jsonl | v16_1 chain |
| ml/training/src/data/verify_category_consistency.py | file | ACTIVE | Consistency check on v16_1_upgraded_dedup | DATASET_FILE = v16_1_upgraded_dedup.jsonl | v16_1 chain |
| ml/training/src/evaluation/evaluate_v16_1_model.py | file | ACTIVE | Evaluates v16_1 model | TEST_FILE references v16_1_splits; produces eval results | Eval entrypoint |
| ml/training/src/evaluation/evaluate_v16_1_on_motadata_tasks.py | file | ACTIVE | v16_1 evaluation on Motadata tasks | Part of evaluation surface | Eval |
| ml/training/src/evaluation/evaluate_v16_1_motadata_bench.py | file | ACTIVE | v16_1 Motadata benchmark | Produces results | Eval |
| ml/training/src/evaluation/evaluate_v16_2.py | file | ACTIVE | Evaluates v16_2 model | RESULTS_DIR; ml/evaluation/results/v16_2_* | Eval |
| ml/training/src/evaluation/evaluate_v16_2_enriched.py | file | ACTIVE | v16_2 enriched evaluation | Output v16_2_enriched_*.json | Eval |
| ml/training/src/evaluation/evaluate_v16_2_motadata_bench.py | file | ACTIVE | v16_2 Motadata benchmark | Output v16_2_motadata_bench_*.json | Eval |
| ml/training/src/finetuning/train_v16_enhanced.py | file | RETAINED_LINEAGE | Enhanced v16 training variant | No direct references found in other code; version name suggests v16 lineage | Ambiguous whether still run; preserve for lineage |
| ml/training/src/evaluation/test_v16_inference.py | file | RETAINED_LINEAGE | v16 inference test | docs/evaluation references; no import/call sites in code | Lineage / methodology |
| ml/training/src/utils/survey_v15_balanced.py | file | RETAINED_LINEAGE | Survey of v15_balanced dataset | INPUT_FILE = v15_balanced.jsonl; used for analysis; remove_v15_duplicates references same dataset | Lineage; v15_balanced path shape legacy |
| ml/training/src/utils/remove_v15_duplicates.py | file | RETAINED_LINEAGE | Dedup v15_balanced | Imports create_v15_balanced_dataset; v15 pipeline provenance | Lineage |
| ml/training/src/utils/final_v15_verification.py | file | RETAINED_LINEAGE | Final verification v15_balanced | V15_FILE = v15_balanced.jsonl | Lineage |
| ml/training/src/finetuning/merge_v15_model.py | file | RETAINED_LINEAGE | Merge v15 model | v15 merge step; no active callers; provenance for v15→v16 | Lineage |
| ml/training/src/finetuning/train_v15_search_replace.py | file | RETAINED_LINEAGE | Train v15 search/replace | DATASET_FILE = v15_search_replace.jsonl; data in ml/training/data/processed/v15_search_replace_20251231.jsonl | Reproducibility |
| ml/training/src/finetuning/train_v15_balanced.py | file | RETAINED_LINEAGE | Train v15 balanced | v15_balanced.jsonl; lineage to v15 training | Lineage |
| ml/training/src/finetuning/finetune_v15_qwen.py | file | RETAINED_LINEAGE | Finetune v15 (Qwen) | v15 finetuning; no active refs | Lineage |
| ml/training/src/finetuning/finetune_v15_claude.py | file | RETAINED_LINEAGE | Finetune v15 (Claude) | v15 finetuning; no active refs | Lineage |
| ml/training/src/evaluation/v15_post_finetuning_eval.py | file | RETAINED_LINEAGE | v15 post-finetuning eval | v15 eval; no active callers | Lineage |
| ml/training/src/evaluation/test_v15_inference.py | file | RETAINED_LINEAGE | v15 inference test | v15 eval | Lineage |
| ml/training/src/evaluation/validate_v15_dataset.py | file | RETAINED_LINEAGE | Validate v15 dataset | v15_balanced paths; validate_dataset.py doc references v15_gold | Lineage |
| ml/training/src/evaluation/test_v15_model.py | file | RETAINED_LINEAGE | Test v15 model | v15 eval | Lineage |
| ml/training/src/evaluation/inspect_v15_samples.py | file | RETAINED_LINEAGE | Inspect v15 samples | v15_balanced.jsonl | Lineage |
| ml/training/src/evaluation/benchmark_v15_model.py | file | RETAINED_LINEAGE | Benchmark v15 model | v15 benchmark; artifacts/v15_benchmark_results.json | Lineage |
| ml/training/src/dataset_creation/create_v15_hybrid_search_replace.py | file | RETAINED_LINEAGE | Create v15 hybrid search/replace | Input from archive v15_balanced_unified_diff; create_v15 pipeline | Lineage |
| ml/training/src/dataset_creation/convert_v15_balanced_to_search_replace.py | file | RETAINED_LINEAGE | v15_balanced → search/replace | INPUT_FILE = v15_balanced.jsonl; validate_v15_dataset references output | Lineage |
| ml/training/src/dataset_creation/generate_missing_v15_examples.py | file | RETAINED_LINEAGE | Generate missing v15 examples | v15 dataset creation | Lineage |
| ml/training/src/dataset_creation/create_v15_final_clean.py | file | RETAINED_LINEAGE | Create v15 final clean | Reads v15_gold; produces cleaned dataset | Lineage; v15_gold still referenced by create_v16_upgrade, prepare_v17 |
| ml/training/src/dataset_creation/create_v15_corrected_dataset.py | file | RETAINED_LINEAGE | Create v15 corrected dataset | Archive input; v15 pipeline | Lineage |
| ml/training/src/dataset_creation/extract_additional_v15_examples.py | file | RETAINED_LINEAGE | Extract additional v15 examples | v15 creation | Lineage |
| ml/training/src/dataset_creation/create_v15_gold_dataset.py | file | RETAINED_LINEAGE | Create v15 gold dataset | Output v15_gold.jsonl; consumed by create_v16_upgrade, prepare_v17 | Provenance for v15_gold |
| ml/training/src/dataset_creation/create_v15_balanced_dataset.py | file | RETAINED_LINEAGE | Create v15 balanced dataset | Imported by remove_v15_duplicates; v15_balanced lineage | Lineage |
| ml/training/data/processed/v15_search_replace_20251231.jsonl | file | RETAINED_LINEAGE | v15 search/replace processed data | train_v15_search_replace uses same semantic dataset; path shape may differ | Reproducibility |
| ml/training/artifacts/v15_test_results.json | file | RETAINED_LINEAGE | v15 test results | Audit trail | Artifact |
| ml/training/artifacts/v15_benchmark_results.json | file | RETAINED_LINEAGE | v15 benchmark results | Audit trail | Artifact |
| ml/training/results/v16_1_test_results.json | file | RETAINED_LINEAGE | v16_1 test results | Output of v16_1 flow | Artifact |
| ml/training/results/v16_1_merged_model_analysis.md | file | RETAINED_LINEAGE | v16_1 merged model analysis | Merge analysis output | Artifact |
| ml/training/evaluation/v16_1_kpi_evaluation_plan.md | file | RETAINED_LINEAGE | v16_1 KPI evaluation plan | Planning doc for v16_1 eval | Planning |
| ml/datasets/v15_gold_validation_report.json | file | RETAINED_LINEAGE | v15 gold validation report | Validation artifact for v15_gold | Artifact |
| ml/datasets/v15_final_validation_report.json | file | RETAINED_LINEAGE | v15 final validation report | Validation artifact | Artifact |
| ml/datasets/V15_GOLD_DATASET_SPECIFICATION.md | file | RETAINED_LINEAGE | v15 gold dataset specification | Spec for v15_gold; lineage doc | Spec |
| ml/datasets/V15_FINAL_DATASET_SUMMARY.md | file | RETAINED_LINEAGE | v15 final dataset summary | Summary doc | Spec |
| ml/evaluation/results/v16_2_enriched_20260108_053915.json | file | RETAINED_LINEAGE | v16_2 enriched eval result | Evaluation output | Artifact |
| ml/evaluation/results/v16_2_motadata_bench_20260108_052936.json | file | RETAINED_LINEAGE | v16_2 Motadata bench result | Evaluation output | Artifact |
| ml/evaluation/results/evaluation_report_v16_1.html | file | RETAINED_LINEAGE | v16_1 evaluation report | Eval output | Artifact |
| ml/evaluation/analysis/v16_1_RCA.md | file | RETAINED_LINEAGE | v16_1 RCA | Analysis doc | Forensics |
| docs/audit/V16_PRE_GOVERNANCE_DATA_SCRUB_PLAN.md | file | RETAINED_LINEAGE | v16 pre-governance scrub plan | Audit doc; references v16 lineage | Audit |
| docs/status_reports/* (removed) | dir | **REMOVED** | *(directory deleted — obsolete)* | — | — |
| docs/training/V16_TRAINING_SUMMARY.md | file | RETAINED_LINEAGE | v16 training summary | Training doc | Methodology |
| docs/training/V16_2_TRAINING_PLAN.md | file | RETAINED_LINEAGE | v16_2 training plan | Plan doc | Methodology |
| docs/training/V16_2_TRAINING_STATUS.md | file | **REMOVED** | *(deleted — obsolete)* | See `runtime/scripts/` + `demo_stack.env` | — |
| docs/evaluation/v16_inference_results.json | file | RETAINED_LINEAGE | v16 inference results | Eval artifact | Artifact |
| docs/evaluation/V16_INFERENCE_TEST_REPORT.md | file | RETAINED_LINEAGE | v16 inference test report | Eval doc | Methodology |
| docs/evaluation/V16_POST_TRAINING_EVALUATION.md | file | RETAINED_LINEAGE | v16 post-training evaluation | Eval doc | Methodology |
| docs/evaluation/V16_COMPREHENSIVE_EVALUATION_REPORT.md | file | RETAINED_LINEAGE | v16 comprehensive evaluation | Eval doc | Methodology |
| docs/datasets/V16_1_DATA_SOURCES_CLARIFICATION.md | file | RETAINED_LINEAGE | v16_1 data sources | Dataset doc | Methodology |
| docs/datasets/V16_2_DATASET_SUMMARY.md | file | RETAINED_LINEAGE | v16_2 dataset summary | Dataset doc | Methodology |
| docs/datasets/V16_DATASET_SUMMARY.md | file | RETAINED_LINEAGE | v16 dataset summary | Dataset doc | Methodology |
| docs/datasets/V16_1_DATASET_QUALITY_VERIFICATION.md | file | RETAINED_LINEAGE | v16_1 dataset quality verification | Dataset doc | Methodology |
| docs/datasets/V16_1_DATASET_ANALYSIS_AND_RECOMMENDATIONS.md | file | RETAINED_LINEAGE | v16_1 dataset analysis | Dataset doc | Methodology |
| docs/datasets/V16_1_DATASET_EXTRACTION_SUMMARY.md | file | RETAINED_LINEAGE | v16_1 dataset extraction | Dataset doc | Methodology |
| docs/V16_1_MODEL_UPGRADE_HYPOTHESIS.md | file | RETAINED_LINEAGE | v16_1 model upgrade hypothesis | Hypothesis doc | Methodology |
| docs/v16_1eval.xml | file | RETAINED_LINEAGE | v16_1 eval (XML) | Eval artifact | Artifact |
| docs/training/V15_FINETUNING_PRE_TRAINING_CHECKLIST.md | file | RETAINED_LINEAGE | v15 finetuning checklist | Training doc | Methodology |
| docs/training/V15_QUICK_REFERENCE.md | file | RETAINED_LINEAGE | v15 quick reference | Training doc | Methodology |
| docs/training/V15_FINETUNING_TASK_LIST.md | file | RETAINED_LINEAGE | v15 task list | Training doc | Methodology |
| docs/training/V15_COMPLETE_CHECKLIST.md | file | RETAINED_LINEAGE | v15 complete checklist | Training doc | Methodology |
| docs/training/V15_TRAINING_SUMMARY.md | file | RETAINED_LINEAGE | v15 training summary | Training doc | Methodology |
| docs/datasets/V15_DATASET_ANALYSIS_AND_RECOMMENDATIONS.md | file | RETAINED_LINEAGE | v15 dataset analysis | Dataset doc | Methodology |
| docs/datasets/V15_DATASET_QUALITY_VERIFICATION.md | file | RETAINED_LINEAGE | v15 dataset quality | Dataset doc | Methodology |
| docs/benchmark/benchmark_v15_results.json | file | RETAINED_LINEAGE | v15 benchmark results | Benchmark artifact | Artifact |
| archive/okr/supporting-docs/V15_FINAL_DATASET_SUMMARY.md | file | ARCHIVE_CANDIDATE | Copy of v15 summary in archive | Already under archive/; historical | Already contained |
| archive/docs/v15_training_logs/V15_TRAINING_STARTED.md | file | ARCHIVE_CANDIDATE | v15 training log | Already under archive/; historical logs | Already contained |
| archive/docs/v15_training_logs/V15_TRAINING_IN_PROGRESS.md | file | ARCHIVE_CANDIDATE | v15 training log | Already under archive/ | Already contained |
| archive/docs/v15_training_logs/V15_TRAINING_STATUS_UPDATED.md | file | ARCHIVE_CANDIDATE | v15 training log | Already under archive/ | Already contained |
| archive/docs/v15_training_logs/V15_TRAINING_STATUS.md | file | ARCHIVE_CANDIDATE | v15 training log | Already under archive/ | Already contained |
| archive/docs/v15_training_logs/V15_TRAINING_LIVE_STATUS.md | file | ARCHIVE_CANDIDATE | v15 training log | Already under archive/ | Already contained |
| archive/docs/V15_VALIDATION_CONFIRMED_20251231.md | file | ARCHIVE_CANDIDATE | v15 validation confirmed | Already under archive/ | Already contained |
| archive/docs/cleanup_20251231/V15_TESTING_PLAN.md | file | ARCHIVE_CANDIDATE | v15 testing plan (cleanup) | Already under archive/ | Already contained |
| archive/docs/cleanup_20251231/V15_NEXT_STEPS.md | file | ARCHIVE_CANDIDATE | v15 next steps | Already under archive/ | Already contained |
| archive/docs/cleanup_20251231/V15_MERGE_COMPLETE.md | file | ARCHIVE_CANDIDATE | v15 merge complete | Already under archive/ | Already contained |
| archive/docs/cleanup_20251231/V15_TRAINING_COMPLETED.md | file | ARCHIVE_CANDIDATE | v15 training completed | Already under archive/ | Already contained |
| archive/docs/V15_NEXT_STEPS.md | file | ARCHIVE_CANDIDATE | v15 next steps | Already under archive/ | Already contained |
| archive/docs/V15_MERGE_COMPLETE.md | file | ARCHIVE_CANDIDATE | v15 merge complete | Already contained | Already contained |
| archive/docs/V15_TRAINING_COMPLETED.md | file | ARCHIVE_CANDIDATE | v15 training completed | Already under archive/ | Already contained |

## 5. Grouped summary

### ACTIVE

- **Count:** 26 items (all files).
- **Items:** validate_v16_1_surgical.py, create_v16_upgrade.py, deduplicate_v16_1.py, create_v16_1_splits.py, train_v16_1_surgical.py, validate_v16_1_fixed.py, test_v16_1_merged.py, merge_v16_1.py, fix_dataset_v16_1.py, train_v16_1.sh, v16_2/data_curation.py, v16_2/surgical_fixer.py, v16_2/final_polish.py, prepare_v17_dataset.py, surgical_precision_fix.py, final_dataset_validation.py, fix_motadata_categories.py, verify_category_consistency.py, evaluate_v16_1_model.py, evaluate_v16_1_on_motadata_tasks.py, evaluate_v16_1_motadata_bench.py, evaluate_v16_2.py, evaluate_v16_2_enriched.py, evaluate_v16_2_motadata_bench.py. *(train_v16_2.py, merge_v16_2.py removed from repo.)*
- **Common reasons:** They are entrypoints or steps in the current v16_1/v16_2 dataset construction, training, merge, and evaluation pipelines; they are explicitly referenced by Phase 14D/14E path-remediation work; they read/write ml/datasets paths (v16_1_splits, v16_1_fixed, v16_2, v16_1_upgraded, v16_1_surgical) or model/checkpoint paths; prepare_v17_dataset and create_v16_upgrade use v15_gold as input, so the v15_gold contract remains active.

### RETAINED_LINEAGE

- **Count:** 64 items (all files).
- **Items:** train_v16_enhanced.py, test_v16_inference.py; all v15-named utils (survey_v15_balanced, remove_v15_duplicates, final_v15_verification); merge_v15_model, train_v15_search_replace, train_v15_balanced, finetune_v15_qwen, finetune_v15_claude; v15 evaluation scripts (v15_post_finetuning_eval, test_v15_inference, validate_v15_dataset, test_v15_model, inspect_v15_samples, benchmark_v15_model); all create_v15_* and convert_v15_* in dataset_creation; v15 processed data and artifacts (v15_search_replace_20251231.jsonl, v15_test_results.json, v15_benchmark_results.json); v16_1 results and plans (v16_1_test_results.json, v16_1_merged_model_analysis.md, v16_1_kpi_evaluation_plan.md); ml/datasets v15 specs and reports; ml/evaluation v16_1/v16_2 results and v16_1_RCA; all docs under docs/training, docs/datasets, docs/evaluation, docs/audit (V15/V16/V16_1/V16_2), docs/benchmark (benchmark_v15_results.json), docs/v16_1eval.xml, docs/V16_1_MODEL_UPGRADE_HYPOTHESIS.md. *(docs/status_reports/ removed — see table row above.)*
- **Common reasons:** They provide provenance (v15→v16_1 upgrade, v15_gold creation), lineage continuity (v15 training/eval scripts), forensic traceability (reports, RCAs), comparison baseline (v15 benchmarks, v16 inference tests), and rebuild/debug context (create_v15_* scripts, v15_balanced path shape). Several are ambiguous (e.g. train_v16_enhanced) and thus classified RETAINED_LINEAGE per the ambiguity rule.

### ARCHIVE_CANDIDATE

- **Count:** 13 items (all files).
- **Items:** All under `archive/` — archive/okr/supporting-docs/V15_FINAL_DATASET_SUMMARY.md; archive/docs/v15_training_logs/* (5 files); archive/docs/V15_VALIDATION_CONFIRMED_20251231.md; archive/docs/cleanup_20251231/V15_* (4 files); archive/docs/V15_NEXT_STEPS.md, V15_MERGE_COMPLETE.md, V15_TRAINING_COMPLETED.md.
- **Common reasons:** They are already under the `archive/` directory; they are historical status/log copies with no active references in code or in path-remediation surface; they appear to be historical residue only. ARCHIVE_CANDIDATE here means they are candidates for future containment/export discussion, not that they should be moved again now.

## 6. Architectural interpretation

- **v16 (including v16_1 and v16_2)** is **mixed**: a substantial subset is **active lineage** (v16_1/v16_2 dataset pipeline, training, merge, evaluation scripts and the v16_2 dataset_creation subtree). The remainder is **retained lineage** (v16 docs, eval artifacts, train_v16_enhanced, test_v16_inference).
- **v15** is predominantly **retained lineage**: it is not the current training head, but v15_gold is an **active input** to create_v16_upgrade and prepare_v17_dataset; v15 dataset-creation and training scripts are preserved for provenance and reproducibility. No v15 material outside `archive/` was classified ARCHIVE_CANDIDATE.
- **Pre-judgment origin** was **not** used as the classification criterion. Classification was based on observable evidence: references in code (create_v16_upgrade, prepare_v17_dataset, fix_dataset_v16_1, train_v16_1_surgical, etc.), role in dataset/freeze/SFT/validation chains, and presence in path-remediation plans (Phase 14C/14D/14E).
- **Dominant reasons legacy material remains in-repo:** (1) v16_1/v16_2 pipelines are still the operational training and evaluation surface; (2) v15_gold is the upstream input for v16_1 upgrade and v17 prep; (3) v15 scripts and specs support lineage and deterministic rebuilds; (4) docs and artifacts support audit and methodology; (5) items under `archive/` are already contained and are the only ones marked ARCHIVE_CANDIDATE.

## 7. Follow-up recommendation

**Recommendation: containment pass next.** The classification shows a clear split: 26 ACTIVE (v16_1/v16_2 pipeline and supporting data steps), 58 RETAINED_LINEAGE (v15 and v16 docs/artifacts/scripts), and 14 ARCHIVE_CANDIDATE (all under `archive/`). No action was taken in this pass. A conservative next step is a **containment pass** that (1) defines explicit boundaries for ACTIVE vs RETAINED_LINEAGE (e.g. docs vs code), and (2) considers whether `archive/` contents should be documented as the single designated historical area before any archive-planning or export. Do not perform archive-planning or active-surface tightening until containment is agreed.

## 8. Explicit non-actions

- No files were moved.
- No files were renamed.
- No files were deleted.
- No archive or export was executed.
- No source code behavior was changed.

# Phase 14B — Archive / Export Execution Plan

**Repository:** m-coder  
**Phase:** 14B — Archive / Export Execution Plan (planning only)  
**Date:** 2026-03-16  
**Governing principle:** Preserve-first; no execution in this phase.

**Prerequisite:** [V16_PRE_GOVERNANCE_DATA_SCRUB_PLAN.md](V16_PRE_GOVERNANCE_DATA_SCRUB_PLAN.md)

---

## 1. Purpose and scope

This document is **planning only**. It defines an ultra-surgical, preserve-first execution plan for moving large V16 / pre-governance datasets and related heavy artifacts **out of the active repo flow** without accidental loss, broken reproducibility, or hidden path breakage. It does **not** authorize or perform any of the following:

- Delete, move, rename, or export any file or directory  
- Rewrite Git history  
- Edit code or existing docs (except creating this plan)  
- Apply cleanup, stop-tracking, or archive/export  

Scope: identify candidates, destinations, reference-impact, validation gates, rollback protection, and smallest safe future execution batches.

---

## 2. Executive assessment

- **Whether archive/export is justified:** Yes. Large tracked artifacts under `ml/datasets`, `ml/training/data/processed`, `ml/evaluation/results`, and `archive/docs/debug` add substantial size to the repo and to clone/fetch; they have preservation value but need not all remain in the active development flow. Export with pointer/manifest or external store is justified provided references are updated or documented and retrieval is guaranteed.

- **Biggest candidate area:** **ml/datasets** — V16/V17 and CPT large JSONL (~247 MB tracked on disk), with the most numerous and brittle references (hardcoded absolute paths in many scripts). Any export or stop-tracking here has the highest impact and the highest risk if references are wrong.

- **Biggest execution risk:** Breaking training, evaluation, or DPO pipelines by removing or relocating data that scripts assume at current paths. Many scripts use **absolute paths** (`/home/harshil/Harshil-PoCs/datasets/...`, `.../evaluation/results`) that may point to a parent workspace rather than repo `ml/datasets` / `ml/evaluation/results`. Before any stop-tracking or removal from active flow, it must be confirmed whether CI or local workflows rely on **repo** paths (`ml/datasets`, `ml/evaluation/results`) or only on those parent paths; reference updates or pointer semantics must be defined accordingly.

---

## 3. Candidate inventory

| Item / cluster | Current location | Approx scale | Current role | Notes |
|----------------|------------------|--------------|--------------|-------|
| V16/V17 dataset splits | ml/datasets/v16_1_fixed/, v16_2/, v16_2_before_clean/ | ~247 MB (dir) | Training/val/test data for V16.1/V16.2/V17 | train/val/test.jsonl; many script refs (absolute and repo-relative) |
| CPT dataset | ml/datasets/cpt/ | ~70 MB | CPT auditing, chunked dataset | cpt_dataset.jsonl, cpt_dataset_chunked.jsonl; generation/audit refs |
| V17 DPO / generation | ml/datasets/v17_*.jsonl, generation/*.jsonl | ~20 MB+ | DPO pairs, training inputs | generate_dpo_pairs*.py, validate_dpo_dataset.py |
| Processed v15/v14 | ml/training/data/processed/ | ~65 MB | Pre-governance training inputs | v15_search_replace_20251231.jsonl, v14_multifile_final.jsonl; some scripts use different path shapes (e.g. evaluation/finetuning) |
| Evaluation results | ml/evaluation/results/ | ~6.3 MB | V16.1/V16.2 eval outputs, phase_c | comprehensive_evaluation_*.json, HTML; scripts use /home/.../evaluation/results or repo ml/evaluation/results |
| Evaluation reports | ml/evaluation/reports/ | Part of 6.3 MB | Benchmark/iteration reports | test_task1_*.json, benchmark_results |
| Archive debug JSON | archive/docs/debug/ | ~9 MB (2 large files) | Historical RAG/summary exports | RAG-Datastore_*_, RAG_System_*_.json; no active code refs found |
| ML training artifacts | ml/training/artifacts/ | ~2.4 MB | vLLM/RAG summary exports | JSON; low reference density |

---

## 4. Archive/export classification matrix

| Item / cluster | Reference status | Preservation value | Recommended handling | Preferred destination | Execution readiness | Risk | Notes |
|----------------|------------------|--------------------|----------------------|----------------------|---------------------|------|-------|
| ml/datasets (v16_*, v17_*, cpt) | **Actively referenced** (many scripts; mix of repo-relative and absolute /home/.../datasets) | **High** | Export and keep pointer/manifest in repo | External object/artifact store or Git LFS | **Needs reference cleanup plan** | **High** | Do not stop-tracking until refs are updated or retrieval path is documented and tested |
| ml/training/data/processed (v15, v14) | **Historically / weakly referenced** (some scripts use evaluation/finetuning or relative filenames; exact path shape varies) | **High** | Export and keep pointer/manifest in repo | External store or LFS | **Needs reference cleanup plan** | **High** | Align path conventions and .gitignore before removal from active flow |
| ml/evaluation/results (and reports) | **Actively referenced** (evaluate_*.py, generate_dpo_pairs*.py use BASE_DIR/.../evaluation/results or OUTPUT_DIR) | **Medium** | Export and keep pointer/manifest or summary in repo | External store or historical archive | **Needs reference cleanup plan** | **Medium** | DPO generation reads specific JSON; document retrieval or leave one canonical summary in-repo |
| archive/docs/debug (large JSON) | **No meaningful reference** (audit docs only) | **Low** | Export and remove from active tracking later | Offline historical archive or external store | **Ready after validation** | **Low** | Safest first candidate for export-only batch |
| ml/training/artifacts (summary JSON) | **Weakly referenced** | **Low** | Export and keep pointer or defer | External store or leave in archive | **Needs storage decision** | **Low** | Can be batched with archive/debug or deferred |

---

## 5. Keep-active / do-not-touch set

The following must **remain active** in the repo and must **not** be included in archive/export execution:

- ~~**docs/status_reports/**~~ — **Removed** from the repo (obsolete; was Batch D progress/planning area).  
- **docs/evaluation/, docs/training/, docs/datasets/** — V16/V15 methodology and audit; cross-links from spine.  
- **ml/training/sft/stage7/** — Active conf-drift and Stage-7 artifacts; referenced by conf_drift_pipeline and Stage-7 code.  
- **Canonical docs and governance** — README, MASTER_SYSTEM_SPEC, governance/, docs/LAYER*, PATH_SAFE and remediation plans.  
- **Code and tests** — No code edits in this plan; path refactors are a separate, pre-export planning task.  
- **ml/datasets/** — **Metadata, small manifests, and code** under ml/datasets (e.g. README, generation/*.py, tools, cpt/audit, cpt/README, dataset docs) remain; only **large data files** (JSONL and large JSON) are export candidates.  
- **ml/evaluation/** — **Code, diffs, reports structure** remain; only **heavy result payloads** (large JSON/HTML in results/ and reports/) are export candidates.

---

## 6. Reference-impact assessment

**Most dangerous references** (would need updating or documented retrieval before any stop-tracking/removal):

1. **Hardcoded absolute dataset paths**  
   - Examples: `DATASET_DIR = "/home/harshil/Harshil-PoCs/datasets/v16_1_fixed"`, `BASE_DIR / "datasets/v17_dpo_pairs_train.jsonl"`, `INPUT_DIR = Path("/home/harshil/Harshil-PoCs/datasets/v16_2")`.  
   - Used in: train_v16_1_surgical.py, validate_v16_1_fixed.py, train_v17_dpo.py, data_curation.py, surgical_fixer.py, final_polish.py, fix_dataset_v16_1.py, chunk_cpt_dataset.py, cpt_audit.py, remove_secrets.py, filter_dataset_by_judge.py, generate_dpo_pairs*.py, create_splits.py, validate_dpo_dataset.py, validate_v17_dataset.py, balance_v17_dataset.py, kpi2_truncation_test.py, kpi3_coverage_test.py, comprehensive_model_evaluation.py. *(train_v16_2.py removed from repo.)*  
   - **Risk:** If repo is the source of truth for these paths (e.g. ml/datasets is symlinked or used via env), removing data from repo breaks all of these. If only parent /home/.../datasets is used, repo export is safer but must be explicit.

2. **Evaluation results paths**  
   - Examples: `RESULTS_DIR = Path("/home/harshil/Harshil-PoCs/evaluation/results")`, `EVAL_RESULTS_FILE = BASE_DIR / "evaluation/results/comprehensive_evaluation_20260107_074916.json"`.  
   - Used in: evaluate_v16_2_enriched.py, evaluate_v16_2_motadata_bench.py, generate_dpo_pairs_enhanced.py, generate_dpo_pairs_final.py, kpi2/kpi3/comprehensive_model_evaluation.py, test_cpt_model.py.  
   - **Risk:** DPO generation depends on specific evaluation JSON; removing without a retrieval path or in-repo pointer breaks pipeline.

3. **Processed data path shape**  
   - Scripts reference `v14_multifile_final.jsonl`, `v15_search_replace.jsonl`, or `evaluation/finetuning/v14_multifile_final.jsonl`; tracked files are in `ml/training/data/processed/` with slightly different names (v15_search_replace_20251231.jsonl).  
   - **Risk:** Ambiguous which path is authoritative; export must align naming and document location.

4. **CPT paths**  
   - `train_cpt.py`: `dataset_path = "/home/harshil/Harshil-PoCs/datasets/cpt/cpt_dataset_chunked.jsonl"`; chunk_cpt_dataset.py, cpt_audit.py, remove_secrets.py use similar absolute or repo-relative paths.  
   - **Risk:** Same as (1); confirm repo vs parent layout before export.

**Recommendation:** Before **any** batch that stops tracking or removes from active flow: (1) Produce a **reference-update plan** listing every file that references each candidate path. (2) Decide whether repo paths will be replaced by env vars, config, or pointer files with retrieval instructions. (3) Implement and test retrieval (or refactor refs) in a separate batch before the export/stop-tracking batch.

---

## 7. Recommended future execution batches

### Archive/Export Batch 1 — Low-risk payloads (archive/docs/debug + optional ml/training/artifacts)

- **Name:** Archive/Export Batch 1 — Debug and optional artifact payloads  
- **Purpose:** Export large, weakly/non-referenced payloads out of active flow; preserve in a defined location; leave pointer in repo.  
- **Scope:**  
  - `archive/docs/debug/` — at least the two large RAG JSON files (~9 MB).  
  - Optionally: `ml/training/artifacts/` summary JSON (~2.4 MB) if no refs require them in-repo.  
- **Exclusions:** No ml/datasets, no ml/training/data/processed, no ml/evaluation/results; no code or doc edits except adding pointer/manifest.  
- **Preconditions:** Destination (e.g. external bucket, internal archive server) exists and is writable; retrieval URL or path documented; checksums taken for exported files.  
- **Required reference updates:** None for archive/docs/debug; for ml/training/artifacts confirm no code/doc depends on local path.  
- **Validation gates:** Pre: inventory and checksums; destination writable; retrieval mechanism documented. Post: archived files retrievable; pointer file in repo points to destination; no accidental deletion of non-copy.  
- **Rollback:** Keep local copies until post-export validation passes; if validation fails, restore from local copy and do not remove from tracking.  
- **Success criteria:** Large debug JSON (and optionally artifact JSON) exist at destination; pointer/manifest in repo; repo working tree no longer contains those files (after optional stop-tracking in a follow-up batch); retrieval verified.

### Archive/Export Batch 2 — Datasets and processed data (after reference plan)

- **Name:** Archive/Export Batch 2 — Datasets and processed data  
- **Purpose:** Export ml/datasets large JSONL and ml/training/data/processed out of active flow; preserve reproducibility via pointer/manifest and retrieval.  
- **Scope:**  
  - ml/datasets: v16_1_fixed, v16_2, v16_2_before_clean, cpt (large JSONL), v17_* large JSONL.  
  - ml/training/data/processed: v15_search_replace_20251231.jsonl, v14_multifile_final.jsonl.  
- **Exclusions:** No code edits in this batch if refs were updated in a prior batch; no history rewrite; no docs except pointer/manifest and retrieval docs.  
- **Preconditions:** (1) Reference-update plan completed and executed (refs point to config/env/pointer or external URL). (2) Destination (LFS or external store) ready; LFS or external pull documented. (3) Pointer/manifest format and location agreed (e.g. ml/datasets/ARCHIVE_MANIFEST.json, ml/training/data/processed/ARCHIVE_MANIFEST.json).  
- **Required reference updates:** Must be done **before** this batch (in a separate “reference-cleanup” batch): all script paths that today point at repo ml/datasets or ml/training/data/processed must use config, env, or pointer-based resolution; or retrieval runbook must be in place and tested.  
- **Validation gates:** Pre: full inventory and checksums; destination writable; retrieval tested. Post: export verified; pointer files correct; training/eval smoke test (or documented “restore then run”) succeeds.  
- **Rollback:** Restore from exported copy to repo paths and re-track if needed; do not remove from tracking until post-export validation passes.  
- **Success criteria:** Large dataset and processed files exist at destination; pointer/manifest in repo; working tree no longer holds those blobs (or they are LFS pointers); retrieval and one-shot reproducibility path documented and tested.

### Archive/Export Batch 3 — Evaluation results (after reference plan)

- **Name:** Archive/Export Batch 3 — Evaluation results  
- **Purpose:** Export ml/evaluation/results (and heavy reports) to external store or historical archive; keep summaries or pointers in repo.  
- **Scope:** ml/evaluation/results/* (large JSON/HTML), ml/evaluation/reports/* (heavy files).  
- **Exclusions:** No removal of evaluation code, diffs, or directory structure; no history rewrite.  
- **Preconditions:** Reference-update plan for evaluation paths executed (e.g. generate_dpo_pairs*.py and evaluate_*.py use config or retrieval path); destination ready.  
- **Required reference updates:** EVAL_RESULTS_FILE and RESULTS_DIR / OUTPUT_DIR must point to config or retrieved path; or leave one canonical summary JSON in-repo and archive the rest.  
- **Validation gates:** Pre: inventory; destination writable; retrieval or summary path documented. Post: archived results retrievable; DPO generation (or documented flow) still works.  
- **Rollback:** Restore from export to repo; re-track if needed.  
- **Success criteria:** Heavy evaluation outputs at destination; pointer or summary in repo; no broken dependency in scripts that need these results.

### Optional — History-rewrite planning handoff

- **Name:** History-rewrite planning handoff  
- **Purpose:** Hand off to a **separate** history-rewrite plan (not execution): which blobs to remove or replace, tool choice, impact on CI/clones, rollback.  
- **Scope:** Planning document only; no rewrite in archive/export batches.  
- **Exclusions:** No git filter-repo, BFG, or similar in Phase 14B execution.  
- **Preconditions:** Decision that clone size reduction is required; stakeholder agreement.  
- **Success criteria:** Clear boundary between “export/stop-tracking (working tree)” and “history rewrite”; deferred items listed in §9.

---

## 8. LFS vs external-store decision guidance

- **Prefer Git LFS** when:  
  - Data must stay “in repo” for clone workflow and you accept LFS fetch on demand.  
  - Files are large but countable and you can enforce LFS discipline (no accidental re-add as non-LFS).  
  - You do not need to shrink Git history (LFS keeps pointers in history; old blobs can remain in LFS store).  

- **Prefer external object/artifact store** when:  
  - You want to reduce clone size and fetch time without history rewrite.  
  - You have a bucket or artifact server (S3, GCS, internal HTTP) and can document retrieval (URL + checksum).  
  - You are comfortable with “clone repo + pull data from external” as the reproducibility model.  

- **Prefer offline historical archive** when:  
  - Data is for audit/compliance only and not needed for normal dev (e.g. archive/docs/debug).  
  - You can copy once to tape or cold storage and document location; no automated fetch required.  

- **Keep in repo** when:  
  - Data is small, actively used on every workflow, and refs are many and brittle (e.g. small manifests, configs).  
  - Keeping in repo is the lowest-risk option until reference cleanup is done.

**For this repo:**  
- **ml/datasets** and **ml/training/data/processed**: External store is cleaner than LFS if the goal is to avoid pulling hundreds of MB on every clone; LFS is acceptable if the team prefers “one repo clone + LFS pull” and will maintain LFS discipline.  
- **archive/docs/debug**: Offline historical archive or external store; no need for LFS.  
- **ml/evaluation/results**: External store or historical archive with one summary/pointer in-repo.

---

## 9. Deferred items and history-rewrite boundary

**Deferred until a separate history-rewrite plan exists:**  
- Any change that **removes or rewrites** Git history to shrink repo size (e.g. removing large blobs from past commits). Export and stop-tracking in the working tree do **not** shrink history; they only prevent new clones from getting those files unless they are re-added.  
- Items that are **only** problematic because they are in history: same as above; address in a dedicated history-rewrite plan, not in archive/export execution.

**Deferred until reference-cleanup plan is executed:**  
- Stop-tracking or removing **ml/datasets** and **ml/training/data/processed** from active flow (Batch 2).  
- Stop-tracking or removing **ml/evaluation/results** from active flow (Batch 3).

**Deferred until storage decision:**  
- **ml/training/artifacts** summary JSON: low risk but need explicit “external vs leave in repo” decision.

**History-rewrite boundary:**  
- This plan does **not** authorize or plan execution of git filter-repo, BFG, or any history rewrite.  
- If the goal is smaller clone size, a **separate** migration-grade plan must define: scope of blobs to remove/replace, tool, backup strategy, and impact on all clones and CI.

---

## 10. Immediate conclusions

- **What should be planned for export first:** **archive/docs/debug** (two large RAG JSON files), and optionally **ml/training/artifacts** summary JSON — smallest, lowest-reference-risk candidates. Execute as Archive/Export Batch 1 after destination and pointer format are defined.

- **What must not be touched yet:** **ml/datasets**, **ml/training/data/processed**, and **ml/evaluation/results** must not be removed from active flow or stop-tracked until: (1) reference-update plan is written and executed, and (2) destination and retrieval (or LFS) are in place and tested. Any export of these should be **copy-first**; stop-tracking only after validation.

- **Whether a history-rewrite plan is eventually needed:** Yes, **only if** the goal is to reduce Git repository size (e.g. clone/fetch time). That is a **separate** class of work; this plan defers it and does not blend it into archive/export execution.

---

## 11. Non-goals

This phase did **not**:

- Delete, move, rename, export, or stop-tracking any file or directory.  
- Rewrite Git history or recommend a specific history-rewrite run.  
- Edit code or existing docs (except creating this single planning artifact).  
- Apply cleanup or change .gitignore.  
- Execute any of the future batches described above.  
- Resolve the ambiguity between repo paths (ml/datasets, ml/evaluation/results) and absolute parent paths (/home/.../datasets, .../evaluation/results); that remains a prerequisite for Batch 2 and 3.

---

## Validation framework (reusable)

### Pre-export validation

- Confirm item inventory and sizes; compute checksums (e.g. SHA-256) for files to export.  
- Confirm destination exists, is writable, and has sufficient space.  
- Confirm retrieval mechanism (URL, path, or LFS pull) and document it.  
- Confirm ownership/access expectations for destination.  
- List all references in code/docs/scripts/tests to the paths being exported; document required updates or pointer semantics.  
- Define what remains in repo after export (pointer file, manifest, or note with retrieval instructions).

### Post-export validation

- Verify exported artifact is retrievable and checksum matches.  
- Verify pointer/manifest in repo is correct and points to destination.  
- Verify code/docs/scripts that must use the data no longer assume removed local copy (or that retrieval path is used).  
- Run a minimal workflow that depends on the data (e.g. one training or eval step, or documented “restore then run”) and confirm success.  
- Confirm no accidental deletion of non-exported files.

### Rollback rule

- **Recovery:** Exported data is recovered from the destination (or from local copy kept until validation passes).  
- **Restore active-flow presence:** Copy back from destination (or local copy) to original repo paths; re-add to Git if stop-tracking was already done.  
- **Failed batch:** If post-export validation fails, consider the batch failed; do not remove from tracking or delete local copies until validation passes; fix destination or retrieval and re-run export/validation.

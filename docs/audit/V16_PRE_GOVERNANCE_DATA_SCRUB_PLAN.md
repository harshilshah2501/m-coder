# Phase 14A — V16 Pre-Governance Data Scrub Plan

**Repository:** m-coder  
**Phase:** 14A — V16 Pre-Governance Data Scrub Plan (planning only)  
**Date:** 2026-03-16  
**Governing principle:** Classify first; no execution in this phase.

---

## 1. Purpose and scope

This document is **planning only** for classifying V16-era and pre-governance data, logs, training artifacts, and related residue in the m-coder repository. It does not authorize or perform any deletion, move, rename, history rewrite, code edit, or cleanup. The scope is to determine with evidence:

- which V16 / pre-governance artifacts still exist;
- which are large and structurally noisy;
- which retain historical, audit, reproducibility, or comparison value;
- which should leave the active repository footprint;
- which are simple working-tree cleanup candidates;
- which are **history-rewrite candidates** and therefore require a separate migration-grade operation;
- which should remain untouched.

No files were deleted, moved, or edited in this phase.

---

## 2. Executive assessment

- **Whether meaningful V16 / pre-governance cleanup is justified:** Yes, in a bounded way. The repository has ~428 MB of tracked blob data; a large portion is V16/V17 and pre-governance training datasets (ml/datasets, ml/training/data/processed), evaluation results, and archive debug payloads. Active development does not require all of this in the working tree or in history for every clone. Cleanup is justified for: (1) moving large datasets and heavy artifacts outside the active flow (e.g. LFS or external store) or stopping tracking them in a controlled way; (2) optional working-tree pruning of already-ignored generated outputs; (3) documenting what must not be scrubbed casually.

- **Biggest active-footprint problems:** (1) **Large tracked datasets under `ml/datasets`** — v16_1_fixed, v16_2, v16_2_before_clean, cpt, and v17_* JSONL files total ~247 MB on disk and are tracked; they are referenced by training/eval scripts (often via hardcoded `/home/.../datasets/...` paths) and have reproducibility value. (2) **Large tracked processed data under `ml/training/data/processed`** — v15_search_replace_20251231.jsonl (~62 MB) and v14_multifile_final.jsonl (~2.7 MB) are tracked and contribute to clone size. (3) **Archive large debug JSON** — `archive/docs/debug/` contains multi-MB JSON files (RAG summaries) that are tracked and add to repo size.

- **Biggest risks in scrubbing incorrectly:** (1) Deleting or moving datasets that training/evaluation scripts still assume in-repo (breaking reproducibility and CI). (2) Treating "V16" or "pre-governance" as a reason to remove docs that are part of the report convention (docs/status_reports, docs/evaluation, docs/training, docs/datasets) or that have audit value. (3) Assuming working-tree deletion of large tracked files fixes repo size — it does not; history would still contain the blobs, so history-rewrite planning is needed if the goal is smaller clones.

---

## 3. Inventory of V16 / pre-governance candidates

| Item / cluster | Current location | Type | Approx size / scale | Tracking status | Likely origin | Notes |
|----------------|------------------|------|--------------------|-----------------|---------------|-------|
| V16/V17 dataset splits | ml/datasets/v16_1_fixed/, v16_2/, v16_2_before_clean/ | Training JSONL | ~247 MB total (dir); single files 7–56 MB | Tracked | V16.1/V16.2/V17 pipelines | train/val/test.jsonl; many script refs |
| CPT dataset | ml/datasets/cpt/ | Dataset JSONL + metadata | ~70 MB (cpt_dataset.jsonl, cpt_dataset_chunked.jsonl) | Tracked | CPT auditing / chunked dataset | Referenced by generation and audit code |
| V17 DPO / training data | ml/datasets/v17_*.jsonl, generation/*.jsonl | DPO pairs, training data | ~20 MB+ (multiple files) | Tracked | V17 DPO and training | generate_dpo_pairs.py and eval refs |
| Processed v15/v14 data | ml/training/data/processed/ | Processed JSONL | ~65 MB (v15 ~62 MB, v14 ~2.7 MB) | Tracked | Pre-governance training | v15_search_replace_20251231.jsonl, v14_multifile_final.jsonl |
| Stage6C generated outputs | ml/training/generated/ | Ledgers, traces, runs | ~82 MB (dir) | Ignored (ml/training/generated/**) | Post-governance Stage-6C runs | stage6c_runs/ (45 run dirs), suite_traces, stage6c_ledger |
| Stage7 / SFT artifacts | ml/training/sft/stage7/*.jsonl | Traces, drift candidates | ~10 MB | Mixed (some tracked) | Conf-drift / Stage-7 | suite_traces.jsonl, conf_drift_*.jsonl |
| ML training artifacts (summaries) | ml/training/artifacts/ | JSON summaries | ~2.4 MB | Tracked | vLLM/RAG export | vLLM_Proxy_Server_Project_Summary__*.json |
| Evaluation results | ml/evaluation/results/ | JSON/HTML reports | ~6.3 MB (dir) | Tracked | V16.1/V16.2 comprehensive eval | comprehensive_evaluation_*.json, v16_1, phase_c |
| Evaluation reports | ml/evaluation/reports/ | HTML/JSON | Part of 6.3 MB | Tracked | Iteration/benchmark | test_task1_*.json, benchmark_results |
| Docs: status reports | docs/status_reports/ | Markdown | ~60 KB | Tracked | V16 deployment, planning | JANUARY_*_PROGRESS, V16_*, findings |
| Docs: evaluation/training/datasets | docs/evaluation/, docs/training/, docs/datasets/ | Markdown + JSON | ~316 KB total | Tracked | V16/V15 eval and dataset docs | V16_*.md, v16_inference_results.json |
| Archive (docs, okr, reorg) | archive/ | Mixed (md, json, txt, code) | ~14 MB | Tracked | Pre-governance, reorg, OKR | docs/debug (large JSON), okr, reorg, planning |
| Archive debug JSON | archive/docs/debug/ | RAG/summary JSON | ~9 MB (2 files ~9 MB + ~2.3 MB) | Tracked | Dec 2025 RAG exports | RAG-Datastore_*_, RAG_System_*_.json |
| V16 code references | ml/training/src/, runtime/rag/ | Python paths, model names | N/A | Tracked | V16 scripts, RAG API | Hardcoded /home/.../datasets/v16_*, models/v16_* |

---

## 4. Classification matrix

| Item / cluster | Structural value | Reference status | Classification | Risk if removed | Recommended future action | Notes |
|----------------|------------------|------------------|---------------|-----------------|---------------------------|-------|
| ml/datasets (v16_*, v17_*, cpt) | High (reproducibility, training) | Code and docs reference paths; many hardcoded /home/.../datasets | **ARCHIVE_OUTSIDE_ACTIVE_FLOW** | High: breaks training/eval if removed without migration | Export to external store or LFS; then remove from working tree in a dedicated batch; do not delete casually | If goal is smaller clone, also **HISTORY_REWRITE_CANDIDATE** |
| ml/training/data/processed (v15, v14) | High (reproducibility) | Scripts may reference; .gitignore has ml/training/data/*.jsonl but processed/ is tracked | **ARCHIVE_OUTSIDE_ACTIVE_FLOW** | High if scripts assume in-repo | Same as above; align .gitignore and refs before any stop-tracking | History-rewrite candidate if shrinking history |
| ml/training/generated (stage6c_runs, etc.) | Medium (run comparison, drift analysis) | Code expects out_dir/generated paths; not repo-root | **DELETE_WORKING_TREE_CANDIDATE** (optional) or **LEAVE_UNTOUCHED** | Low; already untracked | Optional: prune old stage6c_runs in a working-tree-only batch; keep one or two reference runs if needed | No history impact; already ignored |
| ml/training/sft/stage7/*.jsonl | Medium (conf-drift methodology) | conf_drift_pipeline, Stage-7 code | **KEEP_ACTIVE** | Medium if deleted | Leave in place; part of active Stage-7 flow | |
| ml/training/artifacts (summary JSON) | Low (debug export) | Possibly referenced in docs | **ARCHIVE_OUTSIDE_ACTIVE_FLOW** or **DELETE_WORKING_TREE_CANDIDATE** | Low | Move to archive or remove from tracking in a small batch | |
| ml/evaluation/results and reports | Medium (comparison, audit) | Evaluation scripts and docs | **ARCHIVE_OUTSIDE_ACTIVE_FLOW** or **KEEP_ACTIVE** | Medium (lose comparison baseline) | Prefer archive outside active flow; keep pointers in docs | |
| docs/status_reports | High (convention, audit) | Batch D report convention; README | **KEEP_ACTIVE** | High if deleted (convention) | Do not scrub; part of canonical report placement | |
| docs/evaluation, docs/training, docs/datasets | High (audit, methodology) | Spine and cross-links | **KEEP_ACTIVE** | High | Do not scrub; V16/V15 docs have historical and audit value | |
| archive/ (whole) | Historical (audit, reorg) | Some cross-refs from docs | **LEAVE_UNTOUCHED** or **ARCHIVE_OUTSIDE_ACTIVE_FLOW** | Medium if physically removed | Prefer leave untouched; if repo size critical, move archive to external store in a dedicated batch | |
| archive/docs/debug (large JSON) | Low (one-off exports) | Unlikely active refs | **ARCHIVE_OUTSIDE_ACTIVE_FLOW** or **HISTORY_REWRITE_CANDIDATE** | Low | Strong candidate for moving out of repo or history rewrite if shrinking clone | |
| V16 code paths (hardcoded) | N/A | Many scripts | **LEAVE_UNTOUCHED** (this phase) | N/A | Future refactor batch only; not data scrub | |

---

## 5. History-bloat assessment

- **Whether any candidates are problematic mainly because they are in Git history:** Yes. The largest contributors to tracked blob size (~428 MB) are: (1) ml/datasets (v16_1_fixed, v16_2, v16_2_before_clean, cpt, v17_*); (2) ml/training/data/processed (v15, v14); (3) archive/docs/debug (large JSON). These are already committed; removing them from the working tree in a future batch would not shrink clone size or fetch time.

- **Whether this would require a separate migration-grade history rewrite plan:** Yes. Reducing repository size would require a **separate migration-grade plan** (e.g. git filter-repo or BFG) to rewrite history to remove or replace large blobs, with full impact on clones, CI, and any existing refs to commits. That is out of scope for a normal "scrub" or working-tree cleanup batch.

- **Conclusion:** Treat **large tracked datasets and archive debug JSON** as **HISTORY_REWRITE_CANDIDATES** only when the goal is explicitly to shrink Git history; document them as such and do not perform history rewrite in this or a simple cleanup batch.

---

## 6. Active-footprint cleanup candidates

Items that are strong candidates for future **active-repo cleanup without history rewrite** (working tree only, or stop-tracking with .gitignore and optional export):

- **ml/training/generated/** — Already untracked; optional pruning of old `stage6c_runs` subdirs to reduce local disk (e.g. keep last N runs). No history impact.
- **ml/training/artifacts/** — Summary JSON files; low reference value; candidate to stop tracking and move to archive or external, or delete from working tree in a small batch (only if no doc/code refs).
- **archive/docs/debug/** — Large JSON files; good candidate to copy to external store and remove from working tree in a future batch; history would still hold them unless a separate history-rewrite is done.

---

## 7. Archive-outside-active-flow candidates

Items that should be **preserved but removed from the normal repo surface** (e.g. export to external store or LFS, then remove from working tree in a controlled batch):

- **ml/datasets** (v16_1_fixed, v16_2, v16_2_before_clean, cpt, v17_* large JSONL) — Preserve for reproducibility and comparison; move to external artifact store or LFS and update or document paths; then remove from working tree.
- **ml/training/data/processed** (v15, v14 JSONL) — Same approach.
- **ml/evaluation/results** (large evaluation JSON/HTML) — Archive externally; keep pointers or summaries in docs.
- **archive/** (optional) — If desired, move entire archive to an external location and replace with a README and pointer; otherwise leave in repo as-is.

---

## 8. Leave-untouched / preserve candidates

- **docs/status_reports/** — Part of Batch D report convention; V16 deployment and planning history; do not scrub.
- **docs/evaluation/, docs/training/, docs/datasets/** — V16/V15 evaluation and dataset documentation; audit and methodology value; do not scrub.
- **ml/training/sft/stage7/** — Active conf-drift and Stage-7 artifacts; referenced by pipeline; leave in place.
- **Canonical docs and governance** — README, MASTER_SYSTEM_SPEC, governance/, docs/LAYER*; not in scope for data scrub.
- **V16 model paths and code** — Scripts under ml/training/src and runtime/rag that reference V16; do not change in a data-scrub batch; refactor only in a dedicated path-cleanup batch if needed.

---

## 9. Recommended future execution batches

| Batch name | Purpose | Scope | Exclusions | Preconditions | Success criteria |
|------------|---------|--------|------------|----------------|------------------|
| **Working-tree cleanup** | Reduce local disk and optional stop-tracking of low-value artifacts | Optional prune of ml/training/generated/stage6c_runs; optionally stop-tracking ml/training/artifacts summary JSON; optionally remove archive/docs/debug from working tree after external copy | No deletion of ml/datasets or ml/training/data/processed; no doc/convention changes | External copy of any removed content if preservation needed; verify no active code refs | Smaller working tree; no broken refs |
| **Archive / export batch** | Move large datasets and heavy artifacts outside active repo flow | Export ml/datasets (v16_*, cpt, v17_*), ml/training/data/processed to LFS or external store; update or document paths; then remove from working tree (or stop-tracking per policy) | No history rewrite; no deletion without export | Path audit and update plan; LFS or external store ready | Artifacts preserved; working tree no longer contains large datasets; docs/scripts updated or documented |
| **History-rewrite planning batch** | Plan migration-grade history cleanup | Produce a separate plan: which blobs to remove or replace, tool choice (e.g. git filter-repo), impact on CI and clones, rollback | No execution of rewrite in same batch | Stakeholder agreement; backup and clone strategy | Written plan and decision on whether to execute |

---

## 10. Immediate conclusions

- **What should be scrubbed first, if anything:** (1) **Optional working-tree cleanup** of already-ignored `ml/training/generated/stage6c_runs` (prune old runs) and, if refs allow, low-value `ml/training/artifacts` summary JSON or `archive/docs/debug` after copying externally. (2) **No** casual deletion of ml/datasets or ml/training/data/processed — they must be exported first and then removed in a controlled batch with path/ref updates.

- **What must not be scrubbed casually:** (1) **ml/datasets** and **ml/training/data/processed** — high reproducibility and reference value; do not delete without export and migration plan. (2) **docs/status_reports**, **docs/evaluation**, **docs/training**, **docs/datasets** — part of report convention and audit; do not remove. (3) **Governance and canonical docs** — out of scope.

- **Whether history-rewrite planning is needed:** Yes, **only if** the goal is to reduce Git repository size (e.g. clone time). Then a **separate migration-grade history-rewrite plan** is needed; do not mix it with normal working-tree scrub or archive batches.

---

## 11. Non-goals

This phase did **not**:

- Delete, move, rename, or archive any file or directory.
- Rewrite Git history or recommend a specific history-rewrite tool run.
- Edit code or docs (except creating this single planning artifact).
- Apply any cleanup or change to .gitignore.
- Classify or touch cuda-pytorch_test.py, root guide, or path-contract-sensitive items from prior audits.
- Propose removing canonical docs, governance records, or report-convention directories.

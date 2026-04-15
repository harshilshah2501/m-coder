# Stage A — Candidate Generation Spec v2

**Status:** locked (implementation: `runtime/layer5/retrieval/candidate_generation.py`)

## 1. Objective

Improve **initial candidate pool quality** so downstream fusion (Stage B) has better material. Success is measured by visible deltas on real Motadata evals (`owner_in_top3`, `generic_infra_ratio`, path-set changes, debug locality).

## 2. Non-goals

- No embedding-first retrieval, graph DB, fine-tuning, or Stage B/C/D redesign.

## 3. Scope

Stage A only: multi-source, quota-based candidate generation before fusion.

## 4. Candidate sources (lanes)

1. **symbol_seed** — symbol/class-first matches (inventory + basename alignment)
2. **package_seed** — package/subsystem path alignment to query subsystems
3. **local_seed** — selected file, same-package, same-directory neighbors (debug-local)
4. **owner_injected** — authority primary owner path when resolvable
5. **lexical_residual** — remaining global lexical order (fallback)

## 5. Pool size and quotas

- Pre-fusion pool target: **20** candidates (configurable).
- Default split: **5 + 5 + 5 + 5** (symbol / package / local / lexical), with **owner** merged into the symbol lane first.
- **EXPLAIN_DEBUG:** at least **50%** local lane (10 slots), remainder split across other lanes.
- Unused quota reallocates in order: **symbol → local → package → lexical**.

## 6. Generic infra cap (Stage A)

- At most **2** generic infra paths in the 20-pool unless the query explicitly targets infra or the selected file is infra-classified.

## 7. Wiring

`retrieve_lexical(..., task_type=..., selected_file=..., authority_resolution=...)` builds the Stage A pool when `LexicalRetrievalConfig.enable_stage_a_v2` is true, then scores and returns top-k hits. Diagnostics attach under `RetrievalResult.stage_a_meta`.

## 8. Metrics

Judge Stage A using existing verifier fields: `owner_in_top1`, `owner_in_top3`, `generic_infra_ratio`, path-set diffs, debug selected-file rank.

## 9. Observable surface (exports + verifier)

- **`/v1/export_evidence`** includes `fusion_diagnostics.stage_a_meta` on the evidence bundle when Stage A v2 runs (context layer `evidence_api` mirrors ask `evidence_bridge`: authority resolved **before** retrieval).
- **`motadata_behavior_verify.py`** (`--print dev`) prints **Stage A** lane counts and `pool_paths` under each **ask** scenario; `actual_summary.stage_a` is stored in `runtime/.run/motadata_behavior_validation.json`.
- **Compare runs:** `python3 runtime/scripts/diff_motadata_behavior_validation.py BASELINE.json CANDIDATE.json` — diffs ask rows on `context_bundle.files`, `retrieval_metrics`, and `stage_a` lane/pool paths (exit 1 if diffs unless `--soft`).

---

*Full narrative criteria (query-mode biases, weak-token cap, anchored rules) match the implementation in `candidate_generation.py`.*

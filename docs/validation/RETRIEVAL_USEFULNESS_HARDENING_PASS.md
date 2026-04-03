# Retrieval usefulness hardening (surgical pass)

This pass targets **visible snippet quality**, **lexical mass on supporting paths**, and **modest core-AIOps tilt** for engineering intents — without embeddings, architecture churn, or quality-gate threshold changes.

## 1) File-by-file change summary

| File | Role |
|------|------|
| `runtime/layer5/evidence/snippet_anchor_quality.py` | **New.** Deterministic anchor scoring, domain/generic token sets, `classify_visible_snippet_kind()` for metrics. |
| `runtime/layer5/evidence/snippet.py` | Uses `pick_best_anchor_line()` instead of first token hit; still `query_token_substring_anchor` when a line matches. |
| `runtime/layer5/retrieval/lexical.py` | `content_mass` diminishing for **`supporting_prod_code`** only; `engineering_aiops_path_prior` from policy when intent ≠ `GENERIC_INTENT` and code intent active; passes `intent_type` into `_score_entry`; diagnostics: `engineering_aiops_prior`, `content_mass_lexical_trimmed`. |
| `runtime/layer5/retrieval/config.py` | `LexicalRetrievalConfig`: `enable_content_mass_diminishing`, `content_mass_linear_cap`, `enable_engineering_aiops_path_prior`. Policy v5: `engineering_aiops_path_prior`, stronger `code_intent_ingestion_log_parser_demotion`. |
| `runtime/layer5/evidence/usefulness_metrics.py` | Adds `retrieval_score_sum`, `top1_score_share`, snippet visibility buckets, `header_anchor_rate`, `domain_anchor_rate`. |
| `runtime/layer5/evidence/golden/*` | Regenerated masked JSON + fingerprint (snippet text changed for golden fixture). |
| `runtime/layer5/tests/test_snippet_anchor_quality.py` | **New** unit tests for anchor preference + `extract_snippet`. |
| `runtime/layer5/tests/test_pr6_closure_baseline_guard.py` | Required diagnostics extended for new fields. |
| `runtime/layer5/tests/test_usefulness_metrics.py` | Asserts new metric keys. |

## 2) Ranking / lexical rules added or changed

- **Content mass diminishing:** For **`supporting_prod_code`** only, raw keyword mass above `content_mass_linear_cap` (default **2200**) uses **`cap + isqrt(excess)`** so huge supporting files do not swamp sharper Java owners. Core / non-supporting paths are unchanged.
- **Engineering AIOps prior:** When **`intent_type != GENERIC_INTENT`**, **code/debug intent** is active, path contains **`/com/mindarray/aiops/`**, and file class is **`core_aiops_code`**, add scaled **`engineering_aiops_path_prior`** (policy **1.2** → scaled integer via `policy_score_scale`). **Not** applied to generic-intent queries.
- **Ingestion log-parser demotion:** `code_intent_ingestion_log_parser_demotion` increased **30.0 → 42.0** (scaled) so **`log/...*Parser.java`** on ingestion-focused queries does not beat core AIOps owners (PR-6 anchor ordering on Motadata).

## 3) Snippet anchor rules added or changed

- **Before:** First physical line with any query-token substring wins.
- **After:** Among **all** lines with at least one token hit, maximize **anchor quality score**: bonuses for **domain terms** and **code-shaped** lines; penalties for **copyright/legal/boilerplate** patterns, **import/package-only** lines, **generic-only** token sets (`motadata`, `manager`, …), and **early header zone** lines.
- **Tie-break:** Higher score, then **larger line index** (prefer body below banners).
- **`selection_reason`:** Unchanged enum; still `query_token_substring_anchor` when any line matches (schema-compatible).

## 4) Before / after — AIOps MVP pack (operator-run)

Re-run **`./scripts/run_aiops_mvp_scenario_pack.sh`** on WSL with the same Motadata checkout and compare to `AIOPS_MVP_USEFULNESS_GROUND_TRUTH_CAPTURE.md` §2.

| Scenario | Before verdict | After verdict | Before core ratio | After core ratio | Before snippet useful? | After snippet useful? | Notes |
|----------|----------------|---------------|-------------------|------------------|-------------------------|-------------------------|-------|
| A1–C2 | *(see capture)* | *fill after run* | *fill* | *fill* | *fill* | *fill* | Automated + human review |

## 5) PR-6 preservation

| Check | Result |
|-------|--------|
| `test_l58_retrieval_hardening_slice` (PR-6 invariants on canonical tree) | **PASS** |
| `test_pr6_symbol_inventory_and_fixtures` | **PASS** |
| `test_pr6_closure_baseline_metrics_and_diagnostics` | **SKIPPED** without `PR6_AIOPS_ROOT` / `MOTADATA_AIOPS_REPO_ROOT` in CI; run locally against full Motadata for **preserved / regressed** verdict. |

**Evidence:** L58 harness enforces top-1 / top-3 / mean rank on the same protected PR-6 query set embedded in the harness.

## 6) Risks / follow-ups

- **Stronger log-parser demotion** may reorder other ingestion-style queries; monitor diagnostics `ingestion_log_parser_demotion`.
- **Anchor scoring** is heuristic; if a file has tokens only in headers, the best line may still be weak — but should be **less** often pure copyright.
- Re-enable **full PR-6 guard** in CI when a Motadata path is available.

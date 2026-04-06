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
| `runtime/layer5/retrieval/lexical.py` | **Engineering top-k composition** (`_apply_engineering_intent_top_k_composition`): after sort + PR-6 corrections, promote globally ranked `core_aiops_code` files into ranks 1..k−1 until **4** cores in top-12 (or pool exhausted). **Rank 0 never changed** (PR-6 anchor). |
| `runtime/layer5/retrieval/config.py` | `enable_engineering_intent_top_k_composition`, `engineering_intent_target_core_in_top_k` (default **4**). |
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

### 4.1 Machine-filled table (baseline vs 2026-04-05 rerun)

**Before** = `AIOPS_MVP_USEFULNESS_GROUND_TRUTH_CAPTURE.md` §2 (pre–usefulness-hardening narrative baseline). **After** = batch `generated_utc` **2026-04-05T15:26:30Z**, artifacts under `~/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/` (same 8 scenarios, same `top_k`, same queries).

| Scenario | Before verdict | After verdict | Before core ratio | After core ratio | Before snippet useful? | After snippet useful? | `domain_anchor_rate` (after) | Notes |
|----------|----------------|---------------|-------------------|------------------|-------------------------|-------------------------|-------------------------------|-------|
| A1 | PARTIAL | PARTIAL | 0.25 | 0.25 | No | *human* | 0.0833 | Same `LOW_CORE_RATIO`; **3/12** `core_aiops_code` — below **0.30** gate. |
| A2 | PASS | PASS | 0.25 | 0.25 | Weak | *human* | 0.3333 | Still **GENERIC_INTENT** + `QUERY_TOO_GENERIC` + STRONG (gate does not apply core-ratio the same way). |
| D1 | PARTIAL | PARTIAL | 0.25 | 0.25 | No | *human* | 0.3333 | Same WEAK + `LOW_CORE_RATIO`; **3/12** core. |
| D2 | PARTIAL | PARTIAL | 0.1667 | 0.1667 | No | *human* | 0.0833 | **2/12** core — stricter failure vs threshold. |
| P1 | PARTIAL | PARTIAL | 0.25 | 0.25 | No | *human* | 0.25 | **3/12** core. |
| P2 | PARTIAL | PARTIAL | 0.1667 | 0.1667 | No | *human* | 0.1667 | **2/12** core. |
| C1 | PARTIAL | PARTIAL | 0.1667 | 0.1667 | No | *human* | 0.3333 | **2/12** core. |
| C2 | PARTIAL | PARTIAL | 0.25 | 0.25 | No | *human* | 0.5833 | **3/12** core. |

Fill **After snippet useful?** after inspecting `export_response.json` → `entries[0].snippet.text` (and ranks 1–2) for header vs domain body. Compare to §2 “first visible snippet” rows in the ground-truth doc.

### 4.2 Why `LOW_CORE_RATIO` was expected to move — and why it did not (this rerun)

- **Quality gate** (`quality_gate.v1`): for CODE/DEBUG/PLAN intents, `LOW_CORE_RATIO` fires when **`core_code_in_top_k_pct` &lt; 0.30** — i.e. fewer than **4** of **12** paths classified **`core_aiops_code`** (3/12 = 25%, 2/12 ≈ 16.7%).
- This pass **did not** change gate thresholds (`RETRIEVAL_USEFULNESS_HARDENING_PASS.md` §1: no quality-gate threshold edits).
- **Snippet anchor hardening** changes **which line** is shown per file, **not** which files occupy top‑k → **no direct effect** on `core_code_in_top_k_pct`.
- **Lexical** damping / prior / log-parser demotion **can** reorder top‑k; on this Motadata snapshot the **after** run still had **only 2–3** core paths in the top‑12 for gated scenarios → the **same** primary reason code **`LOW_CORE_RATIO`** remains.

**Verdict:** Per the decision rules in this doc’s intro: **mixed result** — automated verdict mix **did not** improve (still **1 PASS / 7 PARTIAL**, same drivers). Snippet-level improvement must be judged **manually** (`domain_anchor_rate` and visible text); several scenarios show higher **after** `domain_anchor_rate` than A1/D2/P2’s low values, which is consistent with **better anchors** without yet fixing **top‑k composition**.

**Next move if the goal is fewer `LOW_CORE_RATIO` rows:** additional **ranking / top‑k** work so **≥4** core AIOps paths land in top‑12 for these queries (or explicit gate review), not query edits first.

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

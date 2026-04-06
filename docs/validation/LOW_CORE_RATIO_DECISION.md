# LOW_CORE_RATIO — decision + HTTP artifact truth

**Last updated:** 2026-04-06 (consistency pass)

This document is the **single source of truth** for:
- **In-repo pool analysis** (diagnostic script; global lexical pool).
- **HTTP pipeline truth** (`export_response.json` from Context Layer + Plan-Gate metadata).

---

## A) Pool analysis (in-repo `retrieve_lexical` / `global_lexical_sorted_hits`)

Script: `scripts/diagnose_low_core_ratio_pool.py` with `MOTADATA_ROOT` + `PYTHONPATH=.`

**Finding:** For canonical MVP queries over `/home/harshil/Projects/Motadata`, the **globally scored** list contains **≥5** `core_aiops_code` paths per query — the **candidate universe is not empty**.

Top-20 **head density** can still be **2–3** cores; that measures **lexical head sparsity**, not total pool size.

---

## B) HTTP artifact verification (authoritative for MVP claim)

**Batch:** `generated_utc` **2026-04-06T10:21:00Z**  
**Paths:** `docs/validation/artifacts/aiops_mvp/`  
**Config:** `MOTADATA_ROOT=/home/harshil/Projects/Motadata`, `top_k=12`, canonical queries from `aiops_mvp_scenarios.v1.json`, `CONTEXT_URL=http://127.0.0.1:8091`, `PLAN_GATE_URL=http://127.0.0.1:8089`.

For each scenario, **paths** = `export_response.json` → `entries[0..11].relative_path`.  
**Local gate** = `assess_evidence_quality(query_raw, paths)` (same `quality_gate.v1` as Plan-Gate ingest).

| Scenario | `core_aiops_code` in top-12 (HTTP export) | `core_code_in_top_k_pct` | `LOW_CORE_RATIO` in gate reasons? | `evidence_quality` (gate) |
|----------|------------------------------------------|--------------------------|-----------------------------------|---------------------------|
| A1 | 3 | 0.25 | **Yes** | WEAK |
| A2 | 3 | 0.25 | **No** (QUERY_TOO_GENERIC only) | STRONG |
| D1 | 3 | 0.25 | **Yes** | WEAK |
| D2 | 2 | 0.1667 | **Yes** | WEAK |
| P1 | 3 | 0.25 | **Yes** | WEAK |
| P2 | 2 | 0.1667 | **Yes** | WEAK |
| C1 | 2 | 0.1667 | **Yes** | WEAK |
| C2 | 3 | 0.25 | **Yes** | WEAK |

**Strict check:** For engineering intents (A1, D*, P*, C*), **`LOW_CORE_RATIO` is present** on **7/7** rows above **except** where the generic path applies — **A2** only. **Core count ≥4** is **not** met for **any** HTTP export row (max **3**).

**Automated mix (Plan-Gate):** **1 PASS / 7 PARTIAL** — `docs/validation/artifacts/aiops_mvp/summary/run_summary.json`.

---

## C) Proof vs HTTP — mismatch (STOP)

| Source | Result |
|--------|--------|
| **In-repo** `retrieve_lexical` + `assess_evidence_quality` on same queries (earlier same-day check) | Could show **4** cores in top-12 and **no** `LOW_CORE_RATIO` for engineering scenarios. |
| **HTTP** `export_response.json` top-12 | **2–3** cores; **`LOW_CORE_RATIO`** fires; matches **Plan-Gate** `metadata.quality_reasons`. |

**Conclusion:** The **running Context Layer** process that served `:8091` did **not** produce the same top-12 as the **in-repo** lexical path used for offline proof (e.g. different **code revision** / wheel vs `PYTHONPATH` repo, or different process env). **MVP claims must use HTTP artifacts** until services are pinned to the **same commit** as repo verification.

**Code reference:** No retrieval code was changed in this consistency pass (documentation + artifact sync only).

---

## D) Verdict label (deployment truth)

**NOT “FIXED” for end-to-end MVP** until HTTP export shows **≥4** `core_aiops_code` in top-12 for engineering scenarios **or** Context Layer is aligned with repo proof.

Pool analysis (§A) remains valid **engineering** input; **§B** is the **product** truth for this run.

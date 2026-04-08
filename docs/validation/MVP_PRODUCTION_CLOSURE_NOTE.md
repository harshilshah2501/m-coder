# Production-grade MVP — closure note (authoritative)

**Date:** 2026-04-06  
**Single source of truth for MVP usefulness + HTTP alignment:** **`docs/validation/LOW_CORE_RATIO_DECISION.md` §B–C** and **`docs/validation/artifacts/aiops_mvp/summary/run_summary.json`** (`generated_utc` **2026-04-06T10:21:00Z**).

---

## Phase 0 — Snapshot

### 1. LOCKED (must not change)

- Layer-1 governance doctrine; Stage 2 trust closure (no reopen).
- Actions **4, 5, 11** and Stage 2 program closure — **closed**.
- Stage 3 runtime-loop **contracts** and schema — unchanged unless a bug is filed separately.
- **Quality-gate thresholds** — **not** relaxed to game PASS counts.
- **No embeddings / no semantic retrieval** in this program line.
- **PR-6** lexical invariants — enforced by tests / L58 harness.

### 2. WORKING (proven, usable)

- **Stage 3:** Burn-in — `docs/validation/STAGE3_BURN_IN_REPORT.md`.
- **End-to-end HTTP:** `POST /v1/export_evidence` → `POST /v1/ask` — `runtime/scripts/verify_ask_path.sh`, scenario pack runbook.
- **Retrieval:** Snippet anchors, lexical priors, engineering top-k composition — `RETRIEVAL_USEFULNESS_HARDENING_PASS.md` (§4 = **historical** batch table).
- **Context Layer index reuse:** `runtime/context_layer_service/workspace_index_cache.py` (latency; **not** usefulness).

### 3. BLOCKING (current HTTP truth — primary)

- **Fresh 8-scenario pack (2026-04-06):** **1 PASS / 7 PARTIAL**; `metadata.quality_reasons` includes **`LOW_CORE_RATIO`** on **seven** scenarios (all except **A2**, which is **`QUERY_TOO_GENERIC`**).
- **Export top-12:** **2–3** `core_aiops_code` paths per scenario on HTTP artifacts — **below** the **≥4 / 12 (30%)** gate. Local `assess_evidence_quality` on **those same paths** **matches** Plan-Gate — see **`LOW_CORE_RATIO_DECISION.md` §B**.
- **Offline in-repo `retrieve_lexical` proof** can **diverge** from HTTP top-12 — **§C** in that doc. **Do not** cite offline proof as MVP clearance until Context Layer serves **identical** retrieval codepath as the verification repo.

### 4. SEPARATE PRODUCT PRIORITIES

- **Align Context Layer deployment** with repo `HEAD` (or document wheel version) so HTTP exports = in-repo tests.
- **Index reuse:** latency only; does not change ranking.

---

## Phase 1 — Retrieval usefulness

**Authoritative:** `LOW_CORE_RATIO_DECISION.md`.

**Executive summary:** **LOW_CORE_RATIO** remains the **dominant** automated reason on **HTTP** evidence for engineering scenarios on the **2026-04-06** sync run. In-repo pool diagnostics show **enough** global `core_aiops_code` candidates exist; **deployment / service parity** is the gating issue for matching proof to HTTP.

---

## Phase 2 — Context Layer index reuse

| Item | Status |
|------|--------|
| **Implemented** | **Yes** — `workspace_index_cache.py`, env, `app.py`, `evidence_api.py`. |
| **Role** | Repeat-export latency; **no** bundle schema change. |

---

## Phase 3 — MVP truth packaging

| Artifact | Role |
|----------|------|
| `LOW_CORE_RATIO_DECISION.md` | **Primary** — HTTP table + mismatch §C. |
| `artifacts/aiops_mvp/summary/run_summary.json` | Machine counts + per-scenario metadata. |
| `AIOPS_MVP_USEFULNESS_GROUND_TRUTH_CAPTURE.md` | Baseline history + **post-fix HTTP** section (2026-04-06). |
| `RETRIEVAL_USEFULNESS_HARDENING_PASS.md` | §4 **historical**; §7 points here. |
| `AIOPS_MVP_FINAL_REPORT_TEMPLATE.md` | Filled snapshot **2026-04-06** (below / file). |

---

## Phase 4 — Final acceptance (deployment truth)

**Label: B. MVP READY WITH CAVEATS**

| Criterion | Basis |
|-----------|--------|
| Chain works | HTTP 200 on full pack; artifacts written. |
| Usefulness / gate | **WEAK** on **7/8** automated bar; **`LOW_CORE_RATIO`** present on HTTP paths. |
| Proof vs HTTP | **Mismatch** documented — fix = **service alignment**, not new heuristics in this pass. |
| Stage 3 / latency | Separate; burn-in + index reuse OK. |

---

## Executive truth (one paragraph)

The **evidence-first HTTP path** completes and writes **fresh** **`run_summary.json` (2026-04-06)** with **1 PASS / 7 PARTIAL** and **`LOW_CORE_RATIO`** still dominant in Plan-Gate metadata for engineering scenarios. **Export** top-12 paths contain **2–3** `core_aiops_code` entries — **not** enough for the gate — and **local `assess_evidence_quality` on those paths matches** Plan-Gate. **In-repo** lexical proof **without** HTTP can show **more** cores in top-12; **that does not ship** until **Context Layer** runs the **same** retrieval code as verification. **Index reuse** remains **latency-only**. **Next hard requirement:** run Context Layer from **repo** `PYTHONPATH` at **documented commit** (or rebuild wheel) and **re-verify** §B table.

---

## Addendum — Plugin Phase-1 truth proof (orthogonal)

**JetBrains plugin Phase-1 truth proof** (S1–S8, backend ↔ plugin-visible copy) is **locked** under `docs/validation/PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md` with frozen artifacts in `docs/validation/artifacts/plugin_phase1_truth_proof/`. This **does not** revise the HTTP usefulness table above; it is a **separate** Stage 2 closure surface documented in `docs/LIVE_ROADMAP_TRACKER.md` **§6.22**.

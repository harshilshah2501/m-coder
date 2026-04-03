# Ground truth capture — usefulness failure modes (AIOps MVP pack)

## Provenance

| Field | Value |
|-------|--------|
| Batch summary | `summary/run_summary.json` / `run_summary.md` — **2026-04-03T11:33:30Z** |
| Automated mix | **1 PASS / 7 PARTIAL / 0 FAIL** |
| Artifact root (this capture) | `/home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp` (WSL may use `~/Stage-4-Artifacts/aiops_mvp`) |
| Per-scenario inputs | `scenario_<ID>/export_response.json`, `scenario_<ID>/ask_response.json`, `summary/run_summary.json` |

**Metadata note:** Captured `ask_response.json` files **predate** Plan-Gate build **`218ebca`** (no `metadata.operator_hints` / `metadata.usefulness_metrics` in HTTP JSON). **`operator_hints`** and **`usefulness_metrics`** below are **recomputed** from `export_response.json` with the same code as v1 ingest. After you deploy **`218ebca`+**, rerun and copy those fields from **`ask_response.json`** for an apples-to-apples **before/after** row (verdict mix should still match §3).

**Regenerate machine columns:**

```bash
cd "$M_CODER_ROOT" && export PYTHONPATH=.
python3 scripts/capture_usefulness_ground_truth.py /path/to/aiops_mvp
```

---

## 1) What to expect — observability-only vs real usefulness fix

### After rerunning with **218ebca** (diagnostics only)

You **should** see:

| Expect | Why |
|--------|-----|
| **Same PASS / PARTIAL / FAIL mix** (or extremely close) | Verdict logic still keys off `metadata.evidence_quality`; gate thresholds unchanged. |
| **Richer diagnosis** | `operator_hints` + `usefulness_metrics` on `ask_response.metadata` (when Plan-Gate includes **`218ebca`**). |
| **Clearer proof of weakness** | Explicit reasons + bundle stats without guessing from logs. |

You **should not** expect (if only **`218ebca`** shipped):

| Do not expect | Why |
|---------------|-----|
| Better **ranking** or **top-k** composition | No retrieval/ranking changes. |
| Better **snippets** or anchor **choice** | No snippet pipeline changes. |
| Fewer **`LOW_CORE_RATIO`** (or materially stronger **evidence_quality**) | Quality gate rules unchanged. |
| Stronger **plan text** by itself | Same planner/model inputs from evidence. |

**If** PASS mix, core ratio, or snippet bodies jump a lot after a release labeled “observability only,” **inspect carefully** — that would indicate unintended behavior drift or a different Motadata index / `top_k` / service version.

### After a future **usefulness hardening** commit

Then you **may** expect: fewer weak signals, better snippets, improved automated mix — tracked against this document as **before** baseline.

---

## 2) Compact diagnostic table (baseline — pre‑218ebca HTTP metadata)

Use this as the **before** row for the **real usefulness fix**. Columns match the rubric: verdict, quality, reasons, **core ratio** (`dominance_metrics.core_code_in_top_k_pct`), whether the **first visible snippet** helps an engineer, and a short **human** read.

| Scenario | Verdict | Quality | Reasons | Top core ratio | First snippet useful? | Human note |
| -------- | ------: | ------- | ------- | -------------: | --------------------- | ---------- |
| A1 | PARTIAL | WEAK | LOW_CORE_RATIO | 0.25 | No | **Looks diluted** — core paths exist in top-k, but gate says weak mix; rank-0 snippet is header only. |
| A2 | PASS | STRONG | QUERY_TOO_GENERIC | 0.25 | Weak | **Looks fake-strong** — machine PASS is permissive; snippet still copyright header, not impressive. |
| D1 | PARTIAL | WEAK | LOW_CORE_RATIO | 0.25 | No | **Looks diluted** — duplicate-incident hypothesis not visible in first snippet. |
| D2 | PARTIAL | WEAK | LOW_CORE_RATIO | 0.1667 | No | **Looks diluted** — ambiguity honesty may be OK in plan text; snippet still uninformative. |
| P1 | PARTIAL | WEAK | LOW_CORE_RATIO | 0.25 | No | **Looks diluted** — correlation-id plan not grounded by visible code in snippet. |
| P2 | PARTIAL | WEAK | LOW_CORE_RATIO | 0.1667 | No | **Looks diluted** — rank-0 legal-warning block is especially poor for “inspect code.” |
| C1 | PARTIAL | WEAK | LOW_CORE_RATIO | 0.1667 | No | **Looks diluted** — patch suggestion not supported by visible implementation text. |
| C2 | PARTIAL | WEAK | LOW_CORE_RATIO | 0.25 | No | **Looks diluted** — test skeleton narrative not reflected in first snippet. |

**Legend — human note vocabulary:** **looks useful** = first window shows domain logic you’d act on; **looks diluted** = paths may be plausible but snippet/core signal feels weak; **looks fake-strong** = machine STRONG/PASS feels stronger than what evidence + snippet show.

---

## 3) Full record per scenario (8)

Fields: **`automated_verdict`** · **`evidence_quality`** · **`quality_reasons`** · **`operator_hints`** (recomputed) · **`usefulness_metrics`** (recomputed) · **top 3 paths** · **first visible snippet** · **header vs body** · **human note**

For every scenario whose only gate reason is **`LOW_CORE_RATIO`**, **`operator_hints`** recomputes to the same sentence:

> Fewer than 30% of retrieved paths are classified as core AIOps packages (e.g. com/mindarray/aiops). Relevant modules may still appear but are diluted by broad support files.

### A1

| Field | Value |
|-------|--------|
| `automated_verdict` | `PARTIAL` |
| `evidence_quality` | `WEAK` |
| `quality_reasons` | `["LOW_CORE_RATIO"]` |
| `operator_hints` | *(LOW_CORE_RATIO — full text in intro above)* |
| `usefulness_metrics` | `{"entry_count":12,"top1_retrieval_score":2232,"retrieval_score_min":1389,"retrieval_score_max":2232,"retrieval_score_spread":843,"snippet_anchor_hits":12,"snippet_non_anchor_hits":0,"file_class_counts":{"supporting_prod_code":9,"core_aiops_code":3},"noise_class_entry_count":0}` |
| Top 3 paths | `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java`, `motadata/src/main/java/com/mindarray/api/APIServer.java`, `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` |
| First visible snippet text | `/*` + Copyright (c) Motadata 2025 … “This source code is the property of Motadata…” (truncated in bundle) |
| Snippet: header/boilerplate vs body logic | **Header / boilerplate** |
| Human note | **Looks diluted** |

### A2

| Field | Value |
|-------|--------|
| `automated_verdict` | `PASS` |
| `evidence_quality` | `STRONG` |
| `quality_reasons` | `["QUERY_TOO_GENERIC"]` |
| `operator_hints` | Generic-intent classification: STRONG does not imply pinpoint engineering grounding. |
| `usefulness_metrics` | `{"entry_count":12,"top1_retrieval_score":428,"retrieval_score_min":240,"retrieval_score_max":428,"retrieval_score_spread":188,"snippet_anchor_hits":12,"snippet_non_anchor_hits":0,"file_class_counts":{"core_aiops_code":3,"supporting_prod_code":9},"noise_class_entry_count":0}` |
| Top 3 paths | `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java`, `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java`, `motadata/src/main/java/com/mindarray/aiops/DependencyManager.java` |
| First visible snippet text | Copyright block at file head (same pattern as A1 rank-0) |
| Snippet: header/boilerplate vs body logic | **Header / boilerplate** |
| Human note | **Looks fake-strong** |

### D1

| Field | Value |
|-------|--------|
| `automated_verdict` | `PARTIAL` |
| `evidence_quality` | `WEAK` |
| `quality_reasons` | `["LOW_CORE_RATIO"]` |
| `operator_hints` | *(same LOW_CORE_RATIO block as §3 intro)* |
| `usefulness_metrics` | `{"entry_count":12,"top1_retrieval_score":4053,"retrieval_score_min":1863,"retrieval_score_max":4053,"retrieval_score_spread":2190,"snippet_anchor_hits":12,"snippet_non_anchor_hits":0,"file_class_counts":{"supporting_prod_code":9,"core_aiops_code":3},"noise_class_entry_count":0}` |
| Top 3 paths | `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java`, `motadata/src/main/java/com/mindarray/nms/ObjectManager.java`, `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` |
| First visible snippet text | Copyright + proprietary / confidential notice |
| Snippet: header/boilerplate vs body logic | **Header / boilerplate** |
| Human note | **Looks diluted** |

### D2

| Field | Value |
|-------|--------|
| `automated_verdict` | `PARTIAL` |
| `evidence_quality` | `WEAK` |
| `quality_reasons` | `["LOW_CORE_RATIO"]` |
| `operator_hints` | *(same LOW_CORE_RATIO block as §3 intro)* |
| `usefulness_metrics` | `{"entry_count":12,"top1_retrieval_score":2804,"retrieval_score_min":1749,"retrieval_score_max":2804,"retrieval_score_spread":1055,"snippet_anchor_hits":12,"snippet_non_anchor_hits":0,"file_class_counts":{"supporting_prod_code":10,"core_aiops_code":2},"noise_class_entry_count":0}` |
| Top 3 paths | `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java`, `motadata/src/main/java/com/mindarray/nms/DiscoveryEngine.java`, `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` |
| First visible snippet text | Copyright + proprietary / confidential notice |
| Snippet: header/boilerplate vs body logic | **Header / boilerplate** |
| Human note | **Looks diluted** |

### P1

| Field | Value |
|-------|--------|
| `automated_verdict` | `PARTIAL` |
| `evidence_quality` | `WEAK` |
| `quality_reasons` | `["LOW_CORE_RATIO"]` |
| `operator_hints` | *(same LOW_CORE_RATIO block as §3 intro)* |
| `usefulness_metrics` | `{"entry_count":12,"top1_retrieval_score":1202,"retrieval_score_min":262,"retrieval_score_max":1202,"retrieval_score_spread":940,"snippet_anchor_hits":12,"snippet_non_anchor_hits":0,"file_class_counts":{"core_aiops_code":3,"supporting_prod_code":9},"noise_class_entry_count":0}` |
| Top 3 paths | `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java`, `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java`, `motadata/src/main/java/com/mindarray/api/AIOpsObject.java` |
| First visible snippet text | Copyright + proprietary / confidential notice |
| Snippet: header/boilerplate vs body logic | **Header / boilerplate** |
| Human note | **Looks diluted** |

### P2

| Field | Value |
|-------|--------|
| `automated_verdict` | `PARTIAL` |
| `evidence_quality` | `WEAK` |
| `quality_reasons` | `["LOW_CORE_RATIO"]` |
| `operator_hints` | *(same LOW_CORE_RATIO block as §3 intro)* |
| `usefulness_metrics` | `{"entry_count":12,"top1_retrieval_score":744,"retrieval_score_min":415,"retrieval_score_max":744,"retrieval_score_spread":329,"snippet_anchor_hits":12,"snippet_non_anchor_hits":0,"file_class_counts":{"supporting_prod_code":10,"core_aiops_code":2},"noise_class_entry_count":0}` |
| Top 3 paths | `motadata/src/main/java/com/mindarray/nms/ObjectManager.java`, `motadata/src/main/java/com/mindarray/api/APIServer.java`, `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` |
| First visible snippet text | Legal / unauthorized-use / “AS IS” warranty block |
| Snippet: header/boilerplate vs body logic | **Header / boilerplate** (legal banner, not implementation) |
| Human note | **Looks diluted** |

### C1

| Field | Value |
|-------|--------|
| `automated_verdict` | `PARTIAL` |
| `evidence_quality` | `WEAK` |
| `quality_reasons` | `["LOW_CORE_RATIO"]` |
| `operator_hints` | *(same LOW_CORE_RATIO block as §3 intro)* |
| `usefulness_metrics` | `{"entry_count":12,"top1_retrieval_score":1102,"retrieval_score_min":613,"retrieval_score_max":1102,"retrieval_score_spread":489,"snippet_anchor_hits":12,"snippet_non_anchor_hits":0,"file_class_counts":{"supporting_prod_code":10,"core_aiops_code":2},"noise_class_entry_count":0}` |
| Top 3 paths | `motadata/src/main/java/com/mindarray/api/APIServer.java`, `motadata/src/main/java/com/mindarray/cache/PolicyCacheServiceImpl.java`, `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` |
| First visible snippet text | Copyright + proprietary / confidential notice |
| Snippet: header/boilerplate vs body logic | **Header / boilerplate** |
| Human note | **Looks diluted** |

### C2

| Field | Value |
|-------|--------|
| `automated_verdict` | `PARTIAL` |
| `evidence_quality` | `WEAK` |
| `quality_reasons` | `["LOW_CORE_RATIO"]` |
| `operator_hints` | *(same LOW_CORE_RATIO block as §3 intro)* |
| `usefulness_metrics` | `{"entry_count":12,"top1_retrieval_score":2796,"retrieval_score_min":1464,"retrieval_score_max":2796,"retrieval_score_spread":1332,"snippet_anchor_hits":12,"snippet_non_anchor_hits":0,"file_class_counts":{"supporting_prod_code":9,"core_aiops_code":3},"noise_class_entry_count":0}` |
| Top 3 paths | `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java`, `motadata/src/main/java/com/mindarray/api/APIServer.java`, `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` |
| First visible snippet text | Copyright + proprietary / confidential notice |
| Snippet: header/boilerplate vs body logic | **Header / boilerplate** |
| Human note | **Looks diluted** |

---

## 4) Cross-scenario themes (failure modes)

1. **`LOW_CORE_RATIO`** on **7/8** runs; **A2** only **`QUERY_TOO_GENERIC`** with **STRONG** + machine **PASS**.
2. **`core_code_in_top_k_pct`** stays **0.1667–0.25** — core files exist in bundle but **not** enough share for the gate on code-like intents.
3. **All 12** entries use **`query_token_substring_anchor`** → **12 / 0** anchor vs non-anchor; the issue is **content**, not missing anchors.
4. **First visible window** is almost always **copyright / legal / license** text — **not** body logic — so operators see **diluted** or **fake-strong** (A2) reads despite plausible paths.

---

## 5) After rerun — blank before/after template (paste row)

Copy for the next capture (e.g. post–**218ebca** Plan-Gate or post–usefulness fix):

| Scenario | Verdict | Quality | Reasons | Top core ratio | First snippet useful? | Human note |
| -------- | ------: | ------- | ------- | -------------: | --------------------- | ---------- |
| A1 | | | | | | |
| A2 | | | | | | |
| D1 | | | | | | |
| D2 | | | | | | |
| P1 | | | | | | |
| P2 | | | | | | |
| C1 | | | | | | |
| C2 | | | | | | |

---

## 6) How this feeds the next hardening commit

Use **§2** + **§3** as the **labeled “before”** for ranking/snippet work; use **§5** to record **after** without conflating **diagnostic-only** releases with **retrieval** changes.

Related: `docs/validation/AIOPS_MVP_SCENARIO_PACK.md` §2.7 (`metadata.operator_hints`, `metadata.usefulness_metrics`).

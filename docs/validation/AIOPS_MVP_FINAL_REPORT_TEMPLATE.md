# AIOps MVP Final Report — filled snapshot (2026-04-06)

> **Template reuse:** For a new batch, copy this file, replace header + §2–6 with the new `run_summary.json` and artifacts. Canonical queries: `docs/validation/aiops_mvp_scenarios.v1.json` (`top_k_default`: **12**).

**Closure baseline:** **1 PASS / 7 PARTIAL** — see `docs/validation/MVP_PRODUCTION_CLOSURE_NOTE.md` and `LOW_CORE_RATIO_DECISION.md` §B.

---

## 1) Header

| Field | Value |
|-------|--------|
| **Date** | 2026-04-06 |
| **Batch `generated_utc`** | **2026-04-06T10:21:00Z** |
| **Repo path** | `/home/harshil/Harshil-PoCs/m-coder` |
| **Branch** | `feature/phase-4-product-authority` |
| **Commit** | `4711ee4` |
| **Motadata root (locked)** | `/home/harshil/Projects/Motadata` |
| **Context Layer** | `http://127.0.0.1:8091` |
| **Plan-Gate** | `http://127.0.0.1:8089` |
| **HTTP timeout (batch)** | 7200 s |

---

## 2) Execution Summary

| Metric | Value |
|--------|--------|
| Total scenarios planned | 8 |
| Total scenarios run | 8 |
| PASS | **1** |
| PARTIAL | **7** |
| FAIL | **0** |
| ERROR | **0** |
| Artifact pack complete | **Yes** |
| Machine summary | `docs/validation/artifacts/aiops_mvp/summary/run_summary.json` |
| Human-readable summary | `docs/validation/artifacts/aiops_mvp/summary/run_summary.md` |

---

## 3) Per-Scenario Results

Queries from `aiops_mvp_scenarios.v1.json`. Verdicts from `run_summary.json` (`automated_verdict`, `evidence_quality`, `quality_reasons`).

### A1 (ASK)

- **Query:** In the Motadata repo, where does alert correlation logic likely live, and which modules appear involved in deriving correlation keys from incoming events?
- **Result:** **PARTIAL**
- **Evidence quality:** WEAK
- **Plan-Gate `quality_reasons`:** `LOW_CORE_RATIO`
- **HTTP export top-12:** 3 `core_aiops_code`; local `assess_evidence_quality` matches gate (WEAK; LOW_CORE_RATIO).
- **Artifacts:** `docs/validation/artifacts/aiops_mvp/scenario_A1/` (`export_response.json`, `ask_response.json`)

### A2 (ASK)

- **Query:** Compare likely data flow across ingestion, normalization, and incident creation for high-cardinality alerts, and cite which files appear relevant.
- **Result:** **PASS**
- **Evidence quality:** STRONG
- **Plan-Gate `quality_reasons`:** `QUERY_TOO_GENERIC` (not LOW_CORE_RATIO)
- **HTTP export top-12:** 3 `core_aiops_code`; gate STRONG.
- **Artifacts:** `docs/validation/artifacts/aiops_mvp/scenario_A2/`

### D1 (DEBUG)

- **Query:** Debug hypothesis: duplicate incidents are created for repeated alerts. Based on repo evidence, where are likely duplication guards implemented and what failure points should be checked first?
- **Result:** **PARTIAL**
- **Evidence quality:** WEAK; **`LOW_CORE_RATIO`**
- **HTTP export top-12:** 3 cores.
- **Artifacts:** `docs/validation/artifacts/aiops_mvp/scenario_D1/`

### D2 (DEBUG)

- **Query:** I suspect a timezone mismatch in alert windowing, but I do not know the responsible module. Identify likely areas and state what evidence is missing before concluding.
- **Result:** **PARTIAL**
- **Evidence quality:** WEAK; **`LOW_CORE_RATIO`**
- **HTTP export top-12:** 2 cores.
- **Artifacts:** `docs/validation/artifacts/aiops_mvp/scenario_D2/`

### P1 (PLAN)

- **Query:** Propose a minimal, low-risk plan to add traceable correlation-id propagation from ingest to incident records, with rollback and validation steps.
- **Result:** **PARTIAL**
- **Evidence quality:** WEAK; **`LOW_CORE_RATIO`**
- **HTTP export top-12:** 3 cores.
- **Artifacts:** `docs/validation/artifacts/aiops_mvp/scenario_P1/`

### P2 (PLAN)

- **Query:** Provide a plan to improve noisy-alert suppression logic while preserving current critical alert pathways; identify likely files to inspect first.
- **Result:** **PARTIAL**
- **Evidence quality:** WEAK; **`LOW_CORE_RATIO`**
- **HTTP export top-12:** 2 cores.
- **Artifacts:** `docs/validation/artifacts/aiops_mvp/scenario_P2/`

### C1 (CODE)

- **Query:** Suggest a safe, non-executed patch snippet to add guardrail logging around correlation decision branches, and point to likely insertion points from evidence.
- **Result:** **PARTIAL**
- **Evidence quality:** WEAK; **`LOW_CORE_RATIO`**
- **HTTP export top-12:** 2 cores.
- **Artifacts:** `docs/validation/artifacts/aiops_mvp/scenario_C1/`

### C2 (CODE)

- **Query:** Provide a minimal test skeleton to validate duplicate-incident prevention logic, grounded in likely existing test structure and related modules.
- **Result:** **PARTIAL**
- **Evidence quality:** WEAK; **`LOW_CORE_RATIO`**
- **HTTP export top-12:** 3 cores.
- **Artifacts:** `docs/validation/artifacts/aiops_mvp/scenario_C2/`

---

## 4) Cross-Scenario Findings

### Strongest scenarios

- **A2** — only automated **PASS**; STRONG evidence quality; gate cites **`QUERY_TOO_GENERIC`** instead of **`LOW_CORE_RATIO`**.

### Weakest scenarios

- **Seven** scenarios share **WEAK** + **`LOW_CORE_RATIO`** per Plan-Gate metadata, consistent with **2–3** `core_aiops_code` paths in HTTP top-12 (below ≥4 / 30% bar).

### Common failure patterns

- **`LOW_CORE_RATIO`** dominates engineering scenarios on **HTTP** exports for this run.
- **Strict engineering bar** (no LOW_CORE_RATIO, core_count ≥ 4) — **not met** on HTTP artifacts; see **`LOW_CORE_RATIO_DECISION.md` §B–C**.

### Failure classification

| Class | Notes |
|-------|--------|
| Retrieval-related | HTTP top-12 core density vs gate — **primary** automated story for this batch. |
| Grounding-related | Aligned with export paths used by Plan-Gate. |
| Deployment / parity | In-repo pool can differ from **running** Context Layer — **§C** decision doc. |

---

## 5) MVP Verdict

**Selected:** **MVP demo ready with caveats** (**B**)

**Rationale:**

- End-to-end chain **works** (HTTP 200, artifacts written, `run_summary` complete).
- Automated usefulness bar: **1/8 PASS**; **7/8** **WEAK** with **`LOW_CORE_RATIO`** on HTTP — not reinterpreted; documented as **known limitation** until Context Layer matches repo proof (**`MVP_PRODUCTION_CLOSURE_NOTE.md`**).
- Stage 3 / index reuse address **latency**, not this usefulness ratio.

---

## 6) Artifact Index

| Path | Role |
|------|------|
| `docs/validation/artifacts/aiops_mvp/summary/run_summary.json` | Machine counts + per-scenario metadata |
| `docs/validation/artifacts/aiops_mvp/summary/run_summary.md` | Human-readable batch summary |
| `docs/validation/artifacts/aiops_mvp/scenario_*/` | Per-scenario `export_response.json`, `ask_response.json` |
| `docs/validation/LOW_CORE_RATIO_DECISION.md` | HTTP vs proof — authoritative |
| `docs/validation/AIOPS_MVP_USEFULNESS_GROUND_TRUTH_CAPTURE.md` | Baseline + **§2.1** post-sync table |

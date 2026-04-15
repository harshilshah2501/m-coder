# PROGRAM_STATE_SNAPSHOT — portable continuity

**Status tags:** `CANONICAL` · `IN_PRODUCT_SLICE`  
**Last updated:** 2026-04-14  
**Detail & evidence IDs:** `docs/LIVE_ROADMAP_TRACKER.md` (this file stays short)

---

## Locked / completed (do not reopen without explicit charter change)

- Stage 2 retrieval + trust alignment → **LOCKED**
- PR-6 retrieval baseline → **LOCKED**
- `layer5.evidence_bundle.v1` contract → **LOCKED**
- Layer-1 Governance → **LOCKED**
- Layer-2 Compilation → **COMPLETE / LOCKED**
- Layer-3 runtime core M3.0–M3.11 → **COMPLETE** (per tracker)
- L5.8 grounded Ask harness + closure gate → **COMPLETE** (B2)
- B1 retrieval generalization program → **CLOSED** (tracker; residual warnings non-blocking)
- B3 plugin truthfulness MVP bar → **CLOSED**; Phase-1 truth proof → **LOCKED**
- B4 observability / trace reconstruction → **CLOSED**
- B5 host readiness (WSL + native Linux placements) → **CLOSED**
- B6 compatibility path hardening (L5.9) → **CLOSED**
- B7 Stage 3 burn-in / acceptance → **CLOSED** (pytest + smokes; IDE E2E to Stage3 loop = follow-on)
- Action 14 final acceptance → **PASS**

---

## Current active work (high level)

- **Post-closure convergence:** controlled expansion from closed baseline; no reopened MVP gates without tracker amendment
- **Retrieval:** baseline preservation + regression protection under L5-RET framing (not PR-6 reopen)
- **Operational follow-through:** log packaging, CI hygiene, runbook maintenance (non-blocking)

---

## Immediate next work (ordered)

1. Use **CLI/HTTP proof** (`docs/CLI_VALIDATION_MATRIX.md`) for regressions; **do not** require JetBrains UI for routine validation unless milestone says so  
2. **Product wiring** of `Stage3LoopController` where planned — **separate** from burn-in closure (tracker)  
3. Residual UX/docs items under §B3 checklist as **secondary** (not MVP gate reopen)

---

## Explicitly deferred (do not treat as open gates)

- Embeddings / semantic retrieval as authority gate
- Neo4j / graph DB
- LangGraph / external orchestration frameworks
- LLM reranking
- Uncontrolled agent loops
- **JetBrains UI** as the **default** proof surface for this program line (CLI-first until reopened)

---

## Architecture truth (one paragraph)

Workspace-side **Context Layer** (WSL or Linux) exports **versioned evidence**; **Plan-Gate + vLLM** run on **GPU**; **runtime** owns validation, execution honesty, and bounded loops; **IDE/plugin** is a thin client — **validation for this phase is HTTP/CLI-first.**

---

## Session rule

If a session goal is “what is true / what is closed,” read **`docs/LIVE_ROADMAP_TRACKER.md`** first, then **`docs/SYSTEM_TRUTH.md`**. Do not re-derive closure from narrative handbooks alone.

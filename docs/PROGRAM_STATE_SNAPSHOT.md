# PROGRAM_STATE_SNAPSHOT — portable continuity

**Status tags:** `CANONICAL` · `IN_PRODUCT_SLICE`  
**Last updated:** 2026-04-18  
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

- **Lane discipline:** split workstreams and keep only one active engineering lane at a time.
- **Retrieval baseline:** anchored authority-gated retrieval is locked as working baseline; formal behavior snapshot promoted (see below).
- **Latest closure:** **Ask v1 evidence quality parity** (`108aabb`) merged to **`main`** — **`POST /v1/ask`** passes grounding + authority into **`assess_evidence_quality`**; promoted baseline in **`docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5**. **Narrative:** **`docs/validation/MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md`**.
- **Active engineering lane:** maintain promoted baseline; optional charters only with explicit scope (see tracker §1.4).

---

## Immediate next work (this week)

**Single entry point:** **`docs/validation/POST_CLOSURE_MAINTENANCE.md`** — operational lock on **`motadata_behavior_verify.py`** (same workspace, scenarios, policy, Stage A); save **`CANDIDATE.*.json`** when tuning; cite **§5** + SHA for regressions; **closure todos 01–09 are done** — this file is the **post-closure / optional-charter** checklist, not open MVP gates; **no architecture churn** by default; next big moves → **explicit charter** (tracker **§1.4**: debug depth **CHARTER-TBD**, **§B1 / L5-RET** with §5 guardrails).

**Regression pair (formal):** **`docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5** + named artifact + m-coder SHA **`108aabb098017b8c551629c745d71f63acf7`** (local copy often under `runtime/.run/`).

**Hardening invariants to preserve:** Authority Expansion Hardening v1 — noise-class suppression for code-oriented Stage A (`db-files/*`, `test-plugin-metrics/*`); **`owner_injected_lane_count >= 1`** on anchored / authority scenarios where applicable.

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

For **Motadata behavior verification** claims (evidence quality labels, broad vs anchored): use **`docs/validation/MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md`** + **`docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5**, not ad-hoc “broad = WEAK” shorthand from older runs.

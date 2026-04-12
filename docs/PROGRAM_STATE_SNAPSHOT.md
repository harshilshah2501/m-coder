# PROGRAM STATE SNAPSHOT — m-coder

Last Updated: 2026-04-02

**Canonical roadmap detail:** `docs/LIVE_ROADMAP_TRACKER.md` (this snapshot stays short; tracker owns milestone IDs and evidence pointers).

---

## ✅ WHAT IS LOCKED (DO NOT REOPEN)

- Stage 2 — Retrieval + Trust + Action Alignment → COMPLETE / LOCKED
- PR-6 retrieval baseline → LOCKED
- Deterministic retrieval → LOCKED
- Evidence bundle contract (`layer5.evidence_bundle.v1`) → LOCKED
- Layer-1 Governance → LOCKED
- Layer-2 Compilation → COMPLETE / LOCKED
- Layer-3 Runtime Core (M3.0–M3.11) → COMPLETE
- Architecture boundaries → LOCKED
- **L5.8 — grounded Ask validation harness + closure gate** → COMPLETE (tracker **B2**, **§6.19a**)
- **Action 4 / 5 / 11** (plugin truthfulness, L5-OBS-1 HTTP, L5.9 path hardening) → CLOSED — tracker **§6.17–§6.19** (residual non-closure checklist items stay under tracker **§B3** / ops only)

---

## ⚙️ CURRENT ACTIVE WORK

Stage 3 — Controlled Runtime Loop (Hybrid Model)

**Implementation status:** In-repo (**schemas, validators, state machine, loop controller, executor, ledger, tests** — see tracker **§6.20**). **Current phase:** **burn-in / validation / product integration**, not greenfield implementation (tracker **§B7**).

Goal:

- Runtime-owned reasoning loop (bounded, schema-driven)

Not allowed:

- agent autonomy
- LLM-controlled loops

Invariant:

- All model outputs are untrusted until runtime validation passes

---

## 🔧 CURRENT TASKS (IN PROGRESS)

- **§B1 / L5-RET** — retrieval generalization and expanded validation depth (Stage 2 reliability program; harness closure remains **locked**)
- **Stage 3 loop** — burn-in, WSL/GPU governed-slice checks, integration acceptance — `docs/guides/STAGE3_BURN_IN_AND_E2E_DEMO.md`
- **L5-OBS-1** — HTTP path **closed**; any follow-through = operational logging / CI collection only (not a reopened Action 5)
- **Plugin** — Action **4** **closed**; remaining gaps = tracker **§B3** / **§1.3** gates, not a reopened truthfulness project

---

## ⏭️ NEXT TASKS (ORDERED)

1. Stage 3 loop **burn-in completion** and **governed vertical slice** acceptance (pytest + operator runbook)
2. **Direct product wiring** of `Stage3LoopController` where planned (separate milestone — not implied by burn-in alone)
3. **§B1** expanded goldens / drift thresholds toward **Action 14** / deployment trust
4. Host-profile and release sign-off per tracker

---

## 🚫 EXPLICITLY DEFERRED (DO NOT TOUCH)

- embeddings / semantic retrieval
- Neo4j / graph DB
- LangGraph / orchestration frameworks
- LLM reranking
- uncontrolled agent loops

---

## 🧠 ARCHITECTURE TRUTH

- WSL → source of code truth
- Context Layer → workspace-local
- GPU → Plan-Gate + vLLM
- Runtime → control + state + governance
- Plugin → thin client

---

## 🎯 DEFINITION OF SUCCESS (CURRENT PHASE)

System must be:

- deterministic
- truthful
- grounded in evidence
- capable of bounded reasoning (not autonomous agents)
- **Stage 3 loop:** burn-in and integration evidence **without** claiming full product-path acceptance until wiring milestone is met (tracker **§B7**)

# PRODUCT_SLICE — current production slice (m-coder)

**Status tags:** `CANONICAL` (scope boundary) · **aligned with** `docs/PRODUCT_SLICE_CHARTER.md` (contracts) · **interpretation for validation:** CLI/HTTP-first  

**Last updated:** 2026-04-14  

This document is the **Layer-5 + Layer-3 product boundary** for what must be proven in the current slice: **Context Layer / evidence** (L5) and **governed Plan-Gate APIs** (L3). The **four-layer constitutional core** is defined in `docs/ARCHITECTURE_4_LAYER.md` and `docs/MASTER_SYSTEM_SPEC.md`.

---

## 0. Validation stance (this pass)

| Surface | Product slice role | Active validation for *this documentation / proof pass* |
|---------|-------------------|---------------------------------------------------------|
| **Plan-Gate + Context Layer + Ask/Execute over HTTP** | **IN_PRODUCT_SLICE** | **YES — CLI-first / runtime-first** |
| **JetBrains plugin / IDE UI** | **IN_PRODUCT_SLICE** as shipped client for some deployments | **PARKED** as **active** closure surface — treat as **`DEFERRED_INTEGRATION`** for proof criteria until explicitly reopened |

**Non-contradiction note:** `PRODUCT_SLICE_CHARTER.md` still lists the plugin in the component table (historical product truth). **This file tightens:** ongoing **regression and closure evidence** are **CLI/HTTP/script** unless a milestone explicitly restores IDE acceptance gates.

**Plugin vs roadmap (no logical conflict):** `docs/LIVE_ROADMAP_TRACKER.md` records **plugin / Ask truthfulness closures** (e.g. B3, Action 4) as **artifact-backed CLOSED**. **This slice** still **parks the IDE as a blocking CI/regression gate** in favor of **CLI-first** proof. That is a **process and gate priority** distinction: **logic validated and locked** in the tracker; **UI automation** not required for every pass until explicitly reopened.

---

## 1. In scope now (critical path)

| Area | Role | Paths / entry (representative) |
|------|------|--------------------------------|
| **Governed HTTP API** | Plan, Ask v0/v1, Execute | `runtime/plan_gate_service/app.py` |
| **Ask service** | Plan-only / Explain-Debug routing | `runtime/ask_service/` |
| **Context + evidence** | Export, indexing, Layer-5 retrieval | `runtime/context_layer_service/`, `runtime/layer5/`, `packaging/motadata-context-layer/` |
| **Execute path** | Honest outcome (executed / blocked / refused) | `runtime/execute_service/` via Plan-Gate |
| **GPU stack** | vLLM for Explain/Debug | `runtime/scripts/governed_services.sh`, `runtime/config/demo_stack.env` |
| **Observability** | Request/trace correlation | Per B4 closure in tracker; grep-stable logs (see `docs/guides/ACTION_5_OBSERVABILITY_CORRELATION.md`) |
| **Host profiles** | WSL vs native Linux workspace backend | `docs/validation/B5_HOST_READINESS.md` |
| **Stage 3 loop (runtime)** | Bounded loop **implementation** + burn-in | `runtime/loop/`, `docs/validation/STAGE3_BURN_IN_REPORT.md` |

---

## 2. Out of scope now (still in repo, not the slice’s proof burden)

| Area | Tag | Notes |
|------|-----|-------|
| `archive/legacy_runtime_rag/` as **product** path to JetBrains | `OUT_OF_PRODUCT_SLICE` | Parallel stack; not wired as primary bridge (audit) |
| `ml/` training pipelines | `OUT_OF_PRODUCT_SLICE` | Separate ML product line for slice |
| `archive/workspace_intelligence/spikes/` | `ARCHIVE` | Historical research |
| **Semantic embedding retrieval as release gate** | `OUT_OF_PRODUCT_SLICE` (gate) | Charter: lexical MVP + PR-6 baseline; Track C later |
| **JetBrains UI acceptance** as **required** regression | `DEFERRED_INTEGRATION` | Use CLI matrix instead for this pass |

---

## 3. Critical vs secondary (within slice)

| Priority | What | Why |
|----------|------|-----|
| **Critical** | HTTP contracts (v0/v1 Ask, evidence bundle, execute honesty), deterministic retrieval baseline (PR-6), trace reconstruction | Tracker-recorded closure gates |
| **Critical** | Host-mode documentation + reproducible scripts | B5 |
| **Secondary** | Spool artifact parity, demo polish, non-blocking latency warnings | Tracker allows warnings without gate reopen |
| **Secondary** | IDE copy defects (e.g. residual `plan_summary.notes` visibility on all surfaces) | Tracker §B3 residual / ops |

---

## 4. Deferred (explicit)

| Item | Tag |
|------|-----|
| Plugin/UI golden demos as **blocking** CI | `DEFERRED_INTEGRATION` |
| Live IDE → Stage3LoopController E2E | **Follow-on** (tracker, STAGE3 burn-in runbook §7) |
| Assist influence on retrieval inputs | **NOT ENABLED** (by design) — see `docs/LIVE_ROADMAP_TRACKER.md` §1.5; Assist v1 is **implemented + advisory-only**, not runtime authority |
| Embeddings, graph DB, LangGraph | `DEFERRED` per program snapshot |

---

## 5. Frozen / versioned contracts (slice)

- `ask_request.v0.1`, `ask_request.v1.0` — `runtime/ide/schemas/`
- `layer5.evidence_bundle.v1`
- Plan-Gate: `/v0/plan`, `/v0/ask`, `/v1/ask`, `/v0/execute` + health/version

---

## 6. Canonical references

| Document | Use |
|----------|-----|
| `docs/MASTER_SYSTEM_SPEC.md` | **Sole canonical** architecture entry; hierarchy of truth |
| `docs/PRODUCT_SLICE_CHARTER.md` | Full contract tables, host modes A/B, observability requirements |
| `docs/LIVE_ROADMAP_TRACKER.md` | What is **closed** vs follow-on |
| `docs/guides/MOTADATA_VERIFICATION_GUIDE.md` | **Active** CLI verification runbook |

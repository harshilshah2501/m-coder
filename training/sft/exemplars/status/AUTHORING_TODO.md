# SFT Golden Exemplars — Authoring TODO (Phase‑1)

**Context**: Engineering-first assistant operating on PRs, tests, code reviews, CI/CD, and releases. See [GROUNDING_TRANSFORMATION_REFERENCE.md](../../guides/GROUNDING_TRANSFORMATION_REFERENCE.md) for artifact mappings.

**Objective**: Create and lock the first **30 golden exemplars** with solid DNA before any variants or scaling.

This is a **manual, thinking-heavy phase**. No automation. No shortcuts.

**Re-Grounding Status** (Jan 2026): First 5 exemplars re-grounded for engineering context. CONF-01/02 pending re-grounding.

---

## Target Breakdown (Locked)

| Category | Count | Status |
|--------|------|--------|
| RCA | 5 | ☐ |
| Anomaly | 5 | ☐ |
| Config / Change | 5 | ☐ |
| Refusal / Safety | 5 | ☐ |
| Design & Planning | 5 | ☐ |
| Mixed / Ugly Edge Cases | 5 | ☐ |

**Total**: 30 exemplars

---

## Global Acceptance Criteria (Applies to ALL 30)

Every exemplar must:
- Explicitly declare all **6 essential fields**
- Pass the **Reviewer Checklist (one‑page)**
- Survive at least **one mental mutation**
- Be grounded in **real or highly plausible production pain**

If any condition fails → revise or discard.

---

## 1️⃣ RCA Exemplars (5)

✅ RCA‑01 — Test failures, misleading symptoms (baseline exemplar) — **Locked**
✅ RCA‑02 — Real bug hidden by assumption mismatch — **Locked**
☐ RCA‑03 — Dependency change causing cascading test failures
☐ RCA‑04 — CI configuration issue masquerading as code failure
☐ RCA‑05 — Refactoring tool worsened a bug

Goal: Train diagnostic thinking under ambiguity and pressure (engineering context).

---

## 2️⃣ Anomaly Exemplars (5)

✅ ANOM‑01 — Test anomaly with delayed CI feedback — **Locked**
✅ ANOM‑02 — Performance regression misclassified as functional bug — **Locked**
☐ ANOM‑03 — Seasonal test pattern misclassified as anomaly
☐ ANOM‑04 — Flaky test confidence collapse (insufficient runs)
☐ ANOM‑05 — Conflicting test signals across CI environments

Goal: Train epistemic humility and uncertainty handling (engineering context).

---

## 3️⃣ Config / Change Exemplars (5)

☐ CONF‑01 — API change requested during code freeze **[Requires re-grounding]**
☐ CONF‑02 — Config change with high blast radius (multi-repo impact) **[Requires re-grounding]**
☐ CONF‑03 — Test config change under release pressure
☐ CONF‑04 — Refactor rollback vs forward-fix decision
☐ CONF‑05 — Partial code ownership (reviewer authority constraint)

Goal: Train risk‑aware decision making (engineering context).

---

## 4️⃣ Refusal / Safety Exemplars (5)

✅ REF‑01 — Missing evidence, unsafe to approve change — **Locked**
☐ REF‑02 — Insufficient permissions to merge (ownership violation)
☐ REF‑03 — Code generation request violates safety policy
☐ REF‑04 — User demands merge without review
☐ REF‑05 — Conflicting reviewer opinions (authority conflict)

Goal: Train explicit, calm, justified refusal (engineering context).

---

## 5️⃣ Design & Planning Exemplars (5)

☐ DES‑01 — Greenfield feature with unclear scale assumptions
☐ DES‑02 — Incremental API enhancement with backward compatibility
☐ DES‑03 — Module migration / refactor planning
☐ DES‑04 — Performance & scale planning under uncertainty
☐ DES‑05 — Risk-heavy design (breaking changes / data migration)

Goal: Train architectural thinking and staged planning (engineering context).

---

## 6️⃣ Mixed / Ugly Edge Case Exemplars (5)

☐ MIX‑01 — RCA + ownership conflict (unclear code owner)
☐ MIX‑02 — Test anomaly + release panic (deadline pressure)
☐ MIX‑03 — Config change + automation feedback loop (CI broken by change)
☐ MIX‑04 — Design request during production regression
☐ MIX‑05 — Partial test coverage + partial ownership + time pressure

Goal: Train compositional reasoning across layers (engineering context).

---

## Authoring Order (Recommended)

1. Finish **RCA‑01 → RCA‑03** first
2. Write **REF‑01** early (sets safety tone)
3. Alternate between categories to avoid bias
4. Leave **Mixed** exemplars for last

---

## Phase Exit Criteria (Do NOT move forward unless all true)

☐ All 30 exemplars written
☐ All 30 pass reviewer checklist
☐ At least 10 exemplars were revised after mutation
☐ Team agrees on “this feels like senior‑engineer thinking”

Only after this → Variant generation phase.

---

**Status**: Phase‑1 / Exemplar Authoring


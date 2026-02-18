# Phase-6 Dataset Freeze Readiness Checklist

## Purpose

Preconditions that must be satisfied **before** dataset freeze and SFT. All items are criteria to be verified; no exemplar generation or phase rebalancing is performed in this checklist.

---

## 1. Phase Balance Threshold

| Criterion | Requirement | Verification |
|-----------|-------------|--------------|
| Minimum REF count | ≥ 3 base exemplars | Count REF in Phase-3 summary (BASE-015, BASE-016, BASE-017). |
| Minimum CONF count | ≥ 10 base exemplars | Count CONF in Phase-3 summary. |
| Minimum DES count | ≥ 2 base exemplars | Count DES in Phase-3 summary (BASE-005, BASE-012). |
| MIX present | ≥ 1 base exemplar | BASE-013. |
| CODE present | ≥ 1 base exemplar | BASE-014. |
| Phase balance lock | No rebalance | Do not add/remove bases to satisfy distribution; current 17 bases are locked. |

**Pass condition:** Phase distribution matches Phase-3 summary and no rebalancing has been applied.

---

## 2. Mutation Stress Coverage Threshold

| Criterion | Requirement | Verification |
|-----------|-------------|--------------|
| Mutation types covered | All 6 mutation classes from Phase-6 taxonomy | Ledger `mutation_coverage` has entries for authority, irreversibility, ambiguity, pressure, collapse, boundary_relocation. |
| Per-phase mutation cases | At least N cases per phase (configurable; e.g. N ≥ 2) | Ledger `phase_coverage[phase].total_cases` ≥ N for REF, CONF, DES, MIX, CODE. |
| Stress coverage threshold | Minimum pass rate (e.g. ≥ 95%) or explicit waiver | Ledger aggregate pass rate across mutation cases meets threshold or waiver documented. |

**Pass condition:** Ledger shows full mutation-type coverage and per-phase case counts and pass rate meet configured thresholds.

---

## 3. Boundary Invariance Lock

| Criterion | Requirement | Verification |
|-----------|-------------|--------------|
| Boundary phrase exact | No change to boundary text in Phase-3/Phase-4 | No edits to PHASE3 or PHASE4; boundary strings match Phase-3 exactly in all variants. |
| Relocation attempts failed | Boundary relocation mutation cases result in preserved boundary | Ledger `guard_coverage.boundary_anchors` shows no accepted relocation/softening; `collapse_vector_flags.boundary_relocation.collapse_prevented === true` when tested. |
| Anchors locked | Governance: boundary anchors cannot be relocated | Constitutional Manifest §5 Locked Constraints satisfied. |

**Pass condition:** No boundary edits in corpus; ledger shows boundary preservation under relocation attempts.

---

## 4. Validation Summary Consistency

| Criterion | Requirement | Verification |
|-----------|-------------|--------------|
| Phase-3 validation | All base exemplars PASS | Phase-3 validation summary: all REF/CONF/DES/MIX/CODE validations PASS. |
| Phase-4 validation | All variants PASS | Phase-4 variant summary: boundary exact, phase stable, no softened language. |
| Phase-5 stability | All bases/variants STABLE | Phase-5 stability table: all rows STABLE. |
| Phase-6 ledger | Ledger schema valid and complete | Ledger JSON validates against mutation_ledger.schema.json; required fields present. |
| Cross-doc consistency | Base IDs and phase labels align | Phase-3 base list = Phase-4 base list = Phase-5 base list; phase labels match Constitutional Manifest. |

**Pass condition:** Phase-3, Phase-4, Phase-5 summaries and Phase-6 ledger are consistent; no conflicting base IDs or phase labels.

---

## 5. Freeze Decision Gate

| Step | Action |
|------|--------|
| 1 | Run Phase-6 harness (mutation case generator + harness run) to produce ledger. |
| 2 | Execute this checklist: phase balance, mutation stress coverage, boundary invariance, validation consistency. |
| 3 | If all pass: **Dataset freeze approved**; proceed to SFT dataset compilation. |
| 4 | If any fail: Document failure; fix (e.g. add mutation cases, fix harness) and re-run; do not freeze until checklist passes. |

---

## 6. Checklist Summary Table

| # | Criterion | Pass / Fail | Notes |
|---|-----------|------------|-------|
| 1 | Phase balance threshold | ☐ | No rebalance; 17 bases, distribution as Phase-3. |
| 2 | Mutation stress coverage threshold | ☐ | Ledger coverage and pass rate meet config. |
| 3 | Boundary invariance lock | ☐ | No boundary edits; relocation attempts failed. |
| 4 | Validation summary consistency | ☐ | Phase-3/4/5/6 aligned and valid. |
| 5 | Freeze decision | ☐ | Freeze approved only when 1–4 pass. |

---

**Strict mode:** This checklist does not authorize new exemplar generation, phase rebalancing, or modification of Phase-3 or Phase-4 files.

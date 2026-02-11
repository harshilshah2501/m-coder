# SFT Golden Exemplars — Phase-1 Authoring Checklist (Updated)

## Context

**Engineering-First Assistant**: Exemplars operate on engineering artifacts (PRs, tests, code reviews, CI/CD, releases) rather than operations (alerts, incidents, on-call). Judgment DNA is identical—only the surface changes.

**Reference**: See [GROUNDING_TRANSFORMATION_REFERENCE.md](../../guides/GROUNDING_TRANSFORMATION_REFERENCE.md) for complete ops→engineering mappings.

## Objective

Create and lock the first **30 golden exemplars** with strong reasoning structure (**B.R.A.I.N**) and enforced behavioral discipline (**D.N.A**), before any automation or scaling.

This is a **manual, thinking-heavy phase**. No shortcuts.

---

## Target Breakdown (Locked)

| Category                | Count | Status |
| ----------------------- | ----- | ------ |
| RCA                     | 5     | ☐      |
| Anomaly                 | 5     | ☐      |
| Config / Change         | 5     | ☐      |
| Refusal / Safety        | 5     | ☐      |
| Design & Planning       | 5     | ☐      |
| Mixed / Ugly Edge Cases | 5     | ☐      |

**Total**: 30 exemplars

---

## Global Acceptance Criteria (Applies to ALL 30)

Every exemplar must:

- Explicitly declare all **B.R.A.I.N sections**
- Include required **D.N.A gates** (see below)
- Respect **DNA-Gate sequencing** (Uncertainty precedes any action)
- Pass the **Reviewer Checklist**
- Survive at least **one mental mutation**
- Be grounded in **real or highly plausible production pain**

If any condition fails → revise or discard.

---

## B.R.A.I.N Structure (Required)

```
B — Baseline
R — Observed Reality
A — Signal / Classification
I — Potential Impact

--- DNA-U-GATE ---
[Uncertainty Statement]
------------------

N — Next Sensible Actions
```

---

## D.N.A Gates (Behavioral Invariants)

> **Sequencing Invariant (Non‑Negotiable)**
>
> **DNA‑U‑GATE must appear before any Next Actions, recommendations, escalation, or execution language.**
>
> Action without acknowledged uncertainty is considered unsafe.

**DNA-Gates are mandatory behavioral control points.** They constrain *how* the model reasons and acts.

**DNA-Gates are mandatory behavioral control points.** They constrain *how* the model reasons and acts.

### DNA-U-GATE — Uncertainty (Mandatory)

- Must appear **before any Next Actions**
- Explicitly states epistemic limits
- No reassurance, no minimization

**Reviewer checks:**

```
☐ DNA-U-GATE present before actions
☐ Cause explicitly stated as unknown or unconfirmed
☐ No action verbs appear before the gate
```

---

### DNA-R-GATE — Refusal (When Applicable)

- Required when action is unsafe, invalid, or unauthorized
- Must precede alternatives or explanations

---

### DNA-S-GATE — Safety (When Applicable)

- Required for config, automation, deletion, or high-blast-radius decisions
- Must explicitly acknowledge risk boundaries

---

## Category-Specific Notes

### RCA Exemplars

- DNA-U-GATE required before investigation steps
- Hypotheses must be framed as *candidates*, not conclusions

### Anomaly Exemplars

- Detection must precede diagnosis
- Temporal or data ambiguity must be explicit

### Config / Change Exemplars

- DNA-S-GATE often required
- Risk framing mandatory before decision

### Refusal Exemplars

- DNA-R-GATE is the core structure
- Alternatives (if any) come *after* refusal

### Mixed Exemplars

- Multiple DNA-Gates may be required
- Ordering discipline is critical under pressure

---

## Current Progress Snapshot

**Re-grounded for Engineering-First Context (Jan 2026)**:
- ✅ RCA‑01 — Locked (test failures with misleading symptoms)
- ✅ RCA‑02 — Locked (assumption mismatch causing bug)
- ✅ ANOM‑01 — Locked (test anomaly with delayed CI feedback)
- ✅ ANOM‑02 — Locked (performance regression misclassified as functional bug)
- ✅ REF‑01 — Locked (refusal to approve change due to insufficient evidence)

**Note**: First 5 exemplars successfully re-grounded from ops to engineering artifacts. CONF-01 and CONF-02 require re-grounding before Phase-2 scaling.

---

## Remaining Authoring Sequence (Agreed)

1. **ANOM‑02** — Log pattern deviation after deployment
2. **ANOM‑03** — Seasonal pattern misclassified as anomaly
3. **ANOM‑04** — Anomaly confidence collapse (model unsure)
4. **ANOM‑05** — Conflicting anomaly signals across metrics
5. **RCA‑03 → RCA‑05** — Cascading, ingestion‑masked, automation‑worsened incidents
6. **REF‑02 → REF‑05** — Authority, policy, evidence, and role conflicts
7. **CONF‑01 → CONF‑05** — High‑blast‑radius config & change decisions
8. **DES‑01 → DES‑05** — Design & planning under uncertainty
9. **MIX‑01 → MIX‑05** — Compositional, high‑pressure edge cases

---

## Phase Exit Criteria

☐ All 30 exemplars written  
☐ All 30 pass reviewer checklist  
☐ At least 10 exemplars revised after mutation  
☐ Team agrees: "this feels like senior‑engineer thinking"

Only after this → Variant generation phase.


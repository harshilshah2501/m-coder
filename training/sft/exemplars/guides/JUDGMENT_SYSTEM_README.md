# Judgment Documentation — Read This First

This directory defines how judgment is authored, validated, reviewed, and eventually enforced in AI systems.

---

## Authority Order (Non-Negotiable)

1. **Golden Exemplars — Complete Production Guide v1.5**
   - Defines judgment, refusal, irreversibility, and phases
   - This is the constitutional source of truth
   - File: `Golden_Exemplars_Guide_v1.5.md`

2. **Reviewer Pack v1.0**
   - Defines how humans adversarially review exemplars
   - Must conform strictly to the Production Guide
   - Files: `Reviewer_Pack_v1.0_README.md`, `Golden Exemplars — External Review Handout.md`, `reviewer_walkthrough_how_to_review_one_exemplar.md`, `Phase_5_6_Reviewer_Addendum.md`, `Reviewer_Scoring_Rubric.md`

3. **Judgment-Governed Architecture**
   - Defines system-level enforcement and runtime invariants
   - File: `Judgement_Governed_Architecture.md`

No other document may redefine judgment semantics.

---

## Where to Start

**Choose your path based on your role:**

### If you are AUTHORING exemplars
→ **Start here:** `Golden_Exemplars_Guide_v1.5.md`

This is the complete manufacturing specification. Read sections 1-8 for foundational understanding, then proceed phase-by-phase (Phases 1-6).

**Key sections:**
- Section 1-3: Core concepts (What, Why, Essential Fields)
- Section 6-7: B.R.A.I.N method and D.N.A validation
- Section 8: Manual authoring workflow
- Section 11: Quality gates and review checklist

---

### If you are REVIEWING exemplars
→ **Start here:** `Reviewer_Pack_v1.0_README.md`

This pack provides everything needed to review exemplars for judgment integrity.

**Quick path:**
1. Read `Golden Exemplars — External Review Handout.md` (5 min)
2. Read `reviewer_walkthrough_how_to_review_one_exemplar.md` (10 min)
3. Review 1-2 exemplars using the checklist
4. If reviewing Phase-5/6, read `Phase_5_6_Reviewer_Addendum.md`

---

### If you are BUILDING systems
→ **Start here:** `Judgement_Governed_Architecture.md`

This document defines system-level invariants and runtime enforcement.

**Then read:**
- `Golden_Exemplars_Guide_v1.5.md` (Sections 1-3 for context)
- Appendix E & F (DPO usage policies)

---

## Conflict Resolution Rule

**If two documents disagree, the Production Guide always wins.**

The authority hierarchy is:
```
Golden Exemplars Production Guide v1.5 (Constitutional)
    ↓
All other documents (Subordinate)
```

---

## Document Integration Map

```
JUDGMENT CONSTITUTION
├── Golden_Exemplars_Guide_v1.5.md
│   └── Defines: Phases, boundaries, B.R.A.I.N, D.N.A, refusal semantics
│
HUMAN ENFORCEMENT
├── Reviewer Pack v1.0
│   ├── Reviewer_Pack_v1.0_README.md (Navigation)
│   ├── Golden Exemplars — External Review Handout.md (Orientation)
│   ├── reviewer_walkthrough_how_to_review_one_exemplar.md (Process)
│   ├── Phase_5_6_Reviewer_Addendum.md (Specialized guidance)
│   └── Reviewer_Scoring_Rubric.md (Quantitative tracking)
│
SYSTEM ENFORCEMENT
└── Judgement_Governed_Architecture.md
    └── Defines: Runtime invariants, memory ≠ authority, system gates
```

---

## Version Compatibility Matrix

| Production Guide | Reviewer Pack | Architecture | Status |
|------------------|---------------|--------------|--------|
| v1.5 | v1.0 | v1.0 | ✅ Current |

**Compatibility rule:** Reviewer Pack versions must always declare which Production Guide version they target.

---

## Future Documents (Not Yet Implemented)

The following documents are referenced in planning but not yet created:

- **Sanitation Pipeline Specification** — Hygiene ruleset and automated content cleaning
- **Training Pipeline Specification** — Automated SFT dataset construction and validation
- **Judgment Validation Harness** — Three-layer validation system (pre/post-training)
- **Dataset Integration Guide** — How to integrate Dataset A/B/C with controlled mixing

These will be added as subordinate documents and will not alter judgment semantics.

---

## Critical Principles (Lock These)

1. **Judgment is authoritative. Memory is not.**
   - Retrieval, history, and prior success never grant permission.

2. **Irreversibility defines phases, not features.**
   - Once unilateral rollback is lost, judgment must stop or defer.

3. **Refusal is a correct outcome.**
   - Safety is defined by stopping, not by progress.

4. **Training is downstream of judgment.**
   - Models learn restraint only after humans freeze it.

5. **If no exemplar applies, the system must refuse.**
   - Absence of judgment is not permission.

---

## Quick Reference: Core Concepts

### The 6 Phases

| Phase | Purpose | What It Must Do | What It Must Not Do |
|-------|---------|-----------------|---------------------|
| Phase-1 (REF) | Refusal & classification | Stop unsafe or illegitimate action | Allow progress |
| Phase-2 (CONF) | Conditional allowance | Permit progress until irreversible boundary | Cross the boundary |
| Phase-3 (DES) | Design reasoning | Explore assumptions and trade-offs | Decide or recommend |
| Phase-4 (MIX) | Judgment collision | Resolve which phase dominates | Invent new semantics |
| Phase-5 (CODE) | Judgment encoding | Encode judgment into code safely | Redefine judgment |
| Phase-6 (ADV) | Judgment endurance | Stress judgment under time/scale/coordination | Introduce new behavior |

### B.R.A.I.N Method (Authoring)

- **B** — Boundary First
- **R** — Reality-Anchored Situation
- **A** — Ambiguity Injection
- **I** — Intent Resolution
- **N** — Narrative Reasoning

### D.N.A Validation (Quality)

- **D** — Decomposition (≥4 reusable reasoning blocks)
- **N** — Negative Capability (stable terminal state)
- **A** — Adversarial Swap (mutation without collapse)

---

## Support & Questions

**Owner:** Harshil Shah  
**Program:** Golden Exemplars — Motadata AI Training  
**Status:** Active — Phase-5 READY

For questions about:
- **Judgment semantics** → Refer to Production Guide
- **Review process** → Refer to Reviewer Pack
- **System integration** → Refer to Architecture doc

---

**End of Entry Point**

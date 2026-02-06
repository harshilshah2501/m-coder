# Gate Terminology Clarification

**Date**: January 21, 2026  
**Purpose**: Eliminate confusion between "9 gates" and "3 D.N.A gates"

---

## The Two Gate Systems

### **9 Comprehensive Review Criteria** (Full Checklist)

These are the **complete peer review criteria** from [REVIEW_CHECKLIST.md](REVIEW_CHECKLIST.md):

| # | Criterion | What It Checks |
|---|-----------|----------------|
| 0 | Identity & Scope | Unique ID, category, grounded scenario |
| 1 | Five-Layer DNA Declaration | B.R.A.I.N structure (Boundary, Reality, Ambiguity, Intent, Narrative) |
| 2 | Reasoning Quality | Multiple hypotheses, explicit rejection, uncertainty stated |
| 3 | Constraint Awareness & Safety | Permissions respected, no hallucinated authority, business risk acknowledged |
| 4 | Response Posture Alignment | Output matches confidence, conditional recommendations, explained deferrals |
| 5 | D.N.A Validation | **→ Contains the 3 core D.N.A gates (see below)** |
| 6 | Architecture Coverage | Maps to ≥1 stress surface (Ingestion, Analytics, Alerting, etc.) |
| 7 | Generalizability | Applies to similar but unseen cases, survives layer swaps |
| 8 | Final Acceptance | All gates passed, strengthens corpus, no redundant overlap |

---

### **3 D.N.A Validation Gates** (Core Quality Bar)

These are the **3 mandatory, non-negotiable tests** embedded in Criterion 5:

| Gate | Name | What It Tests | Pass Criteria |
|------|------|---------------|---------------|
| **6-D** | **Decomposition** | Can reasoning be broken into atomic, reusable blocks? | ≥4 independent diagnostic steps, each testable |
| **6-N** | **Negative Capability** | Can the model refuse/defer safely without false confidence? | Explicit "I don't know yet"; no hallucinated certainty |
| **6-A** | **Adversarial Swap** | Does reasoning survive when constraints change (authority/evidence/risk/timing)? | Correct posture shift when ambiguity/authority/risk/intent mutates |

**These 3 gates are the minimum bar for exemplar quality.** If any D.N.A gate fails, the exemplar is rejected regardless of other criteria.

---

## Relationship Between the Two Systems

```
┌─────────────────────────────────────────────────────────┐
│  9 Comprehensive Review Criteria (Full Checklist)      │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Criteria 0-4: Structure, reasoning, constraints   │ │
│  ├───────────────────────────────────────────────────┤ │
│  │ Criterion 5: D.N.A Validation ← THE 3 CORE GATES  │ │
│  │   ├─ Gate 6-D: Decomposition                      │ │
│  │   ├─ Gate 6-N: Negative Capability                │ │
│  │   └─ Gate 6-A: Adversarial Swap                   │ │
│  ├───────────────────────────────────────────────────┤ │
│  │ Criteria 6-8: Coverage, generalization, final OK  │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Key Insight**: D.N.A gates are **embedded within** the 9 comprehensive review criteria. They're not separate—they're a critical subset.

---

## Updated Terminology

| Old (Ambiguous) | New (Clear) | Meaning |
|-----------------|-------------|---------|
| "9-gate checklist" | **9 comprehensive review criteria** | Full peer review checklist (Criteria 0-8) |
| "D.N.A validation" | **3 D.N.A validation gates** | Core quality bar (Gates 6-D, 6-N, 6-A within Criterion 5) |
| "Pass all gates" | **Pass all 9 criteria (including 3 D.N.A gates)** | Complete acceptance requirement |

---

## When to Use Which

| Context | Use This Term | Example |
|---------|---------------|---------|
| Peer review | "9 comprehensive review criteria" | "This exemplar must pass all 9 criteria before locking" |
| Core quality | "3 D.N.A validation gates" | "The exemplar failed Gate 6-N (Negative Capability)" |
| Mutation testing | "D.N.A gates" or "Adversarial Swap" | "We're running D.N.A validation on all locked exemplars" |
| Team communication | Both (with clarification) | "Pass all 9 review criteria, especially the 3 D.N.A gates" |

---

## Quick Reference

**Question**: "Does this exemplar need to pass 9 gates or 3 gates?"  
**Answer**: **Both**. It must pass all 9 comprehensive review criteria, and within those, the 3 D.N.A gates (Criterion 5) are mandatory and non-negotiable.

**Question**: "What's the minimum bar?"  
**Answer**: **3 D.N.A gates** (Decomposition, Negative Capability, Adversarial Swap). If these fail, reject immediately.

**Question**: "What's the complete acceptance requirement?"  
**Answer**: **All 9 comprehensive review criteria**, including the 3 D.N.A gates.

---

## Implementation Notes

- **REVIEW_CHECKLIST.md** now explicitly labels Gate 6 as "The 3 Core Gates" with sub-sections 6-D, 6-N, 6-A
- All documentation updated to use consistent terminology: "9 comprehensive review criteria (including 3 D.N.A gates)"
- No functional change—just terminology clarity to eliminate confusion

---

## References

- **Full checklist**: [REVIEW_CHECKLIST.md](REVIEW_CHECKLIST.md)
- **Framework guide**: [EXEMPLAR_AUTHORING_GUIDE.md](EXEMPLAR_AUTHORING_GUIDE.md)
- **B.R.A.I.N → D.N.A framework**: [SFT_FRAMEWORK.md](../../docs/SFT_FRAMEWORK.md)

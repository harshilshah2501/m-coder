# Golden Exemplars — Reviewer Pack v1.0

**Status:** Production Ready  
**Version:** 1.0  
**Last Updated:** 2026-02-05

---

## Scope & Authority (Critical)

**This pack does not define judgment semantics.**

It applies the semantics defined in the **Golden Exemplars — Complete Production Guide v1.5**.

**Version Compatibility:**  
Reviewer Pack v1.0 is compatible with Production Guide v1.5.

**Authority hierarchy:**
- Production Guide defines **what judgment is** (constitutional authority)
- This Reviewer Pack defines **how humans validate judgment** (subordinate authority)

If any conflict exists between documents, the Production Guide always wins.

---

## Purpose

This pack provides everything needed to review Golden Exemplars for **judgment integrity** under uncertainty.

Reviewers evaluate whether exemplars correctly **stop, defer, or bound action** — not whether they propose good solutions.

---

## What's Included

This pack contains 4 integrated documents:

### 1️⃣ **External Review Handout** (Start Here)
**File:** `Golden Exemplars — External Review Handout.md`

**Purpose:** Executive overview for external reviewers  
**Read time:** 5 minutes  
**Use when:** First-time reviewer orientation

**Key sections:**
- Phase semantics (6 phases)
- Architecture invariants (memory ≠ authority)
- What reviewers should/shouldn't do
- Quick reviewer checklist

---

### 2️⃣ **Reviewer Walkthrough**
**File:** `reviewer_walkthrough_how_to_review_one_exemplar.md`

**Purpose:** Step-by-step example of reviewing one exemplar  
**Read time:** 10 minutes  
**Use when:** Learning the review process hands-on

**Key sections:**
- Step −1: Authority & Memory Check (mandatory)
- Step 0-5: Complete review workflow
- Common reviewer traps
- Examples of good vs bad feedback

**Scope note:** Demonstrates Phase-2 (CONF) review. Review posture differs by phase.

---

### 3️⃣ **Phase-5 & Phase-6 Addendum**
**File:** `Phase_5_6_Reviewer_Addendum.md`

**Purpose:** Specialized guidance for coding & endurance phases  
**Read time:** 5 minutes  
**Use when:** Reviewing Phase-5 (CODE) or Phase-6 (ADV) exemplars

**Key sections:**
- Phase-5: Judgment encoding in code
- Phase-6: Judgment endurance over time
- Automatic fail conditions for both phases
- Reviewer north star (boring = stable)

---

### 4️⃣ **Reviewer Scoring Rubric** (This Document)
**File:** `Reviewer_Scoring_Rubric.md`

**Purpose:** Quantitative agreement tracking  
**Read time:** 3 minutes  
**Use when:** Calibrating multiple reviewers or tracking review quality

**Key sections:**
- 4-point scoring system per check
- Inter-reviewer agreement metrics
- Calibration workflow

---

## Quick Start Guide

### For First-Time Reviewers

1. Read **External Review Handout** (5 min)
2. Read **Reviewer Walkthrough** (10 min)
3. Review 1-2 exemplars using the checklist
4. If reviewing Phase-5/6, read the **Addendum**

**Total onboarding time:** ~15-20 minutes

---

### For Experienced Reviewers

1. Use the **Quick Reviewer Checklist** (in External Review Handout)
2. Apply **Step −1: Authority & Memory Check** (mandatory)
3. Consult **Phase-5/6 Addendum** if needed
4. Submit feedback using required format

---

## Review Philosophy

### What Reviewers ARE

- **Adversarial testers** of judgment containment
- **Boundary validators** under pressure
- **Misuse pattern detectors**

### What Reviewers ARE NOT

- Solution architects
- Design consultants
- Execution optimizers

---

## Core Principles

### 1. Memory ≠ Authority

Memory, prior success, retrieved context, or historical precedent **never grant permission**.

Only Golden Exemplars define what is allowed.

### 2. Phase Discipline

Each phase does exactly one thing. Exemplars that cross phase boundaries are structurally invalid.

### 3. Negative Capability

Correct exemplars often **refuse or defer**. This is success, not failure.

### 4. Boring = Stable

If an exemplar feels overly restrictive or repetitive, that's usually correct. Judgment stability > helpfulness.

---

## Expected Review Outcomes

### Typical Review Load

- **2-3 exemplars** are sufficient to assess corpus integrity
- If those hold, the rest are likely consistent

### Useful Feedback Sounds Like

- "I don't like the outcome, but I can't break the boundary."
- "This would stop me from doing something stupid under pressure."
- "This could be misused if someone redefines 'exposure' to include only power users."

### Not-Useful Feedback Sounds Like

- "In my experience, gradual rollouts are fine."
- "I would approach this differently."
- "Couldn't we just...?"

---

## Integration with Production Guide

This Reviewer Pack supports the **Golden Exemplars — Complete Production Guide v1.5**.

### Document Relationships

```
Golden Exemplars Guide v1.5
    ↓ defines
Judgment Manufacturing Process
    ↓ produces
LOCKED Exemplars
    ↓ reviewed by
Reviewer Pack v1.0 (this pack)
    ↓ validates
Judgment Integrity
    ↓ flows to
SFT Dataset → Model Training
```

---

## Calibration Workflow

For teams with multiple reviewers:

1. **Anchor Session** (30 min)
   - All reviewers review same 2 exemplars
   - Compare scores using rubric
   - Discuss disagreements

2. **Independent Review** (ongoing)
   - Each reviewer works independently
   - Track agreement metrics
   - Flag outliers for re-calibration

3. **Periodic Re-sync** (monthly)
   - Review scoring drift
   - Update reviewer guidance if needed

---

## Support Documents

This pack references:

- **Golden_Exemplars_Guide_v1.5.md** — Authoritative production guide
- **Judgement_Governed_Architecture.md** — System-level invariants
- **REVIEW_CHECKLIST.md** — Detailed authoring hygiene checklist

---

## Version History

### v1.0 (2026-02-05)
- Initial release
- 6-phase coverage (REF, CONF, DES, MIX, CODE, ADV)
- Authority & Memory Check (Step −1) added
- Phase-5/6 specialized guidance included
- Scoring rubric integrated

---

## Quick Reference Card

### 4-Question Review

1. **Misuse Test** — Can someone push past this safely or unsafely?
2. **Boundary Test** — Can you point to the exact stop line?
3. **Pressure Test** — Does it still stop under urgency or authority?
4. **Phase Purity Test** — Is it doing only what its phase allows?

If all four pass → exemplar is sound.

### Automatic Fail Conditions

- Permission from memory/precedent
- Ambiguous boundaries
- Execution under uncertainty
- Phase boundary crossing
- "Pilot" / "monitor and proceed" language

---

## Contact & Feedback

**Owner:** Harshil Shah  
**Program:** Golden Exemplars — Motadata AI Training  
**Status:** Active — Phase-5 READY

For questions about this pack or the review process, refer to the Golden Exemplars Guide v1.5, Section 12: How to Review (Engineering Lens).

---

**End of Reviewer Pack v1.0 README**

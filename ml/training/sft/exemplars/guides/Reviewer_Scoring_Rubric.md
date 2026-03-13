# Reviewer Scoring Rubric — Golden Exemplars

**Purpose:** Quantitative agreement tracking and calibration for multi-reviewer workflows

**Version:** 1.0 (Reviewer Pack v1.0, compatible with Production Guide v1.5)  
**Status:** Production Ready

**Scope:** This document does not define judgment semantics. It applies the semantics defined in the Golden Exemplars — Complete Production Guide v1.5.

---

## Overview

This rubric provides a **4-point scoring system** for each review check, enabling:

- Inter-reviewer agreement measurement
- Calibration session tracking
- Identification of exemplars needing revision
- Quality assurance for judgment validation

---

## How to Use This Rubric

1. **Apply the 4-question review** (from External Review Handout)
2. **Score each question** using the scale below
3. **Record scores** in the tracking template
4. **Calculate agreement metrics** across reviewers

---

## Scoring Scale (Per Question)

Each review question receives a score from **0-3**:

| Score | Meaning | Interpretation |
|-------|---------|----------------|
| **3** | **Pass** | No concerns. Boundary holds under all tested pressures. |
| **2** | **Pass with Minor Note** | Generally sound, but noted a potential edge case or ambiguity that doesn't invalidate the core boundary. |
| **1** | **Concern** | Identified a misuse path or pressure scenario that could compromise the boundary. Requires author review. |
| **0** | **Fail** | Structural flaw. Boundary is broken, phase is violated, or authority is unclear. Must be rejected. |

---

## The 4 Review Questions

### Question 1: Misuse Test

**Prompt:** "Can someone push past this safely or unsafely?"

**3 (Pass):** No viable misuse path. To violate the boundary, you'd have to ignore explicit constraints.

**2 (Pass w/ Note):** Minor ambiguity in wording could be misinterpreted, but core boundary remains intact.

**1 (Concern):** Found a plausible misuse scenario (e.g., redefining a key term, exploiting implicit assumptions).

**0 (Fail):** Multiple easy misuse paths. Boundary is effectively optional.

---

### Question 2: Boundary Test

**Prompt:** "Can you point to the exact stop line?"

**3 (Pass):** Irreversible boundary is explicit, named, and concrete.

**2 (Pass w/ Note):** Boundary is clear but could benefit from more specific language (e.g., "merge to main" vs "merge").

**1 (Concern):** Boundary is implied or described circumstantially. Hard to pinpoint exactly when it's crossed.

**0 (Fail):** No clear boundary, or boundary is based on outcomes/signals rather than actions.

---

### Question 3: Pressure Test

**Prompt:** "Does it still stop under urgency or authority?"

**3 (Pass):** Boundary holds under time pressure, authority override attempts, and high-confidence scenarios.

**2 (Pass w/ Note):** Holds under most pressure, but language could be misread as softening under specific authority.

**1 (Concern):** Exemplar includes conditional language ("unless leadership approves," "if urgent") that weakens boundary.

**0 (Fail):** Boundary explicitly or implicitly relaxes under pressure. Execution bias is present.

---

### Question 4: Phase Purity Test

**Prompt:** "Is it doing only what its phase allows?"

**3 (Pass):** Exemplar performs exactly one phase function. No cross-phase leakage.

**2 (Pass w/ Note):** Primarily correct, but includes minor language that hints at another phase (e.g., slight recommendation tone in a DES exemplar).

**1 (Concern):** Exemplar crosses into another phase's territory (e.g., CONF exemplar decides, REF exemplar reasons hypothetically).

**0 (Fail):** Clear phase violation. Exemplar does something forbidden by its phase definition.

---

## Aggregate Scoring

### Per Exemplar

**Total Score:** Sum of 4 questions (max 12)

| Total Score | Interpretation | Action |
|-------------|----------------|--------|
| **12** | Perfect pass | LOCK approved |
| **10-11** | Strong pass | LOCK approved with minor notes |
| **8-9** | Weak pass | Author review recommended |
| **6-7** | Concerns | Return to author for revision |
| **0-5** | Fail | Reject. Restart from Essential Fields |

---

### Inter-Reviewer Agreement

For multi-reviewer calibration:

**Agreement Metric:** Calculate **mean absolute deviation (MAD)** per question.

```
MAD = Σ|reviewer_score - mean_score| / number_of_reviewers
```

**Interpretation:**

| MAD | Agreement Quality | Action |
|-----|-------------------|--------|
| **0.0 - 0.3** | Strong agreement | Reviewers are calibrated |
| **0.4 - 0.6** | Moderate agreement | Discuss outliers in calibration session |
| **0.7 - 1.0** | Weak agreement | Re-calibration required |
| **> 1.0** | Poor agreement | Review rubric understanding; exemplar may be ambiguous |

---

## Tracking Template

Use this template for review sessions:

```markdown
## Exemplar Review — [Exemplar ID]

**Reviewers:** [Names]  
**Date:** [YYYY-MM-DD]  
**Phase:** [REF / CONF / DES / MIX / CODE / ADV]

| Reviewer | Q1: Misuse | Q2: Boundary | Q3: Pressure | Q4: Phase Purity | Total | Notes |
|----------|------------|--------------|--------------|------------------|-------|-------|
| Rev A    | 3          | 3            | 2            | 3                | 11    | Minor wording note on pressure language |
| Rev B    | 3          | 2            | 3            | 3                | 11    | Boundary could be more specific |
| Rev C    | 3          | 3            | 3            | 3                | 12    | No concerns |

**Mean Score:** 11.3  
**MAD:** 0.22 (Strong agreement)

**Decision:** LOCK APPROVED

**Flagged Issues:** None (minor notes only)
```

---

## Calibration Session Workflow

### 1. Anchor Session (First Time)

**Goal:** Establish baseline reviewer alignment

**Steps:**

1. Select **2 exemplars** (1 strong, 1 borderline)
2. All reviewers score independently
3. Compare scores using tracking template
4. Discuss any score > 1 point deviation
5. Reach consensus on scoring interpretation

**Duration:** 30 minutes

---

### 2. Independent Review (Ongoing)

**Goal:** Validate exemplars at scale

**Steps:**

1. Assign **2-3 reviewers per exemplar** (random or round-robin)
2. Each reviewer scores independently
3. Log scores in tracking sheet
4. Flag exemplars with MAD > 0.6 for discussion

**Cadence:** Per exemplar release (ongoing)

---

### 3. Periodic Re-sync (Monthly)

**Goal:** Maintain long-term calibration

**Steps:**

1. Review **inter-reviewer agreement trends**
2. Identify systematic drift (e.g., one reviewer consistently softer/harder)
3. Re-review 1-2 exemplars together
4. Update rubric or guidance if needed

**Duration:** 15 minutes

---

## Failure Mode Detection

This rubric helps detect two critical failure modes:

### Reviewer Drift

**Symptom:** One reviewer's scores consistently diverge from group mean

**Detection:** Track per-reviewer MAD over time

**Resolution:** 1-on-1 calibration session with rubric walkthrough

---

### Exemplar Ambiguity

**Symptom:** High MAD across all reviewers on a specific exemplar

**Detection:** MAD > 1.0 on any question

**Resolution:** Exemplar likely has structural ambiguity. Return to author for clarification.

---

## Special Cases

### Step −1 (Authority & Memory Check)

This is a **binary gate**, not scored 0-3:

- ✅ **PASS:** No permission from memory/precedent/norms
- ❌ **FAIL:** Any authority derived from historical context → immediate rejection

**If Step −1 fails, do not proceed with the 4-question scoring.**

---

### Phase-5 & Phase-6 Adjustments

For **Phase-5 (CODE)** and **Phase-6 (ADV)** exemplars:

- Consult the **Phase-5/6 Reviewer Addendum** before scoring
- Apply the same 4 questions, but interpret through phase-specific lens:
  - **Phase-5:** Does code fail safe? Are guardrails before logic?
  - **Phase-6:** Does judgment decay over time/scale?

Automatic fail conditions from the addendum override scoring.

---

## Reviewer Training Checklist

Before using this rubric, reviewers must:

- [ ] Read **External Review Handout** (5 min)
- [ ] Complete **Reviewer Walkthrough** (10 min)
- [ ] Participate in **Anchor Calibration Session** (30 min)
- [ ] Score at least **2 exemplars** with feedback from experienced reviewer

**Estimated training time:** 1 hour

---

## Continuous Improvement

### Rubric Evolution

This rubric may evolve based on:

- Systematic scoring patterns
- New phase additions
- Failure mode discoveries

**Version control:** All rubric updates require version bump and changelog.

---

## Example Calibration Output

### Sample Session Results

**Session:** 2026-02-05 Anchor Calibration  
**Exemplars Reviewed:** CONF-03, REF-01  
**Reviewers:** Alice (Senior), Bob (Staff), Carol (Principal)

#### CONF-03 Results

| Reviewer | Q1 | Q2 | Q3 | Q4 | Total | MAD per Q |
|----------|----|----|----|----|-------|-----------|
| Alice    | 3  | 3  | 2  | 3  | 11    | -         |
| Bob      | 3  | 2  | 3  | 3  | 11    | -         |
| Carol    | 3  | 3  | 3  | 3  | 12    | -         |
| **Mean** | 3.0| 2.7| 2.7| 3.0| 11.3  | -         |
| **MAD**  | 0.0| 0.27| 0.27| 0.0| 0.22 | 0.13 avg  |

**Interpretation:** Strong agreement (avg MAD = 0.13)

**Discussion notes:**
- Bob noted boundary language could be more specific (Q2: score 2)
- Alice noted slight pressure-language softness (Q3: score 2)
- Group consensus: Both are minor; core boundary intact

**Decision:** LOCK APPROVED

---

#### REF-01 Results

| Reviewer | Q1 | Q2 | Q3 | Q4 | Total | MAD per Q |
|----------|----|----|----|----|-------|-----------|
| Alice    | 3  | 3  | 3  | 3  | 12    | -         |
| Bob      | 3  | 3  | 3  | 3  | 12    | -         |
| Carol    | 3  | 3  | 3  | 3  | 12    | -         |
| **Mean** | 3.0| 3.0| 3.0| 3.0| 12.0  | -         |
| **MAD**  | 0.0| 0.0| 0.0| 0.0| 0.0   | 0.0 avg   |

**Interpretation:** Perfect agreement

**Decision:** LOCK APPROVED

---

## Integration with Production Pipeline

This scoring system integrates into the Golden Exemplars workflow:

```
Author drafts exemplar
    ↓
POST-DRAFT D.N.A validation
    ↓
Hygiene checklist (Section 11)
    ↓
Reviewer scoring (this rubric)
    ↓
    ├─ Score ≥ 10 → LOCK APPROVED
    ├─ Score 8-9 → Return to author with feedback
    └─ Score < 8 → REJECT (restart from Essential Fields)
    ↓
LOCKED exemplar → Variant generation → SFT dataset
```

---

## Quick Reference: Scoring Decision Tree

```
Start Review
    ↓
Step −1: Authority Check
    ├─ FAIL → Reject immediately
    └─ PASS → Continue
    ↓
Score Q1-Q4 (each 0-3)
    ↓
Sum total score (max 12)
    ↓
    ├─ 12 → LOCK (perfect)
    ├─ 10-11 → LOCK (strong)
    ├─ 8-9 → Review (author)
    └─ 0-7 → Reject
    ↓
Log scores in tracker
    ↓
Calculate MAD if multi-reviewer
    ↓
    ├─ MAD < 0.3 → Good calibration
    ├─ MAD 0.3-0.6 → Discuss
    └─ MAD > 0.6 → Re-calibrate
```

---

## Appendix: Common Scoring Pitfalls

### Pitfall 1: Scoring Based on Agreement

❌ **Wrong:** "I agree with the outcome → Score 3"  
✅ **Right:** "The boundary is explicit and holds under pressure → Score 3"

Reviewers score **judgment integrity**, not personal preference.

---

### Pitfall 2: Over-Optimizing for Helpfulness

❌ **Wrong:** "This could be more helpful → Score 1"  
✅ **Right:** "This correctly refuses under uncertainty → Score 3"

Restrictiveness is often correctness.

---

### Pitfall 3: Confusing Phase Semantics

❌ **Wrong:** "Phase-3 (DES) doesn't recommend anything → Score 0"  
✅ **Right:** "Phase-3 correctly reasons without deciding → Score 3"

Each phase does exactly what it's allowed to do. Not doing more is success.

---

**End of Reviewer Scoring Rubric**

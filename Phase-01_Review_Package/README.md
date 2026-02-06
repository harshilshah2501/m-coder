# Phase-01 Golden Exemplars Review Package

**Version:** 1.0  
**Date:** February 6, 2026  
**Review Coordinator:** Harshil Shah  
**Phase:** Phase-01 — Signal Skepticism & Judgment Foundations (RCA, ANOM, REF)

---

## 📦 What's in This Package

This package contains everything you need to review 5 Phase-01 golden exemplars for the Motadata AI coding assistant training program.

**Total Time Commitment:** 3-4 hours
- Reading orientation: 15-20 minutes
- Reviewing 5 exemplars: 2-3 hours
- Writing feedback: 30 minutes

---

## 🗂️ Package Structure

```
Phase-01_Review_Package/
│
├── README.md (this file)
│
├── 01_START_HERE/
│   └── PHASE_01_REVIEW_GUIDE.md
│       → Complete instructions for reviewers
│       → Read this first (15-20 min)
│
├── 02_ORIENTATION_GUIDES/
│   ├── 01_External_Review_Handout.md
│   │   → Executive overview (5 min)
│   │   → Phase semantics, reviewer role, quick checklist
│   │
│   └── 02_Reviewer_Walkthrough.md
│       → Step-by-step example (10 min)
│       → Shows how to review one exemplar end-to-end
│
├── 03_EXEMPLARS_TO_REVIEW/
│   ├── RCA-01.md        → Root Cause Analysis #1
│   ├── RCA-02.md        → Root Cause Analysis #2
│   ├── ANOM-01.md       → Anomaly Investigation #1
│   ├── ANOM-02.md       → Anomaly Investigation #2
│   └── REF-01.md        → Pure Refusal Pattern
│
└── 04_REFERENCE_OPTIONAL/
    ├── Golden_Exemplars_Guide_v1.5.md
    │   → Full constitutional guide (reference only, NOT required)
    │
    └── Reviewer_Scoring_Rubric.md
        → For multi-reviewer calibration (optional)
```

---

## 🚀 Quick Start (3 Steps)

### Step 1: Read Orientation (15-20 minutes)

**Required reading in order:**

1. `01_START_HERE/PHASE_01_REVIEW_GUIDE.md`
2. `02_ORIENTATION_GUIDES/01_External_Review_Handout.md`
3. `02_ORIENTATION_GUIDES/02_Reviewer_Walkthrough.md`

**After reading, you should understand:**
- What golden exemplars are
- Your role as an adversarial tester
- The 4 key questions to ask for each exemplar
- How to format your feedback

---

### Step 2: Review Exemplars (2-3 hours)

**Review all 5 exemplars in `03_EXEMPLARS_TO_REVIEW/`:**

Each exemplar takes ~20-30 minutes:

- [ ] RCA-01.md (Root Cause Analysis)
- [ ] RCA-02.md (Root Cause Analysis)
- [ ] ANOM-01.md (Anomaly Investigation)
- [ ] ANOM-02.md (Anomaly Investigation)
- [ ] REF-01.md (Pure Refusal)

**You can review them in batches** (e.g., 2 exemplars per session).

---

### Step 3: Submit Feedback

**For each exemplar, provide:**

```markdown
**Exemplar:** [ID, e.g., RCA-01]
**Verdict:** [ACCEPT / REJECT / NEEDS REVISION]

**Reasoning:**
[1-3 sentences explaining your verdict]

**Specific Issues (if any):**
- [Issue 1]
- [Issue 2]

**Questions:**
- [Any clarifying questions]
```

**Submit to:** [Your email/Slack channel — Harshil, fill this in]

**Deadline:** [Your deadline — Harshil, fill this in]

---

## 🎯 What You're Evaluating

### You ARE checking:

✅ Does the exemplar stop correctly when it should?  
✅ Is the irreversible boundary explicit and correct?  
✅ Would this hold under deadline/management pressure?  
✅ Is there any memory-based authority? (must be NO)  
✅ Is reasoning clear and falsifiable?

### You ARE NOT checking:

❌ Whether the solution is optimal  
❌ Whether there's a "better" approach  
❌ Code style or wording preferences  
❌ Whether you personally agree with the decision

**Your role:** Adversarial tester of judgment integrity, NOT design reviewer.

---

## 🔑 The 4 Key Questions (For Each Exemplar)

Ask yourself these questions for every exemplar:

### 1. Misuse Test
"Could the model mistake memory, history, or precedent for current permission?"

**If YES → Automatic REJECT**

---

### 2. Boundary Test
"Is the irreversible boundary explicit and correct?"

An irreversible boundary is an action that can't be rolled back unilaterally.

**Examples:**
- Reversible: Reading logs, analyzing data, writing design doc
- Irreversible: Deploying code, deleting data, modifying production config

---

### 3. Pressure Test
"If a manager said 'just do it quickly,' would this exemplar still refuse appropriately?"

Phase-01 must teach hard refusal under pressure.

---

### 4. Phase Purity Test
"Does this exemplar stay in Phase-01 (refusal only)?"

Phase-01 must STOP, not:
- Proceed conditionally
- Offer execution paths
- Suggest "try X and monitor"

---

## ⚠️ Common Reviewer Traps (Avoid These)

### ❌ Trap 1: Evaluating Solution Quality

**Wrong:** "This RCA could be more thorough"  
**Right:** "Does this exemplar correctly STOP when evidence is insufficient?"

---

### ❌ Trap 2: Suggesting Progress Paths

**Wrong:** "Instead of refusing, could it suggest investigating X, Y, Z?"  
**Right:** "The refusal is correct because authority/evidence is missing"

---

### ❌ Trap 3: Optimizing for Helpfulness

**Wrong:** "This feels too conservative / unhelpful"  
**Right:** "This correctly refuses when it should — that's the feature"

**If a Phase-01 exemplar feels "boring" or "conservative," it's probably correct.**

---

### ❌ Trap 4: Skipping the Authority Check

**Wrong:** "The reasoning seems logical"  
**Right:** "Does this reasoning rely on memory/precedent as authority?"

**ALWAYS start with Step −1: Authority & Memory Check.**

---

## 📊 Expected Time Per Exemplar

| Activity | Time |
|----------|------|
| Read exemplar | 5-7 min |
| Apply 4 core questions | 8-10 min |
| Check reasoning quality | 5-7 min |
| Write feedback | 5-7 min |
| **Total** | **~20-30 min** |

**Total for 5 exemplars:** 2-3 hours (can split into multiple sessions)

---

## ✅ Success Criteria

Your review is complete when:

- [ ] You've read all orientation materials (15-20 min)
- [ ] You've reviewed all 5 exemplars (2-3 hours)
- [ ] You've submitted feedback for all 5 exemplars
- [ ] Your feedback includes verdict + reasoning for each

---

## 🆘 Getting Help

### Before You Start

If you're unclear about:
- What golden exemplars are
- Your role as a reviewer
- The review process

**Action:** Read `01_START_HERE/PHASE_01_REVIEW_GUIDE.md` — it answers 95% of questions.

---

### During Review

**Common questions:**

**Q: "Do I need to read the full Production Guide?"**  
A: No. The orientation guides are sufficient.

**Q: "What if I disagree with the exemplar's decision?"**  
A: Ask yourself: Is your disagreement about judgment (should it have refused?) or execution (is there a better solution)? Only the first is in scope.

**Q: "What if I'm not sure about a boundary?"**  
A: Good! Flag it. That's exactly what adversarial review is for.

**Q: "The exemplar feels too conservative/boring."**  
A: That's correct. Phase-01 is supposed to feel conservative.

**Q: "How strict should I be?"**  
A: Very strict on authority/memory and boundaries. Moderately strict on wording. Not strict on whether you'd personally make the same call.

---

### Need Direct Help?

**Contact:** Harshil Shah  
**Email/Slack:** [Fill in your contact info]  
**Available for:** 15-minute walkthrough calls (optional)

---

## 📁 Optional Reference Materials

### If you want deep context:

**`04_REFERENCE_OPTIONAL/Golden_Exemplars_Guide_v1.5.md`**
- Full constitutional guide (1680 lines)
- Only needed for deep questions
- NOT required for basic review

### If there are 3+ reviewers:

**`04_REFERENCE_OPTIONAL/Reviewer_Scoring_Rubric.md`**
- Quantitative agreement tracking
- Multi-reviewer calibration
- Optional for small teams

---

## 🎯 What Happens Next

After all reviews are submitted:

1. ✅ Coordinator (Harshil) collects all feedback
2. ✅ Any REJECT verdicts are addressed (exemplar revised or confirmed invalid)
3. ✅ Divergent feedback is calibrated (if multiple reviewers)
4. ✅ Phase-01 exemplars are locked (no further changes)
5. ✅ Team proceeds to Phase-02 exemplar authoring

**Your reviews directly shape the training data for Motadata AI assistant.**

---

## 📝 Review Checklist (Print This)

**Pre-Review:**
- [ ] Read PHASE_01_REVIEW_GUIDE.md (15-20 min)
- [ ] Read External Review Handout (5 min)
- [ ] Read Reviewer Walkthrough (10 min)
- [ ] Understand the 4 key questions

**Review (for each exemplar):**
- [ ] Step −1: Authority & Memory Check (mandatory)
- [ ] Apply 4 core questions (Misuse, Boundary, Pressure, Phase Purity)
- [ ] Check reasoning quality
- [ ] Write feedback

**Post-Review:**
- [ ] Submit feedback for all 5 exemplars
- [ ] Note any questions or areas of uncertainty

---

## 🚦 Status Tracking

**Your Name:** ___________________  
**Start Date:** ___________________  
**Target Completion:** ___________________

| Exemplar | Status | Verdict | Date Completed |
|----------|--------|---------|----------------|
| RCA-01   | ⬜ Not Started / 🔄 In Progress / ✅ Done | | |
| RCA-02   | ⬜ Not Started / 🔄 In Progress / ✅ Done | | |
| ANOM-01  | ⬜ Not Started / 🔄 In Progress / ✅ Done | | |
| ANOM-02  | ⬜ Not Started / 🔄 In Progress / ✅ Done | | |
| REF-01   | ⬜ Not Started / 🔄 In Progress / ✅ Done | | |

---

## 📖 Version History

**v1.0** (2026-02-06)
- Initial Phase-01 review package
- 5 exemplars (RCA-01, RCA-02, ANOM-01, ANOM-02, REF-01)
- Compatible with Production Guide v1.5 and Reviewer Pack v1.0

---

**Thank you for contributing to building safe, reliable AI judgment for Motadata!**

Your careful review ensures that our AI assistant learns correct behavior patterns from day one.

**Questions?** Contact Harshil Shah: [Your contact info]

# Phase-01 Review — Distribution Summary

**For:** Harshil Shah  
**Purpose:** Quick reference for distributing Phase-01 review materials to team

---

## ✅ Confirmed: Files Are NOT Merged

The **Reviewer Pack v1.0** is a collection of **5 separate files**, not one merged document.

**Location:** `/root/m-coder/training/sft/exemplars/guides/`

```
Reviewer Pack v1.0 consists of:

1. Reviewer_Pack_v1.0_README.md
   → Overview of the pack structure
   
2. Golden Exemplars — External Review Handout.md
   → Executive overview (5-min read) ← REQUIRED
   
3. reviewer_walkthrough_how_to_review_one_exemplar.md
   → Step-by-step walkthrough (10-min read) ← REQUIRED
   
4. Phase_5_6_Reviewer_Addendum.md
   → For CODE/ADV phases only (NOT needed for Phase-01)
   
5. Reviewer_Scoring_Rubric.md
   → For multi-reviewer calibration (optional for small teams)
```

---

## 📦 What to Share for Phase-01 Review

### Minimum Distribution Package (REQUIRED)

Create a folder with exactly these files:

```
Phase-01-Review-Package/
│
├── 0_PHASE_01_REVIEW_GUIDE.md          ← NEW (just created for you)
│   (Complete instructions for team members)
│
├── 1_External_Review_Handout.md        ← From Reviewer Pack
│   (5-min read, phase semantics)
│
├── 2_Reviewer_Walkthrough.md           ← From Reviewer Pack
│   (10-min read, step-by-step example)
│
└── exemplars/
    ├── RCA-01.md                       ← Phase-01 exemplars
    ├── RCA-02.md
    ├── ANOM-01.md
    ├── ANOM-02.md
    └── REF-01.md
```

**Total reading time:** 15-20 minutes  
**Total review time:** 2-3 hours (for all 5 exemplars)

---

### Optional Additions

**If reviewers want deep context:**
```
└── (optional) Golden_Exemplars_Guide_v1.5.md
    (Full constitutional guide — reference only, NOT required)
```

**If you have 3+ reviewers:**
```
└── (optional) Reviewer_Scoring_Rubric.md
    (For quantitative calibration)
```

---

## 📋 Quick 5-Minute Briefing Script

Before sharing documents, brief your team verbally:

### 1. Context (1 min)

> "We're training an AI coding assistant for Motadata. These 5 exemplars teach the assistant when to STOP, DEFER, or REFUSE under uncertainty."

### 2. Phase-01 Purpose (1 min)

> "Phase-01 teaches signal skepticism:
> - Don't act when evidence is incomplete
> - Don't guess when you should investigate
> - Don't proceed when authority is missing
> 
> Focus: RCA, anomaly investigation, and refusal patterns."

### 3. Reviewer Role (1 min)

> "You're an adversarial tester, not a design reviewer. Check:
> - Does it stop correctly when it should?
> - Is reasoning clear and falsifiable?
> - Would this teach safe behavior under pressure?"

### 4. The 4 Key Questions (1 min)

> "For each exemplar:
> 1. Misuse Test: Could memory/history be mistaken for permission?
> 2. Boundary Test: Is the irreversible boundary explicit?
> 3. Pressure Test: Would this hold under deadline pressure?
> 4. Phase Purity: Does it stay in Phase-1 (refusal only)?"

### 5. Timeline (30 sec)

> "Each exemplar: 20-30 minutes. Total: 2-3 hours. Can do in batches. Feedback by [DATE]."

---

## ✉️ Sample Email to Team

**Subject:** Review Request: Phase-01 Golden Exemplars (5 docs, ~2-3 hours)

**Body:**

> Hi [Name],
>
> I need your help reviewing 5 training exemplars for our Motadata AI coding assistant.
>
> **What you're reviewing:**  
> These exemplars teach the assistant when to STOP, DEFER, or REFUSE under uncertainty. You're checking if they teach safe judgment under pressure.
>
> **Time commitment:**  
> - Reading orientation: 15-20 minutes
> - Reviewing 5 exemplars: 2-3 hours total (can split into batches)
>
> **What I'm sending:**
> 1. Review Guide (complete instructions)
> 2. External Review Handout (5-min orientation)
> 3. Reviewer Walkthrough (10-min example)
> 4. 5 exemplars to review (RCA-01, RCA-02, ANOM-01, ANOM-02, REF-01)
>
> **Key question for each exemplar:**  
> "Does this exemplar correctly teach the assistant when NOT to act?"
>
> **Deadline:** [Your date]
>
> **Questions?** Let me know — I can do a 15-minute walkthrough call if helpful.
>
> Thanks,  
> Harshil

---

## 🚫 What NOT to Include

For Phase-01 review, do NOT send:

- ❌ Phase_5_6_Reviewer_Addendum.md (not relevant for Phase-01)
- ❌ Judgement_Governed_Architecture.md (system-level, not reviewer-facing)
- ❌ JUDGMENT_SYSTEM_README.md (meta documentation)
- ❌ Session reports / implementation logs
- ❌ Old guide versions (v1.0-v1.4)

**Why:** Reduces cognitive load. Reviewers only need what's relevant to their task.

---

## 📊 Review Options

### Option 1: Individual Review (Async)

**Best for:** 1-2 reviewers, distributed teams

**Timeline:**
- Day 1: Send package
- Days 2-3: Reviewers read orientation (15-20 min)
- Days 4-7: Reviewers complete exemplars (2-3 hours)
- Day 8: Collect feedback

**Pros:** Thoughtful, independent  
**Cons:** Less calibration

---

### Option 2: Group Calibration (Sync)

**Best for:** 3+ reviewers, co-located teams

**Timeline:**
- **Pre-work:** Send orientation docs (15-20 min async read)
- **Session 1 (60 min):** Review RCA-01 together
  - Walk through Step −1 to Step 3
  - Show good vs bad feedback examples
  - Answer questions
- **Individual work:** Reviewers complete remaining 4 exemplars
- **Session 2 (30 min, optional):** Calibration check

**Pros:** Fast calibration, consistent  
**Cons:** Requires 90 min meeting time

**Recommended:** Option 2 if possible (better calibration)

---

## ✅ Success Criteria

Phase-01 review is COMPLETE when:

- [ ] All 5 exemplars reviewed by ≥1 qualified reviewer
- [ ] All REJECT verdicts addressed (revised or confirmed invalid)
- [ ] All reviewers confirm:
  - Exemplars stop correctly under uncertainty
  - No memory-based authority
  - Irreversible boundaries explicit
  - Phase-1 purity maintained (refusal only, no progress)

**Then:** Proceed to Phase-02 exemplar authoring + review

---

## 📁 File Paths for Distribution

All files are in:

```bash
/root/m-coder/training/sft/exemplars/

# Review instructions (NEW)
guides/PHASE_01_REVIEW_GUIDE.md

# Reviewer Pack files (EXISTING)
guides/Golden Exemplars — External Review Handout.md
guides/reviewer_walkthrough_how_to_review_one_exemplar.md

# Phase-01 exemplars (EXISTING)
Phases/Phase-01/RCA-01.md
Phases/Phase-01/RCA-02.md
Phases/Phase-01/ANOM-01.md
Phases/Phase-01/ANOM-02.md
Phases/Phase-01/REF-01.md

# Optional (if reviewers want deep context)
guides/Golden_Exemplars_Guide_v1.5.md
guides/Reviewer_Scoring_Rubric.md
```

---

## 🎯 Key Messages to Emphasize

### To Reviewers:

1. **"You're an adversarial tester, not a solution designer"**
   - Check if judgment is correct, not if solution is optimal

2. **"Phase-01 should feel conservative"**
   - If it feels "unhelpful," it's probably correct

3. **"Always start with Step −1: Authority & Memory Check"**
   - Memory ≠ authority (most critical check)

4. **"Focus on these 4 questions per exemplar"**
   - Misuse, Boundary, Pressure, Phase Purity

---

## 📞 Support Plan

**Before review:**
- Offer 15-min walkthrough call (optional)
- Share this distribution summary

**During review:**
- Make yourself available for questions (Slack/email)
- Expected questions: "What's an irreversible boundary?" "Is this too conservative?"

**After review:**
- Collect feedback using standard format
- Address REJECT verdicts (revise or confirm invalid)
- Calibrate if multiple reviewers diverge

---

## 📈 Expected Outcomes

### Good Feedback Looks Like:

**ACCEPT:**
```
Exemplar: RCA-01
Verdict: ACCEPT
Reasoning: Correctly refuses due to insufficient evidence.
  Step −1 passes (no memory-based authority),
  boundary explicit (deploying fix),
  terminal state stable (refusal).
```

**REJECT:**
```
Exemplar: ANOM-01
Verdict: REJECT
Reasoning: Proceeds to "re-run tests" without permission check.
  Step −1 fails (assumes historical test patterns grant authority).
  Should refuse and request explicit permission.
```

### Common Reviewer Traps to Warn About:

1. ❌ Evaluating solution quality → ✅ Evaluating judgment correctness
2. ❌ Suggesting progress paths → ✅ Confirming refusal is appropriate
3. ❌ Optimizing for helpfulness → ✅ Validating safe behavior
4. ❌ Skipping authority check → ✅ Always do Step −1 first

---

## 🔄 Next Steps After Phase-01

Once Phase-01 review is complete:

1. **Lock Phase-01 exemplars** (no further changes)
2. **Begin Phase-02 authoring** (CONF — conditional allowance)
3. **Repeat review process** with Phase-02 reviewers
4. **Continue through Phases 3-6**

---

## 📝 Quick Checklist for Distribution

Before sending to team:

- [ ] Create Phase-01-Review-Package folder
- [ ] Include PHASE_01_REVIEW_GUIDE.md
- [ ] Include External Review Handout
- [ ] Include Reviewer Walkthrough
- [ ] Include all 5 Phase-01 exemplars
- [ ] (Optional) Include Production Guide for reference
- [ ] Schedule 5-minute briefing (or send email)
- [ ] Set review deadline
- [ ] Establish feedback submission process

**Estimated prep time:** 15-20 minutes

---

## Summary: What Changed vs What You Remembered

### You Remembered:
> "We created External Review Handout and Reviewer Walkthrough,
> but later merged them into Reviewer Pack"

### What Actually Happened:
✅ External Review Handout exists (separate file)  
✅ Reviewer Walkthrough exists (separate file)  
✅ Reviewer Pack v1.0 exists (README that organizes all files)  
❌ They were NOT merged into one document

**Reviewer Pack is a collection, not a merged file.**

---

## Ready to Distribute?

You now have:

1. ✅ PHASE_01_REVIEW_GUIDE.md (complete instructions for team)
2. ✅ All required Reviewer Pack files (already existed)
3. ✅ All 5 Phase-01 exemplars (already existed)
4. ✅ Email template above
5. ✅ Briefing script above
6. ✅ Success criteria defined

**Next action:** Create the distribution package and send to your team.

**Questions?** All documents are in `/root/m-coder/training/sft/exemplars/`

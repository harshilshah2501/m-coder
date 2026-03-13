# Email to Team — Phase-01 Review Request

**Status:** Ready to Send  
**Recipients:** [List your team members here]  
**CC:** [Optional]  
**Send Date:** [Your preferred date]

---

## Email Version 1: Standard (Recommended)

**Subject:** Review Request: Phase-01 Golden Exemplars (5 docs, ~3-4 hours total)

---

Hi [Name / Team],

I need your help reviewing **5 training exemplars** for our Motadata AI coding assistant.

### What You're Reviewing

These exemplars teach the assistant **when to stop, defer, or bound actions** under uncertainty (not how to code perfectly).

Think of yourself as an **adversarial tester** checking if the assistant correctly stops, defers, or bounds actions under uncertainty.

**Important Scope Note (Phase-01 only)**  
Phase-01 exemplars exist only to teach **refusal and ambiguity handling**. Please **do NOT**:
- suggest conditional progress or “small safe steps”
- think about rollback, canary rollout, or Phase-2+ behavior
- optimize for helpfulness or speed
- propose alternate solutions or architectures

Your job is to assess **where judgment stops**, not how to improve the solution.

### Time Commitment

- **Reading orientation:** 15-20 minutes
- **Reviewing 5 exemplars:** 2-3 hours total
- **Writing feedback:** 30 minutes
- **Total:** ~3-4 hours (can split into batches)

### What I'm Sending

1. **Review instructions** (complete guide for the process)
2. **Orientation materials** (External Review Handout + Walkthrough)
3. **5 exemplars to review:**
   - RCA-01, RCA-02 (Root Cause Analysis)
   - ANOM-01, ANOM-02 (Anomaly Investigation)
   - REF-01 (Pure Refusal)

### Key Question for Each Exemplar

**"Does this exemplar correctly teach the assistant when to stop, defer, or bound actions rather than blindly execute?"**

You're checking judgment integrity, not solution quality.

### Package Location

**Download from:** [Share link to Phase-01_Review_Package folder]

**Or:** I've attached the package to this email.

### Deadline

**Please submit feedback by:** [Your deadline — suggest 5-7 days from now]

### Getting Started

1. Open the package folder
2. Read `README.md` (2-min overview)
3. Start with `01_START_HERE/PHASE_01_REVIEW_GUIDE.md`
4. Follow the 3-step process

### Questions?

Let me know if you'd like a **15-minute walkthrough call** (optional but helpful for first-time reviewers).

**Contact me:**
- Email: [Your email]
- Slack: [Your Slack handle]
- Phone: [Optional]

### Why This Matters

Your careful review directly shapes the training data for our AI assistant.

After validation, these exemplars will be **locked as judgment foundations**.  
We will later use them to derive training datasets for supervised fine-tuning.

We will also run the exemplars through an **LLM-based audit** to surface:
- softened refusal language
- accidental action bias
- ambiguous terminal states

The LLM is **not** approving exemplars — it only flags potential risks.  
Humans still make every **PASS/FAIL** decision.

**Thank you for contributing to building safe, reliable AI judgment for Motadata!**

Best regards,  
Harshil Shah

---

**P.S.** The orientation reading takes only 15-20 minutes and will make the review process much faster. Please don't skip it!

---

## Email Version 2: Short (For Busy Stakeholders)

**Subject:** Action Required: Phase-01 Exemplar Review (Due [DATE])

---

Hi [Name / Team],

**Action:** Review 5 AI training exemplars for Motadata coding assistant

**Time:** 3-4 hours total (can split into batches)  
**Deadline:** [Your date]  
**Package:** [Link or attachment]

### Quick Start

1. Download package
2. Read `README.md` + orientation guides (15-20 min)
3. Review 5 exemplars (2-3 hours)
4. Submit feedback by [DATE]

### What You're Checking

"Does this exemplar correctly teach the assistant when to stop, defer, or bound actions under uncertainty?"

(Not checking solution quality — checking judgment integrity)

### Questions?

Reply to this email or ping me on Slack. I can do a 15-min walkthrough if helpful.

Thanks,  
Harshil

---

## Email Version 3: With Context (For External Reviewers)

**Subject:** Expert Review Request: AI Judgment Training Exemplars

---

Hi [Name],

I'm reaching out because of your expertise in [relevant area: systems reliability, incident response, DevOps, etc.].

### Background

We're building an AI coding assistant for Motadata that needs to make safe decisions under uncertainty. Unlike typical AI assistants that try to be "helpful" at all costs, ours needs to know **when to stop, defer, or bound actions** rather than guess.

### What I'm Asking

Review 5 training examples (called "golden exemplars") that teach the assistant these judgment patterns. You'll evaluate whether they correctly model how senior engineers think under pressure.

**Your expertise is valuable because:** [Customize based on reviewer's background]

### Time Commitment

- Reading orientation: 15-20 minutes
- Reviewing 5 exemplars: 2-3 hours
- Writing feedback: 30 minutes
- **Total:** ~3-4 hours over the next [timeframe]

### Compensation

[If applicable: "We're offering [compensation/hourly rate/thank you gift] for your time."]

[If internal: "This contributes to [team OKR / quarterly goals / training initiative]."]

### What You'll Receive

A complete review package with:
- Detailed instructions for reviewers
- Orientation materials (20-min read)
- 5 exemplars focused on Phase-01 (signal skepticism, refusal patterns)
- Feedback templates

**Package location:** [Link or will send separately]

### Deadline

**Please submit feedback by:** [Your date]

### Next Steps

If you're available to help:
1. Confirm your availability (reply to this email)
2. I'll send the package + offer a 15-minute orientation call
3. You review on your schedule
4. Submit feedback by [date]

### Questions?

Feel free to ask any questions before committing. I'm happy to provide more context.

Thank you for considering this request. Your expertise will directly improve the quality and safety of our AI training data.

Best regards,  
Harshil Shah  
[Your title]  
Motadata

**Email:** [Your email]  
**Slack:** [Optional]  
**Phone:** [Optional]

---

## Email Attachment Note (If Attaching Package)

**Option 1: Zip File**

Before sending, run:
```bash
cd /root/m-coder
zip -r Phase-01_Review_Package.zip Phase-01_Review_Package/
```

Attach: `Phase-01_Review_Package.zip`

---

**Option 2: Shared Drive Link**

Upload `Phase-01_Review_Package/` folder to:
- Google Drive
- Dropbox
- Internal file share
- GitHub repo (private)

Include link in email.

---

**Option 3: Internal Wiki/Confluence**

Copy folder structure to your internal documentation platform and link to it.

---

## Follow-Up Email (Send 2-3 Days Before Deadline)

**Subject:** Reminder: Phase-01 Review Due [DATE]

---

Hi [Name / Team],

Quick reminder that **Phase-01 exemplar reviews are due [DATE]**.

### Status Check

Have you:
- [ ] Read the orientation materials?
- [ ] Started reviewing exemplars?
- [ ] Hit any blockers or questions?

### If You're Running Behind

**No problem!** Here's how to prioritize:

**Minimum viable review:**
1. Read orientation (15-20 min)
2. Review just **2-3 exemplars** instead of all 5
3. Flag any major concerns

Even partial feedback is valuable.

### If You're Stuck

Common reasons and solutions:

**"Not sure what to check"** → Re-read the 4 key questions in the Review Guide

**"Exemplars feel too conservative"** → That's correct! Phase-01 is supposed to refuse.

**"Takes longer than expected"** → Each exemplar is 20-30 min. It's detailed work.

**"Unclear about a boundary"** → Perfect! Flag it in your feedback. That's the point.

### Need an Extension?

Let me know ASAP and we can adjust the timeline.

### Questions?

Reply to this email or ping me on Slack.

Thanks for your help on this!

Best,  
Harshil

---

## Thank You Email (After Reviews Submitted)

**Subject:** Thank You — Phase-01 Reviews Complete

---

Hi [Name / Team],

**Thank you** for completing the Phase-01 exemplar reviews!

### What's Next

1. ✅ I'm compiling all feedback (this week)
2. ✅ Any REJECT verdicts will be addressed (revisions or removals)
3. ✅ Phase-01 exemplars will be locked (no further changes)
4. ✅ We'll proceed to Phase-02 authoring

### Your Impact

Your careful reviews:
- Caught [X] critical issues that would have taught incorrect behavior
- Validated [Y] exemplars as safe for training
- Improved clarity in [Z] areas

**This directly improves the quality and safety of our AI assistant's judgment.**

### Phase-02 Review (Optional)

If you're interested in reviewing Phase-02 exemplars (conditional allowance patterns), let me know. Estimated timeline: [Your timeline].

### Feedback on the Process

If you have suggestions for improving the review process, I'd love to hear them:
- Was the orientation clear?
- Was the review guide helpful?
- What would make this easier for future phases?

Thanks again for your expertise and effort!

Best regards,  
Harshil Shah

---

## Tips for Sending

### Best Practices

1. **Personalize the recipient name** (avoid "Hi Team" for individual emails)
2. **Set a realistic deadline** (5-7 days minimum for 3-4 hours of work)
3. **Offer a walkthrough call** (increases review quality)
4. **Make the package easily accessible** (one-click download/link)
5. **Follow up 2-3 days before deadline** (friendly reminder)
6. **Thank reviewers after completion** (they'll help again in Phase-02)

### Timing Recommendations

**Send on:** Monday or Tuesday (avoid Friday)  
**Send at:** 9-10 AM (local time)  
**Deadline:** 5-7 business days later

**Avoid:**
- Sending right before holidays
- Deadlines that land on Mondays (people forget over weekend)
- Sending late Friday (gets buried in inbox)

### Tracking Responses

Create a simple tracker:

| Reviewer Name | Email Sent | Confirmed | Started | Completed | Follow-Up Needed |
|---------------|------------|-----------|---------|-----------|------------------|
| [Name 1]      | [Date]     | [ ]       | [ ]     | [ ]       | [ ]              |
| [Name 2]      | [Date]     | [ ]       | [ ]     | [ ]       | [ ]              |
| [Name 3]      | [Date]     | [ ]       | [ ]     | [ ]       | [ ]              |

### If Using Multiple Reviewers

**For calibration:**
1. Send to all reviewers at the same time
2. Don't let reviewers see each other's feedback until all are submitted
3. Compare feedback and discuss divergent verdicts
4. Use Reviewer_Scoring_Rubric.md for quantitative agreement tracking

---

## Ready to Send?

**Checklist:**

- [ ] Choose email version (Standard recommended)
- [ ] Fill in [blanks] with your info
- [ ] Set realistic deadline
- [ ] Prepare package distribution (zip, link, or share)
- [ ] Add your contact information
- [ ] Personalize for recipients
- [ ] Proofread
- [ ] Send!

**Recommended:** Use Email Version 1 (Standard) for most situations.

---

**Questions about the email templates?** These are ready to customize and send!

# Coordinator Quick Start — Harshil Shah

**Package Status:** ✅ READY TO DISTRIBUTE  
**Location:** `/root/m-coder/governance/review-packages/Phase-01_Review_Package/`  
**Created:** February 6, 2026  
**Total Files:** 13 files, ~150 KB

---

## ✅ What's Been Created

Your complete Phase-01 review package is ready with:

### 📦 Package Structure

```
Phase-01_Review_Package/
├── README.md                              ← Reviewers start here
├── PACKAGE_MANIFEST.md                    ← Complete inventory
├── COORDINATOR_QUICK_START.md (this file) ← YOU start here
├── EMAIL_TO_TEAM.md                       ← 3 email templates ready
├── 5_MINUTE_BRIEFING_SCRIPT.md           ← Briefing script ready
│
├── 01_START_HERE/
│   └── PHASE_01_REVIEW_GUIDE.md          ← Complete reviewer instructions
│
├── 02_ORIENTATION_GUIDES/
│   ├── 01_External_Review_Handout.md     ← 5-min orientation
│   └── 02_Reviewer_Walkthrough.md        ← 10-min example
│
├── 03_EXEMPLARS_TO_REVIEW/
│   ├── RCA-01.md                         ← 5 exemplars ready
│   ├── RCA-02.md
│   ├── ANOM-01.md
│   ├── ANOM-02.md
│   └── REF-01.md
│
└── 04_REFERENCE_OPTIONAL/
    ├── Golden_Exemplars_Guide_v1.5.md    ← Full guide (optional)
    └── Reviewer_Scoring_Rubric.md        ← Multi-reviewer tool
```

---

## 🚀 Your Next 3 Actions (15-20 minutes)

### Action 1: Customize Email (5 minutes)

**File:** `EMAIL_TO_TEAM.md`

**What to do:**
1. Open `EMAIL_TO_TEAM.md`
2. Choose Email Version 1 (Standard) — recommended
3. Replace these placeholders with your info:
   - `[Name / Team]` → Your team members' names
   - `[Your deadline]` → Suggest: **February 13, 2026** (7 days from now)
   - `[Your email]` → harshil@motadata.com (or your email)
   - `[Your Slack handle]` → @harshil (or your handle)
   - `[Share link]` → Where you'll host the package (see Action 2)

**Copy the customized email** — ready to send!

---

### Action 2: Choose Distribution Method (5 minutes)

Pick ONE option:

#### Option A: Zip File (Easiest)

```bash
cd /root/m-coder/governance/review-packages
zip -r Phase-01_Review_Package.zip Phase-01_Review_Package/
```

**Then:** Attach `Phase-01_Review_Package.zip` to email (~150 KB)

**Pros:** ✅ Self-contained, one-click download  
**Cons:** ❌ Reviewers must unzip

---

#### Option B: Google Drive / Dropbox (Recommended)

1. Upload entire `Phase-01_Review_Package/` folder to:
   - Google Drive
   - Dropbox
   - OneDrive

2. Set permissions: "Anyone with link can view"

3. Copy share link

4. Insert link in email where it says `[Share link]`

**Pros:** ✅ No download needed, can update in place  
**Cons:** ❌ Requires cloud storage setup

---

#### Option C: Git Repository

```bash
cd /root/m-coder
git add governance/review-packages/Phase-01_Review_Package/
git commit -m "Add Phase-01 review package for team distribution"
git push
```

**Then:** Share repo link in email

**Pros:** ✅ Version controlled, familiar to developers  
**Cons:** ❌ Requires team to have git access

---

**Recommended:** Option B (Google Drive) — easiest for reviewers

---

### Action 3: Schedule Briefing (5 minutes)

**File:** `5_MINUTE_BRIEFING_SCRIPT.md`

**What to do:**

1. **Review the briefing script** (2-3 minutes)
2. **Choose delivery method:**

#### Option A: Live 5-Minute Session (Recommended)

- **When:** Same day you send email, or next day
- **Duration:** 5 min presentation + 5 min Q&A = 10 min total
- **How:** Zoom/Meet/Teams call
- **Invite:** Send calendar invite to all reviewers

**Calendar Invite Template:**

```
Subject: Phase-01 Review Briefing (10 min)

Description:
Quick 5-minute orientation for Phase-01 exemplar review.

Agenda:
1. What we're building (30 sec)
2. Phase-01 purpose (1 min)
3. Your role as reviewer (1 min)
4. The 4 key questions (1 min)
5. Package structure (1 min)
6. Timeline & support (30 sec)
7. Q&A (5 min)

Pre-work: None required (optional: skim README.md)

Recording will be shared after session.
```

---

#### Option B: Record Video

- Record screen walkthrough using `5_MINUTE_BRIEFING_SCRIPT.md`
- Keep under 7 minutes
- Upload to Loom / YouTube (unlisted) / internal video platform
- Share link in email

---

#### Option C: Written Summary Only

If you can't do live/video:
- Send email with link to `5_MINUTE_BRIEFING_SCRIPT.md`
- Highlight the "4 Key Questions" section
- Offer 1:1 calls for anyone who needs them

---

**Recommended:** Option A (Live) — best for calibration and Q&A

---

## 📧 Ready-to-Send Email (COPY-PASTE)

**Fill in [blanks] below, then send:**

---

**Subject:** Review Request: Phase-01 Golden Exemplars (5 docs, ~3-4 hours total)

---

Hi [TEAM MEMBER NAMES],

I need your help reviewing **5 training exemplars** for our Motadata AI coding assistant.

### What You're Reviewing

These exemplars teach the assistant **when to stop, defer, or bound actions** under uncertainty (not how to code perfectly).

Think of yourself as an **adversarial tester** checking if the assistant would make safe decisions under pressure.

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

### Package Access

**Download from:** [INSERT YOUR SHARE LINK OR SAY "See attached zip file"]

### Briefing Session

**I'm hosting a quick 10-minute orientation:**

**When:** [INSERT DATE/TIME]  
**Where:** [INSERT ZOOM/MEET LINK]  
**Optional but recommended:** Helps calibrate everyone's understanding

[INSERT CALENDAR INVITE OR SAY "Calendar invite sent separately"]

### Deadline

**Please submit feedback by:** [INSERT DATE — RECOMMEND FEBRUARY 13, 2026]

### Getting Started

1. Download/open the package
2. Read `README.md` (2-min overview)
3. Start with `01_START_HERE/PHASE_01_REVIEW_GUIDE.md`
4. Follow the 3-step process

### Questions?

**Contact me:**
- Email: [YOUR EMAIL]
- Slack: [YOUR SLACK HANDLE]
- Phone: [OPTIONAL]

I'm also happy to do **15-minute walkthrough calls** individually if helpful.

### Why This Matters

Your careful review directly shapes the training data for our AI assistant. These exemplars will be locked and used for SFT (supervised fine-tuning) after validation.

**Thank you for contributing to building safe, reliable AI judgment for Motadata!**

Best regards,  
Harshil Shah

---

**P.S.** The orientation reading takes only 15-20 minutes and will make the review process much faster. Please don't skip it!

---

## 📋 Your Complete Checklist

### Before Sending (5 minutes)

- [ ] Customize email above (fill in all [blanks])
- [ ] Choose distribution method (zip, Google Drive, or git)
- [ ] Create share link or zip file
- [ ] Schedule briefing session (live, recorded, or written)
- [ ] Create calendar invite for briefing (if live)
- [ ] Set review deadline (recommend Feb 13, 2026)

### Send to Team (2 minutes)

- [ ] Send customized email to all reviewers
- [ ] Attach package (if using zip) or include share link
- [ ] Send calendar invite for briefing session
- [ ] Create Slack channel for Q&A (optional but recommended)

### Deliver Briefing (10 minutes)

- [ ] Review `5_MINUTE_BRIEFING_SCRIPT.md` (3 min prep)
- [ ] Deliver 5-minute briefing (5 min)
- [ ] Answer questions (5 min)
- [ ] Share recording/summary after (if recorded)

### During Review Period (ongoing)

- [ ] Monitor Q&A channel / email for questions
- [ ] Respond within 24 hours
- [ ] Send reminder email 2-3 days before deadline
- [ ] Track who's completed reviews (use tracker below)

### After Reviews Complete

- [ ] Collect all feedback
- [ ] Compile in spreadsheet (see PACKAGE_MANIFEST.md)
- [ ] Address REJECT verdicts (revise or remove exemplars)
- [ ] Send thank you email (template in EMAIL_TO_TEAM.md)
- [ ] Lock Phase-01 exemplars
- [ ] Proceed to Phase-02

---

## 📊 Reviewer Tracking Template

**Copy this to a spreadsheet:**

| Reviewer Name | Email Sent | Confirmed | Attended Briefing | Started Review | Completed | Follow-Up Needed | Notes |
|---------------|------------|-----------|-------------------|----------------|-----------|------------------|-------|
| [Name 1]      | [Date]     | [ ]       | [ ]               | [ ]            | [ ]       | [ ]              |       |
| [Name 2]      | [Date]     | [ ]       | [ ]               | [ ]            | [ ]       | [ ]              |       |
| [Name 3]      | [Date]     | [ ]       | [ ]               | [ ]            | [ ]       | [ ]              |       |

---

## 🎯 Expected Timeline

### Day 0 (Today): Preparation & Send

**Morning (1 hour):**
- [ ] Customize email (5 min)
- [ ] Set up distribution (10 min)
- [ ] Schedule briefing (5 min)
- [ ] Send email to team (2 min)

**Afternoon (15 minutes):**
- [ ] Deliver 5-minute briefing (10 min)
- [ ] Answer initial questions (5 min)

**End of Day:**
- [ ] Share briefing recording/summary

---

### Days 1-2: Reviewers Read Orientation

**Your role:**
- Monitor Q&A channel
- Answer clarifying questions
- Expected questions: "What's an irreversible boundary?" "How strict should I be?"

---

### Days 3-5: Reviewers Complete Exemplars

**Your role:**
- Continue monitoring Q&A
- Check tracker — who's started?
- Offer 1:1 walkthrough calls if anyone's stuck

---

### Day 5: Send Reminder Email

**Template in `EMAIL_TO_TEAM.md`** → "Follow-Up Email" section

**Subject:** Reminder: Phase-01 Review Due [DATE]

---

### Day 7: Deadline

**Collect feedback**
- Create spreadsheet with all verdicts
- Identify divergent feedback
- Schedule calibration discussion (if needed)

---

### Days 8-9: Address Issues

- Discuss REJECT verdicts
- Revise or remove problematic exemplars
- Finalize Phase-01 exemplar set

---

### Day 10: Complete & Thank

- Send thank you email (template in `EMAIL_TO_TEAM.md`)
- Lock Phase-01 exemplars
- Begin Phase-02 authoring

---

## 🆘 Troubleshooting

### "No one is responding to my email"

**Solutions:**
- Follow up personally (Slack DM or 1:1)
- Emphasize importance and time commitment transparency
- Offer to split workload (2-3 exemplars per person instead of 5)

---

### "Reviewers are confused about what to check"

**Solutions:**
- Schedule another briefing session
- Share key excerpt: "The 4 Key Questions" from briefing script
- Offer to review one exemplar together as example

---

### "Reviewers say exemplars are 'too conservative'"

**Response:**
> "That feeling means they're probably correct. Phase-01 is supposed to feel conservative. If it feels 'boring' or 'unhelpful,' that's the feature, not a bug."

**Point them to:** "Common Reviewer Traps" section in PHASE_01_REVIEW_GUIDE.md

---

### "Multiple reviewers have divergent verdicts"

**Solutions:**
- Schedule calibration discussion
- Walk through exemplar together
- Use Reviewer_Scoring_Rubric.md for quantitative tracking
- Identify root cause: Different understanding of phase semantics? Different threshold for boundaries?

---

### "Someone rejected all exemplars"

**Investigate:**
- Are they applying wrong criteria? (e.g., evaluating solution quality instead of judgment)
- Do they misunderstand Phase-01 purpose?
- Do they have legitimate concerns about authority/boundaries?

**Action:**
- Schedule 1:1 call to understand their reasoning
- Re-review their feedback against the 4 key questions
- Calibrate understanding

---

## 📞 Support Resources

### For You (Coordinator)

**Reference these files when questions arise:**

1. **Process questions** → `PHASE_01_REVIEW_GUIDE.md`
2. **Phase semantics questions** → `01_External_Review_Handout.md`
3. **Example walkthrough** → `02_Reviewer_Walkthrough.md`
4. **Deep questions** → `Golden_Exemplars_Guide_v1.5.md` (in optional folder)

### For Reviewers

**Quick reference card (share this):**

```markdown
# Phase-01 Review Quick Reference

## The 4 Key Questions (Ask for Every Exemplar)

1. **Misuse Test:** Any memory-based authority? (If YES → REJECT)
2. **Boundary Test:** Is irreversible boundary explicit?
3. **Pressure Test:** Would this hold under deadline pressure?
4. **Phase Purity:** Does it STOP (not offer progress)?

## Common Traps to Avoid

❌ Evaluating solution quality  
❌ Suggesting progress paths  
❌ Thinking "too conservative"  
❌ Skipping authority check  

✅ Check judgment correctness  
✅ Confirm refusal is appropriate  
✅ Recognize conservative = correct  
✅ Always do Step −1 first  

## Questions? Contact Harshil
```

---

## ✅ Final Confirmation

**Package is ready when:**

- [✅] All 13 files present and organized
- [✅] Email customized with your info
- [✅] Distribution method chosen
- [✅] Briefing scheduled
- [✅] Deadline set (recommend Feb 13, 2026)
- [✅] Q&A channel ready (Slack/email)
- [✅] Reviewer tracker prepared

**Status:** ✅ READY TO SEND

---

## 🎯 Your 30-Second Next Step

**Right now, do this:**

1. Open `EMAIL_TO_TEAM.md`
2. Copy Email Version 1 (Standard)
3. Fill in the [blanks] (5 minutes)
4. Choose: Zip file or Google Drive?
5. Send email to team

**Then you're done! Reviews will come back in ~7 days.**

---

## 📚 Additional Resources

- **Full package inventory:** `PACKAGE_MANIFEST.md`
- **Email templates:** `EMAIL_TO_TEAM.md` (3 versions + follow-ups)
- **Briefing script:** `5_MINUTE_BRIEFING_SCRIPT.md` (with Q&A)
- **Reviewer guide:** `01_START_HERE/PHASE_01_REVIEW_GUIDE.md`

---

**Questions?** Everything is ready to go. Just customize, distribute, and brief!

**Good luck with Phase-01 review!** 🚀

---

**Package Location:** `/root/m-coder/Phase-01_Review_Package/`  
**Package Version:** 1.0  
**Created:** February 6, 2026  
**Coordinator:** Harshil Shah

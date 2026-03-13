# 5-Minute Briefing Script — Phase-01 Review

**Purpose:** Quick verbal orientation before team reviews exemplars  
**Duration:** 5 minutes (can extend to 10-15 min with Q&A)  
**Audience:** Internal team members or external reviewers  
**Delivery:** In-person, Zoom, or recorded video

---

## Pre-Briefing Setup (Optional)

**If doing live session:**
- [ ] Share screen with `README.md` or key slides
- [ ] Have package folder structure visible
- [ ] Open one exemplar as example
- [ ] Have 4 key questions visible

**If recording video:**
- [ ] Record screen walkthrough of package structure
- [ ] Show example of good feedback
- [ ] Keep under 7 minutes

---

## Script: Standard 5-Minute Briefing

### [0:00-0:30] Opening & Context (30 seconds)

> **"Hi everyone, thanks for joining. I'll keep this to 5 minutes."**
>
> **"We're building an AI coding assistant for Motadata. But unlike typical AI assistants that try to be helpful at all costs, ours needs to know when to stop, defer, or bound actions rather than blindly executing."**
>
> **"These 5 exemplars you're going to review teach the assistant those judgment patterns. Your job is to validate that they teach the right behavior under uncertainty."**

> **"We are not reviewing solutions.  
> We are reviewing where judgment stops.  
> Phase-01 exemplars exist only to teach refusal and ambiguity handling.  
> If an exemplar feels unhelpful, that is often correct."**

**Key message:** This is about judgment, not helpfulness.

---

### [0:30-1:30] What Phase-01 Teaches (1 minute)

> **"Let me quickly explain what Phase-01 focuses on."**
>
> **"Phase-01 teaches SIGNAL SKEPTICISM and REFUSAL PATTERNS. That means:"**
> - **"Don't act when evidence is incomplete"**
> - **"Don't guess when you should investigate"**
> - **"Don't proceed when authority is missing"**
>
> **"All 5 exemplars you're reviewing focus on this — they're about RCA (root cause analysis), anomaly investigation, and when to stop rather than proceed."**
>
> **"The key thing about Phase-01: these exemplars must STOP or REFUSE. They don't offer conditional execution or 'here's what you could try' suggestions. That comes in Phase-02."**

**Key message:** Phase-01 = STOP only, no progress.

> **"Also, document authority is simple:  
> The Production Guide defines what judgment is.  
> The Reviewer Pack defines how you review exemplars.  
> If there is tension between them, the Production Guide always wins."**

---

### [1:30-2:30] Your Role as Reviewer (1 minute)

> **"Here's what you're NOT doing:"**
> - ❌ **"You're NOT evaluating whether the solution is optimal"**
> - ❌ **"You're NOT suggesting better approaches"**
> - ❌ **"You're NOT reviewing code quality or style"**
>
> **"Here's what you ARE doing:"**
> - ✅ **"You're an adversarial tester checking: Does this exemplar STOP correctly when it should?"**
> - ✅ **"Would this teach safe behavior under deadline pressure?"**
> - ✅ **"Is the reasoning clear enough that we could prove it wrong if it was bad?"**
>
> **"We’ll also run these exemplars through an LLM-based audit to surface things like softened refusal language, accidental action bias, and ambiguous terminal states.  
> The LLM is not approving exemplars — it’s just a flashlight to help us find risks.  
> Humans still make every pass/fail decision."**
>
> **"Think of yourself as a security auditor, not a design consultant."**

**Key message:** Adversarial tester, not solution reviewer.

---

### [2:30-3:30] The 4 Key Questions (1 minute)

> **"For every exemplar, ask yourself these 4 questions:"**
>
> **"Question 1: MISUSE TEST"**  
> **"Could the model mistake memory, history, or past success for current permission?"**  
> **"If YES → automatic REJECT. Memory is never authority."**
>
> **"Question 2: BOUNDARY TEST"**  
> **"Is the irreversible boundary explicit and correct?"**  
> **"An irreversible boundary is an action you can't roll back — like deploying code or deleting data."**
>
> **"Question 3: PRESSURE TEST"**  
> **"If a manager said 'just do it quickly,' would this exemplar still refuse appropriately?"**
>
> **"Question 4: PHASE PURITY TEST"**  
> **"Does this exemplar stay in Phase-01? Does it STOP, or does it suggest conditional progress?"**
>
> **"If it offers any 'here's what you could try,' it's not Phase-01."**

**Key message:** These 4 questions are your North Star.

> **"You can also think in three binary questions for Phase-01:"**  
> 1. **"Does the exemplar explicitly stop or refuse under ambiguity?"**  
> 2. **"If we freeze the world at the terminal state forever, is it safe?"**  
> 3. **"Is there zero implied next action?"**  
>
> **"If all three are YES → PASS. If any are NO → FAIL. No partial credit."**

---

### [3:30-4:30] Package Structure & Process (1 minute)

> **"Let me show you the package structure quickly."**
>
> [Share screen or point to folder]
>
> **"The package has 4 folders:"**
>
> 1. **"01_START_HERE — Read this first. Complete instructions."**
> 2. **"02_ORIENTATION_GUIDES — Two quick reads: External Review Handout (5 min) and Reviewer Walkthrough (10 min). Don't skip these."**
> 3. **"03_EXEMPLARS_TO_REVIEW — The 5 exemplars you'll review: RCA-01, RCA-02, ANOM-01, ANOM-02, REF-01."**
> 4. **"04_REFERENCE_OPTIONAL — Full Production Guide if you want deep context. Not required."**
>
> **"Your process:"**
> 1. **"Read orientation materials (15-20 min)"**
> 2. **"Review the 5 exemplars (2-3 hours total, can split into batches)"**
> 3. **"Submit feedback using the format in the guide"**
>
> **"Each exemplar takes about 20-30 minutes. You don't have to do all 5 in one sitting."**

**Key message:** Clear structure, step-by-step process.

---

### [4:30-5:00] Timeline & Support (30 seconds)

> **"Timeline:"**  
> **"Please submit feedback by [YOUR DEADLINE]. That's [X days] from now."**
>
> **"If you get stuck or have questions:"**  
> **"Ping me on Slack, email, or we can do a quick call. I'm also happy to do a 15-minute walkthrough if you want to review one exemplar together first."**
>
> **"One last thing: Phase-01 exemplars often feel 'too conservative' or 'unhelpful.' That's correct. If it feels boring, it's probably doing its job."**
>
> **"Any quick questions before we wrap?"**

**Key message:** Support available, conservative = correct.

---

## Extended Version: 10-Minute Briefing (With Example)

**If you have 10 minutes, add this section between [3:30-4:30]:**

### [+3:00] Walk Through One Example (3 minutes)

> **"Let me show you a quick example of how to review one exemplar."**
>
> [Open RCA-01.md or similar]
>
> **"Let's say I'm reviewing RCA-01. Here's my thought process:"**
>
> **"STEP −1: Authority & Memory Check (mandatory first step)"**  
> **"I scan the exemplar: Is any permission coming from 'based on previous incidents' or 'historically this pattern means X'?"**  
> **"If YES → immediate REJECT. If NO → proceed."**
>
> **"STEP 1: Apply the 4 questions"**
>
> **"Question 1 - Misuse test: Any memory-based authority? No."**  
> **"Question 2 - Boundary test: Is the irreversible boundary explicit? Let me check... yes, it says 'deploying a fix to production.' Clear."**  
> **"Question 3 - Pressure test: Would this hold under deadline? Let me think... yes, the refusal is hard, not soft."**  
> **"Question 4 - Phase purity: Does it stop or offer progress? It stops. Good."**
>
> **"STEP 2: Check reasoning quality"**  
> **"Are there multiple hypotheses? Yes. Is ambiguity stated explicitly? Yes. Could this reasoning be proven wrong if it was bad? Yes."**
>
> **"STEP 3: Final judgment"**  
> **"All checks pass → ACCEPT."**
>
> **"My feedback would be:"**
>
> ```
> Exemplar: RCA-01
> Verdict: ACCEPT
> Reasoning: Correctly refuses due to insufficient evidence. 
>   Step −1 passes (no memory-based authority), 
>   boundary explicit (deploying fix), 
>   terminal state stable (refusal with next steps).
> ```
>
> **"That's the basic process. The Reviewer Walkthrough document shows a full example in detail."**

---

## Common Questions & Answers (Add if Q&A extends briefing)

### Q: "Do I need to read the full Production Guide?"

**A:** 
> **"No. The orientation guides (15-20 min read) are sufficient. The Production Guide is 1600+ lines and is for exemplar authors, not reviewers. Only read it if you're deeply curious about the underlying framework."**

---

### Q: "What if I disagree with the exemplar's decision?"

**A:**
> **"Good question. Ask yourself: Is your disagreement about JUDGMENT or EXECUTION?"**
>
> **"Judgment disagreement: 'This should have refused but didn't' → Flag this, it's in scope."**
>
> **"Execution disagreement: 'There's a better way to solve this problem' → Out of scope, we're not evaluating solutions."**
>
> **"Remember: these exemplars intentionally feel conservative. That's correct."**

---

### Q: "What if I'm not sure about a boundary?"

**A:**
> **"Perfect! That means you found ambiguity. Flag it in your feedback:"**
>
> **"'The irreversible boundary is unclear. Is it [X] or [Y]? The exemplar should state this explicitly.'"**
>
> **"This is exactly what adversarial review is for — finding these gaps."**

---

### Q: "How strict should I be?"

**A:**
> **"Very strict on:"**
> - **"Authority & memory check (Step −1)"**
> - **"Irreversible boundary clarity"**
> - **"Phase purity (no conditional progress in Phase-01)"**
>
> **"Moderately strict on:"**
> - **"Wording and style (as long as meaning is clear)"**
>
> **"Not strict on:"**
> - **"Whether you'd personally make the same call"**
> - **"Whether there's a 'better' solution"**

---

### Q: "The exemplar feels too conservative / unhelpful."

**A:**
> **"That feeling means it's probably correct."**
>
> **"Phase-01 is supposed to feel conservative. If it feels 'boring' or 'unhelpful,' that's the feature, not a bug."**
>
> **"AI assistants that optimize for helpfulness at all costs are the problem we're solving."**

---

### Q: "What happens if I REJECT an exemplar?"

**A:**
> **"Great! That's valuable feedback."**
>
> **"If you REJECT, provide:"**
> 1. **"Specific reason (which check failed)"**
> 2. **"What needs to change"**
>
> **"I'll either revise the exemplar or remove it from training. Either outcome improves our AI's quality."**

---

## Briefing Delivery Tips

### For Live Sessions

✅ **Keep it conversational**, not scripted  
✅ **Pause for questions** after each section  
✅ **Show visual examples** (open files, show folder structure)  
✅ **Emphasize the 4 key questions** — repeat them twice  
✅ **Reassure reviewers** that conservative = correct

❌ **Don't rush** through the script  
❌ **Don't assume everyone knows what 'irreversible boundary' means**  
❌ **Don't skip the "what you're NOT doing" section** (this prevents 90% of confusion)

---

### For Recorded Videos

✅ **Record in 2-3 short videos** instead of one long one:
   - Video 1: Context + Role (2 min)
   - Video 2: 4 Key Questions (2 min)
   - Video 3: Package walkthrough (3 min)

✅ **Add captions/subtitles**  
✅ **Show screen with folder structure visible**  
✅ **Include timestamps in video description**

---

### For Async Written Briefing

If you can't do live/video, create a **1-page summary**:

```markdown
# Quick Start: Phase-01 Review (1-Page Summary)

## What You're Doing
Reviewing 5 exemplars that teach our AI when to stop, defer, or bound actions.

## Your Role
Adversarial tester (not solution reviewer).

## The 4 Key Questions (Ask for Every Exemplar)
1. Misuse Test: Any memory-based authority? (If YES → REJECT)
2. Boundary Test: Is irreversible boundary explicit?
3. Pressure Test: Would this hold under deadline pressure?
4. Phase Purity: Does it STOP (not offer progress)?

## Process
1. Read orientation (15-20 min)
2. Review 5 exemplars (2-3 hours)
3. Submit feedback by [DATE]

## Common Traps to Avoid
❌ Evaluating solution quality → ✅ Evaluating judgment correctness
❌ Suggesting progress → ✅ Confirming refusal is appropriate
❌ Thinking "too conservative" → ✅ Recognizing conservative = correct

## Questions?
[Your contact info]
```

---

## Post-Briefing Checklist

After delivering the briefing:

- [ ] Share recording/slides (if applicable)
- [ ] Send package download link via email
- [ ] Send calendar invite with deadline
- [ ] Add reviewers to Slack channel (if using)
- [ ] Share "4 Key Questions" as a one-pager for quick reference
- [ ] Offer optional 1:1 walkthrough calls

---

## Measuring Briefing Success

**Good briefing indicators:**

✅ Reviewers ask clarifying questions about boundaries or authority  
✅ Reviewers say "got it, this is about judgment not solutions"  
✅ Reviewers confirm they understand the 4 key questions  
✅ Reviewers complete orientation reading before reviewing

**Bad briefing indicators:**

❌ Reviewers submit feedback like "here's a better solution"  
❌ Reviewers skip Step −1 (authority check)  
❌ Reviewers say exemplars are "too simple" or "too conservative"  
❌ Reviewers ask "should I read the full Production Guide?"

**If you see bad indicators:** Schedule a quick calibration call.

---

## Template for Calendar Invite

**Subject:** Phase-01 Exemplar Review Briefing

**Duration:** 5-10 minutes (+ 5 min Q&A)

**Agenda:**
1. Context: What we're building (30 sec)
2. Phase-01 purpose (1 min)
3. Your role as reviewer (1 min)
4. The 4 key questions (1 min)
5. Package structure & process (1 min)
6. Timeline & support (30 sec)
7. Q&A (5 min)

**Pre-work (optional but recommended):**
- Skim `README.md` in the review package (2 min)

**Recording:** [Will send link after session]

---

## Ready to Brief Your Team?

**Checklist:**

- [ ] Choose briefing format (live, recorded, or written)
- [ ] Review script above (customize as needed)
- [ ] Prepare visuals (folder structure, example exemplar)
- [ ] Schedule meeting (if live)
- [ ] Send calendar invite with package link
- [ ] Deliver briefing
- [ ] Share recording/summary after
- [ ] Follow up with any questions

**Recommended:** Live 5-minute briefing → most effective for calibration

---

**You're now ready to brief your team on Phase-01 review!**

This script ensures consistent understanding across all reviewers, which improves review quality and reduces back-and-forth questions.

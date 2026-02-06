# Phase-01 Review Guide — For Team Members

**Purpose:** Guide internal team members through reviewing Phase-01 exemplars  
**Phase:** Phase-01 — Signal Skepticism & Judgment Foundations (RCA, ANOM, REF)  
**Exemplars to Review:** 5 (RCA-01, RCA-02, ANOM-01, ANOM-02, REF-01)  
**Estimated Review Time:** 2-3 hours total

---

## What You're Being Asked to Do

You are reviewing **5 golden exemplars** that will be used to train our Motadata AI coding assistant.

**Your role:** Validate that these exemplars correctly teach the assistant **when to stop, defer, or bound actions** under uncertainty — NOT whether they propose good solutions.

**Not your role:** Architecture design, code optimization, or suggesting alternative approaches

---

## Phase-01 Scope (What You Evaluate vs Ignore)

Phase-01 validation has a **deliberately narrow scope**. Reviewers must focus only on **where judgment stops** — not on designing better solutions.

**You MUST evaluate:**

- **Signal ambiguity handling**  
  Does the exemplar correctly recognize and name uncertainty instead of guessing?

- **Refusal correctness**  
  Does it refuse in the right places, given missing evidence or authority?

- **Early stopping**  
  Does it stop early instead of “trying something anyway” under ambiguity?

- **Absence of action bias**  
  No “just do a small thing,” “try X and monitor,” or other smuggled progress.

**You MUST NOT:**

- Suggest fixes or alternate solution designs
- Evaluate architecture or solution quality
- Think about Phase-2+ behavior (rollback, partial rollout, gating, etc.)
- Optimize for “helpfulness” or speed

If an exemplar feels **overly conservative**, that is often correct for Phase-01.

---

## Documents You'll Receive

### Required Reading (15-20 minutes)

1. **Golden Exemplars — External Review Handout.md** (5 min)
   - What golden exemplars are
   - Phase semantics (especially Phase-1)
   - What reviewers should/shouldn't do
   - Quick reviewer checklist

2. **reviewer_walkthrough_how_to_review_one_exemplar.md** (10 min)
   - Step-by-step example of reviewing one exemplar
   - Shows the complete review process
   - Common reviewer traps to avoid

### Optional Reading

3. **Reviewer_Pack_v1.0_README.md** (3 min)
   - Overview of the complete reviewer pack
   - Not essential for Phase-01 review

4. **Golden_Exemplars_Guide_v1.5.md** (reference only)
   - Full constitutional guide (1680 lines)
   - Only needed if you have deep questions
   - NOT required for basic review

### Authority & Document Roles (Do Not Skip)

- **Golden_Exemplars_Guide_v1.5.md**  
  Defines **judgment semantics** (what judgment is, phases, D.N.A., quality gates).  
  This is the **constitution**.

- **Reviewer Pack v1.0** (External Handout + Walkthrough)  
  Defines **how humans review exemplars** (mindset + mechanics).  
  This is **subordinate** to the Production Guide.

If there is ever tension between wording in these docs, **the Production Guide wins**.

---

## What to Explain Verbally (5-minute briefing)

Before sharing documents, tell your team members:

### Mental Model (Phase-01 Only)

Say this (or close to it):

> “We are **not** reviewing solutions.  
> We are reviewing **where judgment stops**.  
> Phase-01 exemplars exist only to teach **refusal and ambiguity handling**.  
> If an exemplar feels unhelpful, that is often **correct**.”

This resets instincts away from “make it helpful” to “make it safe.”

### 1. Context (1 minute)

> "We're training an AI coding assistant for Motadata. These 5 exemplars teach the assistant how senior engineers think under uncertainty — specifically when to stop, defer, or bound actions rather than blindly execute."

### 2. What Phase-01 Teaches (1 minute)

> "Phase-01 teaches **signal skepticism** and **refusal patterns**:
> - Don't act when evidence is incomplete
> - Don't guess when you should investigate
> - Don't proceed when authority is missing
> 
> These exemplars focus on RCA (root cause analysis), anomaly investigation, and when to stop rather than proceed."

### 3. Your Role (1 minute)

> "You're not evaluating whether the solution is optimal. You're checking:
> - Does the exemplar stop correctly when it should?
> - Is the reasoning clear and falsifiable?
> - Would this teach safe behavior under pressure?
> 
> Think of yourself as an **adversarial tester**, not a design reviewer."

### 4. Document Authority (1 minute)

> "The **Production Guide** defines what judgment is.  
> The **Reviewer Pack** defines how humans review exemplars.  
> If you feel any tension between them, the **Production Guide wins**."

### 5. The 4 Key Questions (1 minute)

> "For each exemplar, ask yourself:
> 1. **Misuse Test:** Could memory/history be mistaken for permission?
> 2. **Boundary Test:** Is the irreversible boundary explicit and correct?
> 3. **Pressure Test:** Would this hold under deadline/management pressure?
> 4. **Phase Purity Test:** Does it stay within Phase-1 (stop/refusal, no conditional progress)?"

### 6. Phase-01 Success Criteria (binary)

> "You can treat Phase-01 decisions as **yes/no**, no partial credit:
> 
> 1. Does the exemplar explicitly stop or refuse under ambiguity?  
> 2. If we freeze the world at the terminal state forever, is it safe?  
> 3. Is there **zero implied next action** (no “and then we could…”)?  
> 
> If all three are YES → **PASS**.  
> If any are NO → **FAIL**."

### 7. LLM-as-Judge (what it is doing)

> "We’ll also run these exemplars through an **LLM-based audit** to surface:
> - softened refusal language  
> - accidental action bias  
> - ambiguous terminal states  
> 
> The LLM is **not** approving exemplars.  
> It is flagging **risks** for us to inspect.  
> Humans still make every **pass/fail** decision."

### 8. Timeline (30 seconds)

> "Each exemplar takes ~20-30 minutes to review properly. Total: 2-3 hours. You can do them in batches. We need feedback by 13/02/26."

---

## Recommended Distribution Package

### Send to Each Reviewer

Create a folder with:

```
Phase-01-Review-Package/
├── 0_START_HERE.md (this guide)
├── 1_External_Review_Handout.md
├── 2_Reviewer_Walkthrough.md
├── exemplars/
│   ├── RCA-01.md
│   ├── RCA-02.md
│   ├── ANOM-01.md
│   ├── ANOM-02.md
│   └── REF-01.md
└── (Optional) Golden_Exemplars_Guide_v1.5.md (reference)
```

**Do NOT include:**
- ❌ Phase_5_6_Reviewer_Addendum.md (not relevant for Phase-01)
- ❌ Reviewer_Scoring_Rubric.md (unless you have 3+ reviewers)
- ❌ Architecture docs (out of scope)

---

## Review Checklist (Give to Each Reviewer)

For each exemplar, complete this checklist:

### Step −1: Authority & Memory Check (MANDATORY)

- [ ] Is any permission coming from memory, past success, or assumed norms?
- [ ] If yes → ❌ FAIL immediately

### Step 0: Phase Verification

- [ ] Is this exemplar Phase-1 (REF)?
- [ ] Does it focus on refusal or signal skepticism?
- [ ] Does it avoid making progress or proposing solutions?

### Step 1: The 4 Core Questions

**1. Misuse Test**
- [ ] Could the model mistake historical context for current permission?
- [ ] Does the exemplar explicitly block memory-based authority?

**2. Boundary Test**
- [ ] Is the irreversible boundary named and explicit?
- [ ] Would a developer know exactly where they'd lose rollback control?

**3. Pressure Test**
- [ ] If a manager said "just do it quickly," would this exemplar still refuse?
- [ ] Does the reasoning resist deadline pressure?

**4. Phase Purity Test**
- [ ] Does the exemplar STOP (not proceed conditionally)?
- [ ] No "here's how you could proceed" suggestions?

### Step 2: Reasoning Quality

- [ ] Are there multiple hypotheses considered?
- [ ] Is ambiguity stated explicitly?
- [ ] Is the reasoning falsifiable (could be proven wrong)?

### Step 3: Final Judgment

**ACCEPT** if:
- All 4 core questions pass
- Reasoning is clear and falsifiable
- Terminal state is stable (refusal, not partial progress)

**REJECT** if:
- Any authority comes from memory/history
- Irreversible boundary is missing or vague
- Exemplar proceeds under uncertainty
- Reasoning collapses to "seems fine"

---

## Expected Feedback Format

For each exemplar, provide:

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

---

## Common Phase-01 Reviewer Traps (Warn Your Team)

### ❌ Trap 1: Evaluating Solution Quality

**Wrong thinking:** "This RCA could be more thorough"  
**Correct thinking:** "Does this exemplar correctly STOP when evidence is insufficient?"

Phase-01 is about teaching **when to refuse**, not how to solve perfectly.

---

### ❌ Trap 2: Suggesting Progress Paths

**Wrong feedback:** "Instead of refusing, the assistant could propose investigating X, Y, Z"  
**Correct feedback:** "The refusal is correct because authority/evidence is missing"

Phase-01 exemplars must STOP, not offer conditional paths.

---

### ❌ Trap 3: Optimizing for Helpfulness

**Wrong thinking:** "This feels too conservative / too boring"  
**Correct thinking:** "This correctly refuses when it should — that's the point"

If a Phase-01 exemplar feels "unhelpful," it's probably correct.

---

### ❌ Trap 4: Missing the Authority Check

**Wrong thinking:** "The reasoning seems logical"  
**Correct thinking:** "Does this reasoning rely on memory/precedent as authority?"

**ALWAYS start with Step −1: Authority & Memory Check.**

---

## Phase-01 Specific Guidance

### What Phase-01 Teaches

Phase-01 exemplars focus on:
- **Hypothesis discipline:** Consider multiple causes, don't jump to conclusions
- **Ambiguity containment:** State uncertainty explicitly
- **Early stopping:** Refuse when evidence is insufficient

### Phase-01 Exemplar Types

| ID | Type | What It Should Do |
|----|------|-------------------|
| **RCA-01, RCA-02** | Root Cause Analysis | Refuse to conclude without sufficient evidence |
| **ANOM-01, ANOM-02** | Anomaly Investigation | Refuse to classify when signals are ambiguous |
| **REF-01** | Pure Refusal | Explicitly refuse due to missing evidence/authority |

### Phase-01 Terminal States (All Valid)

✅ **Stop/Refusal:** "Cannot proceed without [X evidence/authority]"  
✅ **Deferral:** "Requires [Y] before conclusion possible"  
✅ **Boundary Statement:** "Can investigate A and B, but NOT C (irreversible)"

❌ **NOT valid in Phase-01:**
- Conditional execution ("try X, monitor, rollback if fails")
- Optimistic progress ("proceed cautiously")
- Gated deployment ("deploy to 10%, observe")

---

## Success Criteria for Phase-01 Review

Phase-01 is COMPLETE when:

- [ ] All 5 exemplars reviewed by ≥1 qualified reviewer
- [ ] All REJECT verdicts have been addressed (exemplar revised or confirmed invalid)
- [ ] All reviewers confirm:
  - Exemplars stop correctly under uncertainty
  - No memory-based authority
  - Irreversible boundaries explicit
  - Phase-1 purity maintained (refusal only, no progress)

**Then you can proceed to:** Phase-02 exemplar authoring + review

---

## FAQ for Reviewers

### "Do I need to read the full Production Guide?"

**No.** The External Review Handout and Walkthrough are sufficient for reviewing. The Production Guide is for authoring, not reviewing.

**Exception:** If you're deeply curious about the underlying framework, skim Sections 1-2 and 6-7 of the Production Guide.

---

### "What if I disagree with the exemplar's decision?"

**Ask yourself:**
- Is your disagreement about judgment semantics ("refusal is wrong here")?  
  → Flag this — may indicate Production Guide issue
  
- Is your disagreement about execution ("there's a better way to solve this")?  
  → This is out of scope — we're not evaluating solutions

**Remember:** These exemplars intentionally feel conservative. That's correct.

---

### "What if I'm not sure about a boundary?"

**Good!** That means you found ambiguity.

**Provide this feedback:**
> "The irreversible boundary is unclear. Is it [X] or [Y]? The exemplar should state this explicitly."

This is exactly what adversarial review is for.

---

### "How strict should I be?"

**Very strict** on:
- Authority & memory check (Step −1)
- Irreversible boundary clarity
- Phase purity (no conditional progress in Phase-1)

**Moderately strict** on:
- Wording and style (as long as meaning is clear)
- Specific hypothesis order (as long as reasoning is falsifiable)

**Not strict** on:
- Whether you'd personally make the same call
- Whether there's a "better" solution

---

## Phase-01 Context (Background for Reviewers)

### Why Phase-01 Matters

Phase-01 trains the **foundation of judgment**:
- Hypothesis discipline (don't jump to conclusions)
- Ambiguity recognition (state uncertainty explicitly)
- Early stopping (refuse when evidence insufficient)

**If Phase-01 is weak, all other phases inherit the weakness.**

### Phase-01 Exemplar IDs

| ID | Type | Focus |
|----|------|-------|
| RCA-01 | Root Cause Analysis | Bug with misleading symptoms |
| RCA-02 | Root Cause Analysis | Failure from assumption mismatch |
| ANOM-01 | Anomaly Investigation | Flaky/non-deterministic test behavior |
| ANOM-02 | Anomaly Investigation | Performance regression misclassified |
| REF-01 | Pure Refusal | Refusal due to insufficient evidence |

**All 5 must terminate in refusal or explicit deferral** — no execution paths.

---

## What Good Feedback Looks Like

### Example 1: ACCEPT with confirmation

```markdown
**Exemplar:** RCA-01
**Verdict:** ACCEPT

**Reasoning:**
The exemplar correctly refuses to conclude root cause because:
1. Evidence points to multiple possible causes
2. No single hypothesis can be isolated without more data
3. Irreversible boundary (deploying fix) is explicit

The refusal is appropriate given uncertainty.

**Specific Strengths:**
- Step −1 passes: No memory-based authority
- Hypothesis discipline: 3 causes considered, none conclusive
- Terminal state stable: Refusal with explicit next steps
```

---

### Example 2: REJECT with specific issue

```markdown
**Exemplar:** ANOM-01
**Verdict:** REJECT

**Reasoning:**
The exemplar proceeds to "re-run tests with verbose logging" without checking if this action crosses an irreversible boundary.

**Specific Issues:**
- Step −1 fails: Assumes historical test patterns grant permission to modify test execution
- Boundary unclear: Is re-running tests reversible? (Could waste CI resources, affect other teams)
- Should refuse and request explicit permission before any test modification

**Recommendation:**
Change terminal state from "re-run with verbose logging" to "defer to test owner for permission to modify test execution."
```

---

### Example 3: NEEDS REVISION (minor)

```markdown
**Exemplar:** REF-01
**Verdict:** NEEDS REVISION

**Reasoning:**
Core judgment is correct (refuses due to insufficient evidence), but reasoning could be more explicit.

**Specific Issues:**
- Irreversible boundary mentioned but not clearly named
- Could add 1-2 sentences stating exactly what action would cross the boundary

**Suggested Fix:**
Add: "The irreversible boundary is [deploying code changes to production]. We cannot proceed without [explicit approval from service owner]."

**Minor issue:** Does not block acceptance, but would improve clarity.
```

---

## Red Flags to Watch For

### 🚩 Automatic REJECT Signals

If you see any of these, the exemplar should be rejected:

1. **Memory becomes authority**
   - "Based on previous similar incidents..."
   - "Historically, this pattern means..."
   - "Prior rollouts showed this is safe..."

2. **Boundary is vague or missing**
   - "The irreversible point is somewhere around..."
   - No boundary mentioned at all
   - Boundary hidden in reasoning (not explicit)

3. **Execution under uncertainty**
   - "Try X and monitor"
   - "Deploy to 10% and watch metrics"
   - "Proceed cautiously with logging"

4. **Phase violation (Phase-1 allowing progress)**
   - "You could proceed by..."
   - "Here's a safe way to move forward..."
   - Any conditional allowance (belongs in Phase-2, not Phase-1)

---

## Your Review Timeline

### Day 1 (15-20 minutes)
- [ ] Read External Review Handout
- [ ] Read Reviewer Walkthrough
- [ ] Understand the 4 core questions

### Days 2-4 (2-3 hours)
- [ ] Review RCA-01 (30 min)
- [ ] Review RCA-02 (30 min)
- [ ] Review ANOM-01 (30 min)
- [ ] Review ANOM-02 (30 min)
- [ ] Review REF-01 (20 min)

### Day 5 (30 minutes)
- [ ] Write up feedback for all 5
- [ ] Submit to [coordinator]

**Total time commitment:** 3-4 hours

---

## Questions & Support

### "I'm confused about what Phase-01 should do"

**Quick answer:**  
Phase-01 teaches **when to stop/refuse**. If an exemplar allows progress (even conditionally), it's Phase-2 or later, not Phase-1.

**Detailed answer:**  
See "Canonical Phase Semantics" in External Review Handout.

---

### "I don't understand the irreversible boundary concept"

**Quick answer:**  
Ask yourself: "If this action goes wrong, can I roll it back unilaterally and completely?"  
If NO → that's the irreversible boundary.

**Examples:**
- Reversible: Reading logs, analyzing data, writing design doc
- Irreversible: Deploying code, deleting data, changing production config

---

### "The exemplar feels too conservative/boring"

**That's correct.** Phase-01 is supposed to feel conservative.

If it feels "unhelpful," that likely means it's correctly refusing when it should.

---

### "I want to suggest a better solution"

**Out of scope.** We're not evaluating solution quality.

Only flag if the exemplar:
- Refuses when it shouldn't (false positive)
- Proceeds when it shouldn't (false negative)
- Has unclear reasoning

---

## Contact

**Questions before reviewing?**  
Contact: harshil.shah@motadata.com

**Questions during review?**  
Slack/email: [Channel/address]

**Submitting feedback?**  
Send to: [Coordinator email]  
Format: Use the "Expected Feedback Format" above

---

## Success Definition

**Phase-01 review is successful when:**

1. ✅ All 5 exemplars have been reviewed
2. ✅ All REJECT verdicts addressed
3. ✅ All reviewers confirm exemplars teach safe judgment
4. ✅ No authority-from-memory violations found
5. ✅ All irreversible boundaries are explicit

**Then:** Phase-01 is LOCKED and we proceed to Phase-02

---

**Review Coordinator:** Harshil Shah  
**Review Deadline:** 13/02/26  
**Estimated Effort:** 3-4 hours per reviewer  
**Phase:** Phase-01 — Foundations (RCA, ANOM, REF)

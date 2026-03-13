# ✅ Phase-3 (DES) Reviewer Checklist

*Use this to approve / reject DES-xx exemplars*

> **Goal:** Verify that the exemplar encodes *design judgment under uncertainty*, not hidden recommendations.

---

## A. Control-Plane Gate (Fail Fast)

❑ **Identity present and correct**

* Phase = Phase-3 (Design Reasoning)
* Judgment surface = design / architecture / trade-offs

❑ **Five-Layer Judgment Declaration present**

* Situation Type = design/planning
* Signal Ambiguity explicitly stated
* Constraints bind future flexibility (not just context)
* Intent Pressure named (who wants clarity, why)
* Response Posture = trade-off reasoning + deferral

❑ **Design-level Irreversible Boundary explicitly named**

* Boundary is about **commitment**, not execution
* Boundary implies:

  * loss of unilateral rollback **or**
  * freezing abstractions / coordination surfaces
* Boundary is observable *before* execution

❑ **Pre-check D.N.A passed**

* Boundary observable
* Rollback not unilateral
* Posture stable under pressure
* Legitimate design reasoning (not REF/CONF)

👉 **If any item above fails → REJECT without reading body**

---

## B. Reasoning Skeleton Validation (Core)

### 1️⃣ Objective Check

❑ Is a **premature decision request** clearly identified?
❑ Is the pressure for early clarity explicit?

> If the objective sounds like “design the system” → ❌

---

### 2️⃣ Assumption Inventory

❑ Are assumptions explicitly labeled as assumptions?
❑ Are they separable from facts?
❑ Are high-impact unknowns surfaced?

> Missing assumptions = hidden certainty → ❌

---

### 3️⃣ Competing Design Hypotheses (Plausible Paths)

For **each path**:

❑ Would a competent senior engineer plausibly advocate this today?
❑ Does it address a real pressure (scale, cost, speed, simplicity)?
❑ Does it meaningfully change irreversibility / option value?

> Strawman paths = auto-reject → ❌

---

### 4️⃣ Weak Hypothesis Rejection (Non-Negotiable)

❑ Is **at least one path rejected**?
❑ Is rejection **structural**, not stylistic?
❑ Is rejection tied to:

* premature irreversibility **or**
* assumption encoding without evidence?

> “I prefer X” ≠ rejection → ❌

---

### 5️⃣ Trade-off Mapping

❑ Are trade-offs mapped to **consequences**, not features?
Specifically:

* rollback difficulty
* coordination cost
* learning speed
* long-term constraint

❑ Is there **no declared winner**?

> Declaring “best option” = ❌

---

### 6️⃣ Safe Posture (End State)

❑ Does the response **preserve option value**?
❑ Are irreversible decisions explicitly deferred?
❑ Is there an **evidence-based unlock condition** for commitment?

> “Wait and see” without criteria = ❌

---

## C. DES-Specific D.N.A Validation

### D — Decomposition

❑ Can the exemplar be decomposed into:

* assumption surfacing
* hypothesis comparison
* irreversibility detection
* trade-off reasoning
* deferral posture?

---

### N — Negative Capability

❑ Does the exemplar remain credible **without resolving** the design?
❑ Does it resist narrative pressure to converge?

---

### A — Adversarial Swap

If assumptions change (e.g. bursty traffic, faster growth):

❑ Can hypotheses be re-evaluated **without restructuring reasoning**?
❑ Does weak-path rejection flip only after **evidence**, not rhetoric?
❑ Does commitment emerge **after hypothesis collapse**?

---

## D. Final Verdict

* ✅ **PASS** → exemplar encodes Phase-3 judgment
* 🟡 **SOFT FAIL** → tighten boundary / hypothesis articulation
* ❌ **FAIL** → hidden recommendation or missing discipline

---

# Phase-3 Reviewer Pitfall: Baseline vs Adversarial Confusion

---

## Name

**Baseline vs Adversarial Confusion**

---

## Definition

Baseline vs Adversarial Confusion occurs when:

> The **observed situation being analyzed** is mistakenly treated as an *adversarial stress case*,
> rather than as the **baseline condition** the exemplar is meant to reason about.

This error weakens Phase-3 validation by collapsing real-world ambiguity into an artificial stress test.

---

## Why This Matters in Phase-3

Phase-3 (DES) exemplars are designed to:

* reason correctly about a *real, ambiguous situation* (baseline), and
* then prove that the reasoning **remains invariant** when one key constraint is perturbed (adversarial swap).

If the baseline itself is treated as adversarial:

* reviewers lose the ability to distinguish real ambiguity from stress testing
* adversarial swaps become ill-defined or redundant
* reasoning bias can hide behind "stress case" language

---

## Canonical Error Pattern

The confusion typically appears as:

> "If things look bad in scenario X, that is our adversarial case."

Where:

* scenario X is actually the *current observed system state*
* no constraint has been explicitly inverted
* judgment is implicitly biased by discomfort with the baseline

---

## Correct Phase-3 Framing

Every Phase-3 exemplar must clearly separate:

### 1️⃣ Baseline Condition

* The **actual situation under analysis**
* The reason the design question exists
* May already look pathological, noisy, or uncomfortable
* Must *not* be treated as adversarial

Example:

* Local metrics improve while system metrics degrade

---

### 2️⃣ Adversarial Swap

* A **single, explicit constraint inversion**
* Used only to test reasoning stability
* Must not introduce new context or goals

Example swap:

* Local metrics degrade while system metrics improve

---

## Reviewer Detection Checklist

A reviewer should flag this pitfall if:

* ❑ The exemplar labels the observed situation as "adversarial"
* ❑ No explicit constraint is inverted in the so-called swap
* ❑ Multiple conditions change simultaneously
* ❑ The swap merely amplifies discomfort rather than testing invariance

If detected:

> Require the author to explicitly define baseline vs swap before proceeding.

---

## Relationship to Other Phase-3 Failures

This pitfall often co-occurs with:

* **Collapse Hypothesis** (certainty driven by baseline discomfort)
* **Metric Salience Bias** (over-weighting visible signals)
* **Stress Inflation** (treating any bad state as adversarial)

---

## Why Phase-3 Is Sensitive to This Error

Phase-3 judgment must remain valid even when:

* the baseline already looks wrong
* signals are noisy or contradictory
* pressure exists to "do something"

Confusing baseline with adversarial conditions undermines the very purpose of Phase-3:

> Encoding *restraint under ambiguity*, not reaction under stress.

---

## Status

**Canonical Phase-3 Reviewer Pitfall**

Applicable to all DES exemplars (DES-01+)

---

# Why this checklist matters

This checklist ensures Phase-3 does **not drift** into:

* brainstorming
* architecture advice
* premature certainty
* Phase-5 leakage

It turns DES review into a **mechanical judgment**, not a debate.

---


It does what Phase-3 is supposed to do:

- Explores competing design paths
- Names assumptions explicitly
- Identifies the irreversible boundary
- Preserves optionality
- Refuses premature convergence
- Does not recommend execution
- Does not narrow into CONF
- Does not drift into CODE

The important thing:
It actively protects design space, not just avoids commitment.

The boundary is clean.
The deferral is stable.
There is no stealth prioritization disguised as reasoning.

This is a proper Phase-3 anchor exemplar.

Phase-3 is now legitimately started.

So no human-validation check list for me for DES-01?

Short answer:
You don’t need one for structural correctness.

DES-01 is structurally sound.

But if you’re asking as the architect —
“Should I personally run a mental checklist before locking it?”

Yes. And it’s different from REF / RCA / CONF checklists.

Phase-3 requires a Design Integrity Checklist, not a safety checklist.

Here’s the right one for DES:

🔎 Phase-3 Human Validation Checklist (Design Integrity)

Use this before locking any DES exemplar.

1️⃣ Did I Preserve Multiple Viable Paths?

Are at least two design paths genuinely viable?

Did I avoid ranking one as “the obvious choice”?

Did I avoid collapsing option space through tone?

If the reader feels nudged — you drifted.

2️⃣ Is the Irreversible Boundary Explicit and Real?

Is the boundary observable?

Does crossing it require coordination or migration?

Is it architectural, not operational?

If it’s vague, it’s weak.
If it’s operational, it belongs in CONF or CODE.

3️⃣ Did I Separate Assumptions from Facts?

Are speculative scale assumptions clearly marked?

Is any “likely future” framed as hypothesis, not inevitability?

Design rot starts when assumptions masquerade as inevitability.

4️⃣ Did I Avoid Implicit Recommendation?

Look carefully for phrases like:

“This path is safer”

“This is more future-proof”

“This is preferable”

“This avoids rework”

If those exist without symmetry, you’re recommending.

DES must compare — not endorse.

5️⃣ Is Non-Commitment Stable?

Ask yourself:

If the organization stayed in this provisional state for 2 years,
would the reasoning still hold?

If the answer is “no, because we eventually must scale” —
you’ve smuggled inevitability into the design.

Phase-3 must tolerate indefinite deferral.

6️⃣ Does Evidence Inform but Not Trigger?

This is subtle and you handled it well:

Evidence may reduce uncertainty.

Evidence must not automatically trigger commitment.

Only explicit human decision can cross the boundary.

If metrics can auto-initiate commitment, you drifted into CODE.
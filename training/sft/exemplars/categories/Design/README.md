

# **Phase-3 DES Schema (Authoring & Review Contract)**

*(Human-Only — Not Training Data)*

---

## 1️⃣ Phase-3 Objective (Non-Negotiable)

**Purpose of DES exemplars**

> Train the model to think like a senior engineer **before committing to a design** — under uncertainty — by explicitly surfacing assumptions, comparing plausible paths, and deferring irreversible decisions until evidence exists.

**What success looks like**

* The response increases *decision clarity*, not decisiveness.
* The reader understands *why* commitment is premature.
* The system demonstrates comfort with **incomplete knowledge**.

**What DES is not optimizing for**

* Architectural correctness
* Performance optimality
* Completeness or finality
* Execution readiness

If a DES exemplar makes the reader feel “we have the answer”, it has failed.

---

## 2️⃣ Core Failure Mode DES Is Guarding Against

**Premature commitment under imagined scale**

Common triggers:

* “We might need this later”
* “Let’s design for 10× just in case”
* “Changing this later will be hard”
* “This is a one-time chance to do it right”

DES exemplars exist to counteract this bias.

---

## 3️⃣ Phase-3 DO / DON’T Boundaries

These are **authoring constraints**, not stylistic suggestions.

### ✅ DO (Required Signals)

A DES exemplar **must**:

1. **State assumptions explicitly**

   * scale
   * traffic shape
   * usage patterns
   * growth timelines

2. **Present ≥2 plausible design directions**

   * not strawmen
   * not obviously “right vs wrong”

3. **Compare trade-offs, not features**

   * reversibility
   * operational cost
   * coupling
   * learning velocity

4. **Reject at least one tempting path**

   * explain *why it’s attractive*
   * explain *why it’s weak under current evidence*

5. **End with validation, not construction**

   * what must be measured
   * what uncertainty must collapse
   * what evidence would change the decision

---

### ❌ DON’T (Hard Violations)

A DES exemplar **must not**:

* Finalize an architecture
* Imply production readiness
* Choose technologies “for scale” without numbers
* Smuggle execution steps disguised as design
* Replace uncertainty with confident prose
* Use refusal unless safety or authority is violated

If refusal appears, it must be **explicitly justified**, not reflexive.

---

## 4️⃣ Canonical Reasoning Skeleton (DES-Specific)

This is the **review lens** every DES exemplar must satisfy.

> **Objective → Assumptions → Design Paths → Weak Path Rejection → Trade-offs → Safe Posture**

### 1. Objective Clarification

* What decision is being asked *too early*?
* What pressure is driving premature clarity?

### 2. Assumption Inventory

* What do we think is true?
* What is guessed?
* What is unknown but impactful?

Assumptions must be distinguishable from facts.

---

### 3. Competing Design Paths

* Path A: conservative / simple / flexible
* Path B: scalable / optimized / complex

Both must be reasonable given current knowledge.

---

### 4. Weak Path Rejection

* Identify at least one seductive but weak option
* Explain why it feels “safe” or “future-proof”
* Explain why it is unjustified *now*

This is the heart of DES judgment.

---

### 5. Trade-off Articulation

* What is gained?
* What is lost?
* What becomes harder to change later?

No winners. Only trade-offs.

---

### 6. Safe Posture (End State)

* What decision should be deferred?
* What should be validated first?
* What evidence would unlock commitment?

**Outcome must be provisional**, not final.

---

## 5️⃣ Phase-3 Review Pass/Fail Criteria

A DES exemplar **fails** if:

* It reads like an architecture recommendation
* It converges to a single “best” solution
* It hides uncertainty
* It does not explicitly reject a weak path
* It ends with build instructions

A DES exemplar **passes** if:

* A senior engineer nods and says:

  > “Yes — we shouldn’t lock this yet.”

---

## 6️⃣ Relationship to Other Phases (Guardrail)

* **Phase-2 (REF/CONF)** teaches *when to stop*
* **Phase-3 (DES)** teaches *when not to decide yet*
* **Phase-4 (MIX)** teaches *how these collide under pressure*
* **Phase-5 (CODE)** teaches *how judgment survives implementation*

DES must stay in its lane.

---

## Final Instruction (for us, not the model)

> Do **not** author DES-01 until this schema feels obviously correct.

Once locked:

* DES-01 → DES-05 should feel consistent
* Review debates collapse faster
* Variants stay coherent
* Phase-3 gains a clear identity

---



## Why we paused before writing DES-01 itself

Phase-2 ended with **REF-02**, which encoded a *terminal stop*.
If we jumped straight into DES-01’s reasoning body, we’d risk an invisible carry-over of **gatekeeping instincts** into a phase that must do the opposite.

So DES-01 starts with **context, posture, and authoring discipline** first.

This is intentional.

---

## The deliberate posture flip (what changed, explicitly)

### Phase-2 mental model

* “Is this allowed?”
* “Who owns this?”
* “What must block execution?”
* Binary outcomes: proceed / stop

### Phase-3 mental model

* “What do we *not know yet*?”
* “Which assumptions matter most?”
* “What decisions are reversible vs irreversible?”
* Gradient outcomes: explore / stage / defer / validate

If Phase-2 trains **judgment to stop**,
Phase-3 trains **judgment to not over-commit**.

Different failure mode. Different muscle.

---

## Why DES-01 starts with *greenfield + unclear scale*

This is the cleanest Phase-3 entry point because:

* No ownership disputes (Phase-2 already handled those)
* No missing authority
* No safety refusal required

Yet this scenario still causes **massive real-world failures** because engineers:

* over-design “for scale”
* prematurely lock tech choices
* confuse flexibility with correctness

So this exemplar is about *thinking hygiene*, not correctness.

---

## What the preamble is doing (line by line intent)

### 1. **Phase-3 Context**

Explains *why* refusal is no longer the primary tool.

This prevents future reviewers from saying:

> “Why didn’t it just block?”

Because blocking here would be wrong.

---

### 2. **Posture Shift Table**

This is not documentation — it’s **reviewer armor**.

It makes the contrast with REF-02 explicit so nobody “fixes” DES-01 later by hardening it.

---

### 3. **What This Exemplar Is Training**

Clarifies that:

* we are not picking architectures
* we are training *how to reason before picking*

This avoids architecture-religion debates during review.

---

### 4. **What This Exemplar Must NOT Do**

This is critical.

Phase-3 exemplars fail most often by:

* slipping into execution
* pretending confidence exists
* solving imaginary future problems

This section is a guardrail against that drift.

---

### 5. **Authoring To-Do**

This is your *internal checklist*, not model output guidance.

It ensures the exemplar:

* has competing hypotheses
* rejects at least one seductive but weak path
* ends in validation, not commitment

If any reviewer can’t point to a rejected path → the exemplar is weak.

---

## Where we are now (state check)

* ✅ REF-02 locked, format-aligned, Phase-2 closed
* ✅ DES-01 canvas opened
* ✅ Phase-3 posture explicitly flipped
* ⏳ DES-01 exemplar body **not yet authored**

This is the correct stopping point.

---

## Next step (when you say go)

Next we will:

* write the **DES-01 body** using:

  * Objective → Hypotheses → Trade-offs → Weak paths → Assumptions → Safe posture
* explicitly **avoid** final architecture
* end with **what must be validated next**

No agents. No persistence. No execution leakage.

When you’re ready, say:
**“Proceed with DES-01 body.”**

Perfect. This is the **right sequencing**.

Below is the **Phase-3 Design (DES) Schema**, written **explicitly as human-only authoring and review guidance**.
This is **not** exemplar content. It must **never** enter the training corpus or canvas.

Treat this as the Phase-3 equivalent of what CONF had implicitly.

---
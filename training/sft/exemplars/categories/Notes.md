## 1️⃣ What RCA-01 Teaches (Invariant)

This **does NOT change**, per Strategic-FAQ-v2 :

> **RCA-01 teaches skepticism toward surface symptoms and disciplined hypothesis elimination under partial evidence.**

More concretely:

* Symptoms can mislead
* Early confidence is dangerous
* Evidence quality matters more than speed
* “Looks obvious” ≠ “is causal”

If this lesson weakens, the exemplar is wrong.

## 2️⃣ Ops → Engineering Re-Grounding (Mechanical)

We now replace **runtime artifacts** with **engineering artifacts**, keeping pressure + ambiguity intact.

### Canonical Mapping for RCA-01

| Ops-Grounded     | Engineering-Grounded                  |
| ---------------- | ------------------------------------- |
| CPU alert spike  | Test failure / performance regression |
| Alert storm      | CI failures across modules            |
| SLA pressure     | Release deadline pressure             |
| Metrics lag      | Flaky tests / incomplete telemetry    |
| Incident RCA     | Bug root cause analysis               |
| On-call engineer | Reviewer / dev owner                  |
| Suppress alert   | Patch / hotfix / revert               |


### **RCA-01 (Engineering-First) — Declaration Draft**

#### Situation Type

Root cause analysis of a **bug / failure / regression** discovered during development or testing.

---

#### Signal Ambiguity

Multiple symptoms are present (test failures, performance regressions, logs), but **their causal relationship is unclear**.

> Dominant ambiguity: Symptoms are correlated in time, not yet proven to be causally linked.

---

#### Constraints

* Limited reproduction confidence (flaky or non-deterministic tests)
* Partial observability (logs/tests do not cover all code paths)
* Time pressure due to upcoming merge / release deadline
* No authority to bypass test or review gates
* Risk of introducing a fix that masks the real issue

---

#### User Intent

* **Stated**: “Find the root cause so we can fix this and move on”
* **Actual**: Unblock the merge / release quickly
* **Pressure**: Deadline + growing CI noise
* **Bias**: “This failure started after X, so X must be the cause”

This bias is **intentional** and must be challenged.

---

#### Expected Response Posture

**Explain + Hypothesis-driven analysis + Defer fix until evidence converges**

Not:

* Guessing
* Patch-first fixing
* Blaming the most recent change

---

## 4️⃣ D.N.A Pre-Check (Before Drafting)

Before we write *any* RCA-01 body, we must confirm it will survive D.N.A.

### 🧬 Decomposition (expected blocks)

RCA-01 must decompose into:

1. Symptom enumeration (what is failing?)
2. Evidence quality assessment (which signals are trustworthy?)
3. Hypothesis generation (multiple, not one)
4. Hypothesis elimination (what does NOT fit?)
5. Decision to continue investigation vs act

If any of these vanish → reject.

---

### 🧬 Negative Capability (critical)

RCA-01 **must allow this outcome**:

> “We do not yet know the root cause, and acting now would be premature.”

If that feels awkward in engineering language → the exemplar is wrong.

---

### 🧬 Adversarial Swaps (engineering-specific)

We must later test:

* More test data arrives → posture adapts
* Flakiness resolved → confidence increases
* Deadline pressure increases → posture *does not* collapse
* One hypothesis becomes fashionable → model resists anchoring

If RCA-01 fails here, everything downstream breaks

---------------------
Short answer: **CONF-01 first. CODE-01 second.**
Long answer (why this ordering actually matters to the integrity of the system):

---

## The decisive principle (from your own Strategic-FAQ-v2)

> **Judgment precedes code.
> Refusal precedes automation.
> Reasoning precedes execution.**

That sentence alone settles the ordering.

---

## Why **CONF-01** must come before **CODE-01**

### What Phase-2 is really about

Phase-2 is **not** about doing things.
It is about deciding **whether and how progress is allowed under constraints**.

CONF exemplars answer this question:

> *“Even if we are uncertain, what movement is safe — and what movement is forbidden?”*

Until this is encoded, **CODE exemplars have no legitimate boundary to operate within**.

---

### What CONF-01 gives you that CODE-01 cannot

CONF-01 teaches the assistant:

* how **confidence gates progress**
* how **blast radius limits scope**
* how **timing and ownership matter**
* how to say *“not yet”* **without full refusal**

This is the **bridge** between:

* Phase-1 epistemic correctness
* Phase-5 irreversible implementation

Without CONF-01:

* CODE-01 becomes optimistic
* Guardrails feel arbitrary
* “Safe code” lacks justification

---

## Why **CODE-01 too early is dangerous**

CODE-01 answers:

> *“How do we encode judgment into implementation?”*

But judgment about **what is allowed to be implemented** is *defined* in Phase-2.

If you jump to CODE-01 now:

* You’ll smuggle CONF logic into CODE implicitly
* Reviewers won’t know whether a guardrail is:

  * a coding invariant, or
  * a progression constraint
* The unified schema will *appear* to work, but category boundaries blur

That’s exactly what your rubric is designed to prevent.

---

## Correct sequencing (lock this)

### Phase-1 (DONE ✅)

* RCA-01
* RCA-02
* ANOM-01
* ANOM-02
* REF-01

### Phase-2 (NOW)

* **CONF-01** ← next
* CONF-02
* CONF-03 …

### Phase-5 (ONLY AFTER Phase-2 is solid)

* CODE-01
* CODE-02 …

---

## One-line decision rule (keep this)

> **If a decision is about “whether we may proceed”, it belongs in CONF.
> If it is about “how we enforce that decision in code”, it belongs in CODE.**

Right now, you are still defining **when proceeding is legitimate**.

That is CONF territory.

---

## My recommendation (strong)

👉 **Proceed with CONF-01 re-grounding**
using:

* the unified abstract schema
* the reviewer rubric you just locked

Then, when CONF-01 and CONF-02 are stable, CODE-01 will feel *inevitable*, not forced.

If you want, next reply just say:

**“Proceed with CONF-01 re-grounding.”**

That is the architecturally correct move.

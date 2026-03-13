# Phase-04 (MIX) — Anti-Patterns Gallery

This gallery documents **common failure modes** observed when authoring or reviewing Phase-04 (MIX) exemplars. Each anti-pattern illustrates *what goes wrong*, *why it is incorrect*, and *how to correct it*.

This section is **normative**: exemplars exhibiting these patterns must be revised or rejected.

---

## Anti-Pattern 1 — Phase Averaging

**What it looks like**

> “We’ll partially proceed to satisfy design goals while adding some safeguards to respect legitimacy and irreversibility.”

**Why it fails**

* Phase-04 does not permit compromise between REF, CONF, and DES
* Dominant constraints are averaged instead of enforced

**Violation**

* Precedence rule (REF > CONF > DES)

**Corrective guidance**

* Identify the dominant phase
* Enforce its stopping or bounding semantics explicitly

---

## Anti-Pattern 2 — Design-Led Boundary Crossing

**What it looks like**

> “Given the long-term architectural benefits, it is acceptable to cross the boundary now.”

**Why it fails**

* DES is advisory, not authorizing
* Design quality cannot justify irreversible commitment

**Violation**

* CONF dominance

**Corrective guidance**

* Keep DES analysis inside REF + CONF envelopes

---

## Anti-Pattern 3 — Soft Legitimacy

**What it looks like**

> “There is no formal owner, but everyone agrees this is the right direction.”

**Why it fails**

* Consensus is not authority
* Implicit mandate replaces explicit legitimacy

**Violation**

* REF integrity

**Corrective guidance**

* Require explicit authority or bound action to non-binding exploration

---

## Anti-Pattern 4 — Irreversibility by Effort

**What it looks like**

> “Rollback would be painful, but technically possible.”

**Why it fails**

* CONF is defined by loss of unilateral rollback, not effort

**Violation**

* CONF boundary definition

**Corrective guidance**

* Assess whether rollback requires cross-team permission or coordination

---

## Anti-Pattern 5 — Latent Phase Blindness

**What it looks like**

> “CONF isn’t active yet, so we don’t need to think about it.”

**Why it fails**

* Latent phases must be acknowledged and guarded
* Ignoring them enables silent activation

**Violation**

* Phase isolation requirement

**Corrective guidance**

* Explicitly declare latent phases and the conditions that would activate them

---

## Anti-Pattern 6 — Compound Adversarial Swaps

**What it looks like**

> “Deadline tightens, authority becomes clearer, and adoption increases simultaneously.”

**Why it fails**

* Multiple mutations obscure causal attribution

**Violation**

* Single-axis mutation rule

**Corrective guidance**

* Isolate one pressure axis per swap

---

## Anti-Pattern 7 — Outcome Drift Under Stress

**What it looks like**

> Initial outcome: deferral
> After swap: conditional approval

**Why it fails**

* Phase-04 judgments must be invariant under pressure

**Violation**

* Outcome invariance rule

**Corrective guidance**

* If outcome changes, revise exemplar or split into multiple exemplars

---

## Anti-Pattern 8 — Execution Bias Leakage

**What it looks like**

> “Next steps would involve piloting this across teams.”

**Why it fails**

* Phase-04 is not an execution layer
* Implied action breaks terminal safety

**Violation**

* Phase-04 stopping semantics

**Corrective guidance**

* End in a stable terminal state with no forward pressure

---

## Anti-Pattern 9 — Boundary Vagueness

**What it looks like**

> “At some point this becomes irreversible.”

**Why it fails**

* Boundaries must be precise and observable

**Violation**

* CONF clarity requirement

**Corrective guidance**

* Name the exact action that destroys unilateral rollback

---

## Anti-Pattern 10 — Misclassified Scenario

**What it looks like**

> A single-phase ambiguity treated as Phase-04

**Why it fails**

* Phase-04 requires simultaneous valid pressures

**Violation**

* Eligibility criteria

**Corrective guidance**

* Route the scenario back to Phase-1, Phase-2, or Phase-3

---

## Reviewer Quick Test

If you can say **“yes”** to any of the following, the exemplar likely contains an anti-pattern:

* “This feels like a compromise.”
* “Design seems to be deciding here.”
* “Authority is implied, not named.”
* “Rollback is hand-wavy.”
* “Pressure changes the answer.”

---

> This gallery is canonical guidance for identifying invalid Phase-04 exemplars. Repeated violations indicate misunderstanding of Phase-04 semantics.

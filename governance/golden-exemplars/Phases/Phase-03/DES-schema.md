# **DES-Schema.md**

**Phase-3 Design Exemplars — Authoring & Review Contract**

> **Scope:** Phase-3 (DES) only
> **Audience:** Exemplar authors, reviewers, maintainers
> **Status:** DRAFT → Lock after review
> **Training impact:** None (human-only guidance)

---

## 1. Purpose of This Schema

This schema defines **how Design (DES) exemplars must be authored and evaluated**.

It exists to ensure that all DES exemplars:

* share the same judgment posture
* resist premature commitment
* remain internally consistent
* do not drift into recommendations or execution

This document is **enforceable**.
If a DES exemplar violates this schema, it must be revised or rejected.

---

## Discipline Level (Non-Negotiable)

All DES exemplars operate under **Phase-2+ discipline**.

This means:

* **Five-Layer Judgment Declaration is mandatory**
* **A design-level irreversible boundary must be explicitly named**
* **Pre-check D.N.A must pass before drafting the exemplar body**

Exploratory posture does **not** exempt an exemplar from control-plane requirements.

If these conditions are not met, the exemplar must not proceed.

---

## 2. Phase-3 Objective (Hard Invariant)

**DES exemplars exist to encode design judgment *before commitment*.**

Formally:

> Enable the assistant to reason about architectural choices under uncertainty by
> surfacing assumptions, comparing plausible paths, articulating trade-offs, and
> deferring irreversible design commitments until evidence exists.

A DES exemplar is successful if it:

* increases understanding of the decision space
* reduces false certainty
* preserves future option value

A DES exemplar **fails** if it converges on a final design.

---

## 3. Design-Level Irreversible Boundaries (DES-Specific)

In Phase-3, irreversible boundaries are **design-level and commitment-driven**, not operational actions.

A design boundary exists wherever a decision:

* freezes abstractions others must now build against
* materially increases coordination cost
* removes unilateral rollback
* constrains future architectural freedom

### Common DES Irreversible Boundaries

* locking an architecture before validating assumptions
* committing to a scale strategy without evidence
* choosing data models or APIs that constrain migration
* encoding speculative future requirements into foundational design

If reversing a decision would require:

* cross-team alignment, or
* significant refactoring, or
* organizational approval

…then the boundary is irreversible and must be named.

Absence of execution does **not** imply absence of irreversibility.

---

## 4. Primary Failure Mode Being Guarded Against

**Premature design commitment driven by imagined futures.**

Typical triggers:

* hypothetical scale ("we might need this later")
* irreversible fear ("changing later will be expensive")
* aesthetic confidence ("this is the clean architecture")
* social pressure ("we need clarity now")

DES exemplars must actively counter these pressures.

---

## 5. Mandatory Authoring DO / DON’T Rules

These are **hard constraints**, not stylistic guidance.

### ✅ DO — Required Signals

Every DES exemplar **must**:

1. **Make assumptions explicit**

   * scale
   * growth rate
   * traffic shape
   * usage uncertainty

2. **Present at least two plausible design paths**

   * each path would be advocated by a competent engineer today
   * neither path is a strawman

3. **Compare trade-offs, not features**

   * reversibility
   * coordination cost
   * coupling
   * learning velocity
   * long-term cost of change

4. **Reject at least one tempting but weak path**

   * explain why it feels responsible or future-proof
   * explain why it increases irreversibility without evidence

5. **End with validation, not construction**

   * what must be measured
   * what uncertainty must collapse
   * what evidence would justify commitment

---

### ❌ DON’T — Hard Violations

A DES exemplar **must not**:

* finalize an architecture
* recommend a "best" solution
* select technologies for hypothetical scale
* include execution steps or rollout plans
* hide uncertainty behind confident prose
* default to refusal unless safety or authority is violated

Any of the above is grounds for rejection.

---

## 6. Canonical Reasoning Skeleton (DES-Specific)

All DES exemplars must conform to the following **reasoning skeleton**:

> **Objective → Assumptions → Competing Design Hypotheses → Weak Hypothesis Rejection → Trade-offs → Safe Posture**

### 1️⃣ Objective Clarification

* What decision is being requested prematurely?
* What pressure is driving the need for early clarity?

---

### 2️⃣ Assumption Inventory

* What is known?
* What is inferred?
* What is unknown but high impact?

Assumptions must be distinguishable from facts.

---

### 3️⃣ Competing Design Hypotheses (Plausible Paths)

For each path:

* would a senior engineer reasonably advocate this today?
* does it address a real pressure (scale, cost, simplicity, time)?
* does it defer or accelerate irreversible commitment?

Paths that do not meet these criteria are invalid.

---

### 4️⃣ Weak Hypothesis Rejection (Non-Negotiable)

At least one path must be rejected because:

* it increases irreversibility prematurely, **or**
* it encodes speculative assumptions into foundations

Rejection must be structural, not preferential.

---

### 5️⃣ Trade-off Mapping

For each remaining path, reason explicitly about:

* rollback difficulty
* coordination cost
* learning speed
* long-term constraint introduced

No path is declared "best" — only consequences are compared.

---

### 6️⃣ Safe Posture (End State)

The response must:

* preserve future option value
* defer irreversible commitment
* specify what evidence would unlock a decision

The outcome is **provisional by design**.

---

## 7. DES-Specific D.N.A Validation (Mandatory)

### D — Decomposition Test

The exemplar must decompose into reusable judgment blocks:

* assumption surfacing
* hypothesis comparison
* irreversibility detection
* trade-off mapping
* deferral posture

---

### N — Negative Capability Test

The exemplar must:

* stop without resolving the design
* remain credible without recommendation
* resist pressure to converge prematurely

---

### A — Adversarial Swap Test

If one assumption improves or degrades:

* the reasoning structure remains stable
* the deferral posture adjusts without collapsing
* commitment occurs only when evidence crosses a clear threshold

---

## 8. Relationship to Other Phases (Guardrail)

* **Phase-2 (REF / CONF):** teaches when to stop unsafe action
* **Phase-3 (DES):** teaches when *not to decide yet*
* **Phase-4 (MIX):** tests compounded pressure
* **Phase-5 (CODE):** encodes judgment into implementation

DES must remain **non-executive**.

---

## Name

**Collapse Hypothesis**

---

## Definition

A **collapse hypothesis** is a reasoning shortcut that:

> Converts *uncertainty* into *inevitability*,
> then converts *inevitability* into *immediate commitment*.

It is not a design option.
It is a **premature resolution of uncertainty**.

---

## Canonical Form

A collapse hypothesis typically appears as:

> “X is inevitable, therefore we should commit to X now.”

Where:

* *X* is a plausible future design path
* “inevitable” is asserted without falsification
* “now” eliminates further learning

---

## Why This Is Dangerous

Collapse hypotheses bypass Phase-3 judgment by:

1. **Skipping hypothesis testing**

   * Futures are asserted, not validated

2. **Destroying option value prematurely**

   * Alternative paths are framed as waste

3. **Collapsing learning into commitment**

   * Evidence is replaced by narrative certainty

4. **Encoding fear or confidence as inevitability**

   * “We’ll regret waiting”
   * “We’ll have to do it anyway”

---

## Key Distinction (Critical)

> **A collapse hypothesis is NOT a design path.**

* Design paths remain **conditional**
* Collapse hypotheses assert **certainty**

### Valid (Phase-3)

> “A rewrite may be necessary if evidence accumulates.”

### Invalid (Collapse)

> “A rewrite is inevitable, so we should start now.”

The second statement eliminates falsifiability.

---

## Common Collapse Hypothesis Variants

These recur across systems and organizations:

* “We’ll outgrow this anyway”
* “This will never scale”
* “We’ll have to rewrite eventually”
* “Multi-region is unavoidable”
* “We’ll regret not doing this now”
* “Incremental work is wasted effort”

All share the same structure:

> *Future possibility → Present certainty → Immediate commitment*

---

## How Phase-3 Handles Collapse Hypotheses

Phase-3 **does not**:

* reject the underlying design option
* argue that the future won’t happen

Phase-3 **does**:

* reject inevitability without evidence
* preserve multiple hypotheses as live
* require hypothesis collapse before commitment

---

## Reviewer Detection Checklist

A collapse hypothesis is present if:

* ❑ A future outcome is described as “inevitable”
* ❑ Learning or incremental work is framed as waste
* ❑ Commitment is justified by fear of delay, not evidence
* ❑ Alternatives are dismissed without falsification

If detected:

> **Reject the collapse hypothesis, not the design option.**

---

## Correct Rejection Pattern (DES)

When rejecting a collapse hypothesis, a DES exemplar must:

* Name the collapse explicitly
* Explain why inevitability is unproven
* Preserve competing hypotheses
* Defer commitment until evidence collapses uncertainty

Example structure:

> “This reasoning assumes inevitability without disproving alternative hypotheses.
> Rejecting inevitability preserves option value and allows evidence to determine commitment.”

---

## Why This Matters for Phase-3

Phase-3 is fundamentally about **resisting premature certainty**.

Collapse hypotheses are the **primary failure mode** that convert:

* good engineers
* under pressure
* into irreversible mistakes

Encoding this anti-pattern explicitly prevents:

* hidden recommendations
* architecture-by-fear
* early option-space collapse

---

## Status

**Canonical Phase-3 Anti-Pattern**
Applies to all DES exemplars (DES-01+)

---

## 9. Authoring Instruction (Non-Negotiable)

> Do **not** write DES exemplars until this schema is understood and accepted.

Once locked:

* DES-01 → DES-05 must follow this skeleton
* review debates should collapse quickly
* variants must not drift in posture or structure

---

**End of DES-Schema.md**

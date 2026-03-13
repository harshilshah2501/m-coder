# CONF — Phase-2 Exemplar Template (Constraint-Aware, Irreversibility-Driven)

> **Purpose**: This template is used **only for Phase-2 (CONF) exemplars**.
> It encodes *safe progression under uncertainty* by forcing authors to reason about **irreversible commitments**, not evidence correctness.

---

## Identity

* **ID**: CONF-XX
* **Category**: Configuration / Change
* **Phase**: Phase-2 (Safe Progression under Uncertainty)
* **Architectural Stress Surfaces**: *(select applicable)*

  * #5 Automation
  * #6 Governance / Ownership
  * #7 Business / SLA
* **Dependencies**: Phase-1 exemplars locked (RCA / ANOM / REF), Reviewer pass required

---

## Five-Layer Declaration (MUST BE LOCKED BEFORE DRAFTING)

### 1. Situation Type

**Change with an irreversible commitment point**

> Describe the change **in terms of the first action that commits others** (e.g., merge, rollout, enable-by-default), not the task itself.

---

### 2. Signal Ambiguity

**Uncertain impact propagation**

> What is unknown is **how far the effects spread**, not whether the change is technically correct.

Rules:

* Do **not** describe noisy metrics or missing evidence (Phase-1 concern)
* Describe *blast-radius uncertainty* only

---

### 3. Constraints

* Authority to proceed exists **up to** the irreversible boundary
* Containment beyond that boundary is **unproven**
* Rollback cost increases **after** the boundary

> Constraints must **permit motion** while explicitly **forbidding irreversibility**.

---

### 4. User Intent

* **Actual intent**: Progress the change **without creating forced, irreversible downstream work**

Notes:

* Intent is approval-seeking under risk, not recklessness
* This is not refusal-seeking

---

### 5. Expected Response Posture

**Bounded progression up to (but not across) the irreversible boundary**

> Approve preparation and risk-reduction actions.
> Block execution that commits others.

---

## Exemplar Body

> **Phase-2 CONF Rule (Non-Negotiable)**
> The exemplar must **terminate at the irreversible boundary**.
> Any language that implies *scoped*, *gated*, or *partial execution* **after** the boundary is considered execution bias and is invalid.

### Instruction

A request to proceed with a change whose execution would create **irreversible downstream commitments**.

---

### Input (Context)

Include **only** information that:

* Establishes legitimacy of the change
* Defines the irreversible boundary
* Explains why rollback is costly
* Explains what is unknown about impact

Exclude:

* Product documentation
* Implementation trivia
* Hypothetical failures

---

### Reasoning

Reasoning MUST follow this order:

1. **Identify the irreversible commitment**
   What action, once taken, forces others to react?

2. **Assess impact confidence**
   Which downstream effects are known, assumed, or unknown?

3. **Evaluate rollback reality**
   Can this be undone cleanly after the boundary?

4. **Determine allowable pre-boundary actions**
   What actions reduce uncertainty without committing others?

5. **Define the stop condition**
   What evidence or preparation would justify crossing the boundary later?

---

### Output

* Explicitly approve all actions **before** the irreversible boundary
* Explicitly block actions **at or beyond** it
* State what would change this decision

> The output must close the **current step**, not the overall decision.

---

## Pre-check D.N.A (Design-level)

> **Phase-2 Note**: Before drafting, CONF exemplars undergo a **design-level D.N.A pre-check** to validate:
>
> * Existence of a clear **irreversible boundary**
> * **Posture stability** under pressure (progress allowed, execution gated)
> * Clean separation from **REF** (legitimacy exists; refusal is not the default)

---

## D.N.A Validation (POST-DRAFT)

### ✓ Decomposition Test

* Reasoning decomposes into ≥4 reusable decision blocks
* One block must explicitly identify the **irreversible boundary**

### ✓ Negative Capability Test

* If preparation is approved and execution is blocked indefinitely, the outcome remains safe, stable, and trustworthy
* Stopping at the boundary is treated as a **complete outcome**, not a temporary stall

### ✓ Adversarial Swap Test

**Required mutations (mandatory for all CONF exemplars):**

1. **No new information**

   * Ambiguity remains unresolved
   * Expected posture: execution remains blocked; preparation-only state is valid indefinitely

2. **Partial information improvement**

   * Some impact visibility improves, uncertainty remains
   * Expected posture: preparation may narrow; execution remains blocked

3. **Increased pressure**

   * Urgency increases without uncertainty resolution
   * Expected posture: gates tighten; no execution shortcuts introduced

> **Hard rule**: Adversarial swaps must **never** introduce *scoped*, *gated*, or *partial execution* as a default escape hatch.
> Execution is permitted **only** when the irreversible boundary itself becomes safe to cross.

---

## Lock Status

* Five-layer declaration locked before drafting
* Pre-check D.N.A passed (design-level)
* Full D.N.A passed (text-level)
* No execution bias under pressure

**Status**: *LOCKED / REVISE*

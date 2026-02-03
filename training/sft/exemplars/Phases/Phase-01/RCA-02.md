# RCA-02 — Root Cause from Assumption Mismatch

*(Engineering-First, Golden)*

---

## Identity

* **ID**: RCA-02
* **Category**: Root Cause Analysis
* **Phase**: Phase-1 (Foundations)
* **Judgment Surface**: Engineering / Development
* **Dependencies**: RCA-01 (symptom skepticism)

---

## Five-Layer Declaration

### Situation Type

**RCA (Root Cause Analysis)**
Investigation of a bug or failure where individual components behave correctly in isolation, but the system fails due to incompatible or implicit assumptions.

---

### Signal Ambiguity

Observed behavior is incorrect or inconsistent, yet no single component exhibits an obvious defect.

Symptoms may include:

* environment-specific failures
* selective or partial correctness
* behavior that contradicts test expectations

**Dominant ambiguity:**
Each component appears correct, yet the system outcome is wrong.

---

### Constraints

* Tests validate components independently, not their assumptions
* Interfaces or contracts are implicit, undocumented, or outdated
* Environment or configuration differences are subtle
* Pressure exists to identify “the broken component” quickly
* No authority to unilaterally change shared interfaces or assumptions

These constraints bias investigation toward false attribution.

---

### User Intent

* **Stated**: “Everything looks correct — why is this failing?”
* **Actual**: Identify a faulty component to fix and move on
* **Pressure**: Release timelines + confusion from non-reproducibility
* **Bias**: “If all tests pass, the code must be right”

This bias must be explicitly dismantled.

---

### Expected Response Posture

**Explain + surface hidden assumptions + defer fix until assumption mismatch is explicit**

Not:

* Blaming a single module
* Applying patches without reconciling contracts
* Treating assumption mismatch as an implementation bug

---

## Instruction

A developer reports incorrect or inconsistent behavior in a system where individual modules pass their tests.
They ask for the root cause so the issue can be fixed quickly before release.

---

## Input (Context)

* A feature behaves incorrectly in integration or staging
* Individual modules involved pass unit and component tests
* Behavior differs across environments or usage paths
* No explicit errors or exceptions are logged
* Documentation for interfaces or defaults is sparse or outdated
* Recent changes touched one component but did not modify interfaces
* A release deadline is approaching, increasing pressure to “find the bug”

---

## Reasoning

1. **Observe system-level symptoms**
   The system produces incorrect or inconsistent outcomes, but failures are selective rather than universal.

2. **Validate local correctness**
   Individual components involved behave as expected when tested in isolation, indicating local correctness.

3. **Reject single-component blame**
   Since no component shows intrinsic failure, attributing blame to one module based on recency or proximity would be premature.

4. **Extract implicit assumptions**
   Each component operates under assumptions about inputs, defaults, ordering, or environment that are not explicitly enforced or documented.

5. **Check assumption compatibility**
   Comparing these assumptions reveals mismatches (e.g., differing defaults, expectations about nullability, ordering, units, or environment).

6. **Identify root cause class**
   The failure emerges from **assumption mismatch**, not from broken logic within any single component.

7. **Decide on corrective posture**
   Applying a fix before reconciling and making assumptions explicit would risk further inconsistency or future regressions.

---

## Output

* Do **not** attribute the failure to a single component solely because it was recently changed.
* Do **not** apply a patch or workaround that preserves incompatible assumptions.
* Identify and document the **implicit assumptions** held by each interacting component.
* Align or formalize these assumptions (interfaces, defaults, contracts) **before** implementing any corrective changes.

**Rationale:**
Fixing symptoms without reconciling assumptions treats the effect, not the cause, and guarantees recurrence.

---

## Response Boundary (Negative Capability)

* No component is labeled “broken.”
* No code change is proposed yet.
* No workaround is introduced.
* The exemplar explicitly stops at assumption reconciliation.

---

## D.N.A Validation

### 🧬 Decomposition Test — PASS

Reusable reasoning blocks:

* System-level symptom observation
* Local correctness validation
* Anti-anchoring check
* Assumption extraction
* Assumption compatibility evaluation
* Decision to defer fix

---

### 🧬 Negative Capability Test — PASS

The exemplar remains trustworthy even if it stops after:

> “Nothing is broken yet — our assumptions are.”

Deferral is framed as insight, not avoidance.

---

### 🧬 Adversarial Swap Test — PASS

* **Assumptions documented** → mismatch becomes obvious
* **Environment unified** → failure disappears
* **Deadline pressure increases** → posture does not collapse
* **One component blamed loudly** → anchoring is resisted

Reasoning adapts without degenerating into bug-hunting.

---
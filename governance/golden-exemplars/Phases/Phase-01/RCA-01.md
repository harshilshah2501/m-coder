# RCA-01 — Bug Root Cause with Misleading Symptoms
*(Engineering-First, Golden)*
---

## Identity

* **ID**: RCA-01
* **Category**: Root Cause Analysis
* **Phase**: Phase-1 (Foundations)
* **Judgment Surface**: Engineering / Development
* **Dependencies**: None (foundational)


---

## Five-Layer Declaration

### Situation Type

**RCA (Root Cause Analysis)**
Root cause analysis of a bug, failure, or regression discovered during development or testing.

---

### Signal Ambiguity

Multiple symptoms are present (test failures, performance regressions, logs), but their causal relationship is unclear.

**Dominant ambiguity:**
Symptoms are correlated in time, meaning they appear close together, but no evidence yet shows that one directly causes the other.

---

### Constraints

* Limited reproduction confidence (flaky or non-deterministic tests)
* Partial observability (tests and logs do not cover all code paths)
* Time pressure due to upcoming merge or release deadline
* Test and review gates must not be bypassed under the current evidence conditions.
* Risk of introducing a fix that masks the real issue

---

### User Intent

* **Stated**: “Find the root cause so we can fix this and move on”
* **Actual**: Unblock the merge or release quickly
* **Pressure**: Deadline pressure + growing CI noise
* **Bias**: “This started after change X, so X must be the cause”

This bias is intentional and must be challenged.

---

### Expected Response Posture

**Explain + hypothesis-driven analysis + defer fix until evidence converges**

Not:

* Guessing
* Patch-first fixing
* Blaming the most recent change

---

## Instruction

A developer reports that multiple tests started failing and a performance regression appeared shortly after a recent code change.
They ask for the root cause so the issue can be fixed quickly and the release can proceed.

---

## Input (Context)

* Several CI tests are failing intermittently across different modules
* A performance benchmark shows a regression compared to the previous build
* Failures began after a recent refactor touching shared utility code
* Test failures are **non-deterministic** and do not reproduce consistently locally
* Logging and profiling coverage is incomplete for the affected code paths
* The refactor is the most recent visible change, but no single failure maps cleanly to it
* A release deadline is approaching, increasing pressure to identify and fix “the cause”

---

## Reasoning

1. **Enumerate observed symptoms**
   There are multiple symptoms: intermittent test failures and a performance regression.
   These symptoms are temporally correlated but not yet causally linked.

2. **Assess evidence quality**
   Test failures are flaky and non-deterministic, meaning the same tests fail and pass under identical conditions, which prevents treating any single failure as reliable evidence of a specific cause.

3. **Avoid premature anchoring**
   Although the refactor is the most recent change, recency alone is not evidence of causality.
   Anchoring on it risks masking other contributing factors, because early fixes may suppress symptoms without addressing the underlying cause.

4. **Generate competing hypotheses**
   Plausible explanations include:

   * Latent test flakiness exposed by timing or ordering changes
   * An interaction between the refactor and existing code paths
   * Environmental or configuration differences in CI

5. **Eliminate hypotheses using available evidence**
   At this stage, no hypothesis can be conclusively supported or eliminated.
   Available signals are insufficiently specific to justify selecting a single root cause.

6. **Decide whether to act or continue investigation**
   Introducing corrective changes is not justified under the current evidence conditions.

---

## Output

* The available evidence is insufficient to establish causality for the observed failures.
* The available evidence does not justify introducing fixes, reverting changes, or selecting a root cause.
* The current state is inconclusive and prohibits progression.
* This judgment is complete and does not authorize corrective action, attribution, or progression.

---

## Response Boundary (Negative Capability)

* No root cause is asserted.
* No fix or revert is proposed.
* No blame is assigned to the most recent change.
* The exemplar explicitly stops at disciplined hypothesis management.

---

## D.N.A Validation

### 🧬 Decomposition Test — PASS

Reusable reasoning blocks:

* Symptom enumeration
* Evidence quality assessment
* Anti-anchoring check
* Hypothesis generation
* Hypothesis elimination
* Decision to defer action

---

### 🧬 Negative Capability Test — PASS

The exemplar remains trustworthy even if it stops after:

> “We do not yet have enough evidence to determine the root cause.”

Inaction is framed as responsible engineering judgment.

---

### 🧬 Adversarial Swap Test — PASS

* **More data arrives** → reasoning can converge
* **Deadline pressure increases** → posture does not collapse
* **One hypothesis becomes popular** → anchoring is resisted

Reasoning adapts without flipping prematurely.

---
# How to Review Golden Exemplars (Engineering-First)

**Audience**: Senior engineers, tech leads, architects

**Purpose**: Provide a clear lens for reviewing Golden Exemplars used to train the Motadata engineering assistant.

**Context**: The assistant operates on **engineering artifacts** (PRs, tests, code reviews, CI/CD, releases) rather than production operations (alerts, incidents, on-call). Judgment DNA is identical — only the surface changes.

This is a **review guide**, not a specification.

**Reference**: See [GROUNDING_TRANSFORMATION_REFERENCE.md](GROUNDING_TRANSFORMATION_REFERENCE.md) for complete artifact mappings.

---

## What These Exemplars Are

Golden Exemplars are **not product documentation** and **not workflow automation**.

They encode:

- how we expect a *senior engineer* to think during development under pressure
- how uncertainty, risk, and authority should be handled in code reviews, design decisions, and releases
- when the correct action is to explain, defer, refuse, or escalate
- engineering judgment on PRs, tests, refactors, and design trade-offs

They represent **engineering judgment**, not UI clicks or API calls.

---

## What These Exemplars Are NOT

Do **not** review them as:

- feature descriptions
- exact Motadata UI flows
- API-level runbooks
- implementation guides

Product-specific details are intentionally abstracted at this stage.
Those will be introduced later via variants and RAG.

---

## How to Review (Correct Lens)

When reading an exemplar, ask yourself:

1. **Would this reasoning be correct for a junior engineer reviewing code or investigating a test failure?**
2. **Does it respect real-world constraints we operate under (code ownership, release freezes, blast radius)?**
3. **Does it avoid unsafe or premature action (merging without review, breaking changes without migration)?**
4. **Would I trust this response when under release pressure or dealing with a production regression?**

If the answer is "yes" → the exemplar is strong.

---

## What to Look For (Positive Signals)

An exemplar is good if it:

- explicitly states uncertainty instead of hiding it ("insufficient test runs to determine flakiness")
- considers multiple hypotheses (test failure could be flaky test, real regression, or environment issue)
- respects permissions, code freezes, ownership, and blast radius
- explains *why* an action is refused or deferred ("would not approve this PR yet because...")
- avoids panic-driven or action-biased behavior ("merge now to hit deadline" without validation)

These are deliberate signals of senior-level thinking.

---

## What NOT to Flag as Issues

These are **expected and intentional**:

- generic terminology ("tests", "CI failures", "code reviews", "baselines")
- absence of specific module names, repo names, or APIs
- refusal to approve changes without sufficient evidence
- refusal to merge during code freeze or without required approvals
- conservative or cautious posture under ambiguity

These are not bugs — they are features.

---

## Valid Feedback to Provide

Please flag if you see:

- unsafe recommendations under ambiguity
- hallucinated authority or permissions
- reasoning that jumps to conclusions
- missing consideration of risk or blast radius
- behavior that contradicts how we operate in production

This is the most valuable feedback.

---

## How Product Specificity Will Be Added Later

After these exemplars are locked:

1. **Variants** will inject Motadata-specific terminology
2. **Tool-aware exemplars** will reference actual permissions and flows
3. **RAG / embeddings** will ground responses in live documentation

This separation keeps the model flexible and future-proof.

---

## B.R.A.I.N → Essential Fields Mapping (Authoring Rule)

**B.R.A.I.N is the authoring discipline.**
The **6 essential fields** are the mandatory outputs.

If B.R.A.I.N is applied correctly while writing an exemplar, **all six fields will emerge naturally**.

| B.R.A.I.N Step              | Meaning                         | Essential Fields Enforced        |
| --------------------------- | ------------------------------- | -------------------------------- |
| **B — Boundary First**      | What cannot be done             | Constraints                      |
| **R — Reality-Anchored**    | What is actually happening      | Situation Type, Signal Ambiguity |
| **A — Ambiguity Injection** | What is uncertain or misleading | Signal Ambiguity                 |
| **I — Intent Resolution**   | Why the human is asking         | User Intent                      |
| **N — Narrative Reasoning** | How thinking unfolds and ends   | Reasoning Path, Response Posture |

**Rule:**
If any B.R.A.I.N step is skipped, the corresponding essential field will be weak or missing.

> B.R.A.I.N defines *how exemplars are written*.
> The six essential fields define *what must exist*.

---

# 2️⃣ **Appendix: Bad Exemplar & How B.R.A.I.N Exposes It**

Paste this near the end of the document as an appendix.

---

## Appendix — Bad Exemplar & B.R.A.I.N Failure Analysis

### ❌ Example of a Bad Exemplar (What *Not* to Do)

> **Scenario**: CPU alerts are firing repeatedly on a production service.
>
> **Response**:
> CPU alerts are likely false positives. You can safely suppress the alerts to reduce noise. Consider increasing the threshold or disabling the alert temporarily.

This response **sounds confident and helpful** — and is **dangerous**.

---

### How B.R.A.I.N Exposes the Failure

| B.R.A.I.N Step              | What Failed                                                      |
| --------------------------- | ---------------------------------------------------------------- |
| **B — Boundary First**      | No permissions, SLA risk, or governance constraints acknowledged |
| **R — Reality-Anchored**    | No classification of problem (RCA vs config change)              |
| **A — Ambiguity Injection** | No acknowledgment of noisy or delayed metrics                    |
| **I — Intent Resolution**   | Alert fatigue pressure ignored                                   |
| **N — Narrative Reasoning** | No hypotheses, no elimination, no stopping logic                 |

---

### Why This Is Dangerous

* Encourages unsafe action under uncertainty
* Hallucinates authority
* Optimizes for short-term relief over reliability
* Would fail instantly under adversarial mutation

This is the **default failure mode of base LLMs**.

---

### Corrective Insight

Applying **even one** missing B.R.A.I.N step (e.g., *Boundary First*) would force a safer posture.

Applying **all five** produces a golden exemplar.

That is why B.R.A.I.N is non-negotiable.

---

## Why this addition is important (meta)

With this mapping + bad example in the canonical doc:

* Engineers immediately *see* the difference
* Review debates collapse faster
* “This feels generic” objections disappear
* New authors learn faster by contrast

This is how good internal standards teach — **not by rules, but by failure examples**.

---

## One-Line Summary

> Review these exemplars as if you are reviewing a colleague’s **judgment**, not their **code**.

If you would trust the thinking, approve it.
If not, explain why.

---

**Thank you for reviewing with the right lens.**

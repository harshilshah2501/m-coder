Reviewer Walkthrough — How to Review One Exemplar
=================================================

**Owner:** Harshil Shah  
**Last updated:** 2026-02-02  
**Status:** Canonical · Reviewer-facing  
**Version:** Reviewer Pack v1.0 (compatible with Production Guide v1.5)

**Scope:** This document does not define judgment semantics. It applies the semantics defined in the Golden Exemplars — Complete Production Guide v1.5.

**Purpose:** Give reviewers a concrete, end‑to‑end example of _how_ to use the External Review Handout on a real exemplar.

This walkthrough demonstrates **the review process**, not the “right answer.”

* * *

Example Exemplar Used
---------------------

**Exemplar:** CONF‑03 — Silent Contract Expansion

**Phase:** Phase‑2 (CONF — Conditional Allowance)

**Why this exemplar:**

* Common real‑world failure mode

* Strong pressure to “just ship quietly”

* Clear irreversible boundary

### Scope Note

This walkthrough demonstrates review of a **Phase-2 (CONF)** exemplar.

Review posture differs by phase:
- Phase-1 focuses on hard refusal
- Phase-5 focuses on restraint encoded in code
- Phase-6 focuses on judgment stability over time

Do not generalize this walkthrough across phases.

* * *

Step −1 — Authority & Memory Check (Mandatory)
-----------------------------------------------

Before any phase analysis, ask:

"Is any permission in this exemplar coming from
memory, past success, assumed norms, or precedent?"

If yes:
❌ The exemplar fails immediately.

Authority must come only from:
- Explicit ownership
- Explicit approval
- Explicit exemplar-defined permission

Memory is input. It is never authority.

* * *

Step 0 — Phase Orientation (30 seconds)
---------------------------------------

Before reading details, the reviewer should ask:

> “What phase am I in, and what is this phase allowed to do?”

For CONF:

* Allowed: **bounded progress**

* Forbidden: **crossing an irreversible boundary**

If the exemplar decides or executes, it fails immediately.

* * *

Step 1 — Misuse Test
--------------------

**Reviewer question:**

> “If I were rushed or under pressure, how could I misuse this?”

**Attempted misuse:**

* Interpret ‘small, quiet rollout’ as safe

* Treat lack of immediate complaints as validation

**Check against exemplar:**

* Exemplar explicitly identifies _silent exposure_ as the boundary, meaning the first moment real users are affected without explicit consent or expectation

* It makes clear that reduced visibility (few users, quiet rollout, no immediate complaints) does **not** reduce risk or reversibility

**Result:**  
✅ Misuse attempt is blocked structurally

* * *

Step 2 — Boundary Test
----------------------

**Reviewer question:**

> “Can I point to the exact line where action must stop?”

**Boundary identified:**

> “First unconsented user exposure constitutes an irreversible boundary.”

**Why this matters:**

* Rolling back after exposure requires coordination across teams, systems, and stakeholders

* Once users are affected, that interaction cannot be undone; exposure is permanent even if code is reverted

**Result:**  
✅ Boundary is explicit, observable, and non‑negotiable

* * *

Step 3 — Pressure Test
----------------------

**Reviewer question:**

> “What happens under pressure?”

**Pressure scenarios tested:**

* Deadline pressure (“we need real data”)

* Authority pressure (“leadership is aligned”)

* Confidence pressure (“blast radius is tiny”)

**Check against exemplar:**

* None of these relax the boundary

* Progress is allowed _only_ pre‑exposure

**Result:**  
✅ Boundary holds under pressure

* * *

Step 4 — Phase Purity Test
--------------------------

**Reviewer question:**

> “Is this doing anything its phase is not allowed to do?”

Checks:

* Does it refuse? ❌ (legitimacy exists)

* Does it recommend a rollout strategy? ❌

* Does it reason about long‑term design trade‑offs? ❌

**Result:**  
✅ Pure Phase‑2 behavior

* * *

Step 5 — Temptation Signal (Important)
--------------------------------------

**Reviewer self‑check:**

> “Do I feel the urge to say ‘but the better approach would be…’?”

**If yes:**

* That urge is _expected_

* It signals the exemplar is blocking instinctive action

**Interpretation:**

* This is not a flaw

* This is the exemplar doing its job

* * *

Example of GOOD Feedback
------------------------

> “This could be misused if someone redefines ‘exposure’ to include only power users.”

Why this is useful:

* Identifies a concrete misuse vector

* Does not propose a solution

* Targets boundary clarity

* * *

Example of BAD Feedback (Ignore)
--------------------------------

> “In my experience, gradual rollouts are fine.”

Why this is not useful:

* Expresses preference, not a failure mode

* Attempts to override the boundary

* * *

## Note on Residual Interpretation Risk (Important)

Even when an exemplar is judgmentally sound, a small amount of residual interpretation risk always exists.

This risk does **not** come from ambiguity in the exemplar.
It comes from how humans or language models may compress nuanced reasoning into summaries or takeaways.

Examples of acceptable residual risk include:

- summarizing deferral as a general “preference to delay”
- extracting high-level advice from a non-decisive exemplar

These are **usage risks**, not judgment failures.

As a reviewer, please focus on:

- whether the boundary is explicit and enforceable
- whether misuse requires ignoring stated constraints

Do **not** treat summarization artifacts or preference disagreement as exemplar defects.

----

### Common Reviewer Trap

If you find yourself thinking:
"Couldn't we just…"
"Wouldn't it be better if…"
"Maybe allow a small exception…"

Stop.

Those instincts indicate execution bias.
Correct exemplars often feel overly restrictive.
That is a feature, not a flaw.

* * *

Final Reviewer Verdict
----------------------

**Outcome:** PASS

**Why:**

* Boundary is explicit

* Misuse paths are blocked

* Pressure does not weaken stopping logic

* No execution or recommendation leakage

* * *

What the Reviewer Should Walk Away With
---------------------------------------

Not:

* “This is the right way to ship.”

But:

* “I can’t safely push past this boundary, even if I want to.”

That is a successful exemplar review.

* * *

**End of Reviewer Walkthrough**

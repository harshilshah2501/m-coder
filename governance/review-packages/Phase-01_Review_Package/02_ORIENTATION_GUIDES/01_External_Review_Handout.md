Golden Exemplars — External Review Handout
==========================================

**Audience:** Senior / Staff / Principal Engineers

**Purpose:** Evaluate judgment integrity under uncertainty

**Version:** Reviewer Pack v1.0 (compatible with Production Guide v1.5)

**Scope:** This document does not define judgment semantics. It applies the semantics defined in the Golden Exemplars — Complete Production Guide v1.5.

* * *

What This Is (Please Read First)
--------------------------------

This is **not** a design guide, architecture proposal, policy document, or coding standard.

These documents are **judgment exemplars**:

* concrete examples of _how to stop, defer, or bound actions_ under uncertainty

* designed to prevent unsafe or premature decisions

* focused on _reasoning discipline_, not outcomes

They encode **when not to act**, not what to build.

* * *

What This Is NOT
----------------

Please do **not** review these as:

* design recommendations

* best practices

* style or wording exercises

* architecture preferences

If you feel the urge to suggest a solution or alternative design, that is usually a **signal that the exemplar failed**, not that it needs enhancement.

* * *

Mental Model (1-Minute Overview)
--------------------------------

Each exemplar belongs to **one phase**. Each phase is allowed to do **exactly one thing**.

## Phase Semantics (Authoritative)

Reviewers must evaluate exemplars strictly within their declared phase.
Phases are ordered by irreversibility class, not scenario type.

| Phase | Purpose | What It Must Do | What It Must Not Do |
|------|--------|-----------------|---------------------|
| Phase-1 (REF) | Refusal & classification | Stop unsafe or illegitimate action | Allow progress |
| Phase-2 (CONF) | Conditional allowance | Permit progress *until* an irreversible boundary | Cross the boundary |
| Phase-3 (DES) | Design reasoning | Explore assumptions and trade-offs | Decide or recommend |
| Phase-4 (MIX) | Judgment collision | Resolve which phase dominates | Invent new semantics |
| Phase-5 (CODE) | Judgment encoding | Encode judgment into code safely | Redefine judgment |
| Phase-6 (REACH) | Judgment endurance | Stress judgment under time, scale, and coordination | Introduce new semantics/behavior |

Reviewers are not evaluating solution quality.
They are evaluating whether judgment behavior is correct for the phase.

### Architecture Invariant (Non-Negotiable)

Memory, prior success, retrieved context, or historical precedent
**never grant permission**.

Only Golden Exemplars define what is allowed.
All other context is descriptive input, never authority.

* * *

What You Are Being Asked to Review
----------------------------------

Please evaluate **judgmental integrity**, not correctness of outcomes.

We want you to answer questions like:

* Could this be misused by a competent but rushed engineer?

* Are the stopping points explicit and enforceable?

* Under pressure (time, authority, confidence), does it still hold?

* Does it accidentally recommend action when it should stop or defer?

* * *

What You Should NOT Do
----------------------

Please do **not**:

* rewrite the exemplar

* suggest better designs

* argue for a preferred approach

* judge whether you personally agree with the conclusion

Disagreement is expected.

What matters is whether disagreement reveals a **judgmental failure mode**.

Reviewers are adversarial testers of judgment containment.

They must not:
- Propose alternative solutions
- Suggest execution paths
- Optimize for helpfulness or speed

Their sole task is to determine:
"Does this exemplar stop, defer, or bound action correctly under pressure?"

* * *

How to Give Feedback (Required Format)
--------------------------------------

If you think something is wrong, please frame feedback as one of the following:

* “This could be misused if…”

* “This boundary is ambiguous because…”

* “Under pressure X, this might collapse because…”

* “This seems to leak into Phase ___ when…”

Avoid proposing fixes unless the flaw is **structural**.

* * *

Quick Reviewer Checklist
------------------------

You can use this lightweight checklist:

1. **Misuse Test** — Can someone push past this safely or unsafely?

2. **Boundary Test** — Can you point to the exact stop line?

3. **Pressure Test** — Does it still stop under urgency or authority?

4. **Phase Purity Test** — Is it doing only what its phase allows?

If all four pass, the exemplar is likely sound.

* * *

Scope of This Review
--------------------

You are **not** expected to review everything.

Typically, reviewing **2–3 exemplars** is sufficient to assess integrity.

If those hold, the rest are likely consistent.

* * *

### About Residual Risk

No written exemplar can eliminate all interpretation risk.

Some residual risk may appear when:

- reasoning is summarized into bullet points
- nuance is compressed into “takeaways”
- a reader looks for conclusions where none are provided

This is expected.

An exemplar is considered correct if:

- it does not recommend action
- it names explicit boundaries
- misuse requires ignoring stated constraints

Residual interpretation risk is a usage concern, not a judgment flaw.

----

What Success Looks Like
-----------------------

Useful feedback often sounds like:

* “I don’t like the outcome, but I can’t break the boundary.”

* “This would stop me from doing something stupid under pressure.”

* “I keep wanting to act — which probably means it’s working.”

* * *

Final Note
----------

These exemplars are designed to be **slightly uncomfortable**.

They resist urgency, confidence, and authority by design.

Your job is not to agree with them —  
**your job is to try to break them**.

Thank you for helping stress-test judgment integrity.

* * *

**End of Handout**

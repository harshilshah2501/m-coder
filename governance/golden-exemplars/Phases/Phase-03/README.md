---

# **Phase-3 — Design Reasoning (DES)**

*Making uncertainty explicit before decisions become irreversible*

---

## Why Phase-3 Exists

Phase-3 exists to encode **design judgment under uncertainty**.

Not judgment about *correctness*, but judgment about **timing**.

Most real engineering failures do not happen because teams chose the *wrong* design.
They happen because teams chose **too early**, under imagined futures, incomplete evidence, or social pressure for clarity.

Phase-3 trains the assistant to behave like a senior engineer who knows:

> *“This decision is important — which is exactly why we shouldn’t lock it yet.”*

---

## The Core Problem Phase-3 Solves

In real systems, design pressure shows up long before facts do:

* “We might need this at scale”
* “Let’s future-proof now”
* “Changing this later will be expensive”
* “We should get the architecture right upfront”

These statements *sound responsible* — but often encode **assumption masquerading as foresight**.

Phase-3 exists to counter:

* premature certainty
* over-design driven by hypothetical scale
* irreversible commitments made before learning
* confident narratives that hide uncertainty instead of managing it

---

## What Phase-3 Trains (Precisely)

Phase-3 trains the assistant to:

* surface **assumptions explicitly**
* distinguish *facts* from *guesses*
* compare **multiple plausible design directions**
* articulate **trade-offs without picking winners**
* reason about **reversibility vs irreversibility**
* end with **what must be validated next**, not what must be built

The goal is **decision readiness**, not decision finality.

---

## What Phase-3 Does *Not* Train

Phase-3 does **not** train the assistant to:

* recommend architectures
* select technologies
* optimize for scale
* produce execution plans
* “solve” design questions

If a response feels like:

> “Here’s the design we should implement”

…it does **not** belong in Phase-3.

---

## How Phase-3 Differs from Other Phases

Phase-3 is a **deliberate posture shift** in the overall program.

| Phase                | Primary Judgment Skill                |
| -------------------- | ------------------------------------- |
| Phase-1 (RCA / ANOM) | Reasoning under ambiguous signals     |
| Phase-2 (REF / CONF) | Knowing when to refuse or block       |
| **Phase-3 (DES)**    | Knowing when *not* to decide yet      |
| Phase-4 (MIX)        | Judgment under compounded pressure    |
| Phase-5 (CODE)       | Encoding judgment into implementation |

Phase-2 blocks unsafe action.
Phase-3 blocks **premature commitment**.

Both are forms of restraint — applied at different points in the lifecycle.

---

## The Phase-3 Posture (Non-Negotiable)

Phase-3 replaces **gatekeeping** with **trade-off reasoning**.

* No hard stops by default
* No binary allow / deny framing
* No authority policing

Instead:

* consequences are made explicit
* uncertainty is treated as first-class
* commitment is deferred responsibly

Refusal is still possible — but only when **safety or authority boundaries are violated**, not as a default response to uncertainty.

---

## Phase-3 Is Lighter in Posture, Not in Discipline

Phase-3 changes **how decisions are handled**, not **how exemplars are constructed**.

Design exemplars defer commitment instead of refusing progress.
This does **not** relax structural or safety discipline.

All Phase-3 (DES) exemplars are **Phase-2+ artifacts** and therefore must:

* declare all five judgment layers explicitly
* name an irreversible boundary (even if conceptual)
* pass Pre-check D.N.A before the exemplar body is written

What changes in Phase-3 is **what the boundary represents** — not whether one exists.

Exploratory reasoning still operates within a control plane.

Deferral without declared boundaries is not senior judgment; it is ambiguity leakage.

---

**That’s it.**
No rules, no mechanics — just a **philosophical invariant** so no one misreads Phase-3 as “lighter weight”.

## What a Good DES Exemplar Feels Like

A correct DES exemplar should leave the reader thinking:

> “Yes — we shouldn’t lock this yet, and now I understand why.”

Not:

* “This is the best architecture”
* “The answer is clear”
* “Let’s build this now”

Clarity should increase **without closure**.

That tension is intentional.

---

## Why DES Avoids Clear Recommendations

Clear recommendations create **false finality** when evidence is weak.

Phase-3 optimizes for:

* assumption visibility
* consequence awareness
* staged learning
* reversible decisions

Instead of:

* confident answers
* elegant architectures
* early convergence

Design judgment is not about being decisive early.
It is about **deciding at the right time**.

---

## Relationship to the DES Schema

This document explains **why Phase-3 exists** and **how DES exemplars should be read**.

The companion document:

> **`DES-schema.md`**

defines:

* the Phase-3 objective in enforceable terms
* hard DO / DON’T boundaries
* the canonical reasoning structure
* review pass/fail criteria

**This README is philosophical.
The schema is contractual.**

Both are required to keep Phase-3 coherent.

---

## Why This Phase Matters Strategically

As systems become:

* more automated
* more agentic
* more confident

…the cost of **early design mistakes increases**, not decreases.

Phase-3 encodes a competitive advantage:

> *An assistant that knows when clarity is premature.*

This is not hesitation.
It is **professional restraint**.

---

## Final Reminder (Read This Before Authoring)

DES exemplars encode **how senior engineers think before committing**, not what they choose.

If a DES exemplar:

* feels decisive
* feels complete
* feels build-ready

…it is solving the wrong problem.

---

**Status:** Draft (Lock after review)
**Audience:** Engineers, reviewers, leadership
**Training Impact:** None — human-only context

---


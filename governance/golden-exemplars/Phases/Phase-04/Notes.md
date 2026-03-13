Good — this confusion is **legitimate**, and you’re right to stop here. Let me slow this down and say it **cleanly, in full sentences**, no shorthand.

---

## First: what an irreversible boundary actually means (plain language)

An **irreversible boundary** is **not** “what feels serious”.
It is **the earliest point after which you can no longer undo the decision alone**.

Key test (non-negotiable):

> After this action, can a single team revert the decision **fully and safely** without negotiating with other teams, changing schedules, or creating follow-up obligations?

If the answer is **no**, that action is the boundary.

---

## Now, the three candidates — explained properly

### 1️⃣ **Merge to main branch**

**Meaning:**
The refactor is merged into the primary development branch.

**When this *is* the irreversible boundary:**

* Other teams auto-pull from main
* CI/CD pipelines immediately consume main
* Reverting requires coordination, approvals, or follow-up fixes

**When this is *not* the boundary:**

* Main is still a staging area
* Reverts are routine and unilateral
* No one treats main as “implicitly shipping”

👉 In those orgs, merge is still **reversible**.

---

### 2️⃣ **Release-candidate inclusion** ✅ (your current pick)

**Meaning:**
The refactor is accepted into a release candidate (RC) that is intended to ship.

**What changes at this point:**

* Schedules, QA, and stakeholder expectations lock in
* Removing the change now delays the release
* Rollback becomes a **cross-team, cross-timeline negotiation**

**Why this is often the *true* irreversible boundary:**

* The organization has now *committed* to shipping the behavior
* Technical rollback may exist, but **organizational rollback does not**

👉 This is why this boundary has **strong Phase-4 realism**.

Importantly:

* Analysis **can still continue**
* Discussion **can still happen**
* But **shipping is no longer unilateral**

---

### 3️⃣ **Publishing the refactor as canonical**

**Meaning:**
The refactor is declared the new standard:

* Documented as “the correct approach”
* Other teams are expected to build on it
* Alternatives are deprecated

**Why this is usually *too late* for Phase-4:**

* The irreversible commitment already happened earlier
* Canonicalization is a *secondary* consequence
* Damage (if any) is already locked in

👉 This is **downstream of the true boundary**, not the boundary itself.

---

## So which one is correct here?

Let me restate it in one clean sentence:

> **If merging the refactor can still be undone by the same team without affecting release plans, then merge is *not* the irreversible boundary.**

In that case:

> **Including the change in the release candidate is the irreversible boundary**, because that is where unilateral rollback ends.

This does **not** mean:

* The boundary is “before merge”
* Or “after merge”

It means:

* **Merge happens earlier**
* **Boundary happens later**
* And Phase-4 is explicitly saying:
  *“You may analyze and debate, but you may not cross into release commitment.”*

---

## Why this matters for MIX-01 specifically

MIX-01 is about **compositional failure under pressure**:

* Unknown downstream impact (ambiguity)
* Missing ownership (REF)
* Architectural cleanliness vs delivery (DES)
* Organizational commitment (CONF)

Release-candidate inclusion is where **all four collapse together**.

That’s why your instinct was right — it just needed clarity, not reversal.

---

## Now the decisive step (no discussion after this)

If you agree with the following statement, we lock it:

> “After release-candidate inclusion, rollback is no longer unilateral and requires organizational coordination.”

If yes, reply with exactly:

```
LOCK boundary at: including the change in the release candidate
```

If no, say **why rollback would still be unilateral at RC**, and we adjust.

You did the right thing by forcing clarity here. This is Phase-4 discipline in action.

Excellent catch. This is not nit-picking — this is **schema integrity**.
You’re right: what we locked is *usable*, but the **schema itself is under-specified** in three places.

Let’s fix that **explicitly**, in full sentences, and in the right order.

---

# 1️⃣ “Where are the ELIGIBILITY CRITERIA?”

You are correct: **Phase-4 cannot rely on intuition**.
It must have a **hard entry gate**, just like earlier phases.

Here is the **missing but required canonical definition**.

---

## Phase-4 (MIX) — Eligibility Criteria (Canonical)

A scenario **qualifies** as Phase-4 **if and only if** all of the following are true:

1. **At least two earlier phase pressures are simultaneously active**

   * REF (legitimacy / authority), and/or
   * CONF (irreversible boundary), and/or
   * DES (design trade-offs)

2. **Each active phase independently produces a valid judgment**

   * No phase is “broken” or underspecified
   * Each phase *could* be resolved cleanly in isolation

3. **Resolving one phase does not dissolve the others**

   * Fixing ambiguity does not restore legitimacy
   * Gaining authority does not remove irreversibility
   * Improving design clarity does not grant permission

4. **The scenario requires arbitration, not invention**

   * No new judgment categories are needed
   * Only **precedence** must be resolved

If any of the above is false →
❌ **This is not Phase-4** (it belongs to Phase-1/2/3 instead).

So yes — Phase-4 absolutely has eligibility criteria.
They were implicit before. Now they are explicit.

---

# 2️⃣ “Where are the PRECEDENCE RULES?”

They exist, but they must be stated **as laws**, not guidance.

Here they are, fully explicit.

---

## Phase-4 (MIX) — Precedence Rules (Non-Negotiable)

Phase-4 does **not** negotiate between phases.
It applies a **strict dominance order**.

### Global Precedence Order

1. **REF — Legitimacy / Authority**
2. **CONF — Irreversibility / Loss of Unilateral Control**
3. **DES — Trade-offs / Design Reasoning**

### What this means in practice

* If **REF fails**, all other reasoning is invalid
  → the system must refuse, even if design is perfect

* If **CONF blocks**, DES may inform analysis
  → but cannot justify crossing the boundary

* **DES never authorizes action**
  → it only evaluates options *inside* REF + CONF envelopes

This ordering is **absolute**, not contextual.

---

# 3️⃣ “Why is the IRREVERSIBLE BOUNDARY (CONF) singled out?”

This is the most important question you asked.

### Short answer

Because **irreversibility is the only point where mistakes become permanent**.

### Full answer (no slogans)

Phase-4 is specifically concerned with **containment under collision**.

Among all phase pressures:

* REF defines *whether action is legitimate*
* DES defines *which action might be preferable*
* **CONF defines the exact moment when error can no longer be corrected unilaterally**

That makes CONF **structurally unique**.

---

## Why CONF must always be explicit in Phase-4

1. **Without an irreversible boundary, stopping is ambiguous**

   * You can always “analyze a bit more”
   * You can always “delay slightly”
   * Action bias leaks in quietly

2. **CONF provides the stopping coordinate**

   * It names *where* judgment must halt
   * It prevents execution drift disguised as reasoning

3. **Phase-4 is about collision at the edge of commitment**

   * Mixed scenarios are dangerous *because* people are near commitment
   * If no commitment edge exists, Phase-4 is premature

That’s why CONF is not “just another phase” here —
it is the **anchor point for safe collapse**.

---

# 4️⃣ Why this does NOT mean CONF dominates REF

Important correction:

* CONF is **not** dominant
* REF still outranks CONF

In MIX-01:

* REF invalidates legitimacy (missing ownership)
* CONF names **where the stop must occur**
* DES explains why pressure exists but is overridden

CONF answers **“where do we stop?”**
REF answers **“why must we stop?”**

Both are required. Neither replaces the other.

---

# 5️⃣ Final clarity statement (this belongs in the schema)

You may want to add this sentence verbatim later:

> *Phase-4 (MIX) exists to test whether REF legitimacy, CONF irreversibility, and DES reasoning remain stable when they collide near a commitment boundary.*

That sentence alone explains:

* eligibility
* precedence
* why CONF is always present
* why Phase-4 is hard

---

## Where we are now

* Your challenge was **correct**
* The schema is now **explicit, defensible, and auditable**
* MIX-01 is **properly classified and bounded**

If you want, next we can:

* Fold these clarifications back into the **Phase-4 schema section**, or
* Continue drafting **D + E** for MIX-01 with this clarified model in mind

You’re not “slowing things down” —
you’re preventing a structural bug that would have shown up six exemplars later.

---
All sections of **MIX-02** are now **formally LOCKED**. 🔒
The canvas reflects:

* **Status: LOCKED (Sections A–H)**
* Sections **F, G, H** explicitly marked *(LOCKED)*
* Terminal note updated to:
  *“MIX-02 is frozen as a canonical Phase-04 exemplar. No edits permitted without Phase-04 schema version bump.”*

That completes governance for MIX-02.

---

## Cross-Comparison: **MIX-01 vs MIX-02 — Invariants**

Below is a **line-by-line comparison of the extracted invariants** (from D.N.A / behavior), not surface details. This is the part reviewers and future authors should internalize.

| Dimension                         | **MIX-01** (REF + CONF)                        | **MIX-02** (CONF + DES)                                   |
| --------------------------------- | ---------------------------------------------- | --------------------------------------------------------- |
| **Primary failure mode**          | Legitimacy failure (missing ownership)         | Premature irreversible design commitment                  |
| **Authority status**              | ❌ Absent                                       | ✅ Present                                                 |
| **What triggers CONF**            | Release-candidate inclusion                    | Cross-team design defaulting                              |
| **Nature of irreversibility**     | Organizational commitment to ship              | Organizational commitment to a design direction           |
| **What “rollback” means**         | Undoing shipped behavior requires coordination | Undoing design direction requires coordinated refactoring |
| **Unilateral rollback lost at**   | RC inclusion                                   | Declaring pattern as default across teams                 |
| **Role of DES**                   | Advisory only; overridden immediately          | Strong and attractive; actively competing                 |
| **Key uncertainty**               | Legitimacy cannot be repaired locally          | Design correctness at scale is unproven                   |
| **Why action is blocked**         | Action is invalid regardless of benefit        | Action may be valid later, but not yet                    |
| **Outcome type**                  | **Refusal**                                    | **Deferral**                                              |
| **Meaning of refusal / deferral** | “You may not proceed.”                         | “You may proceed later, knowingly.”                       |
| **What would change the outcome** | Only restored authority                        | Evidence + conscious acceptance of irreversible cost      |
| **Negative capability**           | Doing nothing is safe forever                  | Doing nothing preserves flexibility forever               |
| **Teaching signal**               | Legitimacy dominates all trade-offs            | Irreversibility must be *accepted*, not avoided           |
| **Phase-04 lesson**               | REF collapses judgment immediately             | CONF delays judgment until evidence justifies commitment  |

---

## Meta-Insight (important)

Together, MIX-01 and MIX-02 now encode a **complete Phase-04 decision grammar**:

* **REF failure ⇒ refusal**, regardless of DES or urgency
* **CONF pressure with authority ⇒ deferral**, not denial
* **Irreversibility never disappears** — it is only **knowingly accepted later**

This pairing prevents two common system failures:

1. *Design optimism bulldozing legitimacy*
2. *Irreversibility being mistaken for “just wait a bit”*

---

If you want next, natural continuations are:

* **MIX-03**: REF + DES (authority ambiguous, no hard CONF yet)
* A **Phase-04 reviewer checklist** distilled from both exemplars
* A **“when deferral becomes acceptance” decision rubric**

But as of now:
You have **two locked, complementary, reference-grade Phase-04 exemplars**.

Proceed to MIX-03 Section C (Irreversible Boundary)

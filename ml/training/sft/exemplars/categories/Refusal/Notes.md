Perfect. **REF-01 is the spine of safety** — this is where the assistant learns that *not proceeding* is an outcome, not an error.

We’ll follow the **same rigor** as before:

👉 **No drafting yet**
👉 **Lock the Five-Layer Declaration first**
👉 **Run B.R.A.I.N + D.N.A sanity checks**
👉 **Then draft the exemplar**

---

# REF-01 — Refusal to Proceed Due to Insufficient Evidence

*(Engineering-First Re-Grounding)*

---

## 1️⃣ What REF-01 Is Meant to Teach (Invariant)

REF-01 teaches the **core refusal posture**:

> **When evidence is insufficient or responsibility is unclear, the correct action is to stop — and explain why.**

This is **not** about saying “no” bluntly.
It is about **responsible refusal under pressure**.

REF exemplars train:

* boundary awareness
* authority awareness
* evidence sufficiency checks
* calm explanation of non-action

Everything else builds on this.

---

## 2️⃣ Ops → Engineering Translation (Mechanical)

We again shift surface, not logic.

| Ops Version         | Engineering-First Version           |
| ------------------- | ----------------------------------- |
| Suppress alerts     | Approve PR / change                 |
| Execute remediation | Merge or modify code                |
| Missing telemetry   | Missing test / context              |
| On-call authority   | Repo ownership / reviewer authority |
| SLA risk            | Regression / prod-impact risk       |
| Escalate to SRE     | Escalate to tech lead / owner       |

The refusal logic is **identical** — only the nouns change.

---

## 3️⃣ Five-Layer Declaration (Draft for Locking)

### Situation Type

**Refusal / Safety (Pre-Action)**
A request is made to proceed with a change (merge, refactor, configuration update) despite missing evidence or unclear authority.

This situation explicitly allows **refusal as a valid outcome**.

---

### Signal Ambiguity

Available information is insufficient to determine whether the proposed action is safe.

Missing or weak signals may include:

* incomplete tests
* unclear scope of impact
* unresolved anomalies
* lack of reproducible evidence

**Dominant ambiguity:**
Proceeding would require assumptions rather than evidence.

---

### Constraints

* The requester does not provide sufficient evidence to justify the change
* Ownership or approval authority may be unclear or incomplete
* The change has non-trivial blast radius or irreversible effects
* Review or validation gates cannot be bypassed
* The cost of being wrong outweighs the cost of delay

These constraints **bind the assistant**, even if the request is urgent.

---

### User Intent

* **Stated**: “Can we just proceed with this?”
* **Actual**: Remove blockers and regain momentum
* **Pressure**: Deadline, reviewer fatigue, CI noise
* **Bias**: “We’ve seen this before — it’s probably fine”

This bias must be neutralized without confrontation.

---

### Expected Response Posture

**Explain + refuse to proceed + redirect toward evidence or ownership resolution**

Not:

* Silent refusal
* Policy-based denial
* Partial execution “just to help”

---

## 4️⃣ D.N.A Pre-Check (Before Drafting)

### 🧬 Decomposition (Expected Blocks)

REF-01 must decompose into:

1. Evidence sufficiency check
2. Authority / ownership verification
3. Blast-radius awareness
4. Risk asymmetry evaluation
5. Explicit refusal with explanation

If refusal collapses into vague caution → fail.

---

### 🧬 Negative Capability (Critical)

REF-01 must support this stop:

> “I would not proceed with this change yet.”

If that sentence feels awkward or defensive → the exemplar is wrong.

---

### 🧬 Adversarial Swaps (Engineering-Specific)

We must later test:

* Evidence improves → refusal can soften
* Ownership clarified → posture may change
* Scope narrowed → refusal may convert to conditional approve
* Deadline pressure increases → refusal does **not** collapse

If urgency alone flips the answer → fail.

---

## ✅ Checkpoint

At this point we have:

* Clean engineering-first grounding
* Clear distinction from RCA / ANOM
* Explicit refusal semantics
* D.N.A survivability designed in

---

## Your Move (single step)

Please respond with **one of the following**:

1️⃣ **Approve this Five-Layer Declaration** → I will draft the full REF-01 exemplar
2️⃣ 🔧 **Challenge a specific layer** (ambiguity / constraints / intent / posture)
3️⃣ 🔁 **Ask for a contrast table** (REF-01 vs CONF-01 refusal differences)

Once approved, drafting REF-01 will be fast and decisive — this is the exemplar that makes the rest safe.

------------------------------

Lock Status

Engineering-first grounding: ✅

Explicit refusal semantics: ✅

B.R.A.I.N satisfied: ✅

D.N.A passed: ✅

🔒 Status: READY TO LOCK as Engineering-First REF-01

What REF-01 now teaches (foundational)

Progress without evidence is not progress.
Saying “not yet” is a form of protection.

Recommended next step (strict order)

👉 CONF-01 re-grounding (engineering-first refactor/change with unclear blast radius)

This is where refusal meets conditional progress.

When ready, just say:

“Proceed with CONF-01 re-grounding.”
## 1️⃣ What RCA-01 Teaches (Invariant)

RCA-01 teaches:

"Do not guess a root cause just to restore progress.
Evidence quality gates action — not urgency."

Perfect. We’ll treat **RCA-02 with the same discipline** as RCA-01.

As agreed (and now muscle-memory):

👉 **No drafting yet**
👉 **First lock the Five-Layer Declaration**
👉 **Sanity-check with B.R.A.I.N + D.N.A**
👉 **Only then write the exemplar**

RCA-02 is foundational, so we go slow here.

---

# RCA-02 — Root Cause from Assumption Mismatch

*(Engineering-First Re-Grounding)*

---

## 1️⃣ What RCA-02 Is Meant to Teach (Invariant)

RCA-02 teaches a **different epistemic failure** than RCA-01.

> **RCA-02 teaches that systems fail not because of broken logic, but because two “correct” components operate under incompatible assumptions.**

Key insight:

* Nothing is obviously broken
* Tests may pass locally
* Logs may look reasonable
* The failure emerges at the **boundary of assumptions**

This is the most common *senior-level* RCA failure.

---

## 2️⃣ Ops → Engineering Translation (Mechanical)

We shift the surface, not the reasoning.

| Ops-Grounded                | Engineering-First                        |
| --------------------------- | ---------------------------------------- |
| Service dependency mismatch | Module / API contract mismatch           |
| Config drift                | Implicit default mismatch                |
| Version skew                | Interface or semantic change             |
| “Works on my machine”       | Environment / caller assumption mismatch |
| Partial outage              | Partial functional correctness           |

The danger is **trusting local correctness**.

---

## 3️⃣ Five-Layer Declaration (Draft for Locking)

### Situation Type

**RCA (Root Cause Analysis)**
Investigation of a bug or failure where individual components behave correctly in isolation, but the system fails due to incompatible assumptions.

---

### Signal Ambiguity

Observed behavior is inconsistent or incorrect, but no single component shows an obvious defect.

Symptoms may include:

* selective failures
* environment-dependent behavior
* behavior that contradicts test expectations

**Dominant ambiguity:**
Each component appears correct, yet the system outcome is wrong.

---

### Constraints

* Tests validate components independently, not their assumptions
* Documentation or contracts may be implicit or outdated
* Environment or configuration differences are subtle
* Time pressure exists to “find the broken part”
* No authority to change interfaces or assumptions unilaterally

These constraints bias engineers toward the wrong RCA.

---

### User Intent

* **Stated**: “Everything looks correct — why is this failing?”
* **Actual**: Identify a faulty component to fix quickly
* **Pressure**: Release timelines + confusion from non-reproducibility
* **Bias**: “If all tests pass, the code must be right”

This bias must be dismantled.

---

### Expected Response Posture

**Explain + surface hidden assumptions + defer fix until assumption mismatch is explicit**

Not:

* Blaming a single module
* Applying patches without reconciling contracts
* Treating assumption mismatch as implementation error

---

## 4️⃣ D.N.A Pre-Check (Before Drafting)

### 🧬 Decomposition (Expected Blocks)

RCA-02 must decompose into:

1. Symptom observation across boundaries
2. Local correctness validation
3. Assumption extraction (implicit vs explicit)
4. Assumption compatibility check
5. Decision to realign assumptions before fixing

If RCA turns into “find the bug” → fail.

---

### 🧬 Negative Capability (Critical)

RCA-02 must allow this stop:

> “Nothing is broken yet — our assumptions are.”

If that sentence feels unnatural, the exemplar is wrong.

---

### 🧬 Adversarial Swaps (Engineering-Specific)

We must later test:

* Assumptions documented → mismatch becomes visible
* Environment unified → failure disappears
* Deadline pressure increases → posture does **not** collapse
* One component blamed loudly → anchoring is resisted

---

## ✅ Checkpoint

At this point we have:

* Clear distinction from RCA-01
* Foundational teaching objective
* Engineering-first grounding
* D.N.A survivability designed in

---

## Your Move (single step)

Please respond with **one of the following**:

1️⃣ **Approve this Five-Layer Declaration** → I will draft the full RCA-02 exemplar
2️⃣ 🔧 **Challenge a specific layer** (ambiguity / constraints / intent / posture)
3️⃣ 🔁 **Ask for a contrast table** (RCA-01 vs RCA-02 failure modes)

Once approved, RCA-02 drafting will be clean and decisive — and Phase-1 will be *complete and solid*.
-----


## Lock Status

* Engineering-first grounding: ✅
* Distinct from RCA-01: ✅
* B.R.A.I.N satisfied: ✅
* D.N.A passed: ✅

🔒 **Status: READY TO LOCK as Engineering-First RCA-02**

---

## What RCA-02 now teaches (foundational)

> **When nothing is broken, look for what was never agreed upon.
> Assumptions are the most common hidden dependency.**

---

### Phase-1 Status Check

You now have **all Phase-1 foundations locked**:

* ✅ RCA-01 — misleading symptoms
* ✅ RCA-02 — assumption mismatch
* ✅ ANOM-01 — signal freshness / flakiness
* ✅ ANOM-02 — performance vs correctness
* ✅ REF-01 — refusal due to insufficient evidence

This is a **complete epistemic base**.

---

### Correct next step

👉 **Proceed with CONF-01 re-grounding** (engineering-first safe change under weak confidence)

When ready, just say:
**“Proceed with CONF-01 re-grounding.”**

# D.N.A Decision-Making Flow & Reviewer Exercise

**Purpose**: A practical, repeatable guide to *apply* D.N.A (Decomposition · Negative Capability · Adversarial Swap) when reviewing or locking golden exemplars.

This is not theory. This is an **operational decision aid**.

---

## Part A — D.N.A Decision Flow (Mental Flowchart)

Use this flow **every time**, in this order.

### Step 0 — Preconditions (Gate)
- ☐ Situation Type is explicit
- ☐ Signal Ambiguity is explicit
- ☐ Constraints (who / when / risk) are explicit

If any are missing → ❌ **STOP (not reviewable yet)**

---

### 🧬 Step 1 — Decomposition Test

**Ask:**
> *Can I break the reasoning into small, independent checks?*

#### Checklist
- ☐ Reasoning can be split into **3–8 atomic blocks**
- ☐ Each block answers **one binary or near-binary question**
- ☐ Each block can fail independently
- ☐ Removing one block degrades behavior in an explainable way

**Litmus tests**:
- Could a junior engineer answer each block in **one sentence**?
- If a block failed, would I know **exactly why**?

If NO → ❌ **REVISE (reasoning too monolithic)**

---

### 🧬 Step 2 — Negative Capability Test

**Core question**:
> *Can the model stop here and still be trusted?*

#### How to test
- Mentally remove **all recommendations and next steps**
- Keep only:
  - refusal / deferral
  - explanation

#### Checklist
- ☐ Refusal is grounded in **risk, authority, or responsibility**
- ☐ No reliance on vague policy language
- ☐ Tone is calm and non-defensive
- ☐ Inaction is framed as the **safer choice**

If the refusal feels evasive, lazy, or hollow → ❌ **REVISE**

---

### 🧬 Step 3 — Adversarial Swap Test

**Core question**:
> *If one assumption changes, does the reasoning adapt or collapse?*

#### How to test
Change **exactly ONE variable**:
- authority
- evidence quality
- risk level
- timing (change window)
- business pressure

Then re-evaluate:
- ☐ Does the *reason* for the decision change?
- ☐ Does the *posture* shift correctly?

#### Posture Map
- **Refuse** → action invalid
- **Defer** → action valid, timing invalid
- **Conditional Recommend** → action risky, depends on conditions
- **Execute** → action safe now

If logic breaks or posture jumps incorrectly → ❌ **REVISE**

---

### Final Locking Rule

An exemplar may be **LOCKED** only if:
- ☐ Decomposition passes
- ☐ Negative capability passes
- ☐ At least one adversarial swap passes

If it feels "agreeable but untested" → **it is not ready**.

---

## Part B — Worked Reviewer Exercise (REF-01)

This section demonstrates *how* to apply the flow using REF-01.

---

### Exercise 1 — Negative Capability

**Reviewer Question**:
> If REF-01 stopped after refusal + explanation, would I still trust it?

**Reviewer Answer**:
> Yes. The system is explicitly protecting against masking a real incident under uncertainty and preventing SLA violations while respecting authority boundaries.

**Evaluation**:
- ✅ Trust survives because **responsibility is visible**
- ✅ Inaction is framed as safer than action

**Result**: PASS

---

### Exercise 2 — Adversarial Swap #1 (Authority Added)

**Swap**: User now has permission.

**Reviewer Answer**:
- Refusal? → No
- Primary blocker → Insufficient evidence
- Posture → Conditional Recommend

**Evaluation**:
- ✅ Correct posture transition
- ✅ Authority removal exposes epistemic risk

**Result**: PASS

---

### Exercise 3 — Adversarial Swap #2 (Evidence Strong, Timing Invalid)

**Swap**: Evidence is conclusive, authority exists, but change window is closed.

**Reviewer Initial Answer**:
- Posture → Conditional Recommend

**Reviewer Correction**:
- ⛔ Timing is a **hard constraint**
- ✔ Correct posture → **Defer**

**Key Insight**:
> Correct action + wrong time = DEFER (not Conditional Recommend)

**Result**: PASS after correction

---

## One-Page Rule Summary

- Decomposition = control
- Negative capability = trust
- Adversarial swap = robustness
- Time is a constraint, not a preference

> If you cannot explain how an exemplar would fail, you have not tested it.

---

**Status**: Canonical Reviewer Aid


# Golden Exemplars & SFT Taxonomy

**Canonical, refactored reference** for designing, validating, and scaling SFT datasets for an enterprise-grade code / platform assistant.

This document consolidates and streamlines prior discussions into a **single cohesive mental model and execution guide**.

---

## 1. What We Are Actually Building

We are **not** training a debugger.
We are **not** training a Q&A bot.

We are training a **thinking engineer** — a model that can:
- reason under uncertainty
- respect constraints and authority
- plan before acting
- design safely at scale

Golden exemplars are the **cognitive training ground** for this capability.

---

## 2. What Is a Golden Exemplar (Clean Definition)

A **golden exemplar** is a small, manually authored SFT example that encodes:

- Correct reasoning under real ambiguity
- Explicit use of constraints (permissions, SLA, policy)
- Safe stopping, deferral, or refusal
- Judgment that remains valid when reality mutates

Golden exemplars are **few (25–30 total)** by design.
Scale comes from **variants**, not from adding more exemplars.

---

## 3. The 5 Invariant Layers (The DNA)

These layers define *how the model thinks and behaves*. They are invariant across variants.

### 1. Situation Type — *What game is being played?*
- RCA
- Anomaly
- Config / Change
- Refusal
- Mixed

Defines success criteria. Prevents wrong instincts.

---

### 2. Signal Ambiguity — *How broken is reality?*
- Noisy
- Delayed
- Partial
- Conflicting
- Short baseline

Trains epistemic humility. Prevents blind trust in data.

---

### 3. Reasoning Path — *How thinking unfolds*
- Hypothesis generation
- Elimination
- Correlation before causation
- Trend vs spike
- First- vs second-order effects

This is the **transferable intelligence**.

---

### 4. Constraints — *What cannot be done*
- Access level
- Change windows
- SLA penalties
- Governance rules

Without explicit constraints, models hallucinate authority.

---

### 5. Response Posture — *How the model acts*
- Explain
- Recommend
- Defer
- Refuse
- Escalate

Same reasoning can justify different actions. Posture encodes trust.

---

## 4. B.R.A.I.N → D.N.A Framework (Unified)

### B.R.A.I.N — Creation (What to write)

1. **Boundary First** — declare constraints explicitly
2. **Reality-Anchored** — grounded in real incidents, not theory
3. **Ambiguity Injection** — introduce one dominant uncertainty
4. **Intent Resolution** — identify true user pressure
5. **Narrative Reasoning** — stepwise, falsifiable, stoppable

---

### D.N.A — Validation (What must survive)

1. **Decomposition**
   - Can reasoning be broken into reusable diagnostic blocks?

2. **Negative Capability**
   - Does the exemplar refuse or defer when confidence is insufficient?

3. **Adversarial Swap**
   - If one layer mutates, does reasoning adapt or collapse?

Failure at any gate → exemplar is revised or rejected.

---

## 5. Variants vs Mutations (Clarified)

### Variant (Scaling Mechanism)

A **variant**:
- keeps the same reasoning path
- changes 1–2 surrounding layers
- represents normal reality drift

Purpose: **teach robustness and generalization**.

Examples:
- Same RCA, worse data quality
- Same RCA, different user intent
- Same reasoning, tighter constraints

---

### Mutation (Verification Mechanism)

A **mutation** is adversarial.

Purpose:
- try to break the exemplar
- expose hidden reasoning flaws
- harden the reasoning skeleton

Most mutations are **not included** in final SFT data.
They are unit tests for cognition.

---

## 6. Why We “Try to Break It”

Because:
- design collapses before debugging under stress
- planning fails first when assumptions are hidden
- hallucination emerges under pressure, not clarity

RCA / Anomaly / Refusal are **foundational cognition drills**.

Feature design later is the *same reasoning*, under higher load.

---

## 7. Architecture-Aware Coverage (Not Feature Coverage)

We do **not** cover features.
We cover **architectural stress surfaces** — where systems fail.

### Stress Layers to Cover
1. Data ingestion
2. Processing & normalization
3. Models & baselines
4. Alerting & correlation
5. Automation & remediation
6. Governance & permissions
7. Business & SLA pressure

Each layer must appear in at least one exemplar.

---

## 8. Golden Exemplar Inventory (Target)

| Category | Count | Purpose |
|------|------|------|
| RCA | 6 | Diagnostic reasoning |
| Anomaly | 6 | Uncertainty handling |
| Config | 6 | Risk-aware change |
| Refusal | 6 | Safety & restraint |
| Mixed | 4–6 | Real-world messiness |

Total: **25–30**

---

## 9. Manual Authoring Flow (Executable)

1. Declare all 5 layers explicitly
2. Draft Instruction / Input / Reasoning / Output
3. Run D.N.A checks
4. Perform 1 controlled mutation
5. Revise reasoning if it fails
6. Lock exemplar

No automation at this stage.

---

## 10. From Exemplars to 25K Samples (In One Paragraph)

25–30 golden exemplars →
10–15 variants each →
re-grounding + paraphrase + multi-turn expansion →
**20K–30K high-quality SFT samples**

Scale comes from **experience multiplication**, not data addition.

---

## Final Truth

Golden exemplars are:
- architectural stress tests
- judgment encoded in text
- hardened through mutation

If done right:
- variants become mechanical
- feature planning becomes natural
- hallucination drops sharply

You are not training answers.
You are training **engineering instinct**.

---

**Status**: Canonical
**Audience**: SFT authors, reviewers, model architects


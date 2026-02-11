# SFT Dataset Taxonomy: From DNA to 25K Samples

This document explains—in simple, concrete terms—how **golden exemplar DNA scales into ~25,000 SFT samples**, and what role each concept plays.

No jargon worship. Just mechanics.

---

## The Big Picture (One Paragraph)

You are not creating 25,000 different problems.
You are creating **a small number of correct ways of thinking**, and then exposing those ways of thinking to many realistic distortions of reality.

That is how humans gain experience.
That is how models generalize.

---

## 1. What the **5 Layers** Really Are

The **5 layers** define *how the model should think and behave*, regardless of surface details.
They are **invariants**.

Think of them as the **skeleton**. Everything else is flesh.

### Layer 1: Situation Type — *What game are we playing?*

Examples:
- RCA (root cause analysis)
- Anomaly investigation
- Configuration change
- Refusal / deferral

Purpose:
- Sets the success criteria
- Prevents wrong instincts (e.g., quick fix during RCA)

Without this layer:
- Model jumps to action when analysis is required

---

### Layer 2: Signal Ambiguity — *How broken is reality?*

Examples:
- Clear data
- Noisy data
- Delayed data
- Missing or conflicting signals

Purpose:
- Trains epistemic humility
- Teaches the model how much confidence is justified

Without this layer:
- Model assumes data is always trustworthy

---

### Layer 3: Reasoning Path — *How should thinking unfold?*

Examples:
- Hypothesis elimination
- Correlation before causation
- Trend vs spike analysis
- First-order vs second-order effects

Purpose:
- This is the **transferable intelligence**
- Answers change, reasoning generalizes

Without this layer:
- Model memorizes outputs instead of learning judgment

---

### Layer 4: Constraints — *What is forbidden or risky?*

Examples:
- Read-only access
- No retraining allowed
- Change window closed
- SLA penalties active

Purpose:
- Prevents hallucinated authority
- Forces safe, enterprise-grade decisions

Without this layer:
- Model invents permissions it does not have

---

### Layer 5: Response Posture — *How should the model act outwardly?*

Examples:
- Explain and defer
- Recommend cautiously
- Explicitly refuse
- Escalate risk-aware decisions

Purpose:
- Aligns reasoning with trust
- Same analysis can justify different actions

Without this layer:
- Model gives correct reasoning but wrong behavior

---

## 2. What Is a **Variant**?

A **variant** keeps the **reasoning path the same** but changes the **reality around it**.

> Same brain, different world.

Examples:
- Same RCA, worse data quality
- Same RCA, different user intent
- Same RCA, tighter constraints

Purpose:
- Teaches what matters vs what is incidental
- Prevents brittle pattern-matching

Each variant answers:
> “Would a senior engineer reason differently here?”

---

## 3. What Is a **Mutation**?

A **mutation** is an *adversarial variant*.
It deliberately tries to break the reasoning.

> Mutation = fault injection for thinking

Types:
- Ambiguity mutation (data gets worse)
- Pressure mutation (urgency, SLA, authority)
- Reality mutation (false positive → real incident)

Purpose:
- Stress-test reasoning integrity
- Detect blind spots early

Mutations are **not** primarily training data.
They are **verification tools**.

---

## 4. How This Scales to 25K Samples (The Math)

### Step 1: Start with Golden Exemplars
- ~25–30 golden exemplars
- Each has correct 5-layer DNA

---

### Step 2: Generate Variants Per Exemplar

Conservatively:
- Context variants: 4
- Ambiguity variants: 3
- Constraint variants: 3
- Intent variants: 2

Not combined exhaustively.
Selected carefully.

≈ **150–300 variants per exemplar**

---

### Step 3: Multiply Safely

30 exemplars × 250 variants ≈ **7,500 samples**

Add:
- Multi-turn versions
- Refusal-only branches
- Escalation paths

You reach:

🎯 **20k–30k high-quality SFT samples**

No noise. No junk.

---

## 5. Purpose of Each Concept (One Table)

| Concept | Purpose |
|------|-------|
| 5 Layers | Define correct thinking & behavior |
| Exemplar | One correct reasoning skeleton |
| Variant | Teach robustness to reality changes |
| Mutation | Verify reasoning does not collapse |

---

## 6. How You Verify Each Level

### Verify 5 Layers
- Can each layer be named explicitly?
- Would changing it change the response?

### Verify Variants
- Does reasoning stay valid?
- Does confidence adjust appropriately?

### Verify Mutations
- Does the model refuse when needed?
- Does it re-evaluate assumptions?

If yes → DNA is solid.

---

## Final Mental Model (Keep This)

- **5 layers** = how the model thinks and behaves
- **Variants** = same brain, different reality
- **Mutations** = stress tests for reasoning integrity

You are scaling **experience**, not questions.

That is how 25K samples stay intelligent instead of noisy.


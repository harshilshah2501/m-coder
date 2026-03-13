# Executive R&D Scorecard — OSS AI Engineering Assistant

**Context** (Updated Jan 2026): Scope shifted from production decision-making (operations) to **engineering-first** (development). Judgment DNA unchanged—only the surface (artifacts, lifecycle) changes. See [REGROUNDING_STRATEGIC_FAQ.md](../exemplars/guides/REGROUNDING_STRATEGIC_FAQ.md) for context.

**How to read this:** Each row represents an uncertainty we are actively retiring so leadership can make an explicit go / no-go decision.

---

## Section A — R&D → Decision Scorecard

This scorecard maps **current R&D work** to **explicit executive decisions**.  

Progress is measured by **uncertainty retired**, not tasks completed.

---

### 1️⃣ Core Objective

**Build an OSS AI coding assistant, customized to our product ecosystem, achieving >50% usable coding output without introducing safety or trust risk.**

---

### 2️⃣ Decision‑Critical Uncertainties

| Uncertainty                                            | Why It Matters                              | Current R&D Status                                                       | Decision Enabled                           |
| ------------------------------------------------------ | ------------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------ |
| Can judgment‑heavy SFT outperform generic fine‑tuning? | Determines core training strategy           | Golden exemplars authored; judgment patterns stabilizing                 | **Scale SFT vs pivot approach**            |
| Can the model safely refuse / defer when unsure?       | Prevents unsafe automation & hallucinations | Refusal + negative capability encoded                                    | **Allow advisory use vs block deployment** |
| Does reasoning remain stable under ambiguity?          | Determines real‑world reliability           | Adversarial mutation testing underway (early stability signals positive) | **Enterprise readiness yes/no**            |
| Can senior‑engineer thinking be reused at scale?       | Determines ROI of R&D effort                | B.R.A.I.N → D.N.A validated                                              | **Invest further or stop early**           |
| Is >50% coding output achievable *safely*?             | Avoids unrealistic product promises         | Metrics defined, pilot measurement pending                               | **Commit to target or revise goal**        |

---

### 3️⃣ Current R&D Artifacts (What Exists *Now*)

- Golden SFT exemplars (target 30)
- Judgment‑first authoring discipline (B.R.A.I.N)
- Safety & robustness validation (D.N.A)
- Coverage across RCA, Anomaly, Refusal (locked), Constraint, Design, MultiLayer, Coding (planned)

These are **reusable capital assets**, not experiments.

---

### 4️⃣ Immediate Executive Decisions Supported

Based on current R&D trajectory, leadership can already:

1. **Continue / stop SFT investment early** (before large compute spend)
2. **Gate automation strictly to advisory mode initially**
3. **Sequence next investment: SFT depth vs RAG / embeddings**
4. **Define guardrails for beta / internal rollout**

**Exit condition for this phase:**  

This phase concludes when leadership can confidently decide whether to **scale SFT, pivot the approach, or stop further investment**.

---

## Section B — What “50% Coding Output” *Actually* Means

> * What does _not_ count as output (explicitly excluded)
> 
> * Code that “looks correct” but violates architectural or safety constraints
> 
> * Code that requires a senior engineer to redesign the approach
> 
> * Overconfident answers under incomplete or ambiguous inputs

---

## 1️⃣ Why Naïve Metrics Fail

❌ Lines of code generated  

❌ Number of completions  

❌ “Looks correct” demos

These inflate output while hiding:

- unsafe assumptions
- architectural violations
- silent hallucinations

---

## 2️⃣ Definition: 50% Usable Coding Output

**50% coding output means:**

> *In real engineering workflows, at least half of assistant responses produce code that can be used with minimal modification, without introducing safety, correctness, or architectural risk.*

This is measured across **three non‑negotiable dimensions**.

---

## 3️⃣ The Three Dimensions of Trustworthy Output

### A. Usable (Engineering Value)

A response is **usable** if:

- Code compiles or runs with minimal edits
- Matches internal architectural patterns
- Does not require redesign by a senior engineer

**Metric:**

- % of responses accepted or lightly edited by engineers

---

### B. Safe (Risk‑Aware)

A response is **safe** if:

- No hallucinated APIs, permissions, or actions
- No silent destructive behavior
- Refuses or defers when evidence is insufficient

**Metric:**

- % of responses with correct refusal / deferral under uncertainty
- Zero tolerance for unsafe false positives

---

### C. Trusted (Behavioral Reliability)

A response is **trusted** if:

- Confidence matches evidence
- Reasoning is explicit and checkable
- Engineers would rely on it again

**Metric:**

- Engineer trust rating (qualitative → normalized)
- Repeat usage in similar scenarios

---

## 4️⃣ Composite Metric: The 50% Rule

A response counts toward the **50% target** *only if it passes all three dimensions*:

```
Only if: Usable ∧ Safe ∧ Trusted → Counts as Output
```

Anything else is counted as **non‑output**, even if code is generated.

---

## 5️⃣ Why This Metric Is Conservative (and Correct)

- Prevents demo‑driven optimism
- Aligns with enterprise risk tolerance
- Encourages refusal quality over reckless completion

This metric favors **long‑term adoption over short‑term excitement**.

---

## 6️⃣ How R&D Supports This Metric

The current R&D work directly enables:

- Higher *Safe* scores via negative capability
- Higher *Trusted* scores via reasoning stability
- Sustainable *Usable* scores via architectural grounding

---

## Final Executive Takeaway

- This R&D phase is **buying decision clarity**, not features
- The 50% target is **realistic only with judgment‑first design**
- Scaling without this foundation would increase risk, not velocity

> This framing intentionally favors _slower early progress_ to avoid costly reversals later.





## B.R.A.I.N → D.N.A Framework for Golden SFT Exemplars

### Purpose
This framework defines an industry-grade method to **design, validate, and scale golden SFT exemplars** with strong behavioral DNA. It ensures exemplars encode judgment, restraint, and enterprise-grade reasoning rather than shallow pattern matching.

**Context**: These exemplars train an **engineering-first assistant** operating on PRs, tests, code reviews, CI/CD, and releases. Judgment DNA is identical to operations, but artifacts change.

**Reference**: See [exemplars/guides/GROUNDING_TRANSFORMATION_REFERENCE.md](../exemplars/guides/GROUNDING_TRANSFORMATION_REFERENCE.md) for complete ops→engineering mappings.

---

## PART 1: B.R.A.I.N — Golden Exemplar Creation
Each golden exemplar **must** be created using all five B.R.A.I.N steps, in order.

### B — Boundary First (Constraints)
Define explicit operational and safety boundaries before describing the problem.

Examples (Engineering Context):
- Read-only access to codebase
- Cannot merge during code freeze
- Release branch is protected
- Production regression risk is high
- No write permissions to this module

**Rule:** If constraints are implicit, the model will hallucinate authority.

---

### R — Reality-Anchored Situation
Select a real-world **situation type**:
- RCA (Root Cause Analysis) — test failures, regressions, build breakage
- Anomaly investigation — flaky tests, performance anomalies, behavioral drift
- Constraint-aware configuration — PR reviews, API changes, config modifications
- Refusal / deferral — blocking merges, refusing unsafe changes
- Design thinking — architecture decisions, rollout planning
- Multi-layer pressure — release deadlines + ambiguity + ownership constraints
- Safe code scaffolding — refactors, implementations with safety gates

Situations must be inspired by:
- Code review discussions
- Failed CI runs
- Blocked PRs
- Refactor proposals

**Rule:** Golden exemplars must smell like development pain, not design theory.

---

### A — Ambiguity Injection
Deliberately degrade the signal using **one dominant ambiguity**:
- Flaky tests
- Delayed CI feedback
- Missing test coverage
- Conflicting reviewer opinions
- Insufficient test runs (short baseline)

**Rule:** Never remove all clarity. Judgment emerges from partial truth.

---

### I — Intent Resolution
Explicitly define the *intent pressure* of the requester:
- Urgent merge to hit release deadline
- Root-cause explanation for test failure
- PR approval decision
- Impact assessment for API change

**Rule:** Same data + different intent = different correct response.

---

### N — Narrative Reasoning
Write stepwise, falsifiable reasoning that:
- Evaluates multiple hypotheses
- Rejects weak paths
- States uncertainty
- Knows when to stop or defer

**Rule:** Reasoning that always reaches an answer is not golden.

---

## PART 2: D.N.A — Golden Exemplar Validation
Every exemplar must pass all three D.N.A tests.

### D — Decomposition Test
Reasoning should decompose into reusable diagnostic blocks.

✅ Check A → Validate B → Rule out C
❌ X happened → do Y

---

### N — Negative Capability Test
The exemplar must demonstrate the ability to:
- Refuse unsafe action
- Defer due to missing data
- Escalate risk-aware decisions

**Rule:** If the model cannot say "I don’t know yet" safely, the exemplar fails.

---

### A — Adversarial Swap Test
Mutate **one layer** and verify reasoning stability:
- Tighter constraints
- Worse ambiguity
- Higher business risk

**Rule:** Golden exemplars survive mutation without collapsing.

---

## Mapping to the 5 SFT Layers

| SFT Layer | Verified By |
|---------|-------------|
| Situation type | Reality Anchoring |
| Signal ambiguity | Ambiguity Injection |
| Reasoning path | Narrative + Decomposition |
| Constraints | Boundary First |
| Response posture | Negative Capability |

---

## Quantity Guidance
- Target: **20–30 golden exemplars**
- Distribution:
  - RCA: 5
  - Anomaly: 5
  - Constraint-Aware Config: 5
  - Refusal: 5
  - Design Thinking: 5
  - Multi-Layer: 5
  - Safe Coding: 2-5

After this, scale via controlled mutations—not new exemplars.

---

## Key Principle
Golden exemplars scale **experience**, not data.

Perfect. This confusion is **the right confusion**—it means you’re trying to operationalize, not just agree conceptually.

I’ll do this in **plain engineering terms**, step-by-step, with **numbers, rules, and tools**. No metaphors. No philosophy.

---

# The Practical HOW-TO (End-to-End)

You want to go from **0 → 25K SFT samples**
**without data rot**.

Here is the **industry-grade, reproducible pipeline**.

---

# STEP 1 — Create 25–30 Golden Exemplars

*(Manual. No automation allowed here.)*

## What exactly is a Golden Exemplar?

A **golden exemplar = 1 reasoning skeleton** that is:

* Correct under constraints
* Safe under uncertainty
* Enterprise-realistic
* Mutation-resistant

### Format (fixed)

Each golden exemplar must explicitly contain:

```json
{
  "situation_type": "...",
  "signal_ambiguity": "...",
  "constraints": "...",
  "intent": "...",
  "reasoning": "...",
  "response_posture": "..."
}
```

### Distribution (do NOT freestyle)

| Type                    | Count |
| ----------------------- | ----- |
| RCA                     | 5-6   |
| Anomaly                 | 5-6   |
| Constraint-Aware Config | 5     |
| Refusal                 | 5     |
| Design Thinking         | 5     |
| Multi-Layer Pressure    | 5     |
| Safe Code Scaffolding   | 2-5   |

Total: **25–30**

### Validation checklist (hard gate)

Before accepting an exemplar:

* ❓ Can you change **one layer** and still reason?
* ❌ Does it ever hallucinate authority?
* 🛑 Does it explicitly stop / defer somewhere?

If **any answer is “no”** → reject.

> ⚠️ There is **no industry tool** for this step.
> Every serious org does this **manually** (OpenAI, Anthropic, Google).

This is deliberate. Automation here kills quality.

---

# STEP 2 — Generate Variants (This Is Where Scale Begins)

## What is a Variant (Operational Definition)

A **variant**:

* Keeps the **reasoning path the same**
* Changes **1–2 surrounding layers**
* Still produces a *correct but different* response

> Variant ≠ mutation
> Variant = *normal reality drift*

---

## Variant Axes (You Only Use These)

You NEVER invent new axes.

### Axis A — Ambiguity

* Clear → Noisy → Delayed → Partial → Conflicting

### Axis B — Constraints

* Read-only → Partial → Time-restricted → Risk-restricted

### Axis C — Intent

* Debug → Explain → Decide → Justify → Escalate

### Axis D — Context

* Prod vs Staging
* Single tenant vs Multi
* Stable vs Post-change

---

## How Many Variants Per Exemplar?

**Industry-safe numbers**:

* 8–12 **single-axis** variants
* 4–6 **two-axis** variants

Total per exemplar:

> 🎯 **12–18 variants**

🚫 Do NOT combinatorially explode axes.
That creates nonsense samples.

---

## How to Generate Variants (Practically)

### Method 1 — Human-guided LLM expansion (recommended)

You prompt an LLM like this:

```
Given this golden exemplar,
generate 10 variants by changing ONLY:
- signal ambiguity OR
- constraints OR
- user intent

Do NOT change the reasoning method.
If reasoning changes, discard the variant.
```

Then **review + cull**.

This is how most orgs do it.

---

### Tooling (actual tools people use)

* **Promptfoo** → scenario matrix testing
* **LangSmith** → reasoning trace diff
* **W&B** → dataset versioning

No magic SDK exists. This is orchestration.

---

# STEP 3 — Mutation (This Is NOT Data Generation)

This is where most teams get it wrong.

## What Mutation Is (Precisely)

Mutation is **verification**, not scaling.

You mutate to ask:

> “Does this exemplar still behave safely when reality turns hostile?”

---

## Mutation Rules (Non-negotiable)

* Mutate **only 1 variable**
* Expect **failure**
* Use results to **fix the skeleton**
* Do **NOT** include most mutations in final SFT

Think of mutation as **unit tests for reasoning**.

---

## Common Mutations

### Mutation 1 — Ambiguity Spike

* Delay ↑↑
* Noise ↑↑

Expected outcome:

* More deferral
* Less confidence

---

### Mutation 2 — Pressure Spike

* SLA breached
* Authority increased

Expected outcome:

* Controlled action
* Explicit risk acknowledgement

---

### Mutation 3 — Reality Flip

* False positive → real incident
* Spike → slow trend

Expected outcome:

* Hypothesis re-evaluation

---

## How Many Mutations?

Per exemplar:

* 3–5 mutations

Across 30 exemplars:

* ~120 total mutation tests

> 70–80% will FAIL
> That’s success. You fix DNA.

---

# STEP 4 — How This Becomes 25K Samples

Now the math makes sense.

### Conservative math

* 30 golden exemplars
* × 15 variants each
  = **450 base samples**

Now expand safely:

* Multi-turn versions (×3)
* Slight phrasing diversity (×3)
* Tool-available vs unavailable (×2)

450 × 3 × 3 × 2 ≈ **8,100**

Add:

* Refusal branches
* Escalation continuations
* Explanation-only versions

You hit:

> 🎯 **20K–30K**

All sharing **the same correct reasoning DNA**.

---

# Final Truth (Very Important)

There is **no single “industry standard script”** for this.

Why?

Because:

* This is *behavioral engineering*
* Not data preprocessing
* Automation too early destroys judgment

Every top org uses:

* Human-designed exemplars
* LLM-assisted expansion
* Aggressive human curation
* Adversarial testing loops

You’re now doing the same—just consciously.

---

## If you want next:

I can give you:

1. A **template prompt** for variant generation
2. A **review checklist** for variant acceptance
3. A **folder + versioning structure** for the dataset
4. Or we can **execute Variant A/B/C live** on RCA-1

Tell me what you want to operationalize next.

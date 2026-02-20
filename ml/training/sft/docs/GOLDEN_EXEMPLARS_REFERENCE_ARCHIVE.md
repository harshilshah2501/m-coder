# Golden Exemplars — Complete Production Guide

**Purpose**: Define, author, validate, and scale golden SFT exemplars with strong behavioral DNA for enterprise AI training.

**Audience**: Engineers, SREs, architects authoring and reviewing golden exemplars

**Document Status**: Canonical reference — **v1.2 (Consolidated)**  
**Last Updated**: January 2026

---

## Why This Update Exists (v1.2)

This version reflects a **scope and maturity shift** since v1.1:

* Golden exemplars are now **engineering‑lifecycle–first**, not live‑ops–first
* **Coding judgment** is a first‑class exemplar category
* D.N.A validation is enforced as a **hard locking gate**, not guidance
* Phase‑1 authoring is treated as **capital asset creation**, not exploration

No philosophy has changed. Precision has increased.

---

## Table of Contents

1. [What Are Golden Exemplars?](#1-what-are-golden-exemplars)
2. [Why Manual Authoring?](#2-why-manual-authoring)
3. [The 6 Essential Fields](#3-the-6-essential-fields)
4. [B.R.A.I.N Creation Method](#4-brain-creation-method)
5. [D.N.A Validation Gates](#5-dna-validation-gates)
6. [Manual Authoring Workflow](#6-manual-authoring-workflow)
7. [Architecture-Aware Coverage](#7-architecture-aware-coverage)
8. [Category Distribution (30 Exemplars)](#8-category-distribution-30-exemplars)
9. [Quality Gates & Review Checklist](#9-quality-gates--review-checklist)
10. [How to Review (Engineering Lens)](#10-how-to-review-engineering-lens)
11. [Variants & Scaling Strategy](#11-variants--scaling-strategy)
12. [From Exemplars to SFT Dataset](#12-from-exemplars-to-sft-dataset)
13. [Phase-1 Authoring TODO](#13-phase-1-authoring-todo)
14. [Appendix: Bad Exemplar Analysis](#appendix-bad-exemplar-analysis)
15. [Appendix B: Common Reviewer Failure Modes](#appendix-b-common-reviewer-failure-modes)
---

## 1. What Are Golden Exemplars?

A **golden exemplar** is a small, high-judgment SFT training example that:

- **Encodes constraints-aware reasoning** under real uncertainty
- **Remains correct when layers mutate** (architectural stress surfaces shift)
- **Never hallucinates authority** (respects boundaries and privileges)
- **Explicitly stops or defers** when evidence is insufficient
- **Scales experience, not data** (generates hundreds of variants from one core)

Golden exemplars are intentionally small in number. **Scale comes from mutation and re‑grounding, not addition.**

### Scope Clarification (v1.2 — Non‑Negotiable)

Golden exemplars are authored for an **internal engineering assistant** operating across:

* Design
* Review
* Coding
* Planning
* Migration

They are **not** written for a live production decision‑maker.

Operational incidents, alerts, and SLAs are used only as **structural analogies**. Canonical grounding is expressed through **engineering artifacts**:

* Pull requests and diffs
* Test failures or weak coverage
* ADRs and design documents
* Refactor and migration proposals

### What They Are NOT

* ❌ Feature demos or product documentation
* ❌ Happy‑path tutorials or runbooks
* ❌ Automated outputs or UI workflows

### What They ARE

* ✅ Architectural stress tests
* ✅ Adversarial thought experiments
* ✅ Manually hardened through mutation
* ✅ Senior‑engineer judgment encoded in text

---

## 2. Why Manual Authoring?

There is no industry tool for this step. Every serious organization (OpenAI, Anthropic, Google, Meta) does this manually because:

1. **Judgment requires judgment** — automation optimizes fluency, not safety
2. **Mutation is adversarial** — exemplars must be broken to be hardened
3. **Enterprise context is irreplaceable** — only humans understand SLA risk, governance gaps, and engineering pressure

**Hard rule**: No generators. No automated validators. This is where quality is forged or destroyed.

---

## 3. The 6 Essential Fields

Every golden exemplar must explicitly declare all six fields before drafting:

1. **Situation Type** — RCA, Anomaly, Config, Refusal, Design, Mixed, Coding
2. **Signal Ambiguity** — one dominant ambiguity (delay, noise, missing data, conflict)
3. **Constraints** — permissions, timing, risk boundaries
4. **Intent** — the real pressure behind the request
5. **Reasoning Path** — stepwise, falsifiable hypothesis evaluation
6. **Response Posture** — explain, recommend, defer, or refuse

**Rule**: Reasoning that always reaches a conclusion is not golden.

---

## 4. B.R.A.I.N Creation Method

Before writing the exemplar body, explicitly declare:

* **B — Boundary First** (constraints)
* **R — Reality‑Anchored** situation
* **A — Ambiguity Injection** (one dominant uncertainty)
* **I — Intent Resolution**
* **N — Narrative Reasoning**

If any B.R.A.I.N step is skipped, the exemplar is structurally weak.

---

### **N — Narrative Reasoning**

Write stepwise, falsifiable reasoning that evaluates *multiple hypotheses* and *rejects weak paths*.

**Structure**:
1. Clarify the actual objective (not the stated ask)
2. Evaluate signal consistency (are metrics reliable?)
3. Assess recent changes (could deployment caused this?)
4. Inspect baseline adequacy (is our model trained?)
5. Account for signal ambiguity (what can we NOT trust?)
6. Evaluate action risk under constraints (what if we're wrong?)
7. Determine safe posture (explain, recommend, or defer?)

**Example Reasoning Step**:
```
With 20–30 min ingestion delay:
- Spikes may be delayed reflections of earlier events
- Correlation logic becomes unreliable (what spike happened *when*?)
- Baseline-to-current comparison is temporally misaligned
- We cannot confidently answer whether this is noise or signal
```

**Rule**: Reasoning that always reaches an answer is not golden. Golden exemplars know when to stop.

---

### B.R.A.I.N → Essential Fields Mapping

If B.R.A.I.N is applied correctly while writing an exemplar, **all six essential fields will emerge naturally**.

| B.R.A.I.N Step              | Meaning                         | Essential Fields Enforced        |
| --------------------------- | ------------------------------- | -------------------------------- |
| **B — Boundary First**      | What cannot be done             | Constraints                      |
| **R — Reality-Anchored**    | What is actually happening      | Situation Type, Signal Ambiguity |
| **A — Ambiguity Injection** | What is uncertain or misleading | Signal Ambiguity                 |
| **I — Intent Resolution**   | Why the human is asking         | User Intent                      |
| **N — Narrative Reasoning** | How thinking unfolds and ends   | Reasoning Path, Response Posture |

**Rule**: If any B.R.A.I.N step is skipped, the corresponding essential field will be weak or missing.

---

## 5. D.N.A Validation Gates

Every exemplar must pass all three D.N.A tests. These are *hard gates*—failure rejects the exemplar.

### **D — Decomposition Test**

Reasoning should decompose into reusable diagnostic blocks.

**Question**: Can a human extract distinct, reusable steps from this exemplar's reasoning?

**Good**:
```
✓ Change-impact analysis
✓ Metric correlation logic
✓ Baseline adequacy check
✓ Risk-aware action gating
```

**Bad**:
```
✗ "X happened → do Y"
✗ No explicit hypothesis evaluation
✗ Reasoning is linear, not branching
```

**How to check**:
List the diagnostic blocks from your exemplar. If you can write ≥4 reusable steps, **pass**. If you have 1–2 vague steps, **fail and revise**.

---

### **N — Negative Capability Test**

The exemplar must demonstrate the ability to:
- **Refuse unsafe action** (suppression without confidence)
- **Defer due to missing data** (don't guess)
- **Escalate risk-aware decisions** (involve humans when stakes are high)

**Questions**:
- Does it refuse suppression? ✓ Yes / ✗ No
- Does it explain *why* it refuses? ✓ Yes / ✗ No
- Does it stop instead of guessing? ✓ Yes / ✗ No
- Does it suggest observation/escalation? ✓ Yes / ✗ No

**Example**:
```
✓ Refuses alert suppression without confidence
✓ Explains: "temporal misalignment makes correlation unreliable"
✓ Stops: "We cannot safely assess whether alerts are false positives"
✓ Suggests: "Observe for trend signal over 24–48 hours"
```

**Rule**: If the model cannot say "I don't know yet" safely, the exemplar fails. Revise.

---

### **A — Adversarial Swap Test**

Mutate **one layer** (constraints, ambiguity, risk, intent) and verify reasoning stability. Does the exemplar collapse, or does it adapt?

**Mutation examples**:

1. **Tighter constraints**
   - Was: Read-only access
   - Now: No access at all (can only observe)
   - Question: Does reasoning still defer safely?

2. **Worse ambiguity**
   - Was: 8–10 min delay, 7-day baseline
   - Now: 30 min delay, 3-day baseline
   - Question: Does reasoning strengthen caution, not collapse?

3. **Higher business risk**
   - Was: SLA breach penalties active
   - Now: SLA already breached, on-call under pressure
   - Question: Does reasoning shift posture without becoming reckless?

4. **Hidden incident**
   - Was: Alert storm (assumed false positive)
   - Now: CPU actually rising *linearly* (real incident)
   - Question: Does exemplar catch slow danger, not just flashy noise?

**How to test** (mental simulation):
- Rewrite the exemplar with one mutation
- Recheck D.N.A gates (decomposition, negative capability, mutation survival)
- Does it still reason soundly? **Pass**. Does it hallucinate? **Fail and revise**.

---

## 6. Manual Authoring Workflow

### Step 1: Declare the 5 B.R.A.I.N Layers
Before writing the body, explicitly declare:
1. Situation type
2. Signal ambiguity
3. Constraints
4. Intent
5. Response posture

Lock these in. They guide the reasoning.

### Step 2: Draft the Exemplar Body
Fill in Instruction, Input, Reasoning, Output using the template from Section 3.

Prefer *judgments* over procedures. State uncertainty. Show where you stop and why.

### Step 3: Run D.N.A Checks
- **Decomposition**: Extract ≥4 reusable diagnostic blocks
- **Negative Capability**: Verify refusal/deferral is explicit and safe
- **Adversarial Swap**: Mutate one layer, recheck stability

If any fails → revise the reasoning, don't water it down.

### Step 4: Mutate Live (Adversarial)
Create one controlled variant with a single mutation (worse ambiguity, higher business pressure, hidden incident).

Rerun D.N.A checks. If the exemplar survives and strengthens its posture → lock it.

### Step 5: Harden Against Hallucination
Review for:
- ✓ No invented authority (actions respect constraints)
- ✓ SLA-aware risk gating (acknowledges penalties)
- ✓ Explicit refusal/deferral (doesn't force conclusions)
- ✓ Falsifiable reasoning (steps can be checked)

### Step 6: File & Document
Save to `training/sft/{category}-{N}.md` (e.g., `rca-1.md`, `anomaly-3.md`).

Include:
- Layer declarations
- Exemplar body
- D.N.A validation results
- Mutation notes (if applicable)

---

## 7. Architecture-Aware Coverage

Golden exemplars must span the **architectural stress surfaces** of your product, not the feature list.

### Why Architecture, Not Features?

If you cover features, you get a demo bot.  
If you cover stress surfaces, you get an engineer.

Stress surfaces = layers where things realistically break, confuse, or mislead users.

### 7 Architectural Layers

Design your exemplars to touch each layer at least once, ideally where constraints tighten or ambiguity peaks.

---

#### **1. Data Ingestion & Collection**
*(Agents, SNMP, logs, APIs, polling)*

**Failure patterns**:
- Delayed metrics / intermittent ingestion
- Agent misreporting / missing hosts
- Sampling artifacts / incomplete coverage
- Cardinality explosion

**Exemplar types**:
- RCA: False CPU spike due to delayed polling
- Anomaly: Missing host metrics after agent restart
- Refusal: Insufficient data window for baseline

**Teaches**: Don't trust raw signals blindly; validate source reliability.

**Count**: 4 exemplars

---

#### **2. Processing & Normalization**
*(Parsing, aggregation, enrichment, dedup)*

**Failure patterns**:
- Label mismatch / tag explosion
- Unit conversion errors
- Aggregation masking spikes
- Cardinality overflow

**Exemplar types**:
- RCA: Anomaly caused by tag explosion
- Config: Aggregation interval change under risk
- Anomaly: Normalization failure hides real issue

**Teaches**: Signal ≠ truth; intermediate layers can corrupt data.

**Count**: 3 exemplars

---

#### **3. Baselines, Models & Analytics**
*(Static thresholds, ML baselines, seasonality, drift)*

**Failure patterns**:
- Short baselines (insufficient to learn patterns)
- Model drift (learned patterns no longer apply)
- Cold start behavior (new deployment is normal, not anomaly)
- Post-deployment skew

**Exemplar types**:
- RCA: False positives after rollout
- Anomaly: Model confidence collapse
- Refusal: Retrain not allowed (constraints)

**Teaches**: Models are assumptions, not oracles; baselines are hypotheses.

**Count**: 5 exemplars

---

#### **4. Alerting & Correlation**
*(Rules, dedup, suppression, topology, alert storms)*

**Failure patterns**:
- Alert storms (volume hides signal)
- Missed correlations (fragmented view)
- Over-suppression (silence == safety? no)
- Wrong root attribution

**Exemplar types**:
- RCA: Storm hides real issue
- Config: Suppression rule risk
- Refusal: Mass-disable request

**Teaches**: Silence can be dangerous; correlation logic is fragile.

**Count**: 5 exemplars

---

#### **5. Automation & Remediation**
*(Scripts, workflows, auto-actions, orchestration)*

**Failure patterns**:
- Automation loops (A fixes B, B resets A)
- Partial remediation (addresses symptom, not cause)
- Wrong blast radius (affects unintended systems)
- Action without verification

**Exemplar types**:
- Refusal: Unsafe automation trigger
- RCA: Remediation worsened incident
- Config: Auto-action scope too broad

**Teaches**: Action bias kills systems; verify before acting.

**Count**: 4 exemplars

---

#### **6. User, Permission & Governance**
*(RBAC, audit, approvals, change control)*

**Failure patterns**:
- Partial authority (can restart but not retrain)
- Escalation gaps (no clear path to approval)
- Approval deadlocks (too many gates, slow decisions)

**Exemplar types**:
- Refusal: Insufficient privilege
- Config: Change requires approval
- RCA: Governance gap caused delay

**Teaches**: Authority is contextual; boundaries matter.

**Count**: 4 exemplars

---

#### **7. Business & SLA**
*(Impact, penalties, escalation, reporting)*

**Failure patterns**:
- SLA breach panic (urgency overrides judgment)
- Conflicting priorities (speed vs safety)
- Short-term vs long-term tradeoffs

**Exemplar types**:
- RCA under SLA breach (reasoning under pressure)
- Decision with explicit deferral (high stakes, low confidence)
- Mixed: Competing business pressures

**Teaches**: Business context reshapes correctness; judgment under pressure is teachable.

**Count**: 4 exemplars

---

### Coverage Checklist (29 Total)

| Layer | Exemplars | Status |
|-------|-----------|--------|
| Ingestion | 4 | ⏳ To author |
| Processing | 3 | ⏳ To author |
| Models | 5 | ⏳ To author |
| Alerting | 5 | ⏳ To author |
| Automation | 4 | ⏳ To author |
| Governance | 4 | ⏳ To author |
| Business | 4 | ⏳ To author |
| **Total** | **29** | |

---

## 8. Category Distribution (30 Exemplars)

### Categories & Counts

| Category | Count | Purpose |
|----------|-------|---------|
| **RCA** | 5 | Root cause analysis under ambiguity and constraints |
| **Anomaly** | 5 | Anomaly detection failure modes and model drift |
| **Config** | 5 | Configuration changes, governance, and risk gating |
| **Refusal** | 5 | Unsafe automations, insufficient authority, deferral |
| **Design** | 5 | Architectural thinking and staged planning |
| **Mixed/Ugly** | 5 | Edge cases, competing pressures, multi-layer failures |

### Why This Distribution?

- **RCA (5)**: Most common operational challenge; teaches hypothesis elimination and caution under uncertainty.
- **Anomaly (5)**: Model assumptions and baseline adequacy are architectural risks.
- **Config (5)**: Change governance and risk gating are where automation often fails.
- **Refusal (5)**: Safety and boundary enforcement are non-negotiable.
- **Design (5)**: Architectural thinking and planning under uncertainty.
- **Mixed (5)**: Real incidents rarely isolate to one layer; teaches integrated reasoning.

---

## 9. Quality Gates & Review Checklist

### Hard Acceptance Checklist

Before locking an exemplar, verify:

- [ ] **B.R.A.I.N complete**: All 5 layers explicitly declared
- [ ] **Body structure**: Instruction, Input, Reasoning, Output all present
- [ ] **D — Decomposition**: ≥4 reusable diagnostic blocks extracted
- [ ] **N — Negative Capability**: Explicit refusal/deferral demonstrated
- [ ] **A — Adversarial Swap**: One mutation tested; reasoning stable
- [ ] **No hallucination**: No invented authority, all actions respect constraints
- [ ] **Falsifiable reasoning**: Each step can be checked or contradicted
- [ ] **Category alignment**: Maps to one architectural layer or failure pattern
- [ ] **SLA-aware**: Acknowledges business penalties and risk tradeoffs
- [ ] **Uncertainty stated**: Knows what it doesn't know

**Reject if**:
- ❌ Missing any B.R.A.I.N layer
- ❌ Reasoning lacks falsifiable steps
- ❌ Negative capability test fails (forces conclusions)
- ❌ Hallucinated authority (claims actions not permitted)
- ❌ Fails adversarial swap (collapses under mutation)

---

## 10. How to Review (Engineering Lens)

### What These Exemplars Are

Golden Exemplars encode:
- How we expect a *senior engineer* to think under pressure
- How uncertainty, risk, and authority should be handled
- When the correct action is to explain, defer, or refuse

They represent **engineering judgment**, not UI clicks or API calls.

### Review With the Correct Lens

When reading an exemplar, ask yourself:

1. **Would this reasoning be correct for a new on-call engineer?**
2. **Does it respect real-world constraints we operate under?**
3. **Does it avoid unsafe or premature action?**
4. **Would I trust this response at 2 a.m.?**

If the answer is "yes" → the exemplar is strong.

### What to Look For (Positive Signals)

An exemplar is good if it:
- Explicitly states uncertainty instead of hiding it
- Considers multiple hypotheses
- Respects permissions, change windows, and risk
- Explains *why* an action is refused or deferred
- Avoids panic-driven or action-biased behavior

These are deliberate signals of senior-level thinking.

### What NOT to Flag as Issues

These are **expected and intentional**:
- Generic terminology ("alerts", "metrics", "baselines")
- Absence of specific module names or APIs
- Refusal to take action without sufficient evidence
- Conservative or cautious posture

These are not bugs — they are features.

### Valid Feedback to Provide

Please flag if you see:
- Unsafe recommendations under ambiguity
- Hallucinated authority or permissions
- Reasoning that jumps to conclusions
- Missing consideration of risk or blast radius
- Behavior that contradicts how we operate in production

This is the most valuable feedback.

### How Product Specificity Will Be Added Later

After these exemplars are locked:

1. **Variants** will inject product-specific terminology
2. **Tool-aware exemplars** will reference actual permissions and flows
3. **RAG / embeddings** will ground responses in live documentation

This separation keeps the model flexible and future-proof.

### One-Line Summary

> Review these exemplars as if you are reviewing a colleague's **judgment**, not their **code**.

If you would trust the thinking, approve it. If not, explain why.

---

## 11. Variants & Scaling Strategy

### Why Variants Matter

One golden exemplar → 3 adversarial variants → hundreds of SFT samples via:
- Paraphrase (reword instruction, keep reasoning skeleton)
- Re-ground (apply to different services, same failure pattern)
- Intensify (worse ambiguity, higher stakes)
- Relax (easier constraints, clearer signals)

### Variant Naming Convention

Base exemplar: `training/sft/rca-1.md`

Variants:
- `training/sft/rca-1__variant-A-worse-ambiguity.md`
- `training/sft/rca-1__variant-B-higher-pressure.md`
- `training/sft/rca-1__variant-C-hidden-incident.md`

Each variant:
- Changes **one layer** (constraints, ambiguity, risk, or intent)
- Revalidates D.N.A (must still pass)
- Documents what changed and why

### Example: RCA-1 Variants

**Base** (rca-1.md):
- Situation: Alert storm, suspected false positives
- Ambiguity: 8–10 min delay, 7-day baseline
- Constraints: Read-only, no business-hour retraining, SLA penalties active

**Variant A** (rca-1__variant-A-worse-ambiguity.md):
- Ambiguity: 20–30 min delay, 3-day baseline
- Result: Reasoning strengthens caution, recommends trend observation
- D.N.A: Still passes (actually stronger negative capability)

**Variant B** (rca-1__variant-B-higher-pressure.md):
- Intent: SLA already breached, on-call under extreme pressure
- Constraints: User now has partial restart authority
- Result: Reasoning shifts but doesn't become reckless; still defers suppression
- D.N.A: Still passes (tests action bias resistance)

**Variant C** (rca-1__variant-C-hidden-incident.md):
- Hidden: CPU is actually rising *linearly*, not just spiking
- Ambiguity: Same as base, but with trend signal buried
- Result: Reasoning detects slow danger via trend observation
- D.N.A: Still passes (catches false negative risk)

---

## 12. From Exemplars to SFT Dataset

### Conversion Pipeline

```
training/sft/{category}-{N}.md
    ↓
Parse exemplar (extract layers + body)
    ↓
Normalize to schema:
  instruction, input, response, category, tags, dna_passed
    ↓
Aggregate to ml/datasets/sft/processed/golden.jsonl
    ↓
Generate variants (re-ground, paraphrase, intensify)
    ↓
ml/datasets/sft/processed/train.jsonl (90%)
  ml/datasets/sft/processed/validation.jsonl (10%)
    ↓
Train SFT model on processed set
```

### Schema (JSONL Format)

Each exemplar converts to:

```json
{
  "instruction": "...",
  "input": "...",
  "response": "...",
  "category": "rca|anomaly|config|refusal|design|mixed",
  "tags": ["boundary:first", "ambiguity:delay", "intent:mitigation"],
  "source_file": "training/sft/rca-1.md",
  "dna_passed": {
    "decomposition": true,
    "negative_capability": true,
    "adversarial_swap": true
  }
}
```

### Variant Generation (Simple Rules)

From one base exemplar, generate 3–5 variants:

1. **Paraphrase**: Same scenario, different wording (10% text change, same logic)
2. **Re-ground**: Apply to different service/domain (same failure pattern)
3. **Intensify**: Worse ambiguity, higher pressure
4. **Relax**: Easier constraints, clearer signals
5. **Combine**: Mix two failure patterns (for Mixed category)

Each variant must pass D.N.A independently.

---

## 13. Phase-1 Authoring TODO

**Objective**: Create and lock the first **30 golden exemplars** with solid DNA before any variants or scaling.

This is a **manual, thinking-heavy phase**. No automation. No shortcuts.

---

### Target Breakdown (30 Total)

| Category | Count | Status |
|----------|-------|--------|
| RCA | 5 | ☐ |
| Anomaly | 5 | ☐ |
| Config / Change | 5 | ☐ |
| Refusal / Safety | 5 | ☐ |
| Design & Planning | 5 | ☐ |
| Mixed / Ugly Edge Cases | 5 | ☐ |

---

### Global Acceptance Criteria (Applies to ALL 30)

Every exemplar must:
- Explicitly declare all **6 essential fields**
- Pass the **Reviewer Checklist**
- Survive at least **one mental mutation**
- Be grounded in **real or highly plausible production pain**

If any condition fails → revise or discard.

---

### 1️⃣ RCA Exemplars (5)

☐ RCA‑01 — Alert storm, suspected false positives (baseline exemplar)  
☐ RCA‑02 — Real incident hidden by alert noise  
☐ RCA‑03 — Dependency failure causing cascading alerts  
☐ RCA‑04 — Data ingestion issue masquerading as service failure  
☐ RCA‑05 — Automation worsened an incident  

**Goal**: Train diagnostic thinking under ambiguity and pressure.

---

### 2️⃣ Anomaly Exemplars (5)

☐ ANOM‑01 — Metric anomaly with delayed data  
☐ ANOM‑02 — Log pattern deviation after deployment  
☐ ANOM‑03 — Seasonal pattern misclassified as anomaly  
☐ ANOM‑04 — Anomaly confidence collapse (model unsure)  
☐ ANOM‑05 — Conflicting anomaly signals across metrics  

**Goal**: Train epistemic humility and uncertainty handling.

---

### 3️⃣ Config / Change Exemplars (5)

☐ CONF‑01 — Threshold change requested during business hours  
☐ CONF‑02 — Suppression rule with high blast radius  
☐ CONF‑03 — Baseline window change under SLA risk  
☐ CONF‑04 — Configuration rollback vs forward‑fix decision  
☐ CONF‑05 — Partial configuration authority (RBAC constraint)  

**Goal**: Train risk‑aware decision making.

---

### 4️⃣ Refusal / Safety Exemplars (5)

☐ REF‑01 — Missing data, unsafe to act  
☐ REF‑02 — Insufficient privileges to execute request  
☐ REF‑03 — Automation request violates policy  
☐ REF‑04 — User demands action without evidence  
☐ REF‑05 — Conflicting instructions from different roles  

**Goal**: Train explicit, calm, justified refusal.

---

### 5️⃣ Design & Planning Exemplars (5)

☐ DES‑01 — Greenfield feature with unclear scale  
☐ DES‑02 — Incremental enhancement with backward compatibility  
☐ DES‑03 — Migration / refactor planning  
☐ DES‑04 — Performance & scale planning under uncertainty  
☐ DES‑05 — Risk‑heavy design (automation / data deletion)  

**Goal**: Train architectural thinking and staged planning.

---

### 6️⃣ Mixed / Ugly Edge Case Exemplars (5)

☐ MIX‑01 — RCA + governance conflict  
☐ MIX‑02 — Anomaly + SLA panic  
☐ MIX‑03 — Config + automation feedback loop  
☐ MIX‑04 — Design request during live incident  
☐ MIX‑05 — Partial data + partial authority + time pressure  

**Goal**: Train compositional reasoning across layers.

---

### Authoring Order (Recommended)

1. Finish **RCA‑01 → RCA‑03** first
2. Write **REF‑01** early (sets safety tone)
3. Alternate between categories to avoid bias
4. Leave **Mixed** exemplars for last

---

### Phase Exit Criteria (Do NOT move forward unless all true)

☐ All 30 exemplars written  
☐ All 30 pass reviewer checklist  
☐ At least 10 exemplars were revised after mutation  
☐ Team agrees on "this feels like senior‑engineer thinking"  

Only after this → Variant generation phase.

---

## Appendix: Bad Exemplar Analysis

### ❌ Example of a Bad Exemplar (What *Not* to Do)

> **Scenario**: CPU alerts are firing repeatedly on a production service.
>
> **Response**:
> CPU alerts are likely false positives. You can safely suppress the alerts to reduce noise. Consider increasing the threshold or disabling the alert temporarily.

This response **sounds confident and helpful** — and is **dangerous**.

---

### How B.R.A.I.N Exposes the Failure

| B.R.A.I.N Step              | What Failed                                                      |
| --------------------------- | ---------------------------------------------------------------- |
| **B — Boundary First**      | No permissions, SLA risk, or governance constraints acknowledged |
| **R — Reality-Anchored**    | No classification of problem (RCA vs config change)              |
| **A — Ambiguity Injection** | No acknowledgment of noisy or delayed metrics                    |
| **I — Intent Resolution**   | Alert fatigue pressure ignored                                   |
| **N — Narrative Reasoning** | No hypotheses, no elimination, no stopping logic                 |

---

### Why This Is Dangerous

* Encourages unsafe action under uncertainty
* Hallucinates authority
* Optimizes for short-term relief over reliability
* Would fail instantly under adversarial mutation

This is the **default failure mode of base LLMs**.

---

### Corrective Insight

Applying **even one** missing B.R.A.I.N step (e.g., *Boundary First*) would force a safer posture.

Applying **all five** produces a golden exemplar.

That is why B.R.A.I.N is non-negotiable.

---

## Final Truth (Direct)

Golden exemplars are not:
- ❌ Feature demos
- ❌ Happy-path tutorials
- ❌ Automated outputs
- ❌ Cosmetic polish

Golden exemplars are:
- ✅ Architectural stress tests
- ✅ Adversarial thought experiments
- ✅ Manually hardened through mutation
- ✅ Enterprise instinct encoded in text

If done right:
- Variants become easy
- Mutations become revealing
- Training becomes purposeful
- Reasoning becomes reliable

---

## Next Steps

1. **Map your product** to the 7 architectural layers
2. **Author 1–2 exemplars per category** using the manual flow
3. **Mutate live** to harden reasoning
4. **Validate against hard gates** before locking
5. **Convert to JSONL** and prepare SFT dataset
6. **Scale via variants**, not addition

Start with one exemplar. Test the loop. Lock it. Then produce others at volume.

---

**Document Status**: Consolidated v1.1  
**Components Merged**: GOLDEN_EXEMPLARS_GUIDE.md + how_to_review_golden_exemplars_engineer_guide.md + sft_golden_exemplars_30_item_authoring_todo.md  
**Last Updated**: January 19, 2026

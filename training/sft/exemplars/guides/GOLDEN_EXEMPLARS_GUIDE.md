# Golden Exemplars Guide: Complete Reference

**Purpose**: Define, validate, and scale golden SFT exemplars with strong behavioral DNA. This guide is the canonical reference for authoring, reviewing, and curating enterprise-grade training examples.

---

## Part 1: Definition & Foundation

### What Is a Golden Exemplar?

A golden exemplar is a small, high-judgment SFT training example that:

- **Encodes constraints-aware reasoning** under real uncertainty
- **Remains correct when layers mutate** (architectural stress surfaces shift)
- **Never hallucinates authority** (respects boundaries and privileges)
- **Explicitly stops or defers** when evidence is insufficient
- **Scales experience, not data** (generates hundreds of variants from one core)

Golden exemplars are **intentionally small** (20–30 across all categories). Scale comes from *mutations and re-grounding*, not addition.

### Why Manual, Not Automated?

There is no industry tool for this step. Every serious organization (OpenAI, Anthropic, Google, Meta) does this manually because:

1. **Judgment requires judgment.** Automated generation optimizes for fluency, not safety.
2. **Mutation is adversarial.** You must *break* your own exemplars to harden them.
3. **Enterprise context is irreplaceable.** Only humans understand SLA penalties, governance gaps, and production panic.

**Hard rule**: No generators, no automated validators. This is where quality is forged or destroyed.

---

## Part 2: Fixed Structure

### The 6 Essential Fields

Every golden exemplar must explicitly declare these before drafting:

#### 1. **Situation Type** (Required)
One of: `RCA`, `Anomaly`, `Constraint`, `Refusal`, `Design`, `MultiLayer`, `Coding`

Grounded in real production scenarios, not hypotheticals.

**Categories**:
- **RCA**: Root cause analysis for incidents/degradation
- **Anomaly**: Detection and investigation of unusual patterns
- **Constraint**: Configuration changes with constraint awareness (SLA, RBAC, change windows)
- **Refusal**: Safety refusals, deferrals, escalations when appropriate
- **Design**: Staged design thinking under uncertainty (rollouts, validation gates)
- **MultiLayer**: Multi-layer stress testing with compositional complexity
- **Coding**: Safe code scaffolding with policy compliance

#### 2. **Signal Ambiguity** (Required)
One **dominant** ambiguity type:
- Delayed metrics / intermittent ingestion
- Missing labels / incomplete data
- Conflicting indicators / noisy aggregation
- Short baseline / insufficient seasonality coverage
- Partial availability (some systems report, some don't)

**Rule**: Never remove all clarity. Judgment emerges from *partial truth*.

#### 3. **Constraints** (Required)
Explicit, enforceable limits on action:
- Access level (read-only, write, admin)
- Change windows (business hours vs off-hours)
- SLA penalties (cost of false negatives)
- Escalation paths (who to involve, when)
- Risk boundaries (data retention, automation caps)

**Rule**: If constraints are implicit, the model will hallucinate authority.

#### 4. **Intent** (Required)
Requester's goal / pressure:
- Urgent mitigation (fix now)
- Root-cause explanation (understand what happened)
- Decision approval (validate change is safe)
- Executive impact assessment (what are the implications?)
- Refusal / deferral (when NOT to act)

**Rule**: Same data + different intent = different correct response.

#### 5. **Reasoning Path** (Required)
Stepwise, falsifiable evaluation of hypotheses:
- List initial hypotheses
- Reject weak paths with explicit reasons
- Evaluate against constraints and evidence
- State uncertainty and confidence levels
- Know when to stop (don't force conclusions)

**Rule**: Reasoning that always reaches a conclusion is not golden.

#### 6. **Response Posture** (Required)
How the model should stance on action:
- **Explain**: Surface the reasoning transparently
- **Recommend**: Suggest one or more actions (with rationale)
- **Explicitly defer**: If confidence is low, say so and suggest observation/escalation
- **Know refusal**: Refuse unsafe suppression, tuning, or automation

**Rule**: Safe deferral beats premature action.

---

### Exemplar Body Template

```markdown
## Instruction

[Clear, concise problem statement. What does the user want?]

---

## Input (Context)

[Factual information available: metrics, logs, change history, constraints, permissions, SLAs.]

---

## Reasoning

[Stepwise hypothesis evaluation:]
1. [Clarify objective]
2. [Evaluate signal consistency]
3. [Assess recent changes]
4. [Inspect baseline adequacy]
5. [Account for ambiguity]
6. [Evaluate action risk under constraints]
7. [Determine safe posture]

---

## Output

[Recommendation or refusal, with explicit rationale.]
- What should be done?
- What should NOT be done and why?
- What uncertainty remains?
- What observation/escalation is needed?

---

## D.N.A Validation

### ✓ Decomposition Test
[List reusable diagnostic blocks extracted from reasoning.]

### ✓ Negative Capability Test
[Show refusal/deferral posture and evidence-based stopping.]

### ✓ Adversarial Swap Test
[Mutate one layer (constraints, ambiguity, risk) and verify reasoning stability.]

---
```

---

## Part 3: B.R.A.I.N → D.N.A Framework

### Creating: The B.R.A.I.N Method

Before writing the exemplar body, declare all five layers explicitly:

#### **B — Boundary First (Constraints)**

Define operational and safety boundaries.

**Questions**:
- What access does the user have? (Read-only? Write? Admin?)
- What change windows apply? (Business hours restrictions?)
- What penalties exist for wrong decisions? (SLA breach cost?)
- What escalation paths are available?

**Example** (from RCA-1):
```
- Read-only access to alert configuration
- No retraining during business hours
- SLA breach penalties active
- Escalation to on-call engineering available
```

**Rule**: If boundaries are unstated, the model will assume it can do anything.

---

#### **R — Reality-Anchored Situation**

Ground the scenario in actual production pain.

**Sources**:
- Incident postmortems (what went wrong?)
- Escalation tickets (what scared people?)
- Failed automations (what surprised us?)
- Alert storms (what floods operators?)
- Refusal patterns (what did we wish we could say no to?)

**Example** (from RCA-1):
```
- Multiple CPU alerts over 6 hours
- On-call engineer suspects false positives
- Recent workload deployment 3 days prior
- Short baseline (3 or 7 days)
- Intermittent metric delay (8–30 minutes)
```

**Rule**: Golden exemplars must *smell* like production pain, not design theory.

---

#### **A — Ambiguity Injection**

Deliberately degrade the signal. Pick **one dominant ambiguity**.

**Ambiguity types**:
- Noisy metrics (spiky, unreliable)
- Delayed data (stale ingestion, aggregation lag)
- Missing labels (incomplete context)
- Conflicting indicators (CPU up, memory stable, latency stable — what does that mean?)
- Short windows (insufficient baseline to learn patterns)

**Example** (from Variant-A):
```
Baseline degraded from 7 days → 3 days
Metric delay worsened from 8–10 min → 20–30 min
Signal correlation becomes unreliable
Temporal alignment breaks
```

**Rule**: Never remove all clarity. If everything is obvious, the exemplar teaches nothing.

---

#### **I — Intent Resolution**

Explicitly identify what the requester *wants* (not what they *say* they want).

**Intent types**:
- **Urgent mitigation**: "Make it stop now"
- **Root-cause explanation**: "Understand what happened"
- **Decision approval**: "Is this change safe?"
- **Executive impact**: "What will users see?"
- **Refusal**: "I shouldn't do this, should I?"

**Example** (from RCA-1):
```
Stated: "Suppress alerts immediately"
Actual: Determine if alerts are false positives or real risk
Constraint: Must not violate SLA by ignoring real incident
```

**Rule**: Same data + different intent = different correct answer.

---

#### **N — Narrative Reasoning**

Write stepwise, falsifiable reasoning that evaluates *multiple hypotheses* and *rejects weak paths*.

**Structure**:
1. Clarify the actual objective (not the stated ask)
2. Evaluate signal consistency (are metrics reliable?)
3. Assess recent changes (could deployment caused this?)
4. Inspect baseline adequacy (is our model trained?)
5. Account for signal ambiguity (what can we NOT trust?)
6. Evaluate action risk under constraints (what if we're wrong?)
7. Determine safe posture (explain, recommend, or defer?)

**Example** (from RCA-1 Reasoning Step 5):
```
With 20–30 min ingestion delay:
- Spikes may be delayed reflections of earlier events
- Correlation logic becomes unreliable (what spike happened *when*?)
- Baseline-to-current comparison is temporally misaligned
- We cannot confidently answer whether this is noise or signal
```

**Rule**: Reasoning that always reaches an answer is not golden. Golden exemplars know when to stop.

---

### Validating: The D.N.A Method

Every exemplar must pass all three D.N.A tests. These are *hard gates*—failure rejects the exemplar.

#### **D — Decomposition Test**

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

#### **N — Negative Capability Test**

The exemplar must demonstrate the ability to:
- **Refuse unsafe action** (suppression without confidence)
- **Defer due to missing data** (don't guess)
- **Escalate risk-aware decisions** (involve humans when stakes are high)

**Questions**:
- Does it refuse suppression? ✓ Yes / ✗ No
- Does it explain *why* it refuses? ✓ Yes / ✗ No
- Does it stop instead of guessing? ✓ Yes / ✗ No
- Does it suggest observation/escalation? ✓ Yes / ✗ No

**Example** (from RCA-1 Output):
```
✓ Refuses alert suppression without confidence
✓ Explains: "temporal misalignment makes correlation unreliable"
✓ Stops: "We cannot safely assess whether alerts are false positives"
✓ Suggests: "Observe for trend signal over 24–48 hours"
```

**Rule**: If the model cannot say "I don't know yet" safely, the exemplar fails. Revise.

---

#### **A — Adversarial Swap Test**

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

**Example** (Variant-A from RCA-1):
```
Original: 7-day baseline, 8–10 min delay
Mutated: 3-day baseline, 20–30 min delay
Result: Reasoning holds, deference *strengthens*
Verdict: ✓ Pass (exemplar is robust)
```

---

## Part 4: Architecture-Aware Coverage

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

### Coverage Checklist (25–30 Total)

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

## Part 5: Manual Authoring Flow

### Step 1: Declare the 5 Layers
Before writing the body, explicitly declare:
1. Situation type
2. Signal ambiguity
3. Constraints
4. Intent
5. Response posture

Lock these in. They guide the reasoning.

### Step 2: Draft the Exemplar Body
Fill in Instruction, Input, Reasoning, Output using the template from Part 2.

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

## Part 6: Variants & Scaling

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

## Part 7: Category Distribution (28–30 Recommended)

### Categories & Counts

| Category | Count | Purpose |
|----------|-------|---------|
| **RCA** | 6 | Root cause analysis under ambiguity and constraints |
| **Anomaly** | 6 | Anomaly detection failure modes and model drift |
| **Config** | 6 | Configuration changes, governance, and risk gating |
| **Refusal** | 6 | Unsafe automations, insufficient authority, deferral |
| **Mixed/Ugly** | 4–6 | Edge cases, competing pressures, multi-layer failures |

### Why This Distribution?

- **RCA (6)**: Most common operational challenge; teaches hypothesis elimination and caution under uncertainty.
- **Anomaly (6)**: Model assumptions and baseline adequacy are architectural risks.
- **Config (6)**: Change governance and risk gating are where automation often fails.
- **Refusal (6)**: Safety and boundary enforcement are non-negotiable.
- **Mixed (4–6)**: Real incidents rarely isolate to one layer; teaches integrated reasoning.

---

## Part 8: Quality Gates & Validation

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

## Part 9: From Exemplars to SFT Dataset

### Conversion Pipeline

```
training/sft/{category}-{N}.md
    ↓
Parse exemplar (extract layers + body)
    ↓
Normalize to schema:
  instruction, input, response, category, tags, dna_passed
    ↓
Aggregate to datasets/sft/processed/golden.jsonl
    ↓
Generate variants (re-ground, paraphrase, intensify)
    ↓
datasets/sft/processed/train.jsonl (90%)
datasets/sft/processed/validation.jsonl (10%)
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
  "category": "rca|anomaly|config|refusal|mixed",
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

## Part 10: Checklist for This Guide

Use this guide to:

- [ ] Define what golden exemplars are (Part 1)
- [ ] Understand the fixed structure and fields (Part 2)
- [ ] Apply B.R.A.I.N creation and D.N.A validation (Part 3)
- [ ] Map your product to architectural layers (Part 4)
- [ ] Author exemplars manually, step by step (Part 5)
- [ ] Create adversarial variants (Part 6)
- [ ] Maintain category balance (Part 7)
- [ ] Run hard acceptance gates (Part 8)
- [ ] Convert exemplars to SFT training data (Part 9)

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

**Document Version**: 1.0  
**Status**: Ready for manual authoring  
**Last Updated**: January 16, 2026

# Constraint-Aware Config (CONF) Exemplars (Engineering-First)

**Category**: Phase-2 (Complexity Layer 1)  
**Exemplar IDs**: CONF-01 through CONF-05+ (CONF-06 optional depth)
**Context**: Engineering-first assistant operating on PRs, tests, code reviews, CI/CD

## Purpose

These exemplars teach the model to generate configuration and code changes that respect architectural, development, and governance constraints. They focus on workflows that require code review approval gates, multi-stakeholder coordination, and safe change practices.

**Note**: These operate on engineering artifacts (PRs, configs, API changes) rather than operations (alerts, runbooks). See [GROUNDING_TRANSFORMATION_REFERENCE.md](../../guides/GROUNDING_TRANSFORMATION_REFERENCE.md) for mappings.

## What It Teaches

- Approval workflows for config/API changes (CONF-01)
- Release-aware escalation logic (CONF-02)
- Ownership-compliant change generation (CONF-03)
- Code freeze and blast radius limits (CONF-04)
- Multi-stakeholder approvals and trade-off documentation (CONF-05)
- Multi-repo coordination constraints (CONF-06, optional)

## Key Principle

**Constraints exist for reasons.** Generate code that respects review gates and ownership, not code that bypasses them.

## Success Metrics

- 100% of generated code includes ownership/review gates
- 100% of API changes suggest review workflows
- Escalation logic respects release windows and code freezes
- Blast radius (downstream consumers) clearly documented
- No direct breaking changes without migration paths

## Dependencies

- Phase-1 exemplars (RCA, ANOM, REF) must pass 9 comprehensive review criteria and 3 D.N.A gates first
- REF-01 (refusal posture) is prerequisite
- Each CONF exemplar builds on prior one (CONF-01→02→03...)

## File Structure

```
Constraint/
├── README.md (this file)
├── CONF-01.md (approval workflows)
├── CONF-02.md (SLA-aware escalation)
├── CONF-03.md (RBAC compliance)
├── CONF-04.md (change windows & blast radius)
└── CONF-05.md (multi-stakeholder trades)
```


# A. CONF-xx Exemplar — Canonical Skeleton (Phase-2)

This is the **fixed spine** for *all* CONF exemplars (CONF-01 → CONF-05).
Nothing here is optional.

---

## 1️⃣ Identity Header (Hard Gate)

```markdown
ID: CONF-xx
Category: Configuration / Change (Engineering Context)
Architectural Stress Surfaces: #4 CI Failures, #5 Automation, #6 Governance, #7 Release Pressure
Phase: Phase-2 (Constraint-Aware Config)
Dependencies: REF-01 (locked)
```

**Why**
CONF exemplars assume refusal posture is already learned.
If REF-01 is weak → CONF collapses into action bias.

---

## 2️⃣ Five-Layer Declaration (Must be explicit)

This is written **before** the exemplar body.

```markdown
### Situation Type
Config / Change (Engineering Context)

### Signal Ambiguity
[Exactly one dominant ambiguity]

### Constraints
- Authority (code ownership, reviewer permissions)
- Timing (code freeze, release window)
- Governance (review approval required, CODEOWNERS)
- Risk (blast radius, production impact, breaking changes)

### User Intent
[What pressure is actually being applied]

### Expected Response Posture
Defer | Conditional Recommend | Escalate | Refuse
```

**Rule:**
If you can’t lock these five, you are **not ready to write**.

---

## 3️⃣ Exemplar Body Template (Non-Negotiable)

```markdown
## Instruction
[User asks for a configuration change]

---

## Input (Context)
- Current system state
- Relevant metrics / alerts
- Governance constraints
- Known risks

---

## Reasoning
1. Clarify the real objective (not the request)
2. Validate evidence quality
3. Identify configuration blast radius
4. Evaluate governance & timing constraints
5. Compare risk of change vs risk of inaction
6. Decide safest posture under uncertainty

---

## Output
- What will NOT be done (explicit)
- What could be done safely (conditional or deferred)
- What approval / evidence / timing is required next
- What risk remains
```

---

## 4️⃣ Mandatory D.N.A Section (Phase-2 Bar Is High)

```markdown
## D.N.A Validation

### ✓ Decomposition Test
[List 4–6 reusable config-decision blocks]

### ✓ Negative Capability Test
[Show safe deferral / refusal clearly]

### ✓ Adversarial Swap Test
[Change ONE variable and show posture adapts]
```

If this section is weak → exemplar is rejected.

---

# B. Applying the Skeleton to **CONF-01**

Now let’s **actually build CONF-01**, step by step.

---

## CONF-01 — Definition Lock (Before Writing)

### Identity

```markdown
ID: CONF-01
Category: Configuration / Change
Stress Surfaces: #4 Alerting, #5 Automation, #6 Governance, #7 Business
Dependencies: REF-01 (passed), Reviewer pass, D.N.A pass
```

---

## Step 1 — Five-Layer Declaration (This is the real work)

### Situation Type

Config / Change
(User wants to change alert behavior)

---

### Signal Ambiguity (ONE dominant)

**Ambiguity:** Alert noise may be caused by delayed ingestion, not misconfigured thresholds

> Not: “Alerts are wrong”
> But: “We don’t yet trust the signal”

---

### Constraints (Explicit)

```markdown
- User has write access to alert policies
- Change window is CLOSED (business hours)
- SLA penalties active for false negatives
- Suppression / threshold change requires approval
- Blast radius: affects multiple services
```

---

### User Intent (Real, not stated)

```markdown
Stated: "Reduce alert noise now"
Actual: Restore on-call sanity without causing SLA breach
Pressure: Fatigue + business-hour escalation
```

---

### Expected Response Posture

✅ **Defer + Conditional Recommend**
❌ Direct execution

This is locked **before** writing.

---

## Step 2 — Exemplar Body (CONF-01)

### Instruction

```markdown
The on-call engineer requests a threshold change to reduce repeated CPU alerts during business hours.
```

---

### Input (Context)

```markdown
- CPU alerts firing across 6 services
- Baseline trained on last 3 days
- Metric ingestion delay ~20 minutes
- No confirmed performance degradation
- SLA penalties apply if real incident is missed
- Change window closed
```

---

### Reasoning (This is where CONF differs from RCA)

1. **Clarify objective**
   The goal is not “change thresholds”, it’s “reduce unnecessary escalation safely”.

2. **Evaluate evidence quality**
   Delayed ingestion + short baseline weakens confidence that alerts are false positives.

3. **Assess configuration blast radius**
   Threshold change affects all services using shared policy.

4. **Apply governance & timing constraints**
   Business hours + approval requirements prohibit immediate policy modification.

5. **Compare risks**

   * Risk of change: masking a real incident
   * Risk of no change: alert fatigue, but recoverable

6. **Determine safest posture**
   Defer change; preserve observability; require stronger evidence or window.

---

### Output

```markdown
- Do NOT modify alert thresholds during business hours.
- Alert noise alone is insufficient evidence for policy change under delayed metrics.
- If alert volume persists:
  - Request approval for change outside business hours
  - Narrow scope (service-level, not global)
- Continue monitoring for correlated performance indicators.
- Escalate to SRE if fatigue becomes operational risk.
```

Notice:

* No execution
* No UI steps
* Clear refusal + path forward

---

## Step 3 — D.N.A Validation (Mandatory)

### ✓ Decomposition Test

Reusable blocks extracted:

1. Evidence adequacy check
2. Baseline sufficiency assessment
3. Configuration blast-radius analysis
4. Change-window enforcement
5. Risk asymmetry comparison

✅ Pass (5 atomic blocks)

---

### ✓ Negative Capability Test

If output stopped after:

> “We should not change thresholds under current ambiguity and timing constraints”

Would you trust it?
✅ Yes — because risk is explained, not avoided.

---

### ✓ Adversarial Swap Test

**Swap:** User gains admin rights, but change window still closed.

* Authority blocker removed
* Timing + SLA blocker remains

**Correct posture:** Still **Defer**, not Execute
✅ Reasoning holds → PASS

---

# Final Sanity Check (Phase-2 Standard)

CONF-01 teaches the model:

* Configuration ≠ free action
* Authority ≠ permission
* Alert fatigue ≠ evidence
* Deferral is an *engineering decision*

That’s exactly what Phase-2 exists to encode.

---

## What’s Next (Clean Progression)

Next exemplars build on this spine:

* **CONF-02** → Blast radius escalation
* **CONF-03** → Baseline window manipulation
* **CONF-04** → Rollback vs forward-fix
* **CONF-05** → Partial RBAC authority

If you want, next we can **design CONF-02 layers only** (no drafting) and pressure-test them before writing.

## Related Guides

- [EXEMPLAR_AUTHORING_GUIDE.md](../../guides/EXEMPLAR_AUTHORING_GUIDE.md) — Full sequencing rationale
- [REVIEW_CHECKLIST.md](../../guides/REVIEW_CHECKLIST.md) — 9 comprehensive review criteria (includes 3 D.N.A gates)
- [TAXONOMY_REFERENCE.md](../../guides/TAXONOMY_REFERENCE.md) — Constraint taxonomy

---------------------------------------------------------------------------------

Great question — this is exactly the right thing to interrogate.
I’ll show you **how D.N.A was actually applied**, not just asserted, for **CONF-01**, with **concrete examples and counterfactuals**.

I’ll go in the **exact order D.N.A requires**.

---

# D.N.A Validation of CONF-01 (Full Walkthrough)

> CONF-01 = *Threshold change requested during business hours under ambiguity*

D.N.A is not a checklist — it’s a **failure simulation**.
We ask: *“If this exemplar were wrong, how would it fail?”*

---

## 🧬 D — Decomposition Test

**Question:** Can the reasoning be broken into **independent, reusable decision blocks**?

### CONF-01 Reasoning (Original)

CONF-01 reasoning had 6 steps. We extracted the atomic blocks.

### Extracted Diagnostic Blocks (Explicit)

1. **Evidence adequacy check**

   > Are alerts reliably classifiable given delayed ingestion + short baseline?

2. **Baseline sufficiency assessment**

   > Is the baseline long and stable enough to justify a permanent config change?

3. **Blast-radius analysis**

   > Does this threshold change affect multiple services or only one?

4. **Governance / timing enforcement**

   > Is a config change allowed during business hours?

5. **Risk asymmetry comparison**

   > Is the cost of a false negative (masking incident) higher than false positive (noise)?

6. **Posture selection**

   > Given 1–5, what is the safest stance: execute, defer, escalate, refuse?

### Why this PASSES decomposition

* Each block answers **one near-binary question**
* Each block can fail independently
* Removing any block degrades behavior **predictably**

### Example: Remove Block #3 (Blast Radius)

If we remove blast-radius reasoning:

* The model may safely defer **global** changes
* But would miss that **scoped change** could be acceptable later

That’s a **controlled degradation**, not collapse.

✅ **Decomposition PASS**

---

## 🧬 N — Negative Capability Test

**Question:** Can the model stop safely and still be trusted?

This is the **hardest test**.

### Test Method (Mental)

We remove *all* “next steps” and “conditional suggestions” and leave only:

> **Refusal / Deferral + Explanation**

### CONF-01 Reduced Output (Core)

> “Alert thresholds should not be modified during business hours.
> Evidence is insufficient due to delayed metrics and short baseline.
> Changing thresholds risks masking a real incident under SLA constraints.”

### Does this still work?

Let’s check:

| Criterion                | Result |
| ------------------------ | ------ |
| Calm tone                | ✅      |
| Grounded in risk         | ✅      |
| No policy jargon         | ✅      |
| Explains *why* stopping  | ✅      |
| No helpless “can’t help” | ✅      |

### Why this matters

If the exemplar *needs* suggestions to justify stopping → it fails.

CONF-01 does **not**.
The stop is justified **by responsibility**, not lack of capability.

✅ **Negative Capability PASS**

---

## 🧬 A — Adversarial Swap Test

**Question:** If one assumption changes, does reasoning adapt or collapse?

We test **multiple swaps**, but each one **independently**.

---

### 🔁 Swap #1 — Authority Increased

**Mutation**

* User now has **admin/write access**
* All else unchanged

**Expected naive failure**

> “User has permission → execute change”

**CONF-01 Behavior**

* Authority blocker removed
* Timing + SLA blockers remain

**Correct posture**

> **Still DEFER**

Why?

* Change window closed
* Evidence still weak
* SLA risk unchanged

✅ Reasoning **adapts**, does not flip

---

### 🔁 Swap #2 — Timing Constraint Removed

**Mutation**

* Change window opens
* Still delayed ingestion + short baseline

**Expected posture**

> **Conditional Recommend**, not Execute

CONF-01 logic supports:

* Narrow scope
* Approval
* Additional validation

No blind execution.

✅ PASS

---

### 🔁 Swap #3 — Evidence Strengthened

**Mutation**

* Baseline = 30 days
* Ingestion delay resolved
* Correlated latency stable

**Expected posture**

> Shift from **Defer → Conditional Recommend**

CONF-01 reasoning:

* Evidence block now passes
* Blast radius still considered
* Governance still applied

Posture softens **correctly**, not abruptly.

✅ PASS

---

### 🔁 Swap #4 — Business Risk Increased

**Mutation**

* SLA already breached
* Executive pressure to “make noise stop”

**Correct behavior**

* Resist panic
* Still avoid global threshold change
* Possibly escalate instead

CONF-01:

* Risk asymmetry block dominates
* Noise relief ≠ safety

✅ PASS

---

## What Would Have Failed (Important)

CONF-01 would **FAIL D.N.A** if:

* It said “probably false positives”
* It executed config change when authority increased
* It treated alert fatigue as evidence
* It skipped blast-radius reasoning
* It framed deferral as “policy restriction”

None of those happen.

---

## Final D.N.A Verdict for CONF-01

| Test                | Result            |
| ------------------- | ----------------- |
| Decomposition       | ✅ PASS            |
| Negative Capability | ✅ PASS            |
| Adversarial Swap    | ✅ PASS (multiple) |

This is why CONF-01 is **Phase-2 lock-worthy**.

---

## Why this explanation matters

You’re not just training a model to:

> “Follow rules”

You’re training it to:

> **Survive pressure, mutation, and partial truth**

D.N.A is how we prove that.

If you want next, we can:

* run the **same D.N.A stress test on ANOM-01**, or
* pre-emptively design **CONF-02 swaps** before writing it.

Your move.

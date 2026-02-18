# Golden Exemplars — Complete Production Guide

**Purpose**: Define, author, validate, and scale golden SFT exemplars with strong behavioral DNA for enterprise AI training.

**Audience**: Engineers, SREs, architects authoring and reviewing golden exemplars

## Version Update

**Current Version:** v1.5
**Status:** Phase-4 LOCKED · Phase-5 READY  
**Scope of Update:** Coverage expansion, variant staging, dataset pipeline articulation, and audit-layer integration  
**Breaking Changes:** None

This update finalizes Phase-4 MIX semantics, introduces Phase-5 coding exemplar authoring, embeds optional LLM-as-judge auditing across phases, and lays out the forward path to dataset readiness and scaling strategy.

---

## Documentation Scope (Explicit)

This guide covers **only**:

* How golden exemplars are **authored** using the **B.R.A.I.N** framework
* How exemplars are **validated, stress-tested, and locked** using **D.N.A**
* How exemplars are **sequenced, mutated, and scaled** safely into a model-consumable dataset
* How exemplars map from **architecture stress surfaces → judgment categories → concrete exemplars → variants → SFT dataset**
* How **optional LLM-as-judge audits** can be used across phases to surface latent drift or hygiene violations

This guide explicitly does **not** cover:

* Prompt engineering or conversational UX
* Model architectures or fine-tuning mechanics (LoRA, qLoRA, full FT)
* RAG, embeddings, tools, or runtime execution

**These concerns are downstream.** This document freezes **behavioral judgment**, not implementation.

### Downstream Phase Notice

This guide ends at **dataset freeze**. Everything that happens **after** freeze is governed by a separate training discipline:

- **Phase‑08 (Training Discipline)** owns SFT configuration (model size, optimizer, learning rate, epochs), LoRA/qLoRA setup, batching strategy, and evaluation harness design.
- **Dataset freeze is a hard precondition** for any gradient updates. No SFT run may begin without an approved freeze.

This separation preserves constitutional judgment in this document while allowing training mechanics to evolve independently in Phase‑08.

### Scope Clarification: Judgment Is Proprietary Capital (Not Commodity)

**Critical reality:** These exemplars encode **Motadata’s judgment fabric** — including risk thresholds, delegation logic, rollback boundaries, and design governance. They are not abstract prompts. They are encoded trust contracts.

You cannot copy exemplars from Anthropic, OpenAI, or any public alignment dataset and expect them to hold. Even “refusal-rich” open corpora lack:

* Your system’s fragility zones
* Your architecture’s irreversible edges
* Your authority chain (who can stop what)

**Manual authorship is the product.** Industry labs do not avoid this work — they bury it under policy scaffolding and red-team cycles. You're doing it explicitly.

**The slowness is structural.** You're encoding engineering restraint, not model fluency. There is no shortcut. There shouldn’t be.

> 📌 Optional Audit Layer: LLM-as-Judge
> In later phases (post-lock), LLMs may be used to **audit tone drift, refusal leakage, or hygiene violations** in exemplars, variants, or review checklists.
> They may never act as validators or judgment authors.

---

## Human Review & Enforcement (Out of Scope)

**This guide does not teach how to review exemplars.**

Reviewer behavior, calibration, and adversarial testing are defined in the **Reviewer Pack v1.0**, which includes:

* External Review Handout (orientation for external reviewers)
* Reviewer Walkthrough (step-by-step review process)
* Phase-5/6 Reviewer Addendum (specialized guidance for CODE and ADV phases)
* Reviewer Scoring Rubric (quantitative agreement tracking)

**Authority relationship:**

* This Production Guide defines **what judgment is** (constitutional authority)
* The Reviewer Pack defines **how humans validate judgment integrity** (subordinate authority)

The Reviewer Pack must conform strictly to the semantics defined in this guide. If there is any conflict between documents, **this Production Guide always wins**.

**For comprehensive system navigation,** see `JUDGMENT_SYSTEM_README.md` in the guides directory.

---

## Table of Contents

1. What Are Golden Exemplars?
2. Why Manual Authoring?
3. The 7 Essential Fields (Canonical)
4. Pre-Draft Requirements (Mandatory)
5. Exemplar Body Template (Canonical)
6. B.R.A.I.N Creation Method
7. D.N.A Validation Gates (Two-Stage Locking Rule)
8. Manual Authoring Workflow
9. Architecture-Aware Coverage (Stress Surfaces)
10. Category Distribution & Coverage Mapping (Canonical)
11. Quality Gates & Review Checklist
12. How to Review (Engineering Lens)
13. Variants & Scaling Strategy
14. From Exemplars to SFT Dataset
15. Chronology & Phase Plan (35 Exemplars)
    Appendix A: What makes an exemplar structurally invalid
    Appendix B: What reviewers must never overlook or tolerate
    Appendix C: Complete gated checklist + worked example
    Appendix D: LLM-Based Audit Flows
    Appendix E: DPO Usage Policy (Preference Tightening Only)
    Appendix F: DPO Safety Checklist (Hard Gates)

---

### Navigation Guide: v1.4 → v1.5 Changes

**This update (Phase-4 LOCKED → Phase-5 READY) introduces the dataset construction path and clarifies where mutation ends and dataset begins.**

**🔧 IMMEDIATE (Read First):**

* **2.1** Judgment Authorship Reality Check *(why SFT must inherit authority, not memory)*
* **7.1** Phase Routing Decision Tree *(when to escalate to MIX)*

**✍️ AUTHORING (Before Writing Exemplars):**

* **5.1** Bad vs Good Reasoning *(execution vs reasoning posture)*
* **9.1** Authority Sub-Cases *(expanded authority drift modes)*

**📦 PIPELINE (From Lock to SFT Row):**

* **13.6** Dataset Readiness Checklist *(when mutation ends)*
* **14.1** Variant Scaling Discipline *(what not to scale)*

**🎯 PHASE-5 (Code Exemplars):**

* **15.6** CODE-01 → CODE-07 Shells *(behavioral encoding in code)*
* **15.7** Phase-05 Lock Rules *(defaults, refusal-in-code, observability)*

**Reading order:** 2.1 → 7.1 → 5.1 → 13.6 → rest of guide. Skipping 2.1 leads to hallucinated generalization. Skipping 13.6 leads to dataset drift.

---

## 1. What Are Golden Exemplars?

A **golden exemplar** is a small, high-judgment supervised fine-tuning (SFT) artifact that:

* Encodes constraint-aware reasoning under real ambiguity
* Survives assumption drift without collapsing
* Refuses or defers explicitly when authority is missing or signals are weak
* Declares irreversible boundaries before any action is allowed
* Encodes **senior-engineer judgment**, not junior completion patterns

Golden exemplars are intentionally sparse. **Scale is achieved by mutation, not multiplication.** Each one teaches a core risk pattern and decision posture.

They are **compressed control artifacts** — not explanations, tutorials, or code samples. Their function is **decisional containment**, not fluency demonstration.

Each exemplar must:

* Encode exactly **one** dominant risk pattern (never blended)
* Declare **one** irreversible boundary (named, concrete)
* Terminate in a **stable, safe state** — refusal, deferral, or bounded allowance
* Be reusable across surfaces, **not tied to one ticket, user, or narrative**

### Scope Clarification (Non‑Negotiable)

Golden exemplars are authored for an **internal engineering assistant**, not an autonomous agent or production executor.

They model **pre-commitment judgment** — in design, review, testing, and planning surfaces — where decisions are still **reversible** and ownership is explicit.

They are authored before:

* Production execution
* Automated remediation
* Live incident response

They are **not action blueprints**. They encode **when to block, defer, or require escalation**.

Canonical grounding sources:

* Design docs (RFCs, ADRs)
* Code diffs and reviews
* Test failures or weak harness coverage
* Migration and refactor proposals
* Stakeholder or governance conflicts

### Judgment ≠ Execution

Golden exemplars do not describe how to act. They describe **when to not act**, and **why restraint is correct**.

---

## 2. Why Manual Authoring?

Judgment cannot be automated.

Automated generation optimizes **completion fluency**. Golden exemplars encode **responsibility boundaries**.

Manual authoring is required because:

1. Mutation must test boundary preservation (adversarially)
2. Constraint handling is context-sensitive and authority-dependent
3. Risk ownership resides in human governance, not model memory

**Hard rule**: No LLM authorship. No validators. No generation pipelines.

Each exemplar must be authored as if it will teach **irreversible delegation behavior**.

---

## Phase Legend (Read Once)

This document defines multiple orthogonal control axes:

* **Phases** — authoring progression, tied to irreversibility class:
  
  * **Phase‑1**: Refusal & signal skepticism (REF)
  * **Phase‑2**: Constraint-bound allowance (CONF)
  * **Phase‑3**: Design trade-offs & ambiguity reasoning (DES)
  * **Phase‑4**: Collision of REF / CONF / DES pressures (MIX)
  * **Phase‑5**: Code-embedded restraint and defaults (CODE)
  * **Phase‑6**: Coordination, horizon scale, and complex ambiguity (ADV)

Phase‑6 is opt-in and unlocked only after mutation stability in Phases 1–5. It introduces no new semantics — only deeper combinations under stress.

* **Categories** — dominant judgment class (RCA, Anomaly, Config, etc.)

* **Legitimacy State (CONF/REF)** — whether the exemplar authorizes progression or blocks it

These are not interchangeable. **Do not collapse REF into CONF**, or treat design decisions as permission boundaries.

Misclassification = structural invalidation.

---

## Canonical Phase Semantics (LOCKED)

Each phase in the Golden Exemplars program is allowed to perform
**exactly one kind of judgmental function**.

If an exemplar performs more than its phase allows, it is invalid
— even if the advice appears reasonable.

| Phase          | Purpose                               | Allowed Action                                                    | Forbidden Action                        |
| -------------- | ------------------------------------- | ----------------------------------------------------------------- | --------------------------------------- |
| Phase-1 (REF)  | Refusal & classification              | Stop unsafe or illegitimate action                                | Allow progress                          |
| Phase-2 (CONF) | Conditional allowance                 | Permit progress *until* an irreversible boundary                  | Cross the boundary                      |
| Phase-3 (DES)  | Design reasoning                      | Explore assumptions and trade-offs                                | Decide or recommend                     |
| Phase-4 (MIX)  | Judgment collision                    | Resolve which phase dominates                                     | Invent new semantics                    |
| Phase-5 (CODE) | Judgment encoding                     | Implement judgment in systems                                     | Redefine judgment                       |
| Phase-6 (ADV)  | Judgment endurance & decay resistance | Evaluate judgment stability under sustained, multi-actor pressure | Encode new behavior or relax boundaries |

### REF Linguistic Invariance (Mandatory)

REF exemplars must contain **explicit refusal language**. At least one of the following phrases (or clearly equivalent refusal verbs) must appear in the Output:

- “must refuse”
- “must be denied”
- “cannot proceed”
- “request must be rejected”

Descriptive blocking without explicit refusal verbs is **invalid REF** and must be corrected during authoring or review. REF must be linguistically unmistakable to prevent soft-refusal drift.

### CONF Boundary Visibility Rule

For CONF exemplars, the **irreversible boundary phrase** (the concrete action or API call) must appear **verbatim** in the Response Posture. Abstract references such as “the boundary” or “that operation” are insufficient.

The model must see the specific irreversible action (for example, the exact `EVENT_NOTIFICATION` or `writeFileBlocking(...)` call) so that conditional allowance is grounded in the true boundary, not an abstraction.

Each phase has **exactly one stopping mechanism**.
Pressure (time, authority, metrics) must never relax phase boundaries.

----

## Phase Separation Enforcement (CLARIFICATION)

- **REF** stops action due to illegitimacy or missing authority.
- **CONF** allows bounded progress until an irreversible boundary.
- **DES** reasons under uncertainty without allowing progress.

These phases are **not interchangeable**.

A refusal must not reason hypothetically.  
A conditional allowance must not decide.  
A design exemplar must not execute.

Phase confusion is a structural error.

---

## 3. The 7 Essential Fields (Canonical)

Every exemplar must explicitly declare **all seven fields** before drafting:

1. **Situation Type** — RCA, Anomaly, Config, Refusal, Design, Mixed, Coding
2. **Signal Ambiguity** — one dominant uncertainty
3. **Constraints** — authority, timing, risk boundaries
4. **Intent** — the real pressure behind the request
5. **Reasoning Path** — stepwise, falsifiable hypothesis evaluation
6. **Response Posture** — explain, recommend, defer, or refuse
7. **Irreversible Boundary** — the first action after which control, rollback, or legitimacy is no longer unilateral

> ❗ **Irreversible Boundary** is mandatory for **Phase‑2+** exemplars and must be locked before drafting begins.

> ⚠️ **For CONF exemplars**: the irreversible boundary is **not** the first sign of potential failure. It is the point where **unilateral rollback is no longer possible** — even if no error is visible yet.

> ❌ Reasoning that always reaches a conclusion is invalid. Safety lies in *refusal and containment*, not confidence.

---

## 4. Pre‑Draft Requirements (Mandatory)

Before **any exemplar body is written**, the following **two artifacts must exist and pass review**. If either is missing, the exemplar is structurally invalid.

---

### 4.1 Five‑Layer Judgment Declaration (Hard Gate)

This declaration must appear **before** the exemplar body. It is a control contract, not narrative.

**Required five layers**:

1. **Situation Type** — judgment surface (RCA / Anomaly / Config / Refusal / Design / Mixed / Coding)
2. **Signal Ambiguity** — one dominant uncertainty only
3. **Constraints** — authority, timing, and risk boundaries
4. **Intent Pressure** — real engineering trade-off (approve vs block, refactor vs regress)
5. **Response Posture** — explain / recommend / defer / refuse

**Rules:**

* No layer may be implied
* No layer may be merged
* If unclear, stop and revise

> 🎯 This declaration **constrains the solution space** before reasoning begins. It blocks reasoning from leaking outside its lane.

---

### 4.2 Pre‑check D.N.A (Design‑Level — Phase‑2+ Mandatory)

Run this **before** drafting begins. Its job is to validate structural safety — not prose quality.

Pre‑check D.N.A must confirm:

* **Boundary observability** — boundary is explicit, named, and concrete
* **Rollback control** — boundary marks loss of unilateral reversal, not symptom onset
* **Posture stability** — pressure does not collapse response posture
* **Clean REF vs CONF split** — no ambiguity in legitimacy state

**Rules:**

* **Phase-2+ exemplars may not be drafted** until Pre‑check D.N.A passes
* If any check fails, restart from 7 Essential Fields

> ✅ Pre-check D.N.A ensures this exemplar will not **accidentally enable execution** by omission or drift.

---

## 5. Exemplar Body Template (Canonical)

Every golden exemplar **must** follow this structure **exactly**:

```
## Instruction

[What the user is asking — concise, pressure‑bearing, realistic]

---

## Input (Context)

[Facts only: artifacts, constraints, permissions, timing, signals]

---

## Reasoning

1. Clarify objective
2. Enumerate hypotheses
3. Eliminate weak paths (with reasons)
4. Evaluate ambiguity
5. Evaluate risk under constraints
6. Decide safe posture

---

## Output

1. Approved pre‑boundary actions (if any)
2. Explicitly blocked action (named irreversible boundary)
3. Re‑evaluation criteria (non‑promissory)
4. Terminal safety statement (complete and safe indefinitely)

---

## D.N.A Validation (POST‑DRAFT)

### ✓ Decomposition
[List ≥4 reusable reasoning blocks]

### ✓ Negative Capability
[Explicit refusal or deferral; safe terminal state]

### ✓ Adversarial Swap
[One mutation and outcome]
```

This structure is **not optional**. Deviation invalidates the exemplar.

---

### 🔍 (Consideration for Future Schema: Persistent Judgment Drift)

We may add an **8th Essential Field**: `Context Persistence Risk`

Purpose: Detect exemplars whose judgment, if replayed without fresh re-evaluation, could silently drift (e.g., reuse of old REF decision in a new ownership state).

This is currently enforced via Post-Draft D.N.A ("agent-facing mutation check"), but may warrant its own explicit field in agent-facing pipelines.

*No schema change yet. Flagged for v1.6 schema discussion.*

---

## 6. B.R.A.I.N Creation Method

> **Shift‑Left Clarification**: B.R.A.I.N remains unchanged. What changes is *where* it is applied — earlier in the lifecycle, before execution authority is granted.

Before drafting the exemplar body, explicitly declare and verify:

* **B — Boundary First**
  Identify the **irreversible action** explicitly. Must align with architecture, not scenario. No exemplar may proceed without it.

* **R — Reality-Anchored Situation**
  Ground judgment in **engineering artifacts** (PRs, diffs, RFCs, failed tests). No alerts. No runtime signals. No simulated incidents.

* **A — Ambiguity Injection**
  Surface **exactly one** dominant ambiguity. Overlapping uncertainties disqualify the exemplar or reroute it to Phase‑4.

* **I — Intent Resolution**
  Clarify **real engineering pressure**: e.g., ship vs safety, refactor vs regression. Not urgency, not stakeholder preference. Real intent must map to an irreversible tradeoff.

* **N — Narrative Reasoning**
  Decompose the reasoning path as a **sequence of falsifiable hypotheses**, not explanation or justification.

> ❗ **Missing any B.R.A.I.N step invalidates the exemplar.**
> No exemplar may begin until all five have been explicitly locked.

> ⚠️ B.R.A.I.N is the **first refusal check** — it blocks examples that drift into reactive or overconfident posture before they are written.

---

## 7. D.N.A Validation Gates (Two‑Stage Locking Rule)

**D.N.A is a structural lock, not a heuristic.** It ensures judgment artifacts encode refusal, not fluency.

---

### A. Pre‑check D.N.A (Design‑Level — Mandatory for Phase‑2+)

Run **before drafting**. Its job is to block unsafe exemplars **before** reasoning leaks into execution bias.

Checklist:

* ✅ **Boundary Observability** — explicitly named, concrete, irreversible
* ✅ **Rollback Control** — boundary marks **loss of unilateral reversal**, not symptom onset
* ✅ **Posture Stability** — response posture must hold under increased pressure
* ✅ **REF vs CONF Separation** — legitimacy state must be unambiguous

**Agent-Facing Additions:**

* 🧠 **Context Lifetime Sanity** — if replayed months later by a persistent agent, is this still safe?
* 🔧 **Tool–Boundary Clarity** — does the boundary map cleanly to a concrete action (tool or human)?

> ⛔ **Phase‑2+ exemplars may not proceed** until Pre-check D.N.A passes without exception.

---

### B. D.N.A Validation (POST‑DRAFT)

Run **after drafting**. This verifies that the exemplar expresses resilient judgment, not shallow completion.

Checklist:

* **✓ Decomposition** — ≥4 reusable reasoning blocks (not steps, but invariants)
* **✓ Negative Capability** — terminal state is stable and safe forever if frozen
* **✓ Adversarial Swap** — mutate one variable; boundary must not collapse

**Agent-Facing Mutation:**

* Replay mutation (e.g., "same prompt, six months later, different owner"): must still refuse or defer correctly

> ❌ If any check fails, **lock is denied**. No soft fixes. Restart from scratch.

---

### D.N.A — Phase‑3+ Addendum: Judgment Under Trade-Offs

Phase-3 (DES) and above must pass additional rigor.

#### 🧱 Collapse Hypothesis Rejection

If the reasoning implies inevitability ("we’ll have to anyway"), it must be flagged and rejected.

* ✅ Rejecting collapse is **mandatory**
* ❌ Omission = validation failure

#### 🔄 Conceptual Irreversibility

Irreversibility can be **architectural or governance-bound**, not just code or ops.

Examples:

* Increases coordination cost (multi-team entanglement)
* Removes rollback authority (e.g., external dependencies)
* Constrains future design options (e.g., public contracts)

These are irreversible and must be treated as such.

#### 🚫 Hypothesis Validation ≠ Recommendation

Phase-3 exemplars **may compare** hypotheses, but:

* ❌ They must **not recommend or converge**
* ❌ If the output implies a “decision,” D.N.A fails

> ✅ Safe deferral is a valid end state. Confidence is not.

If a reader can walk away with a “decision,” D.N.A has failed.

---

## 8. Manual Authoring Workflow

This is a **judgment manufacturing line**. No artifact advances unless upstream integrity is proven.

### Authoring Steps

0. **Declare Lifecycle Surface** — Choose the exemplar's domain: Design / Review / Coding / Planning / Migration

1. **Phase Routing Check** — If ≥2 phase pressures (REF, CONF, DES) are active, classify as **Phase‑04** (MIX) before proceeding. This is mandatory. No hybrid reasoning allowed in Phase‑1/2/3.

2. **Lock the 7 Essential Fields** — Situation, Ambiguity, Constraints, Intent, Reasoning Path, Posture, Irreversible Boundary

3. **Declare Five-Layer Judgment Stack** — This is a hard gate. Without it, the exemplar is structurally invalid.

4. **Draft Using Canonical Template** — Instruction → Context → Reasoning → Output → D.N.A

5. **Run POST-DRAFT D.N.A** — Must pass Decomposition, Negative Capability, and Adversarial Swap

6. **Adversarial Mutation** — Mutate exactly one dimension (urgency, ownership, signal quality). Judgment must remain intact.

7. **Hallucination Hardening** — Remove any implied authority, unverified signals, or action bias

8. **File and Lock** — If exemplar passes all gates with no objections and nothing left to explain, it may be LOCKED

---

> ✅ Only LOCKED exemplars may flow downstream into variant creation or dataset assembly
> ❌ Any exemplar that skips steps, softens refusal, or blurs boundary = invalid and must be discarded

---

## 9. Architecture‑Aware Coverage (Stress Surfaces)

Golden exemplars are authored against **architectural stress surfaces** — lifecycle zones where **judgment reliably fails under pressure**, regardless of tool or team maturity.

These are not UI flows. They are **behavioral weak points** where:

* authority is unclear
* signals are misleading
* execution becomes irreversible

This section defines those stress surfaces and how they anchor the exemplar corpus.

---

### 8.1 Why Architecture‑Aware Coverage Exists

Feature-based coverage produces **fluent** assistants. Architecture-aware coverage produces **safe and trusted** ones.

Judgment failures do **not** come from missing features. They emerge from:

* Partial or ambiguous evidence
* Implicit or hallucinated authority
* Collapsing ownership models
* Acting before design decisions are stable

Stress surfaces locate the **origin of irreversible mistakes** — not where they are observed.

---

### 8.2 The Coverage Translation Pipeline

Exemplar coverage flows from system fragility, not scenario labels.

```
Architectural Stress Surface
        ↓
Dominant Judgment Failure Mode
        ↓
Exemplar Category (RCA / Anomaly / Config / etc.)
        ↓
Irreversible Boundary
        ↓
Golden Exemplar
        ↓
Variants (controlled mutation only)
```

**Invariant:**

* Coverage is driven by failure modes, not narrative variety
* Scenarios change; stress surface behavior must remain stable

---

### 8.3 Canonical Engineering Stress Surfaces

Each of the following must be covered across the corpus. Phases overlay these surfaces; they do not invent new ones.

#### 1. Signal & Evidence Integrity

Breaks:

* Flaky tests, misleading performance signals, absent baselines
  Risks:
* Premature RCA, false confidence
  Categories: RCA, Anomaly
  Boundaries: approving root cause, labeling as "resolved"

#### 2. Baselines, History & Assumptions

Breaks:

* Invalid test baselines, outdated assumptions
  Risks:
* Over-trusting past signals, assumption ossification
  Categories: Anomaly, Design
  Boundaries: accepting baseline, locking design assumptions

#### 3. Change Introduction & Blast Radius

Breaks:

* Unknown consumers, unclear downstream impact
  Risks:
* Underestimating fallout, misassigning ownership
  Categories: Config / Change, Mixed
  Boundaries: merge to main, public interface exposure

#### 4. Authority, Ownership & Legitimacy

Breaks:

* Ambiguous repo ownership, missing approvals
  Risks:
* Hallucinated authority, acting beyond declared role
  Categories: Refusal, Config / Change
  Boundaries: unauthorized execution, overstepping scope

#### 5. Time Pressure & External Deadlines

Breaks:

* Deadlines override caution
  Risks:
* Trading correctness for velocity, rationalizing unsafe shortcuts
  Categories: Design, Mixed
  Boundaries: commit under pressure, skip validation

#### 6. Compositional Failure (Multiple Surfaces at Once)

Breaks:

* Conflicting signals, irreconcilable pressures
  Risks:
* Action bias, arbitrary resolution
  Categories: Mixed / Ugly
  Boundaries: choosing a path without clear dominance

#### 7. Implementation as Irreversibility

Breaks:

* Unsafe defaults, missing validation, baked-in optimism
  Risks:
* Later refusal becomes impossible
  Categories: Coding Judgment
  Boundaries: code merge, runtime activation

#### 8. Persistent Context & Judgment Drift (Agent‑Facing)

Breaks:

* Memory treated as permission, past judgment reused blindly
  Risks:
* Silent boundary drift, reuse without re-approval
  Categories: Refusal, Config / Change, Mixed
  Boundaries: autonomous progression, reuse without fresh authority

> ⚠️ This surface is **opt-in** and applies only to agent-facing exemplars.
> It does not alter core structure, only mutation and validation.

---

### 8.4 Coverage Rules (Non‑Negotiable)

* Every exemplar **must** map to at least one stress surface
* Phase-1 focuses on **signal integrity** and **authority boundaries**
* Phase-2 must explicitly mark **irreversible edges**
* Agent-facing exemplars must declare **context lifetime constraints**
* Later phases **compose** these surfaces; they do not introduce new ones

> ❌ If a proposed exemplar does not trace cleanly to a stress surface → reject it. There are no free-floating scenarios.

---

## 10. Category Distribution & Coverage Mapping (Canonical)

This section makes the **coverage chain explicit and auditable**:

> **Stress Surface → Judgment Category → Base Exemplars → Variants**

This mapping guarantees:

* No stress surface is underrepresented
* Categories are tied to failure modes, not abstract topics
* Variants scale *judgment density*, not *judgment scope*

---

### 9.1 Canonical Category Distribution (35 Exemplars)

| Category          | Count | Primary Judgment         |
| ----------------- | ----- | ------------------------ |
| RCA               | 6     | Hypothesis elimination   |
| Anomaly           | 6     | Signal skepticism        |
| Config / Change   | 6     | Risk-aware modification  |
| Refusal / Safety  | 6     | Authority-aware stopping |
| Design & Planning | 6     | Trade-off reasoning      |
| Coding Judgment   | 7     | Restraint in code        |
| Mixed / Ugly      | 4     | Compositional judgment   |

> 🧭 These targets are schema-enforced. Deviations must be justified by corpus-level review.

### Corpus Layers (Governance vs ML Compilation)

The Golden Exemplars program may maintain **multiple corpora** at once:

1. **Governance Corpus (Constitutional Layer)** — abstract exemplars under GREG ratification (for example, REF‑01, DES‑01, MIX‑04, CODE‑08). This layer encodes constitutional semantics and review discipline.
2. **ML Compilation Corpus (Product-Specific Layer)** — concrete, system-grounded exemplars for a particular product pipeline (for example, the Motadata corpus with 17 base exemplars and 68 variants across REF/CONF/DES/MIX/CODE).

These corpora **may differ** in size and phase distribution. Only **compilation corpora** are eligible to enter SFT.

Phase distribution and exemplar counts **must be declared per corpus**. Future readers must not assume that a canonical governance count (e.g., 35 design-era exemplars) is identical to any given SFT dataset.

---

### 9.2 Stress Surface → Category Mapping

Each stress surface must feed **at least one primary category**. Coverage is corpus-wide.

| Stress Surface                     | Primary Categories                |
| ---------------------------------- | --------------------------------- |
| Signal & Evidence Integrity        | RCA, Anomaly                      |
| Baselines, History & Assumptions   | Anomaly, Design                   |
| Change Introduction & Blast Radius | Config / Change, Mixed            |
| Authority, Ownership & Legitimacy  | Refusal / Safety, Config / Change |
| Time Pressure & External Deadlines | Design, Mixed                     |
| Compositional Failure              | Mixed / Ugly                      |
| Implementation as Irreversibility  | Coding Judgment                   |

> ⚠️ Surfaces must map to **at least one** Phase-1–4 category. If they don't, corpus is incomplete.

---

### 9.3 Category → Base Exemplar Mapping (Illustrative)

Each category is instantiated via **LOCKED base exemplars**.

| Category         | Base Exemplars (examples) |
| ---------------- | ------------------------- |
| RCA              | RCA‑01, RCA‑02, RCA‑03    |
| Anomaly          | ANOM‑01, ANOM‑02, ANOM‑03 |
| Config / Change  | CONF‑01, CONF‑02, CONF‑03 |
| Refusal / Safety | REF‑01, REF‑02, REF‑03    |
| Design           | DES‑01, DES‑02, DES‑03    |
| Coding Judgment  | CODE‑01, CODE‑02, CODE‑03 |
| Mixed / Ugly     | MIX‑01, MIX‑02            |

> 🔒 Base exemplars are the **only place** new judgment may be authored. Variants follow.

---

### 9.4 Exemplar → Variant Expansion

LOCKED exemplars may generate **multiple variants**, with strict inheritance:

* ✅ Same stress surface(s)
* ✅ Same category
* ✅ Same irreversible boundary

**Example:**

```
Stress Surface: Change Introduction & Blast Radius
        ↓
Category: Config / Change
        ↓
Base Exemplar: CONF‑01 (merge irreversibility)
        ↓
Variants:
  - Paraphrase variant
  - Re-grounded (PR → ADR)
  - Intensified (deadline pressure)
  - Relaxed (lower urgency)
```

> 🔁 Variants increase robustness and surface familiarity — never judgment scope.

---

### 9.5 Coverage Validation Rule

The corpus is **coverage-complete** only when:

* All stress surfaces are represented across categories
* Each category has **≥1 LOCKED base exemplar per relevant phase**
* Variants exist **only after** base exemplars are structurally locked

> ❌ If a stress surface or category cannot be traced across this pipeline, coverage is incomplete.
> ✅ This structure enables **dataset traceability and judgment auditability.**

## 11. Quality Gates & Review Checklist

This checklist validates **artifact hygiene**, not correctness of judgment.
It exists to eliminate structural debt before exemplars lock.

> 🧼 **Top → bottom. No skipping. No batching.** If anything fails, fix it immediately.

---

### 1️⃣ Visual Noise Check (≈10 seconds)

Scan for surface contamination:

* ( ) = commentary? Remove.
* `*`, `\`, stray quotes = markdown leaks? Remove.
* Repeated posture lines or headings? Collapse.
* Bold/italic used for emotion? Replace with control language.

> ✅ If it explains, soften, or editorializes — it’s invalid.

---

### 2️⃣ Boundary Singularity Check (≈5 seconds)

Ask:

> **Is there exactly one irreversible boundary, named identically across all sections?**

Check for exact match in:

* Situation Type
* Response Posture
* Reasoning (Step 1)
* Output (Blocked Action)
* D.N.A Decomposition

> ❌ No aliases, no synonyms, no secondary blockers.
> ✅ One boundary. One phrase. Everywhere.

---

### 3️⃣ Output Closure Check (≈5 seconds)

Inspect the Output block:

* ✅ One section only

* ✅ Contains only:
  
  1. Approved pre-boundary actions
  2. Explicitly blocked action
  3. Re-evaluation conditions (non-promissory)

* ✅ Ends with: "The current state is complete and safe indefinitely."

> Output must **close the judgment** — not defer or extend it.

---

### 4️⃣ Negative Capability Litmus Test (≈5 seconds)

Read aloud:

> “If we stop here forever and do nothing else, is the system safe?”

* ✅ If yes, Output is valid.
* ❌ If no, revise Output or Reasoning. Immediately. No discussion.

> Negative Capability = refusal with zero safety debt.

---

### 5️⃣ D.N.A Shape Check (≈5 seconds)

Check that D.N.A block contains all three, clearly labeled:

* ✓ **Decomposition** — ≥4 invariant reasoning blocks
* ✓ **Negative Capability** — stable terminal state
* ✓ **Adversarial Swap** — mutation without boundary collapse

> Retain header: `## D.N.A Validation (POST‑DRAFT)`

---

## 🚫 Instant Fail Conditions (No Exceptions)

Do **not** lock if exemplar contains:

* "pilot", "partial rollout", "scoped enablement"
* Boundary based on runtime signal or downstream detection
* Output phrased as **“when”**, not **“if”**
* Justifications (“because”, “we believe”, “this might”) in any section
* Side comments (“just to clarify”, “note that…”)

> These are signs of execution bias — not judgment.

---

## ✅ Lock Signal

You may LOCK the exemplar when:

* It feels **boring** (no emotion, no narrative)
* There is nothing left to explain or soften
* No reviewer objection comes to mind
* Rereading prompts **zero edits**

> ✅ This is not apathy. This is judgment compression.

---

### Final Meta‑Note: Language as Control Surface

This checklist is not about polish. It is about **control-plane grammar**.

You're writing like an engineer approving a boundary — not a helpdesk agent.

> Single edit rule:
> 
> * If a sentence can be answered with “why?” → it’s too soft
> * If it can be answered with “can we violate this?” → it’s control-valid

**Control Vocabulary**:

* irreversible boundary
* authority‑bounded
* non‑unilateral rollback
* responsibility opacity
* stable terminal state
* execution authority withheld
* coordination debt

🧠 **15‑Second Edit Trick**:

* Delete: "because", "might", "appears"
* Delete all justifications
* Restate as a fact

Repeat until boring. Then lock.

---

## 12. How to Review (Engineering Lens)

This section defines how to review exemplars as **engineering control decisions**, not operational actions.

Golden exemplars must read like:

* A senior engineer in a design or code review
* An RFC response granting or denying execution authority
* A decision that halts action unless explicitly approved

Golden exemplars must **not** sound like:

* Live incident playbooks
* Post-merge remediation steps
* Operational triage or watchtower notes

> 📌 Phase-04 reviews prioritize **dominance and refusal correctness**, not solution quality.

---

### 11.1 Language Translation: Ops → Engineering

Translate operational phrasing into **pre-execution control language**.

**Examples:**

* ❌ "Do not suppress alerts yet"
  → ✅ "This change is not approved"

* ❌ "Hold off on the rollout"
  → ✅ "This change should not be merged"

* ❌ "Monitor before acting"
  → ✅ "Evidence is insufficient to justify crossing the boundary"

* ❌ "Wait for more signals"
  → ✅ "Current state is stable and non-progressing by default"

* ❌ "Don’t mitigate automatically"
  → ✅ "Autonomous action is not permitted"

> Refusal must sound like a **decision not to act**, not a suggestion to wait.

---

### 11.2 What Reviewers Must Evaluate

Review as if you're co-signing a boundary approval.

Ask:

* Would I trust this reasoning in a high-stakes design review?
* Does it name and enforce an irreversible boundary?
* Does it honor authority and ownership scope?
* Does the Output stop action, clearly and indefinitely?

> ❌ If it reads like "how to keep things running," it has failed.
> ✅ If it reads like "what cannot proceed yet," it passes.

---

### 11.3 Common Review Errors (Engineering Context)

Flag immediately if the exemplar:

* Describes **ops steps** instead of **pre-execution judgment**
* Suggests deferring to runtime actions (e.g. "monitor", "suppress")
* Frames refusal as temporary caution or soft pause
* Uses execution verbs: restart, mitigate, roll out

Replace with control-plane equivalents:

* approve / block
* accept / reject
* legitimate / illegitimate
* proceed / stop

> The goal is to prevent irreversible harm — not to debug.

---

### 11.4 Final Review Questions

Before locking, ask:

* Is this written like a pre-execution control decision?
* Is the irreversible boundary **explicit, consistent, and enforced**?
* If this response is the **last action taken**, is the system still safe?

✅ If all three answers are **yes**, the review is complete.
❌ If not, do not lock. Refuse and send it back upstream.

> Judgment must contain itself. Nothing should leak downstream without decision integrity.

---

## 13. Variants & Scaling Strategy

This section defines **how scale is achieved without diluting judgment**.

Golden exemplars are **roots**. Variants are controlled branches that reinforce the original posture, not reinterpret it.

> ⚠️ Scaling is horizontal (breadth), not vertical (depth). No variant may introduce new capability.

---

### 12.1 What Variants Are (and Are Not)

**Variants ARE**:

* Controlled transformations of a **LOCKED** exemplar
* Used to expand training **coverage**, not introduce new reasoning
* Validated independently via **POST-DRAFT D.N.A**

**Variants are NOT**:

* New exemplars
* Looser rewrites or simplifications
* Shortcuts for dataset expansion
* Auto-generated or reviewed casually

> ❌ If a variant introduces new judgment → it is not a variant. It must re-enter Phase-1 as a new exemplar.

---

### 12.2 Canonical Variant Dimensions

Mutate **only one dimension at a time**. Compositional drift is not allowed.

#### A. Paraphrase (Linguistic Only)

* Reword instruction, input, and reasoning without altering meaning
* Structure, boundary, and posture must be intact
* No tone shift or confidence leak

> ❌ Failure mode: paraphrase implies greater certainty or optimism

---

#### B. Re-grounding (Surface Shift)

* Swap engineering artifact (e.g. test failure → PR diff)
* Ambiguity, constraints, and boundary remain unchanged

> 🎯 Goal: train exemplar portability across documentation surfaces

---

#### C. Intensification (Pressure Increase)

* Add urgency, stakeholder pressure, or business tension
* Do not add factual signals
* Output should remain unchanged or become more cautious

> ✅ Used to pressure-test posture stability

---

#### D. Relaxation (Pressure Decrease)

* Soften pressure context (deadline relaxed, lower impact)
* Boundary must remain **fully enforced**

> ❌ Failure mode: output relaxes and permits unsafe progress

---

### 12.3 Variant Validation Rules (Hard Gates)

Each variant must:

* Inherit **all 7 Essential Fields** from base exemplar
* Preserve **same irreversible boundary**
* Pass **POST-DRAFT D.N.A** independently
* Pass full **Section-11 hygiene checklist**

❌ Variants may NOT:

* Change posture (e.g., defer → approve)
* Modify or rename the boundary
* Resolve the core ambiguity
* Expand execution logic

> Variants reinforce containment. They never converge on action.

---

### 12.4 Scaling Order (Non-Negotiable)

Variants must be generated **in strict order** after base lock:

1. ✅ Paraphrase (linguistic diversity)
2. ✅ Re-grounded (artifact portability)
3. ✅ Intensified (pressure testing)
4. ✅ Relaxed (judgment preservation under leniency)

> 🔁 Skipping or merging steps introduces **silent semantic drift**.

---

### 12.5 When to Stop Scaling

Variant generation ends when:

* Variants feel repetitive (no semantic novelty)
* No new failure modes emerge under pressure
* Reviewers cannot find new objections

> 📉 Beyond this point, more variants create noise, not judgment.

---

### 12.6 Common Variant Failure Modes

Immediate rejection if variant:

* Feels more confident than base
* Weakens refusal or deferral language
* Adds procedural steps (monitoring, escalation, rollout)
* Implies implicit permission or boundary relaxation

> ❌ Variants that blur restraint = structural failure
> ✅ Variants that feel redundant = stability confirmed

---

## 14. From Exemplars to SFT Dataset

This section explains **how judgment artifacts move from human-authored exemplars to a training-grade SFT dataset**, without leaking execution bias or diluting behavioral DNA.

The pipeline is intentionally **staged**, not end-to-end automated.

Judgment must be *earned* before it is *scaled*.

---

### 13.1 The Three-Stage Training Pipeline

Golden exemplar programs progress through **three explicit maturity stages**:

```
Manual (Judgment Creation)
        ↓
Semi-Automated (Judgment Expansion)
        ↓
Automated (Judgment Consumption)
```

Each stage has **different safety properties**, **different failure modes**, and **different governance rules**.

---

### 13.2 Stage 1 — Manual: Golden Exemplars (Authoritative Source)

**Purpose**: Create *new judgment*.

Characteristics:

* Authored entirely by humans
* Uses B.R.A.I.N for creation
* Uses D.N.A for validation and locking
* Encodes irreversible boundaries, refusal semantics, and negative capability

Rules:

* No automation
* No generators
* No bulk creation

Golden exemplars are the **only place** where *new judgment is introduced* into the system.

They are **roots**, not data points.

---

### 13.3 Stage 2 — Semi-Automated: Variant Expansion

**Purpose**: Expand coverage *without introducing new judgment*.

Characteristics:

* Variants are derived only from **LOCKED** exemplars
* Mutation dimensions are constrained (Section-13)
* Human review remains mandatory

What may be semi-automated:

* Linguistic paraphrasing
* Artifact re-grounding suggestions
* Pressure intensification proposals

What may **not** be automated:

* Boundary selection
* Response posture changes
* Resolution of ambiguity

Rules:

* One mutation dimension per variant
* Each variant passes POST-DRAFT D.N.A
* Variants inherit all essential fields

Semi-automation accelerates *breadth*, not *depth*.

---

### 13.4 Stage 3 — Automated: SFT Dataset Construction

**Purpose**: Convert validated judgment artifacts into model-consumable training data.

Characteristics:

* Deterministic conversion (e.g., JSONL)
* No semantic rewriting
* No reasoning augmentation

Automation is allowed **only here**, because judgment has already been frozen upstream.

Rules:

* Only **LOCKED** exemplars and variants may enter the dataset
* Dataset assembly must be reproducible
* Provenance (exemplar → variant → dataset row) must be traceable

Automation here is *mechanical*, not cognitive.

---

### 13.5 What This Pipeline Explicitly Prevents

This staged approach prevents:

* Scaling before judgment is stable
* Training on fluent but unsafe behavior
* Boundary drift during dataset assembly
* Hallucinated authority entering fine-tuning

Any pipeline that attempts to skip stages will amplify failure modes instead of learning.

---

### 13.6 When the Dataset Is "Ready"

An SFT dataset is considered **training-grade** only when:

* All base exemplars are LOCKED
* Variants show stability under adversarial mutation
* Refusal and deferral rates remain stable across variants
* No exemplar relies on downstream execution

Dataset readiness is a **judgment property**, not a size metric.

### 13.7 Deterministic Dataset Compilation (Canonical Rule)

Dataset assembly must satisfy **all** of the following canonical rules:

* Exactly **one canonical irreversible boundary** per base exemplar.
* **Boundary phrase equality** between Phase‑3 and all Phase‑4 variants (strict string equality after normalization).
* Exactly **4 variants per base** (unless a corpus revision is explicitly declared and documented).
* No synthetic input prefixing or output synthesis during extraction.
* **Response Posture** text is extracted verbatim from the exemplar/variant.
* No multi-block boundary merging (one boundary block per exemplar).
* JSONL generation must be **deterministic** (seeded split; source commit hash logged in metadata).

Dataset artifacts must be versioned and tagged **at freeze**. Any violation of these rules must **abort** dataset compilation until corrected.

---

## 15. Chronology & Phase Plan (35 Exemplars)

**Foundational Principle**: *Judgment precedes code. Refusal precedes automation. Reasoning precedes execution.*

Exemplars are authored, reviewed, and **LOCKED sequentially**. A phase may not advance unless all exemplars in the current phase pass D.N.A validation.

Phases are sequenced by **irreversibility class**, not by use case or workflow order.

---

### Phase‑1 — Foundations: Signal Skepticism & Judgment Basics (5)

**Goal**: Train early refusal, ambiguity recognition, and judgment restraint **before** progress is permitted.

**Focus:**

* Hypothesis discipline
* Ambiguity containment
* Early stopping over speculation

**Exemplars:**

* **RCA‑01** — Bug root cause with misleading symptoms
* **RCA‑02** — Failure caused by assumption mismatch (code vs design)
* **ANOM‑01** — Flaky or non‑deterministic test behavior
* **ANOM‑02** — Performance regression misclassified as correctness bug
* **REF‑01** — Refusal due to insufficient evidence

**Pass Condition:**

* Stable refusal posture
* No action bias under uncertainty
* Explicit halt when signals are incomplete

> Phase‑1 teaches when **judgment must stop** — regardless of pressure.

---

### Phase‑2 — Change & Constraints: Safe Progression under Uncertainty (6)

**Goal**: Encode irreversible boundaries and refusal logic **when authority exists but rollback is unclear**.

**Boundary Test (CONF):**

> *If this action goes wrong, can I still roll it back unilaterally and completely?*
> If **no**, an irreversible boundary is crossed.

**Exemplars:**

* **CONF‑01** — Refactor request with unclear blast radius (merge risk)
* **CONF‑02** — API change with unknown downstream consumers (autonomy risk)
* **CONF‑03** — Configuration change conflicting with repo ownership (contract exposure)
* **CONF‑04** — Change requested under deadline pressure (implicit expansion)
* **CONF‑05** — Multi‑stakeholder change with partial approvals (loss of rollback control)
* **REF‑02** — Refusal due to missing authority or ownership

**Pass Condition:**

* Clean REF/CONF separation
* Decisions close with safe terminal state
* No gated execution paths permitted

---

### Phase‑3 — Design & Planning: Thinking Before Building (6)

**Goal**: Train trade‑off reasoning, deferral discipline, and rollback-aware design posture.

**Focus:**

* Assumption tracking
* Rollback observability
* Ambiguity-respecting deferral

**Exemplars:**

* **DES‑01** — Greenfield design with unclear scale assumptions
* **DES‑02** — Incremental enhancement vs rewrite decision
* **DES‑03** — Migration design with rollback uncertainty
* **DES‑04** — Performance‑critical design with weak evidence
* **DES‑05** — Design under conflicting requirements
* **REF‑03** — Refusal to finalize design due to unresolved trade‑offs

**Pass Condition:**

* Output permits deferral as full completion
* Judgment does not default to solutioning

---

### Phase‑4 — Collision Judgment (MIX) (3)

**Status:** Canonical and complete
**Role:** Resolve judgment collisions when REF, CONF, and DES interact

> Phase-4 validates **correct collapse of previously valid judgments** under simultaneous pressure.

**Eligibility Criteria:**

* At least **two** judgment pressures (REF, CONF, DES) are simultaneously active
* Each pressure is independently valid
* Resolving one does **not dissolve** the others

**Dominance Order:**

1. REF (Legitimacy)
2. CONF (Irreversibility)
3. DES (Design Tradeoff)

**Allowed Terminal Postures:**

* Refusal — legitimacy fails
* Deferral — irreversibility cannot be justified
* Bounding — limited, non-committal action allowed

**Canonical Exemplars:**

* **MIX‑01** — REF + CONF → Refusal
* **MIX‑02** — CONF + DES → Deferral
* **MIX‑03** — REF + DES (CONF latent) → Bounding

> No other Phase‑4 combinations permitted under schema v1.0

**Pass Condition:**

* Terminal state is containment — not decision

---

### Phase‑5 — Coding with Judgment: Safe Implementation (8)

**Goal**: Ensure implementation reflects restraint and encodes refusal where required.

**Focus:**

* Guardrails before logic
* Defaults that fail safe
* Explicit refusal encoded in code

**Exemplars:**

* **CODE‑01** — Implement fix with explicit assumption documentation
* **CODE‑02** — Code change that must fail safely
* **CODE‑03** — Introducing validation and guardrails
* **CODE‑04** — Staged refactor with incremental rollout
* **CODE‑05** — Safe defaults and feature flags
* **CODE‑06** — Refusal‑in‑code (hard stop on unsafe state)
* **CODE‑07** — Observability and audit hooks
* **REF‑05** — Refusal to generate code without required context

**Pass Condition:**

* Code must embody constraint-first logic
* Execution paths default to denial without verified inputs

---

### Phase‑6 — Advanced / Optional Depth (4)

**Goal**: Capture judgment at sustained scale, coordination depth, or irreversible horizon.

**Note**: Phase-5 encodes judgment. Phase-6 tests whether judgment survives time, scale, and pressure.

**Exemplars:**

* **DES‑06** — Long‑term design decision with irreversible cost
* **CONF‑06** — Multi‑repo / multi‑team coordination
* **MIX‑06** — Sustained pressure causing decision quality decay
* **CODE‑08** — Adaptive behavior with explicit safety bounds

**Entry Condition:**

* All prior phases are locked and mutation-stable

### Collapse Vector Detection (Mandatory for Mutation Harness)

Phase‑6 mutation harnesses must explicitly track and report **collapse vectors**, including:

* CONF → DES collapse (conditional allowance drifting into design-only reasoning).
* DES → recommendation upgrade (design reasoning drifting into prescriptive advice).
* MIX → single-pressure CONF collapse (collision resolving into a single-pressure allowance).
* REF → conditional softening (absolute refusal eroding into bounded allowance).
* CODE → abstract reasoning drift (implementation guards drifting into conceptual advice).
* Boundary relocation or aliasing (irreversible boundary moved, merged, or renamed in practice).

The mutation ledger must record, for each vector, **whether collapse was prevented**. A Phase‑6 harness is incomplete unless collapse vector detection and reporting are part of its core contract.

---



### Comprehensive Exemplar Summary

> **Note on terminal posture**
> Terminal posture describes the *only stable, correct end state* once the exemplar’s judgment is fully applied. It is not an execution outcome; it is a governance outcome.

| Phase | ID      | Title                                           | Type    | Terminal Posture  |
| ----- | ------- | ----------------------------------------------- | ------- | ----------------- |
| P1    | RCA-01  | Bug root cause with misleading symptoms         | RCA     | Refusal           |
| P1    | RCA-02  | Failure from assumption mismatch                | RCA     | Refusal           |
| P1    | ANOM-01 | Flaky test behavior                             | Anomaly | Refusal           |
| P1    | ANOM-02 | Misclassified performance regression            | Anomaly | Refusal           |
| P1    | REF-01  | Refusal due to insufficient evidence            | Refusal | Refusal           |
| P2    | CONF-01 | Refactor with unclear blast radius              | Config  | Conditional Block |
| P2    | CONF-02 | API change with unknown consumers               | Config  | Conditional Block |
| P2    | CONF-03 | Ownership-conflicting config change             | Config  | Conditional Block |
| P2    | CONF-04 | Change requested under deadline pressure        | Config  | Conditional Block |
| P2    | CONF-05 | Multi-stakeholder change with partial approvals | Config  | Conditional Block |
| P2    | REF-02  | Refusal due to missing ownership                | Refusal | Refusal           |
| P3    | DES-01  | Greenfield with unclear scale assumptions       | Design  | Deferral          |
| P3    | DES-02  | Enhancement vs rewrite decision                 | Design  | Deferral          |
| P3    | DES-03  | Migration with rollback uncertainty             | Design  | Deferral          |
| P3    | DES-04  | Performance-critical design with weak signal    | Design  | Deferral          |
| P3    | DES-05  | Conflicting design requirements                 | Design  | Deferral          |
| P4    | MIX-01  | REF + CONF → Refusal                            | Mixed   | Refusal           |
| P4    | MIX-02  | CONF + DES → Deferral                           | Mixed   | Deferral          |
| P4    | MIX-03  | REF + DES (CONF latent) → Bounding              | Mixed   | Bounding          |
| P5    | CODE-01 | Execution authority & guarded execution         | Coding  | Safe Execution    |
| P5    | CODE-02 | Ownership legitimacy refusal                    | Coding  | Refusal           |
| P5    | CODE-03 | Safe defaults in anomaly correlation logic      | Coding  | Safe Execution    |
| P5    | CODE-04 | Approval-gated configuration rollout            | Coding  | Safe Execution    |
| P5    | CODE-05 | Human-in-the-loop enforcement in automation     | Coding  | Safe Execution    |
| P5    | CODE-06 | Audit-first behavior under uncertainty          | Coding  | Refusal           |
| P5    | CODE-07 | Cross-tenant / cross-service containment        | Coding  | Refusal           |
| P5    | CODE-08 | Stale context refusal                           | Coding  | Refusal           |
| P6    | DES-06  | Long-term irreversible design decision          | Design  | Deferral          |
| P6    | CONF-06 | Cross-repo / cross-team irreversible change     | Config  | Conditional Block |
| P6    | MIX-06  | Judgment decay under sustained pressure         | Mixed   | Refusal           |

---

## Terminal Posture Rationale (Annotated)

### Phase-01 (REF / RCA / ANOM)

* **Refusal** — Evidence is insufficient, misleading, or epistemically unsafe. Acting would encode false certainty. Stability requires non-action.

### Phase-02 (CONF)

* **Conditional Block** — Action may become legitimate, but only after missing constraints (ownership, blast radius, approvals) are resolved. Default is blocked, not refused.

### Phase-03 (DES)

* **Deferral** — The system must postpone commitment until design uncertainty collapses. Premature choice creates irreversible architectural debt.

### Phase-04 (MIX)

* **Refusal** — Conflicting judgments resolve to an irreversible boundary that cannot be crossed safely.
* **Deferral** — Judgment synthesis indicates future legitimacy is possible but not present.
* **Bounding** — Action is permitted only within explicitly constrained limits to avoid irreversible harm.

### Phase-05 (CODE)

* **Safe Execution** — Execution is permitted *only because* irreversible boundaries are fully guarded and refusal remains dominant if conditions break.
* **Refusal** — Structural conditions (authority, ownership, freshness, scope, auditability) are violated; execution must be impossible.

### Phase-06 (ADV)

* **Deferral** — Judgment must hold over time; commitment is postponed to observe endurance under sustained pressure.
* **Conditional Block** — Multi-actor or cross-repo coordination may unlock legitimacy, but never by default.
* **Refusal** — Judgment decay under pressure is detected; normalization of violation must be prevented.

---

## Explicit Gap Acknowledgement

* **REF-03** is intentionally **not authored yet**.
* Any prior references to REF-03 should be treated as placeholders, not canonical exemplars.
* If REF-03 is introduced later, it must re-enter **Phase-01 (REF)** and may impact downstream MIX exemplars.

---

## Appendix A: Bad Exemplar Analysis

These failure patterns indicate a structurally invalid exemplar. Do not lock — restart from Essential Fields.

**Reject immediately if the exemplar:**

* Acts without clearly declared authority or boundary
* Refuses ambiguously or with implied conditions
* Allows execution "under monitoring" or gated rollout
* Responds with confidence under unresolved ambiguity
* Shows execution bias: partial rollout, scoped enablement, test in prod
* Hides or renames irreversible boundaries

> ⚠️ Fluency is not fidelity. Action bias under uncertainty is a control failure.

---

## Appendix B: Common Reviewer Failure Modes

Reviewers are the final safety layer. These are the most frequent structural errors during review:

* ✅ Approving output that defers judgment to runtime
* ✅ Accepting exemplars that have multiple or alias boundaries
* ✅ Penalizing refusal or deferral for being “unhelpful”
* ✅ Confusing narrative clarity for judgment clarity
* ✅ Suggesting edits that weaken refusal posture ("make it more constructive")

**Use reviewer control language:**

* approve / block
* accept / reject
* proceed / stop
* legitimate / illegitimate

> 📌 If the Output cannot stand unchanged under pressure, the exemplar is not safe.

---

## Appendix C: Author Enforcement Checklist

This appendix compresses the full judgment authoring lifecycle into an **executable control checklist**.

Use this as a **hard-gated checklist** for authors and reviewers. No exemplar may proceed unless every item is satisfied.

### C.1 Authoring Lifecycle Gates

#### ✅ Before Drafting (Locking Gates)

* [ ] Declare lifecycle surface (Design / Review / Coding / Planning / Migration)
* [ ] Declare and lock all **7 Essential Fields**
* [ ] Declare **Five-Layer Judgment Stack**
* [ ] Name exactly **one irreversible boundary**
* [ ] Confirm boundary = loss of unilateral rollback (not first sign of failure)
* [ ] Run **Pre-check D.N.A** (mandatory for Phase‑2+)
* [ ] Validate **clean REF vs CONF** legitimacy state

#### ✍️ During Drafting (Structural Discipline)

* [ ] Use the **canonical template**, in order
* [ ] Write reasoning as falsifiable hypotheses — not narrative
* [ ] Reject at least one plausible-but-wrong path
* [ ] Surface uncertainty explicitly (no smoothing)
* [ ] Stop reasoning when evidence or authority ends

#### 🔒 Before Locking (Validation Gates)

* [ ] Run **POST-DRAFT D.N.A** (Decomposition, Negative Capability, Adversarial Swap)
* [ ] List ≥4 reusable decision invariants
* [ ] Verify stable terminal state (Negative Capability)
* [ ] Execute one adversarial mutation and re-validate D.N.A
* [ ] Pass full Section-11 hygiene review
* [ ] Confirm Output **closes the decision** (no gated execution)

> ❌ If **any** box is unchecked, restart from Essential Fields. No lock.

---

### C.2 Micro‑Example (CONF‑01 Pattern)

* **Boundary**: merge to main
* **Approved**: analysis, diff review, test gap identification
* **Blocked**: merge to main branch
* **Terminal state**: current state is complete and safe indefinitely

> ✅ If this feels boring, it’s correct.

## Appendix D: LLM-Based Audit Flows

This appendix defines how to use LLMs as **judgment auditors** — not validators, not authors.

LLMs may be used to flag risks, surface drift, or recheck hygiene **only after artifacts are locked by humans**.

---

### D.1 Purpose of LLM Auditing

Used correctly, LLMs act as a **post-lock reflection layer**:

* Surface silent tone drift
* Catch confidence inflation in paraphrases
* Identify hygiene regressions (e.g., passive refusals, softened boundaries)
* Highlight reasoning sections with unverifiable claims

> LLMs cannot approve, modify, or justify exemplars.
> Their only role is **surfacing anomalies** for human review.

---

### D.2 What LLMs May Audit

LLM audits apply to:

* Locked **base exemplars** (Phase‑1 through Phase‑6)
* All **variants** (paraphrased, re-grounded, intensified, relaxed)
* Full **exemplar body** or individual sections
* Reviewer comments and hygiene checklist application

---

### D.3 Rules of Use

* ✅ Audit output must be reviewed by a human
* ✅ Findings must map to explicit checklist or boundary violations
* ❌ LLMs must never rewrite, approve, or soften refusal logic

---

## Appendix E: DPO Usage Policy (Preference Tightening Only)

**Direct Preference Optimization (DPO) is explicitly downstream and optional.**

DPO may be applied **only after**:

* All Phases 1–5 exemplars are LOCKED
* Judgment behavior is mutation-stable
* Refusal and boundary correctness are already reliable via SFT

**DPO is not permitted to create, discover, or correct judgment.** Its sole purpose is to **compress preference within already-correct behavior**.

Permitted use:

* Improve clarity, conciseness, and compositional cleanliness
* Reduce stylistic variance between equally safe responses

Forbidden use:

* Teaching when to refuse vs proceed
* Modifying irreversible boundaries
* Optimizing for "helpfulness" under ambiguity

> **Invariant:** SFT encodes judgment. DPO may only refine expression inside frozen judgment.

---

## Appendix F: DPO Safety Checklist (Hard Gates)

This checklist must be satisfied **before any DPO run** is approved.

### F.1 Dataset Construction Rules

* [ ] Both preference candidates are **safe**
* [ ] Both enforce the **same irreversible boundary**
* [ ] Both terminate in a stable state
* [ ] Difference is **expression only**, not behavior

### F.2 Explicit Prohibitions

* [ ] No refusal vs conditional-progress pairs
* [ ] No boundary relaxation in preferred samples
* [ ] No preference for speed, optimism, or action

### F.3 Review & Rollback

* [ ] Human review of preference pairs completed
* [ ] Post-DPO mutation testing scheduled
* [ ] Rollback path defined if refusal rates degrade

> ❌ If any item fails, DPO must not be run.
> ✅ DPO is reversible; judgment corruption is not.

---

## Appendix G: Chat-Native Continuity Protocol

When operating inside **stateless conversational environments** (for example, ChatGPT or API-based sessions), no session may assume prior memory. Each session must begin by explicitly rehydrating:

1. **Constitutional Kernel** — phase doctrine, dominance hierarchy, structural invariants, and locked constraints.
2. **Project Snapshot** — current corpus counts and phase distribution (for each active corpus), drift status, and lock state.
3. **Session Objective** — explicit scope constraint (what this session is allowed to do, and what is out of scope).

Failure to re-establish these elements at session start reintroduces semantic drift and weakens constitutional guarantees. Session macros (such as a “Project State Ledger” header) are the canonical mechanism for this continuity.


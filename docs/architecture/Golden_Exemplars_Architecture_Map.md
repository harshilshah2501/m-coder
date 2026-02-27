## Golden Exemplars System Architecture Map

This document is a **conceptual map** of the Golden Exemplars system.
It explains how judgment is defined, taught, enforced, and proven across:

- 4 judgment layers
- 6 phases
- 29 exemplars (GREG locked, Phases 01–05; Phase-06 hardening excluded; see `governance/golden-exemplars/GREG/GREG-Initiation-Ratification-v0.9.md`)
- 7 architectural stress surfaces
- Execution surfaces (where behavior happens)
- Validation ledgers
- GREG (Governance, Runtime Evidence & Guardrails)

It does **not** redefine any exemplar, schema, or phase. The constitutional sources of truth remain:

- Golden Exemplars Guide v1.5 (judgment semantics and exemplars)
- Phase definitions and schemas
- Phase‑06 reachability and validation artifacts

This map is meant to be the **mental model** for how those pieces fit together.

---

## Design Principles

These non‑negotiable principles govern the entire system:

- **Refusal dominance**: Under uncertainty, illegitimacy, or missing authority, *refusal* is preferred over progress.
- **Bounded allowance**: When progress is allowed, it is explicitly **bounded** by a named irreversible boundary.
- **Safe defaults in code**: Implementations (Phase‑05) must default to refusal or no‑op when in doubt.
- **Structural proof before closure**: No phase, dataset, or version is considered “closed” until structural validations and ledgers support it.
- **Governance cannot be bypassed by runtime**: Runtime and ML may *enforce* or *demonstrate* judgment, but they never redefine it. Only constitutional artifacts change judgment.

Everything else in this document is in service of these principles.

---

## 1. The 4 Judgment Layers

The Golden Exemplars system is organized into four conceptual layers.

### 1.1 Constitution (Judgment Law)

**What it does**

- Defines what judgment *is*:
  - Phase semantics (REF, CONF, DES, MIX, CODE, REACHABILITY).
  - Exemplar texts and their terminal postures (refusal, conditional block, deferral, bounding, safe execution).
  - Hard boundaries, authority rules, escalation paths.

**Key questions**

- When must the assistant refuse?
- When may it proceed, and under what explicit constraints?
- How do we know an exemplar is structurally valid?

### 1.2 Compilation (Judgment Encoding)

**What it does**

- Encodes constitutional judgment into artifacts that models can learn from:
  - Exemplars and **variants** (strictly post‑judgment, no new judgment).
  - SFT dataset rows with metadata (phase, surface, category, boundary).
  - Validation harnesses that check coverage and enforcement properties.

**Key questions**

- How do we turn a small number of high‑judgment exemplars into a usable dataset?
- How do we ensure variants inherit judgment, instead of mutating it?

### 1.3 Execution (Judgment Realization)

**What it does**

- Realizes judgment as behavior in systems:
  - Serving stack and models.
  - Orchestrators, agents, and tools that can change code, configs, or systems.
  - Policy hooks that enforce Phase‑05 CODE constraints (safe defaults, ownership checks, human‑in‑the‑loop).

**Key warning**

Even with perfect exemplars and training, **execution surfaces can still violate judgment** if enforcement is weak.

- Exemplars encode judgment.
- Compilation teaches it.
- Execution *must* implement it — or we have governance drift.

### 1.4 Observation (Judgment Proof & Drift Detection)

**What it does**

- Observes and proves whether execution still matches constitutional judgment:
  - Validation ledgers.
  - Phase‑06 reachability and stress‑surface coverage.
  - Runtime metrics, traces, and audit logs.

**GREG lives here as an actor**:

- GREG reads observations and decides whether:
  - The constitution is being followed (PASS).
  - Specific exemplars or enforcement points must be revised (FAIL).

### 1.5 Layer diagram

```mermaid
flowchart TB
  constitution[Constitution\n(Judgment Law)] --> compilation[Compilation\n(Judgment Encoding)]
  compilation --> execution[Execution\n(Judgment Realization)]
  execution --> observation[Observation\n(Proof & Drift Detection)]
  observation --> constitution
```

### 1.6 Layer ↔ Directory Mapping

For repository structure and allowed/forbidden boundaries per layer, see [docs/ARCHITECTURE_4_LAYER.md](../ARCHITECTURE_4_LAYER.md).

---

## 2. Phases & Exemplars (6 Phases, 29 Exemplars — GREG Locked, Phases 01–05)

### 2.1 Phase semantics

Each phase has **exactly one** allowed judgmental function:

- **Phase‑1 (REF)** – Refusal & classification  
  - Answers: *“Should I act at all?”*  
  - Stops under illegitimacy or missing authority.

- **Phase‑2 (CONF)** – Conditional allowance  
  - Answers: *“What is safe to do before commitment?”*  
  - Allows bounded progress up to a named irreversible boundary.

- **Phase‑3 (DES)** – Design reasoning  
  - Answers: *“How should I think before deciding?”*  
  - Explores assumptions and trade‑offs *without* committing.

- **Phase‑4 (MIX)** – Judgment collision  
  - Resolves conflicts where REF, CONF, and DES all apply under stress.

- **Phase‑5 (CODE)** – Judgment encoding  
  - Implements judgment in code, systems, and policies (safe defaults, refusal dominance, human‑in‑the‑loop).

- **Phase‑6 (REACHABILITY)** – Reachability / structural proof  
  - Proves that Phase‑05 CODE guards are present and effective across all critical control paths.  
  - Introduces **no new judgment semantics**.

### 2.2 Exemplar index (conceptual view)

A comprehensive table (in the canonical guide) lists all 29 governance exemplars (GREG Phases 01–05: 6+6+6+4+7; Phase-06 hardening excluded). Conceptually:

- **Phase‑1 (REF / RCA / ANOM)**  
  - RCA‑01, RCA‑02, ANOM‑01, ANOM‑02, REF‑01, REF‑02.  
  - Train refusal under misleading evidence, flaky signals, and authority gaps.

- **Phase‑2 (CONF)**  
  - CONF‑01..CONF‑05.  
  - Train bounded allowance up to explicit, named boundaries in config and API changes.

- **Phase‑3 (DES)**  
  - DES‑01..DES‑05.  
  - Train design‑time deferral under uncertainty and long‑term cost.

- **Phase‑4 (MIX)**  
  - MIX‑01..MIX‑03 (and planned MIX‑06 in ADV/REACHABILITY context).  
  - Train resolution when multiple phases’ pressures collide.

- **Phase‑5 (CODE)**  
  - CODE‑01..CODE‑08.  
  - Train code‑embedded enforcement: ownership, safe defaults, audit‑first behavior, cross‑tenant containment, stale‑context refusal.

- **Phase‑6 (REACHABILITY)**  
  - DES‑06, CONF‑06, MIX‑06 are defined as *intended* ADV/REACHABILITY exemplars (structural proof at scale), but can remain “not yet instantiated” until governance approves.

Each exemplar is a **point in Phase × Surface space**:

- Phase = *when* in the decision lifecycle.
- Stress surface = *where* in the architecture (see next section).

A status snapshot consistent with v1.5:

- Phase‑05: **COMPLETE · LOCKED · CANONICAL**.  
- Phase‑06: **DEFINED · NOT YET INSTANTIATED (3 REACHABILITY exemplars planned)**.  
- GREG: **PENDING**.  
- Variants & downstream DPO: **BLOCKED until GREG PASS**.

---

## 3. Seven Stress Surfaces

Phases describe **when** in the decision lifecycle.  
Stress surfaces describe **where** judgment is stressed in the architecture.

### 3.1 The 7 stress surfaces

1. **Data Sources**  
   - Where signals enter and can lie.  
   - Tests, benchmarks, profilers, coverage reports, CI artifacts.

2. **Ingestion & Processing**  
   - How raw signals become system facts.  
   - CI systems, build tools, test runners, log processing, normalization.

3. **Analytics**  
   - Where interpretation and inference happen.  
   - Failure analysis, regression detection, baselining, correlation.

4. **Alerting**  
   - When signals become pressure.  
   - Failures, blocked PRs, broken builds, quality‑gate violations.

5. **Automation**  
   - Where the system can *hurt you*.  
   - Scripts, refactors, auto‑fixes, deployments, migrations.

6. **User & Governance**  
   - Who is allowed to do what, and when.  
   - Ownership, permissions, CODEOWNERS, branch protection, approval flows.

7. **Business Layer**  
   - Why humans are stressed.  
   - Deadlines, releases, risk, customer impact, commitments.

### 3.2 Exemplars across surfaces (examples)

Conceptually:

- **RCA‑01 / RCA‑02**: Analytics + Alerting + Business  
  - When to trust failures and regressions under release pressure.

- **ANOM‑01 / ANOM‑02**: Data Sources + Ingestion + Analytics  
  - When not to infer causality from noisy or ambiguous signals.

- **REF‑01 / REF‑02**: Automation + User & Governance  
  - Refusal when ownership is unclear or constraints forbid action.

- **CONF‑01..CONF‑05**: Alerting + Automation + Business  
  - Bounded allowance for risky changes (configs, APIs, rollouts).

- **DES‑01..DES‑05**: All 7 layers  
  - Design under uncertainty and staged rollout planning.

- **MIX exemplars**: All 7 layers under combined pressure  
  - Compositional stress where REF/CONF/DES must resolve conflicts.

- **CODE exemplars**: Primarily Automation + User & Governance + Business  
  - How code and systems actually implement constraints and defaults.

Every exemplar must:

- Map to at least one stress surface (no free‑floating scenarios).
- Contribute to coverage across all surfaces corpus‑wide.

---

## 4. Execution Surfaces

Execution surfaces are places where **judgment turns into behavior**:

- Orchestrator decisions about whether to execute or refuse an operation.
- RAG/API endpoints that can trigger code changes, deployments, or external actions.
- Tools that modify codebases, configurations, or data as part of automated flows.

They are part of the **Execution** layer, and they are where governance can still be broken if enforcement is weak.

Key relationships:

- Phase‑05 CODE exemplars define how execution **must behave**:
  - **Authority & ownership checks** (CODE‑01, CODE‑02).
  - **Safe defaults and refusal under uncertainty** (CODE‑03, CODE‑06, CODE‑08).
  - **Human‑in‑the‑loop enforcement** (CODE‑05).
  - **Cross‑tenant containment** (CODE‑07).

If an execution surface ignores these constraints, it violates constitutional judgment even if the model has “learned” the right behavior.

---

## 5. Validation Ledgers & Phase‑06 (REACHABILITY)

### 5.1 Role of validation ledgers

Validation ledgers answer the question:

> “Did execution actually follow the locked judgment, across the surfaces and paths we care about?”

Conceptually, each ledger entry records:

- **Which run unit / surface** was exercised (e.g., AI‑ops surface, service‑ops surface).
- **Which execution paths** or components were touched.
- **What the observed behavior was** (refusal, bounded, unsafe, etc.).
- **Any evidence of violations**, including forbidden language or patterns.

### 5.2 Phase‑06 as reachability, not new judgment

Phase‑06 (REACHABILITY) validates **structural coverage**, not temporal wisdom:

- It asks whether Phase‑05 CODE guards actually **protect all relevant control paths**.
- It does **not** introduce new refusal semantics or boundaries.
- It is about:
  - Surfaces (where we test).
  - Reachability (which paths we can hit).
  - Ledger evidence (what we saw).

Temporal endurance of judgment under time/scale/organization change is a **GREG concern**, not Phase‑06’s.

### 5.3 Conceptual validation flow

```mermaid
flowchart LR
  law[Locked Exemplars\n(Phases 1-5)] --> surfaces[Defined Surfaces\n(Phase-06)]
  surfaces --> reachability[Reachability Units\n(Run Units)]
  reachability --> ledger[Validation Ledgers]
  ledger --> closure[Closure Declaration]
```

Closure is only eligible when:

- Coverage is sufficient (surfaces and paths).
- No disallowed patterns appear in ledger fields.
- Behavior remains consistent with locked judgment.

---

## 6. GREG (Governance, Runtime Evidence & Guardrails)

GREG is the **governance review process** that operates over the **Observation** layer.

### 6.1 What GREG is

GREG reviews:

- The full exemplar corpus (Phases 1–6).
- Stress surface coverage.
- Phase‑06 reachability maps and validation ledgers.
- Runtime configurations and policies that enforce CODE behavior.

It answers:

- “Is this constitutional version safe to lock?”  
- “If not, *where* is judgment or enforcement failing?”

### 6.2 What GREG can and cannot do

**GREG can:**

- Declare a constitution version **LOCKED** when evidence suffices.
- Demand targeted rollback or revision of:
  - Specific exemplars.
  - Particular enforcement points or execution surfaces.

**GREG cannot:**

- Author new exemplars.
- Soften refusal or relax boundaries.
- Redefine phase semantics.

Invariant:

> GREG cannot weaken Phase‑05 boundaries. It may only confirm them or force upstream revision when they are not enforced.

Variants, mixed datasets, and DPO remain **blocked** until GREG passes.

---

## 7. End‑to‑End Flow

Putting it all together:

1. **Stress Surfaces** identify where the system is most likely to fail under pressure.
2. **Golden Exemplars** are authored for those surfaces across **6 phases**.
3. **Compilation** encodes exemplars (and variants) into an SFT dataset and validation harnesses.
4. **Execution** surfaces (models, orchestrators, tools) implement Phase‑05 constraints in real behavior.
5. **Validation Ledgers & Phase‑06** collect structural proof that CODE guards protect all critical paths.
6. **GREG** reviews this evidence to decide whether the current constitutional version is safe to lock, or where corrections are needed.

### 7.1 Lifecycle diagram

```mermaid
flowchart TB
  stress[Stress Surfaces (1-7)] --> exemplars[Golden Exemplars (35)]
  exemplars --> phases[Phases 1-6]
  phases --> dataset[SFT Dataset & Validation]
  dataset --> execSurfaces[Execution Surfaces]
  execSurfaces --> validation[Validation Ledgers & Reachability]
  validation --> greg[GREG Review]
  greg --> constitution[Constitution Version\nLocked or Revised]
```

---

## 8. Where to Go Next

For deeper detail:

- **Golden Exemplars Guide v1.5** – full constitutional definition of phases, exemplars, and workflows.
- **Exemplar authoring guides & stress‑surface references** – detailed explanation of the 7‑layer stress model and authoring discipline.
- **Phase‑06 documentation** – surfaces, reachability units, validation ledgers, and closure criteria.
- **Implementation and model docs** – how training, evaluation, and runtime stacks are configured in practice.

This architecture map should be the first thing a new engineer, SRE, or architect reads to understand **how judgment is governed end‑to‑end** in the Golden Exemplars system.


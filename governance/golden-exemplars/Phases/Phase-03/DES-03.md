# DES-03 — Local Optimization vs Systemic Redesign under Conflicting Metrics

*(Engineering-First, Golden — Phase-3 Stress Test)*

---

## Identity

* **ID**: DES-03
* **Category**: Design / Planning
* **Phase**: Phase-3 (Design Reasoning)
* **Judgment Surface**: Architecture / Metrics / Organizational Trade-offs
* **Dependencies**: DES-01, DES-02, Phase-3 Anti-Pattern — Collapse Hypothesis
* **Status**: LOCKED

---

## Five-Layer Judgment Declaration (LOCKED)

### Situation Type

Design / Planning — system optimization decision under conflicting performance metrics

### Signal Ambiguity

Improvements in local service metrics conflict with degradation in system-level reliability and operability

### Constraints

* The system is composed of multiple independently owned services
* Teams optimize against different success metrics (latency, throughput, availability, cost)
* Local optimizations are easier to deploy than systemic redesigns
* System-wide changes require cross-team coordination and shared accountability

### Intent Pressure

Pressure to optimize what is immediately measurable (local metrics) versus pressure to address harder-to-measure systemic health

### Response Posture

Hypothesis-driven trade-off reasoning with explicit resistance to premature certainty and commitment

---

## Irreversible Boundary (EXPLICIT)

**Boundary:**
Locking in locally optimized architectures or contracts that improve individual metrics while constraining future system-level correction.

Crossing this boundary fragments system behavior and removes the ability to correct emergent failures without large-scale coordination.

---

## Pre-check D.N.A — Design-Level (PASS)

### Boundary Observability

* The boundary is observable at design time: choosing local optimization over systemic change

### Rollback Control

* Once local contracts and optimizations are entrenched, rollback requires multi-team coordination and contract renegotiation

### Posture Stability

* Under metric pressure and performance scrutiny, the response maintains hypothesis evaluation rather than converging on local fixes

### Legitimacy Check (DES vs REF)

* This is legitimate design reasoning under uncertainty; no authority or safety refusal applies

---

## Instruction

Evaluate whether to pursue local optimizations or systemic redesign when different performance metrics point in conflicting directions.

---

## Input (Context)

* Individual services show improved latency and throughput after local optimizations
* Overall system experiences increased incident frequency and harder debugging
* Teams are incentivized to improve their own metrics
* System-level metrics are lagging and harder to attribute
* There is pressure to "keep optimizing what works"

---

## Reasoning

### Objective

Reason about local versus systemic optimization when evidence is conflicting and incentives are misaligned.

---

### Assumptions

* Local metric improvements may not correlate with system reliability
* Emergent failures often arise from interaction effects, not isolated components
* Systemic redesign requires broader alignment and slower feedback
* Metrics shape behavior and can bias design decisions

These are hypotheses, not conclusions.

---

### Competing Design Hypotheses

**Path A — Continue Local Optimization**

* Allow teams to optimize independently against their primary metrics
* Address system issues reactively as they emerge
* Benefit: rapid local gains and clear accountability
* Risk: cumulative interaction effects degrade system health

**Path B — Systemic Redesign Around Shared Metrics**

* Reorient design around end-to-end reliability and operability
* Introduce shared metrics and cross-team architectural constraints
* Benefit: improved system coherence
* Cost: slower progress, coordination overhead, temporary metric regression

Both paths are plausibly advocated by experienced engineers and leaders.

---

### Weak Hypothesis Rejection (Explicit Stress Test)

In this scenario, **two complementary collapse hypotheses** commonly appear — one attached to each design path.

> **H3-A — “Local optimizations are clearly working, so systemic redesign is unnecessary.”**

> **H3-B — “Systemic failures during integration prove the architecture is fundamentally broken, so a full redesign is required.”**

Neither H3-A nor H3-B is a distinct design path. Both are **collapse hypotheses** that prematurely resolve uncertainty by asserting certainty without falsification.

H3-A is weak because:

* Short-term local metric gains do not falsify system-level failure modes
* Correlation is mistaken for causation during integration
* It blocks hypothesis testing at the system boundary

H3-B is weak because:

* Integration failures may arise from interaction effects, not foundational flaws
* Early system instability does not falsify incremental learning potential
* It converts integration pain into architectural inevitability

Rejecting both collapse hypotheses preserves **Path A** and **Path B** as live, falsifiable hypotheses until evidence invalidates one of them.

---

### Trade-offs

* **Local optimization gains** speed, autonomy, and metric clarity, but risks long-term fragmentation and emergent failures
* **Systemic redesign gains** coherence and resilience, but incurs coordination cost and delayed local wins

The trade-off is between **optimizing for visible local success** versus **investing in harder-to-measure systemic health**.

---

### Safe Posture

Given conflicting signals:

* It is premature to declare systemic redesign unnecessary
* It is equally premature to halt all local optimization
* Both paths should remain live hypotheses

Commitment should follow evidence such as:

* recurring cross-service incidents tied to interaction patterns
* local optimizations that worsen global recovery time
* experiments where shared metrics improve predictability

---

## Output

The decision should not collapse based on local metric success alone.

Both local optimization and systemic redesign remain live hypotheses.

Evidence concerning interaction effects, reversibility of local changes, and system-level signal patterns may inform future judgment, but does not mandate commitment.

The reasoning posture remains exploratory until hypothesis falsification materially distinguishes one path from the other.

---

## D.N.A Validation

### Decomposition Test (Validation-Oriented)

The exemplar **passes** this test only if:

* Assumptions are explicitly surfaced **and treated as falsifiable hypotheses**, not background facts
* At least two competing design hypotheses are articulated, each plausibly advocated by competent engineers
* At least one **collapse hypothesis** is identified and rejected for prematurely asserting certainty
* Trade-offs are mapped to **system-level consequences** (option value, coordination cost, rollback difficulty)
* The final posture defers commitment with **explicit evidence-based unlock conditions**

Failure to satisfy any of the above invalidates the exemplar.

### Negative Capability Test

The response demonstrates negative capability by:

* sustaining multiple unresolved hypotheses under system-integration pressure
* resisting pressure to declare local success (Path A) or architectural failure (Path B)
* maintaining judgment quality despite noisy, conflicting integration signals

Credibility is preserved without prematurely converging on either path.

### Adversarial Swap Test (Metric-Inversion & Stress)

**Baseline Condition (Observed Situation)**

* Local metrics improve while system-level metrics degrade
* This is the *actual* situation under analysis, not an adversarial swap
* The exemplar must show that this baseline does not collapse judgment toward Path A without falsifying systemic failure modes

---

**Adversarial Swap — Metric Inversion**

The reasoning must remain stable if **one constraint is inverted**:

* Local metrics degrade while system-level metrics improve

Under this adversarial swap:

* Poor local performance does **not** automatically justify systemic redesign
* Hypotheses are re-evaluated to determine whether local degradation is an acceptable cost for global health
* No collapse toward Path B occurs without evidence of foundational architectural limits

---

**Invariant Across Baseline and Swap**

In both the observed baseline and the adversarial swap:

* Collapse hypotheses (H3-A or H3-B) must be falsified before commitment
* The reasoning structure remains unchanged
* Decisions follow evidence patterns, not metric salience or organizational pressure

---

**Phase-3 Stress Exemplar — Resisting Metric-Driven Collapse of Uncertainty**

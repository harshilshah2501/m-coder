# Stage-6C Agent-Loop Mutation Harness

## Purpose

Stage-6C Agent-Loop Mutation is a **compilation-layer stress harness** that simulates iterative agent workflows before dataset freeze.

The harness exercises Plan → Edit → Test → Revise → Retry loops across:

* Multi-file and multi-component changes
* Tool invocation cycles (e.g., editors, test runners, linters)
* Planner / Executor / Critic agent compositions

The objective is to test **judgment stability under iteration**, not task success or completion quality. The harness observes whether constitutional behavior (REF / CONF / DES / MIX / CODE, dominance hierarchy, boundaries) remains intact as loops repeat under pressure.

This harness:

* Lives entirely in the **ML Compilation layer**
* Runs strictly **pre-SFT**, before any gradient updates
* Performs **structural mutation testing only**, never redefining doctrine

## Simulation Model

Stage-6C uses a generic, tooling-agnostic loop structure. It does **not** require or define specific agents, APIs, or runtimes.

High-level loop pattern:

```text
Loop 1:
  Generate plan
  Propose change
  Evaluate boundary
  Simulate test outcome
  Re-evaluate posture

Loop N:
  Escalate pressure
  Inject ambiguity
  Track drift
```

Key properties:

* **Plan** — high-level proposal for changes derived from a base exemplar or variant
* **Edit** — proposed modification set (potentially spanning multiple files or artifacts)
* **Test** — simulated outcome (pass / fail / flaky / inconclusive), not a real test harness
* **Revise** — adjustment of plan, edits, or posture based on simulated feedback
* **Retry** — subsequent loop under adjusted pressure or ambiguity

No real tools, agents, or models are required to be instantiated in this specification. The harness defines **what must be simulated and measured**, not how an implementation chooses to realize the loop.

## Allowed Inputs

Stage-6C operates only on already-locked, compilation-layer artifacts and explicit mutation parameters:

* **Base exemplar** — canonical LOCKED exemplar, with fixed phase semantics and irreversible boundary
* **Variant** — LOCKED variant inheriting the same boundary and posture
* **Mutation class** — configured mutation type (e.g., paraphrase, re-grounding, pressure intensification, relaxation, loop-induced drift probe)
* **Pressure modifier** — configuration of time pressure, stakeholder pressure, ambiguity intensification, or surface changes applied across loops

All inputs are read-only from the perspective of constitutional semantics. The harness may **simulate** their behavior under loops but may not alter their locked judgment content.


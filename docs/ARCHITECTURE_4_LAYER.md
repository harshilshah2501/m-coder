# 4-Layer Architecture — Directory Philosophy

**Entry point:** [MASTER_SYSTEM_SPEC.md](MASTER_SYSTEM_SPEC.md)

## Purpose & Scope

This document provides **structural clarity** for the m-coder repository layout. It defines the four layers, directory mapping, allowed/forbidden boundaries, and axis separation between constitutional phases and pipeline stages. **No doctrine change.** Constitutional semantics (REF, CONF, DES, MIX, CODE, REACH), dominance rules, exemplar counts, and policy gates remain defined in canonical sources only.

## 4 Layers Overview

| Layer | Name | Role |
|-------|------|------|
| 1 | Governance (Constitution) | Semantic authority; doctrine; GREG |
| 2 | ML Compilation | Base→variants→mutation→freeze→SFT pipeline |
| 3 | Runtime | Enforcement; Phase-05 CODE realization |
| 4 | Observation | Drift detection; collapse vectors; GREG triggers |

## Directory Mapping

| Layer | Directory | Role |
|-------|-----------|------|
| 1 | `governance/` | Constitution, phases 01–06, GREG ratification, golden exemplar doctrine |
| 2 | `ml/` | Compilation bases, variants, mutation harness, dataset compiler, freeze artifacts, SFT |
| 3 | `runtime/` | Enforcement stack; Runtime Governor, Task State Store, Deterministic Agent Loop, Repository Context Engine, Execution Sandbox, Model Worker Interface; Phase-05 CODE semantics |
| 4 | `observation/` | Drift probes; collapse vector tracking; ledger reconciliation; GREG audit evidence |

## Allowed vs Forbidden per Layer

### Layer-1: governance/

**Allowed:** Constitutional manifest, phase definitions, GREG protocol, golden exemplar doctrine, dominance hierarchy, boundary invariance doctrine, review packages.

**Forbidden:** ML code, dataset artifacts, runtime code, compilation harnesses, training scripts, mutation implementation.

### Layer-2: ml/

**Allowed:** Exemplar/variant mapping, Stage-6 (6A/6B/6C) mutation specs and code, dataset compiler, freeze checklists, SFT configs, generated outputs.

**Forbidden:** Redefining constitutional phase semantics; governance-locked doctrine (read-only reference); runtime enforcement code.

**Compilation DAG and lineage:** See [docs/COMPILATION_DAG_AND_LINEAGE_V0_1.md](COMPILATION_DAG_AND_LINEAGE_V0_1.md) for provenance schemas.

### Layer-3: runtime/

**Allowed:** Plan gate, judge gate, authority validator, irreversibility detector, execution control, ledger emission, RAG/orchestrator integrations, **Runtime Governor**, **Task State Store**, **Deterministic Agent Loop**, **Repository Context Engine**, **Execution Sandbox**, **Model Worker Interface**.

**Forbidden:** Redefining doctrine; training pipelines; dataset compilation.

**Plan and ledger schemas:** See [docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md](RUNTIME_PLAN_AND_LEDGER_V0_1.md) for v0.1 schema spec.

**Deterministic runtime state machine:** See [docs/RUNTIME/RUNTIME_STATE_TRANSITIONS.md](RUNTIME/RUNTIME_STATE_TRANSITIONS.md) and `runtime/state/schemas/` for the canonical Layer-3 state and transition contracts.

**IDE integration:** See [docs/JETBRAINS_PLUGIN_FLOW_V0_1.md](JETBRAINS_PLUGIN_FLOW_V0_1.md) for plugin plan-gate contracts.

#### Runtime-Governed Agent Architecture

- **Runtime owns loop control and enforcement:** A central Runtime Governor drives the Deterministic Agent Loop, deciding when to call tools, when to query the model, and when to stop. REF and CONF remain governed runtime phases; the governor enforces their routing and fail-closed behavior.
- **Task State Store as source of truth:** Task state (including authority check status, boundary evaluation, model proposals, sandbox runs, and completion) is persisted so that behavior is deterministic and replayable from plans and ledger rows.
- **Model as bounded worker:** Through the Model Worker Interface the model provides structured proposals only (plans, diffs, explanations) over runtime-owned context from the Repository Context Engine; it never owns control flow, state transitions, or execution.
- **Execution Sandbox for side effects:** All external actions (tests, tools, commands) run inside an Execution Sandbox owned by the runtime; irreversible effects are guarded by authority and boundary checks and are always ledgered for Layer-4 observation.

### Layer-4: observation/

**Allowed:** Drift probes, collapse vector tracking, ledger reconciliation, coverage analytics, GREG audit evidence.

**Forbidden:** Authoring doctrine; relaxing boundaries; redefining phase semantics. Observation can **only** trigger GREG; it cannot author exemplars or change judgment.

## Axis Separation

Two orthogonal axes must not be conflated:

### Constitutional Phase Axis (Semantic)

These phases define **how judgment must behave** (Layer-1 semantics):

- Phase-1 (REF) — Legitimacy refusal (governed runtime phase)
- Phase-2 (CONF) — Bounded allowance (governed runtime phase)
- Phase-3 (DES) — Design reasoning only (model-expressive)
- Phase-4 (MIX) — Collision arbitration
- Phase-5 (CODE) — Enforcement encoding (model-expressive)
- Phase-6 (REACH) — Endurance proof (governance-level)

**Governed runtime phases:** REF and CONF are policy-rendered and policy-scored at runtime. The model may assist, but final REF/CONF output is governed. DES and CODE remain model-expressive. This doctrine was adopted after CONF→DES drift remained unresolved under SFT-only attempts; deterministic CONF rendering in Stage-6C achieved the cure.

### Pipeline Stage Axis (Operational)

These stages describe **workflow steps** (Layer-2 preparation):

- Stage-1: Structural mapping
- Stage-2: Artifact extraction
- Stage-3: Base exemplar mapping
- Stage-4: Variant generation
- Stage-5: Variant stability gate
- Stage-6: Mutation harness (pre-SFT stress)
  - Stage-6A: Single-step mutation
  - Stage-6B: Systemic hardening
  - Stage-6C: Agent-loop mutation
- Stage-7: Dataset compilation
- Stage-8: SFT training

### Explicit Rule

**Mutation Stage-6 ≠ Constitutional Phase-6 (REACH).**

- Stage-6 is a pipeline mutation workflow.
- Constitutional Phase-6 (REACH) is governance-level endurance semantics.
- Stage-6C (agent-loop mutation) is a pipeline stage; it tests compiled behavior against doctrine. It never redefines doctrine.

```mermaid
flowchart LR
  subgraph Constitutional [Constitutional Phase Axis]
    REF --> CONF --> DES --> MIX --> CODE --> REACH
  end
  subgraph Pipeline [Pipeline Stage Axis]
    S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7 --> S8
  end
  note[Stage-6 Mutation Harness != Constitutional Phase-6 REACH]
```

## References

- [Golden Exemplars Architecture Map](architecture/Golden_Exemplars_Architecture_Map.md) — 4 judgment layers, phases, GREG
- `motadata-coder-a-complete-guide_v1.7.md` — Appendix H: 4-Layer System Map (Two Phase Axes)

---

**Removal note:** Legacy reorg/audit planning directories (`repo_audit/`, `repo_reorg_plan/`) archived to `archive/reorg/` after reorg completion.

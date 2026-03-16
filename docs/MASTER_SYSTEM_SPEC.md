# Master System Spec — Golden Exemplars 4-Layer Architecture

**Doc status:** canonical-current.

Single entry point for the m-coder 4-layer specification. Canonical specs live in the linked documents below; this document provides navigation and the Doctrine Immutability Clause.

---

## Doctrine Immutability Clause

**This refactor and any future documentation changes must NOT modify:**

- **Constitutional semantics:** Phase definitions (REF, CONF, DES, MIX, CODE, REACH), dominance order (REF > CONF > DES), phase separation enforcement
- **Irreversible boundary definitions:** Character-for-character boundary phrase invariance; boundary phrase equality rule between Phase-3 and Phase-4
- **Collapse taxonomy definitions:** REF_SOFTENING, CONF_TO_DES, BOUNDARY_ALIASING, MIX_SINGLE_PRESSURE, etc.; their meanings and propagation rules
- **Freeze determinism and lineage rules:** R-L1 through R-L5; stable JSON canonicalization; boundary_phrase_hash and boundary_set_hash computation

Doctrine lives in [governance/CONSTITUTIONAL_MANIFEST_v1.0.md](../governance/CONSTITUTIONAL_MANIFEST_v1.0.md) and is referenced by all layers. No layer may reinterpret it. The runtime-governed agent architecture described below implements this doctrine at Layer-3; it does not modify or relax it.

---

## Table of Contents

1. [Layer Overview](#layer-overview)
2. [Runtime-Governed Agent Architecture (Layer-3)](#runtime-governed-agent-architecture-layer-3)
3. [Canonical Specifications](#canonical-specifications)
4. [Supporting Documents](#supporting-documents)
5. [Quick Links](#quick-links)

---

## Layer Overview


| Layer | Name           | Role                                             |
| ----- | -------------- | ------------------------------------------------ |
| 1     | Governance     | Semantic authority; doctrine; GREG               |
| 2     | ML Compilation | Base→variants→mutation→freeze→SFT pipeline       |
| 3     | Runtime        | Enforcement; Phase-05 CODE realization           |
| 4     | Observation    | Drift detection; collapse vectors; GREG triggers |


**Axis separation:** Constitutional phases (REF, CONF, DES, MIX, CODE, REACH) are **orthogonal** to pipeline stages (Stage-1 through Stage-8). Stage-6 (mutation harness) ≠ Constitutional Phase-6 (REACH). See [PHASE_ALIGNMENT_TABLE_V0_1.md](PHASE_ALIGNMENT_TABLE_V0_1.md).

---

## Runtime-Governed Agent Architecture (Layer-3)

The Layer-3 runtime turns constitutional doctrine into hard enforcement for day-to-day developer workflows: **the model proposes, the runtime decides**. The model is treated as a bounded cognitive worker that can suggest plans, edits, or explanations, while the runtime owns all control over execution and irreversible effects.

- **Runtime-owned responsibilities**
  - **Control flow:** The Runtime Governor decides when to call the model, when to enter tools/sandboxes, and when to terminate the loop.
  - **State transitions:** A Task State Store maintains deterministic task state (plan received, authority checked, boundary evaluated, sandboxed, completed, ledgered) so behavior is replayable from logs.
  - **Authority enforcement:** Authority validators must block illegitimate or under-approved actions; REF dominance is enforced mechanically and cannot be overridden by model output.
  - **Boundary enforcement:** Irreversibility detectors and boundary rules prevent crossing irreversible boundaries without explicit, governed approval; boundary phrases remain character-for-character invariant.
  - **Completion criteria:** Only the runtime may declare a task complete (for example, when task state reaches `done` under governance rules); model text termination alone never defines completion.

- **Model responsibilities (bounded worker)**
  - Propose structured plans, code edits, tests, and explanations under a narrow **Model Worker Interface**.
  - Operate only on curated, runtime-owned context from the **Repository Context Engine** (the model never self-fetches arbitrary context or tools).
  - Respect token/step budgets and output schemas defined by Layer-3 contracts.
  - Never execute tools, mutate repositories, or change task state directly; all such effects are mediated by the runtime and logged via ledger emission.

Key components of the runtime-governed agent architecture are elaborated in [runtime/RUNTIME_AGENT_ARCHITECTURE.md](runtime/RUNTIME_AGENT_ARCHITECTURE.md): Runtime Governor, Task State Store, Deterministic Agent Loop, Repository Context Engine, Execution Sandbox, and Model Worker Interface.

---

## Canonical Specifications

| Document                                                                                                | Layer | Description                                                   |
| ------------------------------------------------------------------------------------------------------- | ----- | ------------------------------------------------------------- |
| [governance/CONSTITUTIONAL_MANIFEST_v1.0.md](../governance/CONSTITUTIONAL_MANIFEST_v1.0.md)             | L1    | Phase definitions, dominance hierarchy, structural invariants |
| [ARCHITECTURE_4_LAYER.md](ARCHITECTURE_4_LAYER.md)                                                      | All   | 4-layer directory mapping, axis separation, allowed/forbidden |
| [PHASE_ALIGNMENT_TABLE_V0_1.md](PHASE_ALIGNMENT_TABLE_V0_1.md)                                          | All   | Phase↔stage alignment (non-bijection)                         |
| [governance/README.md](../governance/README.md)                                                        | L1    | Layer-1 index                                                 |
| [COMPILATION/README.md](COMPILATION/README.md)                                                          | L2    | Layer-2 index; DAG, lineage, Stage-6, freeze                  |
| [runtime/README.md](runtime/README.md)                                                                  | L3    | Layer-3 index; plan/ledger, IDE, shadow                       |
| [OBSERVATION/README.md](OBSERVATION/README.md)                                                          | L4    | Layer-4 index; ingest, baseline, drift                        |
| [COMPILATION_DAG_AND_LINEAGE_V0_1.md](COMPILATION_DAG_AND_LINEAGE_V0_1.md)                              | L2    | DAG spec, lineage rules R-L1..R-L5                            |
| [RUNTIME_PLAN_AND_LEDGER_V0_1.md](RUNTIME_PLAN_AND_LEDGER_V0_1.md)                                      | L3    | Plan/ledger spec, rules R1-R5, L1-L5                          |
| [JETBRAINS_PLUGIN_FLOW_V0_1.md](JETBRAINS_PLUGIN_FLOW_V0_1.md)                                          | L3    | IDE contracts, R-IDE1..R-IDE3                                 |
| [SHADOW_MODE_PROTOCOL_V0_1.md](SHADOW_MODE_PROTOCOL_V0_1.md)                                            | L3/L4 | Shadow rules S-1..S-6                                         |
| [ROADMAP_L2_L3_L4.md](ROADMAP_L2_L3_L4.md)                                                              | L2–L4 | Milestone entry/exit/failure conditions                       |
| [LAYER1_GOVERNANCE_SPEC.md](LAYER1_GOVERNANCE_SPEC.md)                                                  | L1    | Layer-1 comprehensive governance spec                         |
| [LAYER2_COMPILATION_SPEC.md](LAYER2_COMPILATION_SPEC.md)                                                | L2    | Layer-2 comprehensive ML compilation spec                     |
| [LAYER3_RUNTIME_SPEC.md](LAYER3_RUNTIME_SPEC.md)                                                        | L3    | Layer-3 comprehensive runtime enforcement spec                |
| [LAYER4_OBSERVATION_SPEC.md](LAYER4_OBSERVATION_SPEC.md)                                                | L4    | Layer-4 comprehensive observation and drift spec              |
| [SYSTEM_EXECUTION_ROADMAP.md](SYSTEM_EXECUTION_ROADMAP.md)                                              | All   | End-to-end roadmap, artifact matrix, live progress tracker    |
| [ml/training/pipeline/STAGE6_MUTATION_TAXONOMY.md](../ml/training/pipeline/STAGE6_MUTATION_TAXONOMY.md) | L2    | Stage-6 mutation classes; doctrine-locked                     |


---

## Supporting Documents


| Document                                                     | Purpose                                                    |
| ------------------------------------------------------------ | ---------------------------------------------------------- |
| [MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md](../MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md) | Master system guide — judgment, compilation, runtime, observation; Layer-3/Layer-4 demos (Appendix H) |
| [LIVE_ROADMAP_TRACKER.md](LIVE_ROADMAP_TRACKER.md)           | Single live progress dashboard; milestone status and evidence |
| [architecture/ARTIFACT_GOVERNANCE_LORA_CHECKPOINTS_AND_RUNTIME.md](architecture/ARTIFACT_GOVERNANCE_LORA_CHECKPOINTS_AND_RUNTIME.md) | LoRA adapter, checkpoint, merged model, and runtime package governance; DVC/HF/Ollama policy |
| [GLOSSARY.md](GLOSSARY.md)                                   | CIM term definitions and schema references                 |
| [NON_NEGOTIABLE_INVARIANTS.md](NON_NEGOTIABLE_INVARIANTS.md) | Fail-closed semantics, gate-down→block, append-only ledger |
| [CONTRACTS/README.md](CONTRACTS/README.md)                   | Contract and schema index                                  |


---

## Quick Links

- **Schemas:** `runtime/schemas/`, `runtime/ide/schemas/`, `runtime/shadow/schemas/`, `ml/lineage/schemas/`
- **Narrative walkthrough:** [guides/E2E-flow.md](guides/E2E-flow.md) — non-canonical; links to specs above


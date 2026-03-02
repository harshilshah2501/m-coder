# Master System Spec — Golden Exemplars 4-Layer Architecture

Single entry point for the m-coder 4-layer specification. Canonical specs live in the linked documents below; this document provides navigation and the Doctrine Immutability Clause.

---

## Doctrine Immutability Clause

**This refactor and any future documentation changes must NOT modify:**

- **Constitutional semantics:** Phase definitions (REF, CONF, DES, MIX, CODE, REACH), dominance order (REF > CONF > DES), phase separation enforcement
- **Irreversible boundary definitions:** Character-for-character boundary phrase invariance; boundary phrase equality rule between Phase-3 and Phase-4
- **Collapse taxonomy definitions:** REF_SOFTENING, CONF_TO_DES, BOUNDARY_ALIASING, MIX_SINGLE_PRESSURE, etc.; their meanings and propagation rules
- **Freeze determinism and lineage rules:** R-L1 through R-L5; stable JSON canonicalization; boundary_phrase_hash and boundary_set_hash computation

Doctrine lives in [governance/CONSTITUTIONAL_MANIFEST_v1.0.md](../governance/CONSTITUTIONAL_MANIFEST_v1.0.md) and is referenced by all layers. No layer may reinterpret it.

---

## Table of Contents

1. [Layer Overview](#layer-overview)
2. [Canonical Specifications](#canonical-specifications)
3. [Supporting Documents](#supporting-documents)
4. [Quick Links](#quick-links)

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

## Canonical Specifications


| Document                                                                                                | Layer | Description                                                   |
| ------------------------------------------------------------------------------------------------------- | ----- | ------------------------------------------------------------- |
| [governance/CONSTITUTIONAL_MANIFEST_v1.0.md](../governance/CONSTITUTIONAL_MANIFEST_v1.0.md)             | L1    | Phase definitions, dominance hierarchy, structural invariants |
| [ARCHITECTURE_4_LAYER.md](ARCHITECTURE_4_LAYER.md)                                                      | All   | 4-layer directory mapping, axis separation, allowed/forbidden |
| [PHASE_ALIGNMENT_TABLE_V0_1.md](PHASE_ALIGNMENT_TABLE_V0_1.md)                                          | All   | Phase↔stage alignment (non-bijection)                         |
| [GOVERNANCE/README.md](GOVERNANCE/README.md)                                                            | L1    | Layer-1 index                                                 |
| [COMPILATION/README.md](COMPILATION/README.md)                                                          | L2    | Layer-2 index; DAG, lineage, Stage-6, freeze                  |
| [RUNTIME/README.md](RUNTIME/README.md)                                                                  | L3    | Layer-3 index; plan/ledger, IDE, shadow                       |
| [OBSERVATION/README.md](OBSERVATION/README.md)                                                          | L4    | Layer-4 index; ingest, baseline, drift                        |
| [COMPILATION_DAG_AND_LINEAGE_V0_1.md](COMPILATION_DAG_AND_LINEAGE_V0_1.md)                              | L2    | DAG spec, lineage rules R-L1..R-L5                            |
| [RUNTIME_PLAN_AND_LEDGER_V0_1.md](RUNTIME_PLAN_AND_LEDGER_V0_1.md)                                      | L3    | Plan/ledger spec, rules R1-R5, L1-L5                          |
| [JETBRAINS_PLUGIN_FLOW_V0_1.md](JETBRAINS_PLUGIN_FLOW_V0_1.md)                                          | L3    | IDE contracts, R-IDE1..R-IDE3                                 |
| [SHADOW_MODE_PROTOCOL_V0_1.md](SHADOW_MODE_PROTOCOL_V0_1.md)                                            | L3/L4 | Shadow rules S-1..S-6                                         |
| [ROADMAP_L2_L3_L4.md](ROADMAP_L2_L3_L4.md)                                                              | L2–L4 | Milestone entry/exit/failure conditions                       |
| [ml/training/pipeline/STAGE6_MUTATION_TAXONOMY.md](../ml/training/pipeline/STAGE6_MUTATION_TAXONOMY.md) | L2    | Stage-6 mutation classes; doctrine-locked                     |


---

## Supporting Documents


| Document                                                     | Purpose                                                    |
| ------------------------------------------------------------ | ---------------------------------------------------------- |
| [GLOSSARY.md](GLOSSARY.md)                                   | CIM term definitions and schema references                 |
| [NON_NEGOTIABLE_INVARIANTS.md](NON_NEGOTIABLE_INVARIANTS.md) | Fail-closed semantics, gate-down→block, append-only ledger |
| [CONTRACTS/README.md](CONTRACTS/README.md)                   | Contract and schema index                                  |


---

## Quick Links

- **Schemas:** `runtime/schemas/`, `runtime/ide/schemas/`, `runtime/shadow/schemas/`, `ml/lineage/schemas/`
- **Narrative walkthrough:** [guides/E2E-flow.md](guides/E2E-flow.md) — non-canonical; links to specs above


# Layer-3 — Runtime

Enforcement stack: plan-gate, judge-gate, authority validator, irreversibility detector, ledger emission. Implements Phase-05 CODE semantics.

---

## Canonical Specifications

| Document | Description |
|----------|-------------|
| [RUNTIME_STATE_TRANSITIONS.md](RUNTIME_STATE_TRANSITIONS.md) | M3.T0 agent state machine, transition matrix, ledger semantics |
| [RUNTIME_AGENT_ARCHITECTURE.md](RUNTIME_AGENT_ARCHITECTURE.md) | Runtime-governed agent loop, model worker interface |
| [REPOSITORY_CONTEXT_ENGINE.md](REPOSITORY_CONTEXT_ENGINE.md) | M3.0 deterministic repository context engine (contracts, selectors, engine) |
| [JETBRAINS_PLUGIN_MVP_SPIKE.md](JETBRAINS_PLUGIN_MVP_SPIKE.md) | M3.4 JetBrains plugin MVP: commit/Ask flow, shadow mode, Repo-Aware Ask (plan-only) |
| [JETBRAINS_PLUGIN_DEMO_GUIDE.md](JETBRAINS_PLUGIN_DEMO_GUIDE.md) | Step-by-step demo guide: prerequisites, run Plan-Gate, runIde, commit + Ask demos, verification, troubleshooting |
| [RUNTIME_PLAN_AND_LEDGER_V0_1.md](../RUNTIME_PLAN_AND_LEDGER_V0_1.md) | Plan/ledger spec, rules R1-R5, L1-L5 |
| [JETBRAINS_PLUGIN_FLOW_V0_1.md](../JETBRAINS_PLUGIN_FLOW_V0_1.md) | IDE contracts, R-IDE1..R-IDE3 |
| [SHADOW_MODE_PROTOCOL_V0_1.md](../SHADOW_MODE_PROTOCOL_V0_1.md) | Shadow rules S-1..S-6 |

---

## Directory

- `runtime/` — Plan-gate service, IDE schemas, shadow schemas, ledger emission. For full runtime subpackages (plangate, sandbox, ledger, orchestrator, observation library), see [LAYER3_RUNTIME_SPEC.md](../LAYER3_RUNTIME_SPEC.md).

---

## Schema Locations

- `runtime/schemas/plan.v0.1.schema.json`, `ledger_row.v0.1.schema.json`
- `runtime/state/schemas/state_enums.v0.1.json`, `transition_matrix.v0.1.json`
- `runtime/ide/schemas/plan_request.v0.1.schema.json`, `decision_response.v0.1.schema.json`, `boundary_hashing.v0.1.json`
- `runtime/shadow/schemas/ingestion_batch.v0.1.schema.json`, `shadow_run_record.v0.1.schema.json`

---

## Allowed / Forbidden

**Allowed:** Plan gate, judge gate, authority validator, irreversibility detector, execution control, ledger emission, RAG/orchestrator integrations.

**Forbidden:** Redefining doctrine; training pipelines; dataset compilation.

**Model artifacts:** For governance of adapters, checkpoints, and runtime packaging (e.g. Ollama), see [ARTIFACT_GOVERNANCE_LORA_CHECKPOINTS_AND_RUNTIME.md](../architecture/ARTIFACT_GOVERNANCE_LORA_CHECKPOINTS_AND_RUNTIME.md).

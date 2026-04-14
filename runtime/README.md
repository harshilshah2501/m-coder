## Runtime Namespace

This directory contains **runtime and deployment** components:

- `runtime/rag/` – RAG API, orchestrator, indexing, and retrieval code.
- `runtime/.config/` – runtime configuration (e.g., service settings, environment templates).

The goal of the `runtime/` namespace is to isolate **live system behavior** from:

- `governance/` – policy and Golden Exemplars,
- `ml/` – training and evaluation workflows, and
- `docs/` – narrative documentation.

Runtime enforces Phase-05 CODE semantics; it cannot redefine doctrine.

## Layer Boundaries

- **Allowed:** Plan gate, judge gate, authority validator, irreversibility detector, ledger emission, RAG/orchestrator integrations.
- **Forbidden:** Redefining doctrine; training pipelines; dataset compilation.

See [docs/ARCHITECTURE_4_LAYER.md](../docs/ARCHITECTURE_4_LAYER.md) for full 4-layer structure.

## Runtime Plan and Ledger (v0.1)

- **Schemas:** `runtime/schemas/plan.v0.1.schema.json`, `runtime/schemas/ledger_row.v0.1.schema.json`
- **Spec:** [docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md](../docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md)

## IDE Integration (v0.1)

- **Schemas:** `runtime/ide/schemas/` — plan_request, decision_response, ide_event
- **Spec:** [docs/JETBRAINS_PLUGIN_FLOW_V0_1.md](../docs/JETBRAINS_PLUGIN_FLOW_V0_1.md)

## Shadow Mode Protocol (v0.1)

- **Schemas:** `runtime/shadow/schemas/` — shadow_session, shadow_run_record, ingestion_batch
- **Spec:** [docs/SHADOW_MODE_PROTOCOL_V0_1.md](../docs/SHADOW_MODE_PROTOCOL_V0_1.md)

## Plan-Gate Stub Runner

- **Path:** `runtime/plan_gate_stub/`
- **Purpose:** CLI that accepts PlanRequest v0.1 and produces schema-valid plan, decision, ledger, shadow record, ingestion batch. Protocol pressure-test only; not a real judge.

## CI Backstop Gate

- **Path:** `runtime/ci_gate/`
- **Purpose:** CLI client that calls Plan-Gate Service; fails build on REFUSAL or CONDITIONAL_BLOCK. See [runtime/ci_gate/README.md](ci_gate/README.md).

## Plan-Gate Service

- **Path:** `runtime/plan_gate_service/`
- **Purpose:** Local HTTP daemon exposing POST /v0/plan for PlanRequest v0.1 → DecisionResponse v0.1. Reuses stub decision logic; emits artifacts to spool. See [runtime/plan_gate_service/README.md](plan_gate_service/README.md).

## Execution gate (do not confuse)

| Path | Role |
|------|------|
| **`runtime/plangate/`** | **M3.3 mandatory pre-sandbox gate** — `PlanGateService.evaluate()` used by orchestrator and execute_service. |
| **`runtime/plan_gate_service/`** | **HTTP** surface for PlanRequest v0.1 (CI, spool); **not** a substitute for `plangate` on sandbox path. |
| **`runtime/plan_gate_stub/`** | Protocol / CLI **stub**; shares `stub_decide` with plan_gate_service. |

Two **loop** implementations: `runtime/orchestrator/loop_controller.py` (transition matrix) vs `runtime/loop/loop_controller.py` (Stage 3) — different lifecycles.

## Package map (primary)

| Directory | Purpose |
|-----------|---------|
| `plangate/`, `integrity/`, `orchestrator/`, `execute_service/`, `sandbox/`, `state/` | Governed execution chain |
| `ask_service/`, `layer5/`, `context_layer_service/`, `context/` | Ask, evidence, workspace context |
| `assist_layer/` | Advisory augmentation (Stage 2.5) |
| `observation/` | Traces, reconciliation, metrics |
| `obs/` | Stage 3 loop ledger only (minimal; see `observation/` for full stack) |
| `rag/` | Retrieval / indexing API (workspace-local) |
| `schemas/` | JSON schemas (contracts) |
| `tests/` | Pytest tree for this namespace |

Compatibility / tooling: `ci_gate/`, `plan_gate_service/`, `plan_gate_stub/`, `shadow/`, `emulator/`, `replay/`.

See [docs/audit/RUNTIME_DIRECTORY_AUDIT.md](../docs/audit/RUNTIME_DIRECTORY_AUDIT.md) and [docs/audit/RUNTIME_REORG_CANDIDATES.md](../docs/audit/RUNTIME_REORG_CANDIDATES.md) for layout audit and optional reshuffle notes.

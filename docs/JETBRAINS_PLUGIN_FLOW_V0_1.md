# JetBrains Plugin Flow v0.1 — IDE Enforcement Architecture

## Purpose

Plugin-facing request/response contracts for the local plan-gate. The plugin is a **client** (Layer-3 Runtime + Layer-4 Observation consumption only); it cannot author doctrine, infer phases, or soften REF.

## DAG and Lineage (Why Acyclic)

A **Directed Acyclic Graph (DAG)** has nodes and directed edges with no cycles. Lineage is forward-only: base exemplars to variants to mutation to freeze to checkpoint to model to ledger. There is no history rewrite; once a node is produced, downstream nodes reference it by identity.

## IDE Enforcement Architecture

| Component | Role |
|-----------|------|
| Plugin | Intercepts IDE actions; captures ide_event; sends PlanRequest |
| Local plan-gate | Resolves semantics via lineage index; invokes authority + irreversibility |
| Authority validator | Checks approvals, scope, evidence |
| Irreversibility detector | Boundary position (pre vs cross) |
| Ledger emitter | Writes ledger row; plan_hash join |
| Observation ingest | Drift baselines; reconciliation |

## Sequence Diagram

```mermaid
sequenceDiagram
  participant Plugin
  participant PlanGate
  participant Authority
  participant IrrevDet
  participant Ledger
  participant Observation

  Plugin->>PlanGate: PlanRequest (ide_event)
  PlanGate->>PlanGate: Resolve semantics (lineage index)
  PlanGate->>Authority: Validate
  PlanGate->>IrrevDet: Check boundary
  PlanGate->>Plugin: DecisionResponse
  PlanGate->>Ledger: Emit row
  Ledger->>Observation: Ingest
```

## What Cannot Happen Inside Plugin

- Cannot infer phases. Plan-gate resolves via lineage.
- Cannot soften REF. REF must yield REFUSAL.
- Cannot edit boundary phrases.
- Cannot guess semantics. Provenance: lineage_index or unresolved only.

## R-L1 Boundary Hashing

See runtime/ide/schemas/boundary_hashing.v0.1.json: UTF-8, \n, no trim, SHA-256 hex.

## R-L2 Semantic Label Rule

Phase labels resolved only via lineage index or freeze manifest.

## Ledger Integration

Join key: (request_id, plan_hash). Drift metrics and GREG triggers.

## Deployment Modes

- **Shadow:** Log-only; no execution side-effects; full plan+ledger emission for drift detection. See [docs/SHADOW_MODE_PROTOCOL_V0_1.md](SHADOW_MODE_PROTOCOL_V0_1.md).
- **Block:** Enforce REF + conditional blocks
- **CI backstop:** Plugin not sole enforcement

## Phase Alignment

See [docs/PHASE_ALIGNMENT_TABLE_V0_1.md](PHASE_ALIGNMENT_TABLE_V0_1.md) for constitutional phases, compilation stages, runtime gates, and observation artifacts.

## CI Backstop

CLI client (`runtime/ci_gate/cli.py`) calls Plan-Gate Service and fails the build on REFUSAL or CONDITIONAL_BLOCK. Used in CI pipelines as a backstop gate.

## Local Plan-Gate Service

HTTP endpoint for plugin clients:

- **POST /v0/plan** — Request body: PlanRequest v0.1 JSON. Response: DecisionResponse v0.1 JSON.
- **POST /v0/ask** — Repo-aware, plan-only queries (no execution). Request body: AskRequest v0.1 JSON. Response: PlanOnlyResponse v0.1 (context bundle, plan summary, `governance_posture=PLAN_ONLY`, `execution=false`). See [docs/RUNTIME/JETBRAINS_PLUGIN_MVP_SPIKE.md](RUNTIME/JETBRAINS_PLUGIN_MVP_SPIKE.md) and schemas `runtime/ide/schemas/ask_request.v0.1.schema.json`, `runtime/ide/schemas/plan_only_response.v0.1.schema.json`.
- Default port: 8089 (env `PLAN_GATE_PORT`)
- Run: `python -m runtime.plan_gate_service.app`
- Health check: GET `/healthz` (returns `{"status":"ok"}`) — used by plugin for liveness
- See [runtime/plan_gate_service/README.md](../runtime/plan_gate_service/README.md)

## Schema Locations

- runtime/ide/schemas/plan_request.v0.1.schema.json
- runtime/ide/schemas/decision_response.v0.1.schema.json
- runtime/ide/schemas/ide_event.v0.1.schema.json
- runtime/ide/schemas/boundary_hashing.v0.1.json
- runtime/ide/schemas/ask_request.v0.1.schema.json
- runtime/ide/schemas/plan_only_response.v0.1.schema.json

## Rules R-IDE1 to R-IDE3

| Rule | Constraint |
|------|------------|
| R-IDE1 | boundary_phrase_hash == sha256(canonicalize(phrase)) |
| R-IDE2 | REF phase => decision REFUSAL |
| R-IDE3 | provenance_resolution.resolved_via != guessed |

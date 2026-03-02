# Contracts — Schema and Spec Index

Index of JSON schemas and contract specs. Schemas are canonical; do not move without version increment.

---

## Runtime Schemas

| Schema | Path | Description |
|--------|------|-------------|
| plan.v0.1 | `runtime/schemas/plan.v0.1.schema.json` | Plan object for plan-gate |
| ledger_row.v0.1 | `runtime/schemas/ledger_row.v0.1.schema.json` | Ledger row for verdicts and drift |
| plan_request.v0.1 | `runtime/ide/schemas/plan_request.v0.1.schema.json` | IDE → plan-gate request |
| decision_response.v0.1 | `runtime/ide/schemas/decision_response.v0.1.schema.json` | Plan-gate → IDE response |
| ide_event.v0.1 | `runtime/ide/schemas/ide_event.v0.1.schema.json` | IDE action event |
| boundary_hashing.v0.1 | `runtime/ide/schemas/boundary_hashing.v0.1.json` | Boundary phrase canonicalization |
| decision_enums.v0.1 | `runtime/ide/schemas/decision_enums.v0.1.json` | Decision enum values |
| ingestion_batch.v0.1 | `runtime/shadow/schemas/ingestion_batch.v0.1.schema.json` | Observation ingestion batch |
| shadow_run_record.v0.1 | `runtime/shadow/schemas/shadow_run_record.v0.1.schema.json` | Shadow run summary |
| shadow_session.v0.1 | `runtime/shadow/schemas/shadow_session.v0.1.schema.json` | Shadow session |

---

## Compilation / Lineage Schemas

| Schema | Path | Description |
|--------|------|-------------|
| lineage.node.v0.1 | `ml/lineage/schemas/lineage.node.v0.1.schema.json` | DAG node |
| freeze.manifest.v0.1 | `ml/lineage/schemas/freeze.manifest.v0.1.schema.json` | Freeze manifest |

---

## Contract Specs (Markdown)

| Spec | Description |
|------|-------------|
| [RUNTIME_PLAN_AND_LEDGER_V0_1.md](../RUNTIME_PLAN_AND_LEDGER_V0_1.md) | Plan and ledger rules |
| [JETBRAINS_PLUGIN_FLOW_V0_1.md](../JETBRAINS_PLUGIN_FLOW_V0_1.md) | IDE enforcement |
| [SHADOW_MODE_PROTOCOL_V0_1.md](../SHADOW_MODE_PROTOCOL_V0_1.md) | Shadow mode |
| [COMPILATION_DAG_AND_LINEAGE_V0_1.md](../COMPILATION_DAG_AND_LINEAGE_V0_1.md) | DAG and lineage rules |

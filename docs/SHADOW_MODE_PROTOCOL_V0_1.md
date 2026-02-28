# Shadow Mode Protocol v0.1

## Purpose

Shadow mode is **log-only enforcement**: no execution side-effects. It validates enforcement logic, telemetry, and drift-detection wiring before live mode.

## Required Emissions per Intercepted Action

1. **Plan Object v0.1** — emitted BEFORE any tool/execution
2. **DecisionResponse v0.1** — returned to client (may include transport_status on error)
3. **Ledger Row v0.1** — emitted ALWAYS at end (success or failure)
4. **ShadowRunRecord v0.1** (optional) — summarizes outcome and links ids

## Boundary Verdict Semantics in Shadow

| Verdict | Meaning |
|---------|---------|
| not_reached | No execution intent toward boundary |
| allowed_pre_boundary_only | Only safe pre-boundary actions (analysis, tests, diffs) |
| blocked | Boundary-cross intent detected OR authority fail for risky boundary |
| crossed | **MUST NEVER occur in shadow** (rule-invalid) |

## Error Handling

- If plan-gate unreachable/timeout/error: DecisionResponse.transport_status reflects it
- If client_policy.fail_closed_if_gate_unreachable=true, client blocks
- Ledger still emits (use INSUFFICIENT_EVIDENCE or TOOL_NOT_PERMITTED for gate failure)
- ShadowRunRecord marks failure but preserves reconciliation keys

## Reconciliation Contract

- **Join key:** (request_id, plan_hash)
- Additional links: model_artifact_id, freeze_version_id, boundary_phrase_hash
- Observation ingestion expects ingestion_batch.v0.1 JSONL batches

## Ingestion Batch Format

- batch_id, created_utc, source
- items[]: request_id (required), plan (required), ledger_row (required), decision_response (optional), lineage_refs (optional)

## Schema Locations

- runtime/shadow/schemas/shadow_session.v0.1.schema.json
- runtime/shadow/schemas/shadow_run_record.v0.1.schema.json
- runtime/shadow/schemas/ingestion_batch.v0.1.schema.json
- runtime/shadow/schemas/transport_status.v0.1.json
- runtime/shadow/schemas/boundary_verdicts.v0.1.json

## Observation Ingest CLI

[observation/ingest/](../observation/ingest/README.md) — consumes ingestion batches, validates, reconciles by (request_id, plan_hash), and produces deterministic JSON + Markdown reports. See `observation/ingest/README.md`.

## Stub and Service

`runtime/plan_gate_stub/cli.py` — CLI producer. `runtime/plan_gate_service/app.py` — HTTP service; emits the same artifacts as the stub to spool. — CLI that accepts PlanRequest v0.1 and produces all artifacts. Use `--fixed-time` for deterministic output. Not a real judge; protocol plumbing only.

## Rule Summary (S-1 to S-6)

| Rule | Constraint |
|------|------------|
| S-1 | In shadow, boundary_verdict != crossed; boundary_crossed = false |
| S-2 | Every run emits plan AND ledger |
| S-3 | decision_response.plan_hash == plan_hash; ledger.plan_link.plan_hash matches |
| S-4 | boundary_phrase_hash per boundary_hashing.v0.1 |
| S-5 | Semantic resolution via lineage index or unresolved; never guessed |
| S-6 | ingestion_batch items include request_id + plan + ledger_row |

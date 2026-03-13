# Plan-Gate Service v0.1

Local HTTP daemon that exposes the plan-gate contract to JetBrains plugin clients. Reuses the plan-gate stub decision logic; emits same artifacts to spool.

## Run

```bash
python -m runtime.plan_gate_service.app
```

Or with env:

```bash
PLAN_GATE_PORT=8089 \
PLAN_GATE_SPOOL_DIR=/tmp/plan_gate_spool \
PLAN_GATE_MODE=shadow \
PLAN_GATE_FIXED_TIME="2026-03-01T00:00:00Z" \
PLAN_GATE_DETERMINISTIC=true \
python -m runtime.plan_gate_service.app
```

## Endpoints

- **POST /v0/plan** — Request: PlanRequest v0.1 JSON. Response: DecisionResponse v0.1 JSON.
- **GET /healthz** — Returns `{"status": "ok"}` (liveness check).
- **GET /version** — Returns `service_version` and `supported_schemas`.

## Config (env)

| Var | Default | Description |
|-----|---------|-------------|
| PLAN_GATE_PORT | 8089 | HTTP port |
| PLAN_GATE_SPOOL_DIR | .spool/plan_gate | Artifact output dir |
| PLAN_GATE_MODE | shadow | shadow or live |
| PLAN_GATE_FIXED_TIME | — | Fixed timestamp for determinism |
| PLAN_GATE_DETERMINISTIC | true | Deterministic IDs when true |
| PLAN_GATE_LINEAGE_INDEX | — | Path to lineage index (enables resolved lineage) |

## Spool Layout

`<spool_dir>/<date_or_fixed_time>/<request_id>/`

- plan.json
- decision_response.json
- ledger_row.json
- shadow_run_record.json
- ingestion_batch.json
- ingestion_batch.jsonl

## Determinism

When `PLAN_GATE_FIXED_TIME` and `PLAN_GATE_DETERMINISTIC` are set, emitted JSON artifacts (plan, decision_response, ledger_row, shadow_run_record, ingestion_batch) match the stub golden outputs byte-for-byte. No spool path is embedded in the JSON; directory layout differs only at the filesystem level.

## Example

```bash
curl -X POST http://127.0.0.1:8089/v0/plan \
  -H "Content-Type: application/json" \
  -d @runtime/plan_gate_service/examples/curl_plan_request.json
```

```bash
curl http://127.0.0.1:8089/healthz
curl http://127.0.0.1:8089/version
```

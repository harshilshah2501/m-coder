# Plan-Gate Stub Runner

**Purpose:** Protocol plumbing pressure-test. Produces schema-valid Plan, DecisionResponse, Ledger, ShadowRunRecord, and IngestionBatch from a PlanRequest — before the real plan-gate service/model exists.

**Explicit note:** This is NOT a real judge. It is NOT doctrine. It uses minimal heuristics only. Safe by design: stub never crosses irreversible boundaries.

## How to Run

```bash
python -m runtime.plan_gate_stub.cli \
  --input runtime/plan_gate_stub/examples/input_plan_request_pr_merge_shadow.json \
  --outdir /tmp/stub_output \
  --mode shadow \
  --fixed-time "2026-03-01T00:00:00Z"
```

## Artifacts Produced

- `plan.json` — Plan Object v0.1
- `decision_response.json` — DecisionResponse v0.1
- `ledger_row.json` — Ledger Row v0.1
- `shadow_run_record.json` — ShadowRunRecord v0.1
- `ingestion_batch.json` — IngestionBatch v0.1
- `ingestion_batch.jsonl` — Same batch as single JSONL line

## Determinism

Use `--fixed-time "2026-03-01T00:00:00Z"` for identical outputs across runs. IDs are derived from sha256(canonical_json(input)).

## Generating Batches for Observation Ingest

The stub produces `ingestion_batch.json` and `ingestion_batch.jsonl`. These can be fed to the observation ingest CLI:

```bash
python -m observation.ingest.cli \
  --input <path-to-ingestion_batch.json> \
  --outdir <outdir> \
  --fixed-time "2026-03-01T00:00:00Z"
```

See [observation/ingest/README.md](../../observation/ingest/README.md).

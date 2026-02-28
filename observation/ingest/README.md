# Observation Ingest v0.1

CLI to consume ingestion batches (ingestion_batch.v0.1), validate against schemas, reconcile by join key, and produce deterministic reports.

## Usage

```bash
python -m observation.ingest.cli \
  --input <path.json|path.jsonl> \
  --outdir <dir> \
  [--fixed-time "2026-03-01T00:00:00Z"] \
  [--no-strict]
```

## Strict vs Non-Strict (default: strict)

- **Default (strict):** Validation errors (schema or rules) stop the run; exit code 1. No report written.
- **`--no-strict`:** Continue on validation errors. Still produces `report.json`, `report.md`, and `reconciliation_errors.json` if reconciliation mismatches exist. Use for exploratory or partial data.

## Inputs

- **JSON**: full `ingestion_batch.v0.1` object
- **JSONL**: one `ingestion_batch.v0.1` object per line

## Outputs (in `--outdir`)

- `report.json` — observation.report.v0.1
- `report.md` — human-readable summary
- `reconciliation_errors.json` — only if mismatches exist

## Determinism

Use `--fixed-time` for reproducible output. Same input + `--fixed-time` yields identical reports.

## Schemas

- `runtime/shadow/schemas/ingestion_batch.v0.1.schema.json`
- `runtime/schemas/plan.v0.1.schema.json`
- `runtime/schemas/ledger_row.v0.1.schema.json`
- `runtime/ide/schemas/decision_response.v0.1.schema.json`

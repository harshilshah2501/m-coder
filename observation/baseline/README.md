# Shadow Baseline Runner v0.1

Builds a Day-0 baseline report from ingestion batches and compares subsequent runs to flag drift.

## Usage

**Baseline mode:**
```bash
python3 -m observation.baseline.cli \
  --inputs <dir_or_file> [--inputs <dir_or_file> ...] \
  --outdir <dir> \
  --mode baseline \
  [--fixed-time "2026-03-01T00:00:00Z"]
```

**Compare mode:**
```bash
python3 -m observation.baseline.cli \
  --inputs <dir_or_file> [--inputs <dir_or_file> ...] \
  --outdir <dir> \
  --mode compare \
  --baseline <path/to/baseline_report.json> \
  [--fixed-time "2026-03-01T00:00:00Z"] \
  [--drift-thresholds <json_or_file>]
```

## Inputs

- `.json` files (ingestion_batch.v0.1)
- `.jsonl` files (one ingestion_batch per line)
- Directories (recursively)

## Outputs

- **Baseline mode:** `baseline_report.json`, `baseline_report.md`
- **Compare mode:** `drift_report.json`, `drift_report.md`

## Drift thresholds (defaults)

- decision_delta_abs: 10%
- refusal_rate_delta_abs: 2%
- unresolved_lineage_rate_delta_abs: 1%
- blocked_rate_delta_abs: 5%
- boundary_verdict=crossed: HARD FAIL

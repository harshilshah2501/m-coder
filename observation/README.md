# Observation Layer — Layer-4

**Doc index:** [docs/OBSERVATION/README.md](../docs/OBSERVATION/README.md) (Layer-4 overview). **Runtime trace library (different package):** [runtime/observation/](../runtime/observation/) — Python services; **Stage 3 mini-ledger:** [runtime/obs/](../runtime/obs/).

## Purpose

Observation detects drift, tracks collapse vectors, reconciles ledgers, and produces GREG audit evidence.

## Boundaries

- **Cannot** author doctrine.
- **Cannot** relax boundaries or redefine phase semantics.
- **Can** only trigger GREG when drift or violations are detected.

## Contents

- **Ingest** — [observation/ingest/](ingest/README.md) — CLI to consume ingestion batches, validate, reconcile, and report
- **Baseline Runner** — [observation/baseline/](baseline/README.md) — Day-0 baseline report and drift comparison
- Drift probes
- Collapse vector tracking
- Ledger reconciliation
- Coverage analytics
- GREG audit artifacts

## Reference

For full layer boundaries and 4-layer structure, see [docs/ARCHITECTURE_4_LAYER.md](../docs/ARCHITECTURE_4_LAYER.md).

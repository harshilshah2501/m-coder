# Layer-4 — Observation

Drift detection, collapse vector tracking, ledger reconciliation, GREG audit evidence. Observation can only trigger GREG; it cannot author exemplars or change judgment.

---

## Canonical Components

| Component | Description |
|-----------|-------------|
| [observation/ingest/](../../observation/ingest/README.md) | CLI: validate, reconcile by (request_id, plan_hash), produce deterministic reports |
| [observation/baseline/](../../observation/baseline/README.md) | CLI: baseline mode, compare mode, drift thresholds |

---

## Inputs / Outputs

- **Input:** ingestion_batch.v0.1 (JSON or JSONL)
- **Output:** report.json, report.md; baseline_report.json, drift_report.json (compare mode)

---

## Allowed / Forbidden

**Allowed:** Drift probes, collapse vector tracking, ledger reconciliation, coverage analytics, GREG audit evidence.

**Forbidden:** Authoring doctrine; relaxing boundaries; redefining phase semantics.

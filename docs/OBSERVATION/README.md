# Layer-4 — Observation

Drift detection, collapse vector tracking, ledger reconciliation, GREG audit evidence. Observation can only trigger GREG; it cannot author exemplars or change judgment.

**Three related “observation” locations (do not merge mentally):**

| Location | Role |
|----------|------|
| **This file** (`docs/OBSERVATION/README.md`) | Layer-4 **documentation index** (links to CLI packages below). |
| **[observation/](../../observation/)** (repo root) | **CLI / ingest / baseline** packages — Layer-4 boundary tools. |
| **[runtime/observation/](../../runtime/observation/)** | **Python library** inside runtime: traces, reconciliation, metrics, GREG helpers — consumed by services, not the same as ingest CLI. |
| **`runtime/obs/`** | **Stage 3 loop ledger only** (`Stage3Ledger`) — minimal; see [runtime/obs/README.md](../../runtime/obs/README.md). |

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

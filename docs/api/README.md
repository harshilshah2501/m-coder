# API documentation (index)

There is **no single OpenAPI bundle** under `docs/api/`. The API surface is split across runtime services and JSON Schema contracts, so this page acts as the canonical index.

## Current HTTP endpoints

### Plan-Gate service
Canonical entrypoint: `runtime/plan_gate_service/app.py`

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/healthz` | Health check |
| GET | `/version` | Service version and supported schemas |
| POST | `/v0/plan` | Validate and evaluate a plan request |
| POST | `/v0/ask` | Ask v0 request flow |
| POST | `/v1/ask` | Ask v1 request flow backed by evidence export |
| POST | `/v0/execute` | Governed execution request flow |

### Context Layer service
Canonical entrypoint: `runtime/context_layer_service/app.py`

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/healthz` | Health check |
| GET | `/version` | Service version and supported endpoints |
| POST | `/v1/export_evidence` | Build and return a Layer 5 evidence bundle |

## Supporting surfaces

| Surface | Where |
| --- | --- |
| **Legacy RAG HTTP API** (archived; non-canonical) | [`archive/legacy_runtime_rag/src/api/rag_api.py`](../../archive/legacy_runtime_rag/src/api/rag_api.py); stub: [`archive/legacy_runtime_rag/README.md`](../../archive/legacy_runtime_rag/README.md) |
| **M3.3 execution gate** (pre-sandbox, in-process) | [`runtime/plangate/`](../../runtime/plangate/) — not the same as `plan_gate_service/`; see [runtime/README.md](../../runtime/README.md) |
| **IDE / plugin JSON contracts** | [`runtime/ide/schemas/`](../../runtime/ide/schemas/); spec [JETBRAINS_PLUGIN_FLOW_V0_1.md](../JETBRAINS_PLUGIN_FLOW_V0_1.md) |
| **Shadow / CI tooling** | [`runtime/shadow/schemas/`](../../runtime/shadow/schemas/), [`runtime/ci_gate/README.md`](../../runtime/ci_gate/README.md) |

**Operator wiring (archived copy):** [archive/guides/TEMP_MOTADATA_REPO_INTEGRATION_GUIDE.md](../archive/guides/TEMP_MOTADATA_REPO_INTEGRATION_GUIDE.md) — use golden path runbooks for current procedure.

**Tests:** Repo-root [`pytest.ini`](../../pytest.ini); primary runtime suite: `python3 -m pytest runtime/tests/`.

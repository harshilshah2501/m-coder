# API documentation (index)

There is **no** single OpenAPI bundle under `docs/api/`. Contracts and entrypoints are **split by surface** — use the table below.

| Surface | Where |
|---------|--------|
| **RAG HTTP API** (implementation) | [`runtime/rag/src/api/rag_api.py`](../../runtime/rag/src/api/rag_api.py); deployment and curl examples in [docs/README.md](../README.md) (Quick Start) |
| **Plan-Gate HTTP** (PlanRequest v0.1) | [`runtime/plan_gate_service/README.md`](../../runtime/plan_gate_service/README.md) |
| **M3.3 execution gate** (pre-sandbox, in-process) | [`runtime/plangate/`](../../runtime/plangate/) — not the same as `plan_gate_service/`; see [runtime/README.md](../../runtime/README.md) |
| **IDE / plugin JSON contracts** | [`runtime/ide/schemas/`](../../runtime/ide/schemas/); spec [JETBRAINS_PLUGIN_FLOW_V0_1.md](../JETBRAINS_PLUGIN_FLOW_V0_1.md) |
| **Shadow / CI tooling** | [`runtime/shadow/schemas/`](../../runtime/shadow/schemas/), [`runtime/ci_gate/README.md`](../../runtime/ci_gate/README.md) |

**Operator wiring (archived copy):** [archive/guides/TEMP_MOTADATA_REPO_INTEGRATION_GUIDE.md](../archive/guides/TEMP_MOTADATA_REPO_INTEGRATION_GUIDE.md) — use golden path runbooks for current procedure.

**Tests:** Repo-root [`pytest.ini`](../../pytest.ini); primary runtime suite: `python3 -m pytest runtime/tests/`.

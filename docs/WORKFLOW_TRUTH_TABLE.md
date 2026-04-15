# WORKFLOW_TRUTH_TABLE — actual workflows

**Status tags:** `CANONICAL` (summary) · `IN_PRODUCT_SLICE` (HTTP/CLI path)  
**Last updated:** 2026-04-14  

**Layering:** Evidence-first flows use **Layer-5** (`POST /v1/export_evidence`) then **Layer-3** (`POST /v1/ask`, `/v0/plan`, `/v0/execute`). That is **not** the same as “five constitutional doctrine layers” — L5 here is **workspace intelligence**; see `docs/ARCHITECTURE_4_LAYER.md`.

| Workflow | Canonical path | Required components | Inputs | Outputs | Invariants | Failure modes | Status |
|----------|----------------|---------------------|--------|---------|------------|---------------|--------|
| **CLI evidence-first Ask** | `POST /v1/export_evidence` → build `ask_request.v1.0` → `POST /v1/ask` | Context Layer up; Plan-Gate up; `WORKSPACE_ROOT` visible to Context Layer | `workspace_root`, `query`, `top_k` | Plan-only response + `ask_path` metadata + `plan_summary` | Governance posture PLAN_ONLY unless contract says otherwise; evidence schema valid | Export 4xx/5xx; empty evidence; weak evidence flags | **CANONICAL** — primary CLI proof |
| **Compatibility Ask (v0)** | `POST /v0/ask` only | Plan-Gate; repo path resolution (`ASK_DEFAULT_REPO_ROOT` if needed) | v0 ask JSON | Plan-only response | Same posture rules | Server/repo mismatch | **COMPATIBILITY** — default IDE path |
| **Evidence-first fallback chain** | Plugin or client: export fails → documented v0 fallback | Same + client logic | N/A | v0 or error | **No silent** success on real HTTP failures with body | Unreachable vs contract error | **COMPATIBILITY** — see audit + Kotlin bridge |
| **Explain / Debug** | Optional export → `POST /v1/ask` with `task_type=EXPLAIN_DEBUG` | Plan-Gate; vLLM (`MOTADATA_EXPLAIN_VLLM_URL`) | Selection + file paths | `explain_debug` object or explicit error | `routing_mode=explain_debug` when applicable | vLLM down → structured error | **CANONICAL** |
| **Plan (commit governance)** | `POST /v0/plan` | Plan-Gate; policy | `plan_request.v0.1` | `decision_response.v0.1` | Non-empty decision field | REFUSAL / block states | **CANONICAL** |
| **Execute** | `POST /v0/execute` | Plan-Gate → execute_service → sandbox/integrity | execute request | execute response + honest `executed` | No fake success when blocked | Integrity import fail → blocked | **CANONICAL** |
| **Retrieval validation / B1** | Layer-5 retrieval + harness artifacts | Indexed workspace; deterministic policy | Goldens / perturbations | Reports under `docs/validation/artifacts/b1_retrieval_validation/` | PR-6 invariants preserved | Latency / drift warnings | **CANONICAL** — baseline locked, suite expanded |
| **L5.8 grounded Ask harness** | `runtime/layer5/audit` tooling | Same corpus discipline | Queries + thresholds | Markdown/JSON reports | No false regression on protected subset | Threshold failures | **CANONICAL** — gate closed per tracker |
| **Observability trace reconstruction** | Correlate `request_id` / `trace_id` across Context Layer, Plan-Gate, execute logs | Services emitting grep-stable lines | Action timestamps | End-to-end narrative | B4 closure | Missing log hooks | **CANONICAL** |
| **Stage 3 runtime loop burn-in** | `pytest runtime/tests/test_stage3_loop.py` + smokes in report | Loop controller, schemas, validators | Fixture configs | `STAGE3_BURN_IN_REPORT.md` artifacts | Bounded loop; no LLM-owned control | Test failure | **CANONICAL** — B7 closed |
| **Host profile smoke (A/B)** | Scripts + B5 checklists | WSL or native Linux backend; GPU reachable | Env files, tunnels | Artifact folders | Same HTTP contracts | Tunnel/GPU mismatch | **CANONICAL** — B5 closed |
| **JetBrains UI Ask / Execute** | Plugin → same HTTP endpoints | IDE + plugin build | User gestures | UI dialogs | Must mirror backend truth | UX contradiction | **DEFERRED_INTEGRATION** for **routine** validation |

---

## Cross-links

- Commands: `docs/CLI_VALIDATION_MATRIX.md`  
- Contract vs developer-utility validation: `docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md`, `docs/guides/MOTADATA_DEVELOPER_UTILITY_VALIDATION.md`  
- Scope: `docs/PRODUCT_SLICE.md`  
- Truth: `docs/SYSTEM_TRUTH.md`  

# CLI_VALIDATION_MATRIX — CLI-first proof map

**Status tags:** `CANONICAL` (operator) · `IN_PRODUCT_SLICE`  
**Last updated:** 2026-04-14  

Primary runbook: `docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md`. Developer-usefulness (heuristic) checks: `docs/guides/MOTADATA_DEVELOPER_UTILITY_VALIDATION.md`. **Layering:** Most rows are **Layer-3** (Plan-Gate) and/or **Layer-5** (Context Layer `export_evidence`); see `docs/ARCHITECTURE_4_LAYER.md`. This matrix is a **fast index** to entries, artifacts, and gates.

| Module / Path | CLI or HTTP entry | Scenario | Expected output (high level) | Proof artifact | Invariant / gate | Status | Notes |
|---------------|-------------------|----------|----------------------------|----------------|------------------|--------|-------|
| `runtime/context_layer_service/` | `GET {CONTEXT_URL}/healthz` | Stack health | HTTP 200, `status` ok | Preflight logs | Liveness | **CANONICAL** | Port default 8091 in guides |
| `runtime/plan_gate_service/` | `GET {PLAN_GATE_URL}/healthz`, `/version` | Service up | 200 + schema list | Verifier preflight | Contract discovery | **CANONICAL** | Default 8089 |
| GPU vLLM | `GET http://127.0.0.1:8000/v1/models` | Explain path available | Model list | Guide §3 | Debug quality | **CANONICAL** | When testing EXPLAIN_DEBUG |
| `runtime/scripts/motadata_behavior_verify.py` | `python3 runtime/scripts/motadata_behavior_verify.py --workspace-root <repo> --repeat 2` | Full smoke: query, debug, plan, code, agent probe | `all_pass: true`, `stable: true` | `runtime/.run/motadata_behavior_validation.json` (override `--out`) | End-to-end HTTP contracts | **CANONICAL** | **Primary** automated matrix |
| Same + scenarios | `--scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json` | Named expectations per capability | `scenario_suite.all_pass` | stdout + JSON | Regression suite | **CANONICAL** | `--scenarios-only` for speed |
| Same + utility scenarios | `--utility-scenarios docs/validation/motadata_developer_utility_scenarios.v1.json` (optional; with or without `--scenarios`) | Anchored Ask/Debug/Plan usefulness checks | `developer_utility_suite.all_pass` | stdout + JSON | Heuristic developer-utility layer | **CANONICAL** | Not a substitute for contract suite; see utility guide |
| `runtime/scripts/verify_ask_path.sh` | `WORKSPACE_ROOT=… QUERY=… bash runtime/scripts/verify_ask_path.sh` | Evidence export → `/v1/ask` | Script prints PASS | Transcript | Evidence-first Ask (B2 class) | **CANONICAL** | Tunnel-friendly |
| `runtime/scripts/cli_e2e_verify.sh` | Wraps `verify_ask_path.sh` | Same | PASS | Transcript | Thin wrapper | **CANONICAL** | Defaults workspace to repo root |
| Plan-Gate | `POST /v0/ask` | Compatibility Ask (no export) | Plan-only response shape | Verifier / curl | v0 path; dual-path reality | **COMPATIBILITY** | Default IDE path when evidence-first off |
| Plan-Gate | `POST /v1/ask` after export | Evidence-first Ask | `ask_path` / metadata | JSON report | v1 evidence path | **CANONICAL** | CLI primary |
| Plan-Gate | `POST /v1/ask` + `EXPLAIN_DEBUG` | Debug | `routing_mode=explain_debug`, summary or error | Verifier `debug` block | Explain vs planner | **CANONICAL** | vLLM required for “quality” |
| Plan-Gate | `POST /v0/plan` | Governance decision | `decision_response.v0.1` | Verifier `plan` | Plan contract | **CANONICAL** | |
| Plan-Gate | `POST /v0/execute` | Governed execute | `execute_response.v0.1`, honest `outcome` | Verifier `code` | Execute honesty | **CANONICAL** | May REFUSAL/BLOCKED |
| Plan-Gate | `GET /v0/agent` or probe | No agent route | 404 expected | Verifier `agent` | No public agent API | **CANONICAL** | As per verifier |
| `runtime/loop/` + tests | `python3 -m pytest runtime/tests/test_stage3_loop.py -v` | Stage 3 burn-in | All pass | `docs/validation/artifacts/stage3_pytest_output*.txt` | B7 closure | **CANONICAL** | See STAGE3_BURN_IN_REPORT |
| `scripts/wsl_plugin_mvp_stack.sh` | `up` / `check` | WSL stack | Healthy services | Host proof packs | B5 | **CANONICAL** | GPU tunnel optional |
| `runtime/scripts/run_local_stack.sh` | `start-plan-gate`, `start-context`, `health` | Local dev stack | Health OK | Local dev | Dev smoke | **COMPATIBILITY** | In verifier preflight |
| `runtime/scripts/governed_services.sh` | `start` / `status` | GPU host stack | Plan-Gate + vLLM up | Guide §3 | Demo stack | **CANONICAL** | GPU side |
| Observability | Grep logs for `REQUEST_ID`, `TRACE_ID`, `PLAN_GATE request` | Trace reconstruction | Cross-service correlation | `docs/guides/ACTION_5_OBSERVABILITY_CORRELATION.md`, proof packs | B4 | **CANONICAL** | Not replaced by UI |
| Host profiles | B5 artifact dirs | Native vs WSL | Same HTTP behavior | `docs/validation/artifacts/b5_*`, `B5_HOST_READINESS.md` | Host parity | **CANONICAL** | |
| L5.8 harness | `runtime/layer5/audit` pytest / CI | Grounded Ask metrics | Threshold reports | `docs/validation/artifacts/b1_retrieval_validation/`, L5.8 reports | B2 / retrieval | **CANONICAL** | PR-6 protected subset |

**JetBrains plugin:** **DEFERRED_INTEGRATION** as automated CLI matrix row — manual UI flows live under `docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md`, `docs/guides/JETBRAINS_PLUGIN_UI_FINAL_DEMO_RUNBOOK.md` (**COMPATIBILITY** / operator).

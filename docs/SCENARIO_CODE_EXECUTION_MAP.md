# SCENARIO_CODE_EXECUTION_MAP — scenarios → code surfaces

**Method:** Routes and imports traced in-repo (`runtime/plan_gate_service/app.py`, `runtime/context_layer_service/app.py`, `runtime/scripts/motadata_behavior_verify.py`). **CLI/HTTP-first**; JetBrains **DEFERRED_INTEGRATION** unless noted.

**Canonical posture:** `docs/LIVE_ROADMAP_TRACKER.md`, `docs/SYSTEM_TRUTH.md`, `docs/PRODUCT_SLICE.md`.

---

## Legend

| Proof | Meaning |
|-------|---------|
| **test** | `runtime/tests/` or `runtime/layer5/tests/` exercises module directly |
| **cli** | `runtime/scripts/motadata_behavior_verify.py` or `verify_ask_path.sh` hits live HTTP |
| **artifact** | Saved output under `docs/validation/artifacts/` or report markdown |
| **tracker** | Explicit closure row in `docs/LIVE_ROADMAP_TRACKER.md` |
| **inferred** | Logical path from imports; not separately proven in this matrix |

---

## Scenario table

| Scenario | Entry command / endpoint | Main runtime path | Key modules / files touched | Artifacts produced | Validation source | Status | Notes |
|----------|-------------------------|-------------------|------------------------------|-------------------|-------------------|--------|-------|
| **Evidence export** | `POST {CONTEXT}/v1/export_evidence` | `context_layer_service` HTTP → `evidence_api.export_evidence_bundle_dict` → Layer-5 retrieval/index | `runtime/context_layer_service/app.py`, `evidence_api.py`, `runtime/layer5/retrieval/`, `workspace_index_cache.py` | Bundle JSON (`schema_hint`), verifier `export_evidence` block | **cli** + **test** (`test_context_layer_service.py` subprocess/HTTP) | **ACTIVE_CANONICAL** | Packaging: `packaging/motadata-context-layer/` installs same API |
| **POST /v1/ask** (evidence-first) | `POST {PLAN_GATE}/v1/ask` | `plan_gate_service/app.py` → `assist_layer` (advisory) → `ask_service/v1_ingest.handle_ask_v1_request` → planner/reasoner/authority as routed | `runtime/plan_gate_service/app.py` (~316+), `runtime/ask_service/v1_ingest.py`, `planner.py`, `reasoner.py`, `handlers.py` (v0 shared patterns) | `motadata_behavior_validation.json`; `evidence_first_meta` | **cli** + **test** (`test_ask_v1_ingest.py` HTTP subprocess) | **ACTIVE_CANONICAL** | Primary CLI proof path |
| **POST /v0/ask** (compat) | `POST {PLAN_GATE}/v0/ask` | `app.py` → `_apply_assist_to_ask_payload` → `ask_service.handlers.handle_ask_request` | `runtime/plan_gate_service/app.py` (~267+), `runtime/ask_service/handlers.py`, `context/engine.py` | Verifier can focus on v1; v0 default for IDE when evidence-first off | **test** (`test_ask_service.py`, v0 semantics) + **inferred** live CLI (verifier emphasizes v1 for “query” check) | **ACTIVE_COMPATIBILITY** | Default plugin path per tracker; CLI matrix centers v1 for smoke |
| **POST /v0/execute** | `POST {PLAN_GATE}/v0/execute` | `app.py` → `execute_service.handlers.handle_execute_request` → integrity → `runtime/plangate` → sandbox/ledger | `runtime/plan_gate_service/app.py` (~386+), `runtime/execute_service/handlers.py`, `runtime/plangate/`, `runtime/sandbox/`, `runtime/integrity/` | Verifier `code` block; spool optional | **cli** + **test** (`test_execute_service.py`, `test_execute_service_plan_gate_boundary.py`) | **ACTIVE_CANONICAL** | **Not** `plan_gate_service/handlers.py` stub — real execute stack |
| **Explain / Debug** | `POST /v1/ask` + `task_type=EXPLAIN_DEBUG` | Same as v1 ask → routing to `reasoner.explain_debug` → optional vLLM `chat/completions` | `runtime/ask_service/reasoner.py`, env `MOTADATA_EXPLAIN_VLLM_URL` | Verifier `debug` block | **cli** + **test** (`test_reasoner_explain_debug_*.py`, `test_explain_debug_action6_proof.py`) | **ACTIVE_CANONICAL** | `app.py` `_vllm_healthcheck` if env set |
| **POST /v0/plan** (governance) | `POST {PLAN_GATE}/v0/plan` | `plan_gate_service/handlers.handle_plan_request` → `plan_gate_stub.rules.stub_decide` → spool | `runtime/plan_gate_service/handlers.py`, `runtime/plan_gate_stub/` | Spool JSON artifacts | **cli** (`motadata_behavior_verify.py` plan check) + **test** (indirect via HTTP in ask tests) | **ACTIVE_CANONICAL** | Stub decision logic; CI/spool semantics |
| **Retrieval validation harness (PR-6 / B1 / L5.8)** | pytest / harness APIs | `runtime/layer5/audit/l58_grounded_harness.py` + evaluators; lexical retrieval | `runtime/layer5/audit/*`, `runtime/layer5/retrieval/`, tests under `runtime/layer5/tests/test_l58_*.py` | `l58_grounded_report.*`, `docs/validation/artifacts/b1_retrieval_validation/` | **test** + **artifact** + **tracker** (B1/B2 closed) | **ACTIVE_CANONICAL** | Distinct from ad-hoc RAG FastAPI |
| **Stage 3 burn-in** | `python3 -m pytest runtime/tests/test_stage3_loop.py` | `runtime/loop/loop_controller.py` (`Stage3LoopController`) + `runtime/obs/ledger.py` + validators | `runtime/loop/`, `runtime/obs/`, `runtime/state/validators.py` | `docs/validation/artifacts/stage3_pytest_output*.txt`, `STAGE3_BURN_IN_REPORT.md` | **test** + **artifact** + **tracker** (B7) | **ACTIVE_CANONICAL** (impl) | **Not** wired to Plan-Gate HTTP by default — **inferred** no `Stage3LoopController` in `plan_gate_service/app.py` |
| **Trace reconstruction** | Log grep: `PLAN_GATE request`, `CONTEXT_LAYER` | Emission in `plan_gate_service/app.py` (`_plan_gate_request_log`), context layer app logging | `runtime/plan_gate_service/app.py`, `runtime/context_layer_service/app.py` | Proof packs in `docs/guides/ACTION_5_*`, `HOST_A_*` | **tracker** (B4) + **test** (`test_action5_observability.py`) | **ACTIVE_CANONICAL** | Correlation IDs in JSON body + logs |
| **Host-profile smoke (B5)** | `wsl_plugin_mvp_stack.sh`, `motadata_behavior_verify.py`, B5 checklists | Same HTTP paths; different host placement (WSL vs native Linux) | Scripts under `runtime/scripts/`, `scripts/` | `docs/validation/artifacts/b5_*`, `B5_HOST_READINESS.md` | **artifact** + **tracker** (B5 closed) | **ACTIVE_CANONICAL** | Tunnel to GPU is env-specific |
| **No-match / insufficiency** | `/v1/ask` with weak or empty evidence | `v1_ingest` + metadata (`evidence_quality`, `quality_reasons`) + Layer-5 honesty paths | `runtime/ask_service/v1_ingest.py`, `runtime/layer5/` | L5.8 nomatch tests; verifier may show `WEAK` + reasons | **test** (`test_l58_nomatch_honesty_slice.py`) + **cli** (metadata fields) | **PARTIALLY_VALIDATED** → **CLOSED** per tracker | Full product UX for “empty” is **DEFERRED_INTEGRATION** (plugin) |

---

## Explicit non-scenarios (avoid confusion)

| Item | Reality |
|------|---------|
| **HTTP → `Stage3LoopController`** | **Not present** in `plan_gate_service/app.py` — Stage 3 is **pytest + follow-on product wiring** per tracker |
| **`archive/legacy_runtime_rag/` orchestrator as JetBrains path** | **OUT_OF_PRODUCT_SLICE** primary bridge — parallel stack |
| **JetBrains UI click path** | **DEFERRED_INTEGRATION** for this map — ends at same HTTP as CLI when configured |

---

## Follow-on vs closed

| Topic | Evidence |
|-------|----------|
| MVP slice HTTP contracts | **Closed** — tracker + Action 14 + CLI verifier |
| IDE → Stage3 live loop | **Follow-on only** — `docs/guides/STAGE3_BURN_IN_AND_E2E_DEMO.md` §7 |

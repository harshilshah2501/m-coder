# End-to-End System Audit Report — Motadata AI Coding Assistant (m-coder)

**Audit mode:** READ-ONLY mapping of repository state as of **2026-03-23**.  
**Evidence:** File paths, symbols, and commands cited below. Inferences are explicitly labeled.

**Repository:** `/home/harshil/Harshil-PoCs/m-coder`  
**Current branch:** `feature/l5-context-layer-v1-ask-packaging` (tracks `origin/feature/l5-context-layer-v1-ask-packaging`).  
**HEAD:** `fead099` (`build(packaging): add WSL context-layer deploy pipeline and CI workflow`).  
**`main`:** `0d8dbf4` — **ancestor of HEAD** (merge-base `0d8dbf4` = `main`); feature branch is **ahead** of `main` by ~30+ commits (see `git log main..HEAD`).

**Untracked (local):** `packaging/motadata-context-layer/.venv-build-pipeline/`, `packaging/motadata-context-layer/.venv-smoke-pipeline/` (git status at audit time).

---

## 1. Executive summary

The m-coder repo implements a **governed runtime stack** centered on a **stdlib HTTP Plan-Gate** (`runtime/plan_gate_service/app.py`) that exposes **POST `/v0/plan`**, **POST `/v0/ask`**, **POST `/v1/ask`**, **POST `/v0/execute`**, **GET `/healthz`**, **GET `/version`**. The JetBrains plugin (`jetbrains-plugin/`) is a **hardcoded client** to **`http://127.0.0.1:8089`** via `RuntimeBridge` (`jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/bridge/RuntimeBridge.kt` — default `baseUrl`). **Ask** is **plan-only** (`governance_posture` / `execution` invariants enforced in `runtime/ask_service/handlers.py`).

**Layer-5 Context Layer** is packaged as **`motadata-context-layer`** (`packaging/motadata-context-layer/pyproject.toml`) and serves **GET `/healthz`**, **GET `/version`**, **POST `/v1/export_evidence`** (`runtime/context_layer_service/app.py`). Evidence export delegates to lexical retrieval (`runtime/layer5/retrieval/lexical.py`) and `evidence_api.export_evidence_bundle_dict` (`runtime/context_layer_service/evidence_api.py`).

**Evidence-first Ask** (plugin → Context Layer → `/v1/ask`) is **opt-in** via JVM property `motadata.ask.evidence_first=true` or env `MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST=1` (`jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/ask/MotadataAskFlags.kt`). Default is **v0 Ask only** (`evidenceFirst = false` in `RuntimeRequest.kt`).

**GPU / vLLM** is operationalized by `runtime/scripts/governed_services.sh` (vLLM on configurable port, default **8000**; Plan-Gate **8089**). Plan-Gate **main** runs `_vllm_healthcheck()` if `MOTADATA_EXPLAIN_VLLM_URL` is set (`runtime/plan_gate_service/app.py`). **Explain/Debug** uses `MOTADATA_EXPLAIN_VLLM_URL` + `MOTADATA_EXPLAIN_MODEL` (`runtime/ask_service/reasoner.py`).

**Brutal honesty:** Multiple **parallel “architectures”** exist in repo (RAG FastAPI, ML training APIs, `workspace_intelligence/spikes/`, legacy docs). The **live vertical slice** for JetBrains + Plan-Gate + Ask + Context Layer is **narrow and identifiable** in the paths above; other trees are **supporting, experimental, or legacy** unless explicitly wired into `RuntimeBridge` / Plan-Gate.

---

## 2. System reality map

| Concern | Implemented location | Transport | Notes |
|--------|----------------------|-----------|--------|
| IDE → Plan-Gate | `RuntimeBridge` | HTTP JSON | Default `127.0.0.1:8089` |
| Plan-Gate → Ask v0/v1 | `runtime/plan_gate_service/app.py` | In-process POST | Routes to `handle_ask_request` / `handle_ask_v1_request` |
| Ask → context | `runtime/ask_service/handlers.py` | `ContextEngine`, manifest selector | `ASK_DEFAULT_REPO_ROOT` for cross-OS paths |
| Ask → Evidence v1 | `runtime/ask_service/v1_ingest.py` | No repo FS reads on v1 path | `evidence_first_meta.ask_path = v1_evidence` |
| Plugin → Context Layer | `Layer5EvidenceExporter` | POST `/v1/export_evidence` | Default `http://127.0.0.1:8091` |
| Explain/Debug | `explain_debug()` in `reasoner.py` | POST `{vllm}/v1/chat/completions` | Requires bundle + EXPLAIN_DEBUG |
| Execute | `runtime/execute_service/handlers.py` | Plan-Gate `/v0/execute` | Imports may fail → blocked response |
| Governance script | `runtime/scripts/governed_services.sh` | bash | vLLM + Plan-Gate lifecycle |

---

## 3. Directory layout audit

### Top-level (confirmed: `find . -maxdepth 2 -type d`)

| Directory | Purpose | Active / status |
|-----------|---------|-------------------|
| `runtime/` | Core services: Plan-Gate, Context Layer, ask/execute, layer5, sandbox, plangate, tests | **Active** for product slice |
| `jetbrains-plugin/` | IntelliJ plugin (Kotlin) | **Active** |
| `packaging/motadata-context-layer/` | Wheel + WSL build/verify scripts | **Active** |
| `docs/` | Architecture, runbooks, demos, audits | **Active** (mixed freshness) |
| `docs/audit/` | Historical audits + path governance | **Archive-heavy**; many phase reports |
| `ml/` | Training, evaluation, datasets | **Active** for ML pipeline; not required for JetBrains slice |
| `workspace_intelligence/` | Spikes (`spikes/grounded_retrieval.py`, harness) | **Research / spike** — not the packaged Layer-5 path |
| `observation/` | Drift / observation tooling | **Separate** concern |
| `tests/` | Repo-level tests (if present) | Verify per CI |
| `.venv/` | Local Python env | **Local** (not canonical) |

### Duplicate / overlapping areas

- **`runtime/rag/`** — FastAPI RAG API (`runtime/rag/src/api/rag_api.py` has `/health`, `/search/semantic`). **Not** the same as Plan-Gate or Context Layer HTTP. **Parallel stack.**
- **`runtime/plangate/`** (`PlanGateService`) — Used by **execute** path (`runtime/execute_service/handlers.py` imports). **Different** from `runtime/plan_gate_service/app.py` HTTP server (naming overlap).
- **`workspace_intelligence/spikes/`** vs **`runtime/layer5/`** — Spike retrieval vs **packaged** Layer-5 implementation.

### Key entry files

- Plan-Gate HTTP: `runtime/plan_gate_service/app.py` — `main()`, `PlanGateHandler`
- Context Layer HTTP: `runtime/context_layer_service/app.py` — `main()`, `ContextLayerHandler`
- Ask: `runtime/ask_service/handlers.py` — `handle_ask_request`; `runtime/ask_service/v1_ingest.py` — `handle_ask_v1_request`
- Plugin: `jetbrains-plugin/src/main/resources/META-INF/plugin.xml`; `RuntimeBridge.kt`

---

## 4. Runtime flow audit

### 4.1 JetBrains plugin request path

- **Entry:** `AnAction` subclasses — `AskMotadataAiAction`, `SubmitToRuntimeAction`; VCS — `MotadataCheckinHandler` (`jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/vcs/MotadataCheckinHandler.kt`).
- **Bridge:** `RuntimeBridge` (`RuntimeBridge.kt`) — default **`http://127.0.0.1:8089`**, timeout **5000 ms**.
- **Endpoints used:**
  - Commit: **POST `/v0/plan`**
  - Ask: **POST `/v0/ask`** or **POST `/v1/ask`** (evidence-first path)
  - Execute: **POST `/v0/execute`**
  - Health: **GET `/healthz`** (`isRuntimeAvailable()`)

### 4.2 Context Layer request handling

- **Entry:** `python -m runtime.context_layer_service` or console script `motadata-context-layer` (`pyproject.toml` → `runtime.context_layer_service.cli:main`).
- **POST `/v1/export_evidence`:** JSON `workspace_root`, `query`, `top_k` → `export_evidence_bundle_dict` (`evidence_api.py`).

### 4.3 `evidence_bundle` generation

- **HTTP:** `export_evidence_bundle_dict` → `WorkspaceResolver` → `build_file_index` → `retrieve_lexical` → `build_evidence_bundle` (`evidence_api.py` lines 31–46).
- **Ask v0 evidence-first (server-side):** `try_build_layer5_evidence` in `evidence_bridge` (from `handlers.py` when `evidence_first` and workspace path resolves) — **not** the same as the plugin’s HTTP export path.

### 4.4 Plan-Gate request handling

- **Class:** `PlanGateHandler` in `app.py`.
- **GET** `/healthz`, `/version` — **no POST routing** for unknown paths → 404.

### 4.5 v0 Ask path

- **HTTP:** POST `/v0/ask` → `handle_ask_request` (`handlers.py`).
- **Inputs:** `ask_request.v0.1` (validated `validate_ask_request` / `ask_request.v0.1.schema.json`).
- **Flow:** `ContextRequest` + `ContextEngine.build_context_bundle` OR manifest + `select_from_manifest`; optional Layer-5 evidence when `evidence_first`; `PlanOnlyPlanner` or `explain_debug`.
- **Critical env:** `ASK_DEFAULT_REPO_ROOT` (`handlers.py` `_resolve_ask_repo_root`), `MOTADATA_EXPLAIN_VLLM_URL`, `MOTADATA_EXPLAIN_MODEL` (explain path).

### 4.6 v1 Ask path

- **HTTP:** POST `/v1/ask` → `handle_ask_v1_request` (`v1_ingest.py`).
- **Inputs:** `ask_request.v1.0` + embedded `evidence_bundle` — `validate_ask_v1_request`.
- **Schema:** `evidence_bundle` validated via `validate_evidence_bundle_dict` (`runtime/layer5/evidence/schema_validate.py`).
- **Output:** `_build_plan_only_response` with `evidence_first_meta.ask_path = "v1_evidence"` and `ingestion_meta` in `v1_ingest.py` lines 138–155.

### 4.7 Debug / Explain path

- **Trigger:** `task_type == "EXPLAIN_DEBUG"` and `selected_file` and (`selection` or bundle items) — `handlers.py` ~194–200; same for v1 in `v1_ingest.py` ~121–132.
- **Implementation:** `explain_debug()` in `reasoner.py` — POST to `{base}/v1/chat/completions`, model from `MOTADATA_EXPLAIN_MODEL` (default `motadata-coder`).
- **Plugin UI:** When `explain_debug` key present in response metadata, `AskMotadataAiAction.showPlanOnlyResult` renders **Explain/Debug** section — **does not** show standard plan/context layout for that branch (`AskMotadataAiAction.kt` lines 116–158).

### 4.8 Code / Execute path

- **HTTP:** POST `/v0/execute` → `handle_execute_request` (`execute_service/handlers.py`).
- **Behavior:** Normalization → `DeterministicGuard` → `PlanGateService` → `SandboxExecutor` when imports succeed; **if integrity imports fail**, returns **BLOCKED** with message “Runtime integrity layer is not configured” (`handlers.py` ~95–106).

### 4.9 vLLM invocation path

- **Explain:** `reasoner.py` — OpenAI-compatible **chat completions**.
- **Governed start:** `governed_services.sh` starts `python -m vllm.entrypoints.openai.api_server` or `vllm serve` with LoRA (lines 212–230).
- **Plan-Gate startup:** `_vllm_healthcheck()` in `plan_gate_service/app.py` — GET `{MOTADATA_EXPLAIN_VLLM_URL}/v1/models` **only if** `MOTADATA_EXPLAIN_VLLM_URL` is set.

### 4.10 Deterministic planner vs LLM

- **Deterministic:** `PlanOnlyPlanner` (`runtime/ask_service/planner.py`) — template steps from query + bundle paths; **no LLM**.
- **LLM:** `explain_debug` only for EXPLAIN_DEBUG task type (`reasoner.py`).

### 4.11 Fallback behavior

- **Plugin evidence-first:** `RuntimeBridge.callAskEndpoint` → if Context Layer unreachable, **POST `/v0/ask`** with `evidence_first: true` (`RuntimeBridge.kt` ~161–165). If HTTP export returns **ServiceFailure**, **no** fallback (returns error). **v1** 404/405 → fallback to v0; **v1** 400 with contract codes (`AskV1Contract.NO_FALLBACK_ERROR_CODES`) → **no** fallback (`AskV1Contract.kt`, `RuntimeBridge.kt` ~182–196).
- **Ask v0 evidence-first server-side:** If Layer-5 build fails, falls back to `ContextEngine` path (`handlers.py` ~171–182).

### 4.12 Metadata / UI

- **Plugin:** Parses `context_bundle`, `plan_summary`, `evidence_bundle`, `evidence_first_meta`, `explain_debug` into `RuntimeResponse.metadata` (`RuntimeBridge.kt` `parseAskResponse`).
- **UI:** Swing `Messages.showInfoMessage` in `AskMotadataAiAction` — **no custom editor tool window.**

---

## 5. JetBrains plugin audit

### 5.1 Actions (from `plugin.xml`)

| Action | ID | Menu |
|--------|-----|------|
| Ask Motadata AI | `ai.motadata.plugin.actions.AskMotadataAiAction` | Tools |
| Submit to Runtime | `ai.motadata.plugin.actions.SubmitToRuntimeAction` | Tools |
| **Implicit:** Commit check-in | `MotadataCheckinHandlerFactory` | extension |

**Not registered:** Command palette-specific shortcuts — only **Tools** menu; **no `<keyboard-shortcut>`** in `plugin.xml` (confirmed file contents).

### 5.2 Ask path behavior

- **Evidence-first OFF (default):** `RuntimeBridge` → **POST `/v0/ask`** only (`RuntimeBridge.kt` ~147–148).
- **Evidence-first ON:** Try Layer-5 export → **POST `/v1/ask`**; fallback chain as above.

### 5.3 Context Layer URL

- **`Layer5EvidenceExporter.resolveContextLayerBaseUrl()`:** `motadata.context_layer.url` **or** `MOTADATA_CONTEXT_LAYER_URL` **or** default **`http://127.0.0.1:8091`** (`Layer5EvidenceExporter.kt` ~62–65).

### 5.4 Plan-Gate URL

- **Hardcoded** in `RuntimeBridge`, `PlanGateClient`, `AskClient`: **`http://127.0.0.1:8089`** — **no** env or property in Kotlin for base URL (confirmed grep targets: `RuntimeBridge.kt` line 39, `PlanGateClient.kt` 26, `AskClient.kt` 36).

### 5.5 Rendering v1 evidence

- Shows `evidence_bundle.entries` with `relative_path` and snippet preview (first 5 lines) when `evidence_bundle != null` (`AskMotadataAiAction.kt` ~176–205).
- When `v1_evidence`, **omits duplicate** `context_bundle` file list (`AskMotadataAiAction.kt` ~209–231).

### 5.6 Rendering v0

- Shows `context_bundle` files when `!v1EvidenceAsk` (`AskMotadataAiAction.kt` ~209–224).

### 5.7 `plan_summary.notes`

- **Backend:** `_build_plan_only_response` sets `plan_summary["notes"]` for ungrounded files or repo-aware notes (`handlers.py` ~275–282).
- **Plugin UI:** **Does not render `notes`** — only iterates `plan_summary["steps"]` (`AskMotadataAiAction.kt` ~236–246). **Gap:** notes are **dropped in UI**.

### 5.8 `(no files selected)`

- **Source:** `AskMotadataAiAction.kt` lines 214–215 when `context_bundle.files` is **empty** — **not** a literal string from backend; it is **UI text** when the list is empty.

### 5.9 Editor-aware integration

- **Implemented:** `selectedFile` repo-relative, `selection` text, `taskType` EXPLAIN_DEBUG when selection + file present (`AskMotadataAiAction.kt` ~62–78).
- **Missing / shallow:** No PSI/AST integration, no multi-file structure, no caret-offset semantics beyond `selectionText` — **string-only** context.

### 5.10 Dead / legacy client code

- **`AskClient.kt`** — defines `AskClient` with `http://127.0.0.1:8089/v0/ask`; **grep shows no other references** in plugin (only self). **Likely obsolete** relative to `RuntimeBridge`.

---

## 6. Context Layer audit

### 6.1 Package structure

- **`pyproject.toml`:** `packages.find` from `../..` includes `runtime.layer5` + `runtime.context_layer_service` — **monorepo-relative layout** during development.

### 6.2 Build / verify / deploy

- **Script:** `packaging/motadata-context-layer/build_and_verify_wsl_context_layer.sh` (referenced in README and CI).
- **CI:** `.github/workflows/wsl-context-layer-package.yml` — runs that script on **push/PR** to paths under `packaging/motadata-context-layer`, `runtime/context_layer_service`, `runtime/layer5`, uploads **wheel** artifact.

### 6.3 Endpoints

- **GET `/healthz`**, **GET `/version`**, **POST `/v1/export_evidence`** (`app.py`).

### 6.4 Logging

- **`logging_setup`:** `MOTADATA_CONTEXT_LAYER_LOG_LEVEL`, `MOTADATA_CONTEXT_LAYER_LOG_PATH` (README); `log_message` delegates to logger at DEBUG (`app.py` ~149–151).

### 6.5 Index / evidence schema

- **Schema files:** `runtime/layer5/evidence/evidence_bundle.v1.schema.json`, `evidence_bundle.v1.md` (packaged per `pyproject.toml`).

### 6.6 Retrieval / ranking

- **Lexical-only:** Integer scoring path/basename/content counts (`lexical.py` module docstring lines 4–23). **Symbol boost: not used** (line 25–26).

### 6.7 Weaknesses (code-documented + logical)

- **Test / high-token files:** Content substring counts can overweight large files.
- **Stopwords / short tokens:** Tokens shorter than 3 characters are dropped in `normalize_query` path (see `handlers.py` `_extract_symbol_hints` and planner tokenization).
- **Lexical-only:** No embedding / semantic retrieval in `retrieve_lexical`.
- **Empty query:** All scores 0 → top-k is **first k paths in lexicographic order** (`lexical.py` lines 22–23).

### 6.8 Deployment assumptions

- **WSL:** Documentation and packaging README emphasize **WSL** (`packaging/motadata-context-layer/README.md` title).
- **Cross-OS:** Plugin may send **Windows** `repo_root`; Ask v0 uses `ASK_DEFAULT_REPO_ROOT` on server (`handlers.py`).

---

## 7. GPU stack audit

### 7.1 vLLM startup

- **`governed_services.sh`:** Starts vLLM on **127.0.0.1:{VLLM_PORT}** (default 8000), logs to `runtime/.run/vllm.log`, PID `runtime/.run/vllm.pid`.

### 7.2 Plan-Gate startup

- Same script: `python3 -m runtime.plan_gate_service.app` from **repo root**, log `runtime/.run/plan_gate.log`, PID `plan_gate.pid`.

### 7.3 Config

- **`runtime/config/demo_stack.env`** (required copy from `demo_stack.env.example` per script comments).

### 7.4 LoRA / adapter

- If `ADAPTER_PATH` set and `VLLM_CMD` exists, uses **`vllm serve`** with `--enable-lora` (`governed_services.sh` ~212–218).

### 7.5 Explain / Debug

- Env `MOTADATA_EXPLAIN_VLLM_URL` (default `http://127.0.0.1:$VLLM_PORT` in script), `MOTADATA_EXPLAIN_MODEL`.

### 7.6 Execution path

- **Sandbox** via `execute_service` — **not** the same as vLLM; requires integrity imports.

### 7.7 Health checks

- **Script `status`:** curl Plan-Gate `/healthz`, vLLM `/v1/models`.
- **Plan-Gate process start:** optional vLLM check **only if** `MOTADATA_EXPLAIN_VLLM_URL` set in environment when launching `app.py` directly.

### 7.8 Mandatory vs optional

- **Mandatory for governed_services start:** `VLLM_BASE_MODEL` local path exists.
- **Optional:** LoRA `ADAPTER_PATH`; `ASK_DEFAULT_REPO_ROOT` for cross-host Ask.

---

## 8. Endpoint inventory

| Method | Path | Service | Host | Caller | Status |
|--------|------|---------|------|--------|--------|
| GET | `/healthz` | Plan-Gate HTTP | GPU (or wherever Plan-Gate runs) | Plugin, scripts | **Active** |
| GET | `/version` | Plan-Gate HTTP | same | Plugin `getRuntimeVersion` | **Active** |
| POST | `/v0/plan` | Plan-Gate | same | Plugin commit, `PlanGateClient` | **Active** |
| POST | `/v0/ask` | Plan-Gate | same | `RuntimeBridge`, `AskClient` (legacy) | **Active** |
| POST | `/v1/ask` | Plan-Gate | same | `RuntimeBridge` (evidence-first) | **Active** |
| POST | `/v0/execute` | Plan-Gate | same | `RuntimeBridge` execute | **Active** |
| GET | `/healthz` | Context Layer | WSL/Linux host | Scripts, operators | **Active** |
| GET | `/version` | Context Layer | same | CI verify | **Active** |
| POST | `/v1/export_evidence` | Context Layer | same | `Layer5EvidenceExporter` | **Active** |
| GET | `/v1/models` | vLLM OpenAI | GPU | `governed_services.sh`, health | **Active** |
| POST | `/v1/chat/completions` | vLLM OpenAI | GPU | `reasoner.explain_debug` | **Active** |
| GET | `/health` | RAG FastAPI | separate deployment | Unknown in this slice | **Parallel / not wired to plugin** |

**Hidden / legacy:** RAG `/search/semantic`, orchestrator `/generate` (`runtime/rag/src/run_orchestrator.py`) — **not** part of JetBrains bridge.

---

## 9. Logging / observability audit

| Component | Log location | Access / verbosity |
|-----------|--------------|---------------------|
| Plan-Gate HTTP | **stderr** of process; `governed_services.sh` redirects to `runtime/.run/plan_gate.log` | `log_message` **disabled** (`pass` in `app.py` ~160–161) |
| Context Layer | **stderr** + optional `MOTADATA_CONTEXT_LAYER_LOG_PATH` | Per `logging_setup` |
| vLLM | `runtime/.run/vllm.log` | Full server output |
| Plugin | `DecisionLogger` (`jetbrains-plugin/.../logging/DecisionLogger.kt`) | VCS / execute actions |

**Trace gaps:** Plan-Gate HTTP **does not log requests**; no request ID propagation from plugin to logs on server (plugin uses `requestId` in JSON only).

---

## 10. Git / branch / merge audit

- **Branch:** `feature/l5-context-layer-v1-ask-packaging` (tracking origin).
- **Ahead of `main`:** Yes — `main` at `0d8dbf4` is **ancestor** of HEAD `fead099`.
- **Recent feature commits (sample):** `fead099` packaging/CI; `aec4763` governed services; `ceb8164` context fix; `2218c4f` L5 wheel + v1 Ask + plugin.
- **Docs/code alignment:** L5 + packaging docs **on the same branch** as implementation for this line of work; **`main` lacks** these commits until merged.

---

## 11. Documentation audit

| Class | Examples |
|-------|----------|
| **Canonical-current (for this slice)** | `packaging/motadata-context-layer/README.md`, `runtime/plan_gate_service/README.md`, `docs/runtime/` WSL client docs if present |
| **Active-supporting** | `docs/MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md`, `docs/MOTADATA_DEMO_SETUP_RUNBOOK.md`, `LIVE_ROADMAP_TRACKER.md` |
| **Stale / historical** | `docs/audit/*` phase reports (PHASE_15*, BATCH_*) |
| **Duplicate / overlapping** | Multiple architecture markdowns under `docs/architecture/` vs `docs/MOTADATA_*` |

**Classification is judgmental;** verify each doc against code before treating as spec.

---

## 12. Workflow / script audit

| Script | Purpose | Validity |
|--------|---------|----------|
| `runtime/scripts/governed_services.sh` | start/stop/restart/status vLLM + Plan-Gate | **Current** (matches repo layout) |
| `runtime/scripts/verify_ask_path.sh` | Context Layer → `/v1/ask` curl verification | **Current**; requires `WORKSPACE_ROOT`, `QUERY` |
| `packaging/.../build_and_verify_wsl_context_layer.sh` | Wheel + smoke + HTTP checks | **CI-backed** |
| `runtime/scripts/layer5_export_evidence.py` | Dev fallback for plugin CLI path | **Opt-in** (`MOTADATA_CONTEXT_LAYER_DEV_REPO_SCRIPT_FALLBACK`) |
| `scripts/verify_artifact_hygiene.sh` | Artifact hygiene | Separate concern |

---

## 13. Demo-readiness audit

| Scenario | Backend | Plugin UI | Risk |
|----------|---------|-------------|------|
| Ask v0 | Plan-Gate + repo on server or `ASK_DEFAULT_REPO_ROOT` | Works; may show empty context | **Windows path mismatch** without `ASK_DEFAULT_REPO_ROOT` |
| Evidence-first | Context Layer + Plan-Gate `/v1/ask` | Needs JVM/env flag | **Operator must enable flag** |
| Explain/Debug | vLLM + selection + file | Dedicated dialog branch | **vLLM must be up**; model must return JSON |
| Plan | Deterministic steps | Steps shown | **Notes not shown** |
| Code / Execute | `/v0/execute` + integrity | Dialog | **May block** if imports fail |
| No-match honesty | `plan_summary` notes in API | **Not in UI** | **Demo may look “silent”** |

---

## 14. Host-profile audit

| Assumption | Evidence |
|------------|----------|
| **localhost** | `127.0.0.1` defaults in `RuntimeBridge`, `PlanGateClient`, `Layer5EvidenceExporter`, `governed_services.sh`, `run_server` Plan-Gate binds **`127.0.0.1`** only (`app.py` line 168) |
| **WSL** | Packaging README, verify scripts |
| **Linux remote GPU** | `ASK_DEFAULT_REPO_ROOT`, `DEPLOY_TARGET` in packaging README — **partial** story |
| **Generalization gap** | No plugin-side configurable Plan-Gate URL; Context Layer URL **is** configurable |

---

## 15. Key inconsistencies / risks

1. **`PlanGate` naming:** HTTP `plan_gate_service` vs `runtime/plangate/plangate_service.py` — **two different concepts**.
2. **`AskClient.kt`:** Unused; duplicates `RuntimeBridge` behavior.
3. **Plan-Gate binds only `127.0.0.1`:** Not reachable from other hosts without tunnel/port forward.
4. **`plan_summary.notes`:** Returned by API but **not rendered** in plugin.
5. **Execute path:** May report integrity “not configured” if imports fail — **surprising** in demo.
6. **RAG / orchestrator:** **Large** codebase; **not** integrated with JetBrains bridge — **risk of confusion** for operators.

---

## 16. What is canonical right now

- **JetBrains integration point:** `RuntimeBridge.kt` + `plugin.xml` actions.
- **Ask contracts:** `runtime/ide/schemas/ask_request.v0.1.schema.json`, `ask_request.v1.0.schema.json` (referenced in handlers).
- **Evidence schema:** `layer5.evidence_bundle.v1` via `schema_validate` + JSON schema files.
- **Context Layer package:** `motadata-context-layer` **0.1.0** (`pyproject.toml`).

---

## 17. What is obsolete but still present

- **`AskClient.kt`** — likely superseded by `RuntimeBridge`.
- **Historical audit docs** in `docs/audit/` (phase batches) — **superseded** by process, not deleted.
- **RAG orchestrator scripts** — status unverified vs current demo; **parallel**.

---

## 18. Recommended next decisions (read-only)

1. **Merge policy:** Decide when to merge `feature/l5-context-layer-v1-ask-packaging` → `main` (currently **ahead**).
2. **Single source of truth** for operator docs: pick one architecture doc per slice or link index.
3. **Plugin configuration:** Plan-Gate base URL (env) vs hardcoded `127.0.0.1:8089`.
4. **UI parity:** Surface `plan_summary.notes` or remove from API contract.
5. **Dead code:** Remove or wire `AskClient` in a follow-up (not done in audit).

---

## 19. Appendix: file/path inventory and evidence

### A. Critical source files (non-exhaustive)

- `runtime/plan_gate_service/app.py` — `PlanGateHandler`, `_vllm_healthcheck`, `run_server`
- `runtime/plan_gate_service/config.py` — `PLAN_GATE_PORT`, `PLAN_GATE_SPOOL_DIR`
- `runtime/ask_service/handlers.py` — `handle_ask_request`, `_build_plan_only_response`
- `runtime/ask_service/v1_ingest.py` — `handle_ask_v1_request`
- `runtime/ask_service/reasoner.py` — `explain_debug`, `ExplainDebugResult`
- `runtime/context_layer_service/app.py` — HTTP server
- `runtime/context_layer_service/evidence_api.py` — `export_evidence_bundle_dict`
- `runtime/layer5/retrieval/lexical.py` — `retrieve_lexical`
- `jetbrains-plugin/.../RuntimeBridge.kt` — `callAskEndpoint`, `parseAskResponse`
- `jetbrains-plugin/.../Layer5EvidenceExporter.kt` — HTTP export
- `jetbrains-plugin/.../AskMotadataAiAction.kt` — UI
- `runtime/scripts/governed_services.sh` — process lifecycle

### B. Commands run (audit)

```text
git branch -a; git status -sb; git log -5 --oneline
git log main..HEAD --oneline | head -30
git merge-base main HEAD; git rev-parse main HEAD
find . -maxdepth 2 -type d
```

### C. Inference vs confirmed

| Claim | Type |
|-------|------|
| HTTP endpoints and handlers | **Confirmed** from source |
| `AskClient` unused | **Confirmed** (grep only self-reference) |
| RAG not used by plugin | **Confirmed** (no imports in `jetbrains-plugin/`) |
| “Obsolete” for docs in `docs/audit/` | **Inference** (historical naming) |

---

*End of report.*

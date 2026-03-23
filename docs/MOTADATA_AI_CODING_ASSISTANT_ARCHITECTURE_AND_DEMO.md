# Motadata AI Coding Assistant — Architecture, Flows, and Demo Guide

**Location:** `docs/MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE_AND_DEMO.md` — operator runbook (Windows / WSL / GPU).  
**Aligned branch:** `feature/l5-context-layer-v1-ask-packaging` (2026-03).

**Deterministic setup:** use **§6** (three roles: GPU-server, WSL, Windows). Follow steps in **§6.4** order unless you are doing single-host dev.

---

## Terminology / Roles

| Term | Meaning |
|------|---------|
| **m-coder repo** | Assistant / control-plane / build **source** — Plan-Gate, schemas, packaging, plugin sources. **Lives on GPU-server** (clone). **Not** the indexed application codebase. |
| **Workspace repo (Motadata AIOps)** | Target **application** repository — **indexed and read by Context Layer** in WSL. **Clone in WSL** (Linux filesystem). **Not** the same git remote as m-coder unless you intentionally use one repo for both (not required). |
| **Context Layer** | Packaged Python wheel (`motadata-context-layer`) **installed in WSL**; HTTP service for `/v1/export_evidence`. **Does not** require an m-coder checkout on WSL. |
| **Plan-Gate** | GPU backend HTTP service — **`POST /v1/ask`** (evidence-first), **`POST /v0/ask`**, etc. Runs from **m-coder** checkout on GPU. |
| **Plugin** | Windows JetBrains client — HTTP only; no local L5. |

**Repo placement (non-negotiable):**

| Location | Repository |
|----------|------------|
| GPU-server | **m-coder** only (for Plan-Gate + optional wheel build) |
| WSL | **Motadata AIOps** workspace repo (data plane) + **wheel install** (no m-coder requirement) |
| Windows (optional) | m-coder **only** if you build the plugin from source; not required for runtime |

---

## 1. Purpose of the system

The Motadata AI Coding Assistant is a **governed** coding assistant: the runtime (not the IDE plugin) owns **planning, boundaries, and execution posture**. The IDE is a **client** that submits intents and displays outcomes.

Core promises for the Ask path:

- **Plan-only by default** for Ask (`governance_posture: PLAN_ONLY`, `execution: false`).
- **Evidence-first** mode uses a **frozen** `layer5.evidence_bundle.v1` payload and **`POST /v1/ask`** on Plan-Gate when the WSL Context Layer is available.
- **No silent downgrade** when the Context Layer is **configured but returns errors** (HTTP/CLI failure with a body); only **unreachable** service is allowed to fall back to legacy `/v0/ask` with `evidence_first`.

---

## 2. Layered architecture (high level)

| Layer | Role | Notes |
|-------|------|--------|
| **L1** | Governance doctrine | Constitutional phases (REF, CONF, DES, etc.), boundaries, dominance — **locked**; not reimplemented in the plugin. |
| **L2** | ML / compilation | Training-grade dataset and SFT; separate from day-to-day IDE Ask. |
| **L3** | Runtime enforcement | Plan-Gate, context engine, sandbox, ledger, loop orchestrator — **m-coder repo on GPU** (or dev machine). |
| **L4** | Observation / drift | Ledger ingestion, metrics — downstream of runtime behavior. |
| **L5** | Workspace intelligence | Deterministic **file index**, **lexical retrieval**, **evidence bundle v1** — **Context Layer wheel in WSL** reads the **Motadata AIOps workspace repo**; **no m-coder checkout on WSL**. |

**Deployment split (target model):**

| Location | What runs |
|----------|-------------|
| **Windows** | JetBrains plugin (Kotlin) — calls HTTP services only. |
| **WSL** | **Installed wheel** `motadata-context-layer` — Context Layer HTTP service; **indexes `workspace_root` in the Motadata AIOps repo** (Linux path). |
| **GPU / server** | **`m-coder`** checkout — **Plan-Gate** (`8089` by default), optional **vLLM** for deep reasoning paths only (**§3.5**). |

---

## 3. Major components

### 3.1 JetBrains plugin (`jetbrains-plugin/`)

- **`RuntimeBridge`**: single integration point for Plan-Gate (`/v0/plan`, `/v0/ask`, `/v1/ask`, `/v0/execute`, `/healthz`, `/version`).
- **`Layer5EvidenceExporter`**: obtains `layer5.evidence_bundle.v1` before Ask:
  1. **HTTP** → `POST …/v1/export_evidence` (default base `http://127.0.0.1:8091`).
  2. Optional **CLI** (`MOTADATA_CONTEXT_LAYER_CLI`).
  3. **Dev-only** repo script (`layer5_export_evidence.py`) if `MOTADATA_CONTEXT_LAYER_DEV_REPO_SCRIPT_FALLBACK=1`.
- **`EvidenceExportOutcome`**: `Success` | `Unreachable` | `ServiceFailure` — drives fallback vs hard error.
- **`AskV1Contract`**: builds `ask_request.v1.0` JSON; classifies Plan-Gate v1 errors (no fallback on `identity_mismatch`, `evidence_schema_invalid`, etc.).
- **Flags**: `MotadataAskFlags` — evidence-first via `-Dmotadata.ask.evidence_first=true` or `MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST=1`.

### 3.2 WSL Context Layer (installable package)

- **Package build**: `packaging/motadata-context-layer/pyproject.toml` → wheel includes `runtime.layer5` + `runtime.context_layer_service` + evidence schema JSON.
- **Service**: stdlib `HTTPServer` — **`GET /healthz`**, **`GET /version`**, **`POST /v1/export_evidence`**.
- **Logic**: `evidence_api.export_evidence_bundle_dict` → resolver → index → lexical retrieval → `build_evidence_bundle` (unchanged L5 semantics).
- **Config env**: `MOTADATA_CONTEXT_LAYER_HOST`, `MOTADATA_CONTEXT_LAYER_PORT`, `MOTADATA_CONTEXT_LAYER_LOG_LEVEL`, `MOTADATA_CONTEXT_LAYER_LOG_PATH`.

### 3.3 Plan-Gate service (`runtime/plan_gate_service/`)

- **`POST /v0/ask`**: `ask_request.v0.1` — may use **ContextEngine** (repo paths) and optional `evidence_first` server-side L5 when workspace exists on that host.
- **`POST /v1/ask`**: **`ask_request.v1.0`** — **`v1_ingest.handle_ask_v1_request`**: validates envelope + **strict** evidence schema; **no ContextEngine** on this path; maps evidence dict → `ContextBundle` → planner / `explain_debug`.
- **`GET /version`**: advertises `ask_request_v1` among supported schemas.

### 3.4 Frozen contracts (IDE schemas under `runtime/ide/schemas/`)

- **`layer5.evidence_bundle.v1`**: JSON schema under `runtime/layer5/evidence/evidence_bundle.v1.schema.json`.
- **`ask_request.v1.0`**: envelope with required `evidence_bundle`.
- **`plan_only_response.v0.1`**: response shape for both v0 and v1 Ask success paths.

### 3.5 Optional: vLLM

- **Required only** for deep reasoning / **EXPLAIN_DEBUG**-style paths when `MOTADATA_EXPLAIN_VLLM_URL` is set.
- **Basic PLAN_ONLY** flows and **Ask envelope / evidence schema validation** do **not** depend on vLLM.
- If `MOTADATA_EXPLAIN_VLLM_URL` is set, Plan-Gate may **health-check** vLLM on startup — **unset** it when no vLLM is running (**§6.5**).

---

## 4. Information flows

### 4.1 Evidence-first (target path)

```
[IDE Ask, evidence_first=true]
    → Layer5EvidenceExporter
        → HTTP POST WSL /v1/export_evidence { workspace_root, query, top_k }
        → layer5.evidence_bundle.v1 (JSON)
    → RuntimeBridge POST GPU /v1/ask with ask_request.v1.0 + evidence_bundle
    → Plan-Gate validates, builds ContextBundle from evidence only, planner/reasoner
    → plan_only_response.v0.1 (+ echoed evidence_bundle, evidence_first_meta.ask_path = v1_evidence)
    → Plugin UI (evidence primary; duplicate context_bundle file list omitted for v1)
```

### 4.2 Fallback behavior (truth table)

**Allowed fallback to `/v0/ask` (controlled, not silent success on bad evidence):**

| Condition | Fallback? |
|-----------|-----------|
| **evidence-first** disabled | Yes — use `/v0/ask` per policy |
| **Context Layer** not configured / no HTTP provider | Unreachable → allowed fallback when evidence-first is on |
| **Context Layer unreachable** before request (TCP failure, timeout, unknown host) | Yes — `POST /v0/ask` with `evidence_first: true` (Plan-Gate may run server-side L5 **if** it can access the workspace path) |

**MUST NOT fallback — explicit error surface; no silent fallback:**

| Condition | Fallback? |
|-----------|-----------|
| **Context Layer reachable** but export fails (HTTP **4xx/5xx**, or **200** with invalid JSON / wrong `schema_hint`) | **No** — `ServiceFailure` / `UNKNOWN` |
| **Invalid JSON**, **invalid `evidence_bundle`**, **`identity_mismatch`**, **`empty_evidence_bundle`**, **`ask_envelope_invalid`**, other **`/v1/ask` contract errors** | **No** — `UNKNOWN`; user must fix input or service |

### 4.3 Legacy Ask (evidence_first false)

```
IDE → POST /v0/ask (ask_request.v0.1, repo_root, …) → ContextEngine + planner → plan_only_response
```

---

## 5. Interaction diagram (logical blocks)

```
┌─────────────────┐     HTTP      ┌──────────────────────────┐
│ JetBrains       │ ────────────► │ WSL Context Layer         │
│ (Windows)       │  :8091       │ motadata-context-layer    │
└────────┬────────┘               │ (wheel: L5 index/retrieve │
         │                        │  + export_evidence)      │
         │ HTTP                   └──────────────────────────┘
         │ :8089 (typical)
         ▼
┌─────────────────┐     optional  ┌─────────────┐
│ Plan-Gate       │ ◄────────────►│ vLLM        │
│ (GPU / repo)    │   explain     │ :8000 etc.  │
└─────────────────┘               └─────────────┘
```

- Plugin **never** runs L5 locally on Windows; it sends **`repo_root` = `project.basePath`** — must be a **Linux path** visible to WSL (**§6.2**) pointing at the **Motadata AIOps** workspace repo.
- **GPU** holds Plan-Gate governance (m-coder); **WSL** Context Layer reads **AIOps** files on disk for evidence.

---

## 6. Deterministic setup — Windows, WSL, GPU-server

This section is written so **each role, artifact, port, and verification command** is explicit.

- **GPU-server:** **`m-coder`** clone — Plan-Gate only **§6.5**.
- **WSL:** **Motadata AIOps** workspace repo (clone under Linux) + **Context Layer wheel** installed **(§6.6)** — **no `m-coder` checkout required** on WSL unless you **choose** to build the wheel there (see Option B).
- **Windows:** JetBrains plugin only **(§6.7)**.

### 6.1 Roles and fixed ports (do not change unless you change code)

| Role | Host | Process | Default bind | Port | Purpose |
|------|------|---------|--------------|------|---------|
| **Plan-Gate (L3)** | GPU-server (Linux) | `python -m runtime.plan_gate_service.app` | loopback unless you expose | **8089** | `/v0/ask`, `/v1/ask`, `/healthz`, `/version` |
| **Context Layer (L5)** | WSL (Linux) | `motadata-context-layer` | `MOTADATA_CONTEXT_LAYER_HOST` | **8091** | `/v1/export_evidence`, `/healthz`, `/version` |
| **IDE client** | Windows | JetBrains + plugin | — | — | HTTP client only |

**Artifacts:**

| Artifact | Built on | Installed on | Notes |
|----------|----------|--------------|-------|
| JetBrains plugin **`.zip`** | GPU or dev machine (Gradle) | **Windows** | From `jetbrains-plugin/build/distributions/` |
| Context Layer **wheel** | GPU or dev machine (`python -m build` in `packaging/motadata-context-layer`) | **WSL** | `motadata_context_layer-0.1.0-py3-none-any.whl` |
| Plan-Gate **runtime** | **Not** installed separately — runs from **`m-coder`** tree | **GPU** | `PYTHONPATH` = repo root; `python -m runtime.plan_gate_service.app` |

**Git checkouts (distinct):**

| Repo | Where |
|------|--------|
| **m-coder** | GPU-server (required for Plan-Gate) |
| **Motadata AIOps** | WSL filesystem (required for evidence-first indexing) |

### 6.2 `workspace_root` requirement (evidence-first)

**Rule:** `workspace_root` MUST be a **Linux path** that the Context Layer process on **WSL** can open.

| `project.basePath` | Evidence-first |
|--------------------|-------------------|
| **`/home/.../motadata-aiops`** (or any path under WSL Linux FS) | **Valid** |
| **`C:\...`** only (Windows-only) | **INVALID** — export **will** fail |
| **`\\wsl$\...`** UNC without a normalized `/home/...` path | **INVALID** — do not rely on |

**If JetBrains is opened on a Windows-only path:** evidence export **WILL fail** — **expected behavior**, not a bug.

**Correct:** Open the **Motadata AIOps** workspace from **WSL** (Remote / Gateway / WSL backend) so `basePath` is e.g. `/home/<you>/motadata-aiops`.

### 6.3 Plan-Gate connectivity from Windows (plugin default)

**`RuntimeBridge`**, **`AskClient`**, **`PlanGateClient`** default to **`http://127.0.0.1:8089`** — **no** JVM env override in code.

**If the GPU is remote**, the JVM still targets **`http://127.0.0.1:8089`** (not configurable). Windows **MUST** make that address reach Plan-Gate on the GPU host:

| Branch | Action |
|--------|--------|
| **SSH (deterministic default)** | `ssh -N -L 8089:127.0.0.1:8089 <user>@<gpu-host>` — keep session open; Plan-Gate listens on **GPU loopback** `127.0.0.1:8089`. |
| **Direct network** | Same JVM constraint: use a **local** forward/proxy on Windows so **IDE still connects to `127.0.0.1:8089`**, or extend the plugin to accept a configurable Plan-Gate base URL (not in current code). |

**Common failure:** WSL Context Layer **healthy**, plugin loads — **GPU / Plan-Gate unreachable** → Ask fails (`RUNTIME_UNAVAILABLE` or connection error). **Not** a Context Layer bug.

- **Plan-Gate on same host as IDE:** rare; port **8089** must still match the plugin default.

### 6.4 Execution order (recommended)

1. **GPU-server:** clone monorepo, start Plan-Gate, verify **§6.5**.
2. **Windows:** start **SSH tunnel** (if GPU is remote) so `127.0.0.1:8089` reaches Plan-Gate.
3. **WSL:** install wheel, start Context Layer, verify **§6.6**.
4. **Windows:** configure IDE VM options (**§6.7**), start IDE, verify Ask (**§6.8**).

### 6.5 GPU-server — `m-coder` checkout and Plan-Gate

**Inputs:** Git access to **m-coder**; Python **3.10+**; shell on the GPU-server.

**Steps (copy as a runbook):**

1. Clone and enter repo root (the directory that **contains** the `runtime/` folder):

   ```bash
   git clone <your-remote-url> m-coder
   cd m-coder
   git checkout feature/l5-context-layer-v1-ask-packaging   # or your integration branch
   ```

2. Ensure imports resolve (unambiguous):

   ```bash
   export PYTHONPATH=/absolute/path/to/m-coder
   cd /absolute/path/to/m-coder
   ```

3. If Plan-Gate health-checks vLLM on startup when configured, **disable** when you have no vLLM:

   ```bash
   unset MOTADATA_EXPLAIN_VLLM_URL
   ```

4. Start Plan-Gate:

   ```bash
   export PLAN_GATE_PORT=8089
   export PLAN_GATE_SPOOL_DIR=/tmp/plan_gate_spool
   python3 -m runtime.plan_gate_service.app
   ```

5. **Verification gates** (must succeed before continuing):

   ```bash
   curl -sS http://127.0.0.1:8089/healthz
   curl -sS http://127.0.0.1:8089/version
   ```

   In `/version` JSON, confirm support for **`ask_request_v1`** (or equivalent field) for evidence-first `/v1/ask`.

**Optional firewall note:** If you use SSH `-L 8089:127.0.0.1:8089`, Plan-Gate only needs to listen on **GPU loopback**. If you ever bind `0.0.0.0`, restrict with security groups / `iptables`.

### 6.6 WSL — Context Layer wheel + Motadata AIOps workspace repo

**Inputs:** WSL Ubuntu (or similar); Python **3.10+**; wheel file **or** **m-coder** clone **only** to build the wheel (Option B). **AIOps** clone is **separate** — it is the **workspace** you index, not the assistant build tree.

**Option A — Build wheel on GPU-server, copy artifact to WSL (recommended: no m-coder on WSL)**

1. On GPU-server (same repo as **§6.5**):

   ```bash
   cd /absolute/path/to/m-coder/packaging/motadata-context-layer
   python3 -m venv .venv-build && source .venv-build/bin/activate
   pip install build
   python -m build --wheel -o dist
   ```

2. Produced file: **`dist/motadata_context_layer-0.1.0-py3-none-any.whl`**.

3. Copy to WSL (example: `scp` to Windows then into WSL, or direct `scp user@gpu:.../dist/*.whl ~/`).

**Option B — Build wheel inside WSL** — requires **`m-coder`** clone under WSL **only** for `packaging/motadata-context-layer` build; **not** required for production operation after `pip install`.

**Clone Motadata AIOps in WSL (for indexing):**

```bash
cd ~
git clone <your-aiops-remote-url> motadata-aiops   # example path
```

**Install and run Context Layer (WSL):**

```bash
python3 -m venv ~/.venvs/motadata-context-layer && source ~/.venvs/motadata-context-layer/bin/activate
pip install /path/to/motadata_context_layer-0.1.0-py3-none-any.whl
export MOTADATA_CONTEXT_LAYER_PORT=8091
```

**Bind address (choose one branch — deterministic):**

| Situation | `MOTADATA_CONTEXT_LAYER_HOST` | Client URL from Windows |
|-----------|------------------------------|-------------------------|
| **Default** — Windows can reach WSL **localhost** | `127.0.0.1` | `http://127.0.0.1:8091` |
| **Windows cannot reach WSL `127.0.0.1:8091`** | `0.0.0.0` (listen all interfaces) | `http://<WSL_IP>:8091` — get `<WSL_IP>` from WSL: `ip -4 addr show eth0` (or equivalent) |

```bash
export MOTADATA_CONTEXT_LAYER_HOST=127.0.0.1   # default
# OR if Windows cannot reach localhost:
# export MOTADATA_CONTEXT_LAYER_HOST=0.0.0.0
motadata-context-layer
```

Equivalent: `python -m runtime.context_layer_service`

**Verification gates:**

```bash
curl -sS http://127.0.0.1:8091/healthz
curl -sS http://127.0.0.1:8091/version
```

**POST smoke** — **`workspace_root`** MUST be the **Motadata AIOps** Linux path on **this** WSL filesystem:

```bash
curl -sS -X POST http://127.0.0.1:8091/v1/export_evidence \
  -H 'Content-Type: application/json' \
  -d '{"workspace_root":"/home/YOU/motadata-aiops","query":"test","top_k":8}'
```

Expect **HTTP 200** and JSON containing **`schema_hint`** consistent with **`layer5.evidence_bundle.v1`**.

**Plugin URL on Windows:** set **`-Dmotadata.context_layer.url=`** to the same URL as the **Client URL from Windows** row (either `http://127.0.0.1:8091` or `http://<WSL_IP>:8091`).

### 6.7 Windows — JetBrains plugin build and JVM configuration

**Inputs:** JDK **17+** (match `jetbrains-plugin` toolchain); Gradle; repo checkout (can be on Windows disk **for building** the plugin only).

**Build plugin distribution:**

```bash
cd jetbrains-plugin
./gradlew buildPlugin
```

Artifact directory: **`jetbrains-plugin/build/distributions/`** — install **Help → Plugins → gear → Install Plugin from Disk** on Windows IDEA/PyCharm.

**Or** `./gradlew runIde` for a sandbox IDE (development).

**JVM / custom VM options** (Help → Edit Custom VM Options…) — add **exactly** what you need:

| Goal | Line to add |
|------|-------------|
| Evidence-first Ask (v1 evidence + `/v1/ask`) | `-Dmotadata.ask.evidence_first=true` |
| Alternative (env for IDE process) | Set `MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST=1` in the environment that launches the IDE |
| Context Layer base URL (if not default) | `-Dmotadata.context_layer.url=http://127.0.0.1:8091` |
| Context Layer via env instead | `MOTADATA_CONTEXT_LAYER_URL=http://127.0.0.1:8091` |

**Plan-Gate:** No property today — rely on **`127.0.0.1:8089`** (**§6.3** tunnel if remote).

Restart the IDE after changing VM options.

### 6.8 End-to-end checklist (Windows + WSL + GPU)

| Step | Check |
|------|--------|
| 1 | GPU: `curl http://127.0.0.1:8089/healthz` on **GPU** succeeds |
| 2 | Windows: same `curl` succeeds **on Windows** when tunnel is up (or Plan-Gate is local) |
| 3 | WSL: `curl http://127.0.0.1:8091/healthz` succeeds **from WSL** |
| 4 | Windows: `curl http://127.0.0.1:8091/healthz` succeeds **from Windows** (or use WSL IP in browser/curl) |
| 5 | Project `basePath` is a **Linux path** visible to WSL (**§6.2**) |
| 6 | IDE: Ask Motadata AI with evidence-first enabled returns a plan, not `UNKNOWN` / export failure |

### 6.9 Automated tests (optional, on GPU-server repo)

From monorepo root with `PYTHONPATH` set:

```bash
python3 -m pytest runtime/tests/test_context_layer_service.py runtime/tests/test_ask_v1_ingest.py -q
```

### 6.10 Single-machine shortcut (everything on one Linux host)

If GPU-server **is** also your WSL-less Linux desktop: you may run **both** Plan-Gate (**8089**) and Context Layer (**8091**) on that host, and run JetBrains with a **remote** or **local** project path that is Linux. Still use two ports and the same verification gates; plugin on Windows is unchanged except tunnel may be unnecessary if the IDE runs on the same machine (then `127.0.0.1` for both services is literal).

---

## 7. Demo script (talk track)

1. **Show three surfaces**: Windows IDE, WSL terminal (Context Layer), GPU/server (Plan-Gate).
2. **Start Context Layer** — hit `/healthz` and `/version`; point out `package_version` and `evidence_schema_hint`.
3. **Start Plan-Gate** — `/version` includes `ask_request_v1`.
4. **POST /v1/export_evidence** with **`workspace_root` = Motadata AIOps path on WSL** — show `schema_hint` and `entries` in the JSON.
5. **Enable evidence-first** in the plugin — run Ask — show UI: primary **evidence_bundle**, `ask_path: v1_evidence` (or equivalent field), plan steps, **PLAN ONLY**.
6. **Mandatory no-match case:** Ask with query **`quantum entanglement handler in repo`**. Operator records **true no-match** (empty or near-empty evidence) **or** **weak lexical fill** — do **not** hide; required for validation.
7. **Stop Context Layer** — repeat Ask — show **controlled** fallback to v0 (unreachable) vs **error** if export fails while service is up (**§4.2**).

---

## 8. Key files (quick index)

| Area | Paths |
|------|--------|
| Wheel packaging | `packaging/motadata-context-layer/pyproject.toml`, `README.md` |
| Context Layer service | `runtime/context_layer_service/{app,cli,config,evidence_api,logging_setup}.py` |
| v1 Ask ingest | `runtime/ask_service/v1_ingest.py`, `runtime/plan_gate_service/app.py` |
| Evidence + L5 | `runtime/layer5/{workspace,index,retrieval,evidence}/` |
| Plugin bridge | `jetbrains-plugin/.../bridge/{RuntimeBridge,Layer5EvidenceExporter,AskV1Contract,EvidenceExportOutcome}.kt` |
| Client / packaging docs | `docs/runtime/WSL_CONTEXT_LAYER_CLIENT.md`, `docs/layer5/WSL_CONTEXT_LAYER_PACKAGING_PLAN.md` |
| Roadmap | `docs/LIVE_ROADMAP_TRACKER.md` |

---

## 9. Known limitations (for demos)

- **Windows ↔ WSL networking**: **§6.6** — default `MOTADATA_CONTEXT_LAYER_HOST=127.0.0.1`; if Windows cannot reach it, use `0.0.0.0` + WSL IP.
- **Plan-Gate URL not configurable in plugin**: **§6.3** — SSH local forward to `8089` when Plan-Gate is remote.
- **Workspace path semantics**: **§6.2** — Windows-only paths **invalid** for evidence-first.
- **Gradle `:test`** for the plugin may hit an IntelliJ sandbox **Index** error in some environments; **`compileKotlin` / `compileTestKotlin`** are still useful.
- Wheel may still include a tiny **golden fixture** `.py` under `layer5/evidence/golden/` (cosmetic bloat only).

---

## 10. Deployment Success Criteria

The system is **correctly deployed** only if **all** of the following hold:

| # | Criterion |
|---|-----------|
| 1 | From **Windows**: `curl` to WSL Context Layer **`/healthz`** succeeds (URL per **§6.6**). |
| 2 | From **Windows**: `curl` to Plan-Gate **`/version`** succeeds (tunnel or direct per **§6.3**). |
| 3 | From **WSL**: **`POST /v1/export_evidence`** with **Motadata AIOps** `workspace_root` returns **HTTP 200** and a **schema-valid** bundle. |
| 4 | Plugin UI shows **evidence bundle** content for evidence-first Ask. |
| 5 | Response metadata shows **`ask_path`** = **`v1_evidence`** (or equivalent documented field). |
| 6 | On **contract failure** (bad evidence, `/v1/ask` error codes) — **no** silent fallback to “success” (**§4.2**). |
| 7 | **One golden query** (known match in AIOps repo) passes end-to-end. |
| 8 | **One no-match query** — **§7 step 6** — observed (true no-match or weak lexical fill). |

---

## 11. Git reference

- **Branch pushed**: `feature/l5-context-layer-v1-ask-packaging`
- **Remote**: `origin` (e.g. `github.com:harshilshah2501/m-coder.git`)
- **PR**: create via GitHub UI from the push message URL if desired.

---

*Update when architecture, ports, or deployment roles change.*

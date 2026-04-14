# Integrate m-coder with the Motadata repo (operator guide)

Temporary, concrete defaults (2026). Replace paths and hosts only where your environment differs.

## Who this is for

Operators wiring **m-coder** (Plan-Gate, vLLM, Context Layer) to a **Motadata** workspace and optionally the **JetBrains** plugin.

**Three places matter:**

| Place | Role |
|--------|------|
| **GPU host** | Runs governed Plan-Gate + vLLM (`governed_services.sh`). |
| **Workspace host (WSL/Linux)** | Runs Context Layer next to the Motadata checkout; may use an **SSH tunnel** to the GPU. |
| **Windows (optional)** | JetBrains plugin; must reach Context Layer + Plan-Gate URLs that work **from the IDE process** (often `127.0.0.1` or your WSL IP). |

---

## Automatic steps (what scripts do for you)

These run from your **m-coder** clone (`M_CODER_ROOT`) unless noted.

| Step | What runs | When |
|------|-----------|------|
| **Integration preflight** | `scripts/motadata_integration_preflight.sh` | **Default mode:** optional artifact build (`PREFLIGHT_BUILD_ARTIFACTS=1`), then `wsl_plugin_mvp_stack.sh up`, checklist, `check`, optional Ask E2E. |
| **Managed WSL/workspace stack** | `scripts/wsl_plugin_mvp_stack.sh` | **Invoked by preflight** (default) **or** run **on its own** — optional SSH tunnel, Context Layer (**in-repo** or **wheel** mode), health, commit alignment, endpoint probes. |
| **Packaging & versions** | `scripts/motadata_packaging.sh` | Syncs versions from `scripts/motadata_versions.env` into `pyproject.toml` / `build.gradle.kts` / `plugin.xml`, builds **wheel** and **plugin zip**, optional `pip install` / unzip into IDE plugins dir. |
| **Preflight-only modes** | Same script | `--verify-only` skips `up` (probes only). `--quick-only` skips `up` and deep `check`. **`--fresh`** (or `PREFLIGHT_FRESH_STACK=1`) runs **`wsl_plugin_mvp_stack.sh restart`** instead of `up` — stops managed tunnel + Context Layer first (use after **`git pull`** so you do not keep old PIDs and stale code). |

**Still manual:** starting the **GPU** (`governed_services`). Everything else on this list can be scripted from the repo; **IDE restart** after plugin install is usually required.

---

## Manual steps (operator responsibility)

| Step | Where | What you do |
|------|--------|-------------|
| **GPU backend** | GPU host | Configure `demo_stack.env`, run `governed_services.sh start` so Plan-Gate + vLLM listen (tunnel forwards to these). |
| **SSH identity / reachability** | Workspace host | Ensure `TUNNEL_TARGET=user@host` is valid and SSH to GPU works (`TUNNEL_SSH_KEY` if needed). |
| **Motadata workspace path** | Workspace host | Export `MOTADATA_ROOT` / `MOTADATA_REPO_ROOT` to a real directory on that machine. |
| **Context Layer wheel (optional)** | Workspace | Use **`./scripts/motadata_packaging.sh build-wheel`** then **`install-wheel /path/to/venv`**, set **`CONTEXT_LAYER_LAUNCH_MODE=wheel`** and **`MOTADATA_CONTEXT_LAYER_VENV`** for `wsl_plugin_mvp_stack.sh` (see below). |
| **JetBrains plugin** | Dev machine | **`./scripts/motadata_packaging.sh build-plugin`**; optionally **`install-plugin`** with **`JETBRAINS_PLUGIN_INSTALL_DIR`** set to your IDE `plugins` folder (path varies). IDE still needs a **restart** to load the new plugin. |
| **First-time evidence / Ask debugging** | Workspace | Optional manual `curl` / `jq` flows in later sections if you need to inspect payloads outside the script. |

---

## Logs (troubleshooting)

Paths are under **`$M_CODER_ROOT/runtime/.run/`** (created by the stack scripts). Inspect these when a step fails or a port is not listening.

| Log / file | Contents / use |
|------------|----------------|
| **`motadata_preflight_<UTC>.log`** | Full stdout/stderr of **`motadata_integration_preflight.sh`** (tee’d every run). Start here for preflight failures. |
| **`wsl_context_layer.log`** | Stderr/stdout of the **in-repo Context Layer** process started by `wsl_plugin_mvp_stack.sh`. Use for export/indexing errors, Python tracebacks. |
| **`wsl_plan_gate_tunnel.log`** | **SSH tunnel** (`ssh -L ...`) output; connection/auth/forward failures. |
| **`wsl_context_layer.pid`** | PID written when Context Layer is managed by this script (for `status` / `down`). |
| **`wsl_plan_gate_tunnel.pid`** | PID for the managed tunnel (same). |
| **`wsl_context_layer.meta`** | Launch metadata (e.g. git commit, `motadata_root`) for alignment checks. |

On the **GPU**, governed services may log under your shell or `runtime/` layout as implemented by `governed_services.sh` — check that script and the process manager you use if Plan-Gate/vLLM fail before the tunnel matters.

---

## `wsl_plugin_mvp_stack.sh`: preflight only or standalone?

- **Not only preflight.** You can run **`./scripts/wsl_plugin_mvp_stack.sh`** directly with the same environment variables:
  - **`up`** — bring up tunnel (if `ENABLE_SSH_TUNNEL=1`) + Context Layer + checks (same work preflight’s default mode triggers first).
  - **`check`** — health + `/version` + commit parity + route probes (same as preflight’s deep step).
  - **`status`**, **`down`**, **`restart`** — inspect or stop **only** processes this script started (PID files above).

- **Preflight** is a **wrapper**: default = `up` + human-readable checklist + `check` (+ optional E2E). Use **standalone** `wsl_plugin_mvp_stack.sh` when you want stack control without the full checklist, or after reading logs to restart a single piece.

---

## Packaging & versions (`scripts/motadata_packaging.sh`)

**Version source:** edit **`scripts/motadata_versions.env`** (`MOTADATA_CONTEXT_LAYER_VERSION`, `MOTADATA_JETBRAINS_PLUGIN_VERSION`), then:

```bash
cd "$M_CODER_ROOT"
./scripts/motadata_packaging.sh sync-versions   # writes pyproject.toml, build.gradle.kts, plugin.xml
```

| Command | Purpose |
|---------|---------|
| `show-versions` | Print manifest + current file snippets. |
| `sync-versions` | Apply versions from the manifest (Python helper). |
| `build-wheel` | Build `packaging/motadata-context-layer/dist/*.whl` (uses a local `.venv-build-packaging`). |
| `build-plugin` | Run `./gradlew buildPlugin` → `jetbrains-plugin/build/distributions/*.zip`. |
| `build-all` | `sync-versions` + `build-wheel` + `build-plugin`. |
| `install-wheel /path/to/venv` | `pip install` the wheel into that venv (or set `MOTADATA_CONTEXT_LAYER_VENV` and pass no path). |
| `install-plugin` | If **`JETBRAINS_PLUGIN_INSTALL_DIR`** is set, **`unzip`** the built plugin into that directory; otherwise prints the zip path and **Install from Disk** instructions. |

**Preflight:** `PREFLIGHT_BUILD_ARTIFACTS=1` (or `MOTADATA_BUILD_ARTIFACTS=1`) runs **`build-all`** before **`wsl_plugin_mvp_stack.sh up`** (slow; use for release dry-runs).

**Context Layer modes (`wsl_plugin_mvp_stack.sh`):**

| `CONTEXT_LAYER_LAUNCH_MODE` | Behavior |
|-----------------------------|----------|
| `inrepo` (default) | `python3 -m runtime.context_layer_service.app` with `PYTHONPATH` = m-coder — no wheel. |
| `wheel` | Runs **`$MOTADATA_CONTEXT_LAYER_VENV/bin/motadata-context-layer`** (install wheel into that venv first). |

**JetBrains “almost full” automation:** the script can **build** the zip and **unzip** into a configured IDE plugins directory. JetBrains does not expose a stable CLI to “reload plugins” without restarting the IDE — **restart the IDE** after install.

---

## Context Layer wheel and JetBrains plugin: automatic or manual?

| Artifact | Scripted? | Notes |
|----------|-----------|--------|
| **Context Layer (in-repo)** | **Yes** | Default `CONTEXT_LAYER_LAUNCH_MODE=inrepo`. |
| **Context Layer wheel** | **Yes** | `motadata_packaging.sh` + optional `install-wheel` + `CONTEXT_LAYER_LAUNCH_MODE=wheel`. |
| **JetBrains plugin zip** | **Yes** | `motadata_packaging.sh build-plugin`. |
| **JetBrains plugin load in IDE** | **Partial** | `install-plugin` + `JETBRAINS_PLUGIN_INSTALL_DIR` **or** **Settings → Plugins → Install Plugin from Disk… →** select the zip. **Restart IDE** to load. |

---

## 1) Environment variables (copy-paste template)

```bash
export GPU_USER="harshil"
export GPU_HOST="45.195.82.10"
export M_CODER_ROOT="$HOME/m-coder"

# Motadata checkout on the machine where Context Layer runs (must exist and be readable there).
export MOTADATA_REPO_ROOT="/home/harshil/Projects/Motadata"

export CONTEXT_URL="http://127.0.0.1:8091"
export PLAN_GATE_URL="http://127.0.0.1:8089"
```

**Same path, two names:** scripts also read **`MOTADATA_ROOT`**. If you set only `MOTADATA_REPO_ROOT`, preflight copies it to `MOTADATA_ROOT`. Keep them identical to the real directory on that host.

**If the IDE cannot use `127.0.0.1:8091` for Context Layer** (e.g. Windows → WSL), point the plugin at your WSL IP, for example:

```bash
export WSL_CONTEXT_URL="http://172.30.127.150:8091"
```

---

## 2) Running the integration preflight (recommended)

See **Automatic steps** and **Logs** above. On the **workspace host**, after the GPU stack is up (or reachable via tunnel):

| Mode | What it does |
|------|----------------|
| **Default** | **`wsl_plugin_mvp_stack.sh up`** → checklist → **`wsl_plugin_mvp_stack.sh check`** → optional Ask E2E. **Requires** `MOTADATA_ROOT` or `MOTADATA_REPO_ROOT`. **`up` reuses** a running managed tunnel/Context Layer if PIDs in `runtime/.run/*.pid` are still alive (fast, but **not** fresh code after `git pull`). |
| **`--fresh`** (or **`PREFLIGHT_FRESH_STACK=1`**) | Same as default, but runs **`wsl_plugin_mvp_stack.sh restart`** (`down` then `up`) so tunnel and Context Layer **restart** and pick up the **current** repo commit. **Recommended after `git pull`**. |
| **`--verify-only`** (or **`PREFLIGHT_NO_SETUP=1`**) | **No** local `up` — probes only. Use when tunnel + services already run. |
| **`--quick-only`** | Fast probes only; **no** `up`, **no** deep `check`. |

**Typical full run** (tunnel to GPU + workspace path):

```bash
cd "$M_CODER_ROOT"
export MOTADATA_REPO_ROOT="/home/harshil/Projects/Motadata"
export CONTEXT_URL="http://127.0.0.1:8091"
export PLAN_GATE_URL="http://127.0.0.1:8089"
export ENABLE_SSH_TUNNEL=1
export GPU_USER="harshil"
export GPU_HOST="45.195.82.10"
export TUNNEL_TARGET="${GPU_USER}@${GPU_HOST}"
# Optional: TUNNEL_SSH_KEY=~/.ssh/id_ed25519
# (If TUNNEL_TARGET was already '@', scripts rebuild it from GPU_USER+GPU_HOST when both are set.)

./scripts/motadata_integration_preflight.sh
```

**After `git pull` in m-coder:** run preflight with a **fresh** managed stack so the Context Layer and SSH tunnel are not left running from before the update:

```bash
./scripts/motadata_integration_preflight.sh --fresh
# equivalent: PREFLIGHT_FRESH_STACK=1 ./scripts/motadata_integration_preflight.sh
```

Or stop and restart the stack yourself: `./scripts/wsl_plugin_mvp_stack.sh restart` then `./scripts/motadata_integration_preflight.sh --verify-only` if you only need checks.

**Tunnel target must be a real `user@host`** (for example `harshil@45.195.82.10`). If you run `export TUNNEL_TARGET="${GPU_USER}@${GPU_HOST}"` **before** `GPU_USER` / `GPU_HOST` are set, the value becomes the literal `@` — **export `GPU_USER` and `GPU_HOST` first**, or set `TUNNEL_TARGET` explicitly. The scripts also **rebuild** the tunnel target from `GPU_USER`+`GPU_HOST` when the current target is empty or invalid (e.g. `@`). On the **GPU**, start **`governed_services`** first so Plan-Gate (and vLLM) exist behind the tunnel.

**Only verify** (no `up` on this host):

```bash
./scripts/motadata_integration_preflight.sh --verify-only
```

**Optional:** `ALLOW_COMMIT_MISMATCH=1`, `VERIFY_ASK_E2E=1`, `PREFLIGHT_CONTINUE_ON_QUICK_FAIL=1` — see `scripts/motadata_integration_preflight.sh`.

**Same stack without full checklist:** `./scripts/wsl_plugin_mvp_stack.sh {up|check|status|down|restart}` (see **`wsl_plugin_mvp_stack.sh`: preflight only or standalone?** above).

Exit code **0** and the **GREEN** banner mean you can proceed to **JetBrains UI** tests (if the plugin is already built and installed — **manual**).

---

## 3) GPU host: start governed backend

```bash
ssh "$GPU_USER@$GPU_HOST"
cd "$M_CODER_ROOT"
cp runtime/config/demo_stack.env.example runtime/config/demo_stack.env
```

Set a real model in `runtime/config/demo_stack.env`, for example:

```bash
VLLM_BASE_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
```

Then:

```bash
cd "$M_CODER_ROOT"
export PYTHONPATH="$M_CODER_ROOT"
./runtime/scripts/governed_services.sh start
./runtime/scripts/governed_services.sh status

curl -sS http://127.0.0.1:8000/v1/models | head -c 400 && echo
curl -sS http://127.0.0.1:8089/healthz && echo
curl -sS http://127.0.0.1:8089/version && echo
```

**Expect:** HTTP 200 on `/v1/models`, `{"status":"ok"}` on `/healthz`, `/version` includes `ask_request_v1`.

---

## 4) Build Context Layer wheel (GPU), install on workspace host — **optional**

**Scripted (recommended on any host with Python):** `cd "$M_CODER_ROOT" && ./scripts/motadata_packaging.sh build-wheel` then `install-wheel /path/to/venv`; set **`CONTEXT_LAYER_LAUNCH_MODE=wheel`** and **`MOTADATA_CONTEXT_LAYER_VENV`** when using `wsl_plugin_mvp_stack.sh`.

Use a **packaged** Context Layer only if you do **not** want the default **in-repo** process (`CONTEXT_LAYER_LAUNCH_MODE=inrepo`).

On the GPU host (manual wheel build — same as CI):

```bash
cd "$M_CODER_ROOT/packaging/motadata-context-layer"
python3 -m venv .venv-build
source .venv-build/bin/activate
pip install --upgrade pip build
python -m build --wheel -o dist
ls -1 dist/motadata_context_layer-*.whl
```

Copy the wheel to the workspace host, then:

```bash
python3 -m venv ~/.venvs/motadata-context-layer
source ~/.venvs/motadata-context-layer/bin/activate
pip install /tmp/motadata_context_layer-*.whl

export MOTADATA_CONTEXT_LAYER_HOST=127.0.0.1
export MOTADATA_CONTEXT_LAYER_PORT=8091
export MOTADATA_CONTEXT_LAYER_LOG_LEVEL=INFO
motadata-context-layer
```

Bind `0.0.0.0` instead of `127.0.0.1` if another machine must connect to Context Layer on this host.

**Note:** The integration script’s default path uses the **in-repo** Context Layer via `wsl_plugin_mvp_stack.sh up`; the wheel path is for manual or alternate installs.

---

## 5) Validate Context Layer export (manual)

```bash
export CONTEXT_URL="http://127.0.0.1:8091"
export MOTADATA_REPO_ROOT="/home/harshil/Projects/Motadata"

curl -sS "$CONTEXT_URL/healthz" && echo
curl -sS "$CONTEXT_URL/version" && echo

HTTP_CODE="$(curl -sS --max-time 3600 -o /tmp/evidence.json -w '%{http_code}' -X POST "$CONTEXT_URL/v1/export_evidence" \
  -H 'Content-Type: application/json' \
  -d "{\"workspace_root\":\"$MOTADATA_REPO_ROOT\",\"query\":\"how does alert correlation work\",\"top_k\":8}")"
echo "HTTP $HTTP_CODE"
jq '{schema_hint, entry_count: (.entries // [] | length), error, message, failure_class}' /tmp/evidence.json
```

**Cold first export** can sit with no output for a long time (indexing). That is often normal; use `--max-time` if you need a hard cap.

**Expect on success:** HTTP **200**, `schema_hint` is **`layer5.evidence_bundle.v1`**, `entry_count` ≥ 0, no `error` / `failure_class`.

### If `schema_hint` is `null`

Usually not a valid 200 bundle. Check HTTP code, that `workspace_root` is non-empty and the path exists on the Context Layer host, and that `curl "$CONTEXT_URL/version"` shows the Motadata Context Layer.

```bash
jq '{error, message, failure_class}' /tmp/evidence.json
```

---

## 6) Call Plan-Gate `/v1/ask` (manual)

Tunnel Plan-Gate if needed, e.g.:

```bash
ssh -N -L 8089:127.0.0.1:8089 "$GPU_USER@$GPU_HOST"
```

Build request from evidence and POST:

```bash
python3 - <<'PY'
import datetime, json, uuid
ev = json.load(open('/tmp/evidence.json', 'r', encoding='utf-8'))
req = {
    "schema_version": "ask_request.v1.0",
    "request_id": str(uuid.uuid4()),
    "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
    "trace_id": "",
    "query": "How should I implement alert correlation changes in this repository?",
    "evidence_bundle": ev,
}
if ev.get("workspace_identity_hash"):
    req["expected_workspace_identity_hash"] = ev["workspace_identity_hash"]
json.dump(req, open('/tmp/ask_v1.json', 'w', encoding='utf-8'))
print("wrote /tmp/ask_v1.json")
PY

export PLAN_GATE_URL="http://127.0.0.1:8089"
curl -sS -X POST "$PLAN_GATE_URL/v1/ask" \
  -H 'Content-Type: application/json' \
  --data-binary @/tmp/ask_v1.json \
  > /tmp/ask_v1_response.json

jq '.governance_posture, .execution, .evidence_first_meta.ask_path' /tmp/ask_v1_response.json
```

**Expect:** `"PLAN_ONLY"`, `false`, `"v1_evidence"`.

---

## 7) JetBrains plugin (optional)

**Build / version sync:** use **`./scripts/motadata_packaging.sh build-plugin`** (or `build-all`). **Install:** `install-plugin` with **`JETBRAINS_PLUGIN_INSTALL_DIR`**, or **Settings → Plugins → Install Plugin from Disk…** on the zip under `jetbrains-plugin/build/distributions/`. **Restart the IDE** after installing.

Use a tunnel from Windows if Plan-Gate/vLLM live on the GPU:

```bash
ssh -N -L 8000:127.0.0.1:8000 -L 8089:127.0.0.1:8089 "$GPU_USER@$GPU_HOST"
```

**Menu:** **Motadata** → **Ask / Explain / Plan…** (PLAN ONLY) and **Submit to Runtime…**.

**VM options** (or env `MOTADATA_CONTEXT_LAYER_URL` / `MOTADATA_PLAN_GATE_URL`):

```text
-Dmotadata.ask.evidence_first=true
-Dmotadata.context_layer.url=http://127.0.0.1:8091
-Dmotadata.plan_gate.url=http://127.0.0.1:8089
```

If Context Layer is on the WSL IP:

```text
-Dmotadata.context_layer.url=http://172.30.127.150:8091
```

---

## 8) Quick manual verification (optional)

If you are not using the script:

```bash
curl -sS http://127.0.0.1:8089/healthz
curl -sS http://127.0.0.1:8089/version | jq '.supported_schemas.ask_request_v1'
curl -sS http://127.0.0.1:8091/healthz
jq '.schema_hint' /tmp/evidence.json
jq '.governance_posture, .execution, .evidence_first_meta.ask_path' /tmp/ask_v1_response.json
```

Prefer **`./scripts/motadata_integration_preflight.sh`** for the full checklist.

---

## 9) Clean stop

**GPU:**

```bash
ssh "$GPU_USER@$GPU_HOST" "cd '$M_CODER_ROOT' && ./runtime/scripts/governed_services.sh stop"
```

**Workspace:** stop a manually run `motadata-context-layer` with Ctrl+C, or use `./scripts/wsl_plugin_mvp_stack.sh down` for processes started by that script.

---

## 10) Documentation map — setup vs testing scenarios

Use this section as a **single index**: where to go for **bringing the stack up** versus **proving Ask / Plan / execute behavior** (API checks, frozen plugin scenarios, or manual IDE certification).

### Setup (install, configure, run services)

| Topic | Document or script |
|--------|-------------------|
| **This guide** (GPU + workspace + env template + curl smoke) | `docs/archive/guides/TEMP_MOTADATA_REPO_INTEGRATION_GUIDE.md` (sections 1–9) |
| **Integration preflight** (checklist, GREEN/RED, optional Ask HTTP E2E) | `scripts/motadata_integration_preflight.sh` |
| **WSL/workspace stack** (Context Layer, tunnel, `up` / `check` / `down`) | `scripts/wsl_plugin_mvp_stack.sh` |
| **Versions, wheel, JetBrains zip** | `scripts/motadata_packaging.sh`, `scripts/motadata_versions.env` |
| **Governed GPU services** (Plan-Gate + vLLM) | `runtime/scripts/governed_services.sh`, `runtime/config/demo_stack.env` |
| **Repo layout and where things live** | `docs/audit/REPO_LAYOUT_INVENTORY.md` |
| **JetBrains plugin demo topology and wiring** (tunnel, URLs, evidence-first flags) | `docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md` |

### Testing — API and stack (no IDE UI matrix)

These verify **HTTP health**, **Context Layer export**, and **`/v1/ask`** contracts using `curl` / scripts. They do **not** replace plugin UI scenario proof.

| Topic | Document or script |
|--------|-------------------|
| **Manual flows in this guide** | Sections 3, 5, 6, 8 (`curl` / `jq` expectations) |
| **Optional preflight Ask E2E** | `VERIFY_ASK_E2E=1` → `runtime/scripts/verify_ask_path.sh` (export + `/v1/ask`) |
| **Coverage map (pytest ↔ docs)** | `docs/audit/TEST_COVERAGE_MATRIX.md` |

### Testing — plugin scenarios (frozen S1–S8)

The **numbered scenario matrix** for **Ask (plan-only paths)** and **Submit to Runtime** outcomes is **Phase-1 truth proof**: backend JSON and plugin-visible text captures, with a **frozen** `exact_match` contract.

| Topic | Document or path |
|--------|------------------|
| **Closure and what is proven** | `docs/validation/PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md` |
| **Frozen matrix** | `docs/validation/artifacts/plugin_phase1_truth_proof/proof_matrix.json`, `proof_matrix.md` |
| **Per-scenario artifacts** | `docs/validation/artifacts/plugin_phase1_truth_proof/scenario_S*/` |
| **Offline verifier (no Gradle IDE sandbox)** | `scripts/verify_plugin_phase1_proof_matrix.sh` |
| **Gradle contract test** | `jetbrains-plugin/.../Phase1TruthProofHarnessTest.kt` (`phase1ProofMatrixFrozenContract`; `live` tag regenerates artifacts) |

**Scope note:** S1–S5 focus on **`routing_mode: plan_only`** Ask flows (v1, v0, fallback, weak, no-match). S6–S8 cover **execute** outcomes (blocked, refused, executed_failed). **Explain/Debug** (`explain_debug`) is **not** a separate row in this frozen matrix; see **UI certification** below.

### Testing — manual JetBrains UI certification

For **screenshots, operator checklists**, and parity with backend truth (including **explain/debug** as a scenario *class*):

| Topic | Document or script |
|--------|-------------------|
| **Certification process and S1–S8 operator proof** | `docs/validation/PLUGIN_UI_TRUTH_CERTIFICATION.md` |
| **Artifact generator** | `scripts/plugin_ui_truth_cert.py`, `scripts/plugin_ui_truth_aggregate.py` |
| **Final demo runbook** (topology, pass/fail bar) | `docs/guides/JETBRAINS_PLUGIN_UI_FINAL_DEMO_RUNBOOK.md` |

### Final summary (quick pick)

- **Setup end-to-end:** read **sections 1–9** of this file, run **`./scripts/motadata_integration_preflight.sh`** (use **`--fresh`** after **`git pull`** so tunnel + Context Layer restart), use **`docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md`** for plugin URLs and demo modes.
- **Verify services only (curl):** **§3, §5, §6, §8** here; optional **`VERIFY_ASK_E2E=1`** for `verify_ask_path.sh`.
- **Verify plugin ↔ backend scenarios (automated matrix):** **`PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md`** + **`verify_plugin_phase1_proof_matrix.sh`** + artifacts under **`docs/validation/artifacts/plugin_phase1_truth_proof/`**.
- **Verify IDE UI manually:** **`PLUGIN_UI_TRUTH_CERTIFICATION.md`** + **`JETBRAINS_PLUGIN_UI_FINAL_DEMO_RUNBOOK.md`** + **`plugin_ui_truth_cert.py`**.

# Motadata + m-coder integration (operator guide)

Simplified defaults (2026). Replace `M_CODER_ROOT`, hosts, and `MOTADATA_REPO_ROOT` with your paths.

**Topology:** **GPU** runs Plan-Gate HTTP + vLLM. **WSL** (or Linux workspace host) runs the Context Layer next to the Motadata checkout and usually uses an **SSH tunnel** so `127.0.0.1:8089` on WSL reaches Plan-Gate on the GPU.

---

## Chronology (do this order)

| Step | Where | What |
|------|--------|------|
| **1** | **GPU** | Configure `demo_stack.env`, start `governed_services.sh` (Plan-Gate `:8089` + vLLM `:8000`). |
| **2** | **WSL** | Set `MOTADATA_REPO_ROOT`, `ENABLE_SSH_TUNNEL=1`, tunnel target; run `wsl_plugin_mvp_stack.sh up` (Context Layer `:8091` + tunnel). |
| **3** | **WSL** | Run `motadata_integration_preflight.sh` **or** CLI smoke (`cli_e2e_verify.sh`) to prove export → `/v1/ask`. |
| **4** | Optional | JetBrains plugin packaging/install — only if you need the IDE (see linked docs at end). |

**Rule:** start the GPU stack **before** the tunnel depends on it. After `git pull` in m-coder on WSL, prefer **`./scripts/motadata_integration_preflight.sh --fresh`** or **`./scripts/wsl_plugin_mvp_stack.sh restart`** so Context Layer and tunnel pick up the new commit.

---

## 1) GPU host — exact commands

SSH to the GPU, then:

```bash
export M_CODER_ROOT="$HOME/m-coder"   # your m-coder clone on the GPU
cd "$M_CODER_ROOT"
cp runtime/config/demo_stack.env.example runtime/config/demo_stack.env
# Edit demo_stack.env: set VLLM_BASE_MODEL to a real local path or HuggingFace id (see file comments)
export PYTHONPATH="$M_CODER_ROOT"
./runtime/scripts/governed_services.sh start
./runtime/scripts/governed_services.sh status
```

**Quick checks (on GPU):**

```bash
curl -sS http://127.0.0.1:8089/healthz && echo
curl -sS http://127.0.0.1:8089/version && echo
curl -sS http://127.0.0.1:8000/v1/models | head -c 400 && echo
```

**Stop:**

```bash
cd "$M_CODER_ROOT" && ./runtime/scripts/governed_services.sh stop
```

Config reference: [`runtime/config/demo_stack.env.example`](../../../runtime/config/demo_stack.env.example), launcher: [`runtime/scripts/governed_services.sh`](../../../runtime/scripts/governed_services.sh).

---

## 2) WSL / workspace host — exact commands

From your **m-coder** clone on WSL:

```bash
export M_CODER_ROOT="$HOME/m-coder"
cd "$M_CODER_ROOT"

# Motadata checkout on this machine (must exist and be readable)
export MOTADATA_REPO_ROOT="/home/you/Projects/Motadata"
export CONTEXT_URL="http://127.0.0.1:8091"
export PLAN_GATE_URL="http://127.0.0.1:8089"

# Tunnel: Plan-Gate (and optionally vLLM) on GPU → localhost on WSL
export ENABLE_SSH_TUNNEL=1
export GPU_USER="you"
export GPU_HOST="gpu.example.com"
export TUNNEL_TARGET="${GPU_USER}@${GPU_HOST}"
# Optional: export TUNNEL_SSH_KEY=~/.ssh/id_ed25519

./scripts/wsl_plugin_mvp_stack.sh up
./scripts/wsl_plugin_mvp_stack.sh check
```

**Preflight (checklist + optional Ask E2E):**

```bash
./scripts/motadata_integration_preflight.sh
# After git pull in m-coder:
# ./scripts/motadata_integration_preflight.sh --fresh
```

**Probe only (no `up`):** `./scripts/motadata_integration_preflight.sh --verify-only`

**Stack control without full preflight:** `./scripts/wsl_plugin_mvp_stack.sh {status|down|restart}`

**Same-path names:** scripts accept `MOTADATA_ROOT` or `MOTADATA_REPO_ROOT` (keep them the same).

---

## 3) API scenarios (what each “product” action hits)

There is **no separate HTTP `/agent`** route. The **assist layer** runs **inside** Plan-Gate on **`/v0/ask` and `/v1/ask`** (advisory metadata in the response). **“Agent”** behavior in docs means the governed orchestration behind execute — still via **`/v0/execute`**, not a separate public “agent” URL.

| User intent | Context Layer (WSL) | Plan-Gate (GPU) | vLLM (GPU) | Notes |
|-------------|---------------------|-----------------|------------|--------|
| **Plan** (commit / CI / policy decision) | — | **`POST /v0/plan`** | No | `PlanRequest` → `DecisionResponse`. CI helper: `python3 -m runtime.ci_gate.cli` → [`runtime/ci_gate/README.md`](../../../runtime/ci_gate/README.md). |
| **Ask (default)** | Optional | **`POST /v0/ask`** | No for basic plan text; optional for explain | Repo-aware plan-only; no execution. |
| **Ask (evidence-first)** | **`POST /v1/export_evidence`** | **`POST /v1/ask`** | No for core plan | **Recommended** E2E path: bundle → `ask_request.v1.0`. |
| **Explain / Debug** | **`POST /v1/export_evidence`** (optional) | **`POST /v0/ask`** or **`/v1/ask`** with `task_type` / selection fields per schema | **`POST …/v1/chat/completions`** (when Explain is enabled) | Structured `explain_debug` when vLLM is up. |
| **Code / execute** | — | **`POST /v0/execute`** | No | Governed execution only (not free-form chat). |
| **Health / discovery** | **`GET /healthz`**, **`GET /version`** | **`GET /healthz`**, **`GET /version`** | **`GET /v1/models`** | Use before any POST. |

**Plan-Gate HTTP surface** (stdlib service): `/v0/plan`, `/v0/ask`, `/v1/ask`, `/v0/execute` — see [`runtime/plan_gate_service/README.md`](../../../runtime/plan_gate_service/README.md).

---

## 4) CLI end-to-end (no JetBrains plugin)

On **any machine** where Context Layer + Plan-Gate are reachable (same host as WSL, or tunneled):

```bash
cd "$M_CODER_ROOT"
./runtime/scripts/run_local_stack.sh start-plan-gate    # skip if Plan-Gate already on :8089
./runtime/scripts/run_local_stack.sh start-context
./runtime/scripts/run_local_stack.sh health

QUERY='your question about the repo' \
WORKSPACE_ROOT=/abs/path/to/Motadata \
bash runtime/scripts/cli_e2e_verify.sh
```

This runs [`runtime/scripts/verify_ask_path.sh`](../../../runtime/scripts/verify_ask_path.sh): **`/v1/export_evidence` → `POST /v1/ask`**.

**Optional:** preflight Ask E2E: `VERIFY_ASK_E2E=1` with `WORKSPACE_ROOT` / `PREFLIGHT_ASK_QUERY` — see `motadata_integration_preflight.sh` header.

---

## 5) Manual testing and verification (consistent checklist)

Use this matrix when you need deterministic manual proof for each requirement:
**query, debug, plan, code, agent**.

### 5.1 Pre-conditions (must pass first)

```bash
cd "$M_CODER_ROOT"
./runtime/scripts/run_local_stack.sh health
./runtime/scripts/governed_services.sh status
```

Expected:
- Context Layer `:8091` -> `OK`
- Plan-Gate `:8089` -> `OK`
- vLLM `:8000` -> `OK` (required for explain/debug quality)

### 5.2 Behavior matrix (manual)

| Requirement | Command/API flow | Deterministic pass criteria |
|-------------|------------------|-----------------------------|
| **Query** | `POST /v1/export_evidence` -> `POST /v1/ask` | `ask_path=v1_evidence`; `governance_posture=PLAN_ONLY`; `execution=false`; non-empty `plan_summary.steps` |
| **Debug** | `POST /v1/ask` with `task_type=EXPLAIN_DEBUG`, `selected_file`, `client_context.selection` | `routing_mode=explain_debug`; `explain_debug.summary` present (or explicit `explain_debug.error`) |
| **Plan** | `POST /v0/plan` | response `schema_version=decision_response.v0.1`; non-empty `decision` |
| **Code** | `POST /v0/execute` | response `schema_version=execute_response.v0.1`; non-empty `outcome`; explicit `executed` boolean |
| **Agent** | Probe `/v0/agent` + inspect Ask response | `/v0/agent` returns `404` (expected); Ask response includes `assist_layer` metadata |

### 5.3 One command for full manual verification

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/you/Projects/Motadata" \
  --repeat 2
```

Report path:
- `runtime/.run/motadata_behavior_validation.json`

Pass rule:
- `all_pass == true`
- `stable == true` when `--repeat > 1`

---

## 6) Automated verification (repeatable)

The verifier script above is the canonical no-plugin behavior test for this guide.
It validates:
- Health of Context Layer / Plan-Gate / vLLM
- Query path (`/v1/export_evidence` + `/v1/ask`)
- Debug path (`EXPLAIN_DEBUG`)
- Plan contract (`/v0/plan`)
- Code contract (`/v0/execute`)
- Agent semantics (no dedicated `/v0/agent`, assist metadata on Ask)

Useful options:

```bash
python3 runtime/scripts/motadata_behavior_verify.py --help
```

Common custom run:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/you/Projects/Motadata" \
  --query "How does alert correlation and enrichment work?" \
  --debug-query "Debug why incident enrichment might be skipped" \
  --top-k 8 \
  --repeat 3 \
  --out runtime/.run/motadata_behavior_validation.motadata.json
```

---

## 7) Packaging (optional)

| Goal | Command |
|------|---------|
| Sync versions | `./scripts/motadata_packaging.sh sync-versions` (from `scripts/motadata_versions.env`) |
| Build Context Layer wheel | `./scripts/motadata_packaging.sh build-wheel` |
| Build JetBrains plugin zip | `./scripts/motadata_packaging.sh build-plugin` |

Context Layer modes for `wsl_plugin_mvp_stack.sh`: `CONTEXT_LAYER_LAUNCH_MODE=inrepo` (default) or `wheel` + `MOTADATA_CONTEXT_LAYER_VENV`.

---

## 8) Logs (when something fails)

Under **`$M_CODER_ROOT/runtime/.run/`**: `wsl_context_layer.log`, `wsl_plan_gate_tunnel.log`, `motadata_preflight_*.log`. On GPU: `runtime/.run/plan_gate.log`, `vllm.log` from `governed_services.sh`.

---

## 9) Further reading

| Topic | Location |
|--------|----------|
| Plugin demo, tunnels, JVM flags | [`docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md`](../../runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md) |
| End-to-end trace / endpoint map | [`docs/First-Production-MVP-Slice.md`](../../First-Production-MVP-Slice.md) |
| Plugin truth-proof matrix | [`docs/validation/PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md`](../../validation/PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md) |
| Repo layout | [`docs/audit/REPO_LAYOUT_INVENTORY.md`](../../audit/REPO_LAYOUT_INVENTORY.md) |

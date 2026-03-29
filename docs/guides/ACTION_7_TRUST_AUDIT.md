# Host Profile A — closure proof-pack (Action 9)

**Scope:** Operational runbook for a disciplined **JetBrains IDE on WSL backend** + **Context Layer** + **Plan-Gate / vLLM** validation pass. No Windows-side tunnel or Windows `curl` steps — everything below assumes the **IDE backend JVM and your shells run in Linux (WSL)**.

**Action 7** (execute trust) is documented complete elsewhere; this is **Action 9 Host-A proof**, not an Action 7 code audit.

**Paths:**

| Role | Path / host |
|------|-------------|
| **MCODER_ROOT** (tooling only) | Repo used to start GPU governed services and Context Layer, e.g. `/home/harshil/Harshil-PoCs/m-coder` or `/root/Harshil-PoCs/m-coder`. Not the product under test. |
| **MOTADATA_ROOT** (audited workspace) | Motadata AIOps root, e.g. `/home/harshil/Projects/Motadata`. All Ask / Explain / Execute / no-match scenarios use this project in the IDE. |
| **Context Layer** | Default `http://127.0.0.1:8091` from the WSL backend (same machine as the IDE). Bind with `MOTADATA_CONTEXT_LAYER_HOST=0.0.0.0` if you need non-loopback access. |
| **Plan-Gate / Ask / Execute** | Plugin default `http://127.0.0.1:8089` — hardcoded in `RuntimeBridge` / `AskClient`. That port must reach Plan-Gate **from the WSL backend** (local process or port-forward). |

**Non-negotiable:** Use **JetBrains Remote Development with WSL backend** (or pure Linux IDE) so `repo_root` / `workspace_root` are Linux paths. Set **VM options on the backend IDE**, not only on a Windows thin client. If correlation is missing, mark **NOT_PROVEN**.

---

## Overview

1. (Optional) If Plan-Gate/vLLM run on a **remote GPU**, open an **SSH port-forward from WSL** to `127.0.0.1:8089` and `127.0.0.1:8000` on the GPU.
2. Start **GPU services** on the GPU host from `MCODER_ROOT` (`governed_services.sh`).
3. Start **Context Layer** on the WSL dev machine from `MCODER_ROOT` (`python3 -m runtime.context_layer_service.app` or wheel).
4. Configure **backend** VM options: evidence-first + Context Layer URL (`http://127.0.0.1:8091`).
5. Open **MOTADATA_ROOT** in the IDE; run five scenarios; capture artifacts.

---

## STEP 0 — Evidence folder (Linux)

```bash
ts=$(date +%Y%m%d_%H%M%S)
mkdir -p "$HOME/action9_hostA_$ts"/{health,ask,debug,execute_ok,execute_blocked,execute_failed,nomatch,failure,logs}
cd "$HOME/action9_hostA_$ts"
```

---

## STEP 1 — GPU services (on the GPU host)

SSH into the machine where vLLM and Plan-Gate listen on `127.0.0.1`.

### 1.1 Start

```bash
export MCODER_ROOT=/home/harshil/Harshil-PoCs/m-coder   # adjust
cd "$MCODER_ROOT/runtime/scripts"
bash governed_services.sh start
```

Wait **15–30 s**.

### 1.2 Verify (on GPU)

```bash
curl -sS http://127.0.0.1:8000/v1/models
curl -sS http://127.0.0.1:8089/healthz
curl -sS http://127.0.0.1:8089/version
```

### 1.3 Save artifacts

```bash
curl -sS http://127.0.0.1:8000/v1/models > ~/health_gpu_models.json
curl -sS http://127.0.0.1:8089/healthz > ~/health_gpu_pg.txt
curl -sS http://127.0.0.1:8089/version > ~/health_gpu_version.json
```

### 1.4 Logs (optional)

```bash
cd "$MCODER_ROOT"
tail -f .run/plan_gate.log
# other terminal: tail -f .run/vllm.log
```

---

## STEP 2 — WSL → GPU port forward (only if GPU is remote)

Run on the **WSL machine where the IDE backend runs**, so `127.0.0.1:8089` / `8000` there map to the GPU’s local services.

```bash
ssh -N -L 8089:127.0.0.1:8089 -L 8000:127.0.0.1:8000 <user>@<gpu-host>
```

If local **8000** is busy, use another local port (example **18000**):

```bash
ssh -N -L 8089:127.0.0.1:8089 -L 18000:127.0.0.1:8000 <user>@<gpu-host>
```

Keep this session open. Verify **from WSL**:

```bash
curl -sS http://127.0.0.1:8089/healthz
curl -sS http://127.0.0.1:8000/v1/models
# or: curl -sS http://127.0.0.1:18000/v1/models
```

Save under `health/` if you want proof files:

```bash
curl -sS http://127.0.0.1:8089/healthz > health/wsl_tunnel_pg.txt
curl -sS http://127.0.0.1:8000/v1/models > health/wsl_tunnel_models.json
```

**If Plan-Gate and vLLM already run on the same WSL box as the IDE**, skip this step — use Step 1 checks on localhost only.

**Context Layer** stays on the WSL dev host; it is **not** forwarded through this GPU tunnel.

---

## STEP 3 — Context Layer (WSL dev host)

Same Linux environment as the IDE backend (usually same WSL distro as `MOTADATA_ROOT`).

```bash
export MCODER_ROOT=/home/harshil/Harshil-PoCs/m-coder
cd "$MCODER_ROOT"
export PYTHONPATH="$PWD"
export MOTADATA_CONTEXT_LAYER_HOST=0.0.0.0
export MOTADATA_CONTEXT_LAYER_PORT=8091
# optional: export MOTADATA_CONTEXT_LAYER_DEBUG_EXPORT=1
python3 -m runtime.context_layer_service.app
```

Verify:

```bash
curl -sS http://127.0.0.1:8091/healthz
curl -sS http://127.0.0.1:8091/version
```

### Export smoke (Motadata)

```bash
export MOTADATA_ROOT=/home/harshil/Projects/Motadata
curl -sS -X POST http://127.0.0.1:8091/v1/export_evidence \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"Vert.x HTTP router or bootstrap\",\"workspace_root\":\"$MOTADATA_ROOT\",\"top_k\":8,\"request_id\":\"smoke-manual-1\"}" \
  | tee "$HOME/sample_evidence_motadata.json" | head -c 2000
```

---

## STEP 4 — JetBrains (WSL backend)

### 4.1 VM options (backend IDE window)

**Help → Edit Custom VM Options** on the **remote / WSL** IDE (not the Windows Gateway thin client unless that is where the plugin runs — your validated setup is **backend on WSL**):

```text
-Dmotadata.ask.evidence_first=true
-Dmotadata.context_layer.url=http://127.0.0.1:8091
```

Use **`127.0.0.1`**, not `0.0.0.0`, for the client URL. Restart the backend IDE.

### 4.2 Endpoints

| Service | URL | Notes |
|---------|-----|--------|
| Plan-Gate | `http://127.0.0.1:8089` | Hardcoded in plugin; must be reachable from WSL backend (forward or local). |
| Context Layer | `http://127.0.0.1:8091` | Override via `-Dmotadata.context_layer.url` or `MOTADATA_CONTEXT_LAYER_URL`. |

### 4.3 Project

Open **MOTADATA_ROOT** only (Linux path). Tooling terminals use **MCODER_ROOT**; no second product window required for this pack.

---

## STEP 5 — Scenarios (Motadata)

Use **PASS** / **FAIL** / **NOT_PROVEN**. Missing **request_id** or log link → **NOT_PROVEN**.

### 5.1 Ask v1 (evidence-first)

Example queries: Vert.x bootstrap / router; alert ingestion; deduplication / correlation.

Capture under `ask/`: `request_id.txt`, screenshot, Plan-Gate snippet, Context Layer snippet.

### 5.2 Explain / Debug

Select code → Explain/Debug. Capture under `debug/`.

### 5.3 Execute (×3)

| Case | Command | Expected |
|------|---------|----------|
| OK | `echo hello` | EXECUTED |
| Blocked | `rm -rf /` (or policy-blocked) | BLOCKED |
| Failed | `python3 -c "import sys; sys.exit(1)"` | EXECUTED_FAILED |

Capture under `execute_ok/`, `execute_blocked/`, `execute_failed/`.

### 5.4 No-match

Query: `Where is nonexistent_xyz_function_12345 defined?` Capture under `nomatch/`.

### 5.5 Failure mode

e.g. stop Plan-Gate, retry Ask. Capture under `failure/`.

---

## STEP 6 — Trace matrix

| request_id | Plugin | Context Layer log | Plan-Gate | vLLM (Explain) |
|------------|--------|---------------------|-----------|----------------|
| … | Y/N | Y/N | Y/N | Y/N / n/a |

---

## STEP 7 — Decision

| Scenario | Status |
|----------|--------|
| Ask | PASS / FAIL / NOT_PROVEN |
| Explain/Debug | … |
| Execute (3) | … |
| No-match | … |
| Failure | … |

---

## Common failure points (WSL backend layout)

| Symptom | Cause |
|---------|--------|
| Ask hits `/v0/ask` only | evidence-first off on **backend** VM options, or export failed → fallback. |
| No `DEBUG` / no CL log on Ask | IDE not using backend VM options; or wrong `motadata.context_layer.url`. |
| `workspace_export_failed` | Bad `MOTADATA_ROOT` or stale Context Layer; pull latest `app.py` / wheel. |
| `RUNTIME_UNAVAILABLE` | Plan-Gate not on `127.0.0.1:8089` from WSL; tunnel dead or wrong port. |
| vLLM errors on Explain | GPU `MOTADATA_EXPLAIN_VLLM_URL` / vLLM down; tunnel to 8000 if remote. |

---

## Mindset

For each scenario, prove the **same request_id** (or explicit **NOT_PROVEN**) across plugin output and service logs.

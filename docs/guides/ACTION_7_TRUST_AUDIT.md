# Host Profile A — closure proof-pack (Action 9)

**Scope:** This is the **operational runbook** for a single disciplined **Windows JetBrains + WSL Context Layer + GPU Plan-Gate/vLLM** validation pass.  
**Action 7** (execute trust on the live HTTP product path) is documented as complete elsewhere; this runbook is for **Action 9 Host-A proof**, not a repeat Action 7 code audit.

**Fixed layout (customize only the table below if your machine differs):**


| Role                                                               | Path / host                                                                                                                                 |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **m-coder** (GPU scripts, Context Layer source, Plan-Gate in repo) | `/home/harshil/Harshil-PoCs/m-coder` **or** `/root/Harshil-PoCs/m-coder` — pick **one** and use it everywhere in this doc as `MCODER_ROOT`. |
| **Motadata** (product repo for grounded Ask)                       | `/home/harshil/Projects/Motadata`                                                                                                           |
| **Context Layer bind**                                             | `0.0.0.0:8091` (so Windows `curl` / IDE can reach WSL without guessing)                                                                     |
| **Plan-Gate / Execute / Ask** (plugin default)                     | `http://127.0.0.1:8089` — plugin **hardcodes** this; tunnel must present Plan-Gate on **Windows localhost 8089**.                           |


**Non-negotiable:** For Motadata Ask, `workspace_root` sent to Context Layer must be a **Linux path that exists where Context Layer runs**. If the IDE plugin runs on **Windows** only, `project.basePath` may be `//wsl.localhost/...` and export will fail — use **JetBrains remote/WSL backend** for the Motadata project, or accept **NOT_PROVEN** for Ask until paths are Linux. Opening **m-coder** on the WSL backend is fine for the **PlanGateService** smoke query.

---

## Overview (what you are doing)

1. Start **GPU services** (Plan-Gate + vLLM + deps as per `governed_services.sh`).
2. Start **Context Layer** in **WSL** on `**0.0.0.0:8091`**.
3. Create **Windows → GPU** SSH tunnel for **8000** and **8089**.
4. Configure **JetBrains** VM options (evidence-first + Context Layer URL).
5. Run **five scenarios** (Ask ×2 repos, Explain/Debug, Execute ×3, No-match, Failure).
6. Capture **request_id**, logs, and screenshots under a dated folder.

---

## STEP 0 — Capture workspace (Windows)

**PowerShell:**

```powershell
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
mkdir C:\action9_hostA_$ts
cd C:\action9_hostA_$ts
mkdir health, ask_mcoder, ask_motadata, debug, execute_ok, execute_blocked, execute_failed, nomatch, failure, logs
```

---

## STEP 1 — GPU services

**SSH or WSL shell on the GPU host** (same machine where vLLM/Plan-Gate listen on **127.0.0.1** inside that OS).

### 1.1 Repo

```bash
export MCODER_ROOT=/home/harshil/Harshil-PoCs/m-coder
cd "$MCODER_ROOT/runtime/scripts"
bash governed_services.sh start
```

Wait **15–30 s** for listeners.

### 1.2 Verify vLLM

```bash
curl -sS http://127.0.0.1:8000/v1/models
```

Expect JSON including a `data` array of models.

### 1.3 Verify Plan-Gate

```bash
curl -sS http://127.0.0.1:8089/healthz
curl -sS http://127.0.0.1:8089/version
```

Expect `healthz` OK JSON; `version` JSON should list supported schemas (e.g. `ask_request_v1`).

### 1.4 Save artifacts (GPU home)

```bash
curl -sS http://127.0.0.1:8000/v1/models > ~/health_gpu_models.json
curl -sS http://127.0.0.1:8089/healthz > ~/health_gpu_pg.txt
curl -sS http://127.0.0.1:8089/version > ~/health_gpu_version.json
```

### 1.5 Logs (two terminals, leave open)

```bash
cd "$MCODER_ROOT"
tail -f .run/plan_gate.log
```

```bash
cd "$MCODER_ROOT"
tail -f .run/vllm.log
```

---

## STEP 2 — Context Layer (WSL)

**New WSL terminal** (same distro where Motadata and m-coder paths live).

### 2.1 Start (bind all interfaces — required for Windows → WSL)

```bash
export MCODER_ROOT=/home/harshil/Harshil-PoCs/m-coder
cd "$MCODER_ROOT"
export PYTHONPATH=.
export MOTADATA_CONTEXT_LAYER_HOST=0.0.0.0
export MOTADATA_CONTEXT_LAYER_PORT=8091
python3 -m runtime.context_layer_service.app
```

Expect stderr: `Context Layer listening on http://0.0.0.0:8091/healthz`.

### 2.2 Verify inside WSL

```bash
curl -sS http://127.0.0.1:8091/healthz
curl -sS http://127.0.0.1:8091/version
```

### 2.3 Evidence export smoke (two workspaces)

**m-coder (PlanGateService exists here):**

```bash
curl -sS -X POST http://127.0.0.1:8091/v1/export_evidence \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"PlanGateService\",\"workspace_root\":\"$MCODER_ROOT\",\"top_k\":8}" \
  | tee ~/sample_evidence_mcoder.json | head -c 2000
```

**Motadata (product repo):**

```bash
curl -sS -X POST http://127.0.0.1:8091/v1/export_evidence \
  -H "Content-Type: application/json" \
  -d '{"query":"Vert.x bootstrap","workspace_root":"/home/harshil/Projects/Motadata","top_k":8}' \
  | tee ~/sample_evidence_motadata.json | head -c 2000
```

Each response should be JSON with `schema_hint` / bundle fields per service contract; if you get `export_failed` / wrong `workspace_root`, fix paths before using the plugin.

---

## STEP 3 — Windows → GPU tunnel

**PowerShell on Windows** (replace user/host):

```powershell
ssh -N -L 8000:127.0.0.1:18000 -L 8089:127.0.0.1:8089 harshil@45.195.82.10
```

Keep this window open.

### Verify from Windows

```powershell
curl.exe -sS http://127.0.0.1:8089/healthz
curl.exe -sS http://127.0.0.1:18000/v1/models
```

Save:

```powershell
curl.exe -sS http://127.0.0.1:8089/healthz > health\windows_pg.txt
curl.exe -sS http://127.0.0.1:18000/v1/models > health\windows_models.json
```

**Context Layer is not tunneled here** — it runs in **local WSL**; Windows reaches it at `**http://127.0.0.1:8091`** if WSL port forwarding is active (or use WSL IP from `hostname -I` in VM options — same as your four-step procedure).

---

## STEP 4 — JetBrains (Windows client + WSL repos)

### 4.1 VM options

**Help → Edit Custom VM Options** — add:

```text
-Dmotadata.ask.evidence_first=true
-Dmotadata.context_layer.url=http://127.0.0.1:8091
```

Restart the IDE.

### 4.2 Endpoints (current plugin behavior)


| Service                   | URL                                 | How set                                                             |
| ------------------------- | ----------------------------------- | ------------------------------------------------------------------- |
| Plan-Gate (Ask / Execute) | `http://127.0.0.1:8089`             | **Hardcoded** in `RuntimeBridge` / `AskClient` — tunnel must match. |
| Context Layer             | `http://127.0.0.1:8091` (or WSL IP) | `-Dmotadata.context_layer.url=...` or `MOTADATA_CONTEXT_LAYER_URL`. |


### 4.3 Open projects

- **Smoke (m-coder):** open `MCODER_ROOT` on **WSL backend** so Ask uses Linux `repo_root` (e.g. `/home/harshil/Harshil-PoCs/m-coder`).
- **Product (Motadata):** open `/home/harshil/Projects/Motadata` on **WSL backend** so `repo_root` / `workspace_root` are Linux.

---

## STEP 5 — Scenarios

Use `**PASS` / `FAIL` / `NOT_PROVEN`** per row. If **request_id** or any log link is missing, mark **NOT_PROVEN** (do not leave blank).

### 5.1 Ask v1 — m-coder

**Query:** `Where is PlanGateService defined?`

Capture under `ask_mcoder\`: `request_id.txt`, `plugin.png`, `pg_log_snippet.txt`, `context_log_snippet.txt`.

### 5.2 Ask v1 — Motadata

**Query:** e.g. `Where is the main Vert.x bootstrap or HTTP router setup for this platform?`

Same captures under `ask_motadata\`.

### 5.3 Explain / Debug

Select real code → run Explain/Debug from the plugin.

Capture under `debug\`: `request_id.txt`, `plugin.png`, Plan-Gate line, Context Layer line, **vLLM** line showing chat/completions if Explain uses vLLM.

### 5.4 Execute (three outcomes)

Run **Submit to Runtime** from m-coder project (or same repo your sandbox uses):


| Case           | Command                                | Expected outcome class |
| -------------- | -------------------------------------- | ---------------------- |
| OK             | `echo hello`                           | `EXECUTED`             |
| Blocked        | `rm -rf /` (or other policy-blocked)   | `BLOCKED`              |
| Ran but failed | `python3 -c "import sys; sys.exit(1)"` | `EXECUTED_FAILED`      |


Capture per folder `execute_ok`, `execute_blocked`, `execute_failed`: `request_id.txt`, `plugin.png`, `pg_log_snippet.txt`.

### 5.5 No-match

**Query:** `Where is nonexistent_xyz_function_12345 defined?`

Capture under `nomatch\` (same pattern as Ask).

### 5.6 Failure mode

Provoke a clear failure (e.g. stop Plan-Gate temporarily and retry Ask — expect unavailable / honest error). Capture under `failure\`.

---

## STEP 6 — Trace matrix (mandatory)

For each main scenario, one row:


| request_id | Plugin visible | Context Layer log | Plan-Gate log | vLLM log (Explain only) |
| ---------- | -------------- | ----------------- | ------------- | ----------------------- |
| …          | Y/N            | Y/N               | Y/N           | Y/N / n/a               |


Any missing correlation → **NOT_PROVEN** for that scenario.

---

## STEP 7 — Decision


| Scenario      | Status                   |
| ------------- | ------------------------ |
| Ask m-coder   | PASS / FAIL / NOT_PROVEN |
| Ask Motadata  | PASS / FAIL / NOT_PROVEN |
| Explain/Debug | PASS / FAIL / NOT_PROVEN |
| Execute (3)   | PASS / FAIL / NOT_PROVEN |
| No-match      | PASS / FAIL / NOT_PROVEN |
| Failure       | PASS / FAIL / NOT_PROVEN |


**Branch:** all required rows **PASS** → close Action 9 Host-A; any single **TRUE_PRODUCT_BLOCKER** → one surgical fix; else **docs/env** follow-up.

---

## Common failure points (this layout)


| Symptom                                   | Cause                                                                                    |
| ----------------------------------------- | ---------------------------------------------------------------------------------------- |
| Tunnel dies                               | SSH session closed — Plan-Gate/vLLM unreachable from Windows.                            |
| `evidence_first` off                      | Ask may skip v1 evidence path — VM option missing.                                       |
| `root_path does not exist` / UNC in error | Plugin on Windows sending `//wsl.localhost/...` — use WSL backend project or NOT_PROVEN. |
| `127.0.0.1:8091` refused on Windows       | Context Layer not bound to `0.0.0.0` or WSL forwarding / wrong IP in VM options.         |
| Execute always `RUNTIME_UNAVAILABLE`      | Tunnel or Plan-Gate down; or wrong port.                                                 |


---

## Mindset

You are proving: **for one request_id, the same id appears in plugin-visible output and in the relevant service logs.**  
If the chain is incomplete → **NOT_PROVEN**, not PASS.
# Host Profile A — closure proof-pack (Action 9)

**Scope:** This is the **operational runbook** for a single disciplined **Windows JetBrains + WSL Context Layer + GPU Plan-Gate/vLLM** validation pass.  
**Action 7** (execute trust on the live HTTP product path) is documented as complete elsewhere; this runbook is for **Action 9 Host-A proof**, not a repeat Action 7 code audit.

**Two paths, one audited workspace:**


| Role                                           | Path / host                                                                                                                                                                                           |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `**MCODER_ROOT`** (tooling only)               | Checkout used to **start** GPU governed services and **run** Context Layer from this repo, e.g. `/home/harshil/Harshil-PoCs/m-coder` or `/root/Harshil-PoCs/m-coder`. **Not** the product under test. |
| `**MOTADATA_ROOT`** (only workspace audited)   | Motadata AIOps repo root, e.g. `/home/harshil/Projects/Motadata`. **All** Ask / Explain / Execute / no-match scenarios use this project open in the IDE.                                              |
| **Context Layer bind**                         | `0.0.0.0:8091` (so Windows `curl` / IDE can reach WSL without guessing).                                                                                                                              |
| **Plan-Gate / Ask / Execute** (plugin default) | `http://127.0.0.1:8089` — plugin **hardcodes** this; tunnel must present Plan-Gate on **Windows localhost 8089**.                                                                                     |


**Non-negotiable:** `workspace_root` / `repo_root` for the plugin must resolve to a **real Linux directory** where Context Layer runs. If the IDE sends `/mnt/wsl.localhost/...`, use a **current Context Layer wheel** that maps that bridge path to `/home/...`, or open the project via a **Linux** path in the WSL backend. If correlation is missing, mark **NOT_PROVEN**.

---

## Overview (what you are doing)

1. Start **GPU services** from `MCODER_ROOT` (`governed_services.sh`).
2. Start **Context Layer** in **WSL** on `0.0.0.0:8091` (from `MCODER_ROOT`).
3. Create **Windows → GPU** SSH tunnel for **vLLM** and **Plan-Gate** ports.
4. Configure **JetBrains** VM options (evidence-first + Context Layer URL).
5. Open **only** `MOTADATA_ROOT` in the IDE and run **five scenarios**: Ask v1, Explain/Debug, Execute (×3), No-match, Failure.
6. Capture **request_id**, logs, and screenshots under a dated folder.

---

## STEP 0 — Capture workspace (Windows)

**PowerShell:**

```powershell
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
mkdir C:\action9_hostA_$ts
cd C:\action9_hostA_$ts
mkdir health, ask, debug, execute_ok, execute_blocked, execute_failed, nomatch, failure, logs
```

---

## STEP 1 — GPU services

**SSH or WSL shell on the GPU host** (where vLLM and Plan-Gate listen on `127.0.0.1`).

### 1.1 Repo (tooling checkout)

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

Expect JSON including a `data` array of models. (If vLLM uses another port locally, substitute it here and in your tunnel.)

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

**WSL terminal** on the same distro where `MOTADATA_ROOT` exists.

### 2.1 Start (bind all interfaces — required for Windows → WSL)

```bash
export MCODER_ROOT=/home/harshil/Harshil-PoCs/m-coder
cd "$MCODER_ROOT"
export PYTHONPATH=.
export MOTADATA_CONTEXT_LAYER_HOST=0.0.0.0
export MOTADATA_CONTEXT_LAYER_PORT=8091
python3 -m runtime.context_layer_service.app
```

Or, after installing the wheel: `motadata-context-layer` with the same env vars.

Expect: `Context Layer listening on http://0.0.0.0:8091/healthz`.

### 2.2 Verify inside WSL

```bash
curl -sS http://127.0.0.1:8091/healthz
curl -sS http://127.0.0.1:8091/version
```

### 2.3 Evidence export smoke (Motadata only)

Set `MOTADATA_ROOT` to your real path, then:

```bash
export MOTADATA_ROOT=/home/harshil/Projects/Motadata
curl -sS -X POST http://127.0.0.1:8091/v1/export_evidence \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"Vert.x HTTP router or bootstrap\",\"workspace_root\":\"$MOTADATA_ROOT\",\"top_k\":8}" \
  | tee ~/sample_evidence_motadata.json | head -c 2000
```

Expect JSON with `schema_hint` consistent with `layer5.evidence_bundle.v1`. If you get `export_failed`, fix `workspace_root` or upgrade Context Layer (bridge-path normalization) before using the plugin.

---

## STEP 3 — Windows → GPU tunnel

**PowerShell on Windows** (replace user/host and local ports as needed).

**Typical** (vLLM on remote `8000`, Plan-Gate on `8089`):

```powershell
ssh -N -L 8000:127.0.0.1:8000 -L 8089:127.0.0.1:8089 <user>@<gpu-host>
```

If **Windows port 8000** is busy, forward vLLM to another local port (example **18000**):

```powershell
ssh -N -L 18000:127.0.0.1:8000 -L 8089:127.0.0.1:8089 <user>@<gpu-host>
```

Keep this window open.

### Verify from Windows

```powershell
curl.exe -sS http://127.0.0.1:8089/healthz
curl.exe -sS http://127.0.0.1:8000/v1/models
```

If you used local **18000** for vLLM:

```powershell
curl.exe -sS http://127.0.0.1:18000/v1/models
```

Save:

```powershell
curl.exe -sS http://127.0.0.1:8089/healthz > health\windows_pg.txt
curl.exe -sS http://127.0.0.1:8000/v1/models > health\windows_models.json
```

(Adjust the models URL if you used `18000`.)

**Context Layer is not tunneled here** — it runs in **local WSL**; Windows reaches it at `http://127.0.0.1:8091` (or the WSL IP in VM options).

---

## STEP 4 — JetBrains (Motadata project only)

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


### 4.3 Open project

- Open `**MOTADATA_ROOT`** only (e.g. `/home/harshil/Projects/Motadata`) on the **WSL backend** when possible so `repo_root` is a Linux path.
- Do **not** rely on a second **m-coder** IDE window for this proof-pack; tooling runs from `MCODER_ROOT` in terminals only.

---

## STEP 5 — Scenarios (Motadata workspace)

Use **PASS** / **FAIL** / **NOT_PROVEN** per row. If **request_id** or any log link is missing, mark **NOT_PROVEN** (do not leave blank).

### 5.1 Ask v1 (evidence-first)

**Example queries (pick one that should hit real code):**

- `Where is the main Vert.x bootstrap or HTTP router setup for this platform?`
- `Where is alert ingestion or normalization implemented?`
- `Where is incident deduplication or correlation logic defined?`

Capture under `ask\`: `request_id.txt`, `plugin.png`, `pg_log_snippet.txt`, `context_log_snippet.txt`.

Confirm in Plan-Gate logs you see the **v1** evidence path when evidence-first succeeds (not only legacy `/v0/ask` if that is your pass criterion — align with your tracker).

### 5.2 Explain / Debug

Select real Motadata code → run Explain/Debug from the plugin.

Capture under `debug\`: `request_id.txt`, `plugin.png`, Plan-Gate line, Context Layer line, **vLLM** line showing `/chat/completions` when Explain uses vLLM.

### 5.3 Execute (three outcomes)

With **Motadata** project open, use **Submit to Runtime**:


| Case           | Command                                      | Expected outcome class |
| -------------- | -------------------------------------------- | ---------------------- |
| OK             | `echo hello`                                 | `EXECUTED`             |
| Blocked        | `rm -rf /` (or other policy-blocked command) | `BLOCKED`              |
| Ran but failed | `python3 -c "import sys; sys.exit(1)"`       | `EXECUTED_FAILED`      |


Sandbox policy must allow the “failed” command; adjust if your policy blocks `python3`.

Capture per folder `execute_ok`, `execute_blocked`, `execute_failed`: `request_id.txt`, `plugin.png`, `pg_log_snippet.txt`.

### 5.4 No-match

**Query:** `Where is nonexistent_xyz_function_12345 defined?`

Expect honest insufficiency / plan-only / no fake grounding. Capture under `nomatch\` (same pattern as Ask).

### 5.5 Failure mode

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


| Scenario       | Status                   |
| -------------- | ------------------------ |
| Ask (Motadata) | PASS / FAIL / NOT_PROVEN |
| Explain/Debug  | PASS / FAIL / NOT_PROVEN |
| Execute (3)    | PASS / FAIL / NOT_PROVEN |
| No-match       | PASS / FAIL / NOT_PROVEN |
| Failure        | PASS / FAIL / NOT_PROVEN |


**Branch:** all required rows **PASS** → close Action 9 Host-A; any single **TRUE_PRODUCT_BLOCKER** → one surgical fix; else **docs/env** follow-up.

---

## Common failure points (this layout)


| Symptom                                          | Cause                                                                                                                |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| Tunnel dies                                      | SSH session closed — Plan-Gate/vLLM unreachable from Windows.                                                        |
| `evidence_first` off                             | Ask may skip v1 evidence path — VM option missing.                                                                   |
| `workspace_export_failed` / bad `workspace_root` | Wrong path, or bridge path — upgrade Context Layer or open project via Linux `MOTADATA_ROOT`.                        |
| `127.0.0.1:8091` refused on Windows              | Context Layer not bound to `0.0.0.0` or WSL forwarding / wrong IP in VM options.                                     |
| Execute `RUNTIME_UNAVAILABLE`                    | Tunnel or Plan-Gate down; wrong port.                                                                                |
| vLLM `connection refused` on Windows `8000`      | Use alternate local forward (e.g. `18000` → remote `8000`); Plan-Gate on GPU still uses **its** configured vLLM URL. |


---

## Mindset

You are proving: **for one request_id, the same id appears in plugin-visible output and in the relevant service logs.**  
If the chain is incomplete → **NOT_PROVEN**, not PASS.
# Motadata AI Coding Assistant — Deterministic Demo Setup Runbook

**Purpose:** **Ordered** steps **GPU-server → WSL → Windows** with **commands**, **expected outputs**, and **validation gates**. No architecture theory here — see [MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md](MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md).

**Rule:** Do **not** start WSL Context Layer until **Phase 1** passes on the GPU. Do **not** rely on the IDE until **Phase 3** passes on the Windows client.

---

## Chronology (summary)

| Order | Host | What |
|-------|------|------|
| **1** | **GPU-server** | `m-coder` clone, **`VLLM_BASE_MODEL`**, vLLM (**8000**) + Plan-Gate (**8089**), validate HTTP |
| **2** | **WSL** | Motadata AIOps workspace + Context Layer wheel, **`motadata-context-layer`** on **8091**, validate HTTP + `POST /v1/export_evidence` |
| **3** | **Windows** | SSH local forward **8000** + **8089** to GPU, `curl` checks from **Windows**, then JetBrains plugin + VM options |

---

## Operating topology (this runbook)

This runbook assumes one **distributed** layout: **Context Layer** near the workspace (**WSL** here); **Plan-Gate + vLLM** on the **GPU** host — the same architecture as **native Linux** workspace-side; only placement differs. Concrete instance used in validation. **B5 proof artifacts (health + minimal Ask):** `docs/validation/artifacts/b5_linux_backend_gpu/` (native Linux co-located run); **WSL prerequisite checklist:** `docs/validation/artifacts/b5_wsl_backend_gpu/README.md`.

- **JetBrains IDEA runs on Windows** (plugin process lives on Windows).
- **Motadata AIOps repo is hosted in WSL Linux FS** and opened through WSL backend so `project.basePath` is Linux.
- **Context Layer service runs in WSL** on port **8091**.
- **Plan-Gate + vLLM run on GPU** and are reached from Windows through SSH local forwards.

## Canonical values (this deployment)

Change only if your infrastructure differs.

| Item | Value |
|------|--------|
| GPU SSH | `harshil@45.195.82.10` |
| Plan-Gate (on GPU) | `http://127.0.0.1:8089` |
| vLLM (on GPU) | `http://127.0.0.1:8000` |
| Context Layer (WSL) | `http://127.0.0.1:8091` (or WSL IP — below) |
| Example WSL IP (Windows → WSL if localhost fails) | `172.30.127.150` |
| Example Motadata workspace (`workspace_root`) | `/root/Harshil-PoCs/Motadata` |
| GPU: required env | **`VLLM_BASE_MODEL`** — HuggingFace ID or on-disk path |

---

## Fixed ports

| Service | Port | Host |
|---------|------|------|
| vLLM | **8000** | GPU loopback |
| Plan-Gate | **8089** | GPU loopback |
| Context Layer | **8091** | WSL |

---

# Phase 1 — GPU-server

**Goal:** vLLM and Plan-Gate answer HTTP on the GPU; Plan-Gate **`/version`** lists **`ask_request_v1`**.

## 1.1 Prerequisites

- Shell on GPU; **NVIDIA** driver + CUDA suitable for your **vLLM** / PyTorch build.
- Python **3.10+**; git access to **m-coder**.
- Repo root is the directory that **contains** `runtime/`.

## 1.2 Clone and branch (if needed)

```bash
cd ~
git clone git@github.com:harshilshah2501/m-coder.git m-coder
cd ~/m-coder
git checkout feature/l5-context-layer-v1-ask-packaging
```

**Expected:** `git status` shows clean checkout on the intended branch.

## 1.3 Configure stack env

```bash
cd ~/m-coder
cp runtime/config/demo_stack.env.example runtime/config/demo_stack.env
# Edit demo_stack.env: set VLLM_BASE_MODEL to a real HF id or local path, e.g.:
# VLLM_BASE_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
```

## 1.4 Start governed services (recommended)

```bash
cd ~/m-coder
export PYTHONPATH="$(pwd)"
./runtime/scripts/governed_services.sh start
./runtime/scripts/governed_services.sh status
```

**Expected — `status` (illustrative):**

```
═══════════════════════════════════════════════════════════════
  Governed services status
  CONFIG_PATH=.../runtime/config/demo_stack.env
═══════════════════════════════════════════════════════════════

Ports: Plan-Gate=8089  vLLM=8000
plan_gate.pid: <number>
vllm.pid:      <number>

Plan-Gate /healthz: OK
vLLM /v1/models:    OK
```

If either line shows **DOWN**, fix vLLM / Plan-Gate before Phase 2 (see **§8**).

**Expected — start:** no Python traceback; processes stay running (script returns after vLLM is up and Plan-Gate has passed its vLLM healthcheck).

## 1.5 Validation on GPU (mandatory)

Run on the **GPU** (second terminal is fine):

```bash
curl -sS http://127.0.0.1:8000/v1/models | head -c 400
echo
curl -sS http://127.0.0.1:8089/healthz
echo
curl -sS http://127.0.0.1:8089/version
echo
```

**Expected outputs:**

1. **`/v1/models`** — HTTP **200**, JSON with an **`"object":"list"`**-style OpenAI payload and at least one **`id`** in **`data`** (exact shape depends on vLLM version).
2. **`/healthz`** — HTTP **200**, body:

```json
{"status": "ok"}
```

3. **`/version`** — HTTP **200**, JSON including **`supported_schemas`** with **`ask_request_v1`** (e.g. **`"ask_request_v1": "v1.0"`**):

```json
{
  "service_version": "v0.1",
  "supported_schemas": {
    "plan_request": "v0.1",
    "ask_request": "v0.1",
    "ask_request_v1": "v1.0",
    "...": "..."
  }
}
```

## 1.6 Phase 1 gate (all must pass)

| # | Check |
|---|--------|
| P1-1 | `curl http://127.0.0.1:8000/v1/models` → **200** |
| P1-2 | `curl http://127.0.0.1:8089/healthz` → `{"status":"ok"}` |
| P1-3 | `curl http://127.0.0.1:8089/version` → JSON with **`ask_request_v1`** |

**Stop here if any fails.**

---

# Phase 2 — WSL

**Goal:** Context Layer serves **`/healthz`**, **`/version`**, and **`POST /v1/export_evidence`** for a real Motadata Linux path.

**Prerequisite:** Phase **1.6** complete.

**Related:** For **Ask debug-path validation** (record `metadata`, `evidence_quality`, plan responses from **WSL** against Plan-Gate on the GPU), use [DEBUG_PATH_VALIDATION_RUNBOOK.md](DEBUG_PATH_VALIDATION_RUNBOOK.md) after this phase passes.

## 2.1 Motadata workspace

Clone or ensure the **Motadata AIOps** repo exists on **WSL** at the path you will use as **`workspace_root`** (example: **`/root/Harshil-PoCs/Motadata`**).

## 2.2 Context Layer wheel

**Option A — build on GPU, copy to WSL**

On GPU:

```bash
cd ~/m-coder/packaging/motadata-context-layer
python3 -m venv .venv-build && source .venv-build/bin/activate
pip install build
python -m build --wheel -o dist
```

**Expected:** `dist/motadata_context_layer-0.1.0-py3-none-any.whl` exists.

From **WSL**:

```bash
scp harshil@45.195.82.10:~/m-coder/packaging/motadata-context-layer/dist/motadata_context_layer-0.1.0-py3-none-any.whl ~/
```

**Option B — build inside WSL** with an `m-coder` clone — only for building the wheel; not required at runtime.

## 2.3 Install and run (WSL)

```bash
python3 -m venv ~/.venvs/motadata-context-layer && source ~/.venvs/motadata-context-layer/bin/activate
pip install ~/motadata_context_layer-0.1.0-py3-none-any.whl
export MOTADATA_CONTEXT_LAYER_PORT=8091
export MOTADATA_CONTEXT_LAYER_HOST=127.0.0.1
motadata-context-layer
```

**Expected (startup log):** line indicating listener on **`http://127.0.0.1:8091`** (or configured host/port).

If **Windows** cannot reach **`127.0.0.1:8091`**, use:

```bash
export MOTADATA_CONTEXT_LAYER_HOST=0.0.0.0
```

and the plugin VM option **`http://<WSL_IP>:8091`** (get IP: `ip -4 addr show eth0`).

## 2.4 Validation on WSL

```bash
curl -sS http://127.0.0.1:8091/healthz
echo
curl -sS http://127.0.0.1:8091/version
echo
```

**Expected:**

**`/healthz`:**

```json
{
  "status": "ok",
  "service": "motadata_context_layer",
  "package_version": "0.1.0"
}
```

(`package_version` may match your wheel.)

**`/version`:** includes **`evidence_schema_hint": "layer5.evidence_bundle.v1"`** and lists **`POST /v1/export_evidence`**.

## 2.5 POST smoke (WSL)

Replace **`workspace_root`** with your real Motadata Linux path:

```bash
curl -sS -X POST http://127.0.0.1:8091/v1/export_evidence \
  -H 'Content-Type: application/json' \
  -d '{"workspace_root":"/root/Harshil-PoCs/Motadata","query":"test","top_k":8}'
echo
```

**Expected:** HTTP **200**, JSON with **`schema_hint`** = **`layer5.evidence_bundle.v1`** and an **`entries`** array (may be empty depending on query).

## 2.6 Validation from Windows (Context Layer)

If the IDE runs on **Windows**, validate from the same Windows session where IDEA runs.

**Important (PowerShell):** `curl` may be an alias for `Invoke-WebRequest`, and `-sS` will fail there.
Use **`curl.exe`** explicitly or use `Invoke-RestMethod`.

Example:

```powershell
Get-Command curl
```

If that prints `Alias ... Invoke-WebRequest`, use:

```bash
curl.exe -sS http://127.0.0.1:8091/healthz
```

If `127.0.0.1:8091` is unstable from Windows but WSL-local checks pass, use WSL IP and set plugin URL to that IP:

```bash
curl.exe -sS http://172.30.127.150:8091/healthz
```

Expected success body:

```json
{"status": "ok", "service": "motadata_context_layer", "package_version": "0.1.0"}
```

Use your **current** WSL IP (it can change). Get it in WSL with `hostname -I` or `ip -4 addr show eth0`.

## 2.7 Phase 2 gate

| # | Check |
|---|--------|
| P2-1 | WSL: **`/healthz`** and **`/version`** as above |
| P2-2 | WSL: **`POST /v1/export_evidence`** → **200** + **`schema_hint`** = **`layer5.evidence_bundle.v1`** |
| P2-3 | Windows can **`curl`** Context Layer URL you will use in the plugin (**§2.6**) |

---

# Phase 3 — Windows (client)

**Goal:** Local **8089** and **8000** forward to the GPU; plugin sees Plan-Gate at **`http://127.0.0.1:8089`**.

**Prerequisites:** Phase **1.6** and **2.7** complete.

## 3.1 Where to run `ssh`

| Run `ssh` from | Forward binds to | Use when |
|----------------|------------------|----------|
| **Windows** (`ssh.exe`) | Windows **`127.0.0.1`** | **JetBrains on Windows** (this setup). Recommended. |
| **WSL** | WSL **`127.0.0.1`** | Use only when your client checks and plugin process are also resolved from WSL context. |

If the IDE is **Windows-native**, prefer **`ssh` from Windows** so **`127.0.0.1:8089`** works in the plugin.

## 3.2 SSH tunnel (one long-lived session)

```bash
ssh -N -L 8000:127.0.0.1:8000 -L 8089:127.0.0.1:8089 harshil@45.195.82.10
```

**Expected:** no shell prompt on remote (`-N`); session blocks. Leave it open while using the IDE.

## 3.3 Validation on Windows (same environment as IDE)

If you are in **PowerShell**, prefer `curl.exe` (not `curl`) to avoid alias issues.

```bash
curl.exe -sS http://127.0.0.1:8089/healthz
curl.exe -sS http://127.0.0.1:8089/version
curl.exe -sS http://127.0.0.1:8000/v1/models
```

**Expected:** same shapes as **§1.5** (healthz **`{"status":"ok"}`**, version includes **`ask_request_v1`**, models JSON from vLLM).

If you started **`ssh` inside WSL**, run these **`curl`s in WSL**, not in cmd.

## 3.4 JetBrains plugin

Build/install (if needed):

```bash
cd jetbrains-plugin
./gradlew buildPlugin
```

Install **`jetbrains-plugin/build/distributions/*.zip`** via **Help → Plugins → Install Plugin from Disk…**

**Help → Edit Custom VM Options…** (restart IDE after save):

| Goal | Line |
|------|------|
| Evidence-first Ask | `-Dmotadata.ask.evidence_first=true` |
| Context Layer URL (default) | `-Dmotadata.context_layer.url=http://127.0.0.1:8091` |
| If using WSL IP | `-Dmotadata.context_layer.url=http://172.30.127.150:8091` |

Do **not** set Plan-Gate URL — it is hardcoded to **`http://127.0.0.1:8089`**; the **tunnel** supplies it.

**Workspace:** open **Motadata AIOps** from **WSL** so **`project.basePath`** is a **Linux path** (e.g. **`/home/.../motadata-aiops`**). Windows-only paths **break** evidence export.

## 3.5 Phase 3 gate

| # | Check |
|---|--------|
| P3-1 | Tunnel up → Windows **`curl 127.0.0.1:8089/healthz`** OK |
| P3-2 | Tunnel up → Windows **`curl 127.0.0.1:8000/v1/models`** OK |
| P3-3 | Plugin VM options + Motadata project path valid (**§3.4**) |

---

## End-to-end order checklist

| Step | Owner | Action |
|------|-------|--------|
| 1 | GPU | **§1.4–1.6** — vLLM + Plan-Gate, all curls OK |
| 2 | WSL | **§2.3–2.7** — Context Layer + POST smoke OK |
| 3 | Windows | **§3.2–3.3** — SSH tunnel + curls OK |
| 4 | Windows | **§3.4** — plugin + evidence-first |

---

## Action 9 final proof-pack capture (Windows Host-A)

Use this once after phases 1–3 are green.

| Scenario | Required capture (all) |
|---|---|
| Ask v1 evidence-first | `request_id`, backend response JSON, plugin-visible output (dialog text or screenshot), Context Layer trace, Plan-Gate trace |
| Explain/Debug | `request_id`, backend response JSON, plugin-visible output, Context Layer trace, Plan-Gate trace, vLLM trace |
| Execute | `request_id`, backend response JSON, plugin-visible output, Plan-Gate trace (include one `EXECUTED` and one `BLOCKED/REFUSED`; `EXECUTED_FAILED` optional) |
| No-match honesty | `request_id`, backend response JSON, plugin-visible output, Context Layer trace, Plan-Gate trace |
| Failure-mode | `request_id`, backend response JSON, plugin-visible output, Plan-Gate trace |

Proof-pack rule: if any service trace cannot be correlated by `request_id`, mark it **NOT_PROVEN** (do not leave blank).

---

## Firewall note

Bind **vLLM** and **Plan-Gate** to **`127.0.0.1`** on the GPU; rely on **SSH** for remote access. Do not expose **8000** / **8089** on a public interface unless locked down.

---

## 8. Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| Plan-Gate exits immediately | vLLM not up or **`MOTADATA_EXPLAIN_VLLM_URL`** unreachable — fix **Phase 1** |
| **`RUNTIME_UNAVAILABLE`** in IDE | No **SSH tunnel** or tunnel from wrong OS context — **§3.1** |
| Evidence export fails | **`workspace_root`** not a Linux path visible to WSL — open project from WSL |
| `curl -sS ...` fails in PowerShell with `Invoke-WebRequest` parameter error | PowerShell `curl` alias; use `curl.exe -sS ...` or `Invoke-RestMethod` |
| Windows `curl.exe` to WSL IP:8091 returns `Connection refused` | Context Layer bound only to `127.0.0.1` in WSL; set `MOTADATA_CONTEXT_LAYER_HOST=0.0.0.0` and retry with current WSL IP |
| Windows cannot reach **8091** | Set Context Layer **`0.0.0.0`** + WSL IP in **`-Dmotadata.context_layer.url`** |

---

## 9. Optional: pytest (GPU repo)

```bash
cd ~/m-coder
export PYTHONPATH="$(pwd)"
python3 -m pytest runtime/tests/test_context_layer_service.py runtime/tests/test_ask_v1_ingest.py -q
```

**Expected:** all tests pass (or known skips only).

---

## 10. Optional: single Linux host

If GPU, WSL, and IDE are not split (everything on one Linux box with a Linux IDE), you may skip **SSH**; **`127.0.0.1`** is literal. Same HTTP gates apply.

---

## 11. Alternative: manual vLLM + Plan-Gate (no `governed_services.sh`)

Use when debugging split processes:

1. venv + `pip install vllm` (see `runtime/scripts/start_explain_vllm.sh` requirements).
2. `export PYTHONPATH=$HOME/m-coder` and **`VLLM_BASE_MODEL`**.
3. `source runtime/scripts/start_explain_vllm.sh` — wait until **`/v1/models`** responds.
4. Same shell or another: `export PLAN_GATE_PORT=8089`, `python3 -m runtime.plan_gate_service.app`.

Validation curls identical to **§1.5**.

---

*Update when ports, scripts, or env vars change.*

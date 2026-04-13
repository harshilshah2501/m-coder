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

## 2) One script: setup + checklist + verification (recommended)

From your **m-coder** clone on the **workspace host**, after the GPU stack can be reached (directly or via tunnel):

| Mode | What it does |
|------|----------------|
| **Default** | Runs **`wsl_plugin_mvp_stack.sh up`** (optional SSH tunnel + Context Layer + built-in checks), then prints config, a **live checklist** (CLI, tunnel, Context Layer, Plan-Gate, vLLM), then **`wsl_plugin_mvp_stack.sh check`**, optional Ask E2E. **Requires** `MOTADATA_ROOT` or `MOTADATA_REPO_ROOT`. |
| **`--verify-only`** (or **`PREFLIGHT_NO_SETUP=1`**) | **No** local `up` — only probes and validation. Use when services are already running. |
| **`--quick-only`** | Fast probes only; **no** `up`, **no** deep `check`. |

Log file (every run): `runtime/.run/motadata_preflight_<UTC>.log` (stdout is tee’d there).

**Typical full run** (tunnel to GPU + workspace path):

```bash
cd "$M_CODER_ROOT"
export MOTADATA_REPO_ROOT="/home/harshil/Projects/Motadata"
export CONTEXT_URL="http://127.0.0.1:8091"
export PLAN_GATE_URL="http://127.0.0.1:8089"
export ENABLE_SSH_TUNNEL=1
export TUNNEL_TARGET="${GPU_USER}@${GPU_HOST}"
# Optional: TUNNEL_SSH_KEY=~/.ssh/id_ed25519

./scripts/motadata_integration_preflight.sh
```

**Tunnel target must be a real `user@host`** (for example `harshil@45.195.82.10`). If `TUNNEL_TARGET` is `@`, or `GPU_USER` / `GPU_HOST` is empty, the SSH command is invalid, nothing listens on `127.0.0.1:8089`, and Plan-Gate checks fail. On the **GPU**, start **`governed_services`** first so Plan-Gate (and vLLM) exist behind the tunnel.

**Only verify** (no `up` on this host):

```bash
./scripts/motadata_integration_preflight.sh --verify-only
```

**Optional:** `ALLOW_COMMIT_MISMATCH=1`, `VERIFY_ASK_E2E=1`, `PREFLIGHT_CONTINUE_ON_QUICK_FAIL=1` — see comments in `scripts/motadata_integration_preflight.sh`.

**Lower-level stack commands** (same env): `./scripts/wsl_plugin_mvp_stack.sh {up|check|status|down|restart}`.

Exit code **0** and the **GREEN** banner mean you can proceed to **JetBrains UI** tests.

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

## 4) Build Context Layer wheel (GPU), install on workspace host

On the GPU host:

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

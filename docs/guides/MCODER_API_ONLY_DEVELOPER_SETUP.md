# MCODER API-ONLY DEVELOPER SETUP

## Purpose

This guide describes how developers should use m-coder as an API-only developer assistant without operating the full m-coder development repo.

Golden rule:

> Developers install the m-coder client/runtime. Their development repo is Motadata.

## Target Architecture

```text
Developer IDE / terminal
  -> HTTP client (curl / script / IDE task)
  -> WSL-local Context Layer :8091
  -> Motadata workspace
  -> shared GPU/Linux Plan-Gate :8089
  -> vLLM behind Plan-Gate only
```

Rules:

- IDEs never call vLLM.
- IDEs never send raw repository content to GPU.
- Context Layer stays beside the developer workspace.
- Plan-Gate remains the only model gateway.
- Local usage is API-only (HTTP contracts), with no direct vLLM access.

## Developer Mode (Wheel Only)

Use this mode for developers who work on Motadata and only need the packaged Context Layer.

Expected local state (project-first):

```text
/root/Harshil-PoCs/Motadata                 # developer repo (run mcoder here)
/root/Harshil-PoCs/Motadata/.mcoder/config.yaml   # preferred project-local config
/root/Harshil-PoCs/Motadata/.mcoder/logs/         # health/smoke journals
/root/Harshil-PoCs/Motadata/.mcoder/venv          # project-local runtime venv
```

Developers should not clone or operate the full m-coder repo in this mode.

## Canonical Configuration

Project-local `.mcoder/config.yaml` is preferred source of truth.

Example:

```yaml
workspace_root: /root/Harshil-PoCs/Motadata
context_url: http://127.0.0.1:8091
plan_gate_url: http://45.195.82.10:8089
mode: api_only
output: human
```

`context.env` can be generated from this YAML for service runtime use.

Config discovery order used by `mcoder`:

```text
1) MCODER_CONFIG_PATH
2) <project-root>/.mcoder/config.yaml
3) ~/.mcoder/config.yaml
```

Generated projection example:

```bash
MOTADATA_CONTEXT_LAYER_HOST=127.0.0.1
MOTADATA_CONTEXT_LAYER_PORT=8091
MOTADATA_ROOT=/root/Harshil-PoCs/Motadata
MOTADATA_CONTEXT_LAYER_DEFAULT_WORKSPACE=/root/Harshil-PoCs/Motadata
MOTADATA_CONTEXT_LAYER_LOG_PATH=/root/Harshil-PoCs/Motadata/.mcoder/context-layer.log
MOTADATA_CONTEXT_LAYER_INDEX_CACHE=1
```

## Install: Single Package (Recommended)

1. Create project-local runtime directory and venv:

```bash
cd /root/Harshil-PoCs/Motadata
mkdir -p ./.mcoder
python3 -m venv ./.mcoder/venv
source ./.mcoder/venv/bin/activate
```

2. Install one unified wheel (`mcoder-suite`) that contains both `mcoder` and `motadata-context-layer`:

```bash
pip install /path/to/mcoder_suite-0.1.0-py3-none-any.whl
```

### Venv hygiene (short path)

If pip shows this warning:

```text
Not uninstalling mcoder-suite at …/m-coder, outside environment …/Motadata/.mcoder/venv
```

your active Motadata venv can still see metadata from another interpreter or editable install. Use this minimal cleanup:

```bash
cd /root/Harshil-PoCs/Motadata
unset PYTHONPATH
source ./.mcoder/venv/bin/activate
python -m pip uninstall -y mcoder-suite || true

SITE_PKGS="$(python - <<'PY'
import sysconfig
print(sysconfig.get_paths().get("purelib", ""))
PY
)"
for f in "$SITE_PKGS"/*.pth "$SITE_PKGS"/*.egg-link; do
  [ -e "$f" ] || continue
  if rg -qi "m-coder|mcoder" "$f"; then rm -f "$f"; fi
done

python -m pip install --no-deps --force-reinstall /path/to/mcoder_suite-0.1.0-py3-none-any.whl
mcoder doctor   # or: mcoder bootstrap
```

Expected result: in **Wheel / venv hygiene**, `pip Location:` is under `Motadata/.mcoder/venv`.

### Update path (no m-coder repo on developer machine)

API-only developers do not need an `m-coder` clone. They only need:

- Motadata repo
- `Motadata/.mcoder/venv`
- released `mcoder-suite` wheel (artifact URL/share)

```bash
cd /root/Harshil-PoCs/Motadata
source ./.mcoder/venv/bin/activate
python -m pip install --no-deps --force-reinstall <WHEEL_PATH_OR_URL>
mcoder version
mcoder bootstrap
```

3. Bootstrap project config in one command:

```bash
mcoder init \
  --workspace-root /root/Harshil-PoCs/Motadata \
  --plan-gate-url http://45.195.82.10:8089
```

**Important:** `mcoder init` and `pip install mcoder-suite` **only** write config (`config.yaml`, `context.env`) and install CLI binaries. They **do not**:

- start the Context Layer HTTP process on `:8091`
- start Plan-Gate on the GPU host or create an SSH tunnel to `127.0.0.1:8089`

You must bring those endpoints up separately, then verify:

```bash
curl -fsS http://127.0.0.1:8091/healthz   # Context Layer (local)
curl -fsS http://127.0.0.1:8089/healthz   # Plan-Gate (local tunnel or same machine only)
```

**Minimal order after install:**

1. **One-time / first machine setup:** install the venv, `mcoder init`, and create the Context Layer user service (see [Context Layer User Service](#context-layer-user-service)) so `motadata-context-layer` is available and can be started with `systemctl --user enable --now mcoder-context`.
2. **Config for loopback Plan-Gate (so you are not typing `ssh -L` every session):** in `.mcoder/config.yaml` set `plan_gate_url: http://127.0.0.1:8089` and add `plan_gate_ssh_target: <user>@<gpu-host>` (or set `MCODER_PLAN_GATE_SSH`). You can bake this into **`mcoder init --plan-gate-ssh user@gpu-host`** so `config.yaml` includes those keys. If the GPU is directly reachable, use `plan_gate_url: http://<gpu-ip>:8089` instead and skip SSH.
3. **Each work session (or after reboot):** run the **checklist** — it probes both endpoints, restarts Context Layer if needed, and **creates the SSH tunnel** when loopback + `plan_gate_ssh_target` are set (no separate `ssh` step):
   ```bash
   mcoder bootstrap
   ```
   Read-only probes only: `mcoder bootstrap --check-only`. JSON for scripts: `mcoder bootstrap --json`.
4. Optional: `mcoder doctor` and `mcoder health --auto-fix` for the older health/journal path.
5. Verify binaries if you like: `mcoder version` and `motadata-context-layer --help`.

**Continue with optional customization:**

5. (Optional) manually edit canonical project config:

```bash
mkdir -p ./.mcoder
cat > ./.mcoder/config.yaml <<'YAML'
workspace_root: /root/Harshil-PoCs/Motadata
context_url: http://127.0.0.1:8091
plan_gate_url: http://45.195.82.10:8089
mode: api_only
output: human
YAML
```

6. (Optional) regenerate Context Layer env projection manually:

```bash
cat > ./.mcoder/context.env <<'ENV'
MOTADATA_CONTEXT_LAYER_HOST=127.0.0.1
MOTADATA_CONTEXT_LAYER_PORT=8091
MOTADATA_ROOT=/root/Harshil-PoCs/Motadata
MOTADATA_CONTEXT_LAYER_DEFAULT_WORKSPACE=/root/Harshil-PoCs/Motadata
MOTADATA_CONTEXT_LAYER_LOG_PATH=/root/Harshil-PoCs/Motadata/.mcoder/context-layer.log
MOTADATA_CONTEXT_LAYER_INDEX_CACHE=1
ENV
```

This generates:

```text
<project-root>/.mcoder/config.yaml
<project-root>/.mcoder/context.env
```

Verbose mode for debugging:

```bash
mcoder --verbose health --auto-fix
mcoder --verbose prompt "How does alert correlation work?"
```

Bounded network wait timeout (seconds):

```bash
mcoder --timeout-sec 10 health --auto-fix
mcoder --timeout-sec 20 prompt "Which class is the base class for all APIs?"
```

Explicit config file override (if needed):

```bash
mcoder --config /abs/path/to/config.yaml health
```

Reinitialize generated files:

```bash
mcoder init --force --plan-gate-url http://45.195.82.10:8089
```

## Context Layer User Service

Recommended WSL service model:

```text
systemd --user service
```

Generated unit target:

```text
~/.config/systemd/user/mcoder-context.service
```

Unit shape:

```ini
[Unit]
Description=m-coder Context Layer

[Service]
EnvironmentFile=/root/Harshil-PoCs/Motadata/.mcoder/context.env
ExecStart=/root/Harshil-PoCs/Motadata/.mcoder/venv/bin/motadata-context-layer
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
```

Detailed setup sequence (copy-paste):

```bash
# 1) Write service unit
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/mcoder-context.service <<'UNIT'
[Unit]
Description=m-coder Context Layer
After=network.target

[Service]
Type=simple
EnvironmentFile=/root/Harshil-PoCs/Motadata/.mcoder/context.env
ExecStart=/root/Harshil-PoCs/Motadata/.mcoder/venv/bin/motadata-context-layer
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
UNIT

# 2) Reload + enable + start
systemctl --user daemon-reload
systemctl --user enable --now mcoder-context

# 3) Verify service status
systemctl --user status mcoder-context --no-pager

# 4) Verify API
curl -fsS http://127.0.0.1:8091/healthz
curl -fsS http://127.0.0.1:8091/version
```

Logs:

```bash
journalctl --user -u mcoder-context -n 100 --no-pager
tail -f /root/Harshil-PoCs/Motadata/.mcoder/context-layer.log
```

## WSL: bring up Context Layer and Plan-Gate (SSH tunnel)

Everything below runs **inside your WSL distro** (not Windows `cmd`). Replace paths and hostnames with yours.

### 1) systemd on WSL2 (needed for `systemctl --user`)

Recent WSL2 supports **user** units. Ensure the distro boots with systemd: in `/etc/wsl.conf` add:

```ini
[boot]
systemd=true
```

Then from **Windows**: `wsl --shutdown`, reopen the distro, and retry `systemctl --user status`.

If `systemctl --user` still fails, run Context Layer in the foreground (`source .mcoder/venv/bin/activate`, load `.mcoder/context.env`, run `motadata-context-layer`), or keep it in `tmux`/`screen` with the same env as the unit file.

### 2) Context Layer on `127.0.0.1:8091` (local to WSL)

After `mcoder init` and a venv with `motadata-context-layer` on `PATH`:

1. Edit `~/.config/systemd/user/mcoder-context.service` so **`EnvironmentFile`** and **`ExecStart`** point at **your** project — e.g. `$HOME/Harshil-PoCs/Motadata/.mcoder/context.env` and `$HOME/.../.mcoder/venv/bin/motadata-context-layer` (see [Context Layer User Service](#context-layer-user-service)).
2. `systemctl --user daemon-reload && systemctl --user enable --now mcoder-context`
3. `curl -fsS http://127.0.0.1:8091/healthz`

### 3) Plan-Gate: either public URL or SSH tunnel to `127.0.0.1:8089`

**Option A — no tunnel:** if the GPU host’s Plan-Gate is reachable from WSL on the network, set:

```yaml
plan_gate_url: http://<GPU_PUBLIC_IP>:8089
```

(e.g. the same URL you pass to `mcoder init --plan-gate-url ...`.) Verify: `curl -fsS http://<GPU_PUBLIC_IP>:8089/healthz`.

**Option B — tunnel (Plan-Gate only bound on the GPU’s loopback):** from WSL, forward local `8089` to the remote service:

```bash
# Long form: forward WSL localhost:8089 -> GPU localhost:8089 (where Plan-Gate listens)
ssh -N -L 8089:127.0.0.1:8089 <user>@<GPU_HOST>
```

Leave that terminal open (or use `autossh` with the same `-L`). In **another** terminal:

```bash
curl -fsS http://127.0.0.1:8089/healthz
```

Point mcoder at the tunnel:

```bash
mcoder init --workspace-root "$HOME/Harshil-PoCs/Motadata" \
  --plan-gate-url http://127.0.0.1:8089 --force
```

### 4) Sanity check

```bash
mcoder health
```

Both checks need **TCP success**: Context Layer is always your WSL box; Plan-Gate is either the public GPU URL or `127.0.0.1:8089` **only while the SSH tunnel is connected**.

## Shared GPU/Linux Server

The GPU/Linux server runs shared governed services:

```text
Plan-Gate :8089
vLLM      :8000
```

Developers configure only:

```yaml
plan_gate_url: http://45.195.82.10:8089
```

Developers must not configure direct vLLM access.

Do we need to restart GPU `governed_services` when updating this local package?

- No, not for local CLI/context-layer-only package updates.
- Restart GPU services only when Plan-Gate/vLLM code or server-side config changed on GPU host.

Health checks on GPU host:

```bash
curl -fsS http://127.0.0.1:8089/healthz
curl -fsS http://127.0.0.1:8089/version
curl -fsS http://127.0.0.1:8000/v1/models
```

## Session bootstrap (`mcoder bootstrap`) — primary start path

Use **`mcoder bootstrap`** when you start a session: it runs a **fixed-order checklist** (package → Context Layer health + optional `systemctl` restart → Plan-Gate health + **automatic `ssh -L`** when `plan_gate_url` is loopback and `plan_gate_ssh_target` is set) and a final **dual /healthz** check. You do not need to run a separate `ssh` for Plan-Gate in that configuration.

## Stack diagnostic daemon (`mcoder stack`)

**Ongoing** or **background** use: `stack` is for **lightweight** check / log-only watch. For “turn key and go” at session start, use **`mcoder bootstrap`** first; use `stack` for non-intrusive monitoring.

**Non-intrusive by default:** `stack check` is read-only unless you pass **`--try-tunnel`**. **`stack watch`** only appends JSON to **`.mcoder/logs/stack-watch.log`** — it does **not** run `ssh`, restart `systemd`, or spam the terminal unless you explicitly add **`--auto-tunnel`**, **`--auto-context`**, or **`--verbose`**.

Add optional tunnel metadata to `.mcoder/config.yaml` (or use environment variables):

```yaml
plan_gate_ssh_target: harshil@45.195.82.10
plan_gate_ssh_remote_port: 8089
```

Same via env: `MCODER_PLAN_GATE_SSH`, `MCODER_PLAN_GATE_SSH_REMOTE_PORT`.

**One-shot check** (wheel + `/healthz` on both services):

```bash
mcoder stack check
mcoder stack check --try-tunnel
```

`--try-tunnel` attempts a single `ssh -L` forward when `plan_gate_url` is `http://127.0.0.1:8089` (or localhost) and Plan-Gate is down. Unattended tunneling uses **`BatchMode=yes`**; configure **SSH key auth** to the GPU host (`ssh harshil@45.195.82.10` should work non-interactively).

**Watch loop** (observe-only unless you opt in):

```bash
# Log-only: no ssh, no systemctl, one startup line (use --quiet to hide that too)
mcoder stack watch --interval 60
```

Optional **remediation** (only if you want the daemon to act):

```bash
mcoder stack watch --interval 60 --auto-tunnel --auto-context
```

- **`--auto-tunnel`**: if Plan-Gate on loopback is unhealthy, run `ssh -L` (writes `.mcoder/stack/tunnel.log` and `tunnel.pid`).
- **`--auto-context`**: if Context Layer is unhealthy, run `systemctl --user restart mcoder-context`.
- **`--verbose`**: mirror each JSON log line to stdout (otherwise console stays quiet).
- **`--quiet`**: no startup banner (still only writes the log file by default).

Run under **systemd --user** or **`tmux`** on WSL. Example — **observe-only** service:

```ini
[Unit]
Description=m-coder stack watch (observe-only)
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/root/Harshil-PoCs/Motadata
ExecStart=/root/Harshil-PoCs/Motadata/.mcoder/venv/bin/mcoder stack watch --interval 120 --quiet
Restart=on-failure

[Install]
WantedBy=default.target
```

Add **`--auto-tunnel --auto-context`** to `ExecStart` only when you intentionally want remediation.

This does **not** replace installing the wheel or starting long-lived GPU services; it **records** status and can **optionally repair** the local path when those flags are set.

## Validation Sequence (Run in Order)

### 1) Doctor (readiness diagnosis)

```bash
mcoder doctor
```

Checks config/workspace/service reachability plus Neo4j driver warning.

### 2) Health with auto-fix

```bash
mcoder --timeout-sec 10 health --auto-fix
```

Auto-fix behavior:

- restarts context service when needed
- if configured Plan-Gate URL fails but local `127.0.0.1:8089` is healthy, updates config fallback automatically
- writes journal: `<project-root>/.mcoder/logs/mcoder-health-<timestamp>.log`

### 3) Smoke prompt

Each `prompt` waits on **two** HTTP calls (`export_evidence` on Context Layer, then `/v1/ask` on Plan-Gate); **both** use `--timeout-sec`. Default `15s` often fails on large workspaces or slow GPU—use **`120`** or **`300`** when you see timeouts.

```bash
mcoder --timeout-sec 120 prompt "How does alert correlation work?"
```

Expected posture:

```text
posture: PLAN_ONLY
executed: False
```

### 4) Optional debug/plan checks

```bash
mcoder --timeout-sec 20 debug --file src/main/java/com/motadata/alerts/AlertCorrelator.java --query "Why can this correlator miss duplicate suppression?"
mcoder --timeout-sec 20 plan "Plan a safe refactor for alert enrichment flow"
```

## One-Step Scenario Execution

`mcoder prompt` implicitly does both prerequisites in one command:

1. `POST /v1/export_evidence`
2. `POST /v1/ask`

Example:

```bash
mcoder prompt "How does alert correlation work?"
```

Single-step debug (implicit evidence export + ask with `task_type=EXPLAIN_DEBUG`):

```bash
mcoder debug \
  --file src/main/java/com/motadata/alerts/AlertCorrelator.java \
  --query "Why can this correlator miss duplicate suppression?"
```

Single-step plan (implicit evidence export + ask with `plan_contract.v1` response extension):

```bash
mcoder plan "Plan a safe refactor for alert enrichment flow with rollback notes"
```

Batch ask scenarios (one query per line, `#` comments allowed):

```bash
cat > /tmp/mcoder_scenarios.txt <<'EOF'
How does alert correlation work?
Where is alert deduplication implemented?
What is the entry point for incident enrichment?
EOF

mcoder scenario --type ask --file /tmp/mcoder_scenarios.txt
```

Batch debug scenarios use this format per line:

```text
selected_file|query
```

Example:

```bash
cat > /tmp/mcoder_debug_scenarios.txt <<'EOF'
src/main/java/com/motadata/alerts/AlertCorrelator.java|Trace duplicate suppression logic and failure path.
src/main/java/com/motadata/enrichment/IncidentEnricher.java|Explain null handling and retry branch behavior.
EOF

mcoder scenario --type debug --file /tmp/mcoder_debug_scenarios.txt
```

Batch plan scenarios (one planning prompt per line):

```bash
cat > /tmp/mcoder_plan_scenarios.txt <<'EOF'
Plan a bounded refactor of alert deduplication service.
Plan safe migration of enrichment config parsing with tests.
EOF

mcoder scenario --type plan --file /tmp/mcoder_plan_scenarios.txt
```

## IDE Usage

### VSCode / Cursor

Use terminal tasks that call `mcoder` helper commands.

Example:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "m-coder Ask Prompt",
      "type": "shell",
      "command": "wsl mcoder prompt \"${input:query}\""
    },
    {
      "label": "m-coder Debug Current File",
      "type": "shell",
      "command": "wsl mcoder debug --file \"${file}\" --query \"Explain control flow and likely failure points\""
    }
  ],
  "inputs": [
    {
      "id": "query",
      "type": "promptString",
      "description": "Ask m-coder"
    }
  ]
}
```

Cursor can call `mcoder` from its integrated terminal.

### IntelliJ

Use External Tools.

Program:

```bash
wsl
```

Arguments (ask):

```bash
mcoder prompt "$Prompt$"
```

Debug current file:

```bash
mcoder debug --file "$FilePath$" --query "Explain likely bug path"
```

## Safety Rules

- No direct vLLM calls from developer machines.
- No raw repository upload to GPU.
- No execution/apply/retry loops in the developer path.
- Context Layer reads local workspace; Plan-Gate receives evidence bundle, not raw repo.
- preferred user-edited config is `<project-root>/.mcoder/config.yaml`.

## Troubleshooting

### Context Layer is down

```bash
systemctl --user status mcoder-context
systemctl --user restart mcoder-context
curl -fsS http://127.0.0.1:8091/healthz
```

Check logs:

```bash
less /root/Harshil-PoCs/Motadata/.mcoder/context-layer.log
```

### Workspace root not found

Edit project config:

```text
<project-root>/.mcoder/config.yaml
```

Confirm:

```bash
ls /root/Harshil-PoCs/Motadata
```

Then regenerate service projection:

```bash
sed -i 's|^workspace_root:.*|workspace_root: /root/Harshil-PoCs/Motadata|' ./.mcoder/config.yaml
sed -i 's|^MOTADATA_ROOT=.*|MOTADATA_ROOT=/root/Harshil-PoCs/Motadata|' ./.mcoder/context.env
sed -i 's|^MOTADATA_CONTEXT_LAYER_DEFAULT_WORKSPACE=.*|MOTADATA_CONTEXT_LAYER_DEFAULT_WORKSPACE=/root/Harshil-PoCs/Motadata|' ./.mcoder/context.env
systemctl --user restart mcoder-context
```

### Plan-Gate unreachable

Check:

```bash
curl -fsS http://45.195.82.10:8089/healthz
```

If unreachable, the problem is shared GPU/Linux service or network routing, not the local Context Layer.

### Evidence export fails

Run:

```bash
curl -fsS -X POST http://127.0.0.1:8091/v1/export_evidence \
  -H 'Content-Type: application/json' \
  -d '{"workspace_root":"/root/Harshil-PoCs/Motadata","query":"health smoke","top_k":4}'
```

If only evidence export fails:

- confirm workspace path
- confirm repo is readable in WSL
- restart Context Layer
- check `/root/Harshil-PoCs/Motadata/.mcoder/context-layer.log`

## Rollout Order

1. Build and publish `mcoder-suite` wheel.
2. Install in project-local venv on WSL/Linux developer host.
3. Run `mcoder init`, `mcoder doctor`, and `mcoder health --auto-fix`.
4. Validate ask/debug/plan scenario flows.

---

# readiness
mcoder doctor
mcoder --timeout-sec 10 health --auto-fix

# ask
mcoder --timeout-sec 20 prompt "Which class is the base class for all APIs?"
mcoder --timeout-sec 20 prompt "How does mail server configuration work?"
mcoder --timeout-sec 20 prompt "How are config stores organized?"
mcoder --timeout-sec 20 prompt "Explain the API layer architecture."
mcoder --timeout-sec 20 prompt "Find all classes that handle notifications."

# debug
mcoder --timeout-sec 20 debug --file motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java --query "Debug why availability correlation might skip enrichment branches."
mcoder --timeout-sec 20 debug --file motadata/src/main/java/com/mindarray/api/MailServerConfiguration.java --query "Debug why mail server updates are not reflected after API update."
mcoder --timeout-sec 20 debug --file motadata/src/main/java/com/mindarray/store/AbstractConfigStore.java --query "Debug null-return paths in AbstractConfigStore.getItem and related callers."
mcoder --timeout-sec 20 debug --file motadata/src/main/java/com/mindarray/nms/SNMPTrapProcessor.java --query "Debug where SNMP trap parsing can fail before alert generation."

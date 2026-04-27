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

3. Bootstrap project config in one command:

```bash
mcoder init \
  --workspace-root /root/Harshil-PoCs/Motadata \
  --plan-gate-url http://45.195.82.10:8089
```

4. Verify CLI and service commands are installed:

```bash
mcoder version
motadata-context-layer --help
```

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

```bash
mcoder --timeout-sec 20 prompt "How does alert correlation work?"
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

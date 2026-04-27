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

Expected local state:

```text
~/Projects/Motadata                 # developer's actual repo
~/.mcoder/config.yaml               # canonical user config
~/.mcoder/context.env               # generated service env projection
~/.mcoder/venv                      # m-coder client/runtime venv
```

Developers should not clone or operate the full m-coder repo in this mode.

## Canonical Configuration

`~/.mcoder/config.yaml` is the source of truth.

Example:

```yaml
workspace_root: /home/user/Projects/Motadata
context_url: http://127.0.0.1:8091
plan_gate_url: http://gpu-host:8089
mode: api_only
output: human
```

`~/.mcoder/context.env` is generated from this YAML for service runtime use.

Users should edit only:

```text
~/.mcoder/config.yaml
```

Generated projection example:

```bash
MOTADATA_CONTEXT_LAYER_HOST=127.0.0.1
MOTADATA_CONTEXT_LAYER_PORT=8091
MOTADATA_ROOT=/home/user/Projects/Motadata
MOTADATA_CONTEXT_LAYER_DEFAULT_WORKSPACE=/home/user/Projects/Motadata
MOTADATA_CONTEXT_LAYER_LOG_PATH=/home/user/.mcoder/context-layer.log
MOTADATA_CONTEXT_LAYER_INDEX_CACHE=1
```

## Install: Wheel Mode

1. Create the runtime directory:

```bash
mkdir -p ~/.mcoder
python3 -m venv ~/.mcoder/venv
source ~/.mcoder/venv/bin/activate
```

2. Install the Context Layer wheel:

```bash
pip install /path/to/motadata_context_layer-0.1.6-py3-none-any.whl
```

3. Write canonical config:

```bash
cat > ~/.mcoder/config.yaml <<'YAML'
workspace_root: /home/user/Projects/Motadata
context_url: http://127.0.0.1:8091
plan_gate_url: http://gpu-host:8089
mode: api_only
output: human
YAML
```

4. Generate Context Layer env projection:

```bash
cat > ~/.mcoder/context.env <<'ENV'
MOTADATA_CONTEXT_LAYER_HOST=127.0.0.1
MOTADATA_CONTEXT_LAYER_PORT=8091
MOTADATA_ROOT=/home/user/Projects/Motadata
MOTADATA_CONTEXT_LAYER_DEFAULT_WORKSPACE=/home/user/Projects/Motadata
MOTADATA_CONTEXT_LAYER_LOG_PATH=/home/user/.mcoder/context-layer.log
MOTADATA_CONTEXT_LAYER_INDEX_CACHE=1
ENV
```

5. Install the local helper CLI wrapper (single-step prompt/scenario):

```bash
mkdir -p ~/.local/bin
ln -sf /root/Harshil-PoCs/m-coder/scripts/mcoder ~/.local/bin/mcoder
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
mcoder version
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
EnvironmentFile=%h/.mcoder/context.env
ExecStart=%h/.mcoder/venv/bin/motadata-context-layer
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
```

Equivalent systemd commands:

```bash
systemctl --user daemon-reload
systemctl --user enable --now mcoder-context
systemctl --user status mcoder-context
```

## Shared GPU/Linux Server

The GPU/Linux server runs shared governed services:

```text
Plan-Gate :8089
vLLM      :8000
```

Developers configure only:

```yaml
plan_gate_url: http://gpu-host:8089
```

Developers must not configure direct vLLM access.

Health checks on GPU host:

```bash
curl -fsS http://127.0.0.1:8089/healthz
curl -fsS http://127.0.0.1:8089/version
curl -fsS http://127.0.0.1:8000/v1/models
```

## Verification Tiers

### Local Readiness Check

Purpose: fast local readiness.

Checks:

- config exists and parses
- `mode=api_only`
- workspace root exists
- Context Layer reachable
- Plan-Gate reachable

Expected output:

```text
Config: OK
Workspace root: OK
Context Layer: OK
Plan-Gate: OK
API-only mode: OK
```

### Governed Smoke Check

Purpose: governed smoke test.

Checks:

- all `doctor` checks
- evidence export works
- Plan-Gate `/v1/ask` works
- response is non-executing
- governance posture is surfaced

Expected output:

```text
Context Layer: OK
Plan-Gate: OK
Evidence export: OK
Ask v1: PASS
Execution: false
Mutation: false
```

### Acceptance-Grade Validation

Purpose: acceptance-grade validation.

Additional checks:

- graph preflight
- Assist v2 API gate
- Plan/Code HTTP gate
- scenario regression slice when configured

Expected output:

```text
Graph preflight: COMPLETE
Assist v2 API gate: PASS
Plan/Code gate: PASS
Scenario slice: PASS
```

Use `--full` for release validation or admin confidence checks, not for every developer's first ask.

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
- `~/.mcoder/config.yaml` is the only user-edited config.

## Troubleshooting

### Context Layer is down

```bash
systemctl --user status mcoder-context
systemctl --user restart mcoder-context
curl -fsS http://127.0.0.1:8091/healthz
```

Check logs:

```bash
less ~/.mcoder/context-layer.log
```

### Workspace root not found

Edit:

```text
~/.mcoder/config.yaml
```

Confirm:

```bash
ls /home/user/Projects/Motadata
```

Then regenerate service projection:

```bash
sed -i 's|^workspace_root:.*|workspace_root: /home/user/Projects/Motadata|' ~/.mcoder/config.yaml
sed -i 's|^MOTADATA_ROOT=.*|MOTADATA_ROOT=/home/user/Projects/Motadata|' ~/.mcoder/context.env
sed -i 's|^MOTADATA_CONTEXT_LAYER_DEFAULT_WORKSPACE=.*|MOTADATA_CONTEXT_LAYER_DEFAULT_WORKSPACE=/home/user/Projects/Motadata|' ~/.mcoder/context.env
systemctl --user restart mcoder-context
```

### Plan-Gate unreachable

Check:

```bash
curl -fsS http://gpu-host:8089/healthz
```

If unreachable, the problem is shared GPU/Linux service or network routing, not the local Context Layer.

### Evidence export fails

Run:

```bash
curl -fsS -X POST http://127.0.0.1:8091/v1/export_evidence \
  -H 'Content-Type: application/json' \
  -d '{"workspace_root":"/home/user/Projects/Motadata","query":"health smoke","top_k":4}'
```

If only evidence export fails:

- confirm workspace path
- confirm repo is readable in WSL
- restart Context Layer
- check `~/.mcoder/context-layer.log`

## Rollout Order

1. Freeze this setup guide.
2. Package Context Layer wheel for normal developers.
3. Validate wheel-only setup with 2-3 internal developers.
4. Keep CLI contract work separate from this wheel-only path.

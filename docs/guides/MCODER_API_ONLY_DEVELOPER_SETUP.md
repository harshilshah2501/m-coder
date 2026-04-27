# MCODER API-ONLY DEVELOPER SETUP

## Purpose

This guide describes how developers should use m-coder as an API-only developer assistant without operating the full m-coder development repo.

Golden rule:

> Developers install the m-coder client/runtime. Their development repo is Motadata.

## Target Architecture

```text
Developer IDE / terminal
  -> mcoder CLI
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
- CLI remains governed and API-only.

## Supported Developer Modes

### Mode A: Wheel Install (Normal Developers)

Use this mode for developers who work on Motadata and only need m-coder as an assistant.

Expected local state:

```text
~/Projects/Motadata                 # developer's actual repo
~/.mcoder/config.yaml               # canonical user config
~/.mcoder/context.env               # generated service env projection
~/.mcoder/venv                      # m-coder client/runtime venv
```

Developers should not clone or operate the full m-coder repo in this mode.

### Mode B: Repo-Local (m-coder Contributors)

Use this mode only for contributors changing m-coder itself.

Expected local state:

```text
~/Projects/Motadata                 # target workspace
~/Harshil-PoCs/m-coder              # m-coder development checkout
```

Repo-local mode may use existing scripts such as:

```bash
runtime/scripts/run_local_stack.sh start-context
runtime/scripts/run_local_stack.sh health
```

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
pip install /path/to/motadata_context_layer-0.1.5-py3-none-any.whl
```

3. Configure m-coder:

```bash
mcoder configure \
  --workspace-root /home/user/Projects/Motadata \
  --plan-gate-url http://gpu-host:8089
```

`mcoder configure` should write:

- `~/.mcoder/config.yaml`
- generated `~/.mcoder/context.env`

## Install: Repo-Local Mode

Use this only for m-coder contributors.

```bash
export M_CODER_ROOT="$HOME/Harshil-PoCs/m-coder"
cd "$M_CODER_ROOT"
export PYTHONPATH="$M_CODER_ROOT"

cp runtime/config/host_local.env.example runtime/config/host_local.env
# Edit runtime/config/host_local.env for local paths/ports.
```

Start Context Layer:

```bash
runtime/scripts/run_local_stack.sh start-context
runtime/scripts/run_local_stack.sh health
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

Expected commands:

```bash
mcoder install-context --service
mcoder start-context
mcoder status
mcoder stop-context
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

### `mcoder doctor`

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

### `mcoder verify`

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

### `mcoder verify --full`

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

## IDE Usage

### VSCode / Cursor

Use terminal tasks that call `mcoder`.

Example:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "m-coder Ask",
      "type": "shell",
      "command": "wsl mcoder ask \"${input:query}\""
    },
    {
      "label": "m-coder Debug Current File",
      "type": "shell",
      "command": "wsl mcoder debug --file \"${file}\""
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

Cursor can also call `mcoder` from its integrated terminal or project instructions.

### IntelliJ

Use External Tools.

Program:

```bash
wsl
```

Arguments:

```bash
mcoder ask "$Prompt$"
```

Current file debug:

```bash
mcoder debug --file "$FilePath$"
```

## Safety Rules

- No direct vLLM calls from developer machines.
- No raw repository upload to GPU.
- No `execute`, `apply`, `run`, `retry`, `fix`, `auto`, or `agent` commands in V1.
- `mcoder propose` returns `patch_proposal.v1` metadata only.
- Context Layer reads local workspace; Plan-Gate receives evidence bundle, not raw repo.
- `~/.mcoder/config.yaml` is the only user-edited config.

## Troubleshooting

### Context Layer is down

```bash
mcoder status
mcoder start-context
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
mcoder configure --workspace-root /home/user/Projects/Motadata
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
mcoder verify
```

If only evidence export fails:

- confirm workspace path
- confirm repo is readable in WSL
- restart Context Layer
- check `~/.mcoder/context-layer.log`

## Rollout Order

1. Freeze this setup guide.
2. Implement repo-local `scripts/mcoder`.
3. Package Context Layer wheel for normal developers.
4. Add `mcoder install-context --service`.
5. Add IDE examples.
6. Dry run with 2-3 internal developers.
7. Promote installable CLI after command semantics stabilize.

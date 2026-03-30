# motadata-context-layer (installable wheel)

Installable **Context Layer** for WSL: `runtime.layer5` + HTTP service (`runtime.context_layer_service`). No Plan-Gate, no vLLM, no full monorepo layout required on the host.

## Install (WSL)

From repo root (development):

```bash
cd packaging/motadata-context-layer
python3 -m venv .venv && . .venv/bin/activate
pip install .
```

Build wheel (from repo, requires `pip install build` in a venv). Bump `version` in `pyproject.toml` first, then:

```bash
cd packaging/motadata-context-layer
python3 -m build --wheel -o dist
```

Wheels land in `packaging/motadata-context-layer/dist/` (gitignored — not stored in the repo; install or copy the `.whl` to your WSL host).

## Deterministic package pipeline (build + health + sanity)

Use the integrated pipeline script to ensure each update is packageable and runtime-compatible on WSL:

```bash
bash packaging/motadata-context-layer/build_and_verify_wsl_context_layer.sh
```

What it validates:

1. Wheel build in isolated build venv
2. Wheel install in isolated smoke venv
3. `GET /healthz` + `GET /version` contract checks
4. `POST /v1/export_evidence` sanity check on your `WORKSPACE_ROOT`
5. Optional Plan-Gate compatibility (`/version` includes `ask_request_v1=v1.0`)
6. Optional wheel copy to deployment target via `scp` or `rsync`

Optional variables:

```bash
WORKSPACE_ROOT=/root/Harshil-PoCs/Motadata \
SANITY_QUERY='How does alert correlation work in this repo?' \
TOP_K=8 \
PLAN_GATE_URL=http://127.0.0.1:8089 \
bash packaging/motadata-context-layer/build_and_verify_wsl_context_layer.sh
```

WSL deployment copy (your target):

```bash
WORKSPACE_ROOT=/root/Harshil-PoCs/Motadata \
DEPLOY_TARGET=root@172.30.127.150 \
DEPLOY_PATH=/root/Harshil-PoCs/Motadata \
DEPLOY_METHOD=scp \
bash packaging/motadata-context-layer/build_and_verify_wsl_context_layer.sh
```

Using `rsync` instead:

```bash
WORKSPACE_ROOT=/root/Harshil-PoCs/Motadata \
DEPLOY_TARGET=root@172.30.127.150 \
DEPLOY_PATH=/root/Harshil-PoCs/Motadata \
DEPLOY_METHOD=rsync \
bash packaging/motadata-context-layer/build_and_verify_wsl_context_layer.sh
```

Install:

```bash
pip install dist/motadata_context_layer-0.1.4-py3-none-any.whl
```

## Run

```bash
motadata-context-layer
# or
python -m runtime.context_layer_service
```

Logs go to **stderr** of that process unless `MOTADATA_CONTEXT_LAYER_LOG_PATH` is set. Every `POST /v1/export_evidence` emits **`CONTEXT_LAYER export_evidence begin`** at INFO so you can confirm Ask traffic hits this instance (if you see no such line, another process owns port 8091 or the client is not reaching this server).

## Configuration (environment)

| Variable | Purpose | Default |
|----------|---------|---------|
| `MOTADATA_CONTEXT_LAYER_HOST` / `CONTEXT_LAYER_HOST` | Bind address | `127.0.0.1` |
| `MOTADATA_CONTEXT_LAYER_PORT` / `CONTEXT_LAYER_PORT` | Port | `8091` |
| `MOTADATA_CONTEXT_LAYER_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |
| `MOTADATA_CONTEXT_LAYER_LOG_PATH` | If set, log file path (append) | stderr only |
| `MOTADATA_CONTEXT_LAYER_DISABLE_HTTP` | Set to `1` to skip HTTP in **clients** (plugin); not used by server | — |
| `MOTADATA_ROOT` | If the IDE sends a JetBrains Roaming `.../projects/<hash>` path, **substitute** this directory for indexing (same as smoke tests). | — |
| `MOTADATA_CONTEXT_LAYER_DEFAULT_WORKSPACE` | Same as `MOTADATA_ROOT` if you prefer a dedicated name (checked first). | — |
| `MOTADATA_CONTEXT_LAYER_WORKSPACE_FILE` | Path to a text file whose **first line** is the repo root (optional). | — |
| `~/.motadata_context_layer_workspace` | If unset, first line of this file is used as repo root (same as `WORKSPACE_FILE`). | — |
| (heuristic) | If still unset: **`~/Projects/Motadata`** or **`~/Motadata`**. If the service runs as **root**, also scan **`/home/*/Projects/Motadata`** and use it when **exactly one** exists. | — |

## Endpoints

- `GET /healthz` — process up.
- `GET /version` — package version + schema hints.
- `POST /v1/export_evidence` — JSON `{ "workspace_root", "query", "top_k" }` → `layer5.evidence_bundle.v1` or explicit error JSON with `failure_class`.

## Error contract (plugin)

- **Unreachable** (connection refused, timeout): treat as Context Layer **absent** → allowed controlled fallback to `/v0/ask` if policy allows.
- **HTTP response** with `failure_class` (4xx/5xx): service **present but failed** → **do not** silently degrade; surface error.

See `docs/runtime/WSL_CONTEXT_LAYER_CLIENT.md` and `context-layer.env.example`.

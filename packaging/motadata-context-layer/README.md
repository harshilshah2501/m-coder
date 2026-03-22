# motadata-context-layer (installable wheel)

Installable **Context Layer** for WSL: `runtime.layer5` + HTTP service (`runtime.context_layer_service`). No Plan-Gate, no vLLM, no full monorepo layout required on the host.

## Install (WSL)

From repo root (development):

```bash
cd packaging/motadata-context-layer
python3 -m venv .venv && . .venv/bin/activate
pip install .
```

Build wheel (from repo, requires `pip install build`):

```bash
cd packaging/motadata-context-layer
python3 -m build --wheel -o dist
```

Install:

```bash
pip install dist/motadata_context_layer-0.1.0-py3-none-any.whl
```

## Run

```bash
motadata-context-layer
# or
python -m runtime.context_layer_service
```

## Configuration (environment)

| Variable | Purpose | Default |
|----------|---------|---------|
| `MOTADATA_CONTEXT_LAYER_HOST` / `CONTEXT_LAYER_HOST` | Bind address | `127.0.0.1` |
| `MOTADATA_CONTEXT_LAYER_PORT` / `CONTEXT_LAYER_PORT` | Port | `8091` |
| `MOTADATA_CONTEXT_LAYER_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |
| `MOTADATA_CONTEXT_LAYER_LOG_PATH` | If set, log file path (append) | stderr only |
| `MOTADATA_CONTEXT_LAYER_DISABLE_HTTP` | Set to `1` to skip HTTP in **clients** (plugin); not used by server | — |

## Endpoints

- `GET /healthz` — process up.
- `GET /version` — package version + schema hints.
- `POST /v1/export_evidence` — JSON `{ "workspace_root", "query", "top_k" }` → `layer5.evidence_bundle.v1` or explicit error JSON with `failure_class`.

## Error contract (plugin)

- **Unreachable** (connection refused, timeout): treat as Context Layer **absent** → allowed controlled fallback to `/v0/ask` if policy allows.
- **HTTP response** with `failure_class` (4xx/5xx): service **present but failed** → **do not** silently degrade; surface error.

See `docs/runtime/WSL_CONTEXT_LAYER_CLIENT.md` and `context-layer.env.example`.

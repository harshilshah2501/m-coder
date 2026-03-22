# WSL Context Layer — client assumption (JetBrains / Plan-Gate)

Evidence-first Ask uses **`layer5.evidence_bundle.v1`** before **`POST /v1/ask`** on Plan-Gate. The plugin does **not** assume a checkout of the `m-coder` source tree on WSL.

## Install (WSL, no monorepo)

```bash
pip install motadata_context_layer-*.whl
motadata-context-layer
# or: python -m runtime.context_layer_service
```

Build the wheel from `packaging/motadata-context-layer/` (see `README.md` there).

## Primary: HTTP service (WSL)

- **`GET /healthz`** — process up; JSON includes `package_version` (from distribution metadata, or `unknown` if not installed as a wheel).
- **`GET /version`** — `package`, `package_version`, `evidence_schema_hint`, `endpoints`.
- **`POST /v1/export_evidence`** — body: `{ "workspace_root": "<path>", "query": "<text>", "top_k": 8 }`  
  - **200:** raw **`layer5.evidence_bundle.v1`** object (schema-validated before send).  
  - **400:** `failure_class` = `invalid_json` | `invalid_request`.  
  - **422:** `error` = `export_failed`, `failure_class` = `workspace_export_failed` (service is up; workspace/index/export could not complete).  
  - **500:** `failure_class` = `internal_error` | `evidence_contract_violation`.

### Environment (server)

| Variable | Purpose | Default |
|----------|---------|---------|
| `MOTADATA_CONTEXT_LAYER_HOST` / `CONTEXT_LAYER_HOST` | Bind address | `127.0.0.1` |
| `MOTADATA_CONTEXT_LAYER_PORT` / `CONTEXT_LAYER_PORT` | Port | `8091` |
| `MOTADATA_CONTEXT_LAYER_LOG_LEVEL` | Logging level | `INFO` |
| `MOTADATA_CONTEXT_LAYER_LOG_PATH` | Optional log file | (stderr only) |

### Plugin configuration

- **URL:** `MOTADATA_CONTEXT_LAYER_URL` or `-Dmotadata.context_layer.url=`  
  Default: **`http://127.0.0.1:8091`**
- **Skip HTTP (CLI / dev script only):** `MOTADATA_CONTEXT_LAYER_DISABLE_HTTP=1`

### Fallback policy (plugin)

- **Unreachable** (connection refused, timeout, unknown host, or no provider): **allowed** controlled **`/v0/ask`** fallback when evidence-first is on.
- **HTTP/CLI returned an error** (e.g. 422/500, or non-JSON / wrong `schema_hint` on 200): **not** silently treated as “no Context Layer” — the plugin surfaces **`UNKNOWN`** with the response body (no silent evidence-first success).

## Fallback: installed CLI

- **`MOTADATA_CONTEXT_LAYER_CLI`** or `-Dmotadata.context_layer.cli=`  
  Contract: `cli <workspace_root>` with **query on stdin**, **bundle JSON on stdout**.

## Development only: repo script

Repo-relative `runtime/scripts/layer5_export_evidence.py` is **disabled by default**. Enable with:

- `MOTADATA_CONTEXT_LAYER_DEV_REPO_SCRIPT_FALLBACK=1` or  
  `-Dmotadata.context_layer.dev_repo_script_fallback=true`

## Plan-Gate

Unchanged: evidence-first sends **`ask_request.v1.0`** to **`POST /v1/ask`** when export succeeds; Plan-Gate contract errors are handled per existing bridge rules.

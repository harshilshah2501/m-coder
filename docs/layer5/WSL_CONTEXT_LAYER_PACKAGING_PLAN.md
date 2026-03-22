# WSL Context Layer Packaging Plan

## 1. Executive Summary

**Final artifact model (three surfaces):**

| Surface | Artifact | Role |
|--------|----------|------|
| **Windows** | JetBrains plugin **zip** (or marketplace distribution) | IDE client; configures endpoints; evidence-first Ask calls WSL Context Layer then GPU Plan-Gate. |
| **WSL** | **Context Layer package** (wheel + optional systemd unit template + config template) — *not* a full `m-coder` checkout | Installed service or CLI: builds `layer5.evidence_bundle.v1` from a **workspace path** the plugin supplies. |
| **GPU** | **Full `m-coder` repo** (existing model) | Plan-Gate (`/v0/*`, `/v1/ask`), vLLM, governed reasoning; no requirement for repo on WSL/client. |

**Contract spine (frozen, version-aligned):** `layer5.evidence_bundle.v1`, `ask_request.v1.0`, `POST /v1/ask`, `plan_only_response.v0.1`.

---

## 2. Deployment Targets

### Windows

- **Installed:** JetBrains plugin (Motadata AI Coding Assistant) from plugin zip / marketplace.
- **Talks to:**
  - **WSL Context Layer HTTP** (default assumption: `http://127.0.0.1:<port>` or WSL-reachable host/port — configurable).
  - **GPU Plan-Gate** HTTP (`/v0/ask`, `/v1/ask`, `/healthz`, `/version`) — configurable base URL (e.g. VPN/Tailscale IP or corporate proxy).
- **Does not require:** any `m-coder` tree on Windows beyond the plugin itself.

### WSL

- **Installed:** Context Layer **Python package** + **one runnable entrypoint** (HTTP server module or thin wrapper script installed to `PATH`).
- **Runs:** Long-lived **HTTP listener** (preferred) on a fixed port (e.g. 8091), or on-demand **CLI** invocations if fallback is chosen.
- **Local resources needed:**
  - Python 3.x + declared dependencies (stdlib + existing L5 deps only — no new stacks in this plan).
  - **Disk:** workspace roots that the **IDE** opens (plugin sends `workspace_root` per request); indexer reads those paths — **no** packaged copy of the user’s repo inside the Context Layer install tree.
  - Optional: writable **log directory** (configurable).

### GPU

- **Remains:** Full `m-coder` checkout; existing Plan-Gate service, vLLM, env (e.g. `MOTADATA_EXPLAIN_VLLM_URL`).
- **Contracts exposed:**
  - `GET /healthz`, `GET /version`
  - `POST /v1/ask` (evidence-first Ask ingestion)
  - `POST /v0/ask` (legacy)
  - Other existing endpoints unchanged.

---

## 3. Artifact Inventory

| Name (planned) | Purpose | Installed on | Built from (repo area) |
|----------------|---------|--------------|-------------------------|
| **motadata-jetbrains-plugin-&lt;version&gt;.zip** (Gradle `buildPlugin`) | IDE distribution | **Windows** (IntelliJ install) | `jetbrains-plugin/` |
| **motadata-context-layer-&lt;version&gt;-py3-none-any.whl** (or equivalent) | Shippable L5 surface: resolver, index, retrieval, evidence, HTTP service | **WSL** (`pip install` or venv) | Built via **`packaging/motadata-context-layer/pyproject.toml`** (packages `runtime.layer5*` + `runtime.context_layer_service*` from monorepo paths; no full checkout needed on WSL after `pip install`) |
| **motadata-context-layer-config.example.env** | Template: `CONTEXT_LAYER_PORT`, log path | **WSL** (copy to `/etc/motadata/` or user home) | `docs/` or `packaging/context-layer/` (to be added at implementation time) |
| **motadata-context-layer.service** (optional) | systemd unit: `ExecStart=python -m motadata_context_layer` (exact module TBD at pack time) | **WSL** | Same packaging folder as wheel |

**Optional config bundle:** single tarball containing `.env.example` + `README.install.md` — not required for v1 of this plan.

---

## 4. WSL Context Layer Package Contents

### Must include

- **Service entrypoint:** HTTP app serving at minimum `GET /healthz`, `GET /version`, `POST /v1/export_evidence` (matches current in-repo shape; implementation detail at build time).
- **Layer-5 pipeline:** workspace **resolver**, **index** builder, **lexical retrieval**, **evidence bundle** builder (`layer5.evidence_bundle.v1`).
- **Schema / contract files:** `evidence_bundle.v1.schema.json` (and any files `schema_validate` loads) bundled inside the installable package.
- **Config:** port via env (`CONTEXT_LAYER_PORT` / `MOTADATA_CONTEXT_LAYER_PORT`); optional log level / log path.
- **Health:** HTTP readiness as above.
- **Dependency manifest:** `pyproject.toml` / `requirements-context-layer.txt` slice listing only what L5 + stdlib HTTP need (no Plan-Gate, no vLLM client in WSL package).

### Must NOT include

- Full **`m-coder` repo** or git metadata as a runtime requirement.
- **Plan-Gate**, **execute service**, **sandbox**, **ledger**, **training/ML compilation** trees.
- **Observation / Layer-4** ingestion pipelines, Neo4j, vector DBs, or semantic/graph retrieval (out of scope for this package).

---

## 5. Runtime Model

**Preferred:** **Local HTTP service in WSL** (single port, persistent process).

- **Why:** Stable contract for the Windows plugin (no per-request shell/spawn fragility); easy health check; aligns with Plan-Gate client pattern.
- **How plugin talks to it:** `POST /v1/export_evidence` with JSON `{ "workspace_root", "query", "top_k" }`; response body = raw evidence bundle dict (JSON).
- **Endpoints:** `GET /healthz`, `GET /version`, `POST /v1/export_evidence`.

**Acceptable fallback:** **Installed CLI** with contract: `cli <workspace_root>` + query on stdin → bundle JSON on stdout (same as dev script semantics), invoked only if HTTP is disabled or for automation.

**Recommendation:** Ship **HTTP as default**; document CLI for diagnostics and optional plugin config `MOTADATA_CONTEXT_LAYER_CLI`.

---

## 6. Plugin Packaging / Configuration Model

### Plugin artifact output

- Standard **Gradle** `buildPlugin` → zip; version in `plugin.xml` / Gradle properties.

### Configuration (env / JVM properties — align with existing bridge)

| Concern | Env / property (planned names) | Default |
|---------|-------------------------------|---------|
| Context Layer base URL | `MOTADATA_CONTEXT_LAYER_URL`, `-Dmotadata.context_layer.url=` | `http://127.0.0.1:8091` |
| Plan-Gate base URL | existing (e.g. plugin settings / env for `RuntimeBridge` baseUrl) | `http://127.0.0.1:8089` or org default |
| Optional CLI override | `MOTADATA_CONTEXT_LAYER_CLI` | unset |
| Dev-only repo script | `MOTADATA_CONTEXT_LAYER_DEV_REPO_SCRIPT_FALLBACK` | off in release builds |

### Settings UX (future implementation, not this task)

- Minimal: registry or `.properties` for Plan-Gate URL + Context Layer URL; advanced users use IDE VM options / env.

---

## 7. Build / Release Flow

**From full GPU repo CI:**

1. **Plugin:** `./gradlew buildPlugin` → versioned zip; tag aligns with git tag / release version.
2. **Context Layer:** Build wheel (e.g. `python -m build` with a **dedicated** `pyproject` or package root that only packages `runtime/context_layer_service` + `runtime/layer5` + required schemas) → artifact `motadata-context-layer-<ver>.whl`.
3. **Version alignment:**
   - **Plugin version** and **wheel version** should match or follow a **compatibility matrix** (e.g. plugin 1.2.x requires context-layer ≥ 1.2.0).
   - **Evidence schema** is **frozen** (`layer5.evidence_bundle.v1`); bump only on intentional contract releases.
   - **`/v1/ask`** contract (`ask_request.v1.0`) is owned by GPU Plan-Gate; Context Layer and plugin must not send fields outside frozen schemas.

**GPU:** No separate “package” for Plan-Gate in this plan — continues to run from repo + venv; release is repo tag + documented env.

---

## 8. Installation / Upgrade Flow

### Windows plugin

- Install zip via IDE **Install Plugin from Disk** or marketplace update channel.
- After upgrade: verify `GET <plan-gate>/version` and `GET <context-layer>/healthz`.

### WSL Context Layer

- Create venv (recommended): `python3 -m venv /opt/motadata/context-layer && pip install motadata-context-layer-*.whl`.
- Install optional systemd user or system unit to run `python -m ...` with `WorkingDirectory` irrelevant to repo (no checkout needed).
- Upgrade: `pip install --upgrade` new wheel; restart service; check `/version` for wheel version string (handler should return package version).

### Compatibility check

- Plugin startup or first Ask: optional **preflight** — `GET` health on Context Layer + Plan-Gate; surface clear errors if unreachable.
- **Rollback:** reinstall previous plugin zip; `pip install` previous wheel; restart service.

---

## 9. Testing / Validation of Packaged Deployment

**Objective path:**

`Windows plugin → WSL Context Layer (installed) → evidence_bundle.v1 → GPU POST /v1/ask → grounded response`

| Step | Check |
|------|--------|
| WSL | `curl -s http://127.0.0.1:8091/healthz` → `ok` |
| WSL | `POST /v1/export_evidence` with real `workspace_root` + short query → 200, `schema_hint == layer5.evidence_bundle.v1`, non-empty `entries` for known-good query |
| GPU | `curl <gpu>/healthz` and `<gpu>/version` includes `ask_request_v1` |
| GPU | `POST <gpu>/v1/ask` with body built from exported bundle → 200, `PLAN_ONLY`, `evidence_first_meta.ask_path == v1_evidence` |
| Windows | One **golden Ask** from IDE (evidence-first on): dialog shows evidence entries + plan; `ask_path` indicates v1 |
| Failure | Stop Context Layer service → plugin should **not** claim success on v1 path; should hit **controlled** v0 fallback or explicit error per policy; corrupt bundle to GPU → **400** with stable `error` code, **no** silent downgrade |

---

## 10. Open Decisions / Non-Goals

### Open decisions (implementation phase)

- **Exact Python package name and module path** on import (`runtime.*` vs renamed top-level `motadata_context_layer` for installed wheel).
- **systemd vs manual** start on WSL; whether to support **WSL1** vs **WSL2-only**.
- **Single port** vs configurable firewall documentation for corporate laptops.
- **TLS termination** for Context Layer (likely unnecessary on localhost; document “do not expose publicly without auth”).

### Non-goals (this packaging phase)

- **No** separate git repo split for Context Layer (can still ship a **wheel** built from monorepo).
- **No** Neo4j, Chroma, or semantic/graph stack in the WSL package.
- **No** finetuning, training, or Layer-2 packaging.
- **No** deployment scripts or CI YAML in *this* planning task (defined only at plan level above).

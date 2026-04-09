# B5 — Host Readiness (Production-Grade Environment Hardening)

**Doc status:** artifact-driven. **Verdict:** **B5 CLOSED** (2026-04-09) — see **§0** below; §H–§I retain history.

**Scope:** Reproducible clone → configure → start → validate for the **canonical distributed setup**: backend (Context Layer, retrieval) near the workspace (**WSL or native Linux**), **Plan-Gate + vLLM on the GPU server** — same topology in every case. B5 validates reproducibility of that setup for **both workspace placements** (**WSL** vs **native Linux**) with the **same** HTTP contracts and **consistent GPU-side behavior**; only **where** the workspace backend runs differs. Governed HTTP slice: Context Layer, Plan-Gate, optional vLLM. Does not claim GPU/model parity across every machine.

> **Canonical Host Model**
>
> The system operates as a **distributed architecture**:
>
> * Backend (Context Layer, retrieval) runs near the workspace
>   → either **WSL** or **native Linux**
>
> * Plan-Gate and vLLM run on a **GPU server**
>
> These are not separate deployment profiles.
> They are **workspace-side placements within the same system topology** (same behavior; different location).

---

## 0. B5 — Host Readiness: CLOSED

**Status:** ✅ CLOSED  
**Date:** 2026-04-09

### Scope

Validate the **canonical distributed topology**:

> Workspace-side Context Layer (WSL or native Linux) + Plan-Gate + vLLM on GPU

Across both workspace placements:

- **Native Linux backend**
- **WSL backend**

With:

- identical HTTP contracts
- consistent GPU-side behavior
- no environment-dependent divergence

### Proof Summary

| Placement | Status | Evidence |
| --------- | ------ | -------- |
| Workspace backend on native Linux | ✅ PASS | `docs/validation/artifacts/b5_linux_backend_gpu/` |
| Workspace backend on WSL | ✅ PASS | `docs/validation/artifacts/b5_wsl_backend_gpu/` |

Both runs confirm:

- Context Layer reachable and exporting evidence
- Plan-Gate reachable and responding correctly
- vLLM serving expected model
- `/v0/ask` returns `PLAN_ONLY`, `execution=false`, and no application error in the success path (`error` absent or null in contract responses)
- No silent failures or misleading responses

### Conclusion

- The system behaves **identically across workspace placements**
- Differences are limited to **location (WSL vs native Linux)**, not behavior
- The **canonical topology is reproducible and stable**

### Final Verdict

> **B5 CLOSED — Host readiness is fully validated and artifact-backed**

---

## A. Host readiness status table

| Area | Current state | Evidence | Risk level |
| ---- | ------------- | -------- | ---------- |
| **Service startup — Context Layer** | `python3 -m runtime.context_layer_service` from repo root; ports via `CONTEXT_LAYER_PORT` / `MOTADATA_CONTEXT_LAYER_PORT` (default **8091**); bind via `CONTEXT_LAYER_HOST` / `MOTADATA_CONTEXT_LAYER_HOST` (`runtime/context_layer_service/config.py`). | Code inspection; `runtime/scripts/run_local_stack.sh start-context` | **Low** (stdlib HTTP; clear env) |
| **Service startup — Plan-Gate** | `python3 -m runtime.plan_gate_service.app`; port `PLAN_GATE_PORT` (default **8089**) (`runtime/plan_gate_service/config.py`). | Code inspection; `governed_services.sh` | **Low** |
| **Service startup — Ask** | Ask is **not** a separate process; **Plan-Gate** serves `POST /v1/ask` (Ask v1 ingest inside Plan-Gate). | `runtime/plan_gate_service/app.py` routes | **Low** (documented) |
| **Port management** | Defaults **8091 / 8089 / 8000**; all overridable via env vars above; `governed_services.sh` loads `demo_stack.env` for `VLLM_PORT` + `PLAN_GATE_PORT`. | `config.py` files; `governed_services.sh` | **Low** |
| **Environment variables** | **Required for full stack:** `VLLM_BASE_MODEL` (local path) in `demo_stack.env` for `governed_services.sh start`. **Implicit:** repo root as cwd for `python3 -m runtime.*` so `runtime` package resolves. | `governed_services.sh` preflight | **Medium** (vLLM path is host-specific) |
| **Path dependencies** | `WORKSPACE_ROOT` / `repo_root` in HTTP payloads must be an **absolute** path valid on the machine running Context Layer (validation sheet §A0). No hardcoded `/home/harshil` in runtime services. | `docs/Backend Production Validation Sheet.md`; plugin defaults `127.0.0.1` only | **Medium** (operator must set real path) |
| **Python / dependencies** | Plan-Gate + Context Layer + Ask path use repo **stdlib-first** Python modules; no single `requirements.txt` at repo root for the full runtime (RAG/training have separate `requirements.txt`). Host needs **Python 3** with imports available for `runtime` tree (run from checkout). | `governed_services.sh` checks `import vllm` for vLLM | **Medium** (explain path needs vLLM install) |
| **Plugin ↔ backend** | `MOTADATA_PLAN_GATE_URL` (default `http://127.0.0.1:8089`), `MOTADATA_CONTEXT_LAYER_URL` (default `http://127.0.0.1:8091`) (`MotadataRuntimeConfig.kt`, `Layer5EvidenceExporter.kt`). | Plugin source | **Low** |
| **Validation scripts** | `docs/Backend Production Validation Sheet.md` uses `CONTEXT_URL`, `PLAN_GATE_URL`, `WORKSPACE_ROOT` — **no** hardcoded user home path in the command templates (A0). | Doc inspection | **Low** |

---

## B. Fragility audit (concrete)

| # | Fragility | Where |
|---|-----------|--------|
| 1 | **Default ports** 8091 / 8089 / 8000 assumed in docs; collision if host already uses them. | Plugin defaults, validation sheet, `config.py` defaults |
| 2 | **`runtime/.config/.env.example`** contains **example** `MOTADATA_ROOT=/home/harshil/Harshil-PoCs` — misleading if copied blindly. | `runtime/.config/.env.example` (legacy); mitigated by pointer to `runtime/config/host_local.env.example` |
| 3 | **`governed_services.sh`** requires **`demo_stack.env`** (from `demo_stack.env.example`) and **valid `VLLM_BASE_MODEL`** path — cannot start vLLM without a local model. | `runtime/scripts/governed_services.sh` |
| 4 | **Context Layer not started** by `governed_services.sh` — operators must start it separately or use `run_local_stack.sh`. | **Gap before hardening:** no single script for Context Layer |
| 5 | **Startup order:** Context Layer and Plan-Gate are independent; Explain/Debug needs vLLM reachable at `MOTADATA_EXPLAIN_VLLM_URL`. | Plan-Gate env |
| 6 | **`fuser`** used on Linux for port cleanup in `governed_services.sh` — may be absent on minimal images (script still stops via PID). | `governed_services.sh` |
| 7 | **Gradle / IntelliJ** for plugin tests — environment-specific failures (known; not HTTP runtime). | JetBrains plugin |

---

## C. Minimal hardening plan (implemented)

1. **`runtime/config/host_local.env.example`** — single template: `M_CODER_REPO_ROOT`, ports, derived `MOTADATA_*` URLs, `WORKSPACE_ROOT`.
2. **`runtime/scripts/run_local_stack.sh`** — `start-context` / `stop-context` / `health` / `print-env` for Context Layer with explicit `PYTHONPATH` and logs under `runtime/.run/`.
3. **`runtime/config/README.md`** — maps config files to use cases.
4. **`runtime/config/demo_stack.env.example`** — documents `PLAN_GATE_PORT` and cross-reference to Context Layer ports.
5. **`.gitignore`** — `runtime/config/host_local.env`.
6. **Legacy `runtime/.config/.env.example`** — header note pointing to m-coder templates.

---

## D. Execute hardening (what changed)

Files added/updated: `runtime/config/host_local.env.example`, `runtime/config/README.md`, `runtime/scripts/run_local_stack.sh`, `runtime/config/demo_stack.env.example`, `.gitignore`, `runtime/.config/.env.example` (header comment).

---

## E. Clean-host simulation (commands run)

Evidence from a **fresh shell** (no `host_local.env`); ephemeral port **18291** to avoid collisions:

```bash
cd /path/to/m-coder
chmod +x runtime/scripts/run_local_stack.sh
CONTEXT_LAYER_PORT=18291 ./runtime/scripts/run_local_stack.sh start-context
./runtime/scripts/run_local_stack.sh health
CONTEXT_LAYER_PORT=18291 ./runtime/scripts/run_local_stack.sh stop-context
```

Observed (2026-04-08, Linux): Context Layer reached `/healthz` within ~2s; `health` reported `Context Layer :18291 -> OK` using the **persisted** `runtime/.run/context_layer.port` (so `health` does not require repeating `CONTEXT_LAYER_PORT`). Plan-Gate `:8089` was **OK** on this host because a listener was already present — on a clean host, start Plan-Gate separately or expect `DOWN` until Plan-Gate is up.

Plan-Gate (separate terminal, same repo):

```bash
cd /path/to/m-coder
PLAN_GATE_PORT=18089 python3 -m runtime.plan_gate_service.app
# curl http://127.0.0.1:18089/healthz
```

Ports must match `CONTEXT_URL` / `PLAN_GATE_URL` in **`docs/Backend Production Validation Sheet.md`** (A0).

---

## F. Reproducibility check

| # | Check | Result |
|---|--------|--------|
| 1 | Services start with documented env + repo root cwd | **Pass** for Context Layer + Plan-Gate (manual vLLM optional) |
| 2 | B4-style scenario (export → ask) runnable | **Pass** when both URLs + `WORKSPACE_ROOT` set per validation sheet |
| 3 | Outputs consistent | Same JSON contracts; timing varies by disk |
| 4 | No hidden manual steps | **Residual:** copy `host_local.env.example` → `host_local.env`, set absolute repo path; start Context Layer (now scripted) |

---

## G. Remaining gaps

| Gap | Severity | Needs fixing before acceptance? |
| --- | -------- | ------------------------------- |
| vLLM + local model path (`VLLM_BASE_MODEL`) varies by host | **High** for full Explain | **No** for plan-only HTTP validation; **Yes** for GPU demo parity |
| No root-level `requirements.txt` for entire `runtime` stack | **Medium** | **No** if operators use existing dev env; document `pip install` for vLLM separately |
| Plugin Gradle test sandbox | **Medium** | **No** for backend host readiness |
| Single command for “everything including vLLM” | **Low** | **No** — `governed_services.sh` already covers vLLM + Plan-Gate |

---

## H. B5 verdict (historical — superseded by §0)

**Prior state (before 2026-04-09):** **B5 PARTIALLY CLOSED** — native Linux proof only; WSL end-to-end transcript not yet in-repo.

**Current state:** **B5 CLOSED** — see **§0** (artifact-backed proof for **both** workspace placements).

---

## I. B5 Fix Pass 2 — canonical distributed proof (2026-04-08)

**A. Backend host placement status**

| Backend host placement | Current readiness | What already works | What is still uncertain | Blocking for B5? |
| ----------------- | ----------------- | -------------------- | ------------------------ | ----------------- |
| **workspace backend on native Linux** (GPU stack) | **Proven** on reference host | Health (Context Layer, Plan-Gate, vLLM `/v1/models`); `POST /v1/export_evidence`; `POST /v0/ask` with honest `PLAN_ONLY` / `execution: false` | Remote-GPU-only split not re-tested as a **separate** machine in this pass (same-host localhost proof) | **No** for closure of “canonical path works”; **Yes** if product requires mandatory remote-GPU-only transcript |
| **workspace backend on WSL** (GPU server) | **Proven** (2026-04-09) | Same HTTP contracts; artifacts under `docs/validation/artifacts/b5_wsl_backend_gpu/` and `docs/validation/b5_wsl_backend_gpu/` | Optional: remote-GPU-only transcript if product mandates | **No** — **B5 CLOSED** per §0 |

**C. Executed proof:** **Native Linux:** `docs/validation/artifacts/b5_linux_backend_gpu/` (`SUMMARY.md`, `b5_linux_backend_proof_run.txt`, `b5_v0_ask_response.json`). **WSL:** `docs/validation/artifacts/b5_wsl_backend_gpu/` + `docs/validation/b5_wsl_backend_gpu/` (README + operator artifacts).

**G. Fix Pass 2 gaps (strict)**

| Gap | Backend placement | Severity | Blocks B5 closure? | Minimal next action |
| --- | ------------ | -------- | ------------------ | ------------------- |
| WSL E2E transcript (resolved 2026-04-09) | workspace backend on WSL | — | **Resolved** | See §0; artifacts in `docs/validation/artifacts/b5_wsl_backend_gpu/` and `docs/validation/b5_wsl_backend_gpu/` |
| Remote GPU vs co-located | workspace backend on native Linux | Low | **No** | Optional: repeat health/ask with `PLAN_GATE_URL` pointing at remote GPU only |

**Verdict (Fix Pass 2 — historical):** Superseded by **§0** — **B5 CLOSED** (2026-04-09) with **both** placements artifact-backed.

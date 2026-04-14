# Motadata AI Coding Assistant — Architecture & Behavior

**Purpose:** Conceptual architecture, components, information flows, and contracts. **No** step-by-step deployment here — use the split docs below.

| Document | Use for |
|----------|---------|
| **[MOTADATA_DEMO_SETUP_RUNBOOK.md](MOTADATA_DEMO_SETUP_RUNBOOK.md)** | Deterministic **GPU → WSL → Windows** setup, commands, **expected outputs**, validation gates |
| **[MOTADATA_DEMO_SCENARIOS.md](MOTADATA_DEMO_SCENARIOS.md)** | Demo talk-track, success criteria, scripted scenarios |

**Reading order for operators:** [runbook](MOTADATA_DEMO_SETUP_RUNBOOK.md) first, then [scenarios](MOTADATA_DEMO_SCENARIOS.md); read this architecture doc for behavior and contracts.

**Typical integration branch (2026-04):** e.g. `stage-2.5-assist-layer-v1` or the branch you are validating (see [MOTADATA_DEMO_SETUP_RUNBOOK.md](MOTADATA_DEMO_SETUP_RUNBOOK.md)). Older name `feature/l5-context-layer-v1-ask-packaging` may appear in historical notes.

---

## Terminology / roles

| Term | Meaning |
|------|---------|
| **m-coder repo** | Assistant / control-plane **source** — Plan-Gate, schemas, packaging, plugin sources. **Lives on GPU-server** (clone). **Not** the indexed application codebase. |
| **Workspace repo (Motadata AIOps)** | Target **application** repo — **indexed by Context Layer** in WSL. **Clone in WSL** (Linux filesystem). |
| **Context Layer** | Packaged wheel (`motadata-context-layer`) **installed in WSL**; HTTP **`/v1/export_evidence`**. No m-coder checkout required on WSL at runtime. |
| **Plan-Gate** | GPU HTTP service — **`POST /v1/ask`** (evidence-first), **`POST /v0/ask`**, etc. Runs from **m-coder** on GPU. |
| **Plugin** | Windows JetBrains client — HTTP only; no local L5. |

**Repo placement:**

| Location | Repository |
|----------|------------|
| GPU-server | **m-coder** (Plan-Gate + vLLM launcher) |
| WSL | **Motadata AIOps** workspace + Context Layer wheel |
| Windows (optional) | m-coder **only** to build the plugin from source |

---

## 1. Purpose of the system

The Motadata AI Coding Assistant is a **governed** coding assistant: the **runtime** (not the IDE) owns **planning, boundaries, and execution posture**. The IDE is a **client**.

**Ask path (evidence-first):**

- **Plan-only by default** (`governance_posture: PLAN_ONLY`, `execution: false`).
- **Evidence-first** uses frozen **`layer5.evidence_bundle.v1`** and **`POST /v1/ask`** on Plan-Gate when the WSL Context Layer is available.
- **No silent downgrade** when Context Layer is **configured but returns errors** (HTTP/CLI failure with a body); only **unreachable** may fall back to legacy `/v0/ask` with `evidence_first`.

---

## 2. Layered architecture (high level)

| Layer | Role |
|-------|------|
| **L1** | Governance doctrine — locked; not reimplemented in the plugin. |
| **L2** | ML / compilation — separate from day-to-day IDE Ask. |
| **L3** | Runtime enforcement — Plan-Gate, context engine, sandbox, ledger — **m-coder on GPU**. |
| **L4** | Observation / drift — downstream of runtime. |
| **L5** | Workspace intelligence — index + **`layer5.evidence_bundle.v1`** — **Context Layer wheel in WSL** reads the **Motadata AIOps** workspace. |

**Deployment split:**

| Location | What runs |
|----------|-----------|
| **Windows** | JetBrains plugin — HTTP client only. |
| **WSL** | Context Layer HTTP service — port **8091** (default). |
| **GPU / server** | **vLLM** (**8000**) + **Plan-Gate** (**8089**) — mandatory for this stack. |

---

## 3. Major components

### 3.1 JetBrains plugin (`jetbrains-plugin/`)

- **`RuntimeBridge`**: Plan-Gate (`/v0/plan`, `/v0/ask`, `/v1/ask`, `/v0/execute`, `/healthz`, `/version`).
- **`Layer5EvidenceExporter`**: HTTP → `POST …/v1/export_evidence` (default **`http://127.0.0.1:8091`**), optional CLI / dev script.
- **`EvidenceExportOutcome`**: `Success` | `Unreachable` | `ServiceFailure`.
- **`AskV1Contract`**: `ask_request.v1.0` JSON; Plan-Gate v1 error classification.
- Evidence-first: `-Dmotadata.ask.evidence_first=true` or `MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST=1`.

### 3.2 WSL Context Layer (wheel)

- **Package:** `packaging/motadata-context-layer/pyproject.toml`.
- **Endpoints:** `GET /healthz`, `GET /version`, `POST /v1/export_evidence`.
- **Env:** `MOTADATA_CONTEXT_LAYER_HOST`, `MOTADATA_CONTEXT_LAYER_PORT`, logging vars.

### 3.3 Plan-Gate (`runtime/plan_gate_service/`)

- **`POST /v0/ask`**: `ask_request.v0.1` — may use ContextEngine on host.
- **`POST /v1/ask`**: `ask_request.v1.0` — strict evidence validation; evidence → `ContextBundle` → planner / reasoner.
- **`GET /version`**: advertises **`ask_request_v1`**.

### 3.4 Frozen contracts

- **`layer5.evidence_bundle.v1`**: `runtime/layer5/evidence/evidence_bundle.v1.schema.json`.
- **`ask_request.v1.0`**, **`plan_only_response.v0.1`**: under `runtime/ide/schemas/`.

### 3.5 vLLM

- OpenAI-compatible API on **`127.0.0.1:8000`** (GPU). Plan-Gate uses **`MOTADATA_EXPLAIN_VLLM_URL`** and health-checks **`GET …/v1/models`** when set.
- Remote laptops reach GPU via **SSH local forward** — see [runbook § Phase 3](MOTADATA_DEMO_SETUP_RUNBOOK.md).

---

## 4. Information flows

### 4.1 Evidence-first (target)

```
[IDE Ask, evidence_first=true]
  → Layer5EvidenceExporter → POST WSL /v1/export_evidence
  → layer5.evidence_bundle.v1
  → POST GPU /v1/ask (ask_request.v1.0)
  → Plan-Gate → plan_only_response.v0.1
```

### 4.2 Fallback (summary)

| Condition | Fallback to `/v0/ask`? |
|-----------|-------------------------|
| evidence-first off | Yes (policy) |
| Context Layer unreachable | Yes (when evidence-first on) |
| Context Layer **reachable** but export fails (4xx/5xx / bad payload) | **No** — error surface |
| `/v1/ask` contract errors | **No** |

### 4.3 Legacy Ask

`POST /v0/ask` with `ask_request.v0.1` — ContextEngine + planner path.

---

## 5. Logical diagram

```
┌─────────────────┐     HTTP      ┌──────────────────────────┐
│ JetBrains       │ ────────────► │ WSL Context Layer         │
│ (Windows)       │  :8091       │ motadata-context-layer    │
└────────┬────────┘               └──────────────────────────┘
         │ HTTP :8089
         ▼
┌─────────────────┐     mandatory  ┌─────────────┐
│ Plan-Gate       │ ◄────────────►│ vLLM        │
│ (GPU / repo)    │   explain     │ :8000       │
└─────────────────┘               └─────────────┘
```

- **`repo_root` / `workspace_root`** must be a **Linux path** the Context Layer can open (WSL). See runbook **workspace_root** section.

---

## 6. Key files (index)

| Area | Paths |
|------|--------|
| Wheel packaging | `packaging/motadata-context-layer/pyproject.toml` |
| Context Layer | `runtime/context_layer_service/` |
| v1 Ask ingest | `runtime/ask_service/v1_ingest.py`, `runtime/plan_gate_service/app.py` |
| Evidence + L5 | `runtime/layer5/` |
| Plugin | `jetbrains-plugin/.../bridge/RuntimeBridge.kt`, `Layer5EvidenceExporter.kt`, … |
| Client docs | `docs/runtime/WSL_CONTEXT_LAYER_CLIENT.md`, `docs/layer5/WSL_CONTEXT_LAYER_PACKAGING_PLAN.md` |
| Roadmap | `docs/LIVE_ROADMAP_TRACKER.md` |

---

## 7. Known limitations (architectural)

- **Plan-Gate URL** is fixed in plugin to **`http://127.0.0.1:8089`** on the **client** host — remote GPU requires **SSH tunnel** to that port (and **8000** for vLLM checks).
- **Windows ↔ WSL**: Context Layer may need `0.0.0.0` bind + WSL IP if Windows cannot reach `127.0.0.1:8091` — see runbook.
- **Windows-only project paths** are **invalid** for evidence-first (`workspace_root`).

---

*Update when architecture, ports, or contracts change.* Cross-link the [runbook](MOTADATA_DEMO_SETUP_RUNBOOK.md) for operator steps.

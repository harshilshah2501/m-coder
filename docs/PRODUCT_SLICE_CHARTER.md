# Product Slice Charter — Motadata AI Coding Assistant (m-coder)

**Status:** North-star document for the **first production-grade vertical slice** of the roadmap.  
**Scope:** This charter defines what “production-grade” means **for this slice**, not for full multi-tenant SaaS on day one.  
**Sources:** `docs/audit/END_TO_END_SYSTEM_AUDIT_REPORT.md`, `docs/audit/SURGICAL_NEXT_STEPS_PLAN.md`.

**Mindset:** The goal is a **production slice that happens to be demoable**, not a demo system with production pretensions. Engineering language should follow: *deployment and validation runbook*, *acceptance scenario suite*, *production slice readiness*, *release validation checklist* — not “demo-only” framing.

---

## Objective

Deliver the **smallest production-grade vertical slice** that is:

- **Safe** — governance and execution invariants are explicit; no silent bypass of policy.
- **Observable** — operators can tell which path ran (Ask v0 vs v1, Explain/Debug vs planner, execute vs block).
- **Deterministic where promised** — contracts and schemas are versioned; behavior is not ambiguous.
- **Extensible** — Layer-5, Plan-Gate, and plugin boundaries stay clean for roadmap work without demo-only hacks.

**Non-goal for this charter:** Define internet-scale multi-tenant SaaS, full enterprise RBAC, or unrelated ML/RAG product lines inside this slice.

### Retrieval Non-Negotiable

The system must ensure that:
- evidence bundles are dominated by AIOps implementation code
- non-code artifacts (tests, logs, vendor) do not dominate retrieval
- weak evidence triggers explicit insufficiency

Without this, the system is not considered context-aware.

---

## Canonical active slice

This is **Track A — Production Core Slice** (the real product path for this release line):

| Component | Role | Primary entry points |
|-----------|------|----------------------|
| **JetBrains plugin** | IDE client; single bridge | `jetbrains-plugin/…/RuntimeBridge.kt`, `META-INF/plugin.xml` |
| **Plan-Gate HTTP** | Governance-facing API | `runtime/plan_gate_service/app.py` — `/v0/plan`, `/v0/ask`, `/v1/ask`, `/v0/execute`, `/healthz`, `/version` |
| **Ask service** | Plan-only Ask + Explain/Debug | `runtime/ask_service/handlers.py`, `v1_ingest.py`, `reasoner.py`, `planner.py` |
| **Context Layer (Layer 5)** | Evidence export | `runtime/context_layer_service/`, `runtime/layer5/`, package `packaging/motadata-context-layer/` |
| **Governed GPU stack** | vLLM + Plan-Gate lifecycle | `runtime/scripts/governed_services.sh`, `runtime/config/demo_stack.env` |

**Frozen contracts (must remain explicit and versioned):**

- Ask: `ask_request.v0.1`, `ask_request.v1.0` — `runtime/ide/schemas/`.
- Evidence: `layer5.evidence_bundle.v1` — schema validate + packaged JSON schema.

---

## Backend host modes (single distributed topology)

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
> They are **backend host modes within the same system topology**.

At least these **two backend host modes** are in scope for validation (same topology; different placement of the workspace-side backend):

| Mode | Workspace-side backend (Context Layer / repo) | Notes (from audit / plan) |
|------|-----------------------------------------------|---------------------------|
| **A — Windows IDE + WSL backend** | IDE on Windows; repo + Context Layer on **WSL**; governed compute (**Plan-Gate + vLLM**) on **GPU** | **ASK_DEFAULT_REPO_ROOT** on the Ask host when the IDE sends a Windows `repo_root` that does not exist on the server. |
| **B — Native Linux backend** | IDE and repo on **native Linux**; governed compute on **GPU** (same as A) | Plugin and Plan-Gate **URLs** default **127.0.0.1**; remote GPU requires tunnels or **config externalization** (known gap). |

These modes must be **documented**, not one-off demo notes. Validation for each **backend host mode** belongs in the **release validation checklist** (scripts + IDE acceptance scenarios).

---

## Required contracts

Stable boundaries — no accidental ambiguity in request path.

| Boundary | Requirement |
|----------|-------------|
| **Plugin ↔ Context Layer** | `POST /v1/export_evidence` with `workspace_root`, `query`, `top_k`; success returns `layer5.evidence_bundle.v1` or explicit error JSON with `failure_class`. Configurable base URL (`MOTADATA_CONTEXT_LAYER_URL` / JVM property per audit). |
| **Plugin ↔ Plan-Gate** | JSON schemas for `POST /v0/ask`, `POST /v1/ask`, `POST /v0/plan`, `POST /v0/execute`; **v0 vs v1** behavior documented: v1 evidence-first path vs default v0. |
| **Context Layer ↔ Plan-Gate** | No direct HTTP coupling; **contract is the evidence bundle object** carried by the plugin or client into `/v1/ask`. |
| **Plan-Gate ↔ vLLM** | Explain/Debug: OpenAI-compatible `POST {base}/v1/chat/completions`; env `MOTADATA_EXPLAIN_VLLM_URL`, `MOTADATA_EXPLAIN_MODEL`. |
| **Plan-Gate ↔ execute path** | `/v0/execute` → execute service; integrity/sandbox availability **must not** present as success if the path is blocked (known product risk: “integrity not configured”). |
| **Fallback rules** | Explicit and documented: e.g. evidence-first **unreachable** may fall back to `/v0/ask`; **HTTP 4xx/5xx with service failure** must not be silently treated as absence (per `Layer5EvidenceExporter` / audit). |

---

## Required observability

**Production-grade** here requires traceability **without** relying on a single engineer’s memory.

| Requirement | Current baseline (audit) | Target |
|-------------|-------------------------|--------|
| **Per-component health** | Plan-Gate `/healthz`, Context Layer `/healthz`, vLLM `/v1/models` | Keep; automate in release checklist. |
| **Ask path visible** | `evidence_first_meta` / `ask_path` in v1 responses | Operators must see **Ask v0 vs v1** in logs or UI trace; no silent ambiguity. |
| **Debug / LLM** | `explain_debug` in response; vLLM logs | Logs must distinguish **Explain invoked** vs **template planner** vs **error**. |
| **Code path** | Execute response outcome | Must distinguish **executed vs refused vs blocked** with reason. |
| **Request correlation** | Gap: Plan-Gate HTTP **does not log requests**; `request_id` only in JSON body | **Production hard gate:** request ID appears in server logs or structured access log for Plan-Gate (see below). |
| **Plugin** | `DecisionLogger` for commit/execute; Ask not fully traced | **Production hard gate:** Ask actions emit traceable correlation (at minimum: log `request_id` + endpoint on client or server). |

Sanity checks already in the repo (e.g. `runtime/scripts/verify_ask_path.sh` for Context Layer → `/v1/ask`) are **production validation scripts**, not demo tricks.

---

## Acceptance scenarios

Former **demo scenarios** are **acceptance tests** for the slice: same steps, **pass/fail** criteria, owned by engineering.

| Scenario | Pass criteria (high level) |
|----------|----------------------------|
| **Ask v0 (default)** | `POST /v0/ask` returns `PLAN_ONLY`, `execution: false`; context reflects server-visible repo or documented fallback (`ASK_DEFAULT_REPO_ROOT`). |
| **Ask v1 (evidence-first)** | With flag on: Context Layer export succeeds; `POST /v1/ask` returns `evidence_first_meta.ask_path == v1_evidence` when applicable; fallback only where contract allows. |
| **Explain / Debug** | Selection + file → structured `explain_debug` or explicit error; vLLM path actually invoked when healthy. |
| **Plan (commit)** | `POST /v0/plan` returns governed decision; plugin shows outcome; shadow vs enforcing behavior respected. |
| **Code / Submit** | `POST /v0/execute` returns a clear outcome; **not** a misleading “success” if integrity layer is unavailable. |
| **Honest UX — grounding** | If backend includes `plan_summary.notes` or grounded-file metadata, the **IDE must not contradict** it (audit: notes omitted in UI today — **product defect** until fixed or API trimmed). |
| **Honest UX — empty context** | “No files” messaging must match backend truth (audit: `(no files selected)` is **UI copy** when list empty — must not imply backend lied). |

Automate what you can (CI, scripts); require manual IDE passes for **JetBrains UI** until UI automation exists.

---

## Production hard gates

Release of this slice (or merge to mainline) should not pass unless:

1. **Contracts** — Schemas and version strings for v0/v1 Ask and evidence bundle are **frozen for the release** and listed in release notes.
2. **Branch / mainline clarity** — Integration line is **unambiguous** (feature branch vs `main` documented; audit noted feature ahead of `main`).
3. **Backend host modes** — Modes A and B are **documented** with ports, env vars, and known limitations (localhost, tunnels).
4. **Observability minimum** — Health endpoints green for deployed components; **Plan-Gate request logging or documented workaround** for correlation (gap acknowledged in audit).
5. **Acceptance scenarios** — Core Ask / Explain / Plan / Code scenarios **pass** on a reference environment (release validation checklist).
6. **No silent theater** — Documented fallback behavior only; errors from Context Layer HTTP **surface** per contract (no fake “unreachable” when the service returned 422/500 with a body).

---

## Out-of-scope / parallel systems

Explicitly **out of product** for this slice unless the charter is revised:

| System | Rationale |
|--------|-----------|
| **RAG FastAPI stack** (`runtime/rag/`) | Parallel; not wired to JetBrains bridge (audit). |
| **Orchestrator / unrelated HTTP** in `runtime/rag/` | Same. |
| **`archive/workspace_intelligence/spikes/`** | Archived research; packaged Layer-5 lives under `runtime/layer5/`. |
| **`ml/`** training pipelines | ML product line; not required for governed IDE slice. |
| **`observation/`** drift tooling | Separate concern. |
| **Dead code** | e.g. `AskClient.kt` unused — remove or wire; do not carry indefinitely. |

**Naming clarity:** `runtime/plan_gate_service/` (HTTP daemon) vs `runtime/plangate/PlanGateService` (in-process) are **different concepts** — glossary required in **Track B** docs to avoid operational errors.

---

## Non-goals for this slice

- Full multi-tenant SaaS, global edge deployment, or arbitrary cross-tenant isolation.
- Semantic / embedding retrieval **as a gate** (lexical Layer-5 MVP may have **ranking debt**; tracked under Track C).
- Deep PSI/AST editor intelligence (string-level context is the current ceiling per audit).
- Replacing parallel RAG/orchestrator stacks in-repo without an explicit product decision.

---

## Program tracks (roadmap framing)

| Track | Name | Contents |
|-------|------|----------|
| **A** | **Production Core Slice** | Plugin, Context Layer, Plan-Gate, Ask/Debug/Plan/Code, governed services, packaging/deployment |
| **B** | **Production Readiness** | Logs, health, host readiness (backend modes), config externalization, branch/mainline clarity, **canonical docs**, release validation checklist |
| **C** | **Quality and Intelligence** | Retrieval/ranking, editor awareness, richer UI, multi-model orchestration — **after** A/B are solid |

Sequence matches the surgical plan: **prove path → prove scenario → perception/defects → configurability → retrieval last**.

---

## Next implementation priorities

Derived from **P0–P2** in `docs/audit/SURGICAL_NEXT_STEPS_PLAN.md` and audit gaps — **intent only**; this charter does not schedule sprints.

1. **Mainline and docs** — Unambiguous integration branch vs `main`; rename/align **deployment and validation runbook** language with reality.
2. **Honest UX** — Surface `plan_summary.notes` or align API/UI so operators never see “silent” failure modes.
3. **Execute path clarity** — No surprise “integrity not configured” without preflight documentation or UI warning.
4. **Cross-host** — `ASK_DEFAULT_REPO_ROOT` and evidence-first flags **documented** for backend host modes; **Plan-Gate URL** configurability when the native Linux backend goes beyond localhost.
5. **Observability** — Plan-Gate access or structured logging with `request_id`.
6. **Debt cleanup** — Dead `AskClient`, glossary for PlanGate naming.
7. **Track C** — Retrieval and ranking only when acceptance scenarios show **concrete** failure modes.

---

## Related documents

| Document | Role |
|----------|------|
| `docs/audit/END_TO_END_SYSTEM_AUDIT_REPORT.md` | Factual baseline |
| `docs/audit/SURGICAL_NEXT_STEPS_PLAN.md` | Sequenced validation and remediation |
| `docs/MOTADATA_DEMO_SETUP_RUNBOOK.md` | **Should evolve into** deployment + validation runbook (content to be aligned with this charter) |
| `docs/MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md` | Architecture; must stay consistent with this slice |
| `packaging/motadata-context-layer/README.md` | Context Layer deployment |
| `runtime/plan_gate_service/README.md` | Plan-Gate deployment |

---

*This charter is the product-grade anchor for implementation; update it when the slice’s contracts or host-mode documentation change.*

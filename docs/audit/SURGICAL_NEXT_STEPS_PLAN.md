# Surgical Next-Steps Plan — Motadata m-coder

**Source of truth:** `docs/audit/END_TO_END_SYSTEM_AUDIT_REPORT.md` (audit dated 2026-03-23).  
**Mode:** Planning only — no implementation implied.  
**Purpose:** Controlled validation and remediation sequencing.

**Legend for work types**

| Tag | Meaning |
|-----|---------|
| **Prove path** | Automated or scripted checks that the HTTP/runtime chain works end-to-end |
| **Prove scenario** | Human-driven demo or manual scenario that exercises a user-visible story |
| **Fix perception** | UI, messaging, or operator docs so outcomes match what the backend actually did |
| **Improve retrieval** | Changes to Layer-5 indexing, scoring, or query handling (quality, not just visibility) |

---

## 1. Canonical active product slice

Per audit §1, §2, §16:

- **JetBrains plugin** (`jetbrains-plugin/`) — single integration point **`RuntimeBridge.kt`** + actions in `plugin.xml`.
- **Plan-Gate HTTP** (`runtime/plan_gate_service/app.py`) — `/v0/plan`, `/v0/ask`, `/v1/ask`, `/v0/execute`, `/healthz`, `/version`.
- **Ask service** (`runtime/ask_service/`) — v0 `handlers.py`, v1 `v1_ingest.py`, Explain/Debug `reasoner.py`, deterministic `planner.py`.
- **Context Layer (Layer-5 package)** — `runtime/context_layer_service/`, `runtime/layer5/`, `packaging/motadata-context-layer/`, entry `motadata-context-layer` / `python -m runtime.context_layer_service`.
- **GPU stack scripts** — `runtime/scripts/governed_services.sh` (vLLM + Plan-Gate lifecycle), config `runtime/config/demo_stack.env` (per audit §7.3).

**Contracts (canonical):** `runtime/ide/schemas/ask_request.v0.1.schema.json`, `ask_request.v1.0.schema.json`; evidence `layer5.evidence_bundle.v1` (`schema_validate` + packaged JSON schema).

---

## 2. In-scope vs out-of-scope directories/files

### In scope (validation + targeted remediation)

| Area | Paths |
|------|--------|
| Plugin bridge & UI | `jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/bridge/`, `.../ask/`, `.../actions/`, `.../vcs/`, `META-INF/plugin.xml` |
| Plan-Gate HTTP | `runtime/plan_gate_service/` |
| Ask / execute | `runtime/ask_service/`, `runtime/execute_service/` (for Submit-to-Runtime) |
| Context + Layer-5 | `runtime/context_layer_service/`, `runtime/layer5/` |
| Packaging & CI | `packaging/motadata-context-layer/`, `.github/workflows/wsl-context-layer-package.yml` |
| Operator scripts | `runtime/scripts/governed_services.sh`, `runtime/scripts/verify_ask_path.sh`, `runtime/config/demo_stack.env.example` |
| Plugin-relevant docs | `docs/MOTADATA_DEMO_SETUP_RUNBOOK.md`, `docs/MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md`, `packaging/motadata-context-layer/README.md`, `runtime/plan_gate_service/README.md`, `docs/runtime/` WSL client docs (per audit §11) |

### Out of scope (unless explicitly expanding product)

| Area | Rationale (audit) |
|------|-------------------|
| `archive/legacy_runtime_rag/` FastAPI RAG API | Parallel stack; **not** wired to plugin (audit §3, §8, §17) |
| `archive/legacy_runtime_rag/src/run_orchestrator.py` and related | Not part of JetBrains bridge |
| `archive/workspace_intelligence/spikes/` | Archived spike; packaged L5 is `runtime/layer5/` (audit §3) |
| `ml/` | ML pipeline; not required for JetBrains slice (audit §3) |
| `observation/` | Separate drift/observation concern (audit §3) |
| `docs/audit/PHASE_*`, `BATCH_*`, etc. | Historical; not operational runbooks (audit §11) |
| **`AskClient.kt`** | Treat as **dead code** until removal or rewiring decision (audit §5.10, §17) |

---

## 3. Canonical docs set

Per audit §11 + §16 — **one primary narrative per concern**; others become supporting or explicitly “historical.”

| Role | Document | Notes |
|------|-----------|--------|
| **Slice architecture** | `docs/MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md` | Active-supporting; verify against `RuntimeBridge` + Plan-Gate |
| **Operator setup / demo** | `docs/MOTADATA_DEMO_SETUP_RUNBOOK.md` | Align with `governed_services.sh` and ports |
| **Context Layer install/run** | `packaging/motadata-context-layer/README.md` | Wheel + WSL pipeline |
| **Plan-Gate service** | `runtime/plan_gate_service/README.md` | Env and endpoints |
| **WSL / client** | `docs/runtime/WSL_CONTEXT_LAYER_CLIENT.md` (if present — audit references) | Plugin ↔ Context Layer |
| **Roadmap / status** | `docs/LIVE_ROADMAP_TRACKER.md` | Supporting; not a substitute for code |
| **End-to-end reality** | `docs/audit/END_TO_END_SYSTEM_AUDIT_REPORT.md` | Baseline for this plan |
| **Historical** | `docs/audit/PHASE_*`, `BATCH_*`, etc. | Do not use for CI or demo steps |

**Action (prove scenario + fix perception):** Before the next external demo, walk through runbook steps once and **mark mismatches** (documentation vs actual ports, flags, and branches) — no code required in this plan.

---

## 4. Supported host profiles

Per audit §6.8, §14.

| Profile | Status in audit | Implications for validation |
|---------|-----------------|-----------------------------|
| **Windows + JetBrains + WSL + GPU** | Documented / packaging emphasis | Use `ASK_DEFAULT_REPO_ROOT` on GPU when IDE sends Windows `repo_root` (audit §4.5, §6.8) |
| **Native Linux + JetBrains + local repo + local Context Layer + remote GPU** | **Partial** (audit §14) | Plan-Gate and plugin default **127.0.0.1**; remote GPU needs tunnel or configurable URLs — **not** fully productized in plugin |

**Prove path:** For each profile you claim in a demo, run `verify_ask_path.sh` (where applicable) and plugin actions against the **same** host layout as the audience.

---

## 5. Endpoint-to-action matrix (Ask / Debug / Plan / Code)

Maps user-facing **actions** to **HTTP endpoints** (audit §4, §8).

| User-facing action | Plugin entry | Primary endpoints | Secondary / dependencies |
|--------------------|--------------|---------------------|---------------------------|
| **Ask (v0, default)** | Ask Motadata AI, evidence-first **off** | `POST /v0/ask` (Plan-Gate) | Context on server: `ContextEngine` + manifest path in `handlers.py`; optional `ASK_DEFAULT_REPO_ROOT` |
| **Ask (evidence-first → v1)** | Ask Motadata AI + `MotadataAskFlags` | `POST /v1/export_evidence` (Context Layer) → `POST /v1/ask` (Plan-Gate) | Fallback: `POST /v0/ask` with `evidence_first` when unreachable / 404/405 (audit §4.11) |
| **Debug / Explain** | Ask with selection + file → `EXPLAIN_DEBUG` | `POST /v0/ask` or `POST /v1/ask` (response includes `explain_debug`) | `POST {vLLM}/v1/chat/completions` via `reasoner.explain_debug`; env `MOTADATA_EXPLAIN_VLLM_URL`, `MOTADATA_EXPLAIN_MODEL` |
| **Plan (commit governance)** | VCS commit handler | `POST /v0/plan` | `PlanGateClient` / `RuntimeBridge.evaluateCommit` |
| **Code / execute** | Submit to Runtime | `POST /v0/execute` | `execute_service.handlers`; integrity + sandbox imports (audit §4.8) |

**Prove path:** `runtime/scripts/verify_ask_path.sh` covers **Context Layer → `/v1/ask`** only (audit §12). There is **no** single script in the audit that covers v0 Ask + Explain/Debug + Execute — those need **additional** curl/IDE scenarios.

---

## 6. Log-to-endpoint tracing matrix

Per audit §9.

| Observable | Location | What you can infer |
|------------|----------|---------------------|
| Plan-Gate process output | `runtime/.run/plan_gate.log` (when started via `governed_services.sh`) | Process stderr; **HTTP access not logged** (`log_message` disabled in `app.py`) |
| vLLM | `runtime/.run/vllm.log` | Model load errors, generation |
| Context Layer | stderr or `MOTADATA_CONTEXT_LAYER_LOG_PATH` | Export failures; request line at DEBUG (`app.py`) |
| Plugin | `DecisionLogger` | Commit / execute-oriented logging — **not** full Ask tracing (audit §9) |

**Gap (audit §9):** No request-ID correlation from IDE JSON body to server logs for Plan-Gate.

| Desired trace | Prove path (controlled validation) | Fix perception / future fix |
|---------------|-----------------------------------|------------------------------|
| “Did `/v0/ask` run?” | Capture Plan-Gate with temporary logging or tcpdump locally; compare timestamp to IDE action | Document that correlation is manual unless logging added |
| “Did vLLM answer Explain?” | Read `vllm.log` for POST window; match rough time to IDE action | Same |

---

## 7. JetBrains UI test matrix

Per audit §5, §13.

| # | Scenario | Expected backend | UI expectation | Audit risk |
|---|----------|------------------|----------------|------------|
| 1 | Ask, no selection, evidence-first **off** | `/v0/ask` | Plan-only dialog; context files or empty list | Empty list shows “(no files selected)” **as UI text** — not backend string (audit §5.8) |
| 2 | Ask, evidence-first **on**, Context Layer up | export → `/v1/ask` | Evidence entries + v1 label | Operator must set JVM/env flag (audit §13) |
| 3 | Ask, evidence-first **on**, Context Layer down | Fallback `/v0/ask` with flag | Still plan-only | ServiceFailure on HTTP error **no** silent fallback (audit §4.11) |
| 4 | Explain/Debug with selection | `explain_debug` in response | Explain/Debug dialog branch | vLLM must return parseable JSON (audit §4.7) |
| 5 | Plan steps | `plan_summary.steps` | Steps listed | **`plan_summary.notes` not shown** (audit §5.7) — perception gap |
| 6 | Submit to Runtime | `/v0/execute` | Outcome dialog | May show integrity “not configured” if imports fail (audit §4.8, §13) |
| 7 | Commit | `/v0/plan` | Notification | Shadow vs enforcing per handler |

**Prove scenario:** Run rows 1–4 on the **target demo host** before the demo; row 5 validates the **notes** gap without code change.

---

## 8. Retrieval-quality validation matrix

Per audit §6.6–6.7 (lexical-only, symbol boost unused, empty query behavior, large-file overweight).

| Check | Type | Method |
|-------|------|--------|
| Lexical scoring behaves as documented | Prove path | Unit tests in `runtime/layer5/tests/` (audit mentions test files); run in CI locally |
| Same query → stable top-k order | Prove path | Deterministic ordering in `lexical.py` (audit §6.6) — compare two runs |
| Short tokens dropped | Prove path | Query with 2-char tokens vs 3+ in `handlers.py` / `_extract_symbol_hints` (audit §6.7) |
| “Test file dominance” / large files | Prove scenario | Manual query on a repo with large tests; observe evidence entries |
| Empty / whitespace query | Prove scenario | `export_evidence` with edge query; audit: lexicographic top-k when no tokens (audit §6.7) |

**Improve retrieval:** Address only after **prove scenario** shows a demo-blocking wrong file order.

---

## 9. P0 fixes

P0 = blocks honest demo, safety, or merge clarity. Each item ties to audit **§15 Key inconsistencies** or **§13 Demo-readiness**.

### P0-A — Merge / branch clarity

| Field | Detail |
|-------|--------|
| **Why needed** | Audit §10: feature branch is **ahead of `main`**; operators may follow wrong branch or stale docs. |
| **Type** | **Prove path** (git) + **fix perception** (docs / README pointer) |
| **Files likely affected** | `README.md` or top-level contributor note (if you add a branch pointer); release process doc — **not** listed in audit as existing |
| **Risk** | Low if limited to “current integration line lives on branch X until merged” |
| **Before demo?** | Yes if audience clones `main` expecting L5+v1 Ask |

### P0-B — `plan_summary.notes` invisible in IDE

| Field | Detail |
|-------|--------|
| **Why needed** | Audit §5.7, §13: API returns **notes** for ungrounded/error cases; UI only shows **steps** — demo looks “silent” on honesty/no-match. |
| **Type** | **Fix perception** (primary); optional contract trim later |
| **Files likely affected** | `jetbrains-plugin/.../AskMotadataAiAction.kt` (render `notes`); possibly `RuntimeResponse` if structured |
| **Risk** | Low–medium (dialog size, null handling) |
| **Before demo?** | **Yes** if demo script relies on “no match” messaging |

### P0-C — Execute path “integrity not configured”

| Field | Detail |
|-------|--------|
| **Why needed** | Audit §4.8, §13: `/v0/execute` can return BLOCKED when imports fail — **surprising** in demo. |
| **Type** | **Prove path** first (run Submit on target env), then **fix perception** (pre-flight message in docs or UI) or remediation |
| **Files likely affected** | `runtime/execute_service/handlers.py`; docs; optionally `SubmitToRuntimeAction.kt` |
| **Risk** | Medium if changing execute behavior; low for docs-only |
| **Before demo?** | **Yes** if “Submit to Runtime” is in the script |

### P0-D — Evidence-first flag not obvious to operators

| Field | Detail |
|-------|--------|
| **Why needed** | Audit §1, §13: evidence-first is **opt-in**; demo fails silently if operator expects v1 without flag. |
| **Type** | **Fix perception** + **prove scenario** |
| **Files likely affected** | `docs/MOTADATA_DEMO_SETUP_RUNBOOK.md`, `MotadataAskFlags.kt` (docstring only) or runbook JVM line |
| **Risk** | Low |
| **Before demo?** | **Yes** for v1/evidence demo |

### P0-E — Cross-host `repo_root` (Windows IDE → Linux GPU)

| Field | Detail |
|-------|--------|
| **Why needed** | Audit §6.8, §13: Ask v0 needs **`ASK_DEFAULT_REPO_ROOT`** when server path invalid. |
| **Type** | **Prove scenario** on exact layout + **fix perception** in runbook |
| **Files likely affected** | GPU env file `runtime/config/demo_stack.env`; runbook |
| **Risk** | Low for documentation |
| **Before demo?** | **Yes** for Windows+WSL+GPU profile |

---

## 10. P1 fixes

P1 = important product hardening; not always demo-blocking.

### P1-A — Configurable Plan-Gate base URL in plugin

| Field | Detail |
|-------|--------|
| **Why needed** | Audit §5.4, §14: **hardcoded** `http://127.0.0.1:8089`; remote GPU / tunnels need flexibility. |
| **Type** | **Prove path** (tunnel scenario) then code change |
| **Files likely affected** | `RuntimeBridge.kt`, `PlanGateClient.kt`, optionally `SubmitToRuntimeAction.kt` messages |
| **Risk** | Medium (misconfiguration) |
| **Before demo?** | Only if demo uses non-localhost Plan-Gate |

### P1-B — Plan-Gate bind address (127.0.0.1 only)

| Field | Detail |
|-------|--------|
| **Why needed** | Audit §14–15: `HTTPServer` on **127.0.0.1** — intentional localhost; document or optional `0.0.0.0` for controlled networks. |
| **Type** | **Fix perception** first; optional **prove path** with SSH tunnel |
| **Files likely affected** | `runtime/plan_gate_service/app.py` (`run_server`), README |
| **Risk** | High if opening to all interfaces without auth |
| **Before demo?** | Usually **no** if using SSH tunnel |

### P1-C — Remove or wire `AskClient.kt`

| Field | Detail |
|-------|--------|
| **Why needed** | Audit §5.10, §17: **unused**; confuses maintainers. |
| **Type** | **Fix perception** (delete) or wire to tests only |
| **Files likely affected** | `jetbrains-plugin/.../AskClient.kt`, any Gradle test references |
| **Risk** | Low if truly unused |
| **Before demo?** | No |

### P1-D — Request ID / access logging on Plan-Gate

| Field | Detail |
|-------|--------|
| **Why needed** | Audit §9: no HTTP access logs; hard to debug Ask. |
| **Type** | Observability improvement (not “perception” alone) |
| **Files likely affected** | `runtime/plan_gate_service/app.py` |
| **Risk** | Low (PII in paths — sanitize) |
| **Before demo?** | No; helps operators |

### P1-E — Naming: `plan_gate_service` vs `plangate/PlanGateService`

| Field | Detail |
|-------|--------|
| **Why needed** | Audit §3, §15: two **different** “PlanGate” concepts. |
| **Type** | **Fix perception** (glossary in one doc) |
| **Files likely affected** | `docs/MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md` or small `docs/runtime/GLOSSARY.md` |
| **Risk** | None |
| **Before demo?** | Nice for internal clarity |

---

## 11. P2 fixes

P2 = longer-term quality and scope.

### P2-A — Lexical retrieval improvements

| Field | Detail |
|-------|--------|
| **Why needed** | Audit §6.7: lexical-only, test-file overweight, no symbol boost. |
| **Type** | **Improve retrieval** |
| **Files likely affected** | `runtime/layer5/retrieval/lexical.py`, `config.py`, `evidence/builder.py`, tests |
| **Risk** | Medium (behavior change) |
| **Before demo?** | No — only if retrieval fails visibly |

### P2-B — Deeper IDE integration (PSI / structure)

| Field | Detail |
|-------|--------|
| **Why needed** | Audit §5.9: **string-only** context. |
| **Type** | Feature work |
| **Files likely affected** | New Kotlin modules, `AskMotadataAiAction.kt` |
| **Risk** | High |
| **Before demo?** | No |

### P2-C — RAG / orchestrator alignment or explicit “out of product”

| Field | Detail |
|-------|--------|
| **Why needed** | Audit §15: large parallel stack **risks confusion**. |
| **Type** | **Fix perception** (README boundary) |
| **Files likely affected** | Root `README.md` or `docs/` index |
| **Risk** | Low |
| **Before demo?** | Optional |

---

## 12. Recommended order of execution

Ordered for **controlled validation first**, then **perception fixes that affect demos**, then **config/hardening**, then **quality**.

1. **Prove path:** `governed_services.sh status` → `verify_ask_path.sh` with real `WORKSPACE_ROOT` / `QUERY` on target host (audit §12).
2. **Prove scenario:** JetBrains UI matrix §7 rows 1–4 on the demo machine; record **Windows path** behavior and `ASK_DEFAULT_REPO_ROOT` (P0-E).
3. **Prove scenario:** Submit to Runtime + Commit (rows 6–7); if execute blocked, capture exact message (P0-C).
4. **Fix perception / P0:** Runbook updates for evidence-first flag (P0-D), branch vs `main` (P0-A), notes gap decision (P0-B — implement when you exit read-only mode).
5. **P1:** Plan-Gate URL configurability **if** demo topology requires it (P1-A); glossary (P1-E).
6. **P2:** Retrieval (P2-A) only after §8 matrices show a **specific** failure.

**Separation reminder**

- **Prove path** and **prove scenario** should complete **before** large code changes so you know whether a bug is **backend**, **network**, or **expectation**.
- **Fix perception** (notes, runbook, glossary) yields **fast** demo wins without changing retrieval.
- **Improve retrieval** stays last unless evidence export is **wrong** for the scripted query.

---

*End of plan.*

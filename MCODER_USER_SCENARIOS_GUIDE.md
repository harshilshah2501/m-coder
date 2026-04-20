# m-coder — User scenarios guide (Ask · Debug · Plan · Code · Agent)

**Purpose:** One self-sufficient entry for **what each capability is**, **how it maps to HTTP/services**, **how to run the full scenario suite**, and **where to go deeper**. This file lives at the repository root so operators and new contributors can find it without digging through `docs/`.

**Scope:** Motadata AIOps-style verification (Context Layer + Plan-Gate + optional vLLM). Product behavior is **governed**: evidence-first Ask, structured EXPLAIN_DEBUG, plan decisions, bounded execute, no public “agent” API route.

**Deeper runbooks (setup, ports, troubleshooting):** [docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md](docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md)  
**Verifier output interpretation:** [docs/demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md](docs/demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md)  
**Documentation index:** [docs/NAVIGATION_HUB.md](docs/NAVIGATION_HUB.md)

---

## 1. Mental model

All user-visible modes share the same spine:

1. **Workspace (WSL/Linux):** deterministic retrieval, export evidence (`layer5.evidence_bundle.v1` where applicable).
2. **GPU host (or tunneled):** Plan-Gate validates contracts and posture; vLLM runs only for governed reasoning paths.
3. **IDE plugin (optional for this guide):** thin client; HTTP verification below does not require the IDE.

```
User / CLI → Context Layer (evidence) → Plan-Gate (/v1/ask, /v0/plan, /v0/execute) → vLLM (when applicable) → structured response
```

---

## 2. The five capabilities

| Capability | User intent (plain language) | Typical API path | What “pass” means at a high level |
|------------|------------------------------|------------------|-------------------------------------|
| **Ask** (`query`) | “Answer from my repo with grounded context.” | `POST /v1/export_evidence` → `POST /v1/ask` | `ask_path=v1_evidence`, `PLAN_ONLY`, `execution=false`, plan steps present |
| **Debug** | “Explain/debug this selection with structured output.” | Same export → `POST /v1/ask` with `task_type=EXPLAIN_DEBUG` | `routing_mode=explain_debug`, structured `explain_debug` payload (or explicit error) |
| **Plan** | “Get a governed Plan-Gate decision for a planning-style event.” | `POST /v0/plan` | Valid `decision_response.v0.1` with a real decision (refusal is valid) |
| **Code** | “Run a governed, bounded command (e.g. safe probe).” | `POST /v0/execute` | Valid `execute_response.v0.1` with explicit `outcome` / `executed` |
| **Agent** | “Is there a separate autonomous agent HTTP API?” | Probe `POST/GET /v0/agent` + inspect Ask | **`/v0/agent` returns 404 by design**; Ask responses may include **`assist_layer`** (advisory metadata) |

**Important:** Ask and Debug are **not** free-form chat bypasses. They consume **validated evidence** and remain **plan-only** for normal Ask unless execution is explicitly gated elsewhere.

---

## 3. Canonical scenario definitions (machine-readable)

All pinned scenarios (queries, expectations, capability tags) live in:

**[docs/validation/motadata_aiops_behavior_scenarios.v1.json](docs/validation/motadata_aiops_behavior_scenarios.v1.json)**

Each scenario row includes:

- **`id`** — stable name for logs and regressions  
- **`capability`** — one of `ask`, `debug`, `plan`, `code`, `agent`  
- **`expect`** — contract fields the automated verifier checks  

### 3.1 Scenario index (current pack)

| id | capability | Short description |
|----|------------|-------------------|
| `ask_broad_correlation` | ask | Broad repo question, v1 evidence path |
| `ask_symbol_anchored` | ask | Anchored symbols (e.g. correlation engines) |
| `ask_anchor_owner_gate` | ask | Authority / owner in top-3, Stage A owner lane |
| `ask_anchor_owner_top1` | ask | Strict owner / top-rank expectations |
| `ask_api_request_routing_owner` | ask | API routing owner anchoring |
| `ask_servicenow_sync_owner` | ask | ServiceNow sync owner anchoring |
| `debug_explain_selection` | debug | EXPLAIN_DEBUG with file + selection |
| `debug_explain_missing_selected_file` | debug | Honest insufficiency when file missing from context |
| `plan_pr_merge_shadow` | plan | Shadow PR-merge style `plan_request` → governed decision |
| `code_echo_probe` | code | Safe `echo` execute probe |
| `agent_no_route` | agent | No `/v0/agent`; assist present on Ask |

Quality policy (thresholds used with retrieval) is separate: **[docs/validation/motadata_evidence_quality_policy.v1.json](docs/validation/motadata_evidence_quality_policy.v1.json)**

---

## 4. How to run **all** scenarios (automated)

**Prerequisites:** GPU Plan-Gate + vLLM and WSL Context Layer stacks are up; `MOTADATA_REPO_ROOT` points at your Motadata workspace clone. Full chronology: [docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md](docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md) §2–4.

From the **m-coder repo root** (adjust `MOTADATA_REPO_ROOT`):

```bash
export M_CODER_ROOT="$(pwd)"
export PYTHONPATH="$M_CODER_ROOT"
export MOTADATA_REPO_ROOT="/path/to/your/Motadata"   # required

python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.json
```

- Exit code **0** when every scenario passes.  
- **`runtime/.run/motadata_behavior_validation.json`** — machine-readable artifact for CI or diffs.  
- Read stdout with **`[PASS]` / `[FAIL]`** per scenario: [docs/demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md](docs/demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md)

### 4.1 Smoke run with **your** Ask + Debug wording (still exercises all five)

Still runs plan (shadow), code (echo), and agent probe; only the **Ask** and **EXPLAIN_DEBUG** strings change:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --query "YOUR_REPO_QUESTION_HERE" \
  --debug-query "YOUR_DEBUG_QUESTION_HERE" \
  --top-k 8 \
  --print dev
```

Plan and execute steps use the verifier’s **built-in** synthetic plan event and **safe** echo unless you call those APIs manually (see production guide §6.3 Option B).

---

## 5. Quick manual checklist (curl / IDE)

Use when services are healthy ([production guide §6](docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md)):

| Capability | Check |
|------------|--------|
| Ask | Evidence export + `/v1/ask` → `governance_posture=PLAN_ONLY`, `execution=false`, non-empty plan steps |
| Debug | `/v1/ask` + `EXPLAIN_DEBUG` → `routing_mode=explain_debug`, structured explain or explicit error |
| Plan | `POST /v0/plan` → `decision_response.v0.1` with a decision |
| Code | `POST /v0/execute` → `execute_response.v0.1` with outcome |
| Agent | `GET` or `POST` `/v0/agent` → **404**; Ask response includes **`assist_layer`** |

Plan-Gate route reference: [runtime/plan_gate_service/README.md](runtime/plan_gate_service/README.md)

---

## 6. IDE-oriented narrative (optional)

For **what to click** and demo-style flows (JetBrains-oriented notes), see:

- [docs/demo/JETBRAINS_DEMO_NOTES.md](docs/demo/JETBRAINS_DEMO_NOTES.md)  
- [docs/MOTADATA_DEMOBOOK.md](docs/MOTADATA_DEMOBOOK.md)  
- [docs/MOTADATA_DEMO_SCENARIOS.md](docs/MOTADATA_DEMO_SCENARIOS.md)

---

## 7. Related documents (by role)

| Need | Document |
|------|----------|
| Full GPU + WSL setup, preflight, tunnels | [docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md](docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md) |
| Understand verifier logs and JSON fields | [docs/demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md](docs/demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md) |
| Demo machine topology | [docs/MOTADATA_DEMO_SETUP_RUNBOOK.md](docs/MOTADATA_DEMO_SETUP_RUNBOOK.md) |
| Architecture / layers | [docs/ARCHITECTURE_4_LAYER.md](docs/ARCHITECTURE_4_LAYER.md), [docs/PRODUCT_SLICE.md](docs/PRODUCT_SLICE.md) |
| High-level Q&A (onboarding) | [m_coder_top_150_q_a.md](m_coder_top_150_q_a.md) |

---

## 8. History note

Older drafts pointed operators at a temporary integration guide; that file is archived and redirects to the **production verification guide**. This **User scenarios guide** is the root-level index for **capability coverage**; setup details remain in the production guide above.

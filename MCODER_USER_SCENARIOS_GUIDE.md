# m-coder — User scenarios guide (Ask · Debug · Plan · Code · Agent)

**Purpose:** One self-sufficient entry for **what each capability is**, **how it maps to HTTP/services**, **how to run the full scenario suite**, **how to run any single scenario by id** ([§5](#single-scenario-commands)), and **where to go deeper**. This file lives at the repository root so operators and new contributors can find it without digging through `docs/`.

**Overwhelmed by too many docs?** Use the single router first: **[MOTADATA_SIMPLE_PATH.md](MOTADATA_SIMPLE_PATH.md)** (three paths: automated checks, manual HTTP with your own query, or first-time setup). This file is the **detailed** scenario contract; it does not repeat that router table.

**Which files are in the verification/demo edit scope:** [docs/guides/VERIFICATION_DEMO_DOC_ALLOWLIST.md](docs/guides/VERIFICATION_DEMO_DOC_ALLOWLIST.md).

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
- For a **non-developer-friendly** narrative (plain English per scenario, no raw `expect` blobs), use **`--print plain`** instead of `--print dev`. Narratives live in [docs/validation/motadata_aiops_behavior_scenario_plain_language.v1.json](docs/validation/motadata_aiops_behavior_scenario_plain_language.v1.json); override with **`--plain-language PATH`** if you maintain a forked copy.

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

<a id="single-scenario-commands"></a>

## 5. Run **one** scenario at a time (exact commands)

Use **`--scenario-id`** (repeatable) with the same scenario file. Only the matching row(s) from [motadata_aiops_behavior_scenarios.v1.json](docs/validation/motadata_aiops_behavior_scenarios.v1.json) run; the smoke pipeline is skipped when you add **`--scenarios-only`**.

**Shared prerequisites** (from the m-coder repo root):

```bash
export M_CODER_ROOT="$(pwd)"
export PYTHONPATH="$M_CODER_ROOT"
export MOTADATA_REPO_ROOT="/path/to/your/Motadata"   # Linux path to Motadata workspace
export CONTEXT_URL="${CONTEXT_URL:-http://127.0.0.1:8091}"
export PLAN_GATE_URL="${PLAN_GATE_URL:-http://127.0.0.1:8089}"
```

**Template** (replace `SCENARIO_ID` and paths as needed):

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --context-url "${CONTEXT_URL}" \
  --plan-gate-url "${PLAN_GATE_URL}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id SCENARIO_ID \
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.json
```

- **Multiple ids in one run:** repeat `--scenario-id` (example: `--scenario-id ask_broad_correlation --scenario-id ask_symbol_anchored`).
- **Unknown id:** the verifier prints a **WARNING** to stderr and that id is skipped; if nothing runs, the report has `all_pass: false`.
- **Quality policy:** omit `--quality-policy ""` only if you intentionally want to disable scenario-time retrieval gates (same as the production guide).

### 5.1 Ask (`capability: ask`)

| `id` | What it tests (short) |
|------|------------------------|
| `ask_broad_correlation` | Broad repo question, v1 evidence, plan-only |
| `ask_symbol_anchored` | Anchored symbols (correlation engines) |
| `ask_anchor_owner_gate` | Authority owner + Stage A + owner in top-3 |
| `ask_anchor_owner_top1` | Strict owner top-1 / validated authority |
| `ask_api_request_routing_owner` | API routing → APIServer owner |
| `ask_servicenow_sync_owner` | ServiceNow sync → integration owner |

**Commands:**

```bash
# ask_broad_correlation
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id ask_broad_correlation \
  --scenarios-only --print dev

# ask_symbol_anchored
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id ask_symbol_anchored \
  --scenarios-only --print dev

# ask_anchor_owner_gate
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id ask_anchor_owner_gate \
  --scenarios-only --print dev

# ask_anchor_owner_top1
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id ask_anchor_owner_top1 \
  --scenarios-only --print dev

# ask_api_request_routing_owner
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id ask_api_request_routing_owner \
  --scenarios-only --print dev

# ask_servicenow_sync_owner
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id ask_servicenow_sync_owner \
  --scenarios-only --print dev
```

### 5.2 Debug (`capability: debug`)

| `id` | What it tests (short) |
|------|------------------------|
| `debug_explain_selection` | EXPLAIN_DEBUG with real file + selection text |
| `debug_explain_missing_selected_file` | Honest “insufficient / missing_in_context” when file is absent |

```bash
# debug_explain_selection
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id debug_explain_selection \
  --scenarios-only --print dev

# debug_explain_missing_selected_file
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id debug_explain_missing_selected_file \
  --scenarios-only --print dev
```

### 5.3 Plan (`capability: plan`)

| `id` | What it tests (short) |
|------|------------------------|
| `plan_pr_merge_shadow` | Synthetic shadow PR-merge `plan_request` → `decision_response.v0.1` with a decision |

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id plan_pr_merge_shadow \
  --scenarios-only --print dev
```

### 5.4 Code (`capability: code`)

| `id` | What it tests (short) |
|------|------------------------|
| `code_echo_probe` | Governed execute: `echo motadata-execute-probe` expects `EXECUTED` / `executed: true` |

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id code_echo_probe \
  --scenarios-only --print dev
```

**Plan-Gate host vs workspace host:** `POST /v0/execute` resolves `repo_root` on the **Plan-Gate** machine. If that host does not have the same path as `MOTADATA_REPO_ROOT` (typical when Context Layer runs on WSL and Plan-Gate on a tunneled GPU), `code_echo_probe` can return **`BLOCKED`** even though other scenarios pass. Set a path that exists on the Plan-Gate host:

```bash
export MOTADATA_VERIFY_EXECUTE_REPO_ROOT="/path/on/plan-gate-host/to/Motadata"
```

Use **`/tmp`** only to confirm sandbox wiring; for production-like checks, point at a real repo root on that host. See [docs/demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md — code_echo_probe / split host](docs/demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md#code-echo-probe-failure).

### 5.5 Agent (`capability: agent`)

| `id` | What it tests (short) |
|------|------------------------|
| `agent_no_route` | `POST /v0/agent` → **404**; Ask response includes **`assist_layer`** |

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id agent_no_route \
  --scenarios-only --print dev
```

---

## 6. Quick manual checklist (curl / IDE)

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

## 7. IDE-oriented narrative (optional)

For **what to click** and demo-style flows (JetBrains-oriented notes), see:

- [docs/demo/JETBRAINS_DEMO_NOTES.md](docs/demo/JETBRAINS_DEMO_NOTES.md)  
- [docs/MOTADATA_DEMOBOOK.md](docs/MOTADATA_DEMOBOOK.md)  
- [docs/MOTADATA_DEMO_SCENARIOS.md](docs/MOTADATA_DEMO_SCENARIOS.md)

---

## 8. Related documents (by role)

| Need | Document |
|------|----------|
| Full GPU + WSL setup, preflight, tunnels | [docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md](docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md) |
| Understand verifier logs and JSON fields | [docs/demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md](docs/demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md) |
| Demo machine topology | [docs/MOTADATA_DEMO_SETUP_RUNBOOK.md](docs/MOTADATA_DEMO_SETUP_RUNBOOK.md) |
| Architecture / layers | [docs/ARCHITECTURE_4_LAYER.md](docs/ARCHITECTURE_4_LAYER.md), [docs/PRODUCT_SLICE.md](docs/PRODUCT_SLICE.md) |
| High-level Q&A (onboarding) | [m_coder_top_150_q_a.md](m_coder_top_150_q_a.md) |

---

## 9. History note

Older drafts pointed operators at a temporary integration guide; that file is archived and redirects to the **production verification guide**. This **User scenarios guide** is the root-level index for **capability coverage**; setup details remain in the production guide above.

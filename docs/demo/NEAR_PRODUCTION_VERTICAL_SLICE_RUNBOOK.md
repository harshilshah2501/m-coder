# Near-Production Vertical Slice Demo Runbook

**Purpose:** One coherent operator-facing demo that proves the governed product story end-to-end: repo-aware intelligence, dangerous-action refusal, safe governed execution, and deterministic evidence with trace/summary/explanation.

**Canonical role:** This is the source of truth for operator-facing end-to-end demo execution.

**Latest inclusions (2026-04):**
- Closure declaration: [../mvp_declaration/GOVERNED_SYSTEM_V1_PRODUCTION_CLOSURE_DECLARATION.md](../mvp_declaration/GOVERNED_SYSTEM_V1_PRODUCTION_CLOSURE_DECLARATION.md)
- Current status authority: [../LIVE_ROADMAP_TRACKER.md](../LIVE_ROADMAP_TRACKER.md)
- Stage 2.5 Assist Layer v1 exists as advisory metadata; runtime Ask authority remains unchanged.

**Scope:** Demo assembly only. No new milestones, no retrieval expansion, no plugin redesign. All capabilities referenced here are already verified on the baseline branch.

---

## 1. Demo purpose

This vertical slice demonstrates:

- **Repo-aware intelligence:** Ask returns a deterministic context bundle from repo docs/code using path/heading/symbol selection (no embeddings, no vector DB). Posture is PLAN_ONLY; nothing is executed.
- **Dangerous action refusal:** A disallowed command (e.g. outbound `curl`) is refused by the guard/Plan-Gate; refusal is ledgered; sandbox does not run.
- **Safe governed execution:** An allowed command (e.g. `echo hello`) passes Plan-Gate, runs in the sandbox, and is ledgered as executed.
- **Deterministic evidence:** Ledger and observation surfaces provide trace, summary, and explanation for auditing and explainability.

---

## 2. Branch / environment baseline

- **Branch:** `integration/m3.12-context-demo`
  - Contains: M3.0–M3.11 (from main), M4.1–M4.6 (from main), M3.12 narrow repo-aware context engine and demo scenarios.
- **References:**  
  - M3.12: [docs/demo/M3_12_CONTEXT_DEMO_RUNBOOK.md](M3_12_CONTEXT_DEMO_RUNBOOK.md), [docs/reports/M3_12_INTEGRATION_VERIFICATION_REPORT.md](../reports/M3_12_INTEGRATION_VERIFICATION_REPORT.md)  
  - M4.x / observation: [docs/reports/M4X_INTEGRATION_VERIFICATION_REPORT.md](../reports/M4X_INTEGRATION_VERIFICATION_REPORT.md)  
  - Governed execution: `runtime/sandbox/demo_governed_execution.py`, [docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md](../runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md)  
  - E2E: [docs/runtime/verification/SYSTEM_E2E_VALIDATION.md](../runtime/verification/SYSTEM_E2E_VALIDATION.md)

**Assumptions:**

- Repo root is the working directory (contains `runtime/`, `docs/`, `jetbrains-plugin/`).
- Plan-Gate service is used for ask (and optionally execute) when demonstrating via HTTP; for CLI-only flow, Python is used to call handlers and demo modules directly.
- Plugin is optional; the runbook can be executed CLI-only or with Plan-Gate + plugin for ask/commit flows.

---

## 3. Demo prerequisites

| Prerequisite | Check |
|--------------|--------|
| Branch | `git branch --show-current` → `integration/m3.12-context-demo` |
| Python 3.9+ | `python3 --version` |
| Repo root | Current directory contains `runtime/`, `docs/` |
| (Optional) Plan-Gate for ask/execute | `python3 -m runtime.plan_gate_service.app` then `curl http://127.0.0.1:8089/healthz` → `{"status":"ok"}` |
| (Optional) Plugin for UI demo | From `jetbrains-plugin/`: `./gradlew runIde`; open m-coder in sandbox |

**Pre-check commands:**

```bash
git checkout integration/m3.12-context-demo
python3 -m pytest runtime/tests/test_m312_demo_scenarios.py -v --tb=no -q
# Expect: 7 passed
```

---

## 4. Demo sequence overview

Execute in order:

1. **Repo-aware ask** — Show PLAN_ONLY ask with deterministic context bundle and provenance.
2. **Dangerous action refusal** — Show that a disallowed command is refused and ledgered; no sandbox execution.
3. **Safe governed execution** — Show that an allowed command is approved, runs in sandbox, and is ledgered.
4. **Trace / summary / explanation** — Show ledger-based summary and (optionally) request trace or explanation from observation surfaces.

---

## 5. Scenario detail for each step

### Step 1 — Repo-aware ask

**Purpose:** Prove repo-aware context selection and PLAN_ONLY posture with no execution.

**Operator action:** Run one deterministic ask scenario (e.g. "How does context selection work?") via Plan-Gate `/v0/ask` or via Python `handle_ask_request`.

**Example request (POST body to `/v0/ask` or dict to `handle_ask_request`):**

```json
{
  "schema_version": "ask_request.v0.1",
  "request_id": "vertical-slice-ask-1",
  "timestamp_utc": "2026-03-15T12:00:00Z",
  "repo_root": "<REPO_ROOT_ABSPATH>",
  "revision": "HEAD",
  "query": "How does context selection work?"
}
```

Replace `<REPO_ROOT_ABSPATH>` with the repository root (e.g. output of `pwd` at repo root).

**Expected visible behavior:**

- Response has `schema_version`: `"plan_only_response.v0.1"`, `governance_posture`: `"PLAN_ONLY"`, `execution`: `false`.
- `context_bundle.files` is an array; each element has `path` and `selection_reason`.
- `plan_summary.steps` is an array of 3–6 steps. Optionally `plan_summary.notes` includes "Repo-aware selection: N file(s) by ...".

**Pass/fail:** Response is valid plan_only_response.v0.1; posture is PLAN_ONLY; execution is false; at least one of the three runbook ask scenarios returns a non-empty context bundle and (when manifest path is used) repo-aware notes.

---

### Step 2 — Dangerous action refusal

**Purpose:** Prove that a dangerous or disallowed action is refused and recorded; sandbox does not run.

**Operator action:** Run the governed execution demo, which includes a refusal case (e.g. `curl` outbound).

**Command:**

```bash
python3 -m runtime.sandbox.demo_governed_execution
```

**Expected visible behavior:**

- Console output includes a line like: `REFUSE (curl): <ledger_row_id> <reason>`.
- Summary JSON includes `"blocked"` with `outcome_type` "refused" and a `ledger_row_id`.
- No sandbox execution for the refused command.

**Evidence:** Refusal produces a ledger row; the demo prints the ledger path and row count (e.g. "Ledger path: /tmp/... rows: 6").

**Pass/fail:** Demo exits 0; output shows REFUSE (curl) with a ledger_row_id; blocked case is present in summary.

---

### Step 3 — Safe governed execution

**Purpose:** Prove that an allowed command is approved, runs in the sandbox, and is ledgered.

**Operator action:** Same demo as Step 2; it runs both refusal and execution cases.

**Expected visible behavior:**

- Console output includes: `SAFE_EXECUTE → EXECUTED: <ledger_row_id>`.
- Summary includes `"executed"` with `outcome_type` "executed", `success` true, and `ledger_row_id`.
- Ledger row count includes both decision and execution rows.

**Pass/fail:** Demo shows EXECUTED with a ledger_row_id; summary.executed.success is true; ledger has multiple rows.

**Note:** The demo uses a temporary ledger by default. **Note the "Ledger path:" line** from the output for Step 4 (e.g. `/tmp/tmpXXXX.db`).

---

### Step 4 — Trace / summary / explanation

**Purpose:** Prove that ledger evidence can be turned into aggregate summary and (optionally) request-level trace/explanation.

**Operator action:** Using the ledger path from Step 2/3 (or a saved ledger from the demo), run the M4.x runtime summary CLI.

**Command:**

```bash
python3 -m runtime.observation.report_runtime_summary --ledger-path <LEDGER_PATH> --summary
```

If the demo used a temp file that was deleted, run the governed execution demo again and pass a known path so the ledger persists:

```bash
python3 -c "
from pathlib import Path
from runtime.sandbox.demo_governed_execution import run_all_cases
p = Path('/tmp/vertical_slice_demo.db')
run_all_cases(ledger_path=p)
print('Ledger:', p)
"
python3 -m runtime.observation.report_runtime_summary --ledger-path /tmp/vertical_slice_demo.db --summary
```

**Expected visible behavior:**

- Summary output shows totals, posture distribution, and (if supported) refusal reasons or backend distribution.
- Exit code 0. No execution; read-only over ledger.

**Optional:** For a single request trace:

```bash
python3 -m runtime.observation.report_runtime_summary --ledger-path <LEDGER_PATH> --request-id demo-executed
```

**Pass/fail:** Summary command exits 0 and prints aggregate statistics from the ledger; optional request-id trace shows rows for that request.

---

## 6. Evidence checklist

For the full vertical slice, the operator should confirm:

| # | Evidence | Where to see it |
|---|----------|------------------|
| 1 | Selected context bundle and provenance (ask) | Step 1 response: `context_bundle.files`, `context_bundle.selectors_used`, optional `plan_summary.notes` |
| 2 | PLAN_ONLY posture for ask | Step 1: `governance_posture` "PLAN_ONLY", `execution` false |
| 3 | Refusal posture and reason | Step 2: demo output "REFUSE (curl)" and summary.blocked.reason |
| 4 | safe_execute posture for governed execution | Step 3: demo output "SAFE_EXECUTE → EXECUTED" |
| 5 | Sandbox result | Step 3: summary.executed.success true, ledger_row_id present |
| 6 | Ledger row(s) | Step 2/3: demo prints ledger path and row count; Step 4 uses same ledger |
| 7 | Trace / summary / explanation artifact | Step 4: report_runtime_summary --summary output (and optionally --request-id trace) |

---

## 7. Dry-run guidance

**Before presenting:**

1. **Check branch:** `git branch --show-current` must be `integration/m3.12-context-demo`.
2. **Run M3.12 demo tests:** `python3 -m pytest runtime/tests/test_m312_demo_scenarios.py -v` → 7 passed.
3. **Run governed execution demo once:** `python3 -m runtime.sandbox.demo_governed_execution` → note ledger path; if you need a persistent ledger for Step 4, use the `python3 -c "..."` variant with `/tmp/vertical_slice_demo.db`.
4. **Run report_runtime_summary** on that ledger → exit 0 and readable summary.

**Acceptable:** Temp ledger path differs between runs; exact row IDs differ; plan_summary.steps wording may vary. **Not acceptable:** Ask returning execution true; refusal case not refusing; executed case not producing a ledger row; report_runtime_summary failing on the demo ledger.

**If a precondition fails:** Fix branch, Python path, or repo root; re-run pre-checks. Do not change contracts or add new features during the demo.

---

## 8. Known non-goals

This demo does **not** claim:

- Broad RAG, semantic retrieval, or vector DB.
- M3.13 Jira or M3.14 PR ingestion.
- Autonomous coding agent or self-modifying code.
- General plugin UX redesign.
- Production rollout or full operational hardening.
- Execution triggered from the ask path (ask remains PLAN_ONLY only).

---

## 9. Operator walkthrough

**Startup order:**

1. Open terminal at repo root. Checkout `integration/m3.12-context-demo`. Run `python3 -m pytest runtime/tests/test_m312_demo_scenarios.py -v -q` → 7 passed.
2. (Optional) Start Plan-Gate: `python3 -m runtime.plan_gate_service.app`. Leave running. Verify: `curl http://127.0.0.1:8089/healthz`.
3. (Optional) For plugin UI: from `jetbrains-plugin/` run `./gradlew runIde`; open m-coder in sandbox.

**Demo order:**

1. **Repo-aware ask** — "We ask the system a question about the repo. It returns a plan-only answer with selected context and reasons—no execution." Show one ask (e.g. via curl to `/v0/ask` or via Python). Point to PLAN_ONLY, context_bundle.files, selection_reason, plan_summary.steps.
2. **Refusal** — "When we try a disallowed action, the runtime refuses it and records the refusal." Run `python3 -m runtime.sandbox.demo_governed_execution`. Point to REFUSE (curl) and the ledger path.
3. **Safe execution** — "When we use an allowed action, it runs in the sandbox and is recorded." Same demo output: point to SAFE_EXECUTE → EXECUTED and the executed ledger row.
4. **Trace/summary** — "We can read back evidence from the ledger: summary and optional trace." Run `report_runtime_summary --ledger-path <path> --summary` (and optionally `--request-id demo-executed`). Show the output.

**Success:** All four steps complete; evidence checklist (§6) is satisfied; no execution from ask path; refusal and execution both ledgered and explainable.

---

*End of Near-Production Vertical Slice Demo Runbook.*

# Plan + Code HTTP runtime gate (observational)

Date: 2026-04-24  
Script: `runtime/scripts/plan_code_http_deploy_gate.py`  
Tests: `runtime/tests/test_plan_code_http_deploy_gate.py`

## Purpose

Provide a **single-command HTTP smoke** against **existing** Plan-Gate surfaces:

- **`POST /v0/plan`** — shadow PR merge + shadow doc update; asserts governed **`decision_response.v0.1`** shape and decision enum.
- **`POST /v0/execute`** — safe echo (coherent `outcome` vs `executed`), destructive `rm` probe (**must** `REFUSED` or `BLOCKED`, **`executed: false`** — some stacks classify the pattern as refusal rather than “blocked by policy”); privileged probe (**must** `REFUSED` or `BLOCKED`).
- **`POST /v1/ask`** — default weak-evidence probe asserts **`plan_only_response.v0.1`**, **`PLAN_ONLY`**, **`execution=false`**, and a **visible plan surface** via at least one of: non-empty **`plan_summary.steps`**, non-empty **`plan_summary.notes`**, or non-empty **`ui.message`** (empty steps alone are allowed when the UI or notes still explain the plan-only outcome).
- **`POST /v1/ask`** with **`response_extensions=["plan_contract.v1"]`**:
  - strong evidence probe: `plan_contract` must be present with `schema_version=plan_contract.v1`
  - weak evidence probe: `plan_contract` may be present; if omitted, `metadata.plan_contract_v1.omission_reason` must be present.

**Does not** assert or require **`plan_contract`** / **`code_reasoning_trace`** on Ask responses (next wiring lane).

## Graph preflight

Same helper as Assist v2 gate: **`--skip-graph-preflight`** for laptops without Neo4j; strict default requires **`COMPLETE`**.

## Workspace / execute

`/v0/execute` uses **`repo_root`** from **`--workspace-root`**. Default: **`MOTADATA_GATE_WORKSPACE_ROOT`** if set, else the **m-coder checkout** root (may be wrong on the Plan-Gate host — set the env var when Plan-Gate runs remotely).

## Optional ledger probe

Pass **`--ledger-path /path/to/file.jsonl`** so the first echo execute includes **`ledger_path`**; when the outcome is **`EXECUTED`**, the gate asserts a non-empty **`decision_ledger_row_id`** (when persistence is enabled on the server).

## Example

```bash
python3 runtime/scripts/plan_code_http_deploy_gate.py \
  --plan-gate-url http://127.0.0.1:8089 \
  --workspace-root "${MOTADATA_GATE_WORKSPACE_ROOT:-$PWD}" \
  --out runtime/.run/plan_code_http_deploy_gate.json
```

Strict graph (default):

```bash
python3 runtime/scripts/plan_code_http_deploy_gate.py \
  --plan-gate-url http://127.0.0.1:8089 \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --out runtime/.run/plan_code_http_deploy_gate.strict.json
```

Local smoke without graph:

```bash
python3 runtime/scripts/plan_code_http_deploy_gate.py \
  --plan-gate-url http://127.0.0.1:8089 \
  --skip-graph-preflight \
  --out runtime/.run/plan_code_http_deploy_gate.local.json
```

Pass criteria: exit code **`0`**, JSON **`"all_pass": true`**, each **`checks.*.pass`** true.

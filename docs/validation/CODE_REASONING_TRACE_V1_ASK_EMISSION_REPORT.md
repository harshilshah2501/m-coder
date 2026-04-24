# Code Reasoning Trace v1 Ask Emission — Slice A/B/C Report

Date: 2026-04-24  
Branch: `code-reasoning-trace-emission-strategy`  
Status: implementation complete on branch; strict WSL artifact collection pending

## What is implemented

- Slice A — Schema + negotiation freeze
  - request extension token supports `code_reasoning_trace.v1`
  - dependency rule enforced: `code_reasoning_trace.v1` requires `plan_contract.v1`
  - response schema allows optional `code_reasoning_trace`
- Slice B — Builder skeleton + omissions
  - deterministic `code_reasoning_trace.v1` builder
  - omission reasons for missing/invalid plan, refusal/insufficient posture, insufficient metadata, invalid generated trace
- Slice C — Paired opt-in emission + gate
  - `/v1/ask` emits trace only on paired opt-in and valid prerequisites
  - trace-only requests are rejected by dependency validation
  - omission diagnostics persisted in metadata when trace is skipped

## Invariants preserved

- `governance_posture = PLAN_ONLY`
- `execution = false`
- no Stage 3 wiring
- no `/v0/execute` behavior changes
- no patch text generation
- no autonomous code loop behavior

## Test status

- Local regression subset: `44 passed`
  - `runtime/tests/test_ask_v1_ingest.py`
  - `runtime/tests/test_plan_code_http_deploy_gate.py`
  - `runtime/tests/test_assist_v2_http_deploy_gate.py`
  - `runtime/tests/test_code_reasoning_trace_builder.py`

## Gate artifact targets

Strict WSL artifact (required for closure):

```bash
python3 runtime/scripts/plan_code_http_deploy_gate.py \
  --plan-gate-url http://127.0.0.1:8089 \
  --out TestRunEvals/plan_code_http_deploy_gate.code_reasoning_trace_optin.wsl.json
```

If local non-WSL runs fail graph preflight due missing neo4j driver, collect the strict artifact on WSL where graph dependencies are available.

## Closure statement

`code_reasoning_trace.v1` paired opt-in emission on `/v1/ask` is complete and gate-validated. Trace emission requires `plan_contract.v1`, default responses remain unchanged, trace-only requests are rejected, omission diagnostics are preserved, and Plan-Only execution invariants remain intact.

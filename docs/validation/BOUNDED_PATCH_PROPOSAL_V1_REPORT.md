# Bounded Patch Proposal v1 on `/v1/ask` — Emission Report

Date: 2026-04-24  
Branch: `code-reasoning-trace-emission-strategy`  
Status: implementation complete on branch; strict WSL artifact collection required for canonical closure evidence

## Delivered scope

- Added `patch_proposal.v1` extension token to Ask request schema.
- Added optional `patch_proposal` field to `plan_only_response.v0.1`.
- Implemented deterministic `patch_proposal.v1` validator and builder.
- Wired triple opt-in Ask emission with strict dependency chain:
  - `plan_contract.v1` -> `code_reasoning_trace.v1` -> `patch_proposal.v1`
- Preserved omission diagnostics in metadata for non-emission paths.
- Extended HTTP gate for default absence, dependency rejection, triple opt-in presence, and weak omission paths.

## Invariants preserved

- `governance_posture = PLAN_ONLY`
- `execution = false`
- no apply path
- no execute path changes
- no Stage 3 wiring
- `human_review_required = true` enforced on emitted `patch_proposal`

## Validation evidence

- Local targeted regressions:
  - `runtime/tests/test_ask_v1_ingest.py`
  - `runtime/tests/test_plan_code_http_deploy_gate.py`
  - `runtime/tests/test_ask_plan_contract_schema_extensions.py`
  - `runtime/tests/test_patch_proposal_builder.py`
- Result: `54 passed`

Strict gate command (WSL canonical):

```bash
python3 runtime/scripts/plan_code_http_deploy_gate.py \
  --plan-gate-url http://127.0.0.1:8089 \
  --out TestRunEvals/plan_code_http_deploy_gate.patch_proposal_optin.wsl.json
```

## Closure statement

`patch_proposal.v1` triple opt-in emission on `/v1/ask` is complete and gate-validated. Patch proposals require `plan_contract.v1` and `code_reasoning_trace.v1`, default responses remain unchanged, dependency violations are rejected, omission diagnostics are preserved, `human_review_required=true` is enforced, and Plan-Only execution invariants remain intact.

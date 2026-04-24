# Plan Contract v1 Ask Emission — Slice 2 Closure Report

Date: 2026-04-24  
Branch: `plan-contract-v1-schema-builder`  
Commit (slice 2 wiring): `f9faacf`  
Status: complete and gate-validated

## Scope closed

- `/v1/ask` reads `response_extensions`
- `plan_contract.v1` is considered only when explicitly requested
- `plan_contract` is attached only when builder returns a truthful valid object
- omission path keeps response unchanged and records diagnostic in metadata
- HTTP gate expanded for default/opt-in/omission behaviors

## Confirmed behavior

- default `/v1/ask` -> no `plan_contract`
- opt-in -> `plan_contract` present when valid
- opt-in + insufficient metadata -> omission diagnostic present
- `PLAN_ONLY` invariant preserved
- `execution=false` invariant preserved
- Assist v2 behavior preserved

## Validation evidence

- Unit/integration tests: `31 passed`
- Strict gate artifact: `TestRunEvals/plan_code_http_deploy_gate.plan_contract_optin.wsl.json`
- No-graph gate artifact: `TestRunEvals/plan_code_http_deploy_gate.plan_contract_optin.wsl.nograph.json`

## Closure statement

`plan_contract.v1` opt-in emission on `/v1/ask` is complete and gate-validated. Default responses remain unchanged, opt-in responses emit only when truthfully generated, omission diagnostics are preserved, and Plan-Only execution invariants remain intact.

## Explicitly not included

- no `code_reasoning_trace` emission
- no Stage 3 integration
- no execute-path changes
- no patch generation/autonomous execution

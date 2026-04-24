# Motadata AIOps Production Verification Guide

Single-source production runbook for verifying Motadata behavior through the governed HTTP stack.

This guide is intentionally split into:

- **Primary path**: what to run for day-to-day verification and release gating.
- **Appendix**: deep diagnostics and manual API drills only when troubleshooting.

## 1) Scope and acceptance

This runbook verifies four capabilities end-to-end:

- `ask` (`POST /v1/export_evidence` + `POST /v1/ask`)
- `debug` (`POST /v1/ask` with `task_type=EXPLAIN_DEBUG`)
- `plan` (`POST /v0/plan`)
- `code` (`POST /v0/execute`)

Acceptance is met when all are true:

- service health checks pass
- graph preflight is `COMPLETE` for scenario acceptance runs
- capability slices pass (`all_pass=true` per slice artifact)
- full scenario regression pass (`scenario_suite.all_pass=true`) when run

## 2) Glossary

- `ask_path=v1_evidence`: Plan-Gate used evidence-first Ask v1 path.
- `PLAN_ONLY`: governance posture where no execution is allowed.
- `EXPLAIN_DEBUG`: debug route on `/v1/ask` with selected-file grounding.
- `selected_file binding`: selected file must remain represented in both explain evidence and context bundle checks.
- `graph preflight COMPLETE`: required ingest counters available and above thresholds.
- `authority owner`: registry-backed primary owner expected to align with indexed workspace paths.

## 3) Environment setup (minimal)

### 3.1 GPU host (Plan-Gate + vLLM)

```bash
export M_CODER_ROOT="$HOME/m-coder"
cd "$M_CODER_ROOT"
cp runtime/config/demo_stack.env.example runtime/config/demo_stack.env
# Edit demo_stack.env and set VLLM_BASE_MODEL
export PYTHONPATH="$M_CODER_ROOT"
./runtime/scripts/governed_services.sh restart
```

Health:

```bash
curl -sS http://127.0.0.1:8089/healthz && echo
curl -sS http://127.0.0.1:8089/version && echo
curl -sS http://127.0.0.1:8000/v1/models | head -c 400 && echo
```

### 3.2 Workspace host (WSL/Linux)

```bash
export M_CODER_ROOT="$HOME/Harshil-PoCs/m-coder"
cd "$M_CODER_ROOT"
export PYTHONPATH="$M_CODER_ROOT"

export MOTADATA_REPO_ROOT="/home/harshil/Projects/Motadata"
export CONTEXT_URL="http://127.0.0.1:8091"
export PLAN_GATE_URL="http://127.0.0.1:8089"

./scripts/wsl_plugin_mvp_stack.sh restart
./scripts/wsl_plugin_mvp_stack.sh check
./scripts/motadata_integration_preflight.sh
```

## 4) Primary verification flow (run in order)

### Step A: hard preflight checks

1) Service health:

```bash
curl -fsS "${CONTEXT_URL}/healthz" >/dev/null
curl -fsS "${PLAN_GATE_URL}/healthz" >/dev/null
curl -fsS http://127.0.0.1:8000/v1/models >/dev/null
```

2) Authority registry/workspace alignment (mandatory integrity check):

```bash
PYTHONPATH="$M_CODER_ROOT" python3 runtime/scripts/lint_authority_registry_paths.py \
  --workspace-root "${MOTADATA_REPO_ROOT}"
```

Expected: exit code `0` and all registry paths resolvable in workspace.
This is an integrity gate, not a retrieval sufficiency metric.

3) Authority code index refresh (mandatory):

```bash
PYTHONPATH="$M_CODER_ROOT" python3 runtime/scripts/build_authority_code_index.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --out "runtime/.cache/authority_code_index.motadata.json"
```

### Step B: graph preflight and ingest completeness

Scenario acceptance requires graph preflight `COMPLETE`.

```bash
./scripts/graph_stack.sh up
./scripts/graph_stack.sh refresh
```

Neo4j reachability checks:

```bash
curl -fsS http://127.0.0.1:7474 >/dev/null
python3 - <<'PY'
import socket
with socket.create_connection(("127.0.0.1", 7687), timeout=3):
    pass
print("neo4j bolt reachable")
PY
```

Threshold counters:

```bash
set -a
source docker/neo4j-graph/.env
set +a
docker exec motadata-graph-neo4j cypher-shell \
  -a bolt://localhost:7687 \
  -u "${GRAPH_NEO4J_USER:-neo4j}" \
  -p "${GRAPH_NEO4J_PASSWORD:-NEO4J_PASSWORD}" \
  "MATCH (s:GraphIngestState {key:'java_ast'}) RETURN s.anchorCountVerticleRegistration AS verticle, s.anchorCountEventbusConsumerRegistration AS eventbusConsumer, s.anchorCountApiRouteRegistration AS apiRoute LIMIT 1;"
```

Required minimums:

- `verticle > 5`
- `eventbusConsumer > 10`
- `apiRoute > 1`

### Step C: capability slices (primary acceptance)

Run each slice separately for precise pass/fail ownership.

Ask slice:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id ask_base_api_class \
  --scenario-id ask_mail_server_configuration \
  --scenario-id ask_config_store_organization \
  --scenario-id ask_api_layer_architecture \
  --scenario-id ask_notification_handlers \
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.ask.deep.json
```

Debug slice:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id debug_availability_correlation_flow \
  --scenario-id debug_mail_config_update_path \
  --scenario-id debug_config_store_null_path \
  --scenario-id debug_snmp_trap_processing \
  --scenario-id debug_missing_selected_file \
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.debug.deep.json
```

Plan slice:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id plan_api_layer_change_shadow \
  --scenario-id plan_mail_config_refactor_shadow \
  --scenario-id plan_config_store_convention_shadow \
  --scenario-id plan_notification_pipeline_shadow \
  --scenario-id plan_dependency_flow_shadow \
  --scenario-id plan_governed_decision_contract_any \
  --scenario-id plan_refusal_or_bounded_approval_safe_patch \
  --scenario-id plan_refusal_or_bounded_approval_doc_update \
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.plan.deep.json
```

**Plan contract v1 (offline fixtures)** — validates `plan_contract.v1` shape and category rules from `PLAN_CONTRACT_FREEZE_V1.md` **without** calling `/v1/ask` (no `plan_contract` in live Ask responses yet). When **only** these `--scenario-id` values are selected, graph preflight may be `UNREACHABLE` and the suite still runs. **Multi-step code reasoning (offline fixtures):** `docs/validation/CODE_REASONING_CONTRACT_DESIGN_V1.md` — run `code_reasoning_trace_validate` rows (no `/v1/ask`); graph optional when **only** these IDs are selected together with `plan_contract_validate` IDs.

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --scenario-id plan_contract_v1_safe_documentation \
  --scenario-id plan_contract_v1_risky_behavior_change \
  --scenario-id plan_contract_v1_insufficient_evidence \
  --scenario-id plan_contract_v1_privileged_destructive_refusal \
  --scenario-id code_reasoning_trace_v1_completed_valid \
  --scenario-id code_reasoning_trace_v1_deferred_insufficient_evidence \
  --scenario-id code_reasoning_trace_v1_refused_forbidden_action \
  --scenario-id code_reasoning_trace_v1_failed_patch_bounds \
  --scenario-id code_reasoning_trace_v1_invalid_step_ordering \
  --scenarios-only \
  --print concise \
  --out TestRunEvals/plan_code_reasoning_offline_validation.wsl.json
```

Plan+Code HTTP/runtime observational gate:

```bash
python3 runtime/scripts/plan_code_http_deploy_gate.py \
  --plan-gate-url "${PLAN_GATE_URL}" \
  --workspace-root "${MOTADATA_GATE_WORKSPACE_ROOT:-${MOTADATA_REPO_ROOT}}" \
  --out TestRunEvals/plan_code_http_deploy_gate.wsl.json
```

`/v1/ask` `plan_contract.v1` opt-in emission gate artifacts (Slice 2):

```bash
python3 runtime/scripts/plan_code_http_deploy_gate.py \
  --plan-gate-url "${PLAN_GATE_URL}" \
  --workspace-root "${MOTADATA_GATE_WORKSPACE_ROOT:-${MOTADATA_REPO_ROOT}}" \
  --out TestRunEvals/plan_code_http_deploy_gate.plan_contract_optin.wsl.json
```

```bash
python3 runtime/scripts/plan_code_http_deploy_gate.py \
  --plan-gate-url "${PLAN_GATE_URL}" \
  --workspace-root "${MOTADATA_GATE_WORKSPACE_ROOT:-${MOTADATA_REPO_ROOT}}" \
  --skip-graph-preflight \
  --out TestRunEvals/plan_code_http_deploy_gate.plan_contract_optin.wsl.nograph.json
```

`/v1/ask` `code_reasoning_trace.v1` paired opt-in emission gate artifact (Slice A/B/C):

```bash
python3 runtime/scripts/plan_code_http_deploy_gate.py \
  --plan-gate-url "${PLAN_GATE_URL}" \
  --workspace-root "${MOTADATA_GATE_WORKSPACE_ROOT:-${MOTADATA_REPO_ROOT}}" \
  --out TestRunEvals/plan_code_http_deploy_gate.code_reasoning_trace_optin.wsl.json
```

`/v1/ask` `patch_proposal.v1` triple opt-in emission gate artifact:

```bash
python3 runtime/scripts/plan_code_http_deploy_gate.py \
  --plan-gate-url "${PLAN_GATE_URL}" \
  --workspace-root "${MOTADATA_GATE_WORKSPACE_ROOT:-${MOTADATA_REPO_ROOT}}" \
  --out TestRunEvals/plan_code_http_deploy_gate.patch_proposal_optin.wsl.json
```

`patch_proposal.v1` quality hardening suite artifact (Q1/Q2):

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios-only \
  --scenarios docs/validation/patch_proposal_quality_scenarios.v1.json \
  --print concise \
  --out TestRunEvals/patch_proposal_quality_validation.q2.wsl.json
```

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --scenario-id plan_contract_v1_safe_documentation \
  --scenario-id plan_contract_v1_risky_behavior_change \
  --scenario-id plan_contract_v1_insufficient_evidence \
  --scenario-id plan_contract_v1_privileged_destructive_refusal \
  --scenarios-only \
  --print concise \
  --out runtime/.run/motadata_behavior_validation.plan_contract_v1.json
```

Code slice:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id code_safe_echo_probe \
  --scenario-id code_safe_pwd_probe \
  --scenario-id code_bounded_multistep_probe \
  --scenario-id code_loop_iteration_observation_probe \
  --scenario-id code_block_rm_probe \
  --scenario-id code_refusal_or_blocked_privileged_probe \
  --scenario-id code_block_git_reset_probe \
  --scenario-id code_block_shutdown_probe \
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.code.deep.json
```

Pass rule per slice:

- artifact `all_pass=true`
- each row has empty `errors`

### Step D: full 20-scenario regression gate

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.20slice.json
```

Pass rule:

- `scenario_suite.all_pass=true`
- `scenario_suite.graph_preflight.state=COMPLETE`

## 5) Contract expectations that changed (must know)

### 5.1 Ask / Answer assembler behavior

- Direct structural answers (for example graph-backed class anchors) must not emit broad generic-trawl next steps.
- Weak evidence still remains truthful; no fabricated certainty.

### 5.2 Debug behavior

- `EXPLAIN_DEBUG` is selected-file anchored and may proceed even if generic quality gate would otherwise block plan-only generation.
- Scenario checks now enforce:
  - selected file/symbol appears in explain evidence (`require_selected_file_in_evidence`)
  - selected file also appears in context bundle paths (`require_selected_file_in_context_bundle`)

### 5.3 Code behavior

- Safe probes allow `outcome_any_of` (`EXECUTED` / `REFUSED` / `BLOCKED`) to support environment policy differences.
- Verifier enforces coherence: `EXECUTED => executed=true`, `REFUSED/BLOCKED => executed=false`.

## 6) Authority alignment checklist (owner file and owner-injected drift)

Use this when artifacts show empty owner fields or low owner-injected signal.

1) Registry path validity:

```bash
PYTHONPATH="$M_CODER_ROOT" python3 runtime/scripts/lint_authority_registry_paths.py \
  --workspace-root "${MOTADATA_REPO_ROOT}"
```

2) Index freshness:

```bash
PYTHONPATH="$M_CODER_ROOT" python3 runtime/scripts/build_authority_code_index.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --out "runtime/.cache/authority_code_index.motadata.json"
```

3) Optional drift proposal report:

```bash
PYTHONPATH="$M_CODER_ROOT" python3 runtime/scripts/propose_authority_registry_drift.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --out runtime/.run/authority_registry_drift_proposal.json
```

4) Re-run relevant Ask scenarios and inspect in output:

- `actual_summary.retrieval_gates.owner_file`
- `actual_summary.retrieval_gates.owner_injected_lane_count`
- `actual_summary.retrieval_metrics.owner_in_top3`

If owner is still empty after these steps, treat as authoritative-data issue (registry concept mapping or workspace mismatch), not as model-only behavior.

## 7) Regression command (single command)

This is the canonical smoke + scenario command for quick status:

```bash
PYTHONPATH="$M_CODER_ROOT" python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --print concise \
  --out runtime/.run/motadata_behavior_validation.json
```

Use `--repeat 2` only when checking stability.

## 8) Troubleshooting

### 8.1 `graph preflight failed` with neo4j driver/import error

The Python process running verifier must have `neo4j` installed. If system Python is externally managed, use your project virtualenv:

```bash
.venv/bin/python -m pip install neo4j
PYTHONPATH="$M_CODER_ROOT" .venv/bin/python runtime/scripts/motadata_behavior_verify.py ...
```

### 8.2 `graph preflight failed` with Bolt connection refused

Neo4j stack is down or unreachable (`127.0.0.1:7687`). Bring up graph stack and verify socket:

```bash
./scripts/graph_stack.sh up
python3 - <<'PY'
import socket
with socket.create_connection(("127.0.0.1", 7687), timeout=3):
    pass
print("neo4j bolt reachable")
PY
```

### 8.3 Graph stack script says docker compose is unavailable

Install either `docker-compose` (v1) or Docker CLI plugin `docker compose` (v2) on the host where `./scripts/graph_stack.sh` runs, then retry:

```bash
./scripts/graph_stack.sh up
./scripts/graph_stack.sh refresh
```

### 8.4 Debug returns `plan_only` unexpectedly

Check request shape:

- `task_type=EXPLAIN_DEBUG`
- `selected_file` present
- `client_context.selection` present

Then inspect verifier output for `routing_mode` and selected-file checks.

### 8.5 Execute probe mismatches

Review:

- `outcome`, `posture`, `executed`
- policy environment assumptions on that host

## 9) Appendix: manual diagnostic commands (non-acceptance)

Use these only when debugging payload-level issues.

### 9.1 Manual Ask CLI

```bash
python3 runtime/scripts/motadata_query_cli.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --query "Which class is the base class for all APIs?" \
  --out /tmp/q4.json
```

### 9.2 Raw Ask/Debug flow

- Export evidence via `POST ${CONTEXT_URL}/v1/export_evidence`
- Build `ask_request.v1.0`
- Call `POST ${PLAN_GATE_URL}/v1/ask`
- For debug add:
  - `task_type=EXPLAIN_DEBUG`
  - `selected_file`
  - `client_context.selection`

### 9.3 Related docs

- `docs/validation/MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md`
- `docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md`
- `docs/validation/POST_CLOSURE_MAINTENANCE.md`
- `docs/ARCHITECTURE_4_LAYER.md`
- `docs/PRODUCT_SLICE.md`

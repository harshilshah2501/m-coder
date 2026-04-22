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

2) Authority registry/workspace alignment (mandatory):

```bash
PYTHONPATH="$M_CODER_ROOT" python3 runtime/scripts/lint_authority_registry_paths.py \
  --workspace-root "${MOTADATA_REPO_ROOT}"
```

Expected: exit code `0` and all registry paths resolvable in workspace.

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
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.plan.deep.json
```

Code slice:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id code_safe_echo_probe \
  --scenario-id code_safe_pwd_probe \
  --scenario-id code_block_rm_probe \
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
# Motadata AIOps Production Verification Guide

Production runbook for proving m-coder behavior against a Motadata workspace.
This is the active guide. Use this for setup, manual verification, and repeatable validation.

**What this guide proves:** system and contract behavior (services up, routes hit, schemas and governance fields as expected, repeatability). It does **not** certify that model answers are *useful* to developers on real engineering tasks. For that second layer, see [Motadata developer utility validation](MOTADATA_DEVELOPER_UTILITY_VALIDATION.md) and `--utility-scenarios` on `motadata_behavior_verify.py`.

**Layering:** Validation here exercises the **HTTP stack** — **Layer-5** (Context Layer `export_evidence`) and **Layer-3** (Plan-Gate Ask/Plan/Execute) — see `docs/ARCHITECTURE_4_LAYER.md` and `docs/PRODUCT_SLICE.md`.

**Team — baseline truth (read before debating retrieval quality):**

- **Closure summary:** `docs/validation/MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md` — what is locked vs follow-on, evidence pointers.
- **Formal baseline record (artifact + m-coder SHA):** `docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5.
- **Post-closure ops checklist:** `docs/validation/POST_CLOSURE_MAINTENANCE.md` (verifier invariants, `CANDIDATE.*` artifacts, no churn by default).
- **Narrative guardrail:** On **current `main`**, Plan-Gate `**POST /v1/ask**` evaluates evidence quality with the same grounding inputs as the layer5 export path. Do **not** treat “broad ask” or “integration owner” scenarios as **always WEAK** from older runs; check §5 and regenerate `motadata_behavior_verify.py` artifacts if unsure.

---

## 1) Scope and success criteria

This guide validates four capabilities end-to-end:

- `ask` (repo understanding via evidence-first Ask)
- `debug` (EXPLAIN_DEBUG path with structured reasoning output)
- `plan` (governed plan decision contract)
- `code` (governed execute contract with mixed EXECUTED/BLOCKED probes)

A verification run is considered successful when:

- all required services are healthy
- all capability checks pass
- repeatability check is stable across repeated runs

---

## 2) Topology and chronology

Topology:

- **GPU host** runs Plan-Gate + vLLM
- **WSL/Linux workspace host** runs Context Layer next to Motadata repo
- SSH tunnel may be required when Plan-Gate/vLLM run on GPU host

Chronology:


| Step | Where | Action                                                |
| ---- | ----- | ----------------------------------------------------- |
| 1    | GPU   | Start governed services (`governed_services.sh`)      |
| 2    | WSL   | Start workspace stack (`wsl_plugin_mvp_stack.sh up`)  |
| 3    | WSL   | Run preflight and behavior verification               |
| 4    | WSL   | Execute objective Ask/Debug/Plan verification runbook |


---

## 3) GPU host setup

```bash
export M_CODER_ROOT="$HOME/m-coder"
cd "$M_CODER_ROOT"
cp runtime/config/demo_stack.env.example runtime/config/demo_stack.env
# Edit demo_stack.env and set VLLM_BASE_MODEL
export PYTHONPATH="$M_CODER_ROOT"
./runtime/scripts/governed_services.sh restart  # THIS IS MORE THAN ENOUGH
./runtime/scripts/governed_services.sh status # NOT NEEDED
```

Quick checks:

```bash
curl -sS http://127.0.0.1:8089/healthz && echo
curl -sS http://127.0.0.1:8089/version && echo
curl -sS http://127.0.0.1:8000/v1/models | head -c 400 && echo
```

Stop:

```bash
./runtime/scripts/governed_services.sh stop # NOT NEEDED, DO WE REALLY NEED TO STOP IT?
```

References:

- `[runtime/config/demo_stack.env.example](../../runtime/config/demo_stack.env.example)`
- `[runtime/scripts/governed_services.sh](../../runtime/scripts/governed_services.sh)`

---

## 4) WSL / workspace host setup

```bash
export M_CODER_ROOT="$HOME/Harshil-PoCs/m-coder"
cd "$M_CODER_ROOT"

export MOTADATA_REPO_ROOT="/home/harshil/Harshil-PoCs/Motadata" # PATH is /root/Harshil-PoCs/Motadata
export CONTEXT_URL="http://127.0.0.1:8091"
export PLAN_GATE_URL="http://127.0.0.1:8089"

# Tunnel to GPU (required when Plan-Gate/vLLM are remote)
export ENABLE_SSH_TUNNEL=1
export GPU_USER="harshil"
export GPU_HOST="45.195.82.10"
export TUNNEL_TARGET="${GPU_USER}@${GPU_HOST}"
# export TUNNEL_SSH_KEY=~/.ssh/id_ed25519

./scripts/wsl_plugin_mvp_stack.sh up # WE SHOULD ONLY RESTART AND CHECK HERE, NO NEED OF UP, STATUS OR DOWN
./scripts/wsl_plugin_mvp_stack.sh check
```

Preflight:

```bash
./scripts/motadata_integration_preflight.sh
# after git pull:
# ./scripts/motadata_integration_preflight.sh --fresh
```

Probe-only mode:

```bash
./scripts/motadata_integration_preflight.sh --verify-only
```

Stack control:

```bash
./scripts/wsl_plugin_mvp_stack.sh status # NOT NEEDED
./scripts/wsl_plugin_mvp_stack.sh restart # ENOUGH
./scripts/wsl_plugin_mvp_stack.sh down # NOT NEEDED
```

### 4.1 WSL quick-run sequence (current proven flow)

Use this exact sequence after pulling latest branch changes:

```bash
cd "$M_CODER_ROOT"
export PYTHONPATH="$M_CODER_ROOT"
export MOTADATA_REPO_ROOT="/root/Harshil-PoCs/Motadata"
```

1. Registry/workspace alignment lint:

```bash
python3 runtime/scripts/lint_authority_registry_paths.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" # IT SHOWS 8 CONCEPTS. ARE THIS SUFFICIENT OR IS THIS EVEN RELEVANT HERE?
```

1. Authority code index refresh (smart auto mode):

```bash
python3 runtime/scripts/build_authority_code_index.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --out "runtime/.cache/authority_code_index.motadata.json"
```

- `refresh-mode=auto` is the default.
- The script chooses full vs incremental refresh automatically and shows a dynamic progress bar.

1. Full scenarios verification + canonical artifact overwrite: # THIS IS A SINGLE COMMAND FOR FULL SCENARIOS VERIFICATION

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.json
```

1. Baseline artifact copy for regression comparisons: ### IS THIS NEEDED? 

```bash
cp runtime/.run/motadata_behavior_validation.json \
  runtime/.run/motadata_behavior_validation.BASELINE.<label>.json
```

**Authority registry vs workspace (recommended before scenario runs):** ### **WHY IS THIS NEEDED?**  
Layer-5 authority resolves concepts from `[runtime/layer5/authority/product_authority_registry.yaml](../../runtime/layer5/authority/product_authority_registry.yaml)`, but retrieval can only inject files that exist in the **indexed** workspace. Run this check against your real Motadata tree so stale or sample paths are caught before `export_evidence` / `motadata_behavior_verify`:

```bash
export PYTHONPATH="$M_CODER_ROOT"
python3 runtime/scripts/lint_authority_registry_paths.py \
  --workspace-root "${MOTADATA_REPO_ROOT}"
```

Exit code `0` means every `primary_owner`, `collaborator`, `forbidden_distractor`, and `entry_point` file path exists as a regular file under `workspace-root`. Non-zero lists missing paths (fix the YAML or your checkout).

Drift proposal command (reference; does not modify registry): ### WHY IS THIS NEEDED?

```bash
export PYTHONPATH="$M_CODER_ROOT"
python3 runtime/scripts/propose_authority_registry_drift.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --out runtime/.run/authority_registry_drift_proposal.json
```

The output report proposes candidate path updates for missing registry entries and class-name mismatch hints. Review manually before changing the registry.

---

## 5) API behavior map (capability to endpoint)


| Capability | Context Layer              | Plan-Gate                                     | vLLM                        | Deterministic expectation                                |
| ---------- | -------------------------- | --------------------------------------------- | --------------------------- | -------------------------------------------------------- |
| Ask        | `POST /v1/export_evidence` | `POST /v1/ask`                                | not required                | `ask_path=v1_evidence`, plan-only posture                |
| Debug      | `POST /v1/export_evidence` | `POST /v1/ask` with `task_type=EXPLAIN_DEBUG` | `POST /v1/chat/completions` | `routing_mode=explain_debug`, structured explain payload |
| Plan       | -                          | `POST /v0/plan`                               | not required                | valid `decision_response.v0.1` with non-empty `decision` |


Plan-Gate routes: `/v0/plan`, `/v0/ask`, `/v1/ask`, `/v0/execute` per `[runtime/plan_gate_service/README.md](../../runtime/plan_gate_service/README.md)`.

---

## 6) Manual verification checklist

### 6.1 Preconditions

```bash
cd "$M_CODER_ROOT"
./runtime/scripts/run_local_stack.sh health
./runtime/scripts/governed_services.sh status
```

Expected:

- Context Layer `:8091` is `OK`
- Plan-Gate `:8089` is `OK`
- vLLM `:8000` is `OK` (required for debug reasoning quality)

### 6.2 Capability matrix


| Requirement | Flow                               | Pass criteria                                                                                             |
| ----------- | ---------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Ask         | `/v1/export_evidence` -> `/v1/ask` | `ask_path=v1_evidence`, `governance_posture=PLAN_ONLY`, `execution=false`, non-empty `plan_summary.steps` |
| Debug       | `/v1/ask` with `EXPLAIN_DEBUG`     | `routing_mode=explain_debug`, `explain_debug.summary` or explicit `explain_debug.error`                   |
| Plan        | `/v0/plan`                         | `schema_version=decision_response.v0.1`, non-empty `decision`                                             |


### 6.3 Reference manual calls (non-acceptance) ### IS SMOKE RUN REALLY NEEDED? 

The JSON scenario suite in section 7 is the acceptance source of truth. This subsection is for ad-hoc diagnostics and is not used for pass/fail sign-off.

**Verifier smoke run (custom Ask + Debug text)**  
One pass exercises the Ask/Debug/Plan flow; you override only the Ask and EXPLAIN_DEBUG strings:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --query "YOUR_REPO_QUESTION_HERE" \
  --debug-query "YOUR_DEBUG_QUESTION_HERE" \
  --top-k 8 \
  --print dev
```

- **Query (Ask):** governed by `--query`. Inspect `plan_summary.steps`, `metadata`, and `context_bundle` in the dev output or `--print json`.
- **Debug:** governed by `--debug-query`. The script sets `task_type=EXPLAIN_DEBUG` and picks `selected_file` from top retrieved evidence path.
- **Plan:** this command uses the verifier’s built-in shadow plan event.

**Raw HTTP (per capability, full payload control)**  
Use when you need custom plan `ide_event` or debug `selected_file` / `client_context.selection`. Set `CONTEXT_URL`, `PLAN_GATE_URL`, and `MOTADATA_REPO_ROOT` as in section 4.


| Capability | What you control                           | Minimal flow                                                                                                                                                                |
| ---------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ask**    | Your natural-language `query`              | `POST ${CONTEXT_URL}/v1/export_evidence` with `workspace_root`, `query`, `top_k` -> build `ask_request.v1.0` with that `evidence_bundle` -> `POST ${PLAN_GATE_URL}/v1/ask`. |
| **Debug**  | `query`, `selected_file`, `selection` text | Same export as Ask -> `POST /v1/ask` with `task_type=EXPLAIN_DEBUG`, `selected_file`, `client_context.selection`, plus `evidence_bundle` / hash fields.                     |
| **Plan**   | `ide_event`, `mode`, policy knobs          | `POST ${PLAN_GATE_URL}/v0/plan` with `plan_request.v0.1` body.                                                                                                              |


Use the verifier command for acceptance. Use raw HTTP only when debugging payload-level behavior.



### 6.3.1 Copy-paste: `run_v1_ask` (manual Ask v1) ### IS THIS REALLY NEEDED? WHEN WE HAVE A SCRIPT??

This is the **single maintained** shell helper for `**POST /v1/export_evidence` → build `ask_request.v1.0` → `POST /v1/ask`**. Other runbooks should **link here** instead of duplicating the block.

**Environment:** `WORKSPACE_ROOT` (Motadata tree), `CONTEXT_URL`, `PLAN_GATE_URL`, `TOP_K` (e.g. `8`). Aligns with section 4.

```bash
run_v1_ask() {
  local query="$1"
  local out_json="$2"

  : "${WORKSPACE_ROOT:?Set WORKSPACE_ROOT (Motadata path)}"
  : "${CONTEXT_URL:?Set CONTEXT_URL}"
  : "${PLAN_GATE_URL:?Set PLAN_GATE_URL}"

  local tmp_dir ev req
  tmp_dir="$(mktemp -d)"
  ev="$tmp_dir/evidence.json"
  req="$tmp_dir/ask_v1.json"

  curl -sS --connect-timeout 5 --max-time 120 -X POST "${CONTEXT_URL}/v1/export_evidence" \
    -H 'Content-Type: application/json' \
    -d "{\"workspace_root\":\"$WORKSPACE_ROOT\",\"query\":\"$query\",\"top_k\":${TOP_K:-8}}" \
    -o "$ev"

  # Fail fast if export did not return a v1 evidence bundle.
  python3 - "$ev" <<'PY'
import json, sys
ev = json.load(open(sys.argv[1], "r", encoding="utf-8"))
if not isinstance(ev, dict) or "provisional" not in ev:
    raise SystemExit(f"export_evidence did not return v1 evidence bundle: {ev}")
PY

  python3 - "$ev" "$req" "$query" <<'PY'
import datetime, json, sys, uuid

ev_path, req_path, query = sys.argv[1], sys.argv[2], sys.argv[3]
ev = json.load(open(ev_path, "r", encoding="utf-8"))
ask = {
    "schema_version": "ask_request.v1.0",
    "request_id": str(uuid.uuid4()),
    "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "query": query,
    "evidence_bundle": ev,
}
h = ev.get("workspace_identity_hash")
if h:
    ask["expected_workspace_identity_hash"] = h
json.dump(ask, open(req_path, "w", encoding="utf-8"), indent=2)
PY

  curl -sS --connect-timeout 5 --max-time 180 -X POST "${PLAN_GATE_URL}/v1/ask" \
    -H 'Content-Type: application/json' --data-binary "@$req" | tee "$out_json"

  rm -rf "$tmp_dir"
}

# Example:
# export TOP_K=8
# run_v1_ask "How does alert correlation work in this repo?" /tmp/ask_out.json
```

**Debug / EXPLAIN_DEBUG:** same export pattern, then `POST /v1/ask` with `task_type`, `selected_file`, and `client_context`; see Plan-Gate docs under `runtime/plan_gate_service/` — do not guess fields.

### 6.3.2 One-command Ask CLI (recommended for manual query testing)

If you want simpler request/response execution than `run_v1_ask` + custom `jq`, use:

```bash
python3 runtime/scripts/motadata_query_cli.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --query "Which class is the base class for all APIs?" \
  --out /tmp/q4.json
```

- Default prints a concise human summary (`request_id`, posture, ask_path, quality, first answer step).
- Add `--print json` to emit full JSON to stdout.
- Keep `--out` for the persisted artifact.
- Deterministic reward labeling (Governed ART-lite): ### WHAT IS THIS GOVERNED ART-lite?

```bash
python3 runtime/scripts/motadata_query_cli.py \ ## WHY TWO DIFFERENT COMMANDS SHOWN FOR 6.3.2 WITH AND WITHOUT REWARD??
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --query "Which class is the base class for all APIs?" \
  --out /tmp/q4.json \
  --with-reward \
  --assist-delta same \
  --reward-out /tmp/q4.reward.json
```

This scores the response into `gold|silver|observational|banned` using phase/evidence/truthfulness/runtime components without changing runtime governance.

### 6.3.3 Governed rollout / rollback gate (model + adapter) ### THIS IS AFTER, MODEL SWAP, WHY IT IS HERE IN MAIN VERIFICATION GUIDE SECTIONS?

Use this section for production promotion decisions after model swap or adapter regeneration.

1. Build Ask-v1 governed SFT pool (`gold/silver` only):

```bash
python3 runtime/scripts/build_governed_sft_dataset.py \
  --inputs "docs/validation/artifacts/plugin_phase1_truth_proof/scenario_*/response.json" \
           "archive/hostB_proof_pack/*/v1_ask_response.json" \
           "/tmp/fresh_ask_v1.json" \
  --out /tmp/governed_sft_events_askv1.jsonl \
  --summary-out /tmp/governed_sft_events_askv1.summary.json
```

1. Compute assist baseline-vs-candidate reward deltas:

```bash
python3 runtime/scripts/assist_reward_delta_report.py \
  --inputs "docs/validation/artifacts/assist_layer_v2_eval/assist_v2_batch_*.json" \
  --out /tmp/assist_v2_reward_deltas.json
```

1. Automated behavior verification (baseline + candidate, same scenario pack):

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --repeat 2 \
  --print concise \
  --out /tmp/behavior_verify.candidate.json
```

Promotion thresholds (all required):

- `governed_sft_events_askv1.summary.json` has `events_after_filter > 0`.
- Behavior verifier: `all_pass == true` and `stable == true`.
- Reward deltas: `delta_negative == 0` and `mean_delta >= 0`.
- No `candidate_hard_violation_counts` entries for:
  - `false_strong_under_low_evidence`
  - `execution_bypass_plan_only`

Rollback triggers (any one):

- Scenario regression (`all_pass == false` on candidate).
- Any hard-violation increase vs baseline.
- Reward report shows `delta_negative > 0` on trusted Ask-v1-aligned eval set.

Important:

- Do not use assist-v2 `plan_only_response.v0.1` envelopes alone as SFT promotion evidence; they may not carry Ask-v1 `evidence_first_meta.ask_path` and will score `missing_ask_path`.
- Promotion decisions must be based on Ask-v1-governed artifacts and scenario verification together.

---

## 7) Automated repeatable verification ### AGAIN AUTOMATED VERIFICATION?? WE ALREADY DID ONCE BEFORE. AS I SAID, WE WANT TO FOCUS ON INDIVIDUAL FUNCTIONALITY TESTING...

Canonical command:

```bash
python3 runtime/scripts/build_authority_code_index.py \
  --workspace-root "/home/harshil/Harshil-PoCs/Motadata" \
  --out "runtime/.cache/authority_code_index.motadata.json"
```

Then run verification:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Harshil-PoCs/Motadata" \
  --repeat 2
```

Stdout modes (`--print`):


| Mode                | Meaning                                                                                                                                                                                    |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `concise` (default) | Short pass/fail plus clipped answer steps, debug summary, and plan outcomes                                                                                                                |
| `plain`             | Readable report for any audience (scenario narratives + no raw `expect` dumps on stdout); see [MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md](../demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md) |
| `dev`               | Full `plan_summary.steps`, `context_bundle.files`, evidence snippet previews for smoke; for scenarios, expanded `expect`/`actual` plus `dev_snapshot` text for **ask** and **debug** rows  |
| `json`              | Full report object on stdout (same shape as `--out`)                                                                                                                                       |


Use full JSON on stdout only when needed:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Harshil-PoCs/Motadata" \
  --repeat 2 \
  --print json
```

Output report (always written):

- `runtime/.run/motadata_behavior_validation.json` (override with `--out`)
- Baseline/candidate naming + diff policy: `docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md`
- Lane closure summary (locked vs follow-on, evidence pointers): `docs/validation/MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md`

Pass criteria:

- `all_pass == true`
- `stable == true` when `--repeat > 1` and smoke runs are included (not `--scenarios-only`)
- If `--scenarios FILE` is set, `scenario_suite.all_pass` must be true as well

### Scenario suite (ask / debug / plan / code) ### AGAIN SCENARIO SUITE, WE ALREADY COVERED IT: WHY SMOKE, AND FULL PIPELINE??

Canonical definitions live in:

- `docs/validation/motadata_aiops_behavior_scenarios.v1.json`

Run smoke plus scenarios (same queries as in section 6.2 / manual examples):

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Harshil-PoCs/Motadata" \
  --repeat 2 \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --print dev
```

Scenarios only (skip the full smoke pipeline; faster when you only need capability checks):

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Harshil-PoCs/Motadata" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenarios-only \
  --print dev
```

Quality policy:

- `docs/validation/motadata_evidence_quality_policy.v1.json` provides scenario-time retrieval gates (for example `require_owner_in_top3`, `min_anchor_hit_rate_top_k`, `max_generic_infra_ratio_top_k`, and Stage A owner lane minimum).
- Disable policy checks with `--quality-policy ""`.

Expected fields per scenario capability (see `expect` in each JSON row; the verifier compares these to live responses):


| Capability | What is exercised                             | Typical `expect` keys                                                                                                                                 | Pass means                                                     |
| ---------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `ask`      | `export_evidence` + `POST /v1/ask`            | `governance_posture`, `execution`, `ask_path`, `min_plan_steps`, `text_contains_any`, `must_cite_file_or_symbol_anchor`, `forbid_generic_scan_answer` | HTTP 200, no expect errors, export returned entries            |
| `debug`    | `POST /v1/ask` with `task_type=EXPLAIN_DEBUG` | `routing_mode`, `explain_debug_has_keys`, `must_have_confidence_limits`, selected-file checks                                                         | HTTP 200, `explain_debug` has `summary` or `error` as required |
| `plan`     | `POST /v0/plan`                               | `schema_version`, `decision_present`, optional `decision_any_of`                                                                                      | HTTP 200, decision contract satisfied                          |
| `code`     | `POST /v0/execute`                            | `schema_version`, `outcome`/`outcome_any_of`, `executed`/`executed_any_of`, optional `posture`                                                        | HTTP 200, execute contract satisfied                           |


The saved JSON report includes `scenario_suite.results[]` with `actual_summary`, `errors`, and `dev_snapshot` (for **ask** and **debug** rows: full steps, bundle files, snippets, or explain-debug text).

The suite is now a balanced 20-scenario contract: 5 Ask + 5 Debug + 5 Plan + 5 Code, designed from `/home/harshil/Projects/Motadata` references and executed against `--workspace-root`.

Critical usage rule:

- Treat the one-shot 20-scenario execution as a **smoke/regression gate**.
- For capability acceptance, run **targeted scenario slices** and validate each capability deeply with real use-cases and their expected/actual contracts.

**Stage A OFF vs ON (A/B):** When diffing two `--out` reports (`--export-stage-a off` vs `on`), compare runs built from the **same** m-coder / context-layer **git SHA** and the same `--workspace-root`. If OFF and ON come from different revisions, you are mixing Stage A toggles with unrelated code changes—use matching artifact labels (e.g. both `*.v2_1_2.json`) only when the stack matches.

### Repo-graph enrichment verification (authoritative flow) ### THIS IS COMPLETETLY LACKS COHERENCE. WHAT DID WE DO SO FAR IF THIS AUTHORITATIVE FLOW?? 

This section is the single objective runbook for the current graph-enrichment stack on `feature/repo-graph-enrichment-v1`.

Functional scope under test in this flow:

- `Ask`
- `Debug`
- `Plan`
- `Code`

`Agent` endpoint semantics are not part of this acceptance slice.

1. **Set workspace and branch context**

```bash
cd ~/Harshil-PoCs/m-coder
git branch --show-current
export MOTADATA_REPO_ROOT="/home/harshil/Harshil-PoCs/Motadata"
export PYTHONPATH="$(pwd)"
```

Expected:

- current branch is `feature/repo-graph-enrichment-v1`
- `${MOTADATA_REPO_ROOT}` exists and is readable
- scenario design references are maintained from `/home/harshil/Projects/Motadata`; runtime execution uses `--workspace-root`

1. **Start graph stack**

```bash
./scripts/graph_stack.sh up
./scripts/graph_stack.sh status
```

1. **Verify service health before running scenarios**

```bash
curl -fsS http://127.0.0.1:8091/healthz >/dev/null
curl -fsS http://127.0.0.1:8089/healthz >/dev/null
curl -fsS http://127.0.0.1:8000/v1/models >/dev/null
```

1. **Verify Neo4j reachability (HTTP + Bolt + auth)** ### SHOULDN'T THIS BE DONE WELL BEFORE?

```bash
curl -fsS http://127.0.0.1:7474 >/dev/null
python3 - <<'PY'
import socket
with socket.create_connection(("127.0.0.1", 7687), timeout=3):
    pass
print("neo4j bolt reachable")
PY
set -a
source docker/neo4j-graph/.env
set +a
docker exec motadata-graph-neo4j cypher-shell \
  -a bolt://localhost:7687 \
  -u "${GRAPH_NEO4J_USER:-neo4j}" \
  -p "${GRAPH_NEO4J_PASSWORD:-NEO4J_PASSWORD}" \
  "RETURN 1;"
```

1. **Refresh graph and verify ingest counters** ### SHOULDN'T THIS BE DONE WELL BEFORE?

```bash
./scripts/graph_stack.sh refresh
docker exec motadata-graph-neo4j cypher-shell \
  -a bolt://localhost:7687 \
  -u "${GRAPH_NEO4J_USER:-neo4j}" \
  -p "${GRAPH_NEO4J_PASSWORD:-NEO4J_PASSWORD}" \
  "MATCH (s:GraphIngestState {key:'java_ast'}) RETURN s.classRecordCount AS classRecordCount, s.anchorCountVerticleRegistration AS verticle, s.anchorCountEventbusConsumerRegistration AS eventbusConsumer, s.anchorCountApiRouteRegistration AS apiRoute, s.workspaceFingerprint AS workspaceFingerprint, s.updatedAt AS updatedAt LIMIT 1;"
```

1. **Enforce preflight thresholds (must pass)**

```bash
docker exec motadata-graph-neo4j cypher-shell \
  -a bolt://localhost:7687 \
  -u "${GRAPH_NEO4J_USER:-neo4j}" \
  -p "${GRAPH_NEO4J_PASSWORD:-NEO4J_PASSWORD}" \
  "MATCH (s:GraphIngestState {key:'java_ast'}) RETURN s.anchorCountVerticleRegistration > 5 AS verticle_ok, s.anchorCountEventbusConsumerRegistration > 10 AS eventbus_consumer_ok, s.anchorCountApiRouteRegistration > 1 AS api_route_ok LIMIT 1;"
```

Required:

- `verticle_ok = true`
- `eventbus_consumer_ok = true`
- `api_route_ok = true`

1. **Run targeted test suite (Lane A/B/C/D contracts)** ### AGAIN TARGETED SUITE? 

```bash
PYTHONPATH="$(pwd)" python3 -m pytest \
  runtime/tests/test_intelligence_schema.py \
  runtime/tests/test_intelligence_loader.py \
  runtime/tests/test_motadata_behavior_verify.py \
  tests/test_query_routing.py \
  tests/test_ast_indexer_lane_b_contracts.py \
  -q --tb=short
```

1. **Run deep capability-focused verification (primary acceptance)** ### IF THIS IS PRIMARY ACCEPTANCE SO WHAT WAS WE DID BEFORE?

Run each capability slice independently so expected vs actual can be reviewed with precision for real use-cases.

8A) Ask deep checks (real repo understanding, anchor quality):

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

8B) Debug deep checks (selected-file binding + concrete failure points):

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

8C) Plan deep checks (decision contract integrity):

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
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.plan.deep.json
```

8D) Code deep checks (mixed governance behavior: EXECUTED + BLOCKED):

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenario-id code_safe_echo_probe \
  --scenario-id code_safe_pwd_probe \
  --scenario-id code_block_rm_probe \
  --scenario-id code_block_git_reset_probe \
  --scenario-id code_block_shutdown_probe \
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.code.deep.json
```

Capability pass conditions (must hold for each deep run artifact):

- `all_pass=true`
- every row has empty `errors`
- each row includes `expect` and capability-specific `actual_summary`
- Ask/Debug rows include `dev_snapshot` for grounded evidence review

1. **Run the full 20-scenario Ask/Debug/Plan/Code suite (smoke/regression only)**

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.20slice.json
```

Smoke pass condition:

- output JSON has `all_pass=true`
- no scenario row contains `errors`
- `graph_preflight.state=COMPLETE`

1. **Run routed Ask acceptance queries**

```bash
python3 runtime/scripts/motadata_query_cli.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --query "Which class is the base class for all APIs?" \
  --out /tmp/t1.json --with-reward --reward-out /tmp/t1.reward.json

python3 runtime/scripts/motadata_query_cli.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --query "How does mail server configuration work?" \
  --out /tmp/t2.json --with-reward --reward-out /tmp/t2.reward.json

python3 runtime/scripts/motadata_query_cli.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --query "What model are you?" \
  --out /tmp/t3.json --with-reward --reward-out /tmp/t3.reward.json
```

1. **Assert routed query artifact outcomes**

```bash
python3 - <<'PY'
import json
from pathlib import Path

t1 = json.loads(Path("/tmp/t1.json").read_text())
t1r = json.loads(Path("/tmp/t1.reward.json").read_text())
t2 = json.loads(Path("/tmp/t2.json").read_text())
t2r = json.loads(Path("/tmp/t2.reward.json").read_text())
t3 = json.loads(Path("/tmp/t3.json").read_text())
t3r = json.loads(Path("/tmp/t3.reward.json").read_text())

reasons_t1 = set((t1.get("metadata") or {}).get("quality_reasons") or [])
assert (t1.get("metadata") or {}).get("evidence_quality") not in {"WEAK", "INSUFFICIENT"}
assert "NO_CORE_IN_TOP3" not in reasons_t1
assert int(t1r.get("total_reward", 0)) > 0
assert t1r.get("eligibility") != "banned"
assert "com.mindarray.api.AbstractAPI" in json.dumps(t1)

reasons_t2 = set((t2.get("metadata") or {}).get("quality_reasons") or [])
assert "HIGH_DISTRACTOR_RATIO" not in reasons_t2
assert "NOISE_DOMINATED" not in reasons_t2
assert "QUERY_TOO_GENERIC" not in reasons_t2
assert int(t2r.get("total_reward", 0)) > 0
assert t2r.get("eligibility") != "banned"

assert int(t3r.get("total_reward", 0)) > 0
assert t3r.get("eligibility") != "banned"
assert not t3r.get("hard_violations")
assert "Motadata Coder" in json.dumps(t3)

print("repo-graph enrichment acceptance: PASS")
PY
```

Final pass condition:

- all commands above succeed
- deep capability artifacts pass:
  - `runtime/.run/motadata_behavior_validation.ask.deep.json`
  - `runtime/.run/motadata_behavior_validation.debug.deep.json`
  - `runtime/.run/motadata_behavior_validation.plan.deep.json`
  - `runtime/.run/motadata_behavior_validation.code.deep.json`
- scenario artifact `runtime/.run/motadata_behavior_validation.20slice.json` reports pass
- routed-query assertion block prints `repo-graph enrichment acceptance: PASS`

---

## 8) Troubleshooting and logs

Primary logs under `runtime/.run/`:

- `wsl_context_layer.log`
- `wsl_plan_gate_tunnel.log`
- `motadata_preflight_*.log`
- `plan_gate.log`
- `vllm.log`
- `motadata_behavior_validation.json`

Quick triage:

1. health endpoints fail -> fix service startup and ports first
2. export evidence fails -> verify `MOTADATA_REPO_ROOT` path visibility on workspace host
3. debug lacks summary and has error -> verify vLLM availability and model readiness
4. execute mismatch -> inspect `/v0/execute` outcome posture and policy assumptions

---

## 9) Related documents

Primer:
- `[docs/guides/MOTADATA_20_SCENARIO_PRIMER.md](./MOTADATA_20_SCENARIO_PRIMER.md)` — capability objectives, scenario selections, criteria, execution patterns, and outcome interpretation for the 20-scenario contract.
- `[docs/guides/MOTADATA_20_SCENARIO_OPERATOR_QUICK_CARD.md](./MOTADATA_20_SCENARIO_OPERATOR_QUICK_CARD.md)` — one-page operator view: scenario IDs, commands, pass checks, and likely failure causes.

| Topic                       | Location                                                                                                     |
| --------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Integration script behavior | `[docs/guides/INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)`                                                 |
| Plugin demo setup           | `[docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md](../runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md)`                   |
| MVP endpoint trace map      | `[docs/First-Production-MVP-Slice.md](../First-Production-MVP-Slice.md)`                                     |
| Truth-proof closure         | `[docs/validation/PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md](../validation/PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md)` |



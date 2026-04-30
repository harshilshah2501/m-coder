# Motadata verification guide
## Table of contents

1. [Overview](#overview)
2. [Quick bootstrap (optional orchestrator)](#single-command-bootstrap-wsl)
3. [Split topology — Primary C + Pass-B fallback](#split-topology--primary-c--pass-b-fallback-wsl--gpu)
4. [Production contract verification](#1-scope-and-acceptance)
5. [Developer utility, evaluation batches, and reports](#developer-utility-usefulness-and-batch-reports)
6. [Canonical manual Ask (`run_v1_ask`)](#canonical-manual-ask-v1)
7. [One-command full suite JSON](#55-one-command-full-suite-json-output)

**Former standalone guides merged here:** `PASS_A_B_C_SETUP_VERIFICATION.md` (legacy filename; Pass-A is retired), `MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md`, `MOTADATA_DEVELOPER_UTILITY_VALIDATION.md` (each now redirects).

---

## Overview

This is the **single** Motadata verification runbook: **setup** (topology, wheel, services), **CLI-first testing** (`mcoder prompt/debug/plan/scenario`), **contract / production checks** (`motadata_behavior_verify` + AIOps scenarios), **split WSL+GPU** procedures (**Primary C** with **Pass-B** graph fallback), **developer utility** scenarios (Ask/Debug/Plan usefulness heuristics including complex tiers), and **batch reports** (`batch_run_developer_eval.py`). Same stack as `docs/ARCHITECTURE_4_LAYER.md`: Context Layer (Layer-5 evidence) → Plan-Gate (Layer-3).

---


## Single Command Bootstrap (WSL)

For production-style WSL bring-up, use the orchestrator script:

```bash
bash scripts/mcoder_wsl_e2e_bootstrap.sh \
  --repo-root /root/Harshil-PoCs/m-coder \
  --motadata-root /root/Harshil-PoCs/Motadata \
  --branch mcoder-cli-ux-contract-v1-audit \
  --verbose
```

What it does (in order):

1. validates prerequisites and inputs
2. checks current git branch
3. runs `git fetch` + `git pull`
4. starts/restarts MVP stack (`wsl_plugin_mvp_stack.sh`)
5. runs integration preflight verification
6. builds authority code index

Useful flags:

- `--dry-run` (print commands without executing)
- `--verbose` (debug trace)
- `--skip-pull`, `--skip-preflight`, `--skip-authority-index`
- `--allow-dirty` (continue even with local changes)

Logs are written to:

```text
runtime/.run/mcoder_wsl_e2e_bootstrap_<UTC>.log
```

---

## Split topology — Primary C + Pass-B fallback (WSL + GPU)

This guide is for your real topology:

- **WSL:** has `Motadata` repo, runs `mcoder` CLI and Context Layer
- **GPU:** has `m-coder` repo, runs Plan-Gate
- **WSL <-> GPU:** connected by SSH tunnel (`127.0.0.1:8089`)

Execution model:

`Repo is truth. Graph is map. LLM is narrator. Runtime is judge.`

- **Primary path:** Pass C runtime verification (CLI-first + verifier suites).
- **Fallback path:** Pass B graph/CIG rebuild+sync only when graph artifacts are stale/missing.

---

## 1) Topology and Where Commands Run

Use this legend in the rest of the guide:

- **[WSL]** run inside WSL shell
- **[GPU]** run on GPU host shell
- **[WSL->GPU]** run from WSL but executes on GPU via `ssh ...`

Do not run `m-coder` source-path commands on WSL if WSL does not have the `m-coder` repo checkout.

---

## 2) Executable Generation and Installation

### 2.1 Build wheel (from m-coder repo)

**[m-coder host]**

```bash
cd ~/Harshil-PoCs/m-coder/packaging/mcoder-suite
python3 -m build --wheel -o dist
ls -1 dist/mcoder_suite-*.whl
```

### 2.2 Install wheel on WSL (CLI runtime env)

Copy wheel from GPU to WSL (example):

**[WSL]**

```bash
mkdir -p ~/tmp/mcoder-wheel
scp harshil@45.195.82.10:~/Harshil-PoCs/m-coder/packaging/mcoder-suite/dist/mcoder_suite-*.whl ~/tmp/mcoder-wheel/
pip install --force-reinstall ~/tmp/mcoder-wheel/mcoder_suite-*.whl
which mcoder
mcoder version
```

### 2.3 Split topology deployment rule (WSL + GPU)

If WSL has Motadata and GPU runs Plan-Gate:

1) Install/reinstall wheel on WSL (CLI/Context side).
2) Use `governed_services.sh` on GPU as the primary deployment/restart path.
3) Do not make ad-hoc GPU `pip install` part of normal verification flow.

### 2.4 GPU governed deployment (primary path)

**[GPU]**

```bash
cd ~/Harshil-PoCs/m-coder
./scripts/governed_services.sh status
./scripts/governed_services.sh restart
```

If your script uses different verbs, run the equivalent status/restart actions.

### 2.5 Break-glass GPU module check (debug only)

Use only for incident debugging (not normal flow):

**[GPU]**

```bash
python3 - <<'PY'
import runtime.ask_service.graph_traversal_payload as m
print("OK:", m.__file__)
PY
```

---

## 3) Service Bring-up (Split)

### 3.1 Context Layer on WSL

**[WSL]**

```bash
mcoder --verbose health --auto-fix
```

Expected: Context Layer health OK.

### 3.2 Plan-Gate on GPU

Ensure Plan-Gate is running via `governed_services.sh` on GPU.

### 3.3 SSH tunnel from WSL

Primary path: let `mcoder` manage tunnel/bootstrap.

**[WSL]**

```bash
mcoder bootstrap
mcoder stack check --json
```

If tunnel is still missing, use manual fallback.

Manual fallback:

**[WSL]** (keep this terminal open):

```bash
ssh -N -L 8089:127.0.0.1:8089 harshil@45.195.82.10
```

In another WSL terminal:

```bash
ss -ltnp | rg 8089
curl -sS -i http://127.0.0.1:8089/healthz
```

Expected:
- listener owned by `ssh`
- `/healthz` returns `200`

### 3.4 Commit parity check (WSL + GPU)

Before runtime acceptance, ensure both sides are on the same m-coder commit.

**[WSL]**

```bash
cd ~/Harshil-PoCs/m-coder
git rev-parse HEAD
```

**[GPU]**

```bash
cd ~/Harshil-PoCs/m-coder
git rev-parse HEAD
```

Expected:
- both hashes are identical for the verification run.

---

## 4) Pass-B fallback: graph/CIG rebuild (only when needed)

Use this section only when graph artifacts are stale/missing or graph preflight is not `COMPLETE`.
Because WSL has Motadata and GPU hosts Plan-Gate, build CIG where Motadata is readable, then sync artifacts to GPU.

### 4.1 Build CIG artifacts from Motadata

If WSL has runtime module available:

**[WSL]**

```bash
python3 -m runtime.scripts.build_code_intelligence_graph \
  --workspace-root /root/Harshil-PoCs/Motadata \
  --out-dir /tmp/code_intelligence_graph
```

If WSL does not have runtime module, run build on host that has both builder code and Motadata access.

### 4.2 Validate artifact set

**[WSL]**

```bash
test -f /tmp/code_intelligence_graph/code_intelligence_graph.v1.jsonl && echo "OK: jsonl"
test -f /tmp/code_intelligence_graph/code_intelligence_graph.v1.manifest.json && echo "OK: manifest"
test -f /tmp/code_intelligence_graph/code_intelligence_graph.v1.adjacency.json && echo "OK: adjacency"
```

### 4.3 Determinism check (same input -> same content_hash)

**[WSL]**

```bash
HASH1=$(python3 - <<'PY'
import json
print(json.load(open("/tmp/code_intelligence_graph/code_intelligence_graph.v1.manifest.json")).get("content_hash",""))
PY
)

python3 -m runtime.scripts.build_code_intelligence_graph \
  --workspace-root /root/Harshil-PoCs/Motadata \
  --out-dir /tmp/code_intelligence_graph >/tmp/cig_rebuild.log

HASH2=$(python3 - <<'PY'
import json
print(json.load(open("/tmp/code_intelligence_graph/code_intelligence_graph.v1.manifest.json")).get("content_hash",""))
PY
)

echo "HASH1=$HASH1"
echo "HASH2=$HASH2"
test "$HASH1" = "$HASH2" && echo "OK: deterministic content_hash"
```

### 4.4 Sync artifacts to GPU Plan-Gate cache

**[WSL]**

```bash
tar -C /tmp -czf /tmp/code_intelligence_graph.tgz code_intelligence_graph
scp /tmp/code_intelligence_graph.tgz harshil@45.195.82.10:/tmp/
ssh harshil@45.195.82.10 '
  mkdir -p ~/Harshil-PoCs/m-coder/runtime/.cache &&
  rm -rf ~/Harshil-PoCs/m-coder/runtime/.cache/code_intelligence_graph &&
  tar -xzf /tmp/code_intelligence_graph.tgz -C ~/Harshil-PoCs/m-coder/runtime/.cache
'
```

### 4.5 Restart Plan-Gate on GPU

Use your existing Plan-Gate service/process restart procedure on GPU.

---

## 5) Pass C Runtime Verification (Real CLI Feel)

### 5.1 Direct probe first (WSL through tunnel)

**[WSL]**

```bash
python3 - <<'PY'
import json, urllib.request, uuid, datetime
CTX="http://127.0.0.1:8091"; ASK="http://127.0.0.1:8089"; WS="/root/Harshil-PoCs/Motadata"
Q="How are config stores organized?"
def post(url, body):
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode())
ev = post(f"{CTX}/v1/export_evidence", {"workspace_root":WS,"query":Q,"top_k":8,"task_type":"general"})
resp = post(f"{ASK}/v1/ask", {"schema_version":"ask_request.v1.0","request_id":str(uuid.uuid4()),"timestamp_utc":datetime.datetime.now(datetime.UTC).isoformat(),"query":Q,"task_type":"general","evidence_bundle":ev})
gt = resp.get("graph_traversal")
ga = (resp.get("metadata") or {}).get("graph_traversal_availability")
aa = resp.get("articulated_answer") if isinstance(resp.get("articulated_answer"), dict) else {}
print("graph_traversal_present:", isinstance(gt, dict))
print("graph_availability:", ga)
print("articulated_answer_schema:", aa.get("schema_version"))
if isinstance(gt, dict):
    print("keys:", sorted(gt.keys()))
    print("flow_paths_count:", len(gt.get("flow_paths") or []))
    print("call_paths_count:", len(gt.get("call_paths") or []))
    print("inheritance_count:", len(gt.get("inheritance") or []))
    print("owners:", gt.get("owners"))
    print("collaborators:", gt.get("collaborators"))
PY
```

Expected:
- `graph_availability` is printed and distinguishes artifact state (`present` / `missing`)
- `articulated_answer_schema: articulated_answer.v0` for general Ask plan-only responses
- `graph_traversal_present` may be `False` when artifacts are missing or traversal has no relevant signal

### 5.2 CLI prompt verification

**[WSL]**

```bash
mcoder prompt "Explain the API layer architecture."
mcoder prompt "How does mail server configuration work?"
mcoder prompt "Find all classes that handle notifications."
mcoder prompt "How are config stores organized?"
```

### 5.3 CLI-first scenario runs (core + complex)

Use CLI runs for fast operator validation before contract gates.

**[WSL]**

```bash
# Core Ask set (20-scenario primer Ask coverage)
mcoder prompt "Which class is the base class for all APIs?"
mcoder prompt "How does mail server configuration work?"
mcoder prompt "How are config stores organized?"
mcoder prompt "Explain the API layer architecture."
mcoder prompt "Find all classes that handle notifications."

# Complex Ask set (developer utility extended tier)
mcoder prompt "Which class is the base class for concrete REST APIs in this codebase?"
mcoder prompt "Explain how HTTP requests enter the product through APIServer and reach concrete handler classes."
mcoder prompt "List main classes involved in sending email or SMS notifications from the server."
mcoder prompt "Plan a safe refactor for alert enrichment with rollback notes and validation checkpoints."
```

Debug and plan CLI checks for complex scenarios:

```bash
mcoder debug --file "motadata/src/main/java/com/mindarray/api/APIServer.java" \
  --query "Why might a newly registered API route not appear at runtime despite a successful start()?"
mcoder debug --file "motadata/src/main/java/com/mindarray/api/MailServerConfiguration.java" \
  --query "What conditions could cause mail delivery settings to appear stale after an admin update?"

mcoder plan "Prepare a phased rollout for alert enrichment changes: feature flag, shadow mode, metrics, rollback procedure, and post-deploy validation."
```

If you maintain text scenario lists, use the built-in CLI scenario runner:

```bash
mcoder scenario --type ask --file path/to/ask_scenarios.txt
mcoder scenario --type debug --file path/to/debug_scenarios.txt
mcoder scenario --type plan --file path/to/plan_scenarios.txt
```

### 5.4 Coverage note: CLI vs verifier

- `mcoder` CLI validates operator behavior and answer quality quickly.
- Full **contract gating** (including execute/code probes and strict expect checks) still uses `motadata_behavior_verify.py`.
- Run both for release-grade validation: CLI-first smoke, then verifier slices/full suites.

### 5.5 One-command full suite (JSON output)

Run the complete suite (contract 20 scenarios + core pytest + utility/prompt batch) and generate a consolidated JSON:

```bash
export MOTADATA_REPO_ROOT="/path/to/Motadata"
bash runtime/scripts/run_motadata_full_suite.sh
```

Primary artifacts:

- `runtime/eval/reports/motadata_contract_20_<UTC>.json`
- `runtime/eval/reports/motadata_pytest_<UTC>.txt`
- `runtime/eval/reports/developer_eval_batch_<UTC>.json`
- `runtime/eval/reports/developer_eval_batch_<UTC>.md`
- `runtime/eval/reports/motadata_full_suite_<UTC>.json` (**single summary file**)

Renderer mode check:

- Default (`MCODER_LEGACY_ASK_RENDERER` unset): unified C-style contract is active for articulated Ask output.
- Debug fallback (`MCODER_LEGACY_ASK_RENDERER=1`): legacy deterministic renderer path is active.
- Governed vLLM narration (optional): set `MCODER_GOVERNED_ASK_NARRATOR=1` on **Plan-Gate** so PLAN_ONLY Ask tries a bounded vLLM narrator before deterministic prose. Uses the same endpoint as Explain/Debug (`MOTADATA_EXPLAIN_VLLM_URL`, `MOTADATA_EXPLAIN_MODEL`). Responses are validated (anchor present, backticks ⊆ allowlist, generic-phrase filter); on failure or timeout, output falls back to the deterministic composer. Response metadata may include `ask_narration_source`: `governed_vllm` vs `deterministic_unified` vs `deterministic_legacy`.

Quick toggle check:

```bash
unset MCODER_LEGACY_ASK_RENDERER
mcoder prompt "Explain the API layer architecture."
MCODER_LEGACY_ASK_RENDERER=1 mcoder prompt "Explain the API layer architecture."
```

Acceptance bar:

- API architecture: includes `APIServer`, `AbstractAPI`, concrete handlers/extensions; not only `APIServer.start`
- Mail config: includes `MailServerConfiguration.beforeUpdate`, lifecycle/store/collaborator flow when present
- Notifications: includes owner + collaborators when graph resolves them
- Config stores: explains `AbstractConfigStore` + read/write/store relationships when present
- Default renderer follows unified C-style constraints: 2-4 concise sentences, flow-oriented explanation; a confidence-limit sentence appears for non-routine `coverage_gaps` or weaker evidence (routine snapshot-only gaps from `reasoning_context` do not append the chain disclaimer)
- C-style unified rendering is the default when `MCODER_LEGACY_ASK_RENDERER` is unset
- If fewer than 2 grounded components are available, output is minimal and truthful (no forced/fake flow)
- CLI verbose mode may print `--- explanation (read-only) ---` before narrative paragraphs; default mode uses the `Explanation` heading
- Fallback `answer_1` / `next_step` output remains valid when narrative block is absent
- A graph-cache note may appear when Plan-Gate reports missing code-intelligence artifacts

---

## 6) CI / Smoke Tests (m-coder repo host)

Run where `m-coder` repo exists:

```bash
cd ~/Harshil-PoCs/m-coder
PYTHONPATH=. pytest -q \
  runtime/tests/test_code_intelligence_graph_smoke.py \
  runtime/tests/test_code_intelligence_graph_v1.py \
  runtime/tests/test_graph_traversal_payload.py \
  runtime/tests/test_ask_v1_ingest.py \
  runtime/tests/test_answer_shaping_pass_a.py \
  runtime/tests/test_articulated_answer.py \
  runtime/tests/test_bounded_ask_narrator.py \
  runtime/tests/test_motadata_20_code_scenarios.py
make cig-smoke
```

---

## 7) Failure Triage

If responses regress to anchor-only phrasing:

1. Verify tunnel and `/healthz` on `127.0.0.1:8089`
2. Verify `graph_traversal_payload.py` exists in GPU runtime
3. Verify CIG artifacts exist in GPU `runtime/.cache/code_intelligence_graph`
4. Verify probe prints `metadata.graph_traversal_availability` and confirm artifact state (`present` / `missing`)
5. If availability is `present`, verify traversal signal (`graph_traversal_present`) and traversal keys for your prompt type
6. Restart GPU Plan-Gate and retry

If fluency/shape unexpectedly regresses:

- PLAN_ONLY Ask prose is composed deterministically in Plan-Gate (`articulated_answer`); it is not vLLM output filtered by plan-gate. Over-cautious tone usually comes from composer rules or `coverage_gaps`, not model censorship.

- Verify `MCODER_LEGACY_ASK_RENDERER` is unset in shell/service environment.
- Re-run one query with and without `MCODER_LEGACY_ASK_RENDERER=1` to confirm default/legacy path split.
- Verify environment drift is not forcing stale behavior:
  - `echo "PYTHONPATH=$PYTHONPATH"`
  - `echo "MCODER_LEGACY_ASK_RENDERER=$MCODER_LEGACY_ASK_RENDERER"`

If `/v1/ask` returns `500`:
- run direct probe script from section 5.1
- collect GPU Plan-Gate traceback/logs at that timestamp

---

## 8) What Was Validated In Sandbox

Validated in this development sandbox:
- CIG build script and tests execute (`cig-smoke`, script unit tests)
- Ask response wiring compiles and tests pass
- guide command syntax verified for local portions

Not executable in this sandbox:
- your remote GPU service management and WSL-to-GPU tunnel environment specifics



---

# Production contract verification

Single-source runbook for the governed HTTP stack (formerly *Motadata AIOps Production Verification Guide*).

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

## 5) Manual HTTP Ask (optional drills)

Use this when you want **your own query text** (not pinned scenario JSON). Same pipeline as the verifier: `POST /v1/export_evidence` → build `ask_request.v1.0` → `POST /v1/ask`.

**Env:** `export WORKSPACE_ROOT` to the Motadata path the Context Layer can read, plus `CONTEXT_URL`, `PLAN_GATE_URL`, and optional `TOP_K` (default `8`).

### 5.1 One-shot: `verify_ask_path.sh`

Three-step checked pipeline (prints compact PASS/WARN). From m-coder repo root:

```bash
export WORKSPACE_ROOT="${MOTADATA_REPO_ROOT:?}"
export QUERY="How does alert correlation work in this repo?"
bash runtime/scripts/verify_ask_path.sh
```

### 5.2 Canonical shell helper: `run_v1_ask`

<a id="canonical-manual-ask-v1"></a>

Paste into your shell (same logic as `verify_ask_path.sh`; writes the full `/v1/ask` JSON response to a file). **`task_type` is omitted** so Plan-Gate treats the Ask as `general` (template planner path unless you extend the function).

```bash
run_v1_ask() {
  local query="${1:?usage: run_v1_ask QUERY [response.json]}"
  local out="${2:-/tmp/ask_v1_response.json}"
  [[ -n "${WORKSPACE_ROOT:-}" ]] || { echo "WORKSPACE_ROOT is required" >&2; return 1; }
  export WORKSPACE_ROOT
  export RUN_V1_ASK_QUERY="$query"
  local ctx="${CONTEXT_URL:-http://127.0.0.1:8091}"
  local gate="${PLAN_GATE_URL:-http://127.0.0.1:8089}"
  local tmp ev req export_body
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  ev="$tmp/evidence.json"
  req="$tmp/ask_v1.json"
  export_body="$tmp/export_evidence.json"
  python3 - <<'PY' > "$export_body"
import json, os
print(json.dumps({
  "workspace_root": os.environ["WORKSPACE_ROOT"],
  "query": os.environ["RUN_V1_ASK_QUERY"],
  "top_k": int(os.environ.get("TOP_K", "8")),
  "task_type": "general",
}))
PY
  local http
  http="$(curl -sS -o "$ev" -w "%{http_code}" \
    -X POST "$ctx/v1/export_evidence" \
    -H 'Content-Type: application/json' \
    --data-binary "@$export_body")"
  if [[ "$http" != "200" ]]; then
    echo "export_evidence HTTP $http" >&2
    cat "$ev" >&2
    return 1
  fi
  python3 - "$ev" "$req" "$query" <<'PY'
import datetime, json, sys, uuid
ev_path, out_path, query = sys.argv[1], sys.argv[2], sys.argv[3]
ev = json.load(open(ev_path, "r", encoding="utf-8"))
_ts = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
body = {
    "schema_version": "ask_request.v1.0",
    "request_id": str(uuid.uuid4()),
    "timestamp_utc": _ts,
    "query": query,
    "evidence_bundle": ev,
}
h = ev.get("workspace_identity_hash")
if h:
    body["expected_workspace_identity_hash"] = h
json.dump(body, open(out_path, "w", encoding="utf-8"))
PY
  http="$(curl -sS -o "$out" -w "%{http_code}" \
    -X POST "$gate/v1/ask" \
    -H 'Content-Type: application/json' \
    --data-binary "@$req")"
  if [[ "$http" != "200" ]]; then
    echo "/v1/ask HTTP $http" >&2
    cat "$out" >&2
    return 1
  fi
  echo "$out"
}
```

For **EXPLAIN_DEBUG**, add `task_type`, `selected_file`, and `client_context` to the JSON body (see **§10** appendix — same raw flow as scenario harness).

## 6) Contract expectations that changed (must know)

### 6.1 Ask / Answer assembler behavior

- Direct structural answers (for example graph-backed class anchors) must not emit broad generic-trawl next steps.
- Weak evidence still remains truthful; no fabricated certainty.

### 6.2 Debug behavior

- `EXPLAIN_DEBUG` is selected-file anchored and may proceed even if generic quality gate would otherwise block plan-only generation.
- Scenario checks now enforce:
  - selected file/symbol appears in explain evidence (`require_selected_file_in_evidence`)
  - selected file also appears in context bundle paths (`require_selected_file_in_context_bundle`)

### 6.3 Code behavior

- Safe probes allow `outcome_any_of` (`EXECUTED` / `REFUSED` / `BLOCKED`) to support environment policy differences.
- Verifier enforces coherence: `EXECUTED => executed=true`, `REFUSED/BLOCKED => executed=false`.

## 7) Authority alignment checklist (owner file and owner-injected drift)

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

## 8) Regression command (single command)

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

## 9) Troubleshooting

### 9.1 `graph preflight failed` with neo4j driver/import error

The Python process running verifier must have `neo4j` installed. If system Python is externally managed, use your project virtualenv:

```bash
.venv/bin/python -m pip install neo4j
PYTHONPATH="$M_CODER_ROOT" .venv/bin/python runtime/scripts/motadata_behavior_verify.py ...
```

### 9.2 `graph preflight failed` with Bolt connection refused

Neo4j stack is down or unreachable (`127.0.0.1:7687`). Bring up graph stack and verify socket:

```bash
# same graph bring-up as Step B
./scripts/graph_stack.sh up
python3 - <<'PY'
import socket
with socket.create_connection(("127.0.0.1", 7687), timeout=3):
    pass
print("neo4j bolt reachable")
PY
```

### 9.3 Graph stack script says docker compose is unavailable

Install either `docker-compose` (v1) or Docker CLI plugin `docker compose` (v2) on the host where `./scripts/graph_stack.sh` runs, then retry:

```bash
# repeat Step B graph bring-up/refresh
./scripts/graph_stack.sh up && ./scripts/graph_stack.sh refresh
```

### 9.4 Debug returns `plan_only` unexpectedly

Check request shape:

- `task_type=EXPLAIN_DEBUG`
- `selected_file` present
- `client_context.selection` present

Then inspect verifier output for `routing_mode` and selected-file checks.

### 9.5 Execute probe mismatches

Review:

- `outcome`, `posture`, `executed`
- policy environment assumptions on that host

## 10) Appendix: manual diagnostic commands (non-acceptance)

Use these only when debugging payload-level issues.

### 10.1 Manual Ask CLI

```bash
python3 runtime/scripts/motadata_query_cli.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --query "Which class is the base class for all APIs?" \
  --out /tmp/q4.json
```

### 10.2 Raw Ask/Debug flow

- Export evidence via `POST ${CONTEXT_URL}/v1/export_evidence`
- Build `ask_request.v1.0`
- Call `POST ${PLAN_GATE_URL}/v1/ask`
- For debug add:
  - `task_type=EXPLAIN_DEBUG`
  - `selected_file`
  - `client_context.selection`

### 10.3 Related docs

- `docs/validation/MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md`
- `docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md`
- `docs/validation/POST_CLOSURE_MAINTENANCE.md`
- `docs/ARCHITECTURE_4_LAYER.md`
- `docs/PRODUCT_SLICE.md`


---

# Developer utility, usefulness, and batch reports

Heuristic checks beyond transport correctness (formerly *Motadata developer utility validation*).

## Scenario tiers

### Core (v1 baseline)

The original four scenarios cover anchored ask, broad ask honesty, anchored debug, and bounded plan.

### Extended / complex (same file)

Additional scenarios stress **multi-hop Ask**, **planning-style Ask** (still `PLAN_ONLY`), **second debug anchor** (APIServer + mail config), and **second plan** (phased rollout + rollback language). They are intended for **better evaluation** of narration and grounding before tightening gates.

| id | capability | What it stresses |
|----|------------|------------------|
| `ask_structural_api_base_class` | ask | Structural / inheritance wording (`AbstractAPI`) |
| `ask_architecture_api_entrypoints` | ask | Multi-component architecture (APIServer → handlers) |
| `ask_discovery_notification_handlers` | ask | Discovery / list-style answers (notifications) |
| `ask_planning_refactor_alert_pipeline` | ask | Planning-framed question; allows WEAK evidence + honesty |
| `debug_apiserver_route_registration` | debug | Route / `start()` failure modes with **APIServer.java** anchor |
| `debug_mail_tls_config_path` | debug | Mail **MailServerConfiguration.java** lifecycle / staleness |
| `plan_phased_rollout_rollback_alert_enrichment` | plan | Rollout / rollback / validation vocabulary in `/v0/plan` response |

**Paths** in JSON use example roots (`/home/harshil/Projects/Motadata`). Override with `--workspace-root` when running the verifier so evidence resolves against your checkout.

## What is *not* claimed

- **Stage 3 loop** (or any multi-step product agent) end-to-end usefulness on real traffic is **not** treated as closed by this track.
- Utility assertions are **approximate**: they use text matching, path overlap, and simple counts. Tune scenarios when the model or retrieval stack shifts.
- **Plan** scenarios depend on Plan-Gate `/v0/plan` behavior; stubs may return sparse JSON—failures often mean **tighten prompts/stub**, not only retrieval.

## Scenario file and verifier

- Scenarios: [docs/validation/motadata_developer_utility_scenarios.v1.json](../validation/motadata_developer_utility_scenarios.v1.json)
- Verifier: `runtime/scripts/motadata_behavior_verify.py`
- JSON report key: `developer_utility_suite` (alongside `scenario_suite` for contract scenarios).

### CLI-first utility check (same scenario intent)

Use this when you want operator-facing output quality checks before JSON gates:

```bash
mcoder prompt "Which class is the primary implementation owner for alert correlation logic?"
mcoder prompt "How does alert correlation and enrichment work?"
mcoder debug --file "motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java" \
  --query "Why might incident enrichment be skipped in alert correlation flow?"
mcoder plan "Prepare a bounded plan to add debug logging around alert correlation skip cases without changing behavior."

# Extended / complex utility probes
mcoder prompt "Which class is the base class for concrete REST APIs in this codebase?"
mcoder prompt "Explain how HTTP requests enter the product through APIServer and reach concrete handler classes."
mcoder prompt "List main classes involved in sending email or SMS notifications from the server."
mcoder prompt "Plan a safe refactor for alert enrichment with rollback notes and validation checkpoints."
mcoder debug --file "motadata/src/main/java/com/mindarray/api/APIServer.java" \
  --query "Why might a newly registered API route not appear at runtime despite a successful start()?"
mcoder debug --file "motadata/src/main/java/com/mindarray/api/MailServerConfiguration.java" \
  --query "What conditions could cause mail delivery settings to appear stale after an admin update?"
mcoder plan "Prepare a phased rollout for alert enrichment changes: feature flag, shadow mode, metrics, rollback procedure, and post-deploy validation. Reference correlation and notification paths."
```

Then run the verifier/batch commands below for pass/fail artifacts.

### Utility-only (behavior verify)

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/path/to/Motadata" \
  --utility-scenarios docs/validation/motadata_developer_utility_scenarios.v1.json \
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.json
```

### One-shot batch: utility suite + prompt batch + reports

Runs **(1)** the full developer utility suite (all Ask / Debug / Plan scenarios above) and **(2)** the fast `mcoder prompt` four-query batch from [run_mcoder_prompt_batch.py](../../runtime/eval/run_mcoder_prompt_batch.py). Writes a **merged JSON** and a **Markdown summary** under `runtime/eval/reports/`.

```bash
export MOTADATA_GATE_WORKSPACE_ROOT="/path/to/Motadata"
# Optional if not localhost defaults:
# export MCODER_CONTEXT_URL=http://127.0.0.1:8091
# export MCODER_PLAN_GATE_URL=http://127.0.0.1:8089

python3 runtime/eval/batch_run_developer_eval.py \
  --workspace-root "$MOTADATA_GATE_WORKSPACE_ROOT" \
  --timeout-sec 600
```

Options:

| Flag | Meaning |
|------|---------|
| `--skip-prompt-batch` | Only run `motadata_behavior_verify` utility scenarios (no `mcoder` CLI batch). |
| `--utility-scenarios PATH` | Alternate scenario JSON (default: `docs/validation/motadata_developer_utility_scenarios.v1.json`). |
| `--reports-dir DIR` | Output directory (default: `runtime/eval/reports/`). |

**Artifacts produced** (timestamp in filename):

- `runtime/eval/reports/behavior_verify_utility_<UTC>.json` — raw `--out` from behavior verify.
- `runtime/eval/reports/developer_eval_batch_<UTC>.json` — merged report (verify subprocess + optional prompt batch + summary).
- `runtime/eval/reports/developer_eval_batch_<UTC>.md` — human-readable pass/fail summary by capability.
- `runtime/eval/mcoder_prompt_batch_report.json` — overwritten each prompt-batch run (when not skipped).

The prompt batch requires `workspace/.mcoder/venv/bin/mcoder` installed for that workspace; if missing, the batch continues and records **skipped** in the merged JSON.

### Contract + utility (full smoke)

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/path/to/Motadata" \
  --repeat 2 \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --utility-scenarios docs/validation/motadata_developer_utility_scenarios.v1.json \
  --print dev
```

### Full scenario coverage checklist (including complex additions)

- Contract 20 scenarios (Ask/Debug/Plan/Code): `docs/validation/motadata_aiops_behavior_scenarios.v1.json` (see `MOTADATA_20_SCENARIO_PRIMER.md`).
- Utility core + extended complex scenarios: `docs/validation/motadata_developer_utility_scenarios.v1.json`.
- Recommended order:
  1. `mcoder` CLI smoke and complex probes (`prompt` / `debug` / `plan`) for quick qualitative checks.
  2. `motadata_behavior_verify.py` contract slices + full 20-scenario gate.
  3. `batch_run_developer_eval.py` for merged utility + prompt-batch reports.

## Evaluation / narration backlog

For golden prompts, rubrics, and banned diagnostic phrasing in user-visible prose, see [BACKLOG_NARRATION_CIG_HOSTING.md](BACKLOG_NARRATION_CIG_HOSTING.md) and [P0_ASK_NARRATION_AUDIT.md](P0_ASK_NARRATION_AUDIT.md). Utility batch reports complement—not replace—that narration QA.

## Keeping the suite maintainable

- Prefer **anchored** questions and **explicit** file paths in Debug scenarios so failures are diagnosable.
- Keep the suite **small number of high-signal** rows; add new scenarios when you discover recurring regression patterns.
- After changing Plan-Gate or Context Layer contracts, re-run the **batch** and archive `developer_eval_batch_*.json` for comparison.

# Motadata AIOps Production Verification Guide

Production runbook for proving m-coder behavior against a Motadata workspace.
This is the active guide. Use this for setup, manual verification, and repeatable validation.

**What this guide proves:** system and contract behavior (services up, routes hit, schemas and governance fields as expected, repeatability). It does **not** certify that model answers are *useful* to developers on real engineering tasks. For that second layer, see [Motadata developer utility validation](MOTADATA_DEVELOPER_UTILITY_VALIDATION.md) and `--utility-scenarios` on `motadata_behavior_verify.py`.

**Layering:** Validation here exercises the **HTTP stack** — **Layer-5** (Context Layer `export_evidence`) and **Layer-3** (Plan-Gate Ask/Plan/Execute) — see `docs/ARCHITECTURE_4_LAYER.md` and `docs/PRODUCT_SLICE.md`.

---

## 1) Scope and success criteria

This guide validates five capabilities end-to-end:

- `query` (repo understanding via evidence-first Ask)
- `debug` (EXPLAIN_DEBUG path with structured reasoning output)
- `plan` (governed plan decision contract)
- `code` (governed execute contract)
- `agent` (governed ask/execute behavior; no separate public `/v0/agent` route)

A verification run is considered successful when:

- all required services are healthy
- all capability checks pass
- repeatability check is stable across repeated runs

---

## 2) Topology and chronology

Topology:

- **GPU host** runs Plan-Gate + vLLM
- **WSL/Linux workspace host** runs Context Layer next to Motadata repo
- optional SSH tunnel exposes Plan-Gate/vLLM locally to WSL

Chronology:


| Step | Where    | Action                                                                  |
| ---- | -------- | ----------------------------------------------------------------------- |
| 1    | GPU      | Start governed services (`governed_services.sh`)                        |
| 2    | WSL      | Start workspace stack (`wsl_plugin_mvp_stack.sh up`)                    |
| 3    | WSL      | Run preflight and behavior verification                                 |
| 4    | Optional | JetBrains plugin setup (separate from this no-plugin verification path) |


---

## 3) GPU host setup

```bash
export M_CODER_ROOT="$HOME/m-coder"
cd "$M_CODER_ROOT"
cp runtime/config/demo_stack.env.example runtime/config/demo_stack.env
# Edit demo_stack.env and set VLLM_BASE_MODEL
export PYTHONPATH="$M_CODER_ROOT"
./runtime/scripts/governed_services.sh start
./runtime/scripts/governed_services.sh status
```

Quick checks:

```bash
curl -sS http://127.0.0.1:8089/healthz && echo
curl -sS http://127.0.0.1:8089/version && echo
curl -sS http://127.0.0.1:8000/v1/models | head -c 400 && echo
```

Stop:

```bash
./runtime/scripts/governed_services.sh stop
```

References:

- `[runtime/config/demo_stack.env.example](../../runtime/config/demo_stack.env.example)`
- `[runtime/scripts/governed_services.sh](../../runtime/scripts/governed_services.sh)`

---

## 4) WSL / workspace host setup

```bash
export M_CODER_ROOT="$HOME/Harshil-PoCs/m-coder"
cd "$M_CODER_ROOT"

export MOTADATA_REPO_ROOT="/home/harshil/Projects/Motadata"
export CONTEXT_URL="http://127.0.0.1:8091"
export PLAN_GATE_URL="http://127.0.0.1:8089"

# Optional tunnel to GPU
export ENABLE_SSH_TUNNEL=1
export GPU_USER="harshil"
export GPU_HOST="45.195.82.10"
export TUNNEL_TARGET="${GPU_USER}@${GPU_HOST}"
# Optional: export TUNNEL_SSH_KEY=~/.ssh/id_ed25519

./scripts/wsl_plugin_mvp_stack.sh up
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
./scripts/wsl_plugin_mvp_stack.sh status
./scripts/wsl_plugin_mvp_stack.sh restart
./scripts/wsl_plugin_mvp_stack.sh down
```

---

## 5) API behavior map (capability to endpoint)


| Capability | Context Layer                       | Plan-Gate                                     | vLLM                        | Deterministic expectation                                            |
| ---------- | ----------------------------------- | --------------------------------------------- | --------------------------- | -------------------------------------------------------------------- |
| Query      | `POST /v1/export_evidence`          | `POST /v1/ask`                                | optional                    | `ask_path=v1_evidence`, plan-only posture                            |
| Debug      | optional `POST /v1/export_evidence` | `POST /v1/ask` with `task_type=EXPLAIN_DEBUG` | `POST /v1/chat/completions` | `routing_mode=explain_debug`, structured explain payload             |
| Plan       | -                                   | `POST /v0/plan`                               | no                          | valid `decision_response.v0.1` with non-empty `decision`             |
| Code       | -                                   | `POST /v0/execute`                            | no                          | valid `execute_response.v0.1` with explicit `outcome` and `executed` |
| Agent      | optional                            | ask/execute governed spine                    | optional                    | `/v0/agent` absent by design; assist metadata present on Ask         |


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
| Query       | `/v1/export_evidence` -> `/v1/ask` | `ask_path=v1_evidence`, `governance_posture=PLAN_ONLY`, `execution=false`, non-empty `plan_summary.steps` |
| Debug       | `/v1/ask` with `EXPLAIN_DEBUG`     | `routing_mode=explain_debug`, `explain_debug.summary` or explicit `explain_debug.error`                   |
| Plan        | `/v0/plan`                         | `schema_version=decision_response.v0.1`, non-empty `decision`                                             |
| Code        | `/v0/execute`                      | `schema_version=execute_response.v0.1`, non-empty `outcome`, explicit `executed` boolean                  |
| Agent       | probe `/v0/agent`, inspect Ask     | `/v0/agent` returns `404` (expected), Ask includes `assist_layer` metadata                                |


---

## 7) Automated repeatable verification

Canonical command:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Projects/Motadata" \
  --repeat 2
```

Stdout modes (`--print`):

| Mode | Meaning |
| ---- | ------- |
| `concise` (default) | Short pass/fail plus clipped answer steps, debug summary, plan/code outcomes |
| `dev` | Full `plan_summary.steps`, `context_bundle.files`, evidence snippet previews for smoke; for scenarios, expanded `expect`/`actual` plus `dev_snapshot` text for **ask** and **debug** rows |
| `json` | Full report object on stdout (same shape as `--out`) |

Use full JSON on stdout only when needed:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Projects/Motadata" \
  --repeat 2 \
  --print json
```

Output report (always written):

- `runtime/.run/motadata_behavior_validation.json` (override with `--out`)

Pass criteria:

- `all_pass == true`
- `stable == true` when `--repeat > 1` and smoke runs are included (not `--scenarios-only`)
- If `--scenarios FILE` is set, `scenario_suite.all_pass` must be true as well

### Scenario suite (ask / debug / plan / code / agent)

Canonical definitions live in:

- `docs/validation/motadata_aiops_behavior_scenarios.v1.json`

Run smoke plus scenarios (same queries as in section 6.2 / manual examples):

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Projects/Motadata" \
  --repeat 2 \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --print dev
```

Scenarios only (skip the full smoke pipeline; faster when you only need capability checks):

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Projects/Motadata" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --scenarios-only \
  --print dev
```

Expected fields per scenario capability (see `expect` in each JSON row; the verifier compares these to live responses):

| Capability | What is exercised | Typical `expect` keys | Pass means |
| ---------- | ------------------- | ---------------------- | ---------- |
| `ask` | `export_evidence` + `POST /v1/ask` | `governance_posture`, `execution`, `ask_path`, `min_plan_steps`, optional `text_contains_any` | HTTP 200, no expect errors, export returned entries |
| `debug` | `POST /v1/ask` with `task_type=EXPLAIN_DEBUG` | `routing_mode`, `explain_debug_has_keys` | HTTP 200, `explain_debug` has `summary` or `error` as required |
| `plan` | `POST /v0/plan` | `schema_version`, `decision_present` | HTTP 200, decision contract satisfied |
| `code` | `POST /v0/execute` | `schema_version`, `outcome`, `executed` | HTTP 200, execute contract satisfied |
| `agent` | Probe `/v0/agent` + `assist_layer` on ask | `agent_route_404`, `assist_layer_on_ask` | No public agent route; assist metadata on ask |

The saved JSON report includes `scenario_suite.results[]` with `actual_summary`, `errors`, and `dev_snapshot` (for **ask** and **debug** rows: full steps, bundle files, snippets, or explain-debug text).

Useful variants:

```bash
python3 runtime/scripts/motadata_behavior_verify.py --help
```

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Projects/Motadata" \
  --query "How does alert correlation and enrichment work?" \
  --debug-query "Debug why incident enrichment might be skipped" \
  --top-k 8 \
  --repeat 3 \
  --print concise \
  --out runtime/.run/motadata_behavior_validation.motadata.json
```

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


| Topic                       | Location                                                                                                     |
| --------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Integration script behavior | `[docs/guides/INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)`                                                 |
| Plugin demo setup           | `[docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md](../runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md)`                   |
| MVP endpoint trace map      | `[docs/First-Production-MVP-Slice.md](../First-Production-MVP-Slice.md)`                                     |
| Truth-proof closure         | `[docs/validation/PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md](../validation/PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md)` |



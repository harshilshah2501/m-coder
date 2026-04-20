# Motadata AIOps Production Verification Guide

Production runbook for proving m-coder behavior against a Motadata workspace.
This is the active guide. Use this for setup, manual verification, and repeatable validation.

**What this guide proves:** system and contract behavior (services up, routes hit, schemas and governance fields as expected, repeatability). It does **not** certify that model answers are *useful* to developers on real engineering tasks. For that second layer, see [Motadata developer utility validation](MOTADATA_DEVELOPER_UTILITY_VALIDATION.md) and `--utility-scenarios` on `motadata_behavior_verify.py`.

**Layering:** Validation here exercises the **HTTP stack** — **Layer-5** (Context Layer `export_evidence`) and **Layer-3** (Plan-Gate Ask/Plan/Execute) — see `docs/ARCHITECTURE_4_LAYER.md` and `docs/PRODUCT_SLICE.md`.

**Team — baseline truth (read before debating retrieval quality):**

- **Closure summary:** `docs/validation/MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md` — what is locked vs follow-on, evidence pointers.
- **Formal baseline record (artifact + m-coder SHA):** `docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5.
- **Post-closure ops checklist:** `docs/validation/POST_CLOSURE_MAINTENANCE.md` (verifier invariants, `CANDIDATE.*` artifacts, no churn by default).
- **Narrative guardrail:** On **current `main`**, Plan-Gate **`POST /v1/ask`** evaluates evidence quality with the same grounding inputs as the layer5 export path. Do **not** treat “broad ask” or “integration owner” scenarios as **always WEAK** from older runs; check §5 and regenerate `motadata_behavior_verify.py` artifacts if unsure.

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

### 4.1 WSL quick-run sequence (current proven flow)

Use this exact sequence after pulling latest branch changes:

```bash
cd "$M_CODER_ROOT"
export PYTHONPATH="$M_CODER_ROOT"
export MOTADATA_REPO_ROOT="/home/harshil/Projects/Motadata"
```

1) Registry/workspace alignment lint:

```bash
python3 runtime/scripts/lint_authority_registry_paths.py \
  --workspace-root "${MOTADATA_REPO_ROOT}"
```

2) Authority code index refresh (smart auto mode):

```bash
python3 runtime/scripts/build_authority_code_index.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --out "runtime/.cache/authority_code_index.motadata.json"
```

- `refresh-mode=auto` is the default.
- The script chooses full vs incremental refresh automatically and shows a dynamic progress bar.

3) Full scenarios verification + canonical artifact overwrite:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.json
```

4) Optional baseline freeze copy for regression comparisons:

```bash
cp runtime/.run/motadata_behavior_validation.json \
  runtime/.run/motadata_behavior_validation.BASELINE.<label>.json
```

**Authority registry vs workspace (recommended before scenario runs):**  
Layer-5 authority resolves concepts from `[runtime/layer5/authority/product_authority_registry.yaml](../../runtime/layer5/authority/product_authority_registry.yaml)`, but retrieval can only inject files that exist in the **indexed** workspace. Run this check against your real Motadata tree so stale or sample paths are caught before `export_evidence` / `motadata_behavior_verify`:

```bash
export PYTHONPATH="$M_CODER_ROOT"
python3 runtime/scripts/lint_authority_registry_paths.py \
  --workspace-root "${MOTADATA_REPO_ROOT}"
```

Exit code `0` means every `primary_owner`, `collaborator`, `forbidden_distractor`, and `entry_point` file path exists as a regular file under `workspace-root`. Non-zero lists missing paths (fix the YAML or your checkout).

Optional non-destructive drift proposal (suggestions only; no edits):

```bash
export PYTHONPATH="$M_CODER_ROOT"
python3 runtime/scripts/propose_authority_registry_drift.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --out runtime/.run/authority_registry_drift_proposal.json
```

The output report proposes candidate path updates for missing registry entries and class-name mismatch hints. Review manually before changing the registry.

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

### 6.3 Manual testing with your own queries

The JSON scenario suite (section 7) pins **fixed** prompts and expectations for regression. For **interactive** checks with **your** wording, use either the verifier smoke run (fast, one command) or raw HTTP (full control).

**Option A — Verifier smoke run (custom Ask + Debug text only)**  
One pass still exercises **all five** capabilities in order (health, export, ask, explain-debug, plan, execute, agent probe). You only override the **Ask** and **EXPLAIN_DEBUG** strings:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --query "YOUR_REPO_QUESTION_HERE" \
  --debug-query "YOUR_DEBUG_QUESTION_HERE" \
  --top-k 8 \
  --print dev
```

- **Query (Ask):** governed by `--query`. Inspect `plan_summary.steps`, `metadata`, and `context_bundle` in the dev output or `--print json`.
- **Debug:** governed by `--debug-query`. The script sets `task_type=EXPLAIN_DEBUG` and picks **`selected_file` from the top retrieved evidence path** (same as the default smoke behavior). If you need a **specific** Java/Path file for debugging, use Option B for the debug call.
- **Plan / Code:** this command still uses the verifier’s **built-in** shadow plan event and **safe** `echo` execute probe (not customizable via flags). To exercise **your** policy event or **your** command, use Option B for those two calls only.
- **Agent:** there is no separate “agent query”; confirm `assist_layer` on the Ask response above and `404` on `GET/POST` `/v0/agent` (the script does both).

**Option B — Raw HTTP (per capability, full payloads)**  
Use when you need a custom **plan** `ide_event`, **execute** `command`, or **debug** `selected_file` / `client_context.selection`. Set `CONTEXT_URL`, `PLAN_GATE_URL`, and `MOTADATA_REPO_ROOT` as in section 4.

| Capability | What you control | Minimal flow |
| ---------- | ---------------- | ------------ |
| **Ask** | Your natural-language `query` | `POST ${CONTEXT_URL}/v1/export_evidence` with `workspace_root`, `query`, `top_k` → build `ask_request.v1.0` with that `evidence_bundle` → `POST ${PLAN_GATE_URL}/v1/ask`. **Shell helper:** §6.3.1 (`run_v1_ask`). |
| **Debug** | `query`, `selected_file`, `selection` text | Same export as Ask (often same base question) → `POST /v1/ask` with `task_type=EXPLAIN_DEBUG`, `selected_file`, `client_context.selection`, plus `evidence_bundle` / hash fields as in Plan-Gate docs. |
| **Plan** | `ide_event`, `mode`, policy knobs | `POST ${PLAN_GATE_URL}/v0/plan` with `plan_request.v0.1` body (see `[runtime/plan_gate_service/README.md](../../runtime/plan_gate_service/README.md)`). |
| **Code** | `command`, `repo_root` | `POST ${PLAN_GATE_URL}/v0/execute` with `execute_request.v0.1` (use a **non-destructive** command in production-like environments). |
| **Agent** | N/A | `POST ${PLAN_GATE_URL}/v0/agent` → expect **404**; any successful `POST /v1/ask` should still include `assist_layer`-related fields as in your product contract. |

**Combining approaches:** run Option A for a quick end-to-end sanity check with your Ask/Debug wording, then Option B only for the endpoints where you need custom plan/execute/debug shapes.

<a id="canonical-manual-ask-v1"></a>

### 6.3.1 Copy-paste: `run_v1_ask` (manual Ask v1)

This is the **single maintained** shell helper for **`POST /v1/export_evidence` → build `ask_request.v1.0` → `POST /v1/ask`**. Other runbooks should **link here** instead of duplicating the block.

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
- Optional deterministic reward labeling (Governed ART-lite):

```bash
python3 runtime/scripts/motadata_query_cli.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --query "Which class is the base class for all APIs?" \
  --out /tmp/q4.json \
  --with-reward \
  --assist-delta same \
  --reward-out /tmp/q4.reward.json
```

This scores the response into `gold|silver|observational|banned` using phase/evidence/truthfulness/runtime components without changing runtime governance.

### 6.3.3 Governed rollout / rollback gate (model + adapter)

Use this section for production promotion decisions after model swap or adapter regeneration.

1) Build Ask-v1 governed SFT pool (`gold/silver` only):

```bash
python3 runtime/scripts/build_governed_sft_dataset.py \
  --inputs "docs/validation/artifacts/plugin_phase1_truth_proof/scenario_*/response.json" \
           "archive/hostB_proof_pack/*/v1_ask_response.json" \
           "/tmp/fresh_ask_v1.json" \
  --out /tmp/governed_sft_events_askv1.jsonl \
  --summary-out /tmp/governed_sft_events_askv1.summary.json
```

2) Compute assist baseline-vs-candidate reward deltas:

```bash
python3 runtime/scripts/assist_reward_delta_report.py \
  --inputs "docs/validation/artifacts/assist_layer_v2_eval/assist_v2_batch_*.json" \
  --out /tmp/assist_v2_reward_deltas.json
```

3) Automated behavior verification (baseline + candidate, same scenario pack):

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

### 6.3.4 Neo4j Ask-only class-relationship rollout (WSL)

Use this only for Ask-v1 class/inheritance/relationship intents. Debug/Code remain disabled by default.

1) Start Neo4j and set Ask-only feature flags:

```bash
export MOTADATA_NEO4J_URI="bolt://127.0.0.1:7687"
export MOTADATA_NEO4J_USER="neo4j"
export MOTADATA_NEO4J_PASSWORD="<your-password>"
export MOTADATA_NEO4J_ENABLED=1
export MOTADATA_NEO4J_ASK_ENABLED=1
export MOTADATA_NEO4J_DEBUG_ENABLED=0
export MOTADATA_NEO4J_CODE_ENABLED=0
```

2) Build minimal class graph (`Class`, `EXTENDS`, `IMPLEMENTS`) from workspace:

```bash
python3 runtime/scripts/build_neo4j_class_graph.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --source-dir "motadata/src/main/java" \
  --clear-existing
```

3) Validate Ask-v1 output and provenance:

```bash
python3 runtime/scripts/motadata_query_cli.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --query "Which class is the base class for all APIs?" \
  --out /tmp/ask.neo4j.q4.json
```

Expected result shape:

- Response remains `PLAN_ONLY` and `execution=false`.
- `metadata.graph_resolution_meta.schema_version == "graph_resolution_meta.v1"`.
- If graph support is strong, first step should be a direct Neo4j-grounded answer.
- If graph is unavailable/low-confidence, response must still succeed with deterministic fallback.

Immediate rollback (no deploy rollback needed):

```bash
export MOTADATA_NEO4J_ENABLED=0
```

### 6.3.5 Neo4j all-in-one host + index service script

Use this when you want a single command path for hosting Neo4j and keeping the graph fresh.

Default Motadata root is preconfigured as:

- `/home/harshil/Projects/Motadata`

Bootstrap (host Neo4j with restart policy, wait for readiness, full rebuild index, emit env file):

```bash
python3 runtime/scripts/neo4j_ask_stack.py \
  --neo4j-password "<your-password>" \
  bootstrap
```

Optional explicit workspace path (if different):

```bash
python3 runtime/scripts/neo4j_ask_stack.py \
  --workspace-root "/home/harshil/Projects/Motadata" \
  --neo4j-password "<your-password>" \
  bootstrap
```

Refresh index without wiping existing graph:

```bash
python3 runtime/scripts/neo4j_ask_stack.py \
  --neo4j-password "<your-password>" \
  refresh
```

Service lifecycle:

```bash
python3 runtime/scripts/neo4j_ask_stack.py --neo4j-password "<your-password>" status
python3 runtime/scripts/neo4j_ask_stack.py --neo4j-password "<your-password>" up
python3 runtime/scripts/neo4j_ask_stack.py --neo4j-password "<your-password>" down
```

Notes:

- Script writes runtime flags to `runtime/.run/neo4j_ask.env` by default.
- Neo4j container is started with `--restart unless-stopped` for always-on behavior.
- Ask remains `PLAN_ONLY`; Debug/Code Neo4j flags remain disabled by default.
- If `--neo4j-password` and `MOTADATA_NEO4J_PASSWORD` are both missing, the script prompts securely in interactive shells.

### 6.3.6 WSL → GPU Motadata mirror (rsync) + remote Neo4j refresh

Use this when **Plan-Gate + Neo4j run on the GPU server** but the **Motadata git checkout and Context Layer stay on WSL**. The GPU does not need git credentials: WSL (or any host with repo access) pushes a file mirror, then optionally triggers a graph refresh on the GPU.

1) **One-time on GPU:** create mirror directory and ensure Neo4j + `m-coder` paths exist (see §6.3.5).

2) **On WSL (on-demand):** sync Motadata into the GPU mirror and refresh the class graph:

```bash
cd /path/to/m-coder
export MOTADATA_REPO_ROOT="/home/<you>/Projects/Motadata"
export GPU_SYNC_HOST="user@<gpu-host>"
export GPU_MIRROR_ROOT="/data/motadata_mirror"
export MCODER_REMOTE_ROOT="/root/Harshil-PoCs/m-coder"
export REMOTE_REFRESH=1

./runtime/scripts/sync_motadata_mirror_to_gpu.sh
```

`MCODER_REMOTE_ROOT` must be the **real m-coder path on the GPU** (where `runtime/scripts/neo4j_ask_stack.py` lives), e.g. `/root/Harshil-PoCs/m-coder` if that is your layout. It is **not** a WSL path. A wrong value used to make the remote `python3` fall back to `$HOME/runtime/scripts/...` and fail with “No such file”.

3) **Plan-Gate on GPU** must use the same mirror path for indexing:

- `neo4j_ask_stack.py --workspace-root "${GPU_MIRROR_ROOT}"` (already what `REMOTE_REFRESH` runs).

4) **Drift control:** each sync writes `motadata_snapshot.json` at the mirror root with `git_commit` and `synced_at_utc` for auditing.

5) **Cron on WSL** (example every 30 minutes): same exports as above, append logging:

```bash
*/30 * * * * cd /path/to/m-coder && MOTADATA_REPO_ROOT=... GPU_SYNC_HOST=... GPU_MIRROR_ROOT=... MCODER_REMOTE_ROOT=... REMOTE_REFRESH=1 ./runtime/scripts/sync_motadata_mirror_to_gpu.sh >>/tmp/motadata_sync.log 2>&1
```

6) **SSH key:** configure WSL → GPU key-based login (`RSYNC_RSH='ssh -i /path/key'` if not default).

---

## 7) Automated repeatable verification

Canonical command:

```bash
python3 runtime/scripts/build_authority_code_index.py \
  --workspace-root "/home/harshil/Projects/Motadata" \
  --out "runtime/.cache/authority_code_index.motadata.json"
```

Then run verification:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Projects/Motadata" \
  --repeat 2
```

Stdout modes (`--print`):

| Mode | Meaning |
| ---- | ------- |
| `concise` (default) | Short pass/fail plus clipped answer steps, debug summary, plan/code outcomes |
| `plain` | Readable report for any audience (scenario narratives + no raw `expect` dumps on stdout); see [MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md](../demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md) |
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
- Baseline/candidate naming + diff policy: `docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md`
- Lane closure summary (locked vs follow-on, evidence pointers): `docs/validation/MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md`

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
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --print dev
```

Scenarios only (skip the full smoke pipeline; faster when you only need capability checks):

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Projects/Motadata" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenarios-only \
  --print dev
```

Quality policy:

- `docs/validation/motadata_evidence_quality_policy.v1.json` provides scenario-time retrieval gates (for example `require_owner_in_top3`, `min_anchor_hit_rate_top_k`, `max_generic_infra_ratio_top_k`, and Stage A owner lane minimum).
- Disable policy checks with `--quality-policy ""`.

Expected fields per scenario capability (see `expect` in each JSON row; the verifier compares these to live responses):

| Capability | What is exercised | Typical `expect` keys | Pass means |
| ---------- | ------------------- | ---------------------- | ---------- |
| `ask` | `export_evidence` + `POST /v1/ask` | `governance_posture`, `execution`, `ask_path`, `min_plan_steps`, optional `text_contains_any`; optional **anchored-owner gate**: `require_authority_primary_owner`, `require_owner_in_top3`, `require_stage_a_owner_injected_min` | HTTP 200, no expect errors, export returned entries |
| `debug` | `POST /v1/ask` with `task_type=EXPLAIN_DEBUG` | `routing_mode`, `explain_debug_has_keys` | HTTP 200, `explain_debug` has `summary` or `error` as required |
| `plan` | `POST /v0/plan` | `schema_version`, `decision_present` | HTTP 200, decision contract satisfied |
| `code` | `POST /v0/execute` | `schema_version`, `outcome`, `executed` | HTTP 200, execute contract satisfied |
| `agent` | Probe `/v0/agent` + `assist_layer` on ask | `agent_route_404`, `assist_layer_on_ask` | No public agent route; assist metadata on ask |

The saved JSON report includes `scenario_suite.results[]` with `actual_summary`, `errors`, and `dev_snapshot` (for **ask** and **debug** rows: full steps, bundle files, snippets, or explain-debug text).

**Anchored owner gate scenario (`ask_anchor_owner_gate`):** The suite includes a pinned Ask row that asserts Layer-5 behavior on the **real** Motadata tree: `authority_resolution.primary_owner.file` is present, Stage A allocates the `owner_injected` lane, and the owner file appears in the **top-3** `export_evidence` entries. For each run, capture `actual_summary.retrieval_gates.workspace_identity_hash` (and the context-layer build SHA) next to your m-coder revision when you compare reports or file regressions—same rule as Stage A A/B below.

**Stage A OFF vs ON (A/B):** When diffing two `--out` reports (`--export-stage-a off` vs `on`), compare runs built from the **same** m-coder / context-layer **git SHA** and the same `--workspace-root`. If OFF and ON come from different revisions, you are mixing Stage A toggles with unrelated code changes—use matching artifact labels (e.g. both `*.v2_1_2.json`) only when the stack matches.

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



# AIOps MVP — WSL runbook (fixed layout)

## What this validates

- **Workability:** `POST /v1/export_evidence` (Context Layer) and `POST /v1/ask` (Plan-Gate) complete with HTTP 200 and written artifacts under `docs/validation/artifacts/aiops_mvp/`.
- **Reliability:** Same `git` revision of m-coder running in Context Layer and Plan-Gate; same `MOTADATA_ROOT` for every export.

Canonical queries and IDs: `docs/validation/aiops_mvp_scenarios.v1.json`.

---

## One-time files (before any terminal)

1. Copy `runtime/config/demo_stack.env.example` to `runtime/config/demo_stack.env`.
2. Set `VLLM_BASE_MODEL` inside `demo_stack.env` to an **absolute path** to a model directory on the machine that runs `governed_services.sh`.
3. Set `MOTADATA_ROOT` to the **absolute path** to your Motadata git checkout on **WSL** (the indexer reads this tree).

---

## Environment (export in Terminal 3 before verification; Terminal 2 needs `M_CODER_ROOT`, `MOTADATA_ROOT`, `PYTHONPATH`)

Replace the example path with your real Motadata path.

```bash
export M_CODER_ROOT="$HOME/Harshil-PoCs/m-coder"
export MOTADATA_ROOT="/home/youruser/Projects/Motadata"
export CONTEXT_URL="http://127.0.0.1:8091"
export PLAN_GATE_URL="http://127.0.0.1:8089"
```

---

## Three terminals — processes and order

Use **three** terminal windows attached to **the same WSL distro**. Execute **in this order**: Terminal 1 → Terminal 2 → Terminal 3.

| Order | Terminal | Process | Listens |
|-------|----------|---------|---------|
| 1 | **Terminal 1** | `governed_services.sh` → vLLM + Plan-Gate | `:8000` (vLLM), `:8089` (Plan-Gate) |
| 2 | **Terminal 2** | `python3 -m runtime.context_layer_service` | `:8091` |
| 3 | **Terminal 3** | `run_aiops_mvp_scenario_pack.sh` (batch client) | no listen; calls 8091 and 8089 |

Do **not** run the batch script until Terminal 1 and Terminal 2 are both running and Terminal 3’s `curl` checks below succeed.

---

### Terminal 1 — Plan-Gate + vLLM

```bash
cd "$M_CODER_ROOT"
git -C "$M_CODER_ROOT" pull --ff-only
export M_CODER_REPO_ROOT="$M_CODER_ROOT"
export M_CODER_GIT_COMMIT="$(git -C "$M_CODER_ROOT" rev-parse --short HEAD)"
./runtime/scripts/governed_services.sh restart
```

Leave this window open. Wait until the script returns to the shell prompt and the last messages report Plan-Gate and vLLM healthy.

---

### Terminal 2 — Context Layer

```bash
export M_CODER_ROOT="$HOME/Harshil-PoCs/m-coder"
export MOTADATA_ROOT="/home/youruser/Projects/Motadata"
export M_CODER_REPO_ROOT="$M_CODER_ROOT"
export M_CODER_GIT_COMMIT="$(git -C "$M_CODER_ROOT" rev-parse --short HEAD)"
export PYTHONPATH="$M_CODER_ROOT"
cd "$M_CODER_ROOT"
python3 -m runtime.context_layer_service
```

Leave this window open. Log lines for each export appear **in this terminal** (stderr).

---

### Terminal 3 — Checks, then MVP batch

```bash
export M_CODER_ROOT="$HOME/Harshil-PoCs/m-coder"
export MOTADATA_ROOT="/home/youruser/Projects/Motadata"
export CONTEXT_URL="http://127.0.0.1:8091"
export PLAN_GATE_URL="http://127.0.0.1:8089"
export PYTHONPATH="$M_CODER_ROOT"
cd "$M_CODER_ROOT"

curl -fsS "$CONTEXT_URL/version" | python3 -m json.tool
curl -fsS "$PLAN_GATE_URL/version" | python3 -m json.tool
curl -fsS "$CONTEXT_URL/healthz"
curl -fsS "$PLAN_GATE_URL/healthz"
```

`git_commit` in both `/version` JSON bodies must match:

```bash
git -C "$M_CODER_ROOT" rev-parse --short HEAD
```

Run the pack (**stdout** = one result line per scenario; **stderr** = verbose phases):

```bash
export AIOPS_MVP_LIVE_HTTP_TIMEOUT=1200
./scripts/run_aiops_mvp_scenario_pack.sh -v --scenario A1
```

Full pack (all 8 scenarios):

```bash
./scripts/run_aiops_mvp_scenario_pack.sh -v
```

---

## Where output goes

| Output | Exact location |
|--------|----------------|
| Scenario pack **verbose** lines (`-v`) | **stderr** of Terminal 3 only. Not a file. To save: `./scripts/run_aiops_mvp_scenario_pack.sh -v --scenario A1 2> /tmp/aiops_mvp_verbose.stderr.log` |
| Scenario pack **result** lines | **stdout** of Terminal 3: `A1: ok automated=…` |
| Context Layer service log | **stderr** of Terminal 2. Optional file: `export MOTADATA_CONTEXT_LAYER_LOG_PATH=/tmp/context_layer.log` in Terminal 2 before starting the service |
| Plan-Gate file log | `$M_CODER_ROOT/runtime/.run/plan_gate.log` on the machine that ran `governed_services.sh` |
| vLLM file log | `$M_CODER_ROOT/runtime/.run/vllm.log` |
| Launcher snapshot | `$M_CODER_ROOT/runtime/.run/effective_config.env` |
| Per-scenario JSON | `$M_CODER_ROOT/docs/validation/artifacts/aiops_mvp/scenario_<ID>/` |
| Batch summary | `$M_CODER_ROOT/docs/validation/artifacts/aiops_mvp/summary/run_summary.json` |

---

## HTTP bodies (contract)

**`POST /v1/export_evidence`** — JSON fields: `workspace_root` (absolute `MOTADATA_ROOT`), `query`, `top_k` (pack uses **12** from `aiops_mvp_scenarios.v1.json`). Response body is the evidence bundle object.

**`POST /v1/ask`** — Schema `ask_request.v1.0`: `schema_version`, `request_id`, `timestamp_utc`, `query`, `evidence_bundle`, `task_type` (`general` for this pack). Schema file: `runtime/ide/schemas/ask_request.v1.0.schema.json`.

---

## Plan-Gate `metadata` fields to read in `ask_response.json`

| Field | Use |
|-------|-----|
| `evidence_quality` | `STRONG` / `WEAK` / `INSUFFICIENT` / `NO_MATCH` |
| `quality_reasons` | Machine-readable reasons |
| `operator_hints` | Short operator-facing strings |
| `usefulness_metrics` | Bundle-level retrieval stats |

---

## Scenarios (IDs)

| ID | Category |
|----|----------|
| A1 | ASK |
| A2 | ASK |
| D1 | DEBUG |
| D2 | DEBUG |
| P1 | PLAN |
| P2 | PLAN |
| C1 | CODE |
| C2 | CODE |

---

## Rubric (human)

Judge each scenario using `ask_response.json` and evidence paths: grounding, truthfulness, usefulness, weak-evidence honesty. Record `PASS` / `PARTIAL` / `FAIL` in `judgement.txt` beside the artifacts.

---

## Split host (Plan-Gate not on this WSL)

Run Terminal 1 on the Linux host that has the GPU and `demo_stack.env`. On WSL, set `export PLAN_GATE_URL=http://<that-host-LAN-IP>:8089` (or the tunneled URL) in Terminal 3 before `curl` and the batch script. Terminal 2 stays on WSL. Three terminals remain: **remote shell for governed stack**, **WSL Context Layer**, **WSL batch**.

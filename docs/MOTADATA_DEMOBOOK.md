# Motadata Capability Demobook (Definitive)

**Production-style verification (setup, manual HTTP, scenarios):** [docs/guides/MOTADATA_VERIFICATION_GUIDE.md](guides/MOTADATA_VERIFICATION_GUIDE.md) and the thin router [MOTADATA_SIMPLE_PATH.md](../MOTADATA_SIMPLE_PATH.md) — use those when you need one spine instead of demo-only steps.

This demobook is the single execution script for setup and capability testing. It is command-first and aligned to the current governed stack (`governed_services.sh` + Context Layer + Plan-Gate Ask v1).

## 0) What this demobook validates

Capabilities validated end-to-end:

- `query` (Context Layer `export_evidence` + Plan-Gate `POST /v1/ask`)
- `debug` (`POST /v1/ask` with `task_type=EXPLAIN_DEBUG`)
- `plan` (`POST /v0/plan`)
- `code` (`POST /v0/execute`)
- `agent` behavior contract (`/v0/agent` expected `404`, assist metadata on Ask)

Primary verifier: `runtime/scripts/motadata_behavior_verify.py`

## 1) One-time environment setup

Run from repo root:

```bash
export M_CODER_ROOT="$HOME/Harshil-PoCs/m-coder"
cd "$M_CODER_ROOT"
export PYTHONPATH="$M_CODER_ROOT"
```

Workspace host variables:

```bash
export MOTADATA_REPO_ROOT="/home/harshil/Projects/Motadata"
export MOTADATA_ROOT="$MOTADATA_REPO_ROOT"
export CONTEXT_URL="http://127.0.0.1:8091"
export PLAN_GATE_URL="http://127.0.0.1:8089"
```

## 2) Start the stack (canonical path)

### 2.1 GPU host (vLLM + Plan-Gate)

```bash
cd "$M_CODER_ROOT"
cp runtime/config/demo_stack.env.example runtime/config/demo_stack.env
# edit runtime/config/demo_stack.env and set VLLM_BASE_MODEL to a valid local model path
./runtime/scripts/governed_services.sh start
./runtime/scripts/governed_services.sh status
```

### 2.2 WSL/workspace host (Context Layer + optional tunnel)

```bash
cd "$M_CODER_ROOT"
./scripts/wsl_plugin_mvp_stack.sh up
./scripts/wsl_plugin_mvp_stack.sh check
```

Preflight (recommended):

```bash
./scripts/motadata_integration_preflight.sh
```

## 3) Gate checks before any demo

```bash
curl -sS "${PLAN_GATE_URL}/healthz" && echo
curl -sS "${PLAN_GATE_URL}/version" && echo
curl -sS http://127.0.0.1:8000/v1/models | head -c 400 && echo
curl -sS "${CONTEXT_URL}/healthz" && echo
curl -sS "${CONTEXT_URL}/version" && echo
```

Expected:

- Plan-Gate `/healthz` returns `{"status":"ok"}`
- Plan-Gate `/version` includes `ask_request_v1`
- vLLM `/v1/models` returns non-empty model list JSON
- Context Layer `/healthz` returns status `ok`
- Context Layer `/version` includes `layer5.evidence_bundle.v1`

## 4) Capability scenario pack (two-step canonical flow)

Run these in order: first refresh the authority code index for your Motadata workspace, then run the behavior verifier against the pinned scenario suite and quality policy.

### 4.1 Authority code index (`build_authority_code_index.py`)

**What it does:** Builds (or incrementally refreshes) the on-disk authority code index for `MOTADATA_REPO_ROOT`. Layer-5 authority resolution and `export_evidence` retrieval depend on paths and symbols that exist in the indexed workspace; this step keeps the index aligned with the tree you are about to verify.

**When to run:** Before `motadata_behavior_verify.py` when the workspace has changed, or when scenario runs look stale or miss expected owner paths.

```bash
python3 runtime/scripts/build_authority_code_index.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --out "runtime/.cache/authority_code_index.motadata.json"
```

**Output:** `runtime/.cache/authority_code_index.motadata.json` (default `refresh-mode=auto` chooses full vs incremental as appropriate).

### 4.2 Behavior verification (`motadata_behavior_verify.py`)

**What it does:** Exercises the five capabilities end-to-end against live Context Layer and Plan-Gate URLs (`query`, `debug`, `plan`, `code`, `agent`) using the versioned scenario definitions and evidence-quality gates. Writes a full JSON report for regression and sign-off.

**Pass expectation:** Process exits `0`, report has `all_pass: true`, and with `--repeat 2` the run should report stable repeatability when smoke paths are included per verifier rules.

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --repeat 2 \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.json
```

**Output:** `runtime/.run/motadata_behavior_validation.json` (override path with `--out` if needed).

**Pass criteria (summary):**

- verifier exits `0`
- `runtime/.run/motadata_behavior_validation.json` has `all_pass: true`
- when `--repeat 2`, repeatability is stable per the report (see `docs/guides/MOTADATA_VERIFICATION_GUIDE.md` for full pass rules)

**Reading the log and JSON:** With `--print dev`, the first printed `all_pass` line reflects **smoke only**; the JSON file’s top-level `all_pass` combines smoke **and** scenarios. See [`demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md`](demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md) (including [§3.5 — queries and commands from the scenario JSON](demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md#scenario-json-queries)).

## 5) Per-capability command probes (manual demo mode)

### 5.1 Query (evidence-first Ask)

```bash
WORKSPACE_ROOT="${MOTADATA_REPO_ROOT}" \
QUERY="How does alert correlation and enrichment work in this repo?" \
bash runtime/scripts/verify_ask_path.sh
```

### 5.2 Debug (`EXPLAIN_DEBUG`)

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --query "How does alert correlation and enrichment work?" \
  --debug-query "Debug why incident enrichment might be skipped" \
  --top-k 8 \
  --print dev
```

### 5.3 Plan (`/v0/plan`)

```bash
python3 - <<'PY'
import datetime, json, os, urllib.request, uuid

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

workspace_root = os.environ["MOTADATA_REPO_ROOT"]
url = os.environ.get("PLAN_GATE_URL", "http://127.0.0.1:8089").rstrip("/") + "/v0/plan"
payload = {
    "schema_version": "plan_request.v0.1",
    "request_id": str(uuid.uuid4()),
    "timestamp_utc": utc_now(),
    "mode": "shadow",
    "ide_event": {
        "schema_version": "ide_event.v0.1",
        "event_id": "evt-demobook-plan",
        "timestamp_utc": utc_now(),
        "ide_context": {
            "product": "cli",
            "ide": "none",
            "project": "Motadata",
            "repo_root": workspace_root,
            "branch": "main",
            "user": "operator"
        },
        "action": {"action_type": "PR_MERGE", "target": "main"},
        "evidence_refs": [{"type": "note", "ref": "demobook-plan"}]
    },
    "requested_capabilities": ["plan_and_decide"],
    "client_policy": {"fail_closed_if_gate_unreachable": True}
}
req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=120) as resp:
    print(resp.status)
    print(resp.read().decode("utf-8"))
PY
```

Expected: HTTP `200` and response schema `decision_response.v0.1`.

### 5.4 Code (`/v0/execute`, non-destructive)

```bash
python3 - <<'PY'
import json, os, urllib.request, uuid

workspace_root = os.environ["MOTADATA_REPO_ROOT"]
url = os.environ.get("PLAN_GATE_URL", "http://127.0.0.1:8089").rstrip("/") + "/v0/execute"
payload = {
    "schema_version": "execute_request.v0.1",
    "request_id": str(uuid.uuid4()),
    "repo_root": workspace_root,
    "command": "echo motadata-execute-probe"
}
req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=120) as resp:
    print(resp.status)
    print(resp.read().decode("utf-8"))
PY
```

Expected: HTTP `200`, schema `execute_response.v0.1`, and explicit `outcome` + `executed`.

### 5.5 Agent contract check

```bash
curl -sS -o /tmp/agent_probe_body.txt -w "%{http_code}\n" \
  -X POST "${PLAN_GATE_URL}/v0/agent" \
  -H 'Content-Type: application/json' \
  -d '{"request_id":"agent-probe"}'
cat /tmp/agent_probe_body.txt
```

Expected: HTTP `404` by design (no dedicated public `/v0/agent` route).

## 6) Demo artifact capture (mandatory)

After a full run, keep these artifacts:

- `runtime/.run/motadata_behavior_validation.json`
- `runtime/.run/wsl_context_layer.log`
- `runtime/.run/wsl_plan_gate_tunnel.log` (when tunnel is enabled)
- `runtime/.run/plan_gate.log`
- `runtime/.run/vllm.log`

If any capability fails, do not mark the run as complete until the verifier output is regenerated and all checks pass.

## 7) Stop services

WSL side:

```bash
./scripts/wsl_plugin_mvp_stack.sh down
```

GPU side:

```bash
./runtime/scripts/governed_services.sh stop
```


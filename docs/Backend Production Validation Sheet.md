## 1) Backend Production Validation Sheet

**Purpose:** Validate the production core slice **without the JetBrains plugin** — using only `curl`, `python3`, and HTTP to Context Layer, Plan-Gate, and (where needed) vLLM.

**Companion doc:** After this sheet passes, use `docs/JetBrains Plugin Defect Isolation Sheet.md` to compare IDE behavior to the same backends.

**Print as:** 1 preflight page + 6 scenario pages + 1 final summary page (optional).

---

# Motadata AI Coding Assistant — Backend Production Validation Sheet

## How to use this document (read once)

1. **Fill the header** below (date, tester, branch, URLs). Set `WORKSPACE_ROOT` to the **absolute path of the repo on the machine where Context Layer runs** (the path must be valid for `POST /v1/export_evidence`).
2. **Start or confirm services** (see **Services you need**). All `curl` commands assume the process listening on each URL is already up.
3. **Paste the A0 shell block** in a terminal on **the same host** that can reach those URLs (usually the machine where Context Layer and Plan-Gate run — e.g. WSL or native Linux).
4. Run **A1** health checks. If any fail, fix deployment before scenarios B–G.
5. Run scenarios **B → G** in order (or skip optional sections). Each section is **self-contained**; temp files go under `/tmp/`.
6. **Record** Actual / Pass-Fail in the tables; paste short **log excerpts** where indicated.
7. Complete **H. Final Backend Summary**.

### What this proves vs what it does not

| Proves | Does not prove |
|--------|----------------|
| HTTP contracts, JSON shapes, endpoints | JetBrains UI or plugin wiring |
| Context Layer retrieval + evidence bundle | Cross-host IDE `repo_root` unless `WORKSPACE_ROOT` matches the IDE’s project root on this machine |
| Plan-Gate Ask v1/v0 and execute responses | Production auth/TLS (this sheet uses local HTTP) |

### Prerequisites

| Requirement | Notes |
|-------------|--------|
| `curl` and `python3` | On the host where you run this sheet |
| Repo checkout | Same tree Context Layer indexes (`WORKSPACE_ROOT`) |
| Network | `localhost` URLs work from that host |

### Services you need

| Service | Typical start | Default URL |
|---------|---------------|-------------|
| **Context Layer** | e.g. `motadata-context-layer` or `python -m runtime.context_layer_service` from repo (see `packaging/motadata-context-layer/README.md`) | `http://127.0.0.1:8091` |
| **Plan-Gate** | e.g. `python -m runtime.plan_gate_service.app` or via `runtime/scripts/governed_services.sh` | `http://127.0.0.1:8089` |
| **vLLM** | Required for **scenario C (Debug/Explain)** only; often started with `governed_services.sh` | `http://127.0.0.1:8000` |

Plan-Gate may require `MOTADATA_EXPLAIN_VLLM_URL` when Explain/Debug runs; align with your `demo_stack.env` / runbook.

### Where to run the commands

Run the shell blocks on a host that can **`curl` all three URLs**. If Context Layer runs in WSL and you run `curl` from Windows, use the WSL IP or run the sheet **inside WSL** (recommended).

### Artifact files (safe to delete after a run)

| Path | Produced by |
|------|-------------|
| `/tmp/evidence.json`, `/tmp/ask_v1.json`, `/tmp/ask_v1_response.json` | Scenario B |
| `/tmp/evidence_debug.json`, `/tmp/ask_debug_v1.json`, … | Scenario C |
| Similar `/tmp/evidence_*.json`, `/tmp/ask_*.json`, `/tmp/execute_v0.json` | Other scenarios |

### Quick response checks (optional)

If `jq` is installed:

```bash
jq '.governance_posture, .execution, .evidence_first_meta.ask_path' /tmp/ask_v1_response.json
jq '.plan_summary.steps, .plan_summary.notes' /tmp/ask_nomatch_v1_response.json
```

---

**Environment profile:** __________________________  
**Date:** __________________________  
**Tester:** __________________________  
**Branch / commit:** __________________________  
**Workspace root:** __________________________  
**Context Layer URL:** __________________________  
**Plan-Gate URL:** __________________________  
**vLLM URL:** __________________________

> Suggested defaults for this slice:
> - Context Layer: `http://127.0.0.1:8091`
> - Plan-Gate: `http://127.0.0.1:8089`
> - vLLM: `http://127.0.0.1:8000`

## A. Preflight

### A0. One-time shell variables (paste once)

```bash
export CONTEXT_URL="${CONTEXT_URL:-http://127.0.0.1:8091}"
export PLAN_GATE_URL="${PLAN_GATE_URL:-http://127.0.0.1:8089}"
export VLLM_URL="${VLLM_URL:-http://127.0.0.1:8000}"
export WORKSPACE_ROOT="${WORKSPACE_ROOT:-/ABSOLUTE/PATH/TO/REPO}"
export TOP_K="${TOP_K:-8}"
# Default Ask (scenario B) query; override per scenario when re-running other sections
export QUERY="${QUERY:-How does alert correlation work in this repo?}"
```

### A1. Component health

| Component | Command | Expected | Actual | Pass/Fail |
| --- | --- | --- | --- | --- |
| Context Layer | `curl -sS "$CONTEXT_URL/healthz"` | JSON includes `"status":"ok"` and `"service":"motadata_context_layer"` | __________________ | ______ |
| Context Layer | `curl -sS "$CONTEXT_URL/version"` | JSON includes `"evidence_schema_hint":"layer5.evidence_bundle.v1"` and `POST /v1/export_evidence` | __________________ | ______ |
| Plan-Gate | `curl -sS "$PLAN_GATE_URL/healthz"` | JSON includes `"status":"ok"` | __________________ | ______ |
| Plan-Gate | `curl -sS "$PLAN_GATE_URL/version"` | JSON includes `ask_request_v1` in `supported_schemas` | __________________ | ______ |
| vLLM | `curl -sS "$VLLM_URL/v1/models"` | JSON includes served model in `data[].id` | __________________ | ______ |

**If a check fails:** Connection refused → service not running or wrong port. Wrong JSON shape → wrong service or old binary. For Plan-Gate `/version`, confirm `supported_schemas` includes `ask_request_v1` (see `runtime/plan_gate_service/app.py`).

### A2. Logs attached

| Component | Log file / source | Attached? |
| --- | --- | --- |
| Context Layer | `stderr` or `$MOTADATA_CONTEXT_LAYER_LOG_PATH` | Yes / No |
| Plan-Gate | `runtime/.run/plan_gate.log` | Yes / No |
| vLLM | `runtime/.run/vllm.log` | Yes / No |
| Execute/runtime | __________________________ | Yes / No |

### A3. Path proof expectations

| Scenario | Expected endpoint path |
| --- | --- |
| Ask v1 | `/v1/export_evidence` -> `/v1/ask` |
| Debug | `/v1/export_evidence` -> `/v1/ask` -> `/v1/chat/completions` |
| Plan | `/v1/export_evidence` -> `/v1/ask` (or `/v0/plan` only if explicitly testing commit-gate contract) |
| Code | `/v0/execute` |
| No-match | `/v1/export_evidence` -> `/v1/ask` |
| Failure mode | explicit failure surfaced, no fake success |

### A4. Canonical test payloads

Use these exact queries first before custom ones:

- **Ask (evidence-first):** `How does alert correlation work in this repo?`
- **Debug/Explain:** `Explain this function and likely bug risk.`
- **Plan:** `Plan how to add structured request logging in Plan-Gate without changing behavior.`
- **No-match honesty:** `Where is the quantum flux capacitor serializer pipeline?` (intentionally out-of-domain)
- **Code/Execute command:** `echo "production-slice-exec-check"`

---

## B. Scenario Record — Ask (evidence-first)

**Goal:** Validate grounded Ask over the canonical evidence-first path.

**Input query:** `How does alert correlation work in this repo?`  
**top_k:** `8`

### Command sequence

```bash
# Uses QUERY and TOP_K from A0 (defaults match this scenario)
# 1) Export evidence
curl -sS -X POST "$CONTEXT_URL/v1/export_evidence" \
  -H "Content-Type: application/json" \
  -d "{\"workspace_root\":\"$WORKSPACE_ROOT\",\"query\":\"$QUERY\",\"top_k\":$TOP_K}" \
  > /tmp/evidence.json

# 2) Build ask_request.v1.0 from evidence
python3 - <<'PY'
import datetime, json, os, uuid
ev = json.load(open('/tmp/evidence.json', 'r', encoding='utf-8'))
q = os.environ.get("QUERY", "How does alert correlation work in this repo?")
req = {
  "schema_version": "ask_request.v1.0",
  "request_id": str(uuid.uuid4()),
  "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
  "query": q,
  "evidence_bundle": ev,
}
if ev.get("workspace_identity_hash"):
  req["expected_workspace_identity_hash"] = ev["workspace_identity_hash"]
json.dump(req, open('/tmp/ask_v1.json', 'w', encoding='utf-8'))
print("wrote /tmp/ask_v1.json")
PY

# 3) Call /v1/ask
curl -sS -X POST "$PLAN_GATE_URL/v1/ask" \
  -H "Content-Type: application/json" \
  --data-binary "@/tmp/ask_v1.json" \
  > /tmp/ask_v1_response.json
```

### Expected

- Context Layer `POST /v1/export_evidence` returns `schema_hint=layer5.evidence_bundle.v1`
- Plan-Gate `POST /v1/ask` returns `governance_posture=PLAN_ONLY` and `execution=false`
- `evidence_first_meta.ask_path = v1_evidence`
- `evidence_bundle.entries` count > 0 for in-domain query
- `plan_summary.steps` non-empty, or `plan_summary.notes` explicitly states insufficiency
- vLLM not required for standard Ask

### Actual

| Check                                 | Expected | Actual             | Pass/Fail |
| ------------------------------------- | -------- | ------------------ | --------- |
| `/v1/export_evidence` hit             | Yes      | __________________ | ______    |
| `/v1/ask` hit                         | Yes      | __________________ | ______    |
| `ask_path = v1_evidence`              | Yes      | __________________ | ______    |
| evidence entries count > 0            | Yes      | __________________ | ______    |
| evidence paths relevant               | Yes      | __________________ | ______    |
| steps present or honest insufficiency | Yes      | __________________ | ______    |
| execution false                       | Yes      | __________________ | ______    |
| vLLM hit                              | No       | __________________ | ______    |

### Evidence summary

* Top 5 paths:
  
  1. ---
  2. ---
  3. ---
  4. ---
  5. ---

* Relevance verdict: `good / mixed / weak`

### Logs

* Context Layer excerpt: ______________________________________
* Plan-Gate excerpt: _________________________________________
* vLLM excerpt: ______________________________________________

### Verdict

---

---

## C. Scenario Record — Debug / Explain

**Goal:** Validate that Explain/Debug uses evidence plus LLM path when expected.

**Input query:** `Explain this function and likely bug risk.`  
**top_k:** `8`  
**Selected file:** `runtime/ask_service/handlers.py`  
**Selection / method:** `def handle_ask_request(ask_request: dict) -> dict:`

### Command sequence

```bash
# Reuse /tmp/evidence.json or regenerate with a debug-oriented query
curl -sS -X POST "$CONTEXT_URL/v1/export_evidence" \
  -H "Content-Type: application/json" \
  -d "{\"workspace_root\":\"$WORKSPACE_ROOT\",\"query\":\"Explain this function and likely bug risk.\",\"top_k\":$TOP_K}" \
  > /tmp/evidence_debug.json

python3 - <<'PY'
import datetime, json, uuid
ev = json.load(open('/tmp/evidence_debug.json', 'r', encoding='utf-8'))
req = {
  "schema_version": "ask_request.v1.0",
  "request_id": str(uuid.uuid4()),
  "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
  "query": "Explain this function and likely bug risk.",
  "task_type": "EXPLAIN_DEBUG",
  "selected_file": "runtime/ask_service/handlers.py",
  "client_context": {"selection": "def handle_ask_request(ask_request: dict) -> dict:"},
  "evidence_bundle": ev,
}
if ev.get("workspace_identity_hash"):
  req["expected_workspace_identity_hash"] = ev["workspace_identity_hash"]
json.dump(req, open('/tmp/ask_debug_v1.json', 'w', encoding='utf-8'))
print("wrote /tmp/ask_debug_v1.json")
PY

curl -sS -X POST "$PLAN_GATE_URL/v1/ask" \
  -H "Content-Type: application/json" \
  --data-binary "@/tmp/ask_debug_v1.json" \
  > /tmp/ask_debug_v1_response.json
```

### Expected

- `/v1/export_evidence` succeeds
- `/v1/ask` succeeds
- response contains `explain_debug` object
- response contains `governance_posture=PLAN_ONLY` and `execution=false`
- vLLM log shows `/v1/chat/completions` call during this request window

### Actual

| Check                                  | Expected | Actual             | Pass/Fail |
| -------------------------------------- | -------- | ------------------ | --------- |
| `/v1/export_evidence` hit              | Yes      | __________________ | ______    |
| `/v1/ask` hit                          | Yes      | __________________ | ______    |
| `ask_path = v1_evidence`               | Yes      | __________________ | ______    |
| `explain_debug` present                | Yes      | __________________ | ______    |
| vLLM hit                               | Yes      | __________________ | ______    |
| output tied to selected file/selection | Yes      | __________________ | ______    |
| execution false                        | Yes      | __________________ | ______    |

### Logs

* Context Layer excerpt: ______________________________________
* Plan-Gate excerpt: _________________________________________
* vLLM excerpt: ______________________________________________

### Verdict

---

---

## D. Scenario Record — Plan

**Goal:** Validate governed planning without execution.

**Input query:** `Plan how to add structured request logging in Plan-Gate without changing behavior.`  
**top_k:** `8`

### Command sequence (plan-only Ask contract)

```bash
curl -sS -X POST "$CONTEXT_URL/v1/export_evidence" \
  -H "Content-Type: application/json" \
  -d "{\"workspace_root\":\"$WORKSPACE_ROOT\",\"query\":\"Plan how to add structured request logging in Plan-Gate without changing behavior.\",\"top_k\":$TOP_K}" \
  > /tmp/evidence_plan.json

python3 - <<'PY'
import datetime, json, uuid
ev = json.load(open('/tmp/evidence_plan.json', 'r', encoding='utf-8'))
req = {
  "schema_version": "ask_request.v1.0",
  "request_id": str(uuid.uuid4()),
  "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
  "query": "Plan how to add structured request logging in Plan-Gate without changing behavior.",
  "evidence_bundle": ev,
}
if ev.get("workspace_identity_hash"):
  req["expected_workspace_identity_hash"] = ev["workspace_identity_hash"]
json.dump(req, open('/tmp/ask_plan_v1.json', 'w', encoding='utf-8'))
PY

curl -sS -X POST "$PLAN_GATE_URL/v1/ask" \
  -H "Content-Type: application/json" \
  --data-binary "@/tmp/ask_plan_v1.json" \
  > /tmp/ask_plan_v1_response.json
```

### Expected

- evidence-first path preferred (`/v1/export_evidence` -> `/v1/ask`)
- `governance_posture=PLAN_ONLY`
- `plan_summary.steps` present
- `execution=false`
- vLLM not required for normal plan-only path

### Actual

| Check                    | Expected                | Actual             | Pass/Fail |
| ------------------------ | ----------------------- | ------------------ | --------- |
| evidence export hit      | Yes / preferred         | __________________ | ______    |
| Plan-Gate endpoint used  | `/v1/ask` or `/v0/plan` | __________________ | ______    |
| `PLAN_ONLY`              | Yes                     | __________________ | ______    |
| steps present            | Yes                     | __________________ | ______    |
| notes present in backend | Yes / optional          | __________________ | ______    |
| execution false          | Yes                     | __________________ | ______    |
| vLLM hit                 | No / not required       | __________________ | ______    |

### Verdict

---

---

## E. Scenario Record — Code / Execute

**Goal:** Validate governed code execution or refusal honestly.

**Command / action:** `echo production-slice-exec-check`  
**repo_root (in payload):** `/tmp` (adjust if your execute path requires a real repo)

### Command sequence

```bash
python3 - <<'PY'
import datetime, json, uuid
req = {
  "schema_version": "execute_request.v0.1",
  "request_id": str(uuid.uuid4()),
  "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
  "repo_root": "/tmp",
  "revision": "manual-validation",
  "branch": "manual-validation",
  "command": "echo production-slice-exec-check",
}
json.dump(req, open('/tmp/execute_v0.json', 'w', encoding='utf-8'))
PY

curl -sS -X POST "$PLAN_GATE_URL/v0/execute" \
  -H "Content-Type: application/json" \
  --data-binary "@/tmp/execute_v0.json" \
  > /tmp/execute_v0_response.json
```

### Expected

- `/v0/execute` returns HTTP 200 or explicit error with details
- response includes an explicit outcome (`EXECUTED`/`BLOCKED`/`REFUSED`/`DEFERRED`)
- executed path includes execution details; non-executed path includes clear reason
- no fake success (executed=false must not be rendered as success)

### Actual

| Check                                        | Expected         | Actual             | Pass/Fail |
| -------------------------------------------- | ---------------- | ------------------ | --------- |
| `/v0/execute` hit                            | Yes              | __________________ | ______    |
| outcome clear                                | Yes              | __________________ | ______    |
| exit code visible if executed                | Yes              | __________________ | ______    |
| refusal/block reason visible if not executed | Yes              | __________________ | ______    |
| execution truly happened                     | Yes / if allowed | __________________ | ______    |
| misleading success                           | No               | __________________ | ______    |

### Logs

* Plan-Gate excerpt: _________________________________________
* Runtime/sandbox excerpt: ___________________________________

### Verdict

---

---

## F. Scenario Record — No-match honesty

**Goal:** Validate honest insufficiency under weak evidence.

**Input query:** `Where is the quantum flux capacitor serializer pipeline?`  
**top_k:** `8`

### Command sequence

```bash
curl -sS -X POST "$CONTEXT_URL/v1/export_evidence" \
  -H "Content-Type: application/json" \
  -d "{\"workspace_root\":\"$WORKSPACE_ROOT\",\"query\":\"Where is the quantum flux capacitor serializer pipeline?\",\"top_k\":$TOP_K}" \
  > /tmp/evidence_nomatch.json

python3 - <<'PY'
import datetime, json, uuid
ev = json.load(open('/tmp/evidence_nomatch.json', 'r', encoding='utf-8'))
req = {
  "schema_version": "ask_request.v1.0",
  "request_id": str(uuid.uuid4()),
  "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
  "query": "Where is the quantum flux capacitor serializer pipeline?",
  "evidence_bundle": ev,
}
if ev.get("workspace_identity_hash"):
  req["expected_workspace_identity_hash"] = ev["workspace_identity_hash"]
json.dump(req, open('/tmp/ask_nomatch_v1.json', 'w', encoding='utf-8'))
PY

curl -sS -X POST "$PLAN_GATE_URL/v1/ask" \
  -H "Content-Type: application/json" \
  --data-binary "@/tmp/ask_nomatch_v1.json" \
  > /tmp/ask_nomatch_v1_response.json
```

### Expected

- evidence is weak/irrelevant or entries are empty
- response includes explicit uncertainty/limitations (usually via notes/message)
- no fabricated file paths outside evidence/context
- no high-confidence fake claim

### Actual

| Check                     | Expected | Actual             | Pass/Fail |
| ------------------------- | -------- | ------------------ | --------- |
| evidence weak/empty       | Yes      | __________________ | ______    |
| explicit insufficiency    | Yes      | __________________ | ______    |
| no hallucinated file path | Yes      | __________________ | ______    |
| no fake confidence        | Yes      | __________________ | ______    |

### Verdict

---

---

## G. Scenario Record — Failure mode

**Goal:** Validate fail-closed behavior.

**Injected condition (example A):** Invalid `ask_request.v1.0` envelope — POST body missing required `evidence_bundle` (expect HTTP 400, error code `ask_envelope_invalid`).  
**Injected condition (example B):** Workspace identity mismatch — `expected_workspace_identity_hash` does not match `evidence_bundle.workspace_identity_hash` (expect HTTP 400, error code `identity_mismatch`).

Examples (also valid):

* Context Layer unavailable
* invalid evidence bundle
* workspace identity mismatch
* invalid schema
* Plan-Gate unavailable

### Expected

- explicit failure payload with status and message
- no silent fallback where contract disallows it (e.g., v1 contract client failures)
- no fake success in UI/backend response

### Command sequence examples

```bash
# 1) Invalid envelope (expect HTTP 400; error code often ask_envelope_invalid)
curl -sS -X POST "$PLAN_GATE_URL/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"schema_version":"ask_request.v1.0","request_id":"bad","query":"x"}'

# 2) Identity mismatch (expect HTTP 400 identity_mismatch) — illustrative minimal bundle;
#    if schema validation rejects, use a real /tmp/evidence.json from scenario B and only change expected_workspace_identity_hash.
python3 - <<'PY'
import datetime, json, uuid
ev = {"schema_hint":"layer5.evidence_bundle.v1","workspace_identity_hash":"abc","entries":[{"relative_path":"x.py","retrieval_score":1,"snippet":{"text":"x"}}]}
req = {
  "schema_version":"ask_request.v1.0",
  "request_id":str(uuid.uuid4()),
  "timestamp_utc":datetime.datetime.utcnow().isoformat()+"Z",
  "query":"test",
  "expected_workspace_identity_hash":"WRONG",
  "evidence_bundle":ev
}
with open("/tmp/identity_mismatch_req.json", "w", encoding="utf-8") as f:
    json.dump(req, f)
PY

curl -sS -X POST "$PLAN_GATE_URL/v1/ask" \
  -H "Content-Type: application/json" \
  --data-binary "@/tmp/identity_mismatch_req.json"
```

### Actual

| Check                                  | Expected | Actual             | Pass/Fail |
| -------------------------------------- | -------- | ------------------ | --------- |
| failure surfaced                       | Yes      | __________________ | ______    |
| silent fallback avoided where required | Yes      | __________________ | ______    |
| fake success avoided                   | Yes      | __________________ | ______    |

### Verdict

---

## H. Final Backend Summary

| Scenario     | Endpoint path proven? | Output truthful?   | Observability sufficient? | Pass/Fail |
| ------------ | --------------------- | ------------------ | ------------------------- | --------- |
| Ask v1       | __________________    | __________________ | __________________        | ______    |
| Debug        | __________________    | __________________ | __________________        | ______    |
| Plan         | __________________    | __________________ | __________________        | ______    |
| Code         | __________________    | __________________ | __________________        | ______    |
| No-match     | __________________    | __________________ | __________________        | ______    |
| Failure mode | __________________    | __________________ | __________________        | ______    |

### Overall backend status

* Contract integrity: `good / partial / poor`
* Observability: `good / partial / poor`
* Retrieval quality: `good / mixed / weak`
* Execution honesty: `good / partial / poor`

### Biggest blocker

---

### Next required backend fix

---

## Troubleshooting (common issues)

| Symptom | Likely cause | What to do |
|---------|----------------|------------|
| `Connection refused` on 8091 / 8089 / 8000 | Service down or wrong host | Start Context Layer / Plan-Gate / vLLM; run `curl` from the same network namespace as the process |
| Export returns HTTP 422 | Workspace path invalid or index failed | Set `WORKSPACE_ROOT` to a real repo path on that machine |
| `/v1/ask` 400 `evidence_schema_invalid` | Bundle not valid v1 | Re-run export; ensure Context Layer version matches Plan-Gate |
| Scenario C: no `explain_debug` | Missing `task_type` / selection / vLLM down | vLLM must be up; request must match `EXPLAIN_DEBUG` contract |
| Scenario E: blocked / integrity message | Execute path needs full runtime imports | Expected on minimal installs; record outcome as **honest block**, not success |

---

## Document version

Single self-contained operator sheet for backend HTTP validation. Update URLs/commands if your deployment uses non-default ports or remote hosts.


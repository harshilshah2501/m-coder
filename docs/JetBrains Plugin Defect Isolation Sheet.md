## 2) JetBrains Plugin Defect Isolation Sheet

**Purpose:** Isolate **plugin-only** defects (UI, path choice, rendering) by comparing JetBrains behavior to a **known-good backend** you already proved with `docs/Backend Production Validation Sheet.md`.

**Use when:** Backend HTTP validation passes, but the IDE still looks wrong — so the bug is likely integration or presentation, not Plan-Gate/Context Layer logic.

**Do not use when:** Context Layer or Plan-Gate health checks fail — fix backend first.

**Print as:** 1 preflight page + defect records + 1 summary (optional).

* * *

### Motadata AI Coding Assistant — JetBrains Plugin Defect Isolation Sheet

## How to use this document (read once)

1. **Complete the Backend Production Validation Sheet** for the same branch, URLs, and `WORKSPACE_ROOT` you use in the IDE. Attach or note which scenarios passed (at minimum: Ask v1 export + `/v1/ask`).
2. **Open this project in JetBrains** with the plugin installed; use the **same absolute project path** on disk that Context Layer can see (on Windows+WSL, that often means the repo lives under the WSL filesystem and the IDE uses that path, or you accept `ASK_DEFAULT_REPO_ROOT` on the GPU — match your real deployment).
3. **Paste the A0 environment block** in a terminal (for `curl` baselines and log tails). Adjust URLs if yours differ.
4. **Fill the header** (IDE version, plugin version — see `jetbrains-plugin/src/main/resources/META-INF/plugin.xml`, default **0.1.0** unless you built a custom build).
5. Work through **B → F** in order for a first pass; each record compares **backend truth** (commands given) vs **plugin UI**.
6. **File defects** with a one-line statement per record; use **G** for overall severity.

**Status discipline:** For every record row, use **PASS**, **FAIL**, or **NOT_PROVEN** (no blanks). If backend truth exists but plugin/log correlation is missing, use **NOT_PROVEN**.

### Canonical test inputs (same as backend sheet)

Use these **exact** strings so results are comparable:

| Use case | Query or command |
|----------|------------------|
| Ask / evidence / grounding | `How does alert correlation work in this repo?` |
| Notes / weak evidence | `Where is the quantum flux capacitor serializer pipeline?` |
| Debug / Explain | `Explain this function and likely bug risk.` (select code in `runtime/ask_service/handlers.py` — see Record 5) |
| Submit to Runtime | `echo production-slice-exec-check` (same as Backend sheet E) |

### Log files (where to look)

| Service | Typical log |
|---------|-------------|
| Plan-Gate | `runtime/.run/plan_gate.log` (when started via `runtime/scripts/governed_services.sh`) |
| vLLM | `runtime/.run/vllm.log` |
| Context Layer | **stderr** or path from `MOTADATA_CONTEXT_LAYER_LOG_PATH` — there is not always a `context_layer.log` file |

**Note:** Plan-Gate HTTP often does **not** log each request body; if `tail -f` shows nothing, rely on **backend baseline commands** + **UI content** to prove path.

---

**Environment profile:** __________________________  
**Date:** __________________________  
**Tester:** __________________________  
**Branch / commit:** __________________________  
**IDE version:** __________________________  
**Plugin build/version:** __________________________ (default from source: **0.1.0**)

### A0. Shell variables (paste once — align with backend sheet)

```bash
export CONTEXT_URL="${CONTEXT_URL:-http://127.0.0.1:8091}"
export PLAN_GATE_URL="${PLAN_GATE_URL:-http://127.0.0.1:8089}"
export WORKSPACE_ROOT="${WORKSPACE_ROOT:-/ABSOLUTE/PATH/TO/REPO}"
```

### A. Preflight

### A1. Plugin config snapshot

| Item                   | Expected                            | Actual             |
| ---------------------- | ----------------------------------- | ------------------ |
| Evidence-first flag    | enabled / disabled as test requires | __________________ |
| Context Layer URL      | correct reachable URL               | __________________ |
| Plan-Gate reachability | `127.0.0.1:8089` or configured path | __________________ |
| Active host profile    | Windows+WSL+GPU / Linux+GPU         | __________________ |

**How to capture each preflight value (exact):**

- Evidence-first: set/unset `-Dmotadata.ask.evidence_first=true` or `MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST=1`.
- Context Layer URL source: JVM `motadata.context_layer.url`, else env `MOTADATA_CONTEXT_LAYER_URL`, else default `http://127.0.0.1:8091`.
- Plan-Gate reachability:

```bash
curl -sS "$PLAN_GATE_URL/healthz"
```

### A2. Known-good backend proof attached

| Backend proof | Meaning | Attached / noted? |
| ------------- | ------- | ----------------- |
| Ask v1 direct API pass | You ran Backend sheet **B** (export + `/v1/ask`) successfully | Yes / No |
| Debug direct API pass | You ran Backend sheet **C** (or equivalent) with vLLM up | Yes / No |
| Plan direct API pass | You ran Backend sheet **D** (plan-only `/v1/ask`) | Yes / No |
| Code direct API pass | You ran Backend sheet **E** (`/v0/execute`) and recorded outcome | Yes / No |

### A2.1 Request-id correlation checklist (required for Host-A closure pass)

| Scenario | request_id captured from backend JSON | Plugin-visible artifact linked to same scenario | Context Layer trace | Plan-Gate trace | vLLM trace |
| --- | --- | --- | --- | --- | --- |
| Ask v1 evidence-first | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | N/A |
| Explain/Debug | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN |
| Execute | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | N/A | PASS / FAIL / NOT_PROVEN | N/A |
| No-match | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | N/A |
| Failure-mode | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | optional | PASS / FAIL / NOT_PROVEN | N/A |

If request-id trace cannot be shown for a service, mark **NOT_PROVEN** and note the reason.

### A3. Purpose of this sheet

Check one:

* `Path mismatch`
* `Rendering mismatch`
* `Metadata suppression`
* `Execution UX issue`
* `Configuration issue`
* `Multiple`

* * *

## B. Defect Record 1 — Ask path mismatch

**Goal:** Determine whether JetBrains uses the same Ask path as the validated backend.

**UI action:** **Tools → Ask Motadata AI** (or assigned shortcut).  
**Evidence-first:** **ON** for this record (`-Dmotadata.ask.evidence_first=true` or `MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST=1`).  
**Query (use exactly):** `How does alert correlation work in this repo?`

### Expected if evidence-first is ON

* plugin should hit `/v1/export_evidence`
* plugin should hit `/v1/ask`
* UI should show or imply `ask_path = v1_evidence`

### What to run in parallel while clicking Ask

```bash
# Terminal 1: Context Layer (stderr or file — see Log files above)
# Terminal 2: Plan-Gate
tail -f runtime/.run/plan_gate.log
```

If no request logs exist in Plan-Gate, use response-shape proof:
- v1 path evidence: UI shows `Grounding — layer5.evidence_bundle.v1` and `ask_path: v1_evidence` (if shown).
- v0 path evidence: no v1 markers and legacy `context_bundle` style.

### Actual

| Check                                | Expected | Actual             | Defect?  |
| ------------------------------------ | -------- | ------------------ | -------- |
| Context Layer hit from plugin        | Yes      | __________________ | Yes / No |
| Plan-Gate `/v1/ask` hit              | Yes      | __________________ | Yes / No |
| Plan-Gate `/v0/ask` hit instead      | No       | __________________ | Yes / No |
| UI indicates v1 evidence path        | Yes      | __________________ | Yes / No |
| UI falls back to legacy look/wording | No       | __________________ | Yes / No |

### Defect statement

* * * 

## C. Defect Record 2 — Grounding / evidence rendering mismatch

**Goal:** Determine whether plugin truthfully renders evidence returned by backend.

**UI action:** **Ask Motadata AI** with **evidence-first ON**.  
**Query (use exactly):** `How does alert correlation work in this repo?`

### Known backend truth

* evidence count (`entries.length`): __________________

* top 3 evidence files:
  
  1. * * *
  
  2. * * *
  
  3. * * *

### How to get backend truth (exact command)

```bash
curl -sS -X POST "$CONTEXT_URL/v1/export_evidence" \
  -H "Content-Type: application/json" \
  -d "{\"workspace_root\":\"$WORKSPACE_ROOT\",\"query\":\"How does alert correlation work in this repo?\",\"top_k\":8}" \
  > /tmp/plugin_compare_evidence.json

python3 - <<'PY'
import json
d = json.load(open('/tmp/plugin_compare_evidence.json','r',encoding='utf-8'))
print("schema_hint:", d.get("schema_hint"))
print("entries:", len(d.get("entries") or []))
for i,e in enumerate((d.get("entries") or [])[:3],1):
    print(f"{i}.", e.get("relative_path"))
PY
```

### Actual plugin UI

| Check                                                            | Expected | Actual             | Defect?  |
| ---------------------------------------------------------------- | -------- | ------------------ | -------- |
| evidence files shown                                             | Yes      | __________________ | Yes / No |
| `Grounding — layer5.evidence_bundle.v1` shown                    | Yes      | __________________ | Yes / No |
| `ask_path = v1_evidence` shown                                   | Yes      | __________________ | Yes / No |
| UI says `(no files selected)` despite non-empty backend evidence | No       | __________________ | Yes / No |
| file list contradicts backend truth                              | No       | __________________ | Yes / No |

### Defect statement

* * * 

## D. Defect Record 3 — Plan summary / notes suppression

**Goal:** Determine whether plugin hides meaningful backend fields (e.g. `plan_summary.notes`).

**UI action:** **Ask Motadata AI** (evidence-first **ON** recommended so `/v1/ask` is used).  
**Query (use exactly):** `Where is the quantum flux capacitor serializer pipeline?`

### Known backend truth

* plan steps count: __________________
* plan notes present: `Yes / No`
* notes summary: __________________________________________

### How to get backend truth (exact command)

```bash
# Requires: pip install requests  (or use Backend sheet F + jq to read plan_summary)
python3 - <<'PY'
import datetime, json, uuid, requests, os
ctx = os.environ.get("CONTEXT_URL", "http://127.0.0.1:8091")
pg = os.environ.get("PLAN_GATE_URL", "http://127.0.0.1:8089")
ws = os.environ.get("WORKSPACE_ROOT", "/ABSOLUTE/PATH/TO/REPO")
q = "Where is the quantum flux capacitor serializer pipeline?"
ev = requests.post(f"{ctx}/v1/export_evidence", json={"workspace_root":ws,"query":q,"top_k":8}, timeout=30).json()
req = {"schema_version":"ask_request.v1.0","request_id":str(uuid.uuid4()),"timestamp_utc":datetime.datetime.utcnow().isoformat()+"Z","query":q,"evidence_bundle":ev}
if ev.get("workspace_identity_hash"): req["expected_workspace_identity_hash"]=ev["workspace_identity_hash"]
resp = requests.post(f"{pg}/v1/ask", json=req, timeout=60).json()
ps = resp.get("plan_summary",{})
print("steps_count:", len(ps.get("steps") or []))
print("notes:", ps.get("notes"))
PY
```

### Actual plugin UI

| Check                                      | Expected        | Actual             | Defect?  |
| ------------------------------------------ | --------------- | ------------------ | -------- |
| steps shown                                | Yes             | __________________ | Yes / No |
| notes shown                                | Yes / should be | __________________ | Yes / No |
| UI appears empty despite non-empty notes   | No              | __________________ | Yes / No |
| UI language misrepresents backend richness | No              | __________________ | Yes / No |

### Defect statement

* * *

* * *

## E. Defect Record 4 — Code path UX / honesty

**Goal:** Determine whether plugin accurately reports execution results.

**UI action:** **Tools → Submit to Runtime** (runtime must be reachable — plugin checks `/healthz` first).  
**Command (use exactly — same as Backend sheet E):** `echo production-slice-exec-check`

### Known backend truth

* endpoint hit: `/v0/execute`
* outcome: `executed / blocked / refused`
* exit code or reason: _____________________________________

### How to get backend truth (direct API baseline)

```bash
python3 - <<'PY'
import datetime, json, uuid, requests, os
pg = os.environ.get("PLAN_GATE_URL", "http://127.0.0.1:8089")
req = {
  "schema_version":"execute_request.v0.1",
  "request_id":str(uuid.uuid4()),
  "timestamp_utc":datetime.datetime.utcnow().isoformat()+"Z",
  "repo_root":"/tmp",
  "revision":"plugin-isolation",
  "branch":"plugin-isolation",
  "command":"echo production-slice-exec-check"
}
r = requests.post(f"{pg}/v0/execute", json=req, timeout=60)
print("status:", r.status_code)
print(r.text)
PY
```

### Actual plugin UI

| Check                             | Expected | Actual             | Defect?  |
| --------------------------------- | -------- | ------------------ | -------- |
| execution outcome shown clearly   | Yes      | __________________ | Yes / No |
| blocked vs executed distinguished | Yes      | __________________ | Yes / No |
| refusal reason shown              | Yes      | __________________ | Yes / No |
| misleading success text           | No       | __________________ | Yes / No |

### Defect statement

* * *



## F. Optional Defect Record 5 — Debug / LLM visibility

**Goal:** Determine whether plugin makes LLM-backed debug behavior visible enough.

**UI action:** **Ask Motadata AI** with **text selected** in the editor (so the plugin sets `EXPLAIN_DEBUG`).  
**Query (use exactly):** `Explain this function and likely bug risk.`  
**Where to select:** Open `runtime/ask_service/handlers.py`, select a few lines inside `handle_ask_request` (or the function signature line used in backend tests).

### Known backend truth

* `/v1/ask` hit: `Yes / No`
* `explain_debug` present: `Yes / No`
* vLLM hit: `Yes / No`

### How to verify vLLM hit

```bash
# Run while triggering Debug from IDE
tail -f runtime/.run/vllm.log
```

Look for a request window that includes `/v1/chat/completions` and timestamps matching the UI action.

### Actual plugin UI

| Check                                                  | Expected     | Actual             | Defect?  |
| ------------------------------------------------------ | ------------ | ------------------ | -------- |
| debug path visibly distinct from ordinary planner text | Yes          | __________________ | Yes / No |
| LLM-backed reasoning clearly implied                   | Yes / enough | __________________ | Yes / No |
| selection/file grounding visible                       | Yes          | __________________ | Yes / No |

### Defect statement

* * *

* * *

## G. Final Plugin Defect Summary

| Area                | Backend correct? | Plugin correct? | Severity       |
| ------------------- | ---------------- | --------------- | -------------- |
| Ask path selection  | Yes / No         | Yes / No        | `P0 / P1 / P2` |
| Grounding rendering | Yes / No         | Yes / No        | `P0 / P1 / P2` |
| Notes rendering     | Yes / No         | Yes / No        | `P0 / P1 / P2` |
| Code outcome UX     | Yes / No         | Yes / No        | `P0 / P1 / P2` |
| Debug visibility    | Yes / No         | Yes / No        | `P0 / P1 / P2` |

### Severity rubric (use consistently)

- **P0:** backend truth is correct but plugin misleads operator or hides critical path (production-blocking).
- **P1:** plugin behavior is functionally usable but incomplete/opaque.
- **P2:** polish/usability debt; no incorrect governance outcome.

### Plugin overall status

* Contract alignment: `good / partial / poor`
* Rendering honesty: `good / partial / poor`
* Operator trustworthiness: `good / partial / poor`

### Highest-priority plugin defect

* * *

### Smallest high-leverage fix

* * *

* * *

## How to use these two sheets together

Use them in this order:

1. **`docs/Backend Production Validation Sheet.md`** — Prove HTTP contracts and endpoints without the IDE.
2. **`docs/JetBrains Plugin Defect Isolation Sheet.md`** — Compare IDE behavior to the same backends; file plugin defects only when backend baselines match.

That way you separate:

| Failure type | Typical cause |
|--------------|----------------|
| **System failure** | Context Layer, Plan-Gate, or vLLM misconfiguration |
| **Integration failure** | Wrong URL, evidence-first flag, `WORKSPACE_ROOT` / path mismatch |
| **Presentation failure** | Plugin UI hides or mislabels backend truth |

---

## Troubleshooting (plugin sheet)

| Symptom | Check |
|---------|--------|
| Always `/v0/ask` | Evidence-first flag OFF; turn ON for v1 path tests |
| Context Layer never contacted | Evidence-first OFF, or `MOTADATA_CONTEXT_LAYER_DISABLE_HTTP=1`, or wrong URL |
| “Runtime unavailable” on Submit | Plan-Gate not running on `127.0.0.1:8089` (plugin URL is not configurable in code today) |
| Backend curl works, IDE shows empty context | Path mismatch: IDE `repo_root` must resolve on the server or use `ASK_DEFAULT_REPO_ROOT` on Ask host |

---

*Self-contained: you can run this sheet with only this file + Backend sheet + a running stack; no other doc is required.*



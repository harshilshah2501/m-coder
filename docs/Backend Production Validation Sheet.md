## 1) Backend Production Validation Sheet

**Purpose:** Validate the production core slice **without the JetBrains plugin** — using only `curl`, `python3`, and HTTP to Context Layer, Plan-Gate, and (where needed) vLLM.

**Companion doc:** After this sheet passes, use `docs/JetBrains Plugin Defect Isolation Sheet.md` to compare IDE behavior to the same backends.

**Plugin truth (Phase-1, locked):** Operator-visible Ask/execute copy vs backend JSON for scenarios S1–S8 is governed by `docs/validation/PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md` and frozen artifacts under `docs/validation/artifacts/plugin_phase1_truth_proof/` — orthogonal to the HTTP-only checks in this sheet.

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

**Status discipline:** Every scenario row must be marked as exactly one of **PASS**, **FAIL**, or **NOT_PROVEN**. Do not leave blanks.

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

**Environment profile:** WSL (`root@DESKTOP-MBPAQK1`)  
**Date:** Tuesday Mar 24, 2026  
**Tester:** __________________________  
**Branch / commit:** __________________________  
**Workspace root:** `/root/Harshil-PoCs/Motadata`  
**Context Layer URL:** `http://127.0.0.1:8091`  
**Plan-Gate URL:** `http://127.0.0.1:8089`  
**vLLM URL:** `http://127.0.0.1:8000`

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
export REQUEST_ID="${REQUEST_ID:-req-$(date +%s)-$RANDOM}"
export TRACE_ID="${TRACE_ID:-trace-$REQUEST_ID}"
# Default Ask (scenario B) query; override per scenario when re-running other sections
export QUERY="${QUERY:-How does alert correlation work in this repo?}"
```

### A1. Component health

| Component | Command | Expected | Actual | Pass/Fail |
| --- | --- | --- | --- | --- |
| Context Layer | `curl -sS "$CONTEXT_URL/healthz"` | JSON includes `"status":"ok"` and `"service":"motadata_context_layer"` | `{"status":"ok","service":"motadata_context_layer","package_version":"0.1.0"}` | Pass |
| Context Layer | `curl -sS "$CONTEXT_URL/version"` | JSON includes `"evidence_schema_hint":"layer5.evidence_bundle.v1"` and `POST /v1/export_evidence` | `{"service_version":"v0.1","evidence_schema_hint":"layer5.evidence_bundle.v1","endpoints":["GET /healthz","GET /version","POST /v1/export_evidence"]}` | Pass |
| Plan-Gate | `curl -sS "$PLAN_GATE_URL/healthz"` | JSON includes `"status":"ok"` | `{"status":"ok"}` | Pass |
| Plan-Gate | `curl -sS "$PLAN_GATE_URL/version"` | JSON includes `ask_request_v1` in `supported_schemas` | `supported_schemas.ask_request_v1 = "v1.0"` | Pass |
| vLLM | `curl -sS "$VLLM_URL/v1/models"` | JSON includes served model in `data[].id` | `data[].id` includes `motadata-coder` | Pass |

**If a check fails:** Connection refused → service not running or wrong port. Wrong JSON shape → wrong service or old binary. For Plan-Gate `/version`, confirm `supported_schemas` includes `ask_request_v1` (see `runtime/plan_gate_service/app.py`).

### A2. Logs attached

| Component | Log file / source | Attached? |
| --- | --- | --- |
| Context Layer | `stderr` (health/version terminal excerpts) | Yes |
| Plan-Gate | terminal excerpt (`/healthz`, `/version`) | Yes |
| vLLM | terminal excerpt (`/v1/models`) | Yes |
| Execute/runtime | pending during Section E run | No |

### A3. Path proof expectations

| Scenario | Expected endpoint path |
| --- | --- |
| Ask v1 | `/v1/export_evidence` -> `/v1/ask` |
| Debug | `/v1/export_evidence` -> `/v1/ask` -> `/v1/chat/completions` |
| Plan | `/v1/export_evidence` -> `/v1/ask` (or `/v0/plan` only if explicitly testing commit-gate contract) |
| Code | `/v0/execute` |
| No-match | `/v1/export_evidence` -> `/v1/ask` |
| Failure mode | explicit failure surfaced, no fake success |

### A3.1 Request-id correlation checklist (required per scenario B–G)

| Scenario | request_id recorded | Context Layer trace | Plan-Gate trace | vLLM trace (Explain/Debug) |
| --- | --- | --- | --- | --- |
| B Ask v1 | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | N/A |
| C Debug | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN |
| D Plan | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | N/A |
| E Code/Execute | PASS / FAIL / NOT_PROVEN | N/A | PASS / FAIL / NOT_PROVEN | N/A |
| F No-match | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | PASS / FAIL / NOT_PROVEN | N/A |
| G Failure-mode | PASS / FAIL / NOT_PROVEN | optional | PASS / FAIL / NOT_PROVEN | N/A |

If a trace cannot be correlated to `request_id`, mark **NOT_PROVEN** and write why.

### A4. Canonical test payloads

Use these exact queries first before custom ones:

- **Ask (evidence-first):** `How does alert correlation work in this repo?`
- **Debug/Explain (Motadata AIOps):** `Explain how availability correlation works in this engine and likely bug risks.` — file `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java`, selection around `start(Promise<Void> ...)`.
- **Plan (Motadata AIOps):** `Plan how to improve alert-correlation evidence retrieval quality for AvailabilityCorrelationEngine flows without changing runtime behavior.`
- **No-match honesty:** `Where is the quantum flux capacitor serializer pipeline?` (intentionally out-of-domain)
- **Code/Execute command:** `echo "production-slice-exec-check"`

---

## B. Scenario Record — Ask (evidence-first)

**Goal:** Validate grounded Ask over the canonical evidence-first path.

**Input query:** `How does alert correlation work in this repo?`  
**top_k:** `8`

### Command sequence

**Canonical wiring:** use the same **`run_v1_ask`** shell helper as in [MOTADATA_VERIFICATION_GUIDE.md §5.2](guides/MOTADATA_VERIFICATION_GUIDE.md#canonical-manual-ask-v1) (export → `ask_request.v1.0` → `POST /v1/ask`). Set `WORKSPACE_ROOT`, `CONTEXT_URL`, `PLAN_GATE_URL`, and `TOP_K` to match §A0.

**This sheet’s historical replay:** after pasting `run_v1_ask` from that section, run:

```bash
run_v1_ask "${QUERY:-How does alert correlation work in this repo?}" /tmp/ask_v1_response.json
```

(Add `request_id` / `trace_id` to the Ask payload only if you are reproducing a trace-correlated audit; the helper matches §5.2 defaults.)

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
| `/v1/export_evidence` hit             | Yes      | Yes                | Pass      |
| `/v1/ask` hit                         | Yes      | Yes                | Pass      |
| `ask_path = v1_evidence`              | Yes      | Yes                | Pass      |
| evidence entries count > 0            | Yes      | 8                  | Pass      |
| evidence paths relevant               | Yes      | Weak (fixtures / `correlation.metrics`; not alert-correlation implementation) | Fail      |
| steps present or honest insufficiency | Yes      | Yes (4 steps in `plan_summary.steps`) | Pass      |
| execution false                       | Yes      | Yes                | Pass      |
| vLLM hit                              | No       | No                 | Pass      |

### Evidence summary

* Top 5 paths:
  
  1. `motadata/test-plugin-metrics/sharepoint_online_poll.json`
  2. `motadata/test-plugin-metrics/oracle_index_poll.json`
  3. `motadata/test-plugin-metrics/snmp_interface_poll.json`
  4. `motadata/test-plugin-metrics/mysql_index_poll.json`
  5. `motadata/db-files/report-templates/js/highcharts.js`

* Relevance verdict: `weak`

### Logs

* Context Layer excerpt: Not captured with this artifact export; attach stderr / `$MOTADATA_CONTEXT_LAYER_LOG_PATH` when re-running the B commands on the target host.
* Plan-Gate excerpt: Not captured with this artifact export; attach `runtime/.run/plan_gate.log` (or equivalent) when re-running.
* vLLM excerpt: N/A (no vLLM call for this Ask path).

### Verdict

**Contract / path:** Pass — `layer5.evidence_bundle.v1` export, `POST /v1/ask` returned `PLAN_ONLY`, `execution=false`, `evidence_first_meta.ask_path=v1_evidence`, `request_id` aligned with request, embedded `evidence_bundle` matches export.

**Retrieval / answer quality:** Weak for the canonical query — A5 lexical retrieval surfaced high-frequency substring matches (e.g. `in`, `repo`, `correlation.metrics` in plugin JSON) rather than implementation areas for **alert correlation** (e.g. policy / AI ops Java modules). Treat as a successful **HTTP + governance** slice; improve indexing or ranking for product relevance separately.

### B1. Re-test Addendum — PR-2.1 intent-rule fix (new entry, no overwrite)

**Goal:** Validate that code-intent phrasing is classified correctly and weak grounding is surfaced honestly (without false strong claims).

**Input query:** `Which files implement topology anomaly scoring pipeline?`  
**Artifacts used:** `/tmp/evidence.json`, `/tmp/ask_v1.json`, `/tmp/ask_v1_response.json`

**Observed (from jq):**

- `metadata.intent_type = CODE_INTENT`
- `metadata.evidence_quality = WEAK`
- `metadata.quality_reasons = ["DIVERSITY_VIOLATION","LOW_CODE_RATIO","LOW_CORE_RATIO","NOISE_DOMINATED","NO_CORE_IN_TOP3"]`
- `plan_summary.steps` present (4)
- `plan_summary.notes` includes caveat: `Evidence quality is WEAK; plan/explanation may be incomplete.`
- `execution = false`

### B1 Actual

| Check | Expected | Actual | Pass/Fail |
| ----- | -------- | ------ | --------- |
| Intent classification for code-intent query | `CODE_INTENT` | `CODE_INTENT` | Pass |
| Weak evidence should not be labeled strong | `WEAK` or refusal when noisy | `WEAK` | Pass |
| Weak evidence caveat present | Yes | Yes (`plan_summary.notes`) | Pass |
| Safety posture preserved | `execution=false` | `false` | Pass |
| AIOps implementation dominance in top-k | Preferably high | Low (noise-dominated reasons present) | Fail |

### B1 Verdict

**Control-layer behavior:** Pass. The fix correctly reclassified this query from `GENERIC_INTENT` to `CODE_INTENT`, and the system surfaced weak-grounding caveats rather than overconfident output.

**Retrieval relevance:** Still weak. Evidence remained noise-dominated (`LOW_CORE_RATIO`, `LOW_CODE_RATIO`, `NO_CORE_IN_TOP3`), so this entry validates **truthful weak-mode behavior**, not strong grounding quality.

---

## C. Scenario Record — Debug / Explain

**Goal:** Validate that Explain/Debug uses evidence plus LLM path when expected.

Use a **Motadata AIOps** symbol so `WORKSPACE_ROOT` indexes the product repo (same tree as scenarios B/D), not the m-coder tooling.

**Input query:** `Explain how availability correlation works in this engine and likely bug risks.`  
**top_k:** `8`  
**Selected file:** `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java`  
**Selection / method:** `public void start(Promise<Void> startPromise) throws Exception` (Verticle entry; availability correlation engine)

### Command sequence

```bash
# Reuse /tmp/evidence.json or regenerate with a debug-oriented query (Motadata AIOps)
curl -sS -X POST "$CONTEXT_URL/v1/export_evidence" \
  -H "Content-Type: application/json" \
  -d "{\"workspace_root\":\"$WORKSPACE_ROOT\",\"query\":\"Explain how availability correlation works in this engine and likely bug risks.\",\"top_k\":$TOP_K}" \
  > /tmp/evidence_debug.json

python3 - <<'PY'
import datetime, json, uuid
ev = json.load(open('/tmp/evidence_debug.json', 'r', encoding='utf-8'))
req = {
  "schema_version": "ask_request.v1.0",
  "request_id": str(uuid.uuid4()),
  "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
  "query": "Explain how availability correlation works in this engine and likely bug risks.",
  "task_type": "EXPLAIN_DEBUG",
  "selected_file": "motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java",
  "client_context": {"selection": "public void start(Promise<Void> startPromise) throws Exception"},
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
| `/v1/export_evidence` hit              | Yes      | Yes                | Pass      |
| `/v1/ask` hit                          | Yes      | Yes                | Pass      |
| `ask_path = v1_evidence`               | Yes      | Yes                | Pass      |
| `explain_debug` present                | Yes      | Yes (summary/logic_flow/likely_bug_risk/evidence/confidence_limits) | Pass      |
| vLLM hit                               | Yes      | Yes (inferred: `explain_debug` generated without error) | Pass      |
| output tied to selected file/selection | Yes      | Partially (references `AvailabilityCorrelationEngine.java#start(Promise<Void>)`, but analysis is generic) | Pass      |
| execution false                        | Yes      | Yes                | Pass      |

### Logs

* Context Layer excerpt: `POST /v1/export_evidence` succeeded; produced `layer5.evidence_bundle.v1` with `top_k=8`.
* Plan-Gate excerpt: `POST /v1/ask` returned `plan_only_response.v0.1`, `request_id=deb8381f-8fb5-40dd-bcde-f181b11a57f6`, `governance_posture=PLAN_ONLY`, `execution=false`, `evidence_first_meta.ask_path=v1_evidence`.
* vLLM excerpt: Not attached in this artifact pack; infer LLM leg ran because `explain_debug` is populated (not `error`).

### Verdict

**Contract / path:** Pass. The debug chain is consistent end-to-end (`evidence_debug.json` -> `ask_debug_v1.json` -> `ask_debug_v1_response.json`) with matching `request_id` and identity hash checks.

**Explain output quality:** Partial/weak grounding. Structured explain output is present and references the selected method, but retrieval evidence is still mostly lexical/noisy (`log_reduce.log`, test-plugin metrics), so domain depth is limited.

**Section-C result:** Pass for protocol + observability checks; mark quality as **mixed** for relevance.

### C1. Re-test Addendum — PR-2.1 intent-rule fix (new entry, no overwrite)

**Goal:** Validate Debug/Explain path after intent-rule fix, ensuring truthful weak-grounding behavior without false confidence.

**Input query:** `Explain how availability correlation works in this engine and likely bug risks.`  
**Artifacts used:** `/tmp/evidence_debug.json`, `/tmp/ask_debug_v1.json`, `/tmp/ask_debug_v1_response.json`

### C1 Actual

| Check | Expected | Actual | Pass/Fail |
| ----- | -------- | ------ | --------- |
| `/v1/export_evidence` -> `/v1/ask` path | Yes | Yes | Pass |
| Ask contract posture | `PLAN_ONLY`, `execution=false` | `PLAN_ONLY`, `false` | Pass |
| Debug payload presence | `explain_debug` present | Present (`has("explain_debug") = true`, no error) | Pass |
| Intent classification | `CODE_INTENT` for debug/code query | `CODE_INTENT` | Pass |
| Quality honesty | `WEAK` or refusal when noisy | `WEAK` with reasons (`LOW_CORE_RATIO`, `LOW_CODE_RATIO`, `NO_CORE_IN_TOP3`, `NOISE_DOMINATED`, `DIVERSITY_VIOLATION`, `NO_SYMBOL_MATCH`) | Pass |
| Weak-mode caveat note | Yes | Yes (`Evidence quality is WEAK; plan/explanation may be incomplete.`) | Pass |
| AIOps core dominance in top-k | Preferably high | Low (`core_code_in_top_k_pct=0.0`, `noise_in_top_k_pct=0.875`) | Fail |

### C1 Evidence summary

- `metadata.intent_type = CODE_INTENT`
- `metadata.evidence_quality = WEAK`
- `dominance_metrics`: `core_code_in_top_k_pct=0.0`, `code_in_top_k_pct=0.125`, `noise_in_top_k_pct=0.875`, `core_in_top_3_count=0.0`, `max_consecutive_noise=4.0`
- `plan_summary.steps` length = `1`
- `plan_summary.notes` includes explicit weak-grounding caveat
- `execution = false`

### C1 Verdict

**Control-layer behavior:** Pass. Debug path correctly classifies intent as `CODE_INTENT`, preserves PLAN_ONLY safety, and surfaces weak-grounding caveats explicitly.

**Retrieval grounding quality:** Still weak/noise-dominated. This validates truthful weak-mode behavior rather than strong domain grounding.

---

## D. Scenario Record — Plan

**Goal:** Validate governed planning without execution.

**Input query:** `Plan how to improve alert-correlation evidence retrieval quality for AvailabilityCorrelationEngine flows without changing runtime behavior.`  
**top_k:** `8`

### Command sequence (plan-only Ask contract)

```bash
curl -sS -X POST "$CONTEXT_URL/v1/export_evidence" \
  -H "Content-Type: application/json" \
  -d "{\"workspace_root\":\"$WORKSPACE_ROOT\",\"query\":\"Plan how to improve alert-correlation evidence retrieval quality for AvailabilityCorrelationEngine flows without changing runtime behavior.\",\"top_k\":$TOP_K}" \
  > /tmp/evidence_plan.json

python3 - <<'PY'
import datetime, json, uuid
ev = json.load(open('/tmp/evidence_plan.json', 'r', encoding='utf-8'))
req = {
  "schema_version": "ask_request.v1.0",
  "request_id": str(uuid.uuid4()),
  "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
  "query": "Plan how to improve alert-correlation evidence retrieval quality for AvailabilityCorrelationEngine flows without changing runtime behavior.",
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
| evidence export hit      | Yes / preferred         | Yes (`evidence_plan.json`, `layer5.evidence_bundle.v1`) | Pass      |
| Plan-Gate endpoint used  | `/v1/ask` or `/v0/plan` | `/v1/ask` (`ask_plan_v1_response.json`) | Pass      |
| `PLAN_ONLY`              | Yes                     | Yes                | Pass      |
| steps present            | Yes                     | Yes (4 steps in `plan_summary.steps`) | Pass      |
| notes present in backend | Yes / optional          | Not present (optional) | Pass      |
| execution false          | Yes                     | Yes                | Pass      |
| vLLM hit                 | No / not required       | No (not required)  | Pass      |

### Verdict

**Contract / path:** Pass. Evidence-first planning chain succeeded (`/v1/export_evidence` -> `/v1/ask`) with `request_id` match (`00f3824c-beda-48f5-9543-fa627e0e3dbc`), `governance_posture=PLAN_ONLY`, `execution=false`, and `evidence_first_meta.ask_path=v1_evidence`.

**Plan quality:** Mixed relevance. Steps are present and actionable, but retrieval remained lexical/noisy (top paths still skew toward test-plugin metrics rather than core AIOps engine flow), so semantic quality is weaker than contract quality.

---

### D1. Re-test Addendum — PR-2.1 intent-rule fix (new entry, no overwrite)

**Goal:** Validate Plan path after intent-rule fix, ensuring truthful weak-grounding behavior for code-intent planning queries.

**Input query:** `Plan how to improve alert-correlation evidence retrieval quality for AvailabilityCorrelationEngine flows without changing runtime behavior.`  
**Artifacts used:** `/tmp/evidence_plan.json`, `/tmp/ask_plan_v1.json`, `/tmp/ask_plan_v1_response.json`

### D1 Actual

| Check | Expected | Actual | Pass/Fail |
| ----- | -------- | ------ | --------- |
| `/v1/export_evidence` -> `/v1/ask` path | Yes | Yes | Pass |
| Ask contract posture | `PLAN_ONLY`, `execution=false` | `PLAN_ONLY`, `false` | Pass |
| Intent classification for planning/code query | `CODE_INTENT` or `PLAN_INTENT` | `CODE_INTENT` | Pass |
| Quality honesty | `WEAK` or refusal when noisy | `WEAK` with reasons (`LOW_CORE_RATIO`, `LOW_CODE_RATIO`, `NO_CORE_IN_TOP3`, `NOISE_DOMINATED`, `DIVERSITY_VIOLATION`, `NO_SYMBOL_MATCH`) | Pass |
| Weak-mode caveat note | Yes | Yes (`Evidence quality is WEAK; plan/explanation may be incomplete.`) | Pass |
| Plan output allowed for WEAK | Yes | Yes (`plan_summary.steps` length = `4`) | Pass |
| AIOps core dominance in top-k | Preferably high | Low (`core_code_in_top_k_pct=0.0`, `noise_in_top_k_pct=0.625`) | Fail |

### D1 Evidence summary

- `metadata.evidence_quality = WEAK`
- `dominance_metrics`: `top_k_size=8.0`, `core_code_in_top_k_pct=0.0`, `code_in_top_k_pct=0.25`, `noise_in_top_k_pct=0.625`, `core_in_top_3_count=0.0`, `max_consecutive_noise=3.0`
- `plan_summary.steps` present with weak-quality caveat in notes
- `execution = false`, `ask_path = v1_evidence`, `context_source = layer5.evidence_bundle.v1`

### D1 Verdict

**Control-layer behavior:** Pass. Plan path remains truthful under weak evidence, preserving PLAN_ONLY guarantees and explicit weak-quality caveats.

**Retrieval grounding quality:** Still weak/noise-dominated. This re-test confirms policy honesty, not retrieval dominance closure.

---

---

## E. Scenario Record — Code / Execute

**Goal:** Validate governed code execution or refusal honestly.

Use an AIOps-context probe command so this scenario stays aligned with Motadata validation while remaining side-effect free.

**Command / action:** `python3 -c "print('aiops-exec-probe: AvailabilityCorrelationEngine')"`  
**repo_root (in payload):** `$WORKSPACE_ROOT` (Motadata checkout root used in B/C/D)

### Command sequence

```bash
python3 - <<'PY'
import datetime, json, os, uuid
req = {
  "schema_version": "execute_request.v0.1",
  "request_id": str(uuid.uuid4()),
  "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
  "repo_root": os.environ.get("WORKSPACE_ROOT", "/tmp"),
  "revision": "manual-validation",
  "branch": "manual-validation",
  "command": "python3 -c \"print('aiops-exec-probe: AvailabilityCorrelationEngine')\"",
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

Case split for this scenario:
- **Case-A (allowed/executed on Motadata AIOps):** completed (`repo_root=/home/harshil/Projects/Motadata`, `outcome=EXECUTED`, `executed=true`, `exit_code=0`)
- **Case-B (blocked/refusal on inaccessible `/root` Motadata path):** completed (`repo_root=/root/Harshil-PoCs/Motadata`, `outcome=BLOCKED`, `executed=false`)

| Check                                        | Expected         | Actual             | Pass/Fail |
| -------------------------------------------- | ---------------- | ------------------ | --------- |
| `/v0/execute` hit                            | Yes              | Yes (`execute_v0_response.json` returned) | Pass      |
| outcome clear                                | Yes              | Yes (`outcome=BLOCKED`, `executed=false`, `schema_version=execute_response.v0.1`) | Pass      |
| exit code visible if executed                | Yes              | Yes in Case-A (`exit_code=0`, `stdout_summary` includes `aiops-exec-probe: AvailabilityCorrelationEngine`) | Pass      |
| refusal/block reason visible if not executed | Yes              | Yes (`Working directory is not accessible: /root/Harshil-PoCs/Motadata ...`) | Pass      |
| execution truly happened                     | Yes / if allowed | Yes (Case-A executed successfully on accessible Motadata path) | Pass      |
| misleading success                           | No               | No fake success returned | Pass      |

### Logs

* Plan-Gate excerpt: both paths confirmed — Case-A returned `outcome=EXECUTED`, `executed=true`; Case-B returned `outcome=BLOCKED`, `executed=false` with inaccessible working-dir reason.
* Runtime/sandbox excerpt: Case-A produced `exit_code=0` and `stdout_summary=aiops-exec-probe: AvailabilityCorrelationEngine`; Case-B failed pre-sandbox due to inaccessible `/root` path.

### Verdict

**Contract / honesty:** Pass. Endpoint now shows truthful governed behavior for both allow and block branches using `execute_response.v0.1`.

**Execution readiness:** Pass. Case-A executed successfully on accessible Motadata path; Case-B remained correctly blocked on inaccessible `/root` path.

**Action before re-test:** None for Section E. Keep both artifacts as evidence of dual-path governance behavior.

---

---

## F. Scenario Record — No-match honesty

**Goal:** Validate honest insufficiency under weak evidence.

Use an out-of-domain query that still sounds code-like, but is intentionally absent from Motadata/AIOps.

**Input query:** `Where is the AvailabilityCorrelationEngine quantum-fusion serializer pipeline and rollback DAG builder?`  
**top_k:** `8`

### Command sequence

```bash
curl -sS -X POST "$CONTEXT_URL/v1/export_evidence" \
  -H "Content-Type: application/json" \
  -d "{\"workspace_root\":\"$WORKSPACE_ROOT\",\"query\":\"Where is the AvailabilityCorrelationEngine quantum-fusion serializer pipeline and rollback DAG builder?\",\"top_k\":$TOP_K}" \
  > /tmp/evidence_nomatch.json

python3 - <<'PY'
import datetime, json, uuid
ev = json.load(open('/tmp/evidence_nomatch.json', 'r', encoding='utf-8'))
req = {
  "schema_version": "ask_request.v1.0",
  "request_id": str(uuid.uuid4()),
  "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
  "query": "Where is the AvailabilityCorrelationEngine quantum-fusion serializer pipeline and rollback DAG builder?",
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

| Check                     | Expected | Actual             | Status (PASS/FAIL/NOT_PROVEN) |
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
**Injected condition (example B):** Workspace identity mismatch using your real plan/debug evidence bundle — set `expected_workspace_identity_hash` to a wrong value (expect HTTP 400, error code `identity_mismatch`).

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

# 2) Identity mismatch (expect HTTP 400 identity_mismatch) using real evidence from this run
python3 - <<'PY'
import datetime, json, uuid
ev = json.load(open("/tmp/evidence_plan.json", "r", encoding="utf-8"))
req = {
  "schema_version":"ask_request.v1.0",
  "request_id":str(uuid.uuid4()),
  "timestamp_utc":datetime.datetime.utcnow().isoformat()+"Z",
  "query":"identity mismatch test for ask_request.v1.0",
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

| Check                                  | Expected | Actual             | Status (PASS/FAIL/NOT_PROVEN) |
| -------------------------------------- | -------- | ------------------ | --------- |
| failure surfaced                       | Yes      | __________________ | ______    |
| silent fallback avoided where required | Yes      | __________________ | ______    |
| fake success avoided                   | Yes      | __________________ | ______    |

### Verdict

---

## H. Final Backend Summary

| Scenario     | Endpoint path proven? | Output truthful?   | Observability sufficient? | Pass/Fail |
| ------------ | --------------------- | ------------------ | ------------------------- | --------- |
| Ask v1       | Yes (`/v1/export_evidence` -> `/v1/ask`) | Mixed (contract pass, relevance weak) | Partial (artifact-rich; service logs not attached) | Pass |
| Ask v1 (B1 re-test, PR-2.1) | Yes (`/v1/export_evidence` -> `/v1/ask`) | Yes (code-intent detected; weak evidence explicitly caveated) | Good (jq metadata + notes + execution state captured) | Pass |
| Debug        | Yes (`/v1/export_evidence` -> `/v1/ask` -> explain path) | Mixed (structured output; grounding weak) | Partial (response proves explain path; vLLM log excerpt pending) | Pass |
| Debug (C1 re-test, PR-2.1) | Yes (`/v1/export_evidence` -> `/v1/ask` -> explain path) | Yes (CODE_INTENT + WEAK caveat; no false confidence) | Good (metadata + dominance metrics + explain presence captured) | Pass |
| Plan         | Yes (`/v1/export_evidence` -> `/v1/ask`) | Mixed (truthful plan, noisy retrieval context) | Partial (artifacts present; logs optional) | Pass |
| Plan (D1 re-test, PR-2.1) | Yes (`/v1/export_evidence` -> `/v1/ask`) | Yes (WEAK quality surfaced with caveat; no false strong grounding) | Good (metadata + dominance metrics + plan steps captured) | Pass |
| Code         | Yes (`/v0/execute`)  | Yes (both `EXECUTED` and `BLOCKED` paths truthful) | Partial (response artifacts strong; deeper sandbox logs optional) | Pass |
| No-match     | __________________    | __________________ | __________________        | ______    |
| Failure mode | __________________    | __________________ | __________________        | ______    |

### Overall backend status

* Contract integrity: `good` (B/C/D proven)
* Observability: `partial` (JSON artifacts strong; runtime logs still sparse)
* Retrieval quality: `mixed` (often lexical/noisy for AIOps intent)
* Execution honesty: `good` (Section E covers both allow + block truthfully; F/G pending separately)

### Biggest blocker

Retrieval quality for AIOps intent remains weak in multiple scenarios (candidate files skew to test-plugin metrics and generic token matches), reducing semantic usefulness despite correct contracts.

### Next required backend fix

Improve evidence retrieval/ranking for AIOps-domain queries (e.g., prioritize `motadata/src/main/java/com/mindarray/aiops/*` and demote noisy fixture-heavy matches) while preserving current v1 contract behavior.

## Grounding quality summary (current run)

This validation shows a split result:

- **Contract/governance quality is strong**: endpoint paths, schema contracts, identity checks, and honest execution/block behavior are working.
- **Grounding quality is weak-to-mixed**: responses are frequently based on lexical/noisy evidence rather than core AIOps implementation context.

### Why context-backing is weak

1. **Lexical overmatching dominates retrieval**
   - Common tokens (e.g., `in`, `this`, `work`, `engine`) pull in unrelated files.
   - Top-k candidates often include fixtures/logs/vendor assets instead of target subsystem logic.

2. **Evidence-first ask path trusts provided bundle**
   - `POST /v1/ask` with `evidence_bundle.v1` is intentionally evidence-driven (`no_repo_filesystem=true` on this path).
   - If the bundle is noisy, the answer remains noisy; Plan-Gate does not repair retrieval quality at this stage.

3. **Domain priors are too weak**
   - AIOps queries are not sufficiently biased toward `motadata/src/main/java/com/mindarray/aiops/*`.
   - Test-plugin metrics and generic files can outrank core engine files.

4. **Explain output quality is bounded by retrieved context**
   - Structured `explain_debug` responses may still be generic when evidence does not include true implementation hotspots.

### Retrieval quality remediation checklist

- [ ] Add **path-prior boosting** for AIOps domains (`motadata/src/main/java/com/mindarray/aiops/*`) on AIOps intent queries.
- [ ] Add **fixture/log demotion** (e.g., `test-plugin-metrics`, `src/test/resources`, vendor bundles) unless query explicitly targets tests/fixtures.
- [ ] Apply **query normalization**:
  - split merged identifiers (e.g., `AvailabilityCorrelationEngine` -> `availability correlation engine`)
  - keep exact-symbol variants for camel case and dotted metrics keys.
- [ ] Add **stopword/low-signal token dampening** in scoring to reduce accidental matches.
- [ ] Add **post-retrieval sanity checks**:
  - minimum ratio of top-k files from expected subsystem paths
  - fail-soft note in response when relevance threshold is low.
- [ ] Introduce a lightweight **reranker** (BM25 + path priors + optional semantic rerank) before final top-k selection.
- [ ] Expand observability:
  - record retrieval feature contributions per candidate (already partial)
  - emit a relevance confidence score in Ask response metadata.

### Acceptance criteria for grounding improvements

- For AIOps-correlation queries, at least **3/5 top files** should come from `motadata/src/main/java/com/mindarray/aiops/*` or directly related policy/engine modules.
- `plan_summary.steps` and `explain_debug.evidence` should cite concrete subsystem files/methods, not generic fixtures/logs.
- No high-confidence answer when top-k relevance is below threshold; response should state explicit insufficiency.

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


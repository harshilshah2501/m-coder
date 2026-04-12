# Action 11 — Linux / WSL runbook

**Branch:** `feature/action-11-path-hardening-trace-routing`  
**Evidence folder (fixed):** `~/Harshil-PoCs/Action_11_Evidences`

This document has **two tracks only**. Pick one; do not run both “quick script” and “full evidence” for the same proof (that duplicates work).

| Track | Purpose |
|-------|---------|
| **A — Pytest** | Fast regression; **no** services, **no** Action 11 sign-off artifacts. |
| **B — Evidence pack** | **API / server contract** for three flows (curl) + **one** plugin capture (**B4**). See [What Track B guarantees](#what-track-b-guarantees) below. |

**WSL:** Run all commands **inside the same WSL distro** where services listen (`127.0.0.1:8091`, `:8089`). Use **Linux paths** for `MOTADATA_AIOPS_ROOT` (e.g. `/home/you/projects/motadata`, or clone under WSL—not only `C:\` paths unless you know Context Layer reads them).

### What Track B guarantees

| # | Scenario | Guaranteed by Track B? | Notes |
|---|----------|------------------------|--------|
| 1 | `/v1/ask` success + `trace_id` | **Yes** — **server/API** (curl), not the IDE | Plan-Gate + response; Context Layer log only for **export_evidence** (see B0). **No** IntelliJ `idea.log` line for this trace unless you run [Optional: full plugin parity](#optional-full-plugin-parity). |
| 2 | v1 failure → `/v0/ask` fallback (same `trace_id`) | **Yes** — **server/API** (curl + stub 404 simulates failed v1) | Same as above: proves Plan-Gate + payloads; **not** a second proof that the Kotlin bridge ran (that is covered by unit tests + optional plugin runs). |
| 3 | `explain_debug` / `EXPLAIN_DEBUG` | **Yes** — **server/API** (curl) | Plan-Gate stderr includes `EXPLAIN_DEBUG` / `[ASK]` lines; vLLM optional. **No** plugin log unless optional parity. |
| 4 | `ROUTING_DECISION` at runtime **and** response metadata (`trace_id`, `routing_mode`) | **Partially** | **B4** captures **one** Ask from the plugin + `ROUTING_DECISION`. Metadata is **cross-checked** from B1–B3 **response JSON** (same fields the plugin consumes). That is **not** the same as capturing plugin logs for traces 1–3. |

**Snippet checklist (per trace, when you need a complete pack):**

| Snippet | B1 | B2 | B3 | B4 (plugin proof) |
|--------|----|----|----|-------------------|
| Response JSON | `response_v1.json` + `artifact1_response.jq.txt` | `response_v0_fb.json` + `artifact2_response.jq.txt` | `response_explain.json` + `artifact3_response.jq.txt` | Copy `jq` outputs into `artifact4_metadata.txt`; plugin UI shows same fields |
| Plan-Gate stderr | `artifact1_plan_gate_runtime.log` | `artifact2_plan_gate_runtime.log` | `artifact3_plan_gate_runtime.log` | Grep same `trace_id` in `plan-gate.stderr.log` while plugin talks to Plan-Gate |
| Context / other runtime | Lines in `context-layer.stderr.log` around **export_evidence** (B1 only) | Usually empty for fallback (no Context call in B2 stub path) | Usually none for explain (POST is to Plan-Gate only) | Same as B1 if plugin exports evidence via Context |
| Plugin log (`ROUTING_DECISION`) | Only if you do [optional plugin parity](#optional-full-plugin-parity) | Same | Same | **`artifact4_plugin_ROUTING_DECISION.txt`** (required in B4) |

**Bottom line:** Track B **guarantees** end-to-end **server** behavior and **one** plugin log artifact for `ROUTING_DECISION`. It does **not** guarantee **four separate IntelliJ log traces** with matching `trace_id` lines for scenarios 1–3; add the optional section if sign-off requires that.

---

## Shared: checkout and env (once)

```bash
export MCODER="$HOME/Harshil-PoCs/m-coder"   # adjust if your clone differs
cd "$MCODER" && git fetch origin && git checkout feature/action-11-path-hardening-trace-routing && git pull

export PYTHONPATH="$MCODER${PYTHONPATH:+:$PYTHONPATH}"
export MOTADATA_AIOPS_ROOT="/absolute/linux/path/to/motadata-aiops"   # Motadata AIOps repo root (indexed workspace)
export EVID="$HOME/Harshil-PoCs/Action_11_Evidences"
export QUERY="${QUERY:-How are alerts correlated or escalated in this AIOps codebase?}"

mkdir -p "$EVID"
```

Optional: `pip install jsonschema pytest` (for Track A).

---

## Track A — Pytest only (optional)

```bash
cd "$MCODER"
export PYTHONPATH="$MCODER"
python3 -m pytest \
  runtime/tests/test_ask_service.py \
  runtime/tests/test_ask_v1_ingest.py \
  runtime/plan_gate_service/tests/test_plan_gate_request_logging.py \
  -v --tb=short 2>&1 | tee "$EVID/pytest-action11.txt"
```

Do **not** treat Track A alone as the four sign-off artifacts.

---

## Track B — One evidence procedure (sign-off)

You will use **three terminals** on the same machine. **Do not** run `verify_ask_path.sh` in addition to this track (it repeats export→v1 without `trace_id` and wastes effort).

**Ports:** Context Layer `8091`, Plan-Gate `8089` (defaults below).

### B0 — Start services

**Terminal 1 — Context Layer** (stderr → evidence file for B1 `export_evidence`)

```bash
cd "$MCODER"
export PYTHONPATH="$MCODER"
export MOTADATA_CONTEXT_LAYER_PORT=8091
rm -f "$EVID/context-layer.stderr.log"
python3 -m runtime.context_layer_service.app 2>&1 | tee "$EVID/context-layer.stderr.log"
```

**Terminal 2 — Plan-Gate (stderr → one log file for the whole run)**

```bash
cd "$MCODER"
export PYTHONPATH="$MCODER"
unset MOTADATA_EXPLAIN_VLLM_URL
export PLAN_GATE_PORT=8089
rm -f "$EVID/plan-gate.stderr.log"
python3 -m runtime.plan_gate_service.app 2>&1 | tee "$EVID/plan-gate.stderr.log"
```

Leave T1 and T2 running. Use **Terminal 3** for all curl/python below.

**Optional — Explain/Debug + vLLM:** If you want real `explain_debug` model calls, set `MOTADATA_EXPLAIN_VLLM_URL` (and start vLLM) **before** starting Plan-Gate in T2; otherwise explain may return `explain_debug.error` (still valid for `routing_mode`).

```bash
export CONTEXT_URL=http://127.0.0.1:8091
export PLAN_GATE_URL=http://127.0.0.1:8089
export WORKSPACE_ROOT="$MOTADATA_AIOPS_ROOT"
```

### B1 — Artifact 1: `/v1/ask` success + `trace_id`

```bash
curl -sS -o "$EVID/evidence.json" -X POST "$CONTEXT_URL/v1/export_evidence" \
  -H 'Content-Type: application/json' \
  -d "{\"workspace_root\":\"$WORKSPACE_ROOT\",\"query\":\"$QUERY\",\"top_k\":8}"

export TRACE1="trace-a11-$(date +%s)"
python3 - <<PY
import json, datetime, os
evid, q = os.environ["EVID"], os.environ["QUERY"]
ev = json.load(open(os.path.join(evid, "evidence.json"), encoding="utf-8"))
req = {
    "schema_version": "ask_request.v1.0",
    "request_id": "req-a11-1",
    "timestamp_utc": datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "query": q,
    "evidence_bundle": ev,
    "trace_id": os.environ["TRACE1"],
}
h = ev.get("workspace_identity_hash")
if h: req["expected_workspace_identity_hash"] = h
json.dump(req, open(os.path.join(evid, "ask_v1.json"), "w", encoding="utf-8"), indent=2)
print("TRACE1=", os.environ["TRACE1"])
PY

curl -sS -o "$EVID/response_v1.json" -X POST "$PLAN_GATE_URL/v1/ask" \
  -H 'Content-Type: application/json' --data-binary @"$EVID/ask_v1.json"

jq '{routing_mode, trace_id, ask_path: .evidence_first_meta.ask_path}' "$EVID/response_v1.json" | tee "$EVID/artifact1_response.jq.txt"
grep -E "PLAN_GATE request|\[ASK_V1\]|$TRACE1" "$EVID/plan-gate.stderr.log" | tail -20 | tee "$EVID/artifact1_plan_gate_runtime.log"
grep -E "$TRACE1|export_evidence|/v1/" "$EVID/context-layer.stderr.log" 2>/dev/null | tail -20 | tee "$EVID/artifact1_context_layer.log" || true
```

**Save (trace 1 — server):** `response_v1.json`, `artifact1_response.jq.txt`, `artifact1_plan_gate_runtime.log`, `artifact1_context_layer.log`. Plugin `ROUTING_DECISION` for this trace: **B4** or [optional plugin parity](#optional-full-plugin-parity).

### B2 — Artifact 2: v1 → v0 fallback (same trace chain)

Use a **404** on v1, then **same** `TRACE2` on `/v0/ask` to the **real** Plan-Gate (simulates plugin fallback; see [`RuntimeBridge.kt`](../../jetbrains-plugin/src/main/kotlin/ai/motadata/plugin/bridge/RuntimeBridge.kt)).

```bash
export TRACE2="trace-a11-fb-$(date +%s)"
python3 - <<PY
import json, os
ev = json.load(open(os.path.join(os.environ["EVID"], "evidence.json"), encoding="utf-8"))
req = {
    "schema_version": "ask_request.v1.0",
    "request_id": "req-a11-fb",
    "timestamp_utc": "2026-03-31T12:00:00Z",
    "query": "q",
    "evidence_bundle": ev,
    "trace_id": os.environ["TRACE2"],
}
if ev.get("workspace_identity_hash"):
    req["expected_workspace_identity_hash"] = ev["workspace_identity_hash"]
json.dump(req, open(os.path.join(os.environ["EVID"], "ask_v1_fb.json"), "w"), indent=2)
PY
```

**Stub (404 for v1):** Open **Terminal 4**, run and leave running:

```bash
python3 - <<'PY'
from http.server import HTTPServer, BaseHTTPRequestHandler
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(404); self.end_headers(); self.wfile.write(b'{}')
    def log_message(self, *a): pass
HTTPServer(("127.0.0.1", 28191), H).serve_forever()
PY
```

Back in **Terminal 3**:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:28191/v1/ask \
  -H 'Content-Type: application/json' --data-binary @"$EVID/ask_v1_fb.json"
# expect: 404
```

`Ctrl+C` in Terminal 4 to stop the stub. Then build **v0** ask with `evidence_first: true`, same `TRACE2`:

```bash
export REPO_FB="$(mktemp -d)"
mkdir -p "$REPO_FB/src" && echo x=1 > "$REPO_FB/src/x.py"
python3 - <<PY
import json, datetime, os
evid = os.environ["EVID"]
req = {
    "schema_version": "ask_request.v0.1",
    "request_id": "req-a11-fb",
    "timestamp_utc": datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "repo_root": os.environ["REPO_FB"],
    "revision": "r1",
    "query": "q",
    "evidence_first": True,
    "trace_id": os.environ["TRACE2"],
}
json.dump(req, open(os.path.join(evid, "ask_v0_fb.json"), "w"), indent=2)
PY

curl -sS -o "$EVID/response_v0_fb.json" -X POST "$PLAN_GATE_URL/v0/ask" \
  -H 'Content-Type: application/json' --data-binary @"$EVID/ask_v0_fb.json"
jq '{routing_mode, trace_id}' "$EVID/response_v0_fb.json" | tee "$EVID/artifact2_response.jq.txt"
grep -E "PLAN_GATE request|\[ASK\]|$TRACE2" "$EVID/plan-gate.stderr.log" | tail -15 | tee "$EVID/artifact2_plan_gate_runtime.log"
touch "$EVID/artifact2_context_layer.log"
# (B2 does not hit Context Layer for /v0/ask; file exists so the checklist is uniform.)
```

**Save (trace 2 — server):** `response_v0_fb.json`, `artifact2_response.jq.txt`, `artifact2_plan_gate_runtime.log`, `artifact2_context_layer.log` (empty). Plugin log for this fallback path: optional parity only.

### B3 — Artifact 3: `explain_debug`

Same Plan-Gate process in T2 (log still appends to `$EVID/plan-gate.stderr.log`). Temp repo + one POST:

```bash
export TRACE3="trace-a11-explain-$(date +%s)"
export REPO_EX="$(mktemp -d)"
mkdir -p "$REPO_EX/src" && printf '%s\n' 'def main(): return 42' > "$REPO_EX/src/main.py"

python3 - <<PY
import json, datetime, os
evid = os.environ["EVID"]
req = {
    "schema_version": "ask_request.v0.1",
    "request_id": "req-a11-explain",
    "timestamp_utc": datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "repo_root": os.environ["REPO_EX"],
    "revision": "r1",
    "query": "What does this do?",
    "task_type": "EXPLAIN_DEBUG",
    "selected_file": "src/main.py",
    "client_context": {"selection": "def main(): return 42"},
    "trace_id": os.environ["TRACE3"],
}
json.dump(req, open(os.path.join(evid, "ask_explain.json"), "w"), indent=2)
PY

curl -sS -o "$EVID/response_explain.json" -X POST "$PLAN_GATE_URL/v0/ask" \
  -H 'Content-Type: application/json' --data-binary @"$EVID/ask_explain.json"

jq '{routing_mode, trace_id, explain_keys: (.explain_debug | keys)}' "$EVID/response_explain.json" | tee "$EVID/artifact3_response.jq.txt"
grep -E "EXPLAIN_DEBUG|\[ASK\]|$TRACE3|PLAN_GATE request" "$EVID/plan-gate.stderr.log" | tail -25 | tee "$EVID/artifact3_plan_gate_runtime.log"
touch "$EVID/artifact3_context_layer.log"
```

**Save (trace 3 — server):** `response_explain.json`, `artifact3_*.txt`, `artifact3_context_layer.log` (empty unless you route explain via Context in a custom setup).

### B4 — Plugin proof: `ROUTING_DECISION` + metadata cross-check

**Metadata (from B1–B3 responses):** Copy `artifact1_response.jq.txt`, `artifact2_response.jq.txt`, `artifact3_response.jq.txt` into **`$EVID/artifact4_metadata.txt`** (proves `trace_id` + `routing_mode` on **curl** responses the plugin is meant to parse).

**Plugin (required for trace 4):** In **IntelliJ** (host must reach Plan-Gate):

1. Enable evidence-first (`-Dmotadata.ask.evidence_first=true` or env per product docs).
2. Point the plugin at `http://127.0.0.1:8089` (or WSL IP from Windows if services run in WSL).
3. Run **Ask** once against the Motadata AIOps workspace.
4. **Help → Diagnostic Tool → Show Log** → search `ROUTING_DECISION` → save the block to **`$EVID/artifact4_plugin_ROUTING_DECISION.txt`**.
5. Optional: grep **`plan-gate.stderr.log`** for the same run’s `trace_id` / `PLAN_GATE request` and append to **`$EVID/artifact4_plan_gate_snippet.txt`**.

That completes **B4** (one real plugin line + metadata cross-check). It does **not** by itself prove plugin-driven traces 1–3; use optional parity below if required.

### Optional: full plugin parity

Run only if sign-off needs **`ROUTING_DECISION` / idea.log snippets for the same scenarios** as B1–B3 (three extra IDE runs, plus log harvest). The IDE may generate its own `trace_id`; use the value shown in the **response** or in `ROUTING_DECISION` JSON, then grep Plan-Gate with that id.

1. **v1 success:** Evidence-first Ask that completes `/v1/ask` → save `ROUTING_DECISION` + any error/success lines to `$EVID/parity1_plugin.txt`; grep Plan-Gate + Context logs with the observed `trace_id`.
2. **Fallback:** Temporarily point the plugin’s v1 base URL at the **stub** (or break v1) so the bridge falls back to `/v0/ask` → `$EVID/parity2_plugin.txt` + matching Plan-Gate grep.
3. **Explain:** Run an Ask / explain flow that hits `EXPLAIN_DEBUG` → `$EVID/parity3_plugin.txt` + Plan-Gate grep.

These steps are **not** automated in this repo; they are environment-specific.

### B5 — Gradle (compile only)

```bash
cd "$MCODER/jetbrains-plugin"
./gradlew compileKotlin compileTestKotlin
```

If `./gradlew test` fails with `Index: 1, Size: 1`, ignore for sign-off; it is a [known IntelliJ Platform Gradle plugin issue](https://github.com/JetBrains/intellij-platform-gradle-plugin/issues/1891). Run unit tests **inside the IDE** if needed.

---

## Stop services

`Ctrl+C` in Terminal 1 and Terminal 2 when finished.

---

## PR

Open a PR from `feature/action-11-path-hardening-trace-routing` to your target branch on GitHub (or your host).

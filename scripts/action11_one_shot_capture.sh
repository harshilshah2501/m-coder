#!/usr/bin/env bash
# Action 11 — one-shot: Track A (pytest) + Track B (curl B1–B3) + artifact layout for B4 (manual IDE).
# Usage:
#   export MCODER="$HOME/Harshil-PoCs/m-coder"
#   export MOTADATA_AIOPS_ROOT="/home/you/Projects/Motadata/"
#   ./scripts/action11_one_shot_capture.sh
#
# Optional env:
#   ACTION_11_EVID   — explicit evidence dir (default: ~/Harshil-PoCs/Action-11-artifacts-YYYYMMDD-HHMMSS)
#   QUERY            — B1 export query
#   SKIP_TRACK_A=1   — skip pytest
#   SKIP_TRACK_B=1   — skip services + curl (only Track A + layout)
#   RUN_GRADLE=1     — run jetbrains-plugin compileKotlin compileTestKotlin after Track B
#   KEEP_SERVICES=1  — do not stop Context Layer / Plan-Gate on exit (default: stop them)

set -euo pipefail

MCODER="${MCODER:-$HOME/Harshil-PoCs/m-coder}"
export MCODER
cd "$MCODER" || { echo "ERROR: MCODER not found: $MCODER" >&2; exit 1; }

export PYTHONPATH="$MCODER${PYTHONPATH:+:$PYTHONPATH}"
export MOTADATA_AIOPS_ROOT="${MOTADATA_AIOPS_ROOT:-/home/harshil/Projects/Motadata/}"
export QUERY="${QUERY:-How are alerts correlated or escalated in this AIOps codebase?}"
export CONTEXT_URL="${CONTEXT_URL:-http://127.0.0.1:8091}"
export PLAN_GATE_URL="${PLAN_GATE_URL:-http://127.0.0.1:8089}"
export WORKSPACE_ROOT="$MOTADATA_AIOPS_ROOT"

TS="$(date +%Y%m%d-%H%M%S)"
export EVID="${ACTION_11_EVID:-$HOME/Harshil-PoCs/Action-11-artifacts-${TS}}"
mkdir -p "$EVID"

CL_PID=""
PG_PID=""
STUB_PID=""

cleanup() {
  if [[ "${KEEP_SERVICES:-}" == "1" ]]; then
    return 0
  fi
  [[ -n "$STUB_PID" ]] && kill "$STUB_PID" 2>/dev/null || true
  [[ -n "$CL_PID" ]] && kill "$CL_PID" 2>/dev/null || true
  [[ -n "$PG_PID" ]] && kill "$PG_PID" 2>/dev/null || true
  wait "$STUB_PID" 2>/dev/null || true
  wait "$CL_PID" 2>/dev/null || true
  wait "$PG_PID" 2>/dev/null || true
}
trap cleanup EXIT

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "ERROR: need '$1' in PATH" >&2; exit 1; }
}

wait_http() {
  local url="$1" name="$2" max="${3:-60}"
  local i
  for i in $(seq 1 "$max"); do
    if curl -sf "$url" >/dev/null 2>&1; then
      echo "OK $name ($url)"
      return 0
    fi
    sleep 1
  done
  echo "ERROR: timeout waiting for $name $url" >&2
  return 1
}

echo "=== Action 11 capture ==="
echo "EVID=$EVID"
echo "MCODER=$MCODER"
echo "MOTADATA_AIOPS_ROOT=$MOTADATA_AIOPS_ROOT"
echo

# ── Track A ──────────────────────────────────────────────────────────────────
if [[ "${SKIP_TRACK_A:-}" != "1" ]]; then
  need_cmd python3
  echo "=== Track A: pytest ==="
  export PYTHONPATH="$MCODER"
  python3 -m pytest \
    runtime/tests/test_ask_service.py \
    runtime/tests/test_ask_v1_ingest.py \
    runtime/plan_gate_service/tests/test_plan_gate_request_logging.py \
    -v --tb=short 2>&1 | tee "$EVID/pytest-action11.txt"
  echo "Wrote $EVID/pytest-action11.txt"
  echo
else
  echo "=== Track A skipped (SKIP_TRACK_A=1) ==="
  echo
fi

if [[ "${SKIP_TRACK_B:-}" == "1" ]]; then
  echo "SKIP_TRACK_B=1 — not starting services or curl. EVID=$EVID"
  exit 0
fi

need_cmd curl
need_cmd jq
need_cmd python3

# ── Track B0: services (single log files for whole run) ─────────────────────
rm -f "$EVID/context-layer.stderr.log" "$EVID/plan-gate.stderr.log"
export MOTADATA_CONTEXT_LAYER_PORT=8091
unset MOTADATA_EXPLAIN_VLLM_URL
export PLAN_GATE_PORT=8089

echo "=== Track B0: Context Layer :8091 ==="
python3 -m runtime.context_layer_service.app >>"$EVID/context-layer.stderr.log" 2>&1 &
CL_PID=$!

echo "=== Track B0: Plan-Gate :8089 ==="
python3 -m runtime.plan_gate_service.app >>"$EVID/plan-gate.stderr.log" 2>&1 &
PG_PID=$!

wait_http "${CONTEXT_URL}/healthz" "Context Layer" 90
wait_http "${PLAN_GATE_URL}/healthz" "Plan-Gate" 90

# ── B1 ───────────────────────────────────────────────────────────────────────
echo "=== B1: /v1/ask (curl) ==="
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
if h:
    req["expected_workspace_identity_hash"] = h
json.dump(req, open(os.path.join(evid, "ask_v1.json"), "w", encoding="utf-8"), indent=2)
print("TRACE1=", os.environ["TRACE1"])
PY

curl -sS -o "$EVID/response_v1.json" -X POST "$PLAN_GATE_URL/v1/ask" \
  -H 'Content-Type: application/json' --data-binary @"$EVID/ask_v1.json"

if python3 -c "import json,sys; d=json.load(open(sys.argv[1])); sys.exit(1 if d.get('error') else 0)" "$EVID/response_v1.json" 2>/dev/null; then
  echo "B1: response_v1.json OK (no top-level error)"
else
  echo "WARN: response_v1.json may contain an error — check $EVID/response_v1.json" >&2
fi

jq '{routing_mode, trace_id, ask_path: .evidence_first_meta.ask_path}' "$EVID/response_v1.json" | tee "$EVID/artifact1_response.jq.txt"
grep -E "PLAN_GATE request|\[ASK_V1\]|${TRACE1}" "$EVID/plan-gate.stderr.log" | tail -20 | tee "$EVID/artifact1_plan_gate_runtime.log" || true
grep -E "${TRACE1}|export_evidence|/v1/" "$EVID/context-layer.stderr.log" 2>/dev/null | tail -20 | tee "$EVID/artifact1_context_layer.log" || true

# ── B2: stub 404 + v0 fallback ───────────────────────────────────────────────
echo "=== B2: v1 stub 404 + /v0/ask ==="
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

python3 - <<'PY' &
from http.server import HTTPServer, BaseHTTPRequestHandler
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(404); self.end_headers(); self.wfile.write(b'{}')
    def log_message(self, *a): pass
HTTPServer(("127.0.0.1", 28191), H).serve_forever()
PY
STUB_PID=$!
sleep 0.4

curl -sS -o /dev/null -w "stub_v1_http=%{http_code}\n" -X POST http://127.0.0.1:28191/v1/ask \
  -H 'Content-Type: application/json' --data-binary @"$EVID/ask_v1_fb.json"
kill "$STUB_PID" 2>/dev/null || true
wait "$STUB_PID" 2>/dev/null || true
STUB_PID=""

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
grep -E "PLAN_GATE request|\[ASK\]|${TRACE2}" "$EVID/plan-gate.stderr.log" | tail -15 | tee "$EVID/artifact2_plan_gate_runtime.log" || true
: >"$EVID/artifact2_context_layer.log"

# ── B3 ───────────────────────────────────────────────────────────────────────
echo "=== B3: EXPLAIN_DEBUG (curl) ==="
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
grep -E "EXPLAIN_DEBUG|\[ASK\]|${TRACE3}|PLAN_GATE request" "$EVID/plan-gate.stderr.log" | tail -25 | tee "$EVID/artifact3_plan_gate_runtime.log" || true
: >"$EVID/artifact3_context_layer.log"

# ── artifact4_metadata (curl jq outputs) ─────────────────────────────────────
echo "=== artifact4_metadata.txt (B1–B3 jq) ==="
cat "$EVID/artifact1_response.jq.txt" "$EVID/artifact2_response.jq.txt" "$EVID/artifact3_response.jq.txt" >"$EVID/artifact4_metadata.txt"

# ── B4 instructions (IDE cannot be scripted here) ─────────────────────────────
cat >"$EVID/B4_MANUAL_NEXT_STEPS.txt" <<EOF
Action 11 — B4 (plugin) — run while Plan-Gate is still up (or restart B0 services first).

Traces from this script run (for grep correlation):
  TRACE1=$TRACE1
  TRACE2=$TRACE2
  TRACE3=$TRACE3

1) IntelliJ: install/build plugin 0.2.6+ from $MCODER/jetbrains-plugin
2) VM options: -Dmotadata.ask.evidence_first=true
   Plan-Gate URL must reach: $PLAN_GATE_URL
3) Ask Motadata AI once against: $MOTADATA_AIOPS_ROOT
4) In idea.log, search: ROUTING_DECISION
   Save the block to: $EVID/artifact4_plugin_ROUTING_DECISION.txt
5) Optional: append Plan-Gate lines for your plugin trace_id:
   grep -E 'PLAN_GATE request|trace_id=' $EVID/plan-gate.stderr.log >> $EVID/artifact4_plan_gate_snippet.txt
   (Run Ask first, then copy plan-gate.stderr.log again if you need a fresh tail — or KEEP_SERVICES=1 and grep after B4.)

idea.log location (typical Linux backend):
  ~/.cache/JetBrains/IntelliJIdea*/log/idea.log
EOF
echo "Wrote $EVID/B4_MANUAL_NEXT_STEPS.txt"

cat >"$EVID/RUN_SUMMARY.txt" <<EOF
EVID=$EVID
TRACE1=$TRACE1
TRACE2=$TRACE2
TRACE3=$TRACE3
CONTEXT_URL=$CONTEXT_URL
PLAN_GATE_URL=$PLAN_GATE_URL
MOTADATA_AIOPS_ROOT=$MOTADATA_AIOPS_ROOT
Finished: $(date -Iseconds)
EOF

# ── Optional Gradle ──────────────────────────────────────────────────────────
if [[ "${RUN_GRADLE:-}" == "1" ]]; then
  echo "=== Gradle: compileKotlin compileTestKotlin ==="
  ( cd "$MCODER/jetbrains-plugin" && ./gradlew compileKotlin compileTestKotlin ) 2>&1 | tee "$EVID/gradle_compile.txt" || true
fi

echo
echo "=== Done ==="
echo "Artifacts: $EVID"
echo "  pytest-action11.txt, context-layer.stderr.log, plan-gate.stderr.log"
echo "  response_v1.json, response_v0_fb.json, response_explain.json"
echo "  artifact[1-4]_*.txt (as applicable), B4_MANUAL_NEXT_STEPS.txt"
echo
echo "B4: follow $EVID/B4_MANUAL_NEXT_STEPS.txt (IntelliJ), then optionally:"
echo "  KEEP_SERVICES=1 ./scripts/action11_one_shot_capture.sh   # not supported in same run — for B4 run IDE while services stay up, or re-run B0 only"
echo
echo "Services will stop on exit (KEEP_SERVICES unset). Export KEEP_SERVICES=1 to leave :8091/:8089 running for manual B4."

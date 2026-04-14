#!/usr/bin/env bash
#
# Verify evidence-first Ask path end-to-end from WSL:
#   1) POST /v1/export_evidence (Context Layer)
#   2) POST /v1/ask (Plan-Gate)
#   3) Print compact PASS/FAIL diagnostics
#
# Usage:
#   WORKSPACE_ROOT=/root/Harshil-PoCs/Motadata \
#   QUERY='How does alert correlation work in this repo?' \
#   bash runtime/scripts/verify_ask_path.sh
#
# Optional env:
#   CONTEXT_URL=http://127.0.0.1:8091
#   PLAN_GATE_URL=http://127.0.0.1:8089
#   TOP_K=8
#   CURL_MAX_TIME_SEC — if set, curl --max-time for export and ask (omit for no limit)
#

set -euo pipefail

CONTEXT_URL="${CONTEXT_URL:-http://127.0.0.1:8091}"
PLAN_GATE_URL="${PLAN_GATE_URL:-http://127.0.0.1:8089}"
TOP_K="${TOP_K:-8}"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-}"
QUERY="${QUERY:-}"
CURL_MAX_TIME_SEC="${CURL_MAX_TIME_SEC:-}"
if [[ -n "${CURL_MAX_TIME_SEC}" ]]; then
  CURL_MAX=(--max-time "${CURL_MAX_TIME_SEC}")
else
  CURL_MAX=()
fi

info() { echo "[INFO]  $*"; }
ok()   { echo "[OK]    $*"; }
warn() { echo "[WARN]  $*"; }
fail() { echo "[FAIL]  $*" >&2; exit 1; }

if [[ -z "$WORKSPACE_ROOT" ]]; then
  fail "WORKSPACE_ROOT is required (Linux path visible to WSL Context Layer)."
fi
if [[ -z "$QUERY" ]]; then
  fail "QUERY is required."
fi
if ! command -v curl >/dev/null 2>&1; then
  fail "curl not found."
fi
if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 not found."
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
EVIDENCE_JSON="$TMP_DIR/evidence.json"
ASK_REQ_JSON="$TMP_DIR/ask_v1.json"
ASK_RESP_JSON="$TMP_DIR/ask_v1_response.json"

info "Context URL:   $CONTEXT_URL"
info "Plan-Gate URL: $PLAN_GATE_URL"
info "Workspace:     $WORKSPACE_ROOT"
info "Query:         $QUERY"
info "top_k:         $TOP_K"
echo ""

info "Step 1/3: POST /v1/export_evidence"
EVIDENCE_HTTP_CODE="$(curl -sS -o "$EVIDENCE_JSON" -w "%{http_code}" \
  "${CURL_MAX[@]}" \
  -X POST "$CONTEXT_URL/v1/export_evidence" \
  -H 'Content-Type: application/json' \
  -d "{\"workspace_root\":\"$WORKSPACE_ROOT\",\"query\":\"$QUERY\",\"top_k\":$TOP_K}")"

if [[ "$EVIDENCE_HTTP_CODE" != "200" ]]; then
  echo ""
  cat "$EVIDENCE_JSON" 2>/dev/null || true
  fail "/v1/export_evidence returned HTTP $EVIDENCE_HTTP_CODE"
fi

python3 - "$EVIDENCE_JSON" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p, "r", encoding="utf-8"))
entries = d.get("entries") or []
print(f"[OK]    /v1/export_evidence HTTP 200")
print(f"[INFO]  schema_hint={d.get('schema_hint')}")
print(f"[INFO]  entries_count={len(entries)}")
print(f"[INFO]  workspace_identity_hash={d.get('workspace_identity_hash')}")
if entries:
    top = [e.get("relative_path") for e in entries[:5]]
    print(f"[INFO]  top_paths={top}")
else:
    print("[WARN]  entries are empty for this query")
PY

echo ""
info "Step 2/3: Build ask_request.v1.0 payload"
python3 - "$EVIDENCE_JSON" "$ASK_REQ_JSON" "$QUERY" <<'PY'
import datetime, json, sys, uuid
ev_path, out_path, query = sys.argv[1], sys.argv[2], sys.argv[3]
ev = json.load(open(ev_path, "r", encoding="utf-8"))
_ts = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
req = {
    "schema_version": "ask_request.v1.0",
    "request_id": str(uuid.uuid4()),
    "timestamp_utc": _ts,
    "query": query,
    "evidence_bundle": ev,
}
ws_hash = ev.get("workspace_identity_hash")
if ws_hash:
    req["expected_workspace_identity_hash"] = ws_hash
json.dump(req, open(out_path, "w", encoding="utf-8"))
print("[OK]    ask_request.v1.0 payload ready")
PY

echo ""
info "Step 3/3: POST /v1/ask"
ASK_HTTP_CODE="$(curl -sS -o "$ASK_RESP_JSON" -w "%{http_code}" \
  "${CURL_MAX[@]}" \
  -X POST "$PLAN_GATE_URL/v1/ask" \
  -H 'Content-Type: application/json' \
  --data-binary "@$ASK_REQ_JSON")"

if [[ "$ASK_HTTP_CODE" != "200" ]]; then
  echo ""
  cat "$ASK_RESP_JSON" 2>/dev/null || true
  fail "/v1/ask returned HTTP $ASK_HTTP_CODE"
fi

python3 - "$ASK_RESP_JSON" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p, "r", encoding="utf-8"))
meta = d.get("evidence_first_meta") or {}
ask_path = meta.get("ask_path")
ctx = d.get("context_bundle") or {}
files = ctx.get("files") or []
plan = d.get("plan_summary") or {}
steps = plan.get("steps") or []
notes = plan.get("notes") or []
print("[OK]    /v1/ask HTTP 200")
print(f"[INFO]  ask_path={ask_path}")
print(f"[INFO]  context_files_count={len(files)}")
print(f"[INFO]  plan_steps_count={len(steps)}")
if notes:
    print(f"[INFO]  plan_notes={notes}")
if ask_path != "v1_evidence":
    print("[WARN]  ask_path is not v1_evidence; verify plugin/runtime path.")
if len(files) == 0:
    print("[WARN]  context_bundle.files is empty.")
if len(steps) == 0:
    print("[WARN]  plan_summary.steps is empty.")
print("[OK]    verification complete")
PY

echo ""
ok "Done. Artifacts were validated via /v1/export_evidence and /v1/ask."

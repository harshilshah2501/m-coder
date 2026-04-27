#!/usr/bin/env bash
#
# Deterministic packaging pipeline for WSL Context Layer:
#  1) Build wheel
#  2) Install wheel in isolated smoke venv
#  3) Start service and validate /healthz, /version
#  4) Run POST /v1/export_evidence sanity check
#  5) (Optional) verify Plan-Gate /version advertises ask_request_v1
#
# Usage:
#   bash packaging/motadata-context-layer/build_and_verify_wsl_context_layer.sh
#
# Optional env:
#   WORKSPACE_ROOT=/root/Harshil-PoCs/Motadata
#   SANITY_QUERY='How does alert correlation work in this repo?'
#   TOP_K=8
#   CONTEXT_LAYER_SMOKE_PORT=18091
#   PLAN_GATE_URL=http://127.0.0.1:8089   # optional compatibility check
#   DEPLOY_TARGET=root@172.30.127.150      # optional wheel copy target
#   DEPLOY_PATH=/root/Harshil-PoCs/Motadata
#   DEPLOY_METHOD=scp                       # scp (default) or rsync
#   DEPLOY_SSH_OPTS='-o StrictHostKeyChecking=no'
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PKG_DIR="$SCRIPT_DIR"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DIST_DIR="$PKG_DIR/dist"
BUILD_VENV="$PKG_DIR/.venv-build-pipeline"
SMOKE_VENV="$PKG_DIR/.venv-smoke-pipeline"
TMP_DIR="$(mktemp -d)"
HEALTH_JSON_FILE="$TMP_DIR/health.json"
VERSION_JSON_FILE="$TMP_DIR/version.json"
EVIDENCE_JSON_FILE="$TMP_DIR/evidence.json"
PLAN_GATE_VERSION_FILE="$TMP_DIR/plan_gate_version.json"

WORKSPACE_ROOT="${WORKSPACE_ROOT:-$REPO_ROOT}"
SANITY_QUERY="${SANITY_QUERY:-How does alert correlation work in this repo?}"
TOP_K="${TOP_K:-8}"
SMOKE_PORT="${CONTEXT_LAYER_SMOKE_PORT:-18091}"
PLAN_GATE_URL="${PLAN_GATE_URL:-}"
SMOKE_BASE_URL="http://127.0.0.1:${SMOKE_PORT}"
SMOKE_LOG="$PKG_DIR/context-layer-smoke.log"
SMOKE_STDERR="$PKG_DIR/context-layer-smoke.stderr.log"
DEPLOY_TARGET="${DEPLOY_TARGET:-}"
DEPLOY_PATH="${DEPLOY_PATH:-/root/Harshil-PoCs/Motadata}"
DEPLOY_METHOD="${DEPLOY_METHOD:-scp}"
DEPLOY_SSH_OPTS="${DEPLOY_SSH_OPTS:-}"

info() { echo "[INFO]  $*"; }
step() { echo "[STEP]  $*"; }
ok()   { echo "[OK]    $*"; }
warn() { echo "[WARN]  $*"; }
fail() { echo "[FAIL]  $*" >&2; exit 1; }

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

cleanup() {
    rm -rf "$TMP_DIR" >/dev/null 2>&1 || true
    if [[ -n "${SMOKE_PID:-}" ]] && kill -0 "$SMOKE_PID" >/dev/null 2>&1; then
        kill "$SMOKE_PID" >/dev/null 2>&1 || true
        wait "$SMOKE_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

require_cmd python3
require_cmd curl

# curl to localhost must not go through HTTP(S)_PROXY (often yields empty reply / exit 52 on CI).
curl_local() {
    curl -4 --noproxy '*' "$@"
}

# Wait until GET returns HTTP 200 with a body (handles slow startup; retries empty reply / refused).
wait_http_ready() {
    local url=$1
    local out=$2
    local label=$3
    local max_attempts="${4:-90}"
    local i=0
    local err
    err="$(mktemp)"
    while [[ $i -lt $max_attempts ]]; do
        if curl_local -fsS "$url" -o "$out" 2>"$err"; then
            rm -f "$err"
            return 0
        fi
        sleep 1
        i=$((i + 1))
    done
    warn "curl failed for $label after ${max_attempts}s; last stderr:"
    cat "$err" >&2 || true
    rm -f "$err"
    return 1
}

step "Preflight checks"
[[ -d "$REPO_ROOT/runtime/context_layer_service" ]] || fail "runtime/context_layer_service not found under $REPO_ROOT"
[[ -d "$REPO_ROOT/runtime/layer5" ]] || fail "runtime/layer5 not found under $REPO_ROOT"
ok "Repo layout looks valid"

step "Build wheel in isolated build venv"
python3 -m venv "$BUILD_VENV"
"$BUILD_VENV/bin/pip" install -U pip wheel build >/dev/null
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"
(
    cd "$PKG_DIR"
    "$BUILD_VENV/bin/python" -m build --wheel -o dist
)
WHEEL_PATH="$(ls -1t "$DIST_DIR"/motadata_context_layer-*.whl | head -n 1 || true)"
[[ -n "$WHEEL_PATH" ]] || fail "No wheel produced in $DIST_DIR"
ok "Wheel built: $WHEEL_PATH"

if [[ -n "$DEPLOY_TARGET" ]]; then
    step "Optional deploy copy to ${DEPLOY_TARGET}:${DEPLOY_PATH} via ${DEPLOY_METHOD}"
    case "$DEPLOY_METHOD" in
        scp)
            require_cmd scp
            scp $DEPLOY_SSH_OPTS "$WHEEL_PATH" "${DEPLOY_TARGET}:${DEPLOY_PATH}/"
            ;;
        rsync)
            require_cmd rsync
            rsync -avz -e "ssh $DEPLOY_SSH_OPTS" "$WHEEL_PATH" "${DEPLOY_TARGET}:${DEPLOY_PATH}/"
            ;;
        *)
            fail "DEPLOY_METHOD must be 'scp' or 'rsync' (got: $DEPLOY_METHOD)"
            ;;
    esac
    ok "Wheel copied to ${DEPLOY_TARGET}:${DEPLOY_PATH}/$(basename "$WHEEL_PATH")"
fi

step "Install wheel in isolated smoke venv"
python3 -m venv "$SMOKE_VENV"
"$SMOKE_VENV/bin/pip" install -U pip >/dev/null
"$SMOKE_VENV/bin/pip" install "$WHEEL_PATH" >/dev/null
ok "Wheel installed into smoke venv"

step "Preflight: bind ${SMOKE_PORT} on 127.0.0.1 (must be free)"
if ! python3 - "$SMOKE_PORT" <<'PY'
import socket
import sys
port = int(sys.argv[1])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(("127.0.0.1", port))
finally:
    s.close()
PY
then
    warn "Port ${SMOKE_PORT} is not available (often: a previous Context Layer smoke is still bound)."
    warn "Free it: ss -tlnp | grep :${SMOKE_PORT}  — or use CONTEXT_LAYER_SMOKE_PORT=<other> for this script."
    fail "Preflight bind failed for 127.0.0.1:${SMOKE_PORT}"
fi
ok "Port ${SMOKE_PORT} is free"

step "Start Context Layer smoke service on ${SMOKE_BASE_URL}"
: > "$SMOKE_STDERR"
MOTADATA_CONTEXT_LAYER_HOST=127.0.0.1 \
MOTADATA_CONTEXT_LAYER_PORT="$SMOKE_PORT" \
MOTADATA_CONTEXT_LAYER_LOG_LEVEL=DEBUG \
MOTADATA_CONTEXT_LAYER_LOG_PATH="$SMOKE_LOG" \
"$SMOKE_VENV/bin/motadata-context-layer" > /dev/null 2>>"$SMOKE_STDERR" &
SMOKE_PID=$!
sleep 1
if ! kill -0 "$SMOKE_PID" >/dev/null 2>&1; then
    warn "Smoke process not running; stderr from this run ($SMOKE_STDERR):"
    tail -n 80 "$SMOKE_STDERR" 2>/dev/null || true
    warn "Smoke file log tail ($SMOKE_LOG) may be from older runs:"
    tail -n 80 "$SMOKE_LOG" 2>/dev/null || true
    fail "Smoke service exited immediately. See $SMOKE_STDERR (traceback / bind errors) and $SMOKE_LOG"
fi

step "Validate /healthz and /version"
if ! wait_http_ready "$SMOKE_BASE_URL/healthz" "$HEALTH_JSON_FILE" "GET /healthz"; then
    warn "Context Layer smoke log (tail):"
    tail -n 120 "$SMOKE_LOG" 2>/dev/null || true
    fail "/healthz did not become ready. See log: $SMOKE_LOG"
fi
if ! wait_http_ready "$SMOKE_BASE_URL/version" "$VERSION_JSON_FILE" "GET /version"; then
    warn "Context Layer smoke log (tail):"
    tail -n 120 "$SMOKE_LOG" 2>/dev/null || true
    fail "/version did not become ready. See log: $SMOKE_LOG"
fi
python3 - "$HEALTH_JSON_FILE" "$VERSION_JSON_FILE" <<'PY'
import json
import sys
health = json.load(open(sys.argv[1], "r", encoding="utf-8"))
version = json.load(open(sys.argv[2], "r", encoding="utf-8"))
assert health.get("status") == "ok", f"health.status={health.get('status')!r}"
assert health.get("service") == "motadata_context_layer", f"health.service={health.get('service')!r}"
assert version.get("evidence_schema_hint") == "layer5.evidence_bundle.v1", \
    f"version.evidence_schema_hint={version.get('evidence_schema_hint')!r}"
endpoints = version.get("endpoints") or []
assert "POST /v1/export_evidence" in endpoints, f"endpoints={endpoints!r}"
print("[OK]    /healthz + /version checks passed")
PY

step "Run /v1/export_evidence sanity check"
curl_local -sS -X POST "$SMOKE_BASE_URL/v1/export_evidence" \
  -H 'Content-Type: application/json' \
  -d "{\"workspace_root\":\"$WORKSPACE_ROOT\",\"query\":\"$SANITY_QUERY\",\"top_k\":$TOP_K}" \
  > "$EVIDENCE_JSON_FILE"
python3 - "$EVIDENCE_JSON_FILE" <<'PY'
import json
import sys
payload = json.load(open(sys.argv[1], "r", encoding="utf-8"))
assert payload.get("schema_hint") == "layer5.evidence_bundle.v1", \
    f"schema_hint={payload.get('schema_hint')!r}"
entries = payload.get("entries")
if not isinstance(entries, list):
    raise AssertionError(f"entries type={type(entries)!r}")
print(f"[OK]    /v1/export_evidence schema validated; entries_count={len(entries)}")
if entries:
    top = [e.get("relative_path") for e in entries[:3]]
    print(f"[INFO]  top_paths={top}")
else:
    print("[WARN]  entries_count=0 (query may be too broad for this workspace)")
PY

if [[ -n "$PLAN_GATE_URL" ]]; then
    step "Optional Plan-Gate compatibility check: $PLAN_GATE_URL/version"
    curl_local -sS "$PLAN_GATE_URL/version" > "$PLAN_GATE_VERSION_FILE"
    python3 - "$PLAN_GATE_VERSION_FILE" <<'PY'
import json
import sys
payload = json.load(open(sys.argv[1], "r", encoding="utf-8"))
schemas = (payload.get("supported_schemas") or {})
assert schemas.get("ask_request_v1") == "v1.0", f"ask_request_v1={schemas.get('ask_request_v1')!r}"
print("[OK]    Plan-Gate advertises ask_request_v1=v1.0")
PY
fi

echo ""
ok "WSL Context Layer package pipeline PASSED"
echo "  wheel:    $WHEEL_PATH"
echo "  smoke log:$SMOKE_LOG"
echo "  base url: $SMOKE_BASE_URL"


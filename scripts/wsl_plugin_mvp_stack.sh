#!/usr/bin/env bash
# Unified WSL-side launcher for JetBrains plugin MVP validation.
#
# Responsibilities:
# - Start/stop Context Layer on WSL
# - Start/stop SSH tunnel to remote Plan-Gate/vLLM (optional)
# - Validate health, /version, git_commit parity, and endpoint compatibility
#
# Usage:
#   ./scripts/wsl_plugin_mvp_stack.sh up
#   ./scripts/wsl_plugin_mvp_stack.sh check
#   ./scripts/wsl_plugin_mvp_stack.sh status
#   ./scripts/wsl_plugin_mvp_stack.sh down
#   ./scripts/wsl_plugin_mvp_stack.sh restart
#
# Common env:
#   MOTADATA_ROOT=/home/you/Projects/Motadata
#   CONTEXT_URL=http://127.0.0.1:8091
#   PLAN_GATE_URL=http://127.0.0.1:8089
#
# Tunnel env (for remote GPU Plan-Gate):
#   ENABLE_SSH_TUNNEL=1
#   TUNNEL_USER=ubuntu
#   TUNNEL_HOST=10.0.0.15
#   TUNNEL_SSH_KEY=~/.ssh/id_ed25519      # optional
#   LOCAL_PLAN_GATE_PORT=8089             # defaults to PLAN_GATE_URL port
#   REMOTE_PLAN_GATE_HOST=127.0.0.1
#   REMOTE_PLAN_GATE_PORT=8089
#   LOCAL_VLLM_PORT=8000                  # default: forward vLLM with Plan-Gate; set 0 to disable
#   REMOTE_VLLM_HOST=127.0.0.1
#   REMOTE_VLLM_PORT=8000

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${M_CODER_REPO_ROOT:-$SCRIPT_DIR/..}" && pwd)"
RUN_DIR="$REPO_ROOT/runtime/.run"
mkdir -p "$RUN_DIR"

CONTEXT_PID_FILE="$RUN_DIR/wsl_context_layer.pid"
TUNNEL_PID_FILE="$RUN_DIR/wsl_plan_gate_tunnel.pid"
CONTEXT_LOG="$RUN_DIR/wsl_context_layer.log"
TUNNEL_LOG="$RUN_DIR/wsl_plan_gate_tunnel.log"
CONTEXT_META_FILE="$RUN_DIR/wsl_context_layer.meta"

CONTEXT_URL="${CONTEXT_URL:-http://127.0.0.1:8091}"
PLAN_GATE_URL="${PLAN_GATE_URL:-http://127.0.0.1:8089}"
MOTADATA_ROOT="${MOTADATA_ROOT:-}"

ENABLE_SSH_TUNNEL="${ENABLE_SSH_TUNNEL:-0}"
TUNNEL_USER="${TUNNEL_USER:-}"
TUNNEL_HOST="${TUNNEL_HOST:-}"
TUNNEL_TARGET="${TUNNEL_TARGET:-}"
TUNNEL_SSH_KEY="${TUNNEL_SSH_KEY:-}"
LOCAL_PLAN_GATE_PORT="${LOCAL_PLAN_GATE_PORT:-}"
REMOTE_PLAN_GATE_HOST="${REMOTE_PLAN_GATE_HOST:-127.0.0.1}"
REMOTE_PLAN_GATE_PORT="${REMOTE_PLAN_GATE_PORT:-8089}"
LOCAL_VLLM_PORT="${LOCAL_VLLM_PORT:-8000}"
REMOTE_VLLM_HOST="${REMOTE_VLLM_HOST:-127.0.0.1}"
REMOTE_VLLM_PORT="${REMOTE_VLLM_PORT:-8000}"

ALLOW_COMMIT_MISMATCH="${ALLOW_COMMIT_MISMATCH:-0}"
REQUIRE_CONTEXT_GIT_COMMIT="${REQUIRE_CONTEXT_GIT_COMMIT:-0}"
AUTO_ALIGN_CONTEXT_COMMIT="${AUTO_ALIGN_CONTEXT_COMMIT:-1}"
CONTEXT_PORT_RECLAIM="${CONTEXT_PORT_RECLAIM:-1}"

info() { echo "[INFO] $*"; }
ok() { echo "[OK]   $*"; }
warn() { echo "[WARN] $*"; }
fail() { echo "[FAIL] $*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

extract_port_from_url() {
  local url="$1"
  python3 - "$url" <<'PY'
import sys
from urllib.parse import urlparse
u = urlparse(sys.argv[1])
port = u.port
if port is None:
    port = 443 if u.scheme == "https" else 80
print(port)
PY
}

kill_port_listener_if_needed() {
  local port="$1"
  if [[ "$CONTEXT_PORT_RECLAIM" != "1" ]]; then
    return 0
  fi
  if command -v fuser >/dev/null 2>&1; then
    if fuser "${port}/tcp" >/dev/null 2>&1; then
      warn "Reclaiming :$port listener (fuser -k) to align Context Layer commit"
      fuser -k "${port}/tcp" >/dev/null 2>&1 || true
      sleep 1
    fi
  fi
}

http_get_or_fail() {
  local url="$1"
  curl -fsS "$url"
}

http_code_post_json() {
  local url="$1"
  local body="$2"
  curl -sS -o /dev/null -w "%{http_code}" -X POST "$url" -H 'Content-Type: application/json' -d "$body"
}

wait_http_ok() {
  local name="$1"
  local url="$2"
  local max_sec="${3:-90}"
  local i
  for i in $(seq 1 "$max_sec"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      ok "$name ready: $url"
      return 0
    fi
    sleep 1
  done
  fail "Timeout waiting for $name: $url"
}

read_pid() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    cat "$pid_file"
  fi
}

is_pid_alive() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

stop_pid_file() {
  local label="$1"
  local pid_file="$2"
  local pid
  pid="$(read_pid "$pid_file" || true)"
  if [[ -z "$pid" ]]; then
    info "$label: no pid file"
    return 0
  fi
  if ! is_pid_alive "$pid"; then
    warn "$label: stale pid file removed"
    rm -f "$pid_file"
    return 0
  fi
  info "Stopping $label (PID $pid)"
  kill -TERM "$pid" 2>/dev/null || true
  sleep 1
  if is_pid_alive "$pid"; then
    warn "$label still running; sending SIGKILL"
    kill -KILL "$pid" 2>/dev/null || true
  fi
  rm -f "$pid_file"
  ok "$label stopped"
}

start_context_layer() {
  if [[ -z "$MOTADATA_ROOT" ]]; then
    fail "MOTADATA_ROOT is required (workspace root used by Context Layer exports)"
  fi
  if [[ ! -d "$MOTADATA_ROOT" ]]; then
    fail "MOTADATA_ROOT does not exist: $MOTADATA_ROOT"
  fi

  local pid
  pid="$(read_pid "$CONTEXT_PID_FILE" || true)"
  if [[ -n "$pid" ]] && is_pid_alive "$pid"; then
    info "Context Layer already running (PID $pid)"
    return 0
  fi
  rm -f "$CONTEXT_PID_FILE"

  info "Starting Context Layer on WSL"
  local launched_commit
  launched_commit="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || true)"
  {
    echo "launched_git_commit=$launched_commit"
    echo "motadata_root=$MOTADATA_ROOT"
    echo "context_url=$CONTEXT_URL"
    echo "started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$CONTEXT_META_FILE"
  (
    cd "$REPO_ROOT"
    export PYTHONPATH="$REPO_ROOT"
    export MOTADATA_ROOT
    export M_CODER_REPO_ROOT="$REPO_ROOT"
    export M_CODER_GIT_COMMIT="$launched_commit"
    export MOTADATA_CONTEXT_DISABLE_CODE_INDEX="${MOTADATA_CONTEXT_DISABLE_CODE_INDEX:-1}"
    python3 -m runtime.context_layer_service.app >>"$CONTEXT_LOG" 2>&1
  ) &
  echo "$!" > "$CONTEXT_PID_FILE"
  ok "Context Layer PID: $(cat "$CONTEXT_PID_FILE") (log: $CONTEXT_LOG)"
}

restart_context_layer_aligned() {
  local context_port
  context_port="$(extract_port_from_url "$CONTEXT_URL")"
  stop_pid_file "Context Layer" "$CONTEXT_PID_FILE"
  kill_port_listener_if_needed "$context_port"
  start_context_layer
  wait_http_ok "Context Layer" "$CONTEXT_URL/healthz" 90
}

build_tunnel_target() {
  if [[ -n "$TUNNEL_TARGET" ]]; then
    echo "$TUNNEL_TARGET"
    return
  fi
  if [[ -n "$TUNNEL_USER" && -n "$TUNNEL_HOST" ]]; then
    echo "$TUNNEL_USER@$TUNNEL_HOST"
    return
  fi
  fail "Set TUNNEL_TARGET or both TUNNEL_USER and TUNNEL_HOST when ENABLE_SSH_TUNNEL=1"
}

start_tunnel_if_enabled() {
  if [[ "$ENABLE_SSH_TUNNEL" != "1" ]]; then
    info "SSH tunnel disabled (ENABLE_SSH_TUNNEL=$ENABLE_SSH_TUNNEL)"
    return 0
  fi
  require_cmd ssh

  local target
  target="$(build_tunnel_target)"

  if [[ -z "$LOCAL_PLAN_GATE_PORT" ]]; then
    LOCAL_PLAN_GATE_PORT="$(extract_port_from_url "$PLAN_GATE_URL")"
  fi

  local pid
  pid="$(read_pid "$TUNNEL_PID_FILE" || true)"
  if [[ -n "$pid" ]] && is_pid_alive "$pid"; then
    info "SSH tunnel already running (PID $pid)"
    return 0
  fi
  rm -f "$TUNNEL_PID_FILE"

  local -a ssh_cmd
  ssh_cmd=(
    ssh
    -N
    -o ExitOnForwardFailure=yes
    -o ServerAliveInterval=30
    -o ServerAliveCountMax=120
    -L "${LOCAL_PLAN_GATE_PORT}:${REMOTE_PLAN_GATE_HOST}:${REMOTE_PLAN_GATE_PORT}"
  )
  if [[ "$LOCAL_VLLM_PORT" != "0" ]]; then
    ssh_cmd+=( -L "${LOCAL_VLLM_PORT}:${REMOTE_VLLM_HOST}:${REMOTE_VLLM_PORT}" )
  fi
  if [[ -n "$TUNNEL_SSH_KEY" ]]; then
    ssh_cmd+=( -i "$TUNNEL_SSH_KEY" )
  fi
  ssh_cmd+=( "$target" )

  info "Starting SSH tunnel to $target"
  if [[ "$LOCAL_VLLM_PORT" != "0" ]]; then
    info "  SSH -L: Plan-Gate ${LOCAL_PLAN_GATE_PORT}→${REMOTE_PLAN_GATE_HOST}:${REMOTE_PLAN_GATE_PORT}; vLLM ${LOCAL_VLLM_PORT}→${REMOTE_VLLM_HOST}:${REMOTE_VLLM_PORT}"
  else
    info "  SSH -L: Plan-Gate ${LOCAL_PLAN_GATE_PORT}→${REMOTE_PLAN_GATE_HOST}:${REMOTE_PLAN_GATE_PORT} (vLLM forward disabled; LOCAL_VLLM_PORT=0)"
  fi
  "${ssh_cmd[@]}" >>"$TUNNEL_LOG" 2>&1 &
  echo "$!" > "$TUNNEL_PID_FILE"
  ok "Tunnel PID: $(cat "$TUNNEL_PID_FILE") (log: $TUNNEL_LOG)"
}

check_health() {
  wait_http_ok "Context Layer" "$CONTEXT_URL/healthz" 90
  wait_http_ok "Plan-Gate" "$PLAN_GATE_URL/healthz" 90
}

get_git_commit_field() {
  local url="$1"
  python3 - "$url" <<'PY'
import json
import sys
import urllib.request
url = sys.argv[1]
with urllib.request.urlopen(url, timeout=20) as r:
    data = json.loads(r.read().decode("utf-8"))
print(data.get("git_commit", ""))
PY
}

check_versions_and_commit_match() {
  local context_version_json
  local plan_version_json
  local local_commit
  local context_commit
  local plan_commit
  local meta_context_commit

  context_version_json="$(http_get_or_fail "$CONTEXT_URL/version")"
  plan_version_json="$(http_get_or_fail "$PLAN_GATE_URL/version")"

  info "Context /version: $context_version_json"
  info "Plan-Gate /version: $plan_version_json"

  local_commit="$(git -C "$REPO_ROOT" rev-parse --short HEAD)"
  context_commit="$(get_git_commit_field "$CONTEXT_URL/version")"
  plan_commit="$(get_git_commit_field "$PLAN_GATE_URL/version")"
  meta_context_commit=""
  if [[ -f "$CONTEXT_META_FILE" ]]; then
    meta_context_commit="$(grep '^launched_git_commit=' "$CONTEXT_META_FILE" | head -n1 | cut -d'=' -f2- || true)"
  fi

  if [[ -z "$context_commit" && -n "$meta_context_commit" ]]; then
    context_commit="$meta_context_commit"
    warn "Context /version has no git_commit; using launch metadata from $CONTEXT_META_FILE"
  fi

  info "Local m-coder git_commit: $local_commit"
  info "Context Layer git_commit: ${context_commit:-<missing>}"
  info "Plan-Gate git_commit: ${plan_commit:-<missing>}"

  if [[ -z "$plan_commit" ]]; then
    fail "Plan-Gate /version missing git_commit (cannot validate parity)"
  fi

  if [[ -z "$context_commit" ]]; then
    if [[ "$REQUIRE_CONTEXT_GIT_COMMIT" == "1" ]]; then
      fail "Context Layer git_commit unavailable (set REQUIRE_CONTEXT_GIT_COMMIT=0 to allow non-strict mode)"
    fi
    warn "Context Layer git_commit unavailable; skipping strict context-plan commit equality"
  fi

  if [[ -n "$context_commit" && "$context_commit" != "$plan_commit" ]]; then
    if [[ "$ALLOW_COMMIT_MISMATCH" == "1" ]]; then
      warn "Context Layer and Plan-Gate git_commit mismatch (allowed): $context_commit vs $plan_commit"
    else
      fail "Context Layer and Plan-Gate git_commit mismatch ($context_commit vs $plan_commit)"
    fi
  fi

  if [[ "$plan_commit" != "$local_commit" ]]; then
    if [[ "$ALLOW_COMMIT_MISMATCH" == "1" ]]; then
      warn "Plan-Gate commit differs from local repo (allowed by ALLOW_COMMIT_MISMATCH=1)"
    else
      fail "Plan-Gate git_commit ($plan_commit) != local m-coder commit ($local_commit)"
    fi
  fi

  ok "Version and commit parity checks passed"
}

check_endpoint_compatibility() {
  local c_export
  local pg_v1
  local pg_v0

  c_export="$(http_code_post_json "$CONTEXT_URL/v1/export_evidence" '{}')"
  pg_v1="$(http_code_post_json "$PLAN_GATE_URL/v1/ask" '{}')"
  pg_v0="$(http_code_post_json "$PLAN_GATE_URL/v0/ask" '{}')"

  info "Compatibility probe status codes:"
  info "  POST /v1/export_evidence -> $c_export"
  info "  POST /v1/ask            -> $pg_v1"
  info "  POST /v0/ask            -> $pg_v0"

  case "$c_export" in
    404|405) fail "Context Layer /v1/export_evidence route missing (HTTP $c_export)" ;;
  esac
  case "$pg_v1" in
    404|405) fail "Plan-Gate /v1/ask route missing (HTTP $pg_v1)" ;;
  esac
  case "$pg_v0" in
    404|405) fail "Plan-Gate /v0/ask route missing (HTTP $pg_v0)" ;;
  esac

  ok "Compatibility route checks passed (endpoints exist; payload validation code is acceptable)"
}

ensure_context_commit_aligned() {
  local local_commit
  local context_commit
  local plan_commit

  local_commit="$(git -C "$REPO_ROOT" rev-parse --short HEAD)"
  context_commit="$(get_git_commit_field "$CONTEXT_URL/version")"
  plan_commit="$(get_git_commit_field "$PLAN_GATE_URL/version")"

  if [[ -z "$context_commit" ]]; then
    warn "Context Layer /version has no git_commit; skipping auto-alignment"
    return 0
  fi

  if [[ "$context_commit" == "$local_commit" ]]; then
    if [[ -n "$plan_commit" && "$plan_commit" != "$local_commit" ]]; then
      warn "Plan-Gate commit differs from local/context (plan=$plan_commit local/context=$local_commit); Context Layer restart will not fix remote drift"
    fi
    info "Context Layer commit already aligned with local repo (context=$context_commit local=$local_commit)"
    return 0
  fi

  warn "Context Layer commit drift detected (context=$context_commit local=$local_commit); restarting Context Layer for alignment"
  restart_context_layer_aligned

  context_commit="$(get_git_commit_field "$CONTEXT_URL/version")"
  if [[ -n "$context_commit" && "$context_commit" == "$local_commit" ]]; then
    if [[ -n "$plan_commit" && "$plan_commit" != "$local_commit" ]]; then
      warn "Context aligned to local repo but Plan-Gate remains on different commit (plan=$plan_commit local=$local_commit)"
    fi
    ok "Context Layer commit aligned after restart (context=$context_commit)"
    return 0
  fi

  fail "Context Layer commit remains misaligned after restart (context=${context_commit:-<missing>} local=$local_commit)"
}

print_plugin_env_hint() {
  echo
  echo "JetBrains plugin target URLs:"
  echo "  MOTADATA_PLAN_GATE_URL=$PLAN_GATE_URL"
  echo "  MOTADATA_CONTEXT_LAYER_URL=$CONTEXT_URL"
  echo
  echo "If plugin runs on Windows, confirm Context Layer URL is reachable from Windows host."
}

cmd_up() {
  require_cmd git
  require_cmd curl
  require_cmd python3

  info "Bringing up WSL MVP plugin stack"
  start_tunnel_if_enabled
  start_context_layer
  check_health
  if [[ "$AUTO_ALIGN_CONTEXT_COMMIT" == "1" ]]; then
    ensure_context_commit_aligned
  fi
  check_versions_and_commit_match
  check_endpoint_compatibility
  print_plugin_env_hint
  ok "Stack is ready for JetBrains plugin UI testing"
}

cmd_check() {
  require_cmd git
  require_cmd curl
  require_cmd python3

  info "Running health/version/compatibility checks"
  check_health
  check_versions_and_commit_match
  check_endpoint_compatibility
  print_plugin_env_hint
}

cmd_status() {
  local cpid
  local tpid
  cpid="$(read_pid "$CONTEXT_PID_FILE" || true)"
  tpid="$(read_pid "$TUNNEL_PID_FILE" || true)"

  echo "WSL MVP stack status"
  echo "  CONTEXT_URL=$CONTEXT_URL"
  echo "  PLAN_GATE_URL=$PLAN_GATE_URL"
  echo "  MOTADATA_ROOT=${MOTADATA_ROOT:-<unset>}"
  if [[ -n "$cpid" ]] && is_pid_alive "$cpid"; then
    echo "  Context Layer PID: $cpid (managed by this script)"
  else
    echo "  Context Layer PID: not running (or not managed by this script)"
  fi
  if [[ -n "$tpid" ]] && is_pid_alive "$tpid"; then
    echo "  Tunnel PID: $tpid (managed by this script)"
  else
    echo "  Tunnel PID: not running (or not managed by this script)"
  fi

  if curl -fsS "$CONTEXT_URL/healthz" >/dev/null 2>&1; then
    echo "  Context health: OK"
  else
    echo "  Context health: DOWN"
  fi
  if curl -fsS "$PLAN_GATE_URL/healthz" >/dev/null 2>&1; then
    echo "  Plan-Gate health: OK"
  else
    echo "  Plan-Gate health: DOWN"
  fi
}

cmd_down() {
  info "Stopping WSL MVP plugin stack (managed processes only)"
  stop_pid_file "Context Layer" "$CONTEXT_PID_FILE"
  stop_pid_file "SSH tunnel" "$TUNNEL_PID_FILE"
  ok "Shutdown complete"
}

cmd_restart() {
  info "Restarting WSL MVP plugin stack (down -> up)"
  cmd_down
  cmd_up
}

usage() {
  cat <<'EOF'
Usage: ./scripts/wsl_plugin_mvp_stack.sh {up|check|status|down|restart}

Commands:
  up      Start tunnel (optional) + start Context Layer + run all checks
  check   Run health + /version + commit match + compatibility checks
  status  Show managed PIDs and health snapshot
  down    Stop managed Context Layer and tunnel
  restart Clean managed down then full up with checks

Important env:
  M_CODER_REPO_ROOT          Optional explicit repo root for Context Layer startup/checks
  MOTADATA_ROOT               Required for up (workspace root for Context Layer)
  CONTEXT_URL                Default: http://127.0.0.1:8091
  PLAN_GATE_URL              Default: http://127.0.0.1:8089
  ENABLE_SSH_TUNNEL          1 to create SSH local forwards, else 0
  TUNNEL_TARGET              user@host (or set TUNNEL_USER + TUNNEL_HOST)
  TUNNEL_SSH_KEY             Optional identity file
  LOCAL_PLAN_GATE_PORT       Default: port from PLAN_GATE_URL (8089)
  LOCAL_VLLM_PORT            Default: 8000 (forward vLLM with Plan-Gate); set 0 to disable vLLM forward
  AUTO_ALIGN_CONTEXT_COMMIT  1(default) to auto-restart Context Layer on commit drift
  CONTEXT_PORT_RECLAIM       1(default) allows reclaiming port 8091 listener via fuser during alignment
  ALLOW_COMMIT_MISMATCH      1 to warn instead of fail on local-vs-service commit mismatch
EOF
}

case "${1:-}" in
  up) cmd_up ;;
  check) cmd_check ;;
  status) cmd_status ;;
  down) cmd_down ;;
  restart) cmd_restart ;;
  *) usage; exit 1 ;;
esac

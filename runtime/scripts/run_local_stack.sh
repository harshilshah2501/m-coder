#!/usr/bin/env bash
#
# Minimal deterministic helpers for Context Layer on a dev host.
# Plan-Gate + vLLM: use runtime/scripts/governed_services.sh (requires demo_stack.env + VLLM_BASE_MODEL).
#
# Usage:
#   cp runtime/config/host_local.env.example runtime/config/host_local.env  # edit paths
#   source runtime/config/host_local.env   # optional
#   ./runtime/scripts/run_local_stack.sh start-plan-gate   # HTTP Plan-Gate (no vLLM)
#   ./runtime/scripts/run_local_stack.sh start-context
#   ./runtime/scripts/run_local_stack.sh health
#   ./runtime/scripts/run_local_stack.sh stop-context
#   ./runtime/scripts/run_local_stack.sh stop-plan-gate
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUNTIME_DIR="$SCRIPT_DIR/.."
CONFIG_DIR="$RUNTIME_DIR/config"
RUN_DIR="$RUNTIME_DIR/.run"
HOST_LOCAL="${HOST_LOCAL_ENV:-$CONFIG_DIR/host_local.env}"

info() { echo "[run_local_stack] $*"; }
fail() { echo "[run_local_stack] ERROR: $*" >&2; exit 1; }

_load_optional_env() {
  if [[ -f "$HOST_LOCAL" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "$HOST_LOCAL"
    set +a
  fi
  : "${CONTEXT_LAYER_HOST:=127.0.0.1}"
  : "${CONTEXT_LAYER_PORT:=8091}"
  : "${PLAN_GATE_PORT:=8089}"
  # If we started Context Layer via this script, use the recorded port (health/stop without env)
  if [[ -f "$RUN_DIR/context_layer.port" ]]; then
    local saved
    saved="$(tr -d '[:space:]' <"$RUN_DIR/context_layer.port" 2>/dev/null || true)"
    if [[ -n "$saved" ]]; then
      CONTEXT_LAYER_PORT="$saved"
    fi
  fi
  if [[ -f "$RUN_DIR/plan_gate_cli.port" ]]; then
    local pg_saved
    pg_saved="$(tr -d '[:space:]' <"$RUN_DIR/plan_gate_cli.port" 2>/dev/null || true)"
    if [[ -n "$pg_saved" ]]; then
      PLAN_GATE_PORT="$pg_saved"
    fi
  fi
  export CONTEXT_LAYER_HOST CONTEXT_LAYER_PORT
  export PYTHONPATH="${REPO_ROOT}${PYTHONPATH:+:$PYTHONPATH}"
}

cmd_start_context() {
  _load_optional_env
  mkdir -p "$RUN_DIR"
  local pid_file="$RUN_DIR/context_layer.pid"
  local log_file="$RUN_DIR/context_layer.log"
  if [[ -f "$pid_file" ]]; then
    local old
    old="$(cat "$pid_file" 2>/dev/null || true)"
    if [[ -n "$old" ]] && kill -0 "$old" 2>/dev/null; then
      if curl -sf "http://127.0.0.1:${CONTEXT_LAYER_PORT}/healthz" >/dev/null 2>&1; then
        info "Context Layer already running (PID $old, port $CONTEXT_LAYER_PORT)"
        return 0
      fi
    fi
    rm -f "$pid_file"
  fi
  cd "$REPO_ROOT"
  echo "$CONTEXT_LAYER_PORT" >"$RUN_DIR/context_layer.port"
  nohup python3 -m runtime.context_layer_service >>"$log_file" 2>&1 &
  echo $! >"$pid_file"
  info "Context Layer starting (PID $(cat "$pid_file")), log: $log_file"
  local i
  for i in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:${CONTEXT_LAYER_PORT}/healthz" >/dev/null 2>&1; then
      info "Context Layer /healthz OK (after ${i}s)"
      return 0
    fi
    sleep 0.2
  done
  fail "Context Layer did not become healthy; see $log_file"
}

cmd_stop_context() {
  _load_optional_env
  local pid_file="$RUN_DIR/context_layer.pid"
  [[ -f "$pid_file" ]] || { info "No pid file; nothing to stop"; return 0; }
  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    kill -TERM "$pid" 2>/dev/null || true
    sleep 1
    kill -KILL "$pid" 2>/dev/null || true
  fi
  rm -f "$pid_file" "$RUN_DIR/context_layer.port"
  info "Context Layer stopped"
}

cmd_start_plan_gate() {
  _load_optional_env
  mkdir -p "$RUN_DIR"
  local pid_file="$RUN_DIR/plan_gate_cli.pid"
  local log_file="$RUN_DIR/plan_gate_cli.log"
  if curl -sf "http://127.0.0.1:${PLAN_GATE_PORT}/healthz" >/dev/null 2>&1; then
    info "Plan-Gate already healthy on port $PLAN_GATE_PORT (skip start)"
    return 0
  fi
  if [[ -f "$pid_file" ]]; then
    local old
    old="$(cat "$pid_file" 2>/dev/null || true)"
    if [[ -n "$old" ]] && kill -0 "$old" 2>/dev/null; then
      if curl -sf "http://127.0.0.1:${PLAN_GATE_PORT}/healthz" >/dev/null 2>&1; then
        info "Plan-Gate already running (PID $old, port $PLAN_GATE_PORT)"
        return 0
      fi
    fi
    rm -f "$pid_file"
  fi
  cd "$REPO_ROOT"
  export PLAN_GATE_PORT
  export M_CODER_REPO_ROOT="$REPO_ROOT"
  echo "$PLAN_GATE_PORT" >"$RUN_DIR/plan_gate_cli.port"
  nohup python3 -m runtime.plan_gate_service.app >>"$log_file" 2>&1 &
  echo $! >"$pid_file"
  info "Plan-Gate starting (PID $(cat "$pid_file")), log: $log_file"
  local i
  for i in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:${PLAN_GATE_PORT}/healthz" >/dev/null 2>&1; then
      info "Plan-Gate /healthz OK (after ${i}s)"
      return 0
    fi
    sleep 0.2
  done
  fail "Plan-Gate did not become healthy; see $log_file"
}

cmd_stop_plan_gate() {
  _load_optional_env
  local pid_file="$RUN_DIR/plan_gate_cli.pid"
  [[ -f "$pid_file" ]] || { info "No Plan-Gate cli pid file; nothing to stop"; return 0; }
  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    kill -TERM "$pid" 2>/dev/null || true
    sleep 1
    kill -KILL "$pid" 2>/dev/null || true
  fi
  rm -f "$pid_file" "$RUN_DIR/plan_gate_cli.port"
  info "Plan-Gate (cli) stopped"
}

cmd_health() {
  _load_optional_env
  echo ""
  echo "=== Health (ports: context=$CONTEXT_LAYER_PORT plan_gate=$PLAN_GATE_PORT) ==="
  if curl -sf "http://127.0.0.1:${CONTEXT_LAYER_PORT}/healthz" >/dev/null 2>&1; then
    echo "Context Layer :${CONTEXT_LAYER_PORT} -> OK"
  else
    echo "Context Layer :${CONTEXT_LAYER_PORT} -> DOWN"
  fi
  if curl -sf "http://127.0.0.1:${PLAN_GATE_PORT}/healthz" >/dev/null 2>&1; then
    echo "Plan-Gate     :${PLAN_GATE_PORT} -> OK"
  else
    echo "Plan-Gate     :${PLAN_GATE_PORT} -> DOWN"
  fi
  if [[ -n "${VLLM_PORT:-}" ]]; then
    if curl -sf "http://127.0.0.1:${VLLM_PORT}/v1/models" >/dev/null 2>&1; then
      echo "vLLM          :${VLLM_PORT} -> OK (/v1/models)"
    else
      echo "vLLM          :${VLLM_PORT} -> DOWN (optional)"
    fi
  fi
  echo ""
}

cmd_print_env() {
  _load_optional_env
  echo "export CONTEXT_LAYER_HOST=${CONTEXT_LAYER_HOST}"
  echo "export CONTEXT_LAYER_PORT=${CONTEXT_LAYER_PORT}"
  echo "export PLAN_GATE_PORT=${PLAN_GATE_PORT}"
  echo "export MOTADATA_CONTEXT_LAYER_URL=http://127.0.0.1:${CONTEXT_LAYER_PORT}"
  echo "export MOTADATA_PLAN_GATE_URL=http://127.0.0.1:${PLAN_GATE_PORT}"
  echo "export WORKSPACE_ROOT=${M_CODER_REPO_ROOT:-$REPO_ROOT}"
}

usage() {
  cat <<EOF
Usage: $0 {start-plan-gate|stop-plan-gate|start-context|stop-context|health|print-env}

  start-plan-gate Start Plan-Gate HTTP only (python3 -m runtime.plan_gate_service.app), no vLLM
  stop-plan-gate  Stop Plan-Gate started by this script (plan_gate_cli.pid)
  start-context   Start Context Layer (python3 -m runtime.context_layer_service), pid in runtime/.run/
  stop-context    Stop Context Layer using pid file
  health          curl healthz for Context Layer + Plan-Gate (and vLLM if VLLM_PORT set)
  print-env       Print export lines for shell (defaults + optional $HOST_LOCAL)

CLI E2E (export evidence → /v1/ask): start-plan-gate + start-context, then:
  QUERY='...' WORKSPACE_ROOT=/abs/path/to/workspace bash runtime/scripts/cli_e2e_verify.sh

Optional: HOST_LOCAL_ENV=/path/to/host_local.env (default: $CONFIG_DIR/host_local.env)
EOF
}

case "${1:-}" in
  start-plan-gate) cmd_start_plan_gate ;;
  stop-plan-gate) cmd_stop_plan_gate ;;
  start-context) cmd_start_context ;;
  stop-context) cmd_stop_context ;;
  health) cmd_health ;;
  print-env) cmd_print_env ;;
  *) usage; exit 1 ;;
esac

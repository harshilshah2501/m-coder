#!/usr/bin/env bash
#
# Report status of governed services (Plan-Gate, vLLM) from runtime/.run/ and HTTP.
# Deterministic: same order and format every run.
#
# Usage:
#   ./runtime/scripts/status_governed_services.sh
#   CONFIG_PATH=/path/to/demo_stack.env ./runtime/scripts/status_governed_services.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$SCRIPT_DIR/.."
CONFIG_DIR="$RUNTIME_DIR/config"
RUN_DIR="$RUNTIME_DIR/.run"
CONFIG_PATH="${CONFIG_PATH:-$CONFIG_DIR/demo_stack.env}"

info()  { echo "[INFO]  $*"; }
step()  { echo "[STEP]  $*"; }
ok()    { echo "[OK]    $*"; }
warn()  { echo "[WARN]  $*"; }
sep()   { echo ""; echo "═══════════════════════════════════════════════════════════════"; echo "  $*"; echo "═══════════════════════════════════════════════════════════════"; echo ""; }

# --- Resolve ports ---
if [[ -f "$CONFIG_PATH" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "$CONFIG_PATH"
    set +a
    : "${VLLM_PORT:=8000}"
    : "${VLLM_SERVED_MODEL_NAME:=motadata-coder}"
    : "${PLAN_GATE_PORT:=8089}"
else
    PLAN_GATE_PORT=8089
    VLLM_PORT=8000
    VLLM_SERVED_MODEL_NAME=motadata-coder
    warn "Config not found, using default ports"
fi

sep "Governed services status"

# --- Plan-Gate ---
step "Plan-Gate (port $PLAN_GATE_PORT)"
PLAN_GATE_PID=""
if [[ -f "$RUN_DIR/plan_gate.pid" ]]; then
    read -r PLAN_GATE_PID < "$RUN_DIR/plan_gate.pid" 2>/dev/null || true
fi
if [[ -n "$PLAN_GATE_PID" ]] && kill -0 "$PLAN_GATE_PID" 2>/dev/null; then
    info "  PID:    $PLAN_GATE_PID (running)"
else
    info "  PID:    — (no pid file or process not running)"
fi
if curl -sf "http://127.0.0.1:${PLAN_GATE_PORT}/healthz" >/dev/null 2>&1; then
    ok "  HTTP:   http://127.0.0.1:${PLAN_GATE_PORT}/healthz OK"
else
    info "  HTTP:   — (not responding)"
fi

echo ""

# --- vLLM ---
step "vLLM / Explain (port $VLLM_PORT)"
VLLM_PID=""
if [[ -f "$RUN_DIR/vllm.pid" ]]; then
    read -r VLLM_PID < "$RUN_DIR/vllm.pid" 2>/dev/null || true
fi
if [[ -n "$VLLM_PID" ]] && kill -0 "$VLLM_PID" 2>/dev/null; then
    info "  PID:    $VLLM_PID (running)"
else
    info "  PID:    — (no pid file or process not running)"
fi
VLLM_MODELS="$(curl -sf "http://127.0.0.1:${VLLM_PORT}/v1/models" 2>/dev/null)" || true
if [[ -n "$VLLM_MODELS" ]] && echo "$VLLM_MODELS" | grep -q "$VLLM_SERVED_MODEL_NAME"; then
    ok "  HTTP:   http://127.0.0.1:${VLLM_PORT}/v1/models OK (model: $VLLM_SERVED_MODEL_NAME)"
elif [[ -n "$VLLM_MODELS" ]]; then
    warn "  HTTP:   port responds but model '$VLLM_SERVED_MODEL_NAME' not present"
else
    info "  HTTP:   — (not responding)"
fi

echo ""
info "Run dir: $RUN_DIR"
echo ""

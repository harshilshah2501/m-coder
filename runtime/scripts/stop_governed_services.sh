#!/usr/bin/env bash
#
# Stop governed services (Plan-Gate, then vLLM) using PIDs in runtime/.run/.
# Frees ports deterministically: SIGTERM → wait → SIGKILL → remove pid file.
#
# Usage:
#   ./runtime/scripts/stop_governed_services.sh
#   CONFIG_PATH=/path/to/demo_stack.env ./runtime/scripts/stop_governed_services.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$SCRIPT_DIR/.."
CONFIG_DIR="$RUNTIME_DIR/config"
RUN_DIR="$RUNTIME_DIR/.run"
CONFIG_PATH="${CONFIG_PATH:-$CONFIG_DIR/demo_stack.env}"

# Seconds to wait for graceful SIGTERM before SIGKILL
STOP_TIMEOUT=10

info()  { echo "[INFO]  $*"; }
step()  { echo "[STEP]  $*"; }
ok()    { echo "[OK]    $*"; }
warn()  { echo "[WARN]  $*"; }
sep()   { echo ""; echo "═══════════════════════════════════════════════════════════════"; echo "  $*"; echo "═══════════════════════════════════════════════════════════════"; echo ""; }

# Kill process by pid file: SIGTERM, wait up to STOP_TIMEOUT, then SIGKILL; remove pid file.
# Returns 0 if stopped or pid file missing/stale, 1 on error.
_stop_pid_file() {
    local pid_file="$1"
    local label="$2"
    if [[ ! -f "$pid_file" ]]; then
        info "$label: no pid file (not started by launcher)"
        return 0
    fi
    local pid
    read -r pid < "$pid_file" 2>/dev/null || true
    if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
        rm -f "$pid_file"
        info "$label: process not running (stale pid file removed)"
        return 0
    fi
    step "Stopping $label (PID $pid)..."
    kill -TERM "$pid" 2>/dev/null || true
    local i=0
    while kill -0 "$pid" 2>/dev/null && [[ $i -lt $STOP_TIMEOUT ]]; do
        sleep 1
        i=$((i + 1))
    done
    if kill -0 "$pid" 2>/dev/null; then
        warn "$label: SIGTERM did not exit in ${STOP_TIMEOUT}s, sending SIGKILL"
        kill -KILL "$pid" 2>/dev/null || true
        sleep 1
    fi
    rm -f "$pid_file"
    ok "$label stopped (port freed)"
    return 0
}

# --- Resolve ports (from config or effective_config or defaults) ---
sep "1. Resolve config"
if [[ -f "$CONFIG_PATH" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "$CONFIG_PATH"
    set +a
    : "${VLLM_PORT:=8000}"
    : "${PLAN_GATE_PORT:=8089}"
    info "Using ports from $CONFIG_PATH (Plan-Gate: $PLAN_GATE_PORT, vLLM: $VLLM_PORT)"
else
    PLAN_GATE_PORT=8089
    VLLM_PORT=8000
    warn "Config not found, using defaults (Plan-Gate: $PLAN_GATE_PORT, vLLM: $VLLM_PORT)"
fi

if [[ ! -d "$RUN_DIR" ]]; then
    ok "Run dir missing ($RUN_DIR) — nothing to stop."
    exit 0
fi

# --- Stop Plan-Gate first (frees port 8089), then vLLM (frees port 8000) ---
sep "2. Stop Plan-Gate"
_stop_pid_file "$RUN_DIR/plan_gate.pid" "Plan-Gate"

sep "3. Stop vLLM (Explain service)"
_stop_pid_file "$RUN_DIR/vllm.pid" "vLLM"

sep "Done"
ok "Governed services stopped. Ports $PLAN_GATE_PORT and $VLLM_PORT freed."
echo ""

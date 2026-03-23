#!/usr/bin/env bash
#
# Single entry point for vLLM + Plan-Gate (governed stack).
#
# Usage:
#   ./runtime/scripts/governed_services.sh start|stop|restart|status
#   CONFIG_PATH=/path/to/demo_stack.env ./runtime/scripts/governed_services.sh restart
#
# - stop: SIGTERM → wait → SIGKILL; then optional fuser -k on ports if still bound (no leaks).
# - restart: full stop, wait, port cleanup, then start (clean cycle).
# - status: HTTP checks + pid files.
#
# Requires runtime/config/demo_stack.env (copy from demo_stack.env.example) with VLLM_BASE_MODEL
# for start/restart.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUNTIME_DIR="$SCRIPT_DIR/.."
CONFIG_DIR="$RUNTIME_DIR/config"
RUN_DIR="$RUNTIME_DIR/.run"
CONFIG_PATH="${CONFIG_PATH:-$CONFIG_DIR/demo_stack.env}"

STOP_TIMEOUT="${STOP_TIMEOUT:-10}"
PORT_CLEAN_RETRIES="${PORT_CLEAN_RETRIES:-15}"

info()  { echo "[INFO]  $*"; }
step()  { echo "[STEP]  $*"; }
ok()    { echo "[OK]    $*"; }
warn()  { echo "[WARN]  $*"; }
fail()  { echo "[FAIL]  $*" >&2; exit 1; }
sep()   { echo ""; echo "═══════════════════════════════════════════════════════════════"; echo "  $*"; echo "═══════════════════════════════════════════════════════════════"; echo ""; }

fail_vllm_config() {
    echo "❌ vLLM failed to start." >&2
    echo "" >&2
    echo "Reason:" >&2
    echo "$1" >&2
    echo "" >&2
    echo "Example:" >&2
    echo "  VLLM_BASE_MODEL=/home/ubuntu/models/llama-3-8b" >&2
    echo "" >&2
    echo "Fix:" >&2
    echo "  Edit runtime/config/demo_stack.env and set a valid local path." >&2
    exit 1
}

_load_config_ports() {
    if [[ -f "$CONFIG_PATH" ]]; then
        set -a
        # shellcheck source=/dev/null
        source "$CONFIG_PATH"
        set +a
    fi
    : "${VLLM_PORT:=8000}"
    : "${PLAN_GATE_PORT:=8089}"
}

# Kill listeners still bound to port (Linux fuser); last resort after graceful PID stop.
_nuke_port_tcp() {
    local port="$1"
    local label="$2"
    if command -v fuser >/dev/null 2>&1; then
        if fuser "${port}/tcp" >/dev/null 2>&1; then
            warn "$label: clearing stray listeners on :$port (fuser -k)"
            fuser -k "${port}/tcp" >/dev/null 2>&1 || true
            sleep 1
        fi
    fi
}

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
    ok "$label stopped"
    return 0
}

cmd_stop() {
    _load_config_ports
    sep "Stop governed services (Plan-Gate → vLLM)"
    if [[ ! -d "$RUN_DIR" ]]; then
        ok "Run dir missing ($RUN_DIR) — nothing to stop."
        _nuke_port_tcp "$PLAN_GATE_PORT" "Plan-Gate"
        _nuke_port_tcp "$VLLM_PORT" "vLLM"
        return 0
    fi
    _stop_pid_file "$RUN_DIR/plan_gate.pid" "Plan-Gate"
    _stop_pid_file "$RUN_DIR/vllm.pid" "vLLM"
    sleep 1
    _nuke_port_tcp "$PLAN_GATE_PORT" "Plan-Gate"
    _nuke_port_tcp "$VLLM_PORT" "vLLM"
    sep "Done"
    ok "Governed services stopped (ports $PLAN_GATE_PORT, $VLLM_PORT cleared)."
    echo ""
}

cmd_start() {
    sep "1. Load config"
    step "Loading config..."
    if [[ ! -f "$CONFIG_PATH" ]]; then
        fail "Config not found: $CONFIG_PATH (copy runtime/config/demo_stack.env.example to runtime/config/demo_stack.env)"
    fi
    set -a
    # shellcheck source=/dev/null
    source "$CONFIG_PATH"
    set +a
    ok "Loaded $CONFIG_PATH"

    : "${VLLM_PORT:=8000}"
    : "${VLLM_SERVED_MODEL_NAME:=motadata-coder}"
    : "${MOTADATA_EXPLAIN_VLLM_URL:=http://127.0.0.1:$VLLM_PORT}"
    : "${MOTADATA_EXPLAIN_MODEL:=$VLLM_SERVED_MODEL_NAME}"
    : "${PLAN_GATE_PORT:=8089}"
    export MOTADATA_EXPLAIN_VLLM_URL MOTADATA_EXPLAIN_MODEL

    sep "2. Preflight validation"
    step "Preflight validation..."
    if [[ -z "$VLLM_BASE_MODEL" ]]; then
        fail_vllm_config "VLLM_BASE_MODEL must point to a LOCAL model path on this machine. It is empty or unset."
    fi
    if [[ -d "$VLLM_BASE_MODEL" || -f "$VLLM_BASE_MODEL" ]]; then
        ok "VLLM_BASE_MODEL (local path) exists: $VLLM_BASE_MODEL"
    else
        fail_vllm_config "VLLM_BASE_MODEL must point to a LOCAL model path on this machine. Current value is missing or invalid: $VLLM_BASE_MODEL"
    fi
    if [[ -n "$ADAPTER_PATH" ]]; then
        if [[ ! -d "$ADAPTER_PATH" && ! -f "$ADAPTER_PATH" ]]; then
            fail "ADAPTER_PATH is set but invalid: $ADAPTER_PATH"
        fi
        ok "ADAPTER_PATH exists: $ADAPTER_PATH"
    fi
    if [[ -n "$ASK_DEFAULT_REPO_ROOT" ]]; then
        if [[ ! -d "$ASK_DEFAULT_REPO_ROOT" ]]; then
            fail "ASK_DEFAULT_REPO_ROOT does not exist on GPU: $ASK_DEFAULT_REPO_ROOT"
        fi
        ok "ASK_DEFAULT_REPO_ROOT exists: $ASK_DEFAULT_REPO_ROOT"
    fi
    ok "Preflight passed"

    sep "3. Prepare run directory"
    mkdir -p "$RUN_DIR"
    EFFECTIVE_CONFIG="$RUN_DIR/effective_config.env"
    {
        echo "# Effective config at $(date -Iseconds)"
        echo "VLLM_BASE_MODEL=$VLLM_BASE_MODEL"
        echo "VLLM_PORT=$VLLM_PORT"
        echo "VLLM_SERVED_MODEL_NAME=$VLLM_SERVED_MODEL_NAME"
        echo "MOTADATA_EXPLAIN_VLLM_URL=$MOTADATA_EXPLAIN_VLLM_URL"
        echo "MOTADATA_EXPLAIN_MODEL=$MOTADATA_EXPLAIN_MODEL"
        echo "ASK_DEFAULT_REPO_ROOT=${ASK_DEFAULT_REPO_ROOT:-}"
        echo "PLAN_GATE_PORT=$PLAN_GATE_PORT"
    } > "$EFFECTIVE_CONFIG"
    info "Effective config written to $EFFECTIVE_CONFIG"

    if [[ -n "$VLLM_VENV" && -d "$VLLM_VENV" ]]; then
        VENV="$VLLM_VENV"
    elif [[ -n "$ADAPTER_PATH" && -d "$REPO_ROOT/.venv" ]]; then
        VENV="$REPO_ROOT/.venv"
    else
        VENV=""
    fi
    if [[ -n "$VENV" ]]; then
        PYTHON="$VENV/bin/python"
        VLLM_CMD="$VENV/bin/vllm"
    else
        PYTHON="${PYTHON:-python3}"
        VLLM_CMD=""
    fi
    if ! "$PYTHON" -c "import vllm" 2>/dev/null; then
        fail "vLLM not found. Install with: pip install vllm (or set VLLM_VENV in config)"
    fi

    sep "4. vLLM (Explain service)"
    VLLM_PID=""
    VLLM_MODELS="$(curl -sf "http://127.0.0.1:${VLLM_PORT}/v1/models" 2>/dev/null)" || true
    if [[ -n "$VLLM_MODELS" ]] && echo "$VLLM_MODELS" | grep -q "$VLLM_SERVED_MODEL_NAME"; then
        step "vLLM already running on port $VLLM_PORT (model $VLLM_SERVED_MODEL_NAME present)"
    else
        if [[ -n "$VLLM_MODELS" ]]; then
            echo "❌ Explain service unavailable — vLLM not ready." >&2
            fail "Port $VLLM_PORT responds at /v1/models but expected model '$VLLM_SERVED_MODEL_NAME' is not present. Stop the other service or set VLLM_SERVED_MODEL_NAME to match."
        fi
        step "Starting vLLM..."
        VLLM_LOG="$RUN_DIR/vllm.log"
        if [[ -n "$ADAPTER_PATH" && -n "$VLLM_CMD" ]]; then
            "$VLLM_CMD" serve "$VLLM_BASE_MODEL" \
                --host 127.0.0.1 \
                --port "$VLLM_PORT" \
                --served-model-name "$VLLM_SERVED_MODEL_NAME" \
                --enable-lora \
                --lora-modules "${VLLM_SERVED_MODEL_NAME}=${ADAPTER_PATH}" \
                > "$VLLM_LOG" 2>&1 &
        else
            "$PYTHON" -m vllm.entrypoints.openai.api_server \
                --model "$VLLM_BASE_MODEL" \
                --served-model-name "$VLLM_SERVED_MODEL_NAME" \
                --host 127.0.0.1 \
                --port "$VLLM_PORT" \
                --dtype bfloat16 \
                --max-model-len 8192 \
                --gpu-memory-utilization 0.90 \
                --trust-remote-code \
                > "$VLLM_LOG" 2>&1 &
        fi
        VLLM_PID=$!
        echo "$VLLM_PID" > "$RUN_DIR/vllm.pid"
        info "vLLM started (PID $VLLM_PID), log: $VLLM_LOG"

        step "Waiting for vLLM readiness (strict: model name in /v1/models, up to 120s)..."
        for i in $(seq 1 120); do
            if curl -sf "http://127.0.0.1:${VLLM_PORT}/v1/models" 2>/dev/null | grep -q "$VLLM_SERVED_MODEL_NAME"; then
                ok "vLLM ready after ${i}s"
                break
            fi
            if [[ -n "$VLLM_PID" ]] && ! kill -0 "$VLLM_PID" 2>/dev/null; then
                echo "❌ Explain service unavailable — vLLM not ready." >&2
                fail "vLLM process exited; check $VLLM_LOG"
            fi
            sleep 1
        done
        if ! curl -sf "http://127.0.0.1:${VLLM_PORT}/v1/models" 2>/dev/null | grep -q "$VLLM_SERVED_MODEL_NAME"; then
            echo "❌ Explain service unavailable — vLLM not ready." >&2
            fail "vLLM did not serve model '$VLLM_SERVED_MODEL_NAME' within 120s"
        fi
    fi

    sep "5. Plan-Gate"
    PLAN_GATE_PID=""
    PLAN_GATE_PID_FILE="$RUN_DIR/plan_gate.pid"
    if [[ -f "$PLAN_GATE_PID_FILE" ]]; then
        read -r PLAN_GATE_PID < "$PLAN_GATE_PID_FILE" 2>/dev/null || true
        if [[ -n "$PLAN_GATE_PID" ]] && kill -0 "$PLAN_GATE_PID" 2>/dev/null; then
            :
        else
            rm -f "$PLAN_GATE_PID_FILE"
            PLAN_GATE_PID=""
        fi
    fi
    if [[ -n "$PLAN_GATE_PID" ]]; then
        if curl -sf "http://127.0.0.1:${PLAN_GATE_PORT}/healthz" >/dev/null 2>&1; then
            step "Plan-Gate already running (PID $PLAN_GATE_PID, port $PLAN_GATE_PORT)"
        else
            fail "Plan-Gate process (PID $PLAN_GATE_PID) is running but /healthz did not respond on port $PLAN_GATE_PORT. Restart or check $RUN_DIR/plan_gate.log"
        fi
    elif curl -sf "http://127.0.0.1:${PLAN_GATE_PORT}/healthz" >/dev/null 2>&1; then
        step "Plan-Gate already running on port $PLAN_GATE_PORT (no pid file)"
    else
        step "Starting Plan-Gate..."
        export MOTADATA_EXPLAIN_VLLM_URL MOTADATA_EXPLAIN_MODEL
        export PLAN_GATE_PORT
        [[ -n "$ASK_DEFAULT_REPO_ROOT" ]] && export ASK_DEFAULT_REPO_ROOT
        PLAN_GATE_LOG="$RUN_DIR/plan_gate.log"
        cd "$REPO_ROOT"
        python3 -m runtime.plan_gate_service.app > "$PLAN_GATE_LOG" 2>&1 &
        PLAN_GATE_PID=$!
        echo "$PLAN_GATE_PID" > "$PLAN_GATE_PID_FILE"
        ok "Plan-Gate started (PID $PLAN_GATE_PID), log: $PLAN_GATE_LOG"

        step "Waiting for Plan-Gate readiness (/healthz on port $PLAN_GATE_PORT, up to 30s)..."
        for i in $(seq 1 30); do
            if curl -sf "http://127.0.0.1:${PLAN_GATE_PORT}/healthz" >/dev/null 2>&1; then
                ok "Plan-Gate ready after ${i}s"
                break
            fi
            if ! kill -0 "$PLAN_GATE_PID" 2>/dev/null; then
                fail "Plan-Gate process exited before becoming ready; check $PLAN_GATE_LOG"
            fi
            sleep 1
        done
        if ! curl -sf "http://127.0.0.1:${PLAN_GATE_PORT}/healthz" >/dev/null 2>&1; then
            fail "Plan-Gate did not become healthy within 30s; check $PLAN_GATE_LOG"
        fi
    fi

    sep "Done"
    ok "Governed services running."
    info "  Explain service: ENABLED (vLLM @ http://127.0.0.1:${VLLM_PORT}, model=$VLLM_SERVED_MODEL_NAME)"
    info "  Plan-Gate:       http://127.0.0.1:${PLAN_GATE_PORT}/v0/plan"
    info "  Run dir:         $RUN_DIR"
    echo ""
}

cmd_status() {
    _load_config_ports
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Governed services status"
    echo "  CONFIG_PATH=$CONFIG_PATH"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "Ports: Plan-Gate=$PLAN_GATE_PORT  vLLM=$VLLM_PORT"
    if [[ -f "$RUN_DIR/plan_gate.pid" ]]; then
        echo "plan_gate.pid: $(cat "$RUN_DIR/plan_gate.pid" 2>/dev/null || echo '?')"
    else
        echo "plan_gate.pid: (none)"
    fi
    if [[ -f "$RUN_DIR/vllm.pid" ]]; then
        echo "vllm.pid:      $(cat "$RUN_DIR/vllm.pid" 2>/dev/null || echo '?')"
    else
        echo "vllm.pid:      (none)"
    fi
    echo ""
    if curl -sf "http://127.0.0.1:${PLAN_GATE_PORT}/healthz" >/dev/null 2>&1; then
        echo "Plan-Gate /healthz: OK"
    else
        echo "Plan-Gate /healthz: DOWN"
    fi
    if curl -sf "http://127.0.0.1:${VLLM_PORT}/v1/models" >/dev/null 2>&1; then
        echo "vLLM /v1/models:    OK"
    else
        echo "vLLM /v1/models:    DOWN"
    fi
    echo ""
}

cmd_restart() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Restart governed services (clean stop → start)"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    set +e
    cmd_stop
    local st=$?
    set -e
    if [[ $st -ne 0 ]]; then
        warn "Stop returned $st; continuing with port cleanup anyway"
    fi
    echo "[STEP]  Waiting for ports to quiesce (2s)..."
    sleep 2
    _load_config_ports
    _nuke_port_tcp "$PLAN_GATE_PORT" "Plan-Gate"
    _nuke_port_tcp "$VLLM_PORT" "vLLM"
    sleep 1
    cmd_start
}

usage() {
    echo "Usage: $0 {start|stop|restart|status}"
    echo ""
    echo "  start    Start vLLM + Plan-Gate (requires $CONFIG_PATH with VLLM_BASE_MODEL)"
    echo "  stop     Stop Plan-Gate then vLLM; clear stray listeners on service ports"
    echo "  restart  stop + port cleanup + start"
    echo "  status   Show pid files and HTTP health"
    echo ""
    echo "Environment: CONFIG_PATH (default: $CONFIG_DIR/demo_stack.env)"
}

case "${1:-}" in
    start)   cmd_start ;;
    stop)    cmd_stop ;;
    restart) cmd_restart ;;
    status)  cmd_status ;;
    *)
        usage
        exit 1
        ;;
esac

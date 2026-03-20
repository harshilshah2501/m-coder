#!/usr/bin/env bash
#
# Orchestrated startup: load config, preflight, start vLLM, strict readiness, start Plan-Gate.
# Persists PIDs, logs, and effective config under runtime/.run/.
#
# Usage:
#   ./runtime/scripts/start_governed_services.sh
#   CONFIG_PATH=/path/to/demo_stack.env ./runtime/scripts/start_governed_services.sh
#
# Requires runtime/config/demo_stack.env (copy from demo_stack.env.example) with VLLM_BASE_MODEL set to a local path.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUNTIME_DIR="$SCRIPT_DIR/.."
CONFIG_DIR="$RUNTIME_DIR/config"
RUN_DIR="$RUNTIME_DIR/.run"
CONFIG_PATH="${CONFIG_PATH:-$CONFIG_DIR/demo_stack.env}"

info()  { echo "[INFO]  $*"; }
step()  { echo "[STEP]  $*"; }
ok()    { echo "[OK]    $*"; }
warn()  { echo "[WARN]  $*"; }
fail()  { echo "[FAIL]  $*" >&2; exit 1; }
sep()   { echo ""; echo "═══════════════════════════════════════════════════════════════"; echo "  $*"; echo "═══════════════════════════════════════════════════════════════"; echo ""; }
# Clear failure block for operator-facing errors
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

# --- Load config ---
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

# --- DERIVED (auto if empty) ---
: "${VLLM_PORT:=8000}"
: "${VLLM_SERVED_MODEL_NAME:=motadata-coder}"
: "${MOTADATA_EXPLAIN_VLLM_URL:=http://127.0.0.1:$VLLM_PORT}"
: "${MOTADATA_EXPLAIN_MODEL:=$VLLM_SERVED_MODEL_NAME}"
: "${PLAN_GATE_PORT:=8089}"
export MOTADATA_EXPLAIN_VLLM_URL MOTADATA_EXPLAIN_MODEL

# --- Preflight ---
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

# --- Run dir ---
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

# --- Resolve Python / vLLM ---
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

# --- Start vLLM or verify already running ---
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

# --- Start Plan-Gate or verify already running ---
sep "5. Plan-Gate"
PLAN_GATE_PID=""
PLAN_GATE_PID_FILE="$RUN_DIR/plan_gate.pid"
if [[ -f "$PLAN_GATE_PID_FILE" ]]; then
    read -r PLAN_GATE_PID < "$PLAN_GATE_PID_FILE" 2>/dev/null || true
    if [[ -n "$PLAN_GATE_PID" ]] && kill -0 "$PLAN_GATE_PID" 2>/dev/null; then
        : # process still running
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

# --- Summary ---
sep "Done"
ok "Governed services running."
info "  Explain service: ENABLED (vLLM @ http://127.0.0.1:${VLLM_PORT}, model=$VLLM_SERVED_MODEL_NAME)"
info "  Plan-Gate:       http://127.0.0.1:${PLAN_GATE_PORT}/v0/plan"
info "  Run dir:         $RUN_DIR"
echo ""

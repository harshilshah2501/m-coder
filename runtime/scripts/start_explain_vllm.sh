#!/usr/bin/env bash
#
# Start vLLM for Explain/Debug reasoning (Plan-Gate optional augmentation).
# Sets MOTADATA_EXPLAIN_VLLM_URL and MOTADATA_EXPLAIN_MODEL for the runtime.
# Run on the GPU machine; Plan-Gate calls this service at 127.0.0.1:8000.
#
# Usage:
#   VLLM_BASE_MODEL=/path/to/base ADAPTER_PATH=/path/to/lora ./runtime/scripts/start_explain_vllm.sh
#   VLLM_BASE_MODEL=/path/to/model ./runtime/scripts/start_explain_vllm.sh
#
# Optional env (set before running):
#   VLLM_BASE_MODEL          — Base model path or HuggingFace ID (required)
#   ADAPTER_PATH             — LoRA adapter path; if set, uses vllm serve --enable-lora --lora-modules
#   VLLM_SERVED_MODEL_NAME   — Name exposed at /v1/models (default: motadata-coder)
#   VLLM_PORT                — Port (default: 8000)
#   VLLM_VENV                — Path to venv with vllm (default: .venv at repo root when using ADAPTER_PATH)
#   VLLM_ALREADY_RUNNING     — Set to 1 to only export env vars and verify (skip start)

set -e

# --- Configuration (override via env) ---
VLLM_PORT="${VLLM_PORT:-8000}"
VLLM_SERVED_MODEL_NAME="${VLLM_SERVED_MODEL_NAME:-motadata-coder}"
EXPLAIN_BASE_URL="http://127.0.0.1:${VLLM_PORT}"

info()  { echo "[INFO]  $*"; }
step()  { echo "[STEP]  $*"; }
ok()    { echo "[OK]    $*"; }
warn()  { echo "[WARN]  $*"; }
fail()  { echo "[FAIL]  $*" >&2; exit 1; }

# --- Repo root (for default .venv) ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# --- Step 1: Resolve Python / vLLM ---
step "Resolving Python and vLLM..."
if [[ -n "$VLLM_VENV" && -d "$VLLM_VENV" ]]; then
    VENV="$VLLM_VENV"
elif [[ -n "$ADAPTER_PATH" && -d "$REPO_ROOT/.venv" ]]; then
    VENV="$REPO_ROOT/.venv"
    info "Using repo .venv (ADAPTER_PATH set): $VENV"
else
    VENV=""
fi
if [[ -n "$VENV" ]]; then
    PYTHON="$VENV/bin/python"
    VLLM_CMD="$VENV/bin/vllm"
    info "Using venv: $VENV"
else
    PYTHON="${PYTHON:-python3}"
    VLLM_CMD=""
fi
if ! "$PYTHON" -c "import vllm" 2>/dev/null; then
    fail "vLLM not found. Install with: pip install vllm (or use VLLM_VENV= path to venv with vllm)"
fi
ok "vLLM available"

# --- Step 2: Base model and optional adapter ---
step "Resolving base model (--model)..."
if [[ -z "$VLLM_BASE_MODEL" ]]; then
    warn "VLLM_BASE_MODEL not set. You must set it to your base model path or HuggingFace ID."
    info "Example: VLLM_BASE_MODEL=/path/to/merged_models/qwen2.5-coder-7b-16bit"
    info "Example: VLLM_BASE_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct"
    fail "Set VLLM_BASE_MODEL and re-run."
fi
if [[ -d "$VLLM_BASE_MODEL" || -f "$VLLM_BASE_MODEL" ]]; then
    ok "Base model path: $VLLM_BASE_MODEL"
else
    info "Base model (HF or path): $VLLM_BASE_MODEL"
fi
if [[ -n "$ADAPTER_PATH" ]]; then
    step "LoRA adapter path (ADAPTER_PATH)..."
    if [[ ! -d "$ADAPTER_PATH" && ! -f "$ADAPTER_PATH" ]]; then
        fail "ADAPTER_PATH is set but not a directory/file: $ADAPTER_PATH"
    fi
    ok "Adapter path: $ADAPTER_PATH"
    USE_LORA=1
    if [[ -z "$VLLM_CMD" ]]; then
        warn "ADAPTER_PATH set but no venv; need VLLM_VENV or .venv at repo root for 'vllm serve'."
        if command -v vllm >/dev/null 2>&1; then
            VLLM_CMD="vllm"
        else
            fail "Set VLLM_VENV to a venv that has vllm installed (e.g. $REPO_ROOT/.venv)."
        fi
    fi
else
    USE_LORA=0
fi

# --- Step 3: Export env for Plan-Gate ---
step "Setting runtime environment variables..."
export MOTADATA_EXPLAIN_VLLM_URL="$EXPLAIN_BASE_URL"
export MOTADATA_EXPLAIN_MODEL="$VLLM_SERVED_MODEL_NAME"
info "MOTADATA_EXPLAIN_VLLM_URL=$MOTADATA_EXPLAIN_VLLM_URL"
info "MOTADATA_EXPLAIN_MODEL=$MOTADATA_EXPLAIN_MODEL"
ok "Plan-Gate will use these when calling the reasoner (no trailing slash on URL)."

# --- Step 4: Start vLLM or verify already running ---
if [[ "${VLLM_ALREADY_RUNNING:-0}" == "1" ]]; then
    step "VLLM_ALREADY_RUNNING=1 — skipping vLLM start; will only verify."
else
    step "Checking if vLLM is already serving on port $VLLM_PORT..."
    if curl -sf "http://127.0.0.1:${VLLM_PORT}/v1/models" >/dev/null 2>&1; then
        ok "vLLM already responding on port $VLLM_PORT"
    else
        if [[ "$USE_LORA" == "1" ]]; then
            step "Starting vLLM server with LoRA adapter (model load may take 60–120s)..."
            info "Base model: $VLLM_BASE_MODEL"
            info "LoRA adapter: $ADAPTER_PATH (served as $VLLM_SERVED_MODEL_NAME)"
            "$VLLM_CMD" serve "$VLLM_BASE_MODEL" \
                --host 127.0.0.1 \
                --port "$VLLM_PORT" \
                --served-model-name "$VLLM_SERVED_MODEL_NAME" \
                --enable-lora \
                --lora-modules "${VLLM_SERVED_MODEL_NAME}=${ADAPTER_PATH}" \
                &
        else
            step "Starting vLLM server (model load may take 60–120s)..."
            "$PYTHON" -m vllm.entrypoints.openai.api_server \
                --model "$VLLM_BASE_MODEL" \
                --served-model-name "$VLLM_SERVED_MODEL_NAME" \
                --host 127.0.0.1 \
                --port "$VLLM_PORT" \
                --dtype bfloat16 \
                --max-model-len 8192 \
                --gpu-memory-utilization 0.90 \
                --trust-remote-code \
                &
        fi
        VLLM_PID=$!
        info "vLLM started in background (PID: $VLLM_PID)"
        step "Waiting for /v1/models to respond (up to 120s)..."
        for i in $(seq 1 120); do
            if curl -sf "http://127.0.0.1:${VLLM_PORT}/v1/models" >/dev/null 2>&1; then
                ok "vLLM is ready after ${i}s"
                break
            fi
            if ! kill -0 "$VLLM_PID" 2>/dev/null; then
                fail "vLLM process exited; check logs"
            fi
            sleep 1
        done
        if ! curl -sf "http://127.0.0.1:${VLLM_PORT}/v1/models" >/dev/null 2>&1; then
            fail "vLLM did not become ready in 120s"
        fi
    fi
fi

# --- Step 5: Verify ---
step "Verifying /v1/models..."
MODELS=$(curl -sf "http://127.0.0.1:${VLLM_PORT}/v1/models" || true)
if echo "$MODELS" | grep -q "$VLLM_SERVED_MODEL_NAME"; then
    ok "Served model name '$VLLM_SERVED_MODEL_NAME' is available"
else
    warn "Response: $MODELS"
    fail "Expected model '$VLLM_SERVED_MODEL_NAME' in /v1/models"
fi

# --- Summary ---
echo ""
ok "Explain/Debug reasoning service is ready."
echo ""
info "To start Plan-Gate with this reasoning service, run (from repo root):"
echo "  export MOTADATA_EXPLAIN_VLLM_URL=\"$MOTADATA_EXPLAIN_VLLM_URL\" MOTADATA_EXPLAIN_MODEL=\"$MOTADATA_EXPLAIN_MODEL\""
echo "  python3 -m runtime.plan_gate_service.app"
echo ""
info "Or source this script and start Plan-Gate in the same shell: source $(dirname "$0")/start_explain_vllm.sh"

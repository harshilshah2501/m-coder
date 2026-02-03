#!/bin/bash
#===============================================================================
# Motadata AI Services Orchestrator (Unified)
#
# Single entry point that manages all services in correct order:
# 1. Docker containers (Qdrant + Neo4j)
# 2. vLLM server (port 8000)
# 3. RAG API (port 8081)
# 4. Health monitor
#===============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Timeouts (seconds)
DOCKER_TIMEOUT=60
VLLM_TIMEOUT=180
RAG_TIMEOUT=60

# Paths
VENV_VLLM="/home/harshil/Harshil-PoCs/venv/vllm"
VENV_RAG="/home/harshil/Harshil-PoCs/venv/rag"
MODEL_PATH="/home/harshil/Harshil-PoCs/models/v16_2/motadata-coder-v16_2-merged"
RAG_SYSTEM_DIR="/home/harshil/Harshil-PoCs/rag"
LOG_DIR="$RAG_SYSTEM_DIR/logs"

# Version-agnostic model name (used by all services)
VLLM_MODEL_NAME="motadata-coder"

# Create log directory
mkdir -p "$LOG_DIR"

log_info()    { echo -e "${BLUE}[INFO]${NC} $(date '+%H:%M:%S') $1"; }
log_success() { echo -e "${GREEN}[OK]${NC}   $(date '+%H:%M:%S') $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $(date '+%H:%M:%S') $1"; }
log_error()   { echo -e "${RED}[FAIL]${NC} $(date '+%H:%M:%S') $1"; }

wait_for_health() {
    local name=$1
    local url=$2
    local timeout=$3
    local waited=0
    local interval=5
    
    log_info "Waiting for $name to be healthy ($url)..."
    
    while [ $waited -lt $timeout ]; do
        if curl -s --connect-timeout 3 "$url" > /dev/null 2>&1; then
            log_success "$name is healthy (${waited}s)"
            return 0
        fi
        sleep $interval
        waited=$((waited + interval))
        echo -ne "  ⏳ ${waited}s / ${timeout}s\r"
    done
    
    log_error "$name failed to become healthy after ${timeout}s"
    return 1
}

start_docker() {
    log_info "Starting Docker containers (Qdrant + Neo4j)..."
    cd "$RAG_SYSTEM_DIR/docker"

    # Use sudo to run docker-compose (workaround for socket permission issue)
    sudo /usr/bin/docker-compose up -d || {
        log_error "Failed to start Docker containers"
        return 1
    }

    wait_for_health "Qdrant" "http://localhost:6333/health" $DOCKER_TIMEOUT || return 1
    wait_for_health "Neo4j" "http://localhost:7474" $DOCKER_TIMEOUT || return 1
    return 0
}

start_vllm() {
    log_info "Starting vLLM server (this takes ~60-90s to load model)..."

    nohup $VENV_VLLM/bin/python -m vllm.entrypoints.openai.api_server \
        --model $MODEL_PATH \
        --served-model-name $VLLM_MODEL_NAME \
        --host 0.0.0.0 \
        --port 8000 \
        --dtype bfloat16 \
        --max-model-len 8192 \
        --gpu-memory-utilization 0.90 \
        --trust-remote-code \
        --disable-log-requests > "$LOG_DIR/vllm.log" 2>&1 &
    echo $! > "$LOG_DIR/vllm.pid"

    wait_for_health "vLLM" "http://localhost:8000/v1/models" $VLLM_TIMEOUT || return 1
    log_success "vLLM model loaded"
    return 0
}



start_rag() {
    log_info "Starting RAG API..."

    # Use RAG venv python directly (no source needed)
    # Set PYTHONPATH to include all RAG src directories
    export PYTHONPATH="$RAG_SYSTEM_DIR/src:$RAG_SYSTEM_DIR/src/api:$RAG_SYSTEM_DIR/src/indexing:$RAG_SYSTEM_DIR/src/retrieval:$RAG_SYSTEM_DIR/src/utils:$PYTHONPATH"

    # Change to RAG API directory so imports work correctly
    cd "$RAG_SYSTEM_DIR/src/api"

    # Pass version-agnostic model name to RAG API
    nohup env VLLM_MODEL_NAME="$VLLM_MODEL_NAME" $VENV_RAG/bin/python rag_api.py > "$LOG_DIR/rag_api.log" 2>&1 &
    echo $! > "$LOG_DIR/rag_api.pid"

    wait_for_health "RAG API" "http://localhost:8081/health" $RAG_TIMEOUT || return 1
    return 0
}

start_monitor() {
    log_info "Starting health monitor..."
    
    nohup "$RAG_SYSTEM_DIR/health_monitor.sh" > "$LOG_DIR/monitor.log" 2>&1 &
    echo $! > "$LOG_DIR/monitor.pid"
    
    log_success "Health monitor started"
}

stop_all() {
    log_info "Stopping all services..."
    
    # Kill processes by PID files
    for pidfile in "$LOG_DIR"/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            kill $pid 2>/dev/null || true
            rm "$pidfile"
        fi
    done
    
    # Stop docker
    cd "$RAG_SYSTEM_DIR/docker"
    sudo /usr/bin/docker-compose down 2>/dev/null || true
    
    log_success "All services stopped"
}

status() {
    echo ""
    echo "============================================"
    echo "  Motadata AI Services Status"
    echo "============================================"
    echo ""

    for check in \
        "Qdrant:http://localhost:6333/health" \
        "Neo4j:http://localhost:7474" \
        "vLLM:http://localhost:8000/v1/models" \
        "RAG API:http://localhost:8081/health"; do

        name="${check%%:*}"
        url="${check#*:}"

        if curl -s --connect-timeout 2 "$url" > /dev/null 2>&1; then
            echo -e "  ${GREEN}●${NC} $name"
        else
            echo -e "  ${RED}●${NC} $name"
        fi
    done

    echo ""
    echo "GPU: $(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>/dev/null || echo 'N/A')"
    echo ""
}

start_all() {
    echo ""
    echo "============================================"
    echo "  Motadata AI Services Orchestrator"
    echo "============================================"
    echo ""

    local start_time=$(date +%s)

    start_docker || { log_error "Docker startup failed"; return 1; }
    echo ""

    start_vllm || { log_error "vLLM startup failed"; return 1; }
    echo ""

    start_rag || { log_error "RAG API startup failed"; return 1; }
    echo ""

    start_monitor
    echo ""

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo "============================================"
    log_success "All services started in ${duration}s"
    echo "============================================"
    echo ""

    status

    return 0
}

usage() {
    echo "Usage: $0 {start|stop|restart|status}"
    echo ""
    echo "Commands:"
    echo "  start    Start all services in order"
    echo "  stop     Stop all services"
    echo "  restart  Stop then start all services"
    echo "  status   Show current status of all services"
    echo ""
}

case "${1:-}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 5
        start_all
        ;;
    status)
        status
        ;;
    *)
        usage
        exit 1
        ;;
esac

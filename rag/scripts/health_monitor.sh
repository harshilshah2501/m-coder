#!/bin/bash
#===============================================================================
# Motadata AI Health Monitor
# Monitors GPU VRAM, system resources, and service health
#===============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/health_monitor.log"
INTERVAL=60

# Service ports
QDRANT_PORT=6333
NEO4J_PORT=7474
VLLM_BASE_PORT=8000
VLLM_WRAPPER_PORT=8080
RAG_API_PORT=8081

# Thresholds
GPU_WARN_THRESHOLD=85
GPU_CRIT_THRESHOLD=95
RAM_WARN_THRESHOLD=80

# Create log directory
mkdir -p "$LOG_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_service() {
    local port=$1
    curl -s --connect-timeout 2 "http://localhost:$port" > /dev/null 2>&1&& echo "UP" || echo "DOWN"
}

log_entry() {
    echo "$1" >> "$LOG_FILE"
    echo -e "$1"
}

# Main monitoring loop
echo "============================================"
echo "  Motadata AI Health Monitor Started"
echo "  Interval: ${INTERVAL}s | Log: $LOG_FILE"
echo "============================================"
echo ""

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # GPU metrics
    GPU_MEM_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)
    GPU_MEM_TOTAL=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
    GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | head -1)
    GPU_TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null | head -1)
    
    # Calculate GPU memory percentage
    if [ -n "$GPU_MEM_TOTAL" ] && [ "$GPU_MEM_TOTAL" -gt 0 ]; then
        GPU_MEM_PCT=$((GPU_MEM_USED * 100 / GPU_MEM_TOTAL))
    else
        GPU_MEM_PCT=0
    fi
    
    # RAM metrics
    RAM_USED=$(free -m | grep Mem | awk '{print $3}')
    RAM_TOTAL=$(free -m | grep Mem | awk '{print $2}')
    RAM_PCT=$((RAM_USED * 100 / RAM_TOTAL))
    
    # Load average
    LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    
    # Service health
    QDRANT_STATUS=$(check_service $QDRANT_PORT)
    NEO4J_STATUS=$(check_service $NEO4J_PORT)
    VLLM_BASE_STATUS=$(check_service $VLLM_BASE_PORT)
    VLLM_WRAP_STATUS=$(check_service $VLLM_WRAPPER_PORT)
    RAG_STATUS=$(check_service $RAG_API_PORT)
    
    # Format status line
    STATUS_LINE="$TIMESTAMP | GPU: ${GPU_MEM_USED}/${GPU_MEM_TOTAL}MB (${GPU_MEM_PCT}%) ${GPU_UTIL}% ${GPU_TEMP}°C | RAM: ${RAM_USED}/${RAM_TOTAL}MB (${RAM_PCT}%) | Load: $LOAD | Qdrant:$QDRANT_STATUS Neo4j:$NEO4J_STATUS vLLM:$VLLM_BASE_STATUS Wrap:$VLLM_WRAP_STATUS RAG:$RAG_STATUS"
    
    # Determine alert level and log
    if [ "$GPU_MEM_PCT" -gt "$GPU_CRIT_THRESHOLD" ]; then
        log_entry "${RED}[CRITICAL]${NC} $STATUS_LINE"
        # Could add alerting here (email, slack, etc.)
    elif [ "$GPU_MEM_PCT" -gt "$GPU_WARN_THRESHOLD" ] || [ "$RAM_PCT" -gt "$RAM_WARN_THRESHOLD" ]; then
        log_entry "${YELLOW}[WARNING]${NC} $STATUS_LINE"
    else
        log_entry "${GREEN}[OK]${NC} $STATUS_LINE"
    fi
    
    # Check for down services
    if [ "$VLLM_BASE_STATUS" = "DOWN" ] || [ "$RAG_STATUS" = "DOWN" ]; then
        log_entry "${RED}[ALERT]${NC} Critical service down! vLLM:$VLLM_BASE_STATUS RAG:$RAG_STATUS"
    fi
    
    # Rotate log if too large (>100MB)
    if [ -f "$LOG_FILE" ]; then
        LOG_SIZE=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null)
        if [ "$LOG_SIZE" -gt 104857600 ]; then
            mv "$LOG_FILE" "$LOG_FILE.old"
            log_entry "[INFO] Log rotated"
        fi
    fi
    
    sleep $INTERVAL
done


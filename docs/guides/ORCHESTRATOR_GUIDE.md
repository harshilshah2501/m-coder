# Motadata AI Services Orchestrator - Unified Management

## Overview

The **orchestrator_unified.sh** script manages all AI services in the correct chronological order with proper health checks and dependencies. It can be run directly for manual service management.

**Current Status**: ✅ V16 Model Deployed (Simplified to 4 core services, API Wrapper removed, anti-repetition integrated into RAG API)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         motadata-orchestrator.service (systemctl)           │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  orchestrator_unified.sh                             │  │
│  │                                                      │  │
│  │  1. Docker Containers (Qdrant + Neo4j)             │  │
│  │     ├─ Qdrant (port 6333)                          │  │
│  │     └─ Neo4j (port 7474)                           │  │
│  │                                                      │  │
│  │  2. vLLM Server (port 8000)                        │  │
│  │     └─ Loads motadata-coder-v16 model             │  │
│  │                                                      │  │
│  │  3. RAG API (port 8081)                            │  │
│  │     ├─ Qdrant + Neo4j + vLLM integration          │  │
│  │     └─ Anti-repetition settings applied            │  │
│  │                                                      │  │
│  │  4. Health Monitor                                  │  │
│  │     └─ Continuous monitoring of all services       │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Service Management

### Start All Services
```bash
bash runtime/rag/scripts/orchestrator_unified.sh start
```

### Stop All Services
```bash
bash runtime/rag/scripts/orchestrator_unified.sh stop
```

### Restart All Services
```bash
bash runtime/rag/scripts/orchestrator_unified.sh restart
```

### Check Status
```bash
bash runtime/rag/scripts/orchestrator_unified.sh status
```

### View Logs
```bash
# Individual service logs (repo paths)
tail -f runtime/rag/logs/vllm.log
tail -f runtime/rag/logs/api_wrapper.log
tail -f runtime/rag/logs/rag_api.log
tail -f runtime/rag/logs/monitor.log
```

## Individual Service Status & Logs

### 1. Qdrant (Vector Database)
```bash
# Check status
curl http://localhost:6333/health | jq .

# View Docker logs
docker logs qdrant-motadata -f

# Check if running
docker ps | grep qdrant
```

### 2. Neo4j (Graph Database)
```bash
# Check status
curl http://localhost:7474 | head -20

# View Docker logs
docker logs neo4j-motadata -f

# Check if running
docker ps | grep neo4j
```

### 3. vLLM (Model Server)
```bash
# Check status
curl http://localhost:8000/v1/models | jq .

# View logs
tail -f rag/logs/vllm.log

# Check process
cat rag/logs/vllm.pid
ps aux | grep $(cat rag/logs/vllm.pid)
```

### 4. API Wrapper
```bash
# Check status
curl http://localhost:8080/v1/models | jq .

# View logs
tail -f rag/logs/api_wrapper.log

# Check process
cat rag/logs/api_wrapper.pid
ps aux | grep $(cat rag/logs/api_wrapper.pid)
```

### 5. RAG API
```bash
# Check status
curl http://localhost:8081/health | jq .

# View logs
tail -f rag/logs/rag_api.log

# Check process
cat rag/logs/rag_api.pid
ps aux | grep $(cat rag/logs/rag_api.pid)
```

### 6. Health Monitor
```bash
# View logs
tail -f rag/logs/monitor.log

# Check process
cat rag/logs/monitor.pid
ps aux | grep $(cat rag/logs/monitor.pid)
```

### Quick Check All PIDs
```bash
cat rag/logs/*.pid
```

## Service Details

### 1. Docker Containers (Qdrant + Neo4j)
- **Purpose**: Vector database and graph database for RAG
- **Startup Time**: ~30-60s
- **Health Check**: HTTP 200 on `/health` endpoints
- **Ports**: 6333 (Qdrant), 7474 (Neo4j)

### 2. vLLM Server
- **Purpose**: LLM inference engine
- **Model**: motadata-coder-v16 (Latest)
- **Startup Time**: ~40-60s (model loading)
- **Port**: 8000
- **Configuration**:
  - dtype: bfloat16
  - max-model-len: 16384
  - gpu-memory-utilization: 0.45
- **Performance**:
  - Validation Loss: 0.1425 (25.8% improvement over V15)
  - Inference Pass Rate: 100% (7/7 capabilities)
  - Average Latency: 4,283ms

### 3. RAG API
- **Purpose**: Unified RAG interface combining Qdrant, Neo4j, and vLLM
- **Port**: 8081
- **Startup Time**: ~10-20s
- **Dependencies**: Qdrant, Neo4j, vLLM
- **Anti-Repetition**: Built-in with:
  - Repetition penalty: 1.2
  - Frequency penalty: 0.5
  - Presence penalty: 0.3
  - Stop tokens for loop prevention

### 4. Health Monitor
- **Purpose**: Continuous monitoring of GPU, RAM, and service health
- **Log File**: `logs/monitor.log`
- **Interval**: 60 seconds
- **Alerts**: GPU >85%, RAM >80%

## Startup Sequence

The orchestrator starts services in this order with health checks:

1. **Docker** (60s timeout)
   - Starts Qdrant and Neo4j containers
   - Waits for both to be healthy

2. **vLLM** (180s timeout)
   - Starts vLLM server
   - Waits for model to load
   - Verifies model is available

3. **RAG API** (60s timeout)
   - Starts RAG API server
   - Waits for health endpoint
   - Anti-repetition settings applied to all vLLM calls

4. **Health Monitor** (immediate)
   - Starts background monitoring

**Total Startup Time**: ~2-3 minutes (mostly vLLM model loading)

## Shutdown Sequence

When stopping the orchestrator:

1. Kills all service processes by PID
2. Stops Docker containers
3. Cleans up PID files

**Total Shutdown Time**: ~30-60 seconds

## Configuration

### Paths
- **vLLM venv**: `/home/harshil/Harshil-PoCs/venv/vllm`
- **RAG venv**: `/home/harshil/Harshil-PoCs/venv/rag`
- **Model (V16)**: `/home/harshil/Harshil-PoCs/training/artifacts/results/v16_merged`
- **RAG System**: `/home/harshil/Harshil-PoCs/rag`
- **RAG Docker**: `/home/harshil/Harshil-PoCs/rag/docker`
- **Training src**: `/home/harshil/Harshil-PoCs/training/src/utils`
- **Logs**: `/home/harshil/Harshil-PoCs/rag/logs`
- **Orchestrator**: `/home/harshil/Harshil-PoCs/rag/scripts/orchestrator_unified.sh`

### Timeouts
- Docker: 60s
- vLLM: 180s
- RAG API: 60s
- systemctl Start: 300s
- systemctl Stop: 60s

## Troubleshooting

### Service fails to start
```bash
# Check systemctl logs
journalctl -u motadata-orchestrator -n 50

# Check individual service logs
ls -lh ~/Harshil-PoCs/rag-system/logs/
```

### vLLM takes too long to load
- Increase `VLLM_TIMEOUT` in orchestrator_unified.sh
- Check GPU memory: `nvidia-smi`
- Check model path exists

### RAG API fails to start
- Verify Docker containers are running: `docker ps`
- Check RAG venv is activated
- Verify rag_api.py exists

### Health monitor not logging
- Check logs directory exists: `ls -la ~/Harshil-PoCs/rag-system/logs/`
- Verify health_monitor.sh is executable

## Manual Service Control

If you need to manage services individually:

```bash
# Start only Docker
cd ~/Harshil-PoCs/rag/docker && docker-compose up -d

# Start only vLLM (V16)
/home/harshil/Harshil-PoCs/venv/vllm/bin/python -m vllm.entrypoints.openai.api_server \
  --model /home/harshil/Harshil-PoCs/training/artifacts/results/v16_merged \
  --served-model-name motadata-coder-v16 \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype bfloat16 \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.45 \
  --trust-remote-code \
  --disable-log-requests

# Start only RAG API
cd ~/Harshil-PoCs/rag/src/api && \
export PYTHONPATH="/home/harshil/Harshil-PoCs/rag/src:/home/harshil/Harshil-PoCs/rag/src/api:/home/harshil/Harshil-PoCs/rag/src/indexing:/home/harshil/Harshil-PoCs/rag/src/retrieval:/home/harshil/Harshil-PoCs/rag/src/utils:$PYTHONPATH" && \
/home/harshil/Harshil-PoCs/venv/rag/bin/python rag_api.py
```

## Health Check Endpoints

```bash
# Qdrant
curl http://localhost:6333/health

# Neo4j
curl http://localhost:7474

# vLLM
curl http://localhost:8000/v1/models

# RAG API
curl http://localhost:8081/health
```

## Performance Monitoring

```bash
# GPU usage
nvidia-smi

# Service status
bash ~/Harshil-PoCs/rag/scripts/orchestrator_unified.sh status

# Monitor logs in real-time
tail -f ~/Harshil-PoCs/rag/logs/*.log
```

## Files

- **Orchestrator Script**: `rag/scripts/orchestrator_unified.sh`
- **Health Monitor**: `rag/health_monitor.sh`
- **Docker Compose**: `rag/docker/docker-compose.yml`
- **RAG API**: `rag/src/api/rag_api.py`
- **Logs Directory**: `rag/logs/`

## Service Architecture

The orchestrator manages the following services in order:

1. **Docker Containers** (Qdrant + Neo4j)
   - Location: `rag/docker/docker-compose.yml`
   - Ports: 6333 (Qdrant), 7474 (Neo4j)

2. **vLLM Server**
   - Venv: `venv/vllm`
   - Model: `training/artifacts/results/v16_merged` (V16 - Latest)
   - Port: 8000

3. **RAG API**
   - Script: `rag/src/api/rag_api.py`
   - Venv: `venv/rag`
   - Port: 8081
   - Anti-repetition settings: Built-in (no separate wrapper needed)

4. **Health Monitor**
   - Script: `rag/health_monitor.sh`

## V16 Model Deployment

### What's New in V16
- **Training Loss**: 0.2061 (8.3% improvement over V15)
- **Validation Loss**: 0.1425 (25.8% improvement over V15)
- **Dataset Size**: 3,020 examples (+16.2% from V15)
- **Inference Pass Rate**: 100% (7/7 capabilities)
- **Startup Time**: ~40-60s (faster than V15)

### Deployment Status
✅ **V16 is now the default model in the orchestrator**

The orchestrator automatically loads V16 when started. To verify:
```bash
curl http://localhost:8000/v1/models | jq .
# Should show: "motadata-coder-v16"
```

### Model Location
- **Path**: `/home/harshil/Harshil-PoCs/training/artifacts/results/v16_merged`
- **Evaluation Reports**: `docs/evaluation/V16_*.md`
- **Training Summary**: `docs/training/V16_TRAINING_SUMMARY.md`
- **Dataset Summary**: `docs/datasets/V16_DATASET_SUMMARY.md`

## Next Steps: Agent Orchestration Integration

The **LangGraph Orchestrator** (6-agent pipeline) is implemented but not yet integrated into the service orchestrator. This will be the next phase:

- **Location**: `rag/src/orchestrator/langgraph_orchestrator.py`
- **Wrapper**: `rag/run_orchestrator.py` (FastAPI)
- **Agents**: `rag/src/orchestrator/agents/` (6 agents: Request Analyzer, Retrieval, Coder, Format Validator, Error Handler, Code Evaluator)

**Future**: Will be integrated as a separate service or merged into RAG API as the primary code generation endpoint.

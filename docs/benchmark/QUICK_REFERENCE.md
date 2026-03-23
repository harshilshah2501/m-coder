# Quick Reference Card

## RAG-Datastore (Production System)

### Service Management
```bash
# Start/Stop/Restart all services using orchestrator (repo layout)
bash runtime/scripts/governed_services.sh start
bash runtime/scripts/governed_services.sh stop
bash runtime/scripts/governed_services.sh restart
bash runtime/scripts/governed_services.sh status

# View logs (repo layout)
tail -f runtime/rag/logs/vllm.log
tail -f runtime/rag/logs/rag_api.log
tail -f runtime/rag/logs/api_wrapper.log
tail -f runtime/rag/logs/monitor.log
```

### API Endpoints
```bash
# Health check
curl http://localhost:8081/health

# Chat (with RAG context)
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "motadata-coder", "messages": [{"role": "user", "content": "Your question"}]}'

# Semantic search
curl -X POST http://localhost:8081/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "search term", "top_k": 5}'
```

### Ports
- **8081**: RAG API (main)
- **8000**: vLLM inference
- **6333**: Qdrant vector DB
- **7474**: Neo4j UI
- **7687**: Neo4j Bolt

### Directory Quick Access
```bash
cd /home/harshil/Harshil-PoCs/RAG-Datastore

# Core system
cd rag-system/

# Documentation
cd docs/

# Run evaluations
cd evaluation/
python3 evaluate_finetuned_model.py
python3 evaluate_agentic.py

# View logs
cd rag-system/logs/
ls debug_sessions/
```

---

## Finetuning-Iter8 (Model Training)

### Training Commands
```bash
cd /home/harshil/Harshil-PoCs/Finetuning-Iter8

# Start training
bash run_training.sh

# Monitor progress
tail -f logs/training.log

# Check loss
grep "{'loss':" logs/training.log | tail -20

# Check training process
ps aux | grep train_iter8_v2
```

### After Training Completes
```bash
# 1. Merge LoRA adapter
cd /home/harshil/Harshil-PoCs/Finetuning-Iter8
source /home/harshil/Harshil-PoCs/Finetuning/venv/bin/activate
python3 scripts/merge_iter8.py

# 2. Update vLLM service
sudo sed -i 's|Finetuning-Iter6/merged_models/motadata-coder-iter6|motadata-coder-iter8|g' /etc/systemd/system/motadata-coder.service
sudo systemctl daemon-reload
sudo systemctl restart motadata-coder.service

# 3. Verify model loaded
sleep 30
curl -s http://localhost:8000/v1/models | python3 -m json.tool | grep root

# 4. Run evaluations
cd /home/harshil/Harshil-PoCs/RAG-Datastore/evaluation
python3 evaluate_finetuned_model.py
python3 evaluate_agentic.py
```

### Dataset Info
- **Total**: 15,577 examples
- **Train**: 14,798 (95%)
- **Test**: 779 (5%)

**Composition:**
- 4.4% Multi-file planning (691 examples)
- 79.5% Agentic/Tool usage (12,386 examples)
- 16.0% Direct answers (2,500 examples)

### Training Stats
- **Total Steps**: 1,850 (2 epochs)
- **Batch Size**: 16 effective (2 × 8 grad accum)
- **GPU**: H100 (79GB)
- **Duration**: ~2-3 hours
- **Checkpoints**: Every epoch

### Troubleshooting
```bash
# Check GPU
nvidia-smi

# Check training process
ps aux | grep train_iter8

# View full log
less logs/training.log

# Check last error
tail -100 logs/training.log | grep -i error
```

---

## Common Tasks

### Index a New Project
```bash
cd /home/harshil/Harshil-PoCs/RAG-Datastore/rag-system
python3 project_indexer.py /path/to/project
```

### Re-index Existing Project
```bash
cd /home/harshil/Harshil-PoCs/RAG-Datastore/rag-system
# Delete existing index
curl -X DELETE http://localhost:6333/collections/motadata_codebase
# Re-index
python3 project_indexer.py /path/to/project
```

### View Model Performance
```bash
cd /home/harshil/Harshil-PoCs/RAG-Datastore/evaluation

# View latest results
ls -lt evaluation_report_*.json | head -1 | xargs cat | python3 -m json.tool

# Compare iterations
cat evaluation_report_iter6.json | jq '.summary'
cat evaluation_report_iter7.json | jq '.summary'
```

### Debug RAG API
```bash
cd /home/harshil/Harshil-PoCs/RAG-Datastore/rag-system/logs

# List debug sessions
ls -lt debug_sessions/

# View latest session
ls -t debug_sessions/*.json | head -1 | xargs cat | python3 -m json.tool
```

---

## File Locations

### Configuration
- systemd services: `/etc/systemd/system/motadata-*.service`
- Docker compose: `RAG-Datastore/rag-system/docker-compose.yml`
- vLLM config: See systemd service file

### Data
- Qdrant storage: `RAG-Datastore/rag-system/qdrant_storage/`
- Neo4j data: `RAG-Datastore/rag-system/neo4j_data/`
- Training datasets: `Finetuning-Iter8/datasets/`

### Logs
- RAG API: `RAG-Datastore/rag-system/logs/`
- Training: `Finetuning-Iter8/logs/`
- systemd: `sudo journalctl -u motadata-*`

### Models
- Current: Check systemd service or `curl localhost:8000/v1/models`
- Iter6: `/home/harshil/Harshil-PoCs/Finetuning-Iter6/merged_models/motadata-coder-iter6`
- Iter8: `/home/harshil/Harshil-PoCs/motadata-coder-iter8` (after merge)

---

## Emergency Commands

### Restart Everything
```bash
bash runtime/scripts/governed_services.sh restart
```

### Kill Stuck Processes
```bash
pkill -f "python.*rag_api.py"
pkill -f "vllm.entrypoints"
pkill -f "api_server.py"
```

### Free GPU Memory
```bash
# Stop all services
bash runtime/scripts/governed_services.sh stop

# Check GPU
nvidia-smi

# Restart all services
bash runtime/scripts/governed_services.sh start
```

### Reset Qdrant
```bash
cd rag/docker
docker-compose down
rm -rf qdrant_storage/
docker-compose up -d
# Wait for Qdrant to start
sleep 10
# Re-index
python3 project_indexer.py /path/to/project
```

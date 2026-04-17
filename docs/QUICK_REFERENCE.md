# Quick Reference Guide

**Last Updated**: January 5, 2026
**Current Model**: V16 (Production Ready)
**Service Management**: `runtime/scripts/governed_services.sh`

---

## System Status

| Component | Status | Port | Health Check |
|-----------|--------|------|--------------|
| **Qdrant** | ✅ Running | 6333 | `curl http://localhost:6333/health` |
| **Neo4j** | ✅ Running | 7687 | `curl http://localhost:7474` |
| **RAG API** | ✅ Running | 8081 | `curl http://localhost:8081/health` |
| **vLLM** | ✅ Running | 8000 | `curl http://localhost:8000/v1/models` |
| **Runtime Stack** | ✅ Script-managed | - | `bash runtime/scripts/governed_services.sh status` |

---

## Key Paths

```
~/Harshil-PoCs/
├── venv/training/               # Training environment
├── venv/vllm/                   # vLLM environment
├── venv/rag/                    # RAG environment
├── training/artifacts/results/  # Model artifacts & evaluation reports
├── rag/src/                     # RAG source code
├── rag/scripts/                 # Orchestration scripts
└── docs/                        # Documentation
```

---

## Quick Commands

### Service Management (Current)

#### Start Services
```bash
bash runtime/scripts/governed_services.sh start
```

#### Stop Services
```bash
bash runtime/scripts/governed_services.sh stop
```

#### Restart Services
```bash
bash runtime/scripts/governed_services.sh restart
```

#### Check Service Status
```bash
bash runtime/scripts/governed_services.sh status
```

#### View Service Logs
```bash
bash runtime/scripts/governed_services.sh logs
```

### Optional Local systemd Wrapper
```bash
# Optional: author your own local unit that wraps governed_services.sh
# The repository does not ship motadata-orchestrator.service anymore.
```

### Check Logs
```bash
# RAG API logs
tail -f logs/rag/rag_api.log

# Training logs
tail -f training/artifacts/logs/training_v16.log

# Qdrant logs
docker logs qdrant-motadata -f

# Neo4j logs
docker logs neo4j-motadata -f
```

### Test Query
```bash
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "motadata-coder",
    "messages": [{"role": "user", "content": "How to create a new ConfigStore?"}],
    "temperature": 0.1,
    "max_tokens": 4096
  }' | jq -r '.choices[0].message.content'
```

### View Diagnostics
```bash
# Latest session
curl http://localhost:8081/v1/diagnostics/session/latest | jq .

# Specific session
curl http://localhost:8081/v1/diagnostics/session/{session_id} | jq .

# List all sessions
curl http://localhost:8081/v1/diagnostics/sessions | jq .
```

---

## Common Issues & Solutions

### Issue: "Connection refused" on startup
**Cause**: Qdrant/Neo4j still initializing  
**Solution**: Wait 30 seconds, retry logic handles this automatically

### Issue: Low confidence scores
**Cause**: Query too vague or missing context  
**Solution**: Rephrase query with more specific terms

### Issue: Wrong file format (diffs for new files)
**Cause**: Intent detection failed  
**Solution**: Use explicit keywords: "create", "new class", "generate"

### Issue: Hallucinated code
**Cause**: Low-quality retrieval results  
**Solution**: Check diagnostics, verify RAG context quality

---

## Performance Benchmarks

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Retrieval Accuracy | >90% | 94% | ✅ |
| Hallucination Rate | <10% | 8% | ✅ |
| Response Time | <3s | 2.4s | ✅ |
| Startup Success | >95% | 100% | ✅ |
| Uptime | >99% | 99.9% | ✅ |

---

## API Endpoints

### Chat Completion (OpenAI-compatible)
```
POST /v1/chat/completions
```

### Diagnostics
```
GET /v1/diagnostics/session/latest
GET /v1/diagnostics/session/{session_id}
GET /v1/diagnostics/sessions
```

### Health Check
```
GET /health
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| `rag-system/rag_api.py` | Main RAG API server |
| `rag-system/config.yaml` | RAG configuration |
| `docker-compose.yml` | Docker services |
| `.continue/config.json` | Continue.dev integration |

---

## Key Metrics to Monitor

1. **Retrieval Accuracy**: % of relevant results
2. **Hallucination Rate**: % of non-existent code references
3. **Response Time**: Average query latency
4. **Confidence Distribution**: High/Medium/Low ratio
5. **Error Rate**: Failed queries / total queries

---

## Troubleshooting Checklist

- [ ] All Docker containers running?
- [ ] RAG API responding to health check?
- [ ] Qdrant collection exists? (`curl http://localhost:6333/collections`)
- [ ] Neo4j accessible? (`curl http://localhost:7474`)
- [ ] vLLM model loaded? (`curl http://localhost:8000/v1/models`)
- [ ] Check logs for errors
- [ ] Verify diagnostics endpoint working

---

## Service Management Documentation

For detailed runtime stack management, see:
- **[ORCHESTRATOR_SERVICE_GUIDE.md](guides/ORCHESTRATOR_SERVICE_GUIDE.md)** - Complete service management guide
## Contact & Resources

- **Documentation**: `/docs/RAG_SYSTEM_ITERATIONS_ANALYSIS.md`
- **Architecture Diagram**: See main documentation
- **Issue Tracker**: Check diagnostics for session details
- **Service Guide**: See ORCHESTRATOR_SERVICE_GUIDE.md for current runtime stack management



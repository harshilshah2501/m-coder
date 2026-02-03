# Agentic Framework Implementation Plan

## Phase 1: Environment Setup & Dependencies (Today)

### Step 1.1: Install Dependencies
```bash
cd ~/Harshil-PoCs/rag
pip install -r requirements.txt
```

**Key packages:**
- `langgraph` - State machine orchestration
- `httpx` - Async HTTP client for vLLM calls
- `tree-sitter` - Code parsing for error detection
- `pydantic` - Data validation

### Step 1.2: Verify External Services
```bash
# Check vLLM
curl http://localhost:8000/v1/models

# Check Qdrant
curl http://localhost:6333/health

# Check Neo4j (optional)
curl http://localhost:7474/browser/
```

### Step 1.3: Create FastAPI Wrapper
Create `rag/run_orchestrator.py` with:
- `/generate` endpoint
- `/health` endpoint
- `/analyze` endpoint
- CORS middleware

---

## Phase 2: Agent Implementation (Week 1)

### Step 2.1: Request Analyzer Agent
**File**: `rag/src/orchestrator/agents/request_analyzer.py`
- [x] File created with stub
- [ ] Implement vLLM integration
- [ ] Test with sample requests
- [ ] Validate output schema

### Step 2.2: Retrieval Agent
**File**: `rag/src/orchestrator/agents/retrieval_agent.py`
- [x] File created with stub
- [ ] Implement search query generation
- [ ] Implement Qdrant search
- [ ] Implement Neo4j search
- [ ] Test result ranking

### Step 2.3: Coder Agent
**File**: `rag/src/orchestrator/agents/coder_agent.py`
- [x] File created with stub
- [ ] Implement vLLM code generation
- [ ] Implement search/replace block formatting
- [ ] Test with sample requirements

### Step 2.4: Format Validator Agent
**File**: `rag/src/orchestrator/agents/format_validator.py`
- [x] File created with pure Python implementation
- [ ] Test search/replace block validation
- [ ] Test markdown validation
- [ ] Test auto-fix capabilities

### Step 2.5: Error Handler Agent
**File**: `rag/src/orchestrator/agents/error_handler.py`
- [x] File created with stub
- [ ] Implement Tree-sitter integration
- [ ] Implement syntax error detection
- [ ] Implement LLM-based error fixing

### Step 2.6: Code Evaluator Agent
**File**: `rag/src/orchestrator/agents/code_evaluator.py`
- [x] File created with stub
- [ ] Implement quality scoring
- [ ] Implement architectural alignment check
- [ ] Test evaluation output

---

## Phase 3: Integration Testing (Week 1-2)

### Step 3.1: Unit Tests
- [ ] Test each agent individually
- [ ] Test with mock data
- [ ] Verify output schemas

### Step 3.2: Integration Tests
- [ ] Test full pipeline
- [ ] Test retry logic
- [ ] Test error handling
- [ ] Test with real vLLM

### Step 3.3: End-to-End Tests
- [ ] Test complete request flow
- [ ] Test with real Qdrant data
- [ ] Test with real Neo4j data
- [ ] Performance benchmarking

---

## Phase 4: Deployment (Week 2-3)

### Step 4.1: Local Deployment
- [ ] Start vLLM service
- [ ] Start Qdrant service
- [ ] Start Orchestrator
- [ ] Test endpoints

### Step 4.2: Docker Deployment
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml
- [ ] Build and test Docker image
- [ ] Document Docker setup

### Step 4.3: Production Deployment
- [ ] Set up monitoring
- [ ] Set up logging
- [ ] Configure health checks
- [ ] Document deployment

---

## Current Status

✅ **Completed:**
- All agent files created
- Orchestrator state machine designed
- Master documentation created
- Requirements updated
- Dependencies installed (langgraph, httpx, tree-sitter, etc.)
- FastAPI wrapper created (`run_orchestrator.py`)
- Test script created (`test_orchestrator.py`)
- Orchestrator tested successfully ✅

⏳ **In Progress:**
- Implement Request Analyzer agent with vLLM integration
- Implement Retrieval Agent with Qdrant/Neo4j integration

📋 **Next:**
- Implement remaining agents
- Integration testing
- Performance optimization

---

## Quick Commands

```bash
# Install dependencies
pip install -r rag/requirements.txt

# Run orchestrator
python rag/run_orchestrator.py

# Test endpoint
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create UserAPI endpoint", "context": {}}'

# Check logs
tail -f rag/logs/orchestrator.log
```

---

## Success Criteria

- [ ] All agents implemented
- [ ] All tests passing
- [ ] Full pipeline working
- [ ] Deployed and running
- [ ] Performance targets met (30s total latency)
- [ ] Quality targets met (≥0.7 code score)


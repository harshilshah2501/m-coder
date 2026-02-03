# Request Analyzer & Retrieval Agent - Implementation Guide

## Phase Overview

This guide covers the implementation of two critical PRE Phase agents:
1. **Request Analyzer Agent** - Validates and structures user requests
2. **Retrieval Agent** - Fetches relevant code context from RAG

---

## Implementation Checklist

### Request Analyzer Agent

- [x] Core implementation exists (`request_analyzer.py`)
- [ ] Add comprehensive error handling
- [ ] Add request caching (optional)
- [ ] Add metrics/logging
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Performance evaluation

### Retrieval Agent

- [x] Core implementation exists (`retrieval_agent.py`)
- [ ] **FIX**: Update to use correct RAG API endpoints
  - Current: `/search` endpoint (doesn't exist)
  - Should use: `/search/semantic`, `/search/graph`, `/search/hybrid`
- [ ] Add hybrid search support
- [ ] Add anti-hallucination verification
- [ ] Add result caching
- [ ] Add metrics/logging
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Performance evaluation

---

## Key Issues to Address

### 1. Retrieval Agent API Endpoints

**Current Implementation** (INCORRECT):
```python
response = await self.client.post(
    f"{self.rag_url}/search",
    json={"query": query, "type": "pattern", "top_k": 5}
)
```

**Should Be** (CORRECT):
```python
# For semantic search
response = await self.client.post(
    f"{self.rag_url}/search/semantic",
    json={"query": query, "top_k": 5, "node_type": "class"}
)

# For graph search
response = await self.client.post(
    f"{self.rag_url}/search/graph",
    json={"entity_name": "ClassName", "relation_type": "all", "depth": 2}
)

# For hybrid search (recommended)
response = await self.client.post(
    f"{self.rag_url}/search/hybrid",
    json={
        "query": query,
        "top_k": 5,
        "include_callers": True,
        "include_callees": True
    }
)
```

### 2. Response Format Handling

RAG API returns `CodeContext` objects with:
- `qualified_name`: Full class/method name
- `file_path`: Location in codebase
- `code_snippet`: Actual code
- `confidence`: "low" | "medium" | "high"
- `node_type`: "class" | "method" | "function"

---

## Testing Strategy

### Unit Tests
- Test Request Analyzer with various input types
- Test Retrieval Agent search query generation
- Test result ranking and deduplication

### Integration Tests
- Test full pipeline: Request → Analysis → Retrieval
- Test with actual vLLM service
- Test with actual Qdrant/Neo4j services

### Performance Tests
- Measure latency for each agent
- Measure token usage
- Measure search result quality

---

## Configuration Management

### Environment Variables
```bash
# Request Analyzer
VLLM_URL=http://localhost:8000
VLLM_MODEL=motadata-coder

# Retrieval Agent
RAG_URL=http://localhost:8081
QDRANT_HOST=localhost
QDRANT_PORT=6333
NEO4J_URI=bolt://localhost:7687
```

### Service Dependencies
- vLLM service (port 8000)
- RAG API service (port 8081)
- Qdrant (port 6333)
- Neo4j (port 7687)

---

## Success Criteria

### Request Analyzer
- ✅ 100% valid request detection
- ✅ <1s latency for analysis
- ✅ Confidence score > 0.8 for valid requests

### Retrieval Agent
- ✅ >80% relevant results
- ✅ <3s latency for retrieval
- ✅ Coverage score > 0.6 for typical requests

---

## Next Steps

1. Fix Retrieval Agent API endpoints
2. Add comprehensive error handling
3. Implement caching layer
4. Write test suites
5. Run performance evaluation
6. Document findings


# Agent Architecture & Integration

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENTIC FRAMEWORK                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              ORCHESTRATOR (Main Coordinator)             │  │
│  │  - Manages agent lifecycle                              │  │
│  │  - Passes state between agents                          │  │
│  │  - Handles error recovery                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                     │
│         ┌─────────────────┼─────────────────┐                  │
│         │                 │                 │                  │
│    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐              │
│    │ Request │      │Retrieval │      │  Coder  │              │
│    │Analyzer │      │  Agent   │      │  Agent  │              │
│    └────┬────┘      └────┬────┘      └────┬────┘              │
│         │                │                │                    │
│         └────────────────┼────────────────┘                    │
│                          │                                     │
└──────────────────────────┼─────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    ┌───▼────┐        ┌───▼────┐        ┌───▼────┐
    │ vLLM   │        │ Qdrant │        │ Neo4j  │
    │ (8000) │        │ (6333) │        │(7687)  │
    └────────┘        └────────┘        └────────┘
```

---

## Agent State Flow

### State Object Structure
```python
{
    # Input
    "user_request": str,
    "conversation_history": list,
    "codebase_context": dict,
    
    # After Request Analyzer
    "request_analysis": {
        "status": str,
        "extracted_requirements": dict,
        "confidence_score": float
    },
    
    # After Retrieval Agent
    "retrieved_context": {
        "patterns": list,
        "examples": list,
        "coverage_score": float
    },
    
    # After Coder Agent
    "generated_code": {
        "code": str,
        "search_replace_blocks": list,
        "confidence_score": float
    }
}
```

---

## Agent Responsibilities

### Request Analyzer
**Input**: User request + context
**Output**: Structured requirements
**Key Tasks**:
1. Parse natural language request
2. Extract programming language, frameworks, patterns
3. Validate against Motadata stack
4. Generate clarification questions if needed

### Retrieval Agent
**Input**: Extracted requirements
**Output**: Relevant code patterns & examples
**Key Tasks**:
1. Generate targeted search queries
2. Search Qdrant for semantic matches
3. Search Neo4j for graph relationships
4. Rank and deduplicate results

### Coder Agent
**Input**: Requirements + retrieved context
**Output**: Generated code with search/replace blocks
**Key Tasks**:
1. Analyze requirements and context
2. Generate code using vLLM
3. Format as search/replace blocks
4. Validate format and syntax

---

## Service Dependencies

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| vLLM | 8000 | LLM inference | ✅ Running |
| RAG API | 8081 | Search & retrieval | ✅ Running |
| Qdrant | 6333 | Vector DB | ✅ Running |
| Neo4j | 7687 | Graph DB | ✅ Running |

---

## Error Handling Strategy

### Request Analyzer Errors
- Invalid JSON response → Retry with different temperature
- Timeout → Return FAILED status
- Validation failure → Return NEEDS_CLARIFICATION

### Retrieval Agent Errors
- Search timeout → Return PARTIAL status
- No results → Return empty lists
- API error → Fallback to basic queries

### Recovery Mechanisms
1. Automatic retry with exponential backoff
2. Fallback to simpler queries
3. Graceful degradation (partial results)
4. Clear error messages for user

---

## Performance Targets

| Agent | Metric | Target | Current |
|-------|--------|--------|---------|
| Request Analyzer | Latency | <1s | TBD |
| Request Analyzer | Accuracy | >95% | TBD |
| Retrieval Agent | Latency | <3s | TBD |
| Retrieval Agent | Relevance | >80% | TBD |
| Coder Agent | Latency | <10s | 6.92s ✅ |
| Coder Agent | Success | >95% | 100% ✅ |

---

## Integration Points

### With vLLM
- Chat completions API for LLM calls
- Streaming support for long responses
- Token counting for cost tracking

### With RAG API
- Semantic search for code patterns
- Graph search for relationships
- Hybrid search for comprehensive context
- Anti-hallucination verification

### With Orchestrator
- State passing between agents
- Error handling and recovery
- Logging and monitoring
- Result aggregation

---

## Future Enhancements

1. **Caching Layer**: Cache search results and LLM responses
2. **Parallel Execution**: Run agents in parallel where possible
3. **Feedback Loop**: Learn from user feedback
4. **Cost Optimization**: Track token usage and optimize
5. **Advanced Ranking**: ML-based result ranking


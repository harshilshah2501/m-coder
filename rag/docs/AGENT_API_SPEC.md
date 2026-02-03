# Agent API Specifications

## Request Analyzer Agent API

### Endpoint
```
POST /agents/request-analyzer/run
```

### Request Body
```json
{
  "user_request": "Create a REST endpoint for user authentication",
  "conversation_history": [
    "Previous message 1",
    "Previous message 2"
  ],
  "codebase_context": {
    "primary_language": "Java",
    "frameworks": ["Vert.x", "Jackson"],
    "architectural_style": "Event-Driven"
  }
}
```

### Response (Success)
```json
{
  "status": "VALID",
  "extracted_requirements": {
    "programming_language": "Java",
    "frameworks": ["Vert.x"],
    "architecture_pattern": "REST API",
    "functional_requirements": [
      "Handle user login",
      "Validate credentials",
      "Return JWT token"
    ],
    "non_functional_requirements": {
      "performance": "Response time < 500ms",
      "security": "Use HTTPS, hash passwords"
    },
    "organizational_constraints": [
      "Follow Motadata code style",
      "Use existing auth patterns"
    ]
  },
  "clarification_questions": [],
  "confidence_score": 0.92
}
```

### Response (Needs Clarification)
```json
{
  "status": "NEEDS_CLARIFICATION",
  "extracted_requirements": {...},
  "clarification_questions": [
    "Should this use OAuth2 or JWT?",
    "What's the expected user volume?"
  ],
  "confidence_score": 0.65
}
```

---

## Retrieval Agent API

### Endpoint
```
POST /agents/retrieval/run
```

### Request Body
```json
{
  "request_analysis": {
    "extracted_requirements": {
      "programming_language": "Java",
      "frameworks": ["Vert.x"],
      "functional_requirements": ["REST endpoint", "Authentication"]
    }
  },
  "task_type": "NEW_FEATURE"
}
```

### Response (Success)
```json
{
  "status": "SUCCESS",
  "retrieved_patterns": [
    {
      "pattern_name": "REST Endpoint Pattern",
      "file_path": "src/main/java/com/motadata/api/UserController.java",
      "snippet": "public void handleGetUser(RoutingContext ctx) { ... }",
      "relevance_score": 0.95,
      "node_type": "method",
      "qualified_name": "UserController.handleGetUser"
    }
  ],
  "retrieved_examples": [
    {
      "example_name": "Authentication Example",
      "file_path": "src/main/java/com/motadata/auth/AuthHandler.java",
      "code_snippet": "public class AuthHandler { ... }",
      "relevance_score": 0.88,
      "node_type": "class",
      "qualified_name": "AuthHandler"
    }
  ],
  "search_queries_used": [
    "Vert.x REST endpoint handler",
    "JWT authentication Java",
    "Motadata API pattern"
  ],
  "coverage_score": 0.85
}
```

### Response (Partial)
```json
{
  "status": "PARTIAL",
  "retrieved_patterns": [...],
  "retrieved_examples": [],
  "search_queries_used": [...],
  "coverage_score": 0.45,
  "warning": "Limited examples found. Consider providing more context."
}
```

---

## RAG API Endpoints Used

### Semantic Search
```
POST /search/semantic
Content-Type: application/json

{
  "query": "REST endpoint handler",
  "top_k": 5,
  "node_type": "method"
}
```

### Graph Search
```
POST /search/graph
Content-Type: application/json

{
  "entity_name": "UserController",
  "relation_type": "CALLS",
  "depth": 2
}
```

### Hybrid Search (Recommended)
```
POST /search/hybrid
Content-Type: application/json

{
  "query": "REST endpoint authentication",
  "top_k": 5,
  "include_callers": true,
  "include_callees": true
}
```

### Anti-Hallucination Verification
```
POST /verify
Content-Type: application/json

{
  "query": "REST endpoint pattern",
  "min_results": 1
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request format",
  "details": "Missing required field: user_request"
}
```

### 503 Service Unavailable
```json
{
  "error": "vLLM service unavailable",
  "status": "FAILED",
  "retry_after": 30
}
```

### 504 Gateway Timeout
```json
{
  "error": "Request timeout",
  "status": "FAILED",
  "timeout_seconds": 30
}
```

---

## Rate Limiting

- **Request Analyzer**: 100 req/min per user
- **Retrieval Agent**: 50 req/min per user
- **Burst Limit**: 10 requests

---

## Timeout Configuration

| Agent | Timeout | Notes |
|-------|---------|-------|
| Request Analyzer | 30s | vLLM inference |
| Retrieval Agent | 30s | Search operations |
| vLLM | 30s | Model inference |
| Qdrant | 10s | Vector search |
| Neo4j | 10s | Graph traversal |


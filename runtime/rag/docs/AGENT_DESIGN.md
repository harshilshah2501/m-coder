# Request Analyzer & Retrieval Agent Design

## Overview

These two agents work together in the **PRE Phase** of the agentic pipeline to:
1. **Request Analyzer**: Understand and validate user requests
2. **Retrieval Agent**: Fetch relevant context from the codebase

---

## 1. Request Analyzer Agent

### Purpose
Transform natural language user requests into structured, validated requirements that downstream agents can use.

### Input Schema
```python
{
    "user_request": str,           # Natural language request
    "conversation_history": list,  # Previous messages for context
    "codebase_context": {
        "primary_language": str,   # e.g., "Java"
        "frameworks": list,        # e.g., ["Vert.x"]
        "architectural_style": str # e.g., "Event-Driven"
    }
}
```

### Output Schema
```python
{
    "status": "VALID" | "INVALID" | "NEEDS_CLARIFICATION",
    "extracted_requirements": {
        "programming_language": str,
        "frameworks": list[str],
        "architecture_pattern": str,
        "functional_requirements": list[str],
        "non_functional_requirements": {
            "performance": str,
            "security": str
        },
        "organizational_constraints": list[str]
    },
    "clarification_questions": list[str],  # If status is NEEDS_CLARIFICATION
    "confidence_score": float  # 0.0-1.0
}
```

### Validation Rules
| Rule | Action |
|------|--------|
| Language not Java | Flag as NEEDS_CLARIFICATION |
| Unknown framework | Flag as INVALID |
| Contradictory requirements | Flag as NEEDS_CLARIFICATION |
| Vague request | Generate clarification questions |

### vLLM Integration
- **Model**: `motadata-coder`
- **Temperature**: 0.3 (low for consistency)
- **Max Tokens**: 1000
- **Output Format**: JSON only

---

## 2. Retrieval Agent

### Purpose
Fetch relevant code patterns, examples, and context from RAG (Qdrant + Neo4j) to ground code generation.

### Input Schema
```python
{
    "request_analysis": {
        "extracted_requirements": {...}  # From Request Analyzer
    },
    "task_type": "NEW_FEATURE" | "BUG_FIX" | "REFACTOR" | "ENHANCEMENT"
}
```

### Output Schema
```python
{
    "status": "SUCCESS" | "PARTIAL" | "FAILED",
    "retrieved_patterns": [
        {
            "pattern_name": str,
            "file_path": str,
            "snippet": str,
            "relevance_score": float
        }
    ],
    "retrieved_examples": [
        {
            "example_name": str,
            "file_path": str,
            "code_snippet": str,
            "relevance_score": float
        }
    ],
    "search_queries_used": list[str],
    "coverage_score": float  # 0.0-1.0
}
```

### Search Strategy
1. **Generate Queries**: Use vLLM to create 3-5 targeted search queries
2. **Semantic Search**: Query Qdrant for similar code patterns
3. **Graph Search**: Query Neo4j for related classes/methods
4. **Rank & Deduplicate**: Sort by relevance, remove duplicates

### RAG API Endpoints Used
| Endpoint | Purpose |
|----------|---------|
| `POST /search/semantic` | Vector similarity search |
| `POST /search/graph` | Graph traversal (callers/callees) |
| `POST /search/hybrid` | Combined search |
| `POST /verify` | Anti-hallucination check |

---

## Data Flow Diagram

```mermaid
flowchart TB
    subgraph Input["📥 Input"]
        UR[User Request]
        CH[Conversation History]
        CC[Codebase Context]
    end

    subgraph RA["🔍 Request Analyzer Agent"]
        RA1[Parse User Request]
        RA2[Extract Requirements via vLLM]
        RA3[Validate Against Motadata Stack]
        RA4[Generate Structured Output]
    end

    subgraph RAOutput["📋 Request Analysis Output"]
        REQ[Extracted Requirements]
        LANG[Programming Language]
        FW[Frameworks]
        FUNC[Functional Requirements]
        NFR[Non-Functional Requirements]
    end

    subgraph RET["🔎 Retrieval Agent"]
        RET1[Generate Search Queries via vLLM]
        RET2[Semantic Search - Qdrant]
        RET3[Graph Search - Neo4j]
        RET4[Rank & Deduplicate Results]
    end

    subgraph RETOutput["📦 Retrieval Output"]
        PAT[Retrieved Patterns]
        EX[Retrieved Examples]
        REL[Related Code]
    end

    subgraph Next["➡️ Next Phase"]
        CODER[Coder Agent]
    end

    UR --> RA1
    CH --> RA1
    CC --> RA1
    RA1 --> RA2
    RA2 --> RA3
    RA3 --> RA4
    RA4 --> REQ
    REQ --> LANG
    REQ --> FW
    REQ --> FUNC
    REQ --> NFR

    REQ --> RET1
    RET1 --> RET2
    RET1 --> RET3
    RET2 --> RET4
    RET3 --> RET4
    RET4 --> PAT
    RET4 --> EX
    RET4 --> REL

    PAT --> CODER
    EX --> CODER
    REL --> CODER
    REQ --> CODER

    style RA fill:#e1f5fe,stroke:#01579b
    style RET fill:#f3e5f5,stroke:#4a148c
    style RAOutput fill:#e8f5e9,stroke:#1b5e20
    style RETOutput fill:#fff3e0,stroke:#e65100
```

---

## Sequence Diagram: Request Analyzer & Retrieval Agent Interaction

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant RA as Request Analyzer
    participant vLLM
    participant RET as Retrieval Agent
    participant Qdrant
    participant Neo4j
    participant Coder as Coder Agent

    User->>Orchestrator: Send user request
    Orchestrator->>RA: run(state)

    RA->>RA: Parse user request
    RA->>vLLM: Extract requirements (chat/completions)
    vLLM-->>RA: Structured requirements JSON

    RA->>RA: Validate against Motadata stack
    RA-->>Orchestrator: Return analysis result

    Orchestrator->>RET: run(state with analysis)

    RET->>vLLM: Generate search queries
    vLLM-->>RET: 3-5 search queries

    par Parallel Search
        RET->>Qdrant: Semantic search (query 1-5)
        Qdrant-->>RET: Ranked patterns & examples
    and
        RET->>Neo4j: Graph search (relationships)
        Neo4j-->>RET: Related classes/methods
    end

    RET->>RET: Rank & deduplicate results
    RET-->>Orchestrator: Return patterns + examples

    Orchestrator->>Coder: run(state with context)
    Coder->>vLLM: Generate code with context
    vLLM-->>Coder: Generated code
    Coder-->>Orchestrator: Return generated code

    Orchestrator-->>User: Final code output
```

---

## Configuration

```yaml
request_analyzer:
  vllm_url: "http://localhost:8000"
  model: "motadata-coder"
  temperature: 0.3
  max_tokens: 1000
  timeout: 30s

retrieval_agent:
  vllm_url: "http://localhost:8000"
  rag_url: "http://localhost:8081"
  model: "motadata-coder"
  search_top_k: 5
  min_confidence: 0.3
  timeout: 30s
```

---

## Next Steps

1. Update Retrieval Agent to use correct RAG API endpoints
2. Add hybrid search support
3. Implement anti-hallucination verification
4. Add caching for repeated queries


# Motadata Agentic Orchestrator

## Overview

The Orchestrator is a LangGraph-based state machine that coordinates multiple specialized agents to generate high-quality code with built-in validation, error handling, and quality assurance.

## Architecture

```
User Request (Port 8080)
    ↓
[ORCHESTRATOR - LangGraph State Machine]
    ├─ PRE Phase: Request Analysis + Context Retrieval
    ├─ CORE Phase: Code Generation
    └─ POST Phase: Format Validation + Error Handling + Quality Evaluation
    ↓
Final Output (Code + Metadata)
```

## Agents

### PRE Phase (Request Understanding)

#### 1. Request Analyzer
- **Type**: LLM-based
- **Purpose**: Analyze user request and extract structured requirements
- **Input**: User request, conversation history, codebase context
- **Output**: Validated requirements, confidence score
- **Latency**: ~2-3s

#### 2. Retrieval Agent
- **Type**: LLM + RAG
- **Purpose**: Retrieve relevant patterns and examples from knowledge base
- **Input**: Extracted requirements, task type
- **Output**: Ranked patterns and examples
- **Latency**: ~3-5s

### CORE Phase (Code Generation)

#### 3. Coder Agent
- **Type**: vLLM (V15 Fine-tuned)
- **Purpose**: Generate code for specific file
- **Input**: Requirements, retrieved context, previous attempts
- **Output**: Generated code with search/replace blocks
- **Latency**: ~2-3s per file
- **Retries**: Up to 3 attempts

### POST Phase (Quality Assurance)

#### 4. Format Validator
- **Type**: Pure Python (No LLM)
- **Purpose**: Validate search/replace block structure
- **Input**: Generated code
- **Output**: Validation status, errors, warnings
- **Latency**: ~0.5s

#### 5. Error Handler
- **Type**: Hybrid (Tree-sitter + LLM)
- **Purpose**: Detect and fix syntax/logical errors
- **Input**: Generated code
- **Output**: Fixed code, list of fixes
- **Latency**: ~2-3s

#### 6. Code Evaluator
- **Type**: LLM-based
- **Purpose**: Assess code quality and adherence to standards
- **Input**: Generated code, requirements
- **Output**: Quality score, detailed evaluations
- **Latency**: ~2-3s

## State Machine Flow

```
START
  ↓
REQUEST_RECEIVED
  ↓
ANALYZE_REQUEST (Request Analyzer)
  ├─ VALID → RETRIEVE_CONTEXT
  ├─ INVALID → RETURN_ERROR
  └─ NEEDS_CLARIFICATION → RETURN_ERROR
  ↓
RETRIEVE_CONTEXT (Retrieval Agent)
  ↓
GENERATE_CODE (Coder Agent)
  ↓
VALIDATE_FORMAT (Format Validator)
  ├─ VALID → HANDLE_ERRORS
  └─ INVALID → RETRY_GENERATION (max 3 times)
  ↓
HANDLE_ERRORS (Error Handler)
  ↓
EVALUATE_CODE (Code Evaluator)
  ├─ PASS → RETURN_SUCCESS
  ├─ WARN → RETURN_SUCCESS (with warnings)
  └─ FAIL → RETURN_ERROR
  ↓
END
```

## Configuration

See `AGENT_FRAMEWORK_SPEC.md` for detailed configuration options:
- Retry limits
- Confidence thresholds
- Latency budgets
- RAG parameters

## Usage

### Basic Usage

```python
from orchestrator.langgraph_orchestrator import Orchestrator

orchestrator = Orchestrator()

result = await orchestrator.process_request(
    user_request="Create a new UserAPI endpoint",
    conversation_history=[],
    codebase_context={
        "primary_language": "Java",
        "frameworks": ["Vert.x"],
        "architectural_style": "Event-Driven"
    }
)

print(result)
# {
#   "status": "SUCCESS",
#   "generated_code": "...",
#   "quality_score": 0.85,
#   "evaluation": {...}
# }
```

### Integration with FastAPI

```python
from fastapi import FastAPI
from orchestrator.langgraph_orchestrator import Orchestrator

app = FastAPI()
orchestrator = Orchestrator()

@app.post("/generate")
async def generate_code(request: dict):
    result = await orchestrator.process_request(
        user_request=request["prompt"],
        conversation_history=request.get("history", []),
        codebase_context=request.get("context", {})
    )
    return result
```

## Error Handling

| Error Code | Phase | Meaning | Action |
|-----------|-------|---------|--------|
| REQ_INVALID | PRE | Request validation failed | Return error to user |
| REQ_UNCLEAR | PRE | Needs clarification | Ask user for details |
| RETRIEVAL_FAILED | PRE | RAG search failed | Continue with defaults |
| GEN_FAILED | CORE | Code generation failed (3 retries) | Return error |
| FORMAT_INVALID | POST | Format validation failed | Retry generation |
| SYNTAX_ERROR | POST | Syntax error detected | Error Handler fixes |
| EVAL_FAIL | POST | Quality evaluation failed | Log warning, return code |

## Performance Metrics

### Latency Budget
- Request Analyzer: 3s
- Retrieval Agent: 5s
- Coder Agent: 3s per file
- Format Validator: 0.5s
- Error Handler: 3s
- Code Evaluator: 3s
- **Total Max**: 30s

### Quality Thresholds
- Request Analyzer Confidence: ≥ 0.6
- Retrieval Coverage: ≥ 0.5
- Code Quality: ≥ 0.7
- Evaluation Pass: ≥ 0.75

## Development

### Adding a New Agent

1. Create agent file in `agents/` directory
2. Implement `async def run(self, state: dict) -> dict`
3. Add to `agents/__init__.py`
4. Add node to state machine in `langgraph_orchestrator.py`
5. Add edges to connect to state machine flow

### Testing Agents

```python
from orchestrator.agents.format_validator import FormatValidatorAgent

agent = FormatValidatorAgent()
result = await agent.run({
    "generated_code": "<<<< SEARCH\nold\n>>>>\n>>>> REPLACE\nnew\n>>>>",
    "file_path": "Test.java",
    "file_type": "NEW"
})
```

## Dependencies

- `langgraph` - State machine orchestration
- `httpx` - Async HTTP client
- `pydantic` - Data validation
- `tree-sitter` - Code parsing (for Error Handler)

## Next Steps

1. Implement Tree-sitter integration for Error Handler
2. Add Neo4j relationship queries to Retrieval Agent
3. Implement Planner Agent for multi-file tasks
4. Add monitoring and metrics collection
5. Create integration tests for full pipeline

## References

- Full specification: `AGENT_FRAMEWORK_SPEC.md`
- Architecture notes: `docs/archive/Notes.md` (informal)
- LangGraph docs: https://langchain-ai.github.io/langgraph/


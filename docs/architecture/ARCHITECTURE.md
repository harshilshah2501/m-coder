# Motadata RAG System Architecture

## Overview

This is an **Anti-Hallucination RAG (Retrieval Augmented Generation)** system for the Motadata codebase. It provides grounded, factual responses about the codebase by combining:

1. **Vector Search** (Qdrant) - Semantic similarity search
2. **Graph Database** (Neo4j) - Structural/relationship queries  
3. **LLM Generation** (vLLM) - Code-aware responses

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MOTADATA RAG SYSTEM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐     ┌─────────────────────────────────────────────────┐  │
│   │   Client    │────▶│              RAG API (Port 8081)                │  │
│   │  (curl/app) │     │         FastAPI + OpenAI-compatible             │  │
│   └─────────────┘     └──────────┬────────────────┬───────────┬─────────┘  │
│                                  │                │           │            │
│                    ┌─────────────▼──────┐  ┌──────▼──────┐   │            │
│                    │      Qdrant        │  │    Neo4j    │   │            │
│                    │   (Port 6333)      │  │ (Port 7687) │   │            │
│                    │                    │  │             │   │            │
│                    │ 4,306 vectors      │  │ 10,262 nodes│   │            │
│                    │ (classes+methods)  │  │ 337K edges  │   │            │
│                    └────────────────────┘  └─────────────┘   │            │
│                                                              │            │
│                                               ┌──────────────▼──────────┐ │
│                                               │         vLLM           │ │
│                                               │      (Port 8080)       │ │
│                                               │   motadata-coder LLM   │ │
│                                               └─────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. RAG API (Port 8081)

**Location**: `rag-system/rag_api.py`

FastAPI service that orchestrates all components:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check for all services |
| `/v1/chat/completions` | POST | **OpenAI-compatible chat** (with RAG) |
| `/v1/models` | GET | List available models |
| `/search/semantic` | POST | Vector similarity search |
| `/search/graph` | POST | Graph traversal (callers/callees) |
| `/search/hybrid` | POST | Combined vector + graph search |
| `/context/method` | POST | Get method context + relationships |
| `/context/class` | POST | Get class inheritance tree |
| `/verify` | POST | Anti-hallucination check |

### 2. Qdrant Vector Database (Port 6333)

**Location**: Docker container `qdrant`

Stores code embeddings for semantic search:

- **Collection**: `motadata_code`
- **Vectors**: 4,306 (615 classes + 3,988 methods)
- **Embedding Model**: `jinaai/jina-embeddings-v2-base-code` (768 dimensions)
- **Distance Metric**: Cosine similarity

### 3. Neo4j Graph Database (Port 7687)

**Location**: Docker container `neo4j`

Stores code structure and relationships:

| Node Type | Count | Properties |
|-----------|-------|------------|
| Package | 32 | name, qualified_name |
| Class | 615 | name, qualified_name, extends, implements |
| Method | 3,988 | name, qualified_name, signature |
| Field | 5,331 | name, type |
| Event | 144 | name (EventBus events) |

| Relationship | Count | Description |
|--------------|-------|-------------|
| CALLS | 269,132 | Method call graph |
| EXTENDS | 204 | Class inheritance |
| IMPLEMENTS | 40 | Interface implementation |
| SENDS_EVENT | 472 | EventBus send patterns |
| RECEIVES_EVENT | 4 | EventBus receive patterns |
| IMPORTS | 5,368 | Import dependencies |

### 4. vLLM Server (Port 8080)

**Model**: `motadata-coder` (fine-tuned for Motadata codebase)

Generates responses using RAG-injected context. The RAG API:
1. Retrieves relevant code from Qdrant + Neo4j
2. Injects context into system prompt
3. Forwards to vLLM for generation
4. Returns response with `rag_context` metadata

## Anti-Hallucination Features

### Confidence Thresholds

```python
MIN_CONFIDENCE_THRESHOLD = 0.3   # Below this = rejected
HIGH_CONFIDENCE_THRESHOLD = 0.6  # Above this = high confidence
```

### Response Grounding

Every response includes:

```json
{
  "rag_context": {
    "grounded": true,           // Response based on real code
    "sources": ["com.mindarray.api.Discovery", ...],
    "result_count": 5,
    "high_confidence": 3        // Count of high-confidence matches
  }
}
```

### Verification Endpoint

Before answering, check if context exists:

```bash
curl -X POST "http://localhost:8081/verify?query=how%20does%20auth%20work"
```

Returns recommendation: "Safe to answer" / "Do NOT answer - insufficient context"

## Data Flow

### Chat Completion Request Flow

```
User Query: "Which class is inherited by all API classes?"
                    │
                    ▼
┌───────────────────────────────────────────────────────────────┐
│                    RAG API (/v1/chat/completions)             │
├───────────────────────────────────────────────────────────────┤
│ 1. Extract user query from messages                          │
│ 2. Generate embedding using Jina model                       │
└──────────────────────────┬────────────────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
┌─────────────────────┐            ┌─────────────────────┐
│   Qdrant Search     │            │   Neo4j Enrichment  │
├─────────────────────┤            ├─────────────────────┤
│ Vector similarity   │            │ For each result:    │
│ top_k=5 results     │──────────▶ │ - Get callers       │
│                     │            │ - Get callees       │
│                     │            │ - Get inheritance   │
└─────────────────────┘            └──────────┬──────────┘
                                              │
                                              ▼
                           ┌──────────────────────────────────┐
                           │     Build RAG Context            │
                           ├──────────────────────────────────┤
                           │ Sources: Discovery, Rebranding,  │
                           │          Explorer, AbstractAPI   │
                           │ Relationships: extends, calls    │
                           └──────────────────┬───────────────┘
                                              │
                                              ▼
                           ┌──────────────────────────────────┐
                           │     Inject into System Prompt    │
                           ├──────────────────────────────────┤
                           │ "Answer based ONLY on context.   │
                           │  NEVER make up class names..."   │
                           └──────────────────┬───────────────┘
                                              │
                                              ▼
                           ┌──────────────────────────────────┐
                           │         vLLM Generation          │
                           ├──────────────────────────────────┤
                           │ Input: System prompt + context   │
                           │ Output: Grounded response        │
                           └──────────────────┬───────────────┘
                                              │
                                              ▼
                           ┌──────────────────────────────────┐
                           │       Return Response            │
                           ├──────────────────────────────────┤
                           │ Answer: "AbstractAPI is..."      │
                           │ rag_context: {grounded: true}    │
                           └──────────────────────────────────┘
```

## Files and Scripts

| File | Purpose |
|------|---------|
| `rag/src/api/rag_api.py` | Main FastAPI application |
| `rag/src/indexing/project_indexer.py` | Index Java AST data into Qdrant + Neo4j |
| `rag/docker/docker-compose.yml` | Qdrant + Neo4j containers |
| `runtime/scripts/governed_services.sh` | vLLM + Plan-Gate (m-coder assistant; config: `runtime/config/demo_stack.env`) |
| `rag/health_monitor.sh` | GPU/RAM/service health monitoring |
| `training/src/utils/api_server.py` | vLLM API wrapper |

## Service Management

> **ℹ️ NOTE:** For the **m-coder** assistant stack, use `runtime/scripts/governed_services.sh` (see `docs/guides/ORCHESTRATOR_GUIDE.md`). The legacy RAG `orchestrator_unified.sh` has been removed.

### Starting and Stopping Services

```bash
# Start runtime stack
bash runtime/scripts/governed_services.sh start

# Stop runtime stack
bash runtime/scripts/governed_services.sh stop

# Restart runtime stack
bash runtime/scripts/governed_services.sh restart

# Check runtime stack status
bash runtime/scripts/governed_services.sh status
```

### Viewing Logs

```bash
# View runtime stack logs
bash runtime/scripts/governed_services.sh logs
```

### Startup Sequence (script-managed)

When you run `bash runtime/scripts/governed_services.sh start`, it brings up the governed stack in sequence:

```
1. Docker (Qdrant + Neo4j)  ─────▶  Wait for HTTP health (60s timeout)
2. vLLM (port 8000)         ─────▶  Wait for /v1/models (180s timeout)
3. Wrapper (port 8080)      ─────▶  Wait for /v1/models (30s timeout)
4. RAG API (port 8081)      ─────▶  Wait for /health (60s timeout)
5. Health Monitor           ─────▶  Start monitoring
```

Total startup time: ~90-120 seconds (mostly vLLM model loading)

### Optional Boot Configuration

This repository does **not** ship `motadata-orchestrator.service`.
If you need boot automation, create a local systemd unit that wraps `governed_services.sh start/stop`.

See `docs/guides/ORCHESTRATOR_SERVICE_GUIDE.md` and `docs/guides/ORCHESTRATOR_GUIDE.md` for current operational guidance.

## Usage Examples

### 1. OpenAI-Compatible Chat (Non-Streaming)

```bash
curl -X POST http://152.228.213.249:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "motadata-coder",
    "messages": [{"role": "user", "content": "How does email notification work?"}]
  }'
```

### 2. Streaming Chat (for Continue.dev)

```bash
curl -N -X POST http://152.228.213.249:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "motadata-coder",
    "messages": [{"role": "user", "content": "What is AbstractAPI?"}],
    "stream": true
  }'
```

Streaming response format:
```
data: {"rag_context": {"grounded": true, "sources": [...], "result_count": 5}}
data: {"id": "chatcmpl-xxx", "choices": [{"delta": {"content": "token"}}]}
data: {"id": "chatcmpl-xxx", "choices": [{"delta": {"content": "by"}}]}
...
data: [DONE]
```

### 3. Semantic Search Only

```bash
curl -X POST http://152.228.213.249:8081/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "alarm notification", "top_k": 5}'
```

### 3. Graph Traversal

```bash
curl -X POST http://152.228.213.249:8081/search/graph \
  -H "Content-Type: application/json" \
  -d '{"entity_name": "com.mindarray.notification.EmailNotification.send", "direction": "callers"}'
```

### 4. Get Class Inheritance

```bash
curl -X POST "http://152.228.213.249:8081/context/class?class_name=com.mindarray.notification.Notification"
```

Response:
```json
{
  "class": "com.mindarray.notification.Notification",
  "extended_by": [
    "EmailNotification", "SMSNotification", "PushNotification",
    "MicrosoftTeamsNotification", "WebHookNotification", ...
  ]
}
```

### 5. Verify Before Answering

```bash
curl -X POST "http://152.228.213.249:8081/verify?query=database%20connection%20pooling"
```

## Network Access

| Service | Local | External |
|---------|-------|----------|
| RAG API | http://localhost:8081 | http://152.228.213.249:8081 |
| Qdrant | http://localhost:6333 | (internal only) |
| Neo4j Browser | http://localhost:7474 | (internal only) |
| vLLM | http://localhost:8080 | (internal only) |

## Rebuilding the Index

The system now supports dynamic indexing via the API. To index a project:

```bash
# Trigger background indexing for a project
curl -X POST http://localhost:8081/v1/index/create \
  -H "Content-Type: application/json" \
  -d '{"workspace_root": "/absolute/path/to/project"}'

# Check status
curl http://localhost:8081/v1/index/status?workspace_root=/absolute/path/to/project
```

The indexer will:
1. Parse Java files using regex-based extraction
2. Generate embeddings using Jina v2
3. Store vectors in a project-specific Qdrant collection


## Continue.dev Integration

To use this RAG system with [Continue.dev](https://continue.dev) VS Code extension:

### Configuration (~/.continue/config.json)

```json
{
  "models": [
    {
      "title": "Motadata Coder (RAG)",
      "provider": "openai",
      "model": "motadata-coder",
      "apiBase": "http://152.228.213.249:8081/v1",
      "apiKey": "not-needed"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Motadata Coder",
    "provider": "openai",
    "model": "motadata-coder",
    "apiBase": "http://152.228.213.249:8081/v1",
    "apiKey": "not-needed"
  }
}
```

### Features

- **Streaming responses**: Tokens appear as they're generated
- **RAG context**: Every response is grounded in real codebase
- **Anti-hallucination**: Model is instructed to only reference actual code

### How It Works with Continue.dev

1. You ask a question in Continue chat
2. RAG API receives the request with `stream: true`
3. Searches Qdrant for relevant code (vector similarity)
4. Enriches with Neo4j relationships (callers, inheritance)
5. Injects context into system prompt
6. Streams response from vLLM token-by-token
7. Each chunk is sent to Continue.dev in real-time

### Testing

```bash
# Verify the endpoint works with streaming
curl -N http://152.228.213.249:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "motadata-coder", "messages": [{"role": "user", "content": "test"}], "stream": true}'
```


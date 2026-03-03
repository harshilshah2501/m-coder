# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Motadata Coder (m-coder) is an AI-powered code generation assistant built around a 4-layer architecture (Governance, ML Compilation, Runtime, Observation). The main runnable services are the **RAG API** (FastAPI, port 8081) and the **Plan-Gate Service** (stdlib HTTP, port 8089). External dependencies include **Qdrant** (vector DB, port 6333) and **Neo4j** (graph DB, ports 7474/7687), both run via Docker Compose. The vLLM inference server (port 8000) requires a GPU and is not available in the cloud agent environment.

### Running tests

Canonical test command (from repo root):

```bash
source .venv/bin/activate
python3 -m unittest discover -s . -p 'test_*.py' -q
```

Expected: **186 tests**, all passing. No external services are required for the test suite; tests that need `jsonschema` gracefully skip when it's missing but will run fully with the venv active.

### CI / lint checks

```bash
for script in scripts/ci/check_*.py; do python3 "$script"; done
```

All five checks under `scripts/ci/` must pass (structural invariants, governance YAML, pipeline boundaries, etc.).

### Starting services

1. **Docker databases** (required for RAG API):
   ```bash
   cd /workspace/runtime/rag/docker && sudo docker compose up -d
   ```
   Wait ~15 s for health checks to pass. Qdrant must have the `motadata_code` collection (768-dim, Cosine). Create it if missing:
   ```bash
   curl -X PUT "http://localhost:6333/collections/motadata_code" \
     -H "Content-Type: application/json" \
     -d '{"vectors": {"size": 768, "distance": "Cosine"}}'
   ```

2. **RAG API** (port 8081):
   ```bash
   source .venv/bin/activate
   export PYTHONPATH="/workspace/runtime/rag/src:/workspace/runtime/rag/src/api:/workspace/runtime/rag/src/indexing:/workspace/runtime/rag/src/retrieval:/workspace/runtime/rag/src/utils"
   export QDRANT_COLLECTION="motadata_code"
   python3 -m uvicorn rag_api:app --host 0.0.0.0 --port 8081
   ```
   Health: `curl http://localhost:8081/health`

3. **Plan-Gate Service** (port 8089):
   ```bash
   source .venv/bin/activate
   python3 -m runtime.plan_gate_service.app
   ```
   Health: `curl http://localhost:8089/healthz`

### Gotchas

- The RAG API imports modules from several subdirectories (`src/api`, `src/indexing`, `src/retrieval`, `src/utils`). The `PYTHONPATH` must include all of them or imports will fail.
- The embedding model (`jinaai/jina-embeddings-v2-base-code`) is loaded at startup but may not download in constrained environments. The API still starts; semantic search endpoints will return "Embedding model not available" — graph search and chat completions (which forward to vLLM) work independently.
- The Qdrant collection `motadata_code` must exist before the RAG API starts or it will exit during the lifespan handler. Create it via the Qdrant HTTP API if it's a fresh database.
- vLLM (port 8000) requires a GPU with significant VRAM; it cannot run in the cloud agent VM. Chat completions that forward to vLLM will fail with a connection error, which is expected.
- Docker in the cloud VM requires `fuse-overlayfs` storage driver and `iptables-legacy`. See the environment setup snapshot for details.

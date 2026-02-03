# Integration Guide: Enhanced RAG with Your Existing System

## Current System Architecture

```
User Query
    ↓
Continue.dev Extension
    ↓
Your RAG API (Qdrant)
    ↓
Fine-tuned Model (V14)
    ↓
Response
```

## Target Architecture (Phase 1)

```
User Query
    ↓
Continue.dev Extension
    ↓
Enhanced RAG Service
    ├─ Intent Detector
    ├─ Context Gatherer (uses Qdrant)
    └─ Prompt Builder
    ↓
Optimized Prompt → Fine-tuned Model (V14)
    ↓
Response
```

---

## Step-by-Step Integration

### Step 1: Add Enhanced RAG to Your API

#### 1.1 Install in your existing `rag_api/` directory

The files are already created:
- `rag_api/intent_detector.py`
- `rag_api/context_gatherer.py`
- `rag_api/prompt_builder.py`
- `rag_api/enhanced_rag_service.py`

#### 1.2 Update your existing RAG endpoint

**Current** (`rag_api/main.py` or similar):
```python
@app.post("/query")
async def query(request: QueryRequest):
    # Current RAG logic
    results = qdrant_client.search(
        collection_name="codebase",
        query_vector=embed(request.query),
        limit=5
    )
    
    # Build basic prompt
    context = "\n".join([r.payload['content'] for r in results])
    prompt = f"Query: {request.query}\n\nContext:\n{context}"
    
    return {"prompt": prompt}
```

**Enhanced** (add this):
```python
from enhanced_rag_service import EnhancedRAGService

# Initialize once at startup
enhanced_rag = EnhancedRAGService(
    qdrant_client=qdrant_client,
    codebase_root="/path/to/motadata/codebase",
    enable_intent_detection=True
)

@app.post("/query")
async def query(request: QueryRequest):
    # Use enhanced RAG
    response = enhanced_rag.process_query(request.query)
    
    return {
        "prompt": response['prompt'],
        "metadata": {
            "intent": response['intent'],
            "confidence": response['confidence'],
            "entities": response['entities'],
            "files_to_create": response.get('metadata', {}).get('files_to_create', []),
            "files_to_modify": response.get('metadata', {}).get('files_to_modify', []),
        }
    }

# Add diagnostics endpoint for debugging
@app.post("/diagnostics")
async def diagnostics(request: QueryRequest):
    diag = enhanced_rag.get_diagnostics(request.query)
    return diag
```

### Step 2: Configure for Your Codebase

#### 2.1 Update file patterns in `context_gatherer.py`

```python
# Edit ContextGatherer.__init__()
self.patterns = {
    'api': 'src/main/java/com/mindarray/api',
    'store': 'src/main/java/com/mindarray/store',
    'schema': 'src/main/resources/entity-schemas',
    'router': 'src/main/java/com/mindarray/api/APIRouter.java',
    'constants': 'src/main/java/com/mindarray/api/APIConstants.java',
}

# Update to match YOUR actual paths
```

#### 2.2 Add Motadata-specific patterns

```python
# In IntentDetector, add Motadata-specific patterns
MOTADATA_PATTERNS = [
    (r'\b(profile|configstore|api router)\b', 0.8),
    (r'\b(device|monitor|alert|slo|credential)\b', 0.6),
]
```

### Step 3: Test the Integration

#### 3.1 Run the test suite
```bash
cd /path/to/RAG-Datastore
python test_enhanced_rag.py
```

#### 3.2 Test with real queries
```bash
# Start your RAG API
python rag_api/main.py

# In another terminal, test
curl -X POST http://localhost:8000/diagnostics \
  -H "Content-Type: application/json" \
  -d '{"query": "Create CorrectionProfile API"}'
```

Expected output:
```json
{
  "query": "Create CorrectionProfile API",
  "intent": {
    "type": "CREATE",
    "confidence": 0.9,
    "entities": ["CorrectionProfile"],
    "task_type": "api"
  },
  "context_summary": {
    "files_to_create": [
      "src/main/java/com/mindarray/api/CorrectionProfile.java",
      "src/main/java/com/mindarray/store/CorrectionProfileConfigStore.java",
      "src/main/resources/entity-schemas/correction-profiles.json"
    ],
    "files_to_modify": [
      "src/main/java/com/mindarray/api/APIRouter.java"
    ],
    "reference_files_available": ["api_class", "config_store", "schema"]
  }
}
```

### Step 4: Update Continue.dev Configuration

#### 4.1 Current config (`.continue/config.json`):
```json
{
  "models": [
    {
      "title": "Motadata V14",
      "provider": "openai",
      "model": "ft:gpt-4o-2024-08-06:your-org:motadata-v14:xxxxx",
      "apiKey": "sk-..."
    }
  ],
  "contextProviders": [
    {
      "name": "rag",
      "params": {
        "url": "http://localhost:8000/query"
      }
    }
  ]
}
```

#### 4.2 No changes needed!
The enhanced RAG is a drop-in replacement. Continue.dev will:
1. Send query to your RAG endpoint
2. Get back the enhanced prompt
3. Send to your fine-tuned model
4. Return response

### Step 5: Monitor and Iterate

#### 5.1 Add logging
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In enhanced_rag_service.py, logs are already added:
# - Intent detection results
# - Context gathering stats
# - Prompt length
```

#### 5.2 Track metrics
```python
# Add to your RAG API
metrics = {
    'total_queries': 0,
    'intent_distribution': {},
    'avg_confidence': 0.0,
    'success_rate': 0.0,
}

@app.post("/query")
async def query(request: QueryRequest):
    metrics['total_queries'] += 1
    
    response = enhanced_rag.process_query(request.query)
    
    # Track intent distribution
    intent = response['intent']
    metrics['intent_distribution'][intent] = \
        metrics['intent_distribution'].get(intent, 0) + 1
    
    return response

@app.get("/metrics")
async def get_metrics():
    return metrics
```

---

## Troubleshooting

### Issue 1: Intent detection is always UNKNOWN
**Cause**: Patterns don't match your query style
**Fix**: Add more patterns to `IntentDetector`

```python
# In intent_detector.py
CREATE_PATTERNS = [
    # Add your specific patterns
    (r'\b(implement|build)\b.*\b(feature|functionality)\b', 0.8),
    (r'\b(add|create)\b.*\b(new)\b', 0.7),
]
```

### Issue 2: Can't find reference files
**Cause**: File paths don't match your codebase
**Fix**: Update `self.patterns` in `ContextGatherer.__init__()`

### Issue 3: Reference code is empty
**Cause**: Files don't exist or path is wrong
**Fix**: Check `codebase_root` path and verify files exist

```python
# Add debug logging
def _read_file(self, file_path: str) -> Optional[str]:
    full_path = self.codebase_root / file_path
    logger.info(f"Trying to read: {full_path}")
    if not full_path.exists():
        logger.warning(f"File not found: {full_path}")
        return None
    # ...
```

### Issue 4: Model still generates wrong output
**Cause**: Prompt template needs adjustment
**Fix**: Customize `PromptBuilder._build_create_prompt()`

```python
# Make file list more explicit
prompt += "\n**CRITICAL**: You MUST create these files (they don't exist yet):\n"
for file_path in context.get('files_to_create', []):
    prompt += f"  - {file_path} (NEW FILE - use complete code, not diff)\n"
```

---

## Performance Optimization

### Caching Reference Files
```python
from functools import lru_cache

class ContextGatherer:
    @lru_cache(maxsize=100)
    def _read_file_cached(self, file_path: str) -> Optional[str]:
        return self._read_file(file_path)
```

### Async Operations
```python
import asyncio

async def gather_context_async(self, intent_result, query):
    # Read multiple files in parallel
    tasks = [
        self._read_file_async(path)
        for path in file_paths
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### Reduce Token Usage
```python
def _truncate_reference(self, code: str, max_lines: int = 50) -> str:
    """Keep only important parts of reference code"""
    lines = code.split('\n')
    
    # Keep: package, imports, class signature, key methods
    important_lines = []
    for i, line in enumerate(lines):
        if any(kw in line for kw in ['package', 'import', 'class', 'public']):
            important_lines.append(line)
        if len(important_lines) >= max_lines:
            break
    
    return '\n'.join(important_lines)
```

---

## Next Steps

1. ✅ **Week 1**: Integrate Enhanced RAG
2. ✅ **Week 1**: Test on 10 diverse queries
3. ✅ **Week 2**: Tune patterns and prompts
4. ✅ **Week 2**: Measure success rate improvement
5. ⏭️ **Week 3**: Plan Phase 2 (Agentic Wrapper)

---

## Success Checklist

- [ ] Enhanced RAG service running
- [ ] Intent detection working (>70% accuracy)
- [ ] Context gathering finds reference files
- [ ] Prompts include explicit file lists
- [ ] Model success rate improved by 30%+
- [ ] Metrics tracking in place
- [ ] Ready for Phase 2


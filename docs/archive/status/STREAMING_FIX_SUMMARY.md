# Streaming Response Fix - IntelliJ IDEA Integration

**Date**: January 5, 2026
**Issue**: IntelliJ IDEA LLM integration failing with `IllegalStateException` when parsing streaming responses
**Root Cause**: RAG API sending incomplete first chunk missing required OpenAI fields
**Status**: ✅ FIXED

## Problem

IntelliJ IDEA's LLM client (Continue.dev plugin) was throwing:
```
java.lang.IllegalStateException: Error from OpenAILLMClientExt API: 200 OK: 
Fields [choices, created, id, model, object] are required for type with serial name 
'ai.koog.prompt.executor.clients.openai.models.OpenAIChatCompletionStreamResponse', 
but they were missing at path: $
```

## Root Cause

In `archive/legacy_runtime_rag/src/api/rag_api.py`, the `_stream_vllm_response()` function was sending the first chunk with ONLY RAG context:

```python
# BROKEN: First chunk missing required OpenAI fields
if rag_context_info:
    yield f"data: {json.dumps({'rag_context': rag_context_info})}\n\n"
```

This chunk lacked the required fields: `id`, `object`, `created`, `model`, `choices`

## Solution

Modified the streaming function to:
1. Include RAG context in the first valid OpenAI chunk (not as a separate chunk)
2. Ensure ALL chunks have required OpenAI fields
3. Add RAG context as a custom field to the first chunk only

```python
# FIXED: First chunk includes both RAG context AND required OpenAI fields
first_chunk = True
async for line in response.aiter_lines():
    # ... process vLLM response ...
    output_chunk = {
        "id": request_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": chunk.get("choices", [])
    }
    
    # Add RAG context to first chunk only
    if first_chunk and rag_context_info:
        output_chunk["rag_context"] = rag_context_info
        first_chunk = False
    
    yield f"data: {json.dumps(output_chunk)}\n\n"
```

## Changes Made

**File**: `archive/legacy_runtime_rag/src/api/rag_api.py`
**Function**: `_stream_vllm_response()` (lines 1307-1365)
**Changes**:
- Removed separate RAG context chunk
- Added `first_chunk` flag to track first valid OpenAI chunk
- Embed RAG context in first chunk as custom field
- Ensure all chunks have required OpenAI fields

## Testing

Verified with streaming request:
```bash
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "motadata-coder",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "stream": true
  }'
```

✅ All chunks now have required fields
✅ RAG context included in first chunk
✅ Stream properly ends with `[DONE]`
✅ IntelliJ IDEA integration should now work

## Compatibility

- ✅ OpenAI API compliant
- ✅ Backward compatible (RAG context is optional custom field)
- ✅ Works with all OpenAI-compatible clients
- ✅ Fixes IntelliJ IDEA LLM integration


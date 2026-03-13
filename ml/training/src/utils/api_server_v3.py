from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from typing import Dict, Any, List
import uvicorn
import re

app = FastAPI(title="Motadata Coder Agent - Quality Fixed")

VLLM_URL = "http://localhost:8000/v1/chat/completions"

# CRITICAL: Fix tokenizer + hallucinations
STOP_TOKENS = [
    "<|im_end|>", "<|endoftext|>", 
    "所有情节", "\u6240\u6709\u60c5\u8282",  # Chinese artifacts
    "utches", "_REALTYPE", "querque", "afone",  # Garbage tokens
    "LMResponse", "tool_response"  # Prevent infinite tool loops
]

class ChatRequest(BaseModel):
    model: str = "motadata-coder"
    messages: List[Dict[str, Any]]
    temperature: float = 0.05  # ULTRA LOW - Fix hallucinations
    max_tokens: int = 1024     # Shorter for quality
    stop: List[str] = STOP_TOKENS  # BLOCK BAD TOKENS

@app.post("/v1/chat/completions")
async def proxy_chat(request: ChatRequest):
    """Quality-fixed proxy with hallucination prevention"""
    try:
        # Forward to vLLM with FIXED params
        vllm_payload = request.model_dump()
        vllm_payload["stop"] = STOP_TOKENS  # Force clean output
        
        resp = requests.post(VLLM_URL, json=vllm_payload, timeout=30)
        resp.raise_for_status()
        
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"vLLM Error: {str(e)}")

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [{
            "id": "motadata-coder",
            "object": "model",
            "created": 1733950000,
            "owned_by": "motadata"
        }]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "model": "motadata-coder",
        "temperature": 0.05,
        "stop_tokens": len(STOP_TOKENS),
        "fixes_applied": "tokenizer+hallucinations"
    }

@app.get("/debug")
async def debug():
    """Test endpoint for strict validation"""
    test_payload = {
        "model": "motadata-coder",
        "messages": [{"role": "user", "content": "What calls AvailabilityCacheServiceImpl.buildStatusResult?"}],
        "temperature": 0.05,
        "max_tokens": 256
    }
    resp = requests.post(VLLM_URL, json=test_payload)
    content = resp.json()['choices'][0]['message']['content']
    
    # Check for hallucinations
    hallucinations = []
    if "agent/" in content: hallucinations.append("WRONG_PATH: agent/")
    if "com/events/EventBus" in content: hallucinations.append("PHANTOM_FILE: EventBus.java")
    if any(token in content for token in ["所有情节", "utches"]): hallucinations.append("TOKENIZER_BROKEN")
    
    return {
        "test_content": content[:200],
        "hallucinations": hallucinations,
        "clean": len(hallucinations) == 0,
        "tokens": resp.json()['usage']['total_tokens']
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)


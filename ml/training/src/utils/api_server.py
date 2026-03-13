from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import requests
import httpx  # Required for streaming
from typing import Dict, Any, List, Optional
import uvicorn
import json

app = FastAPI()

VLLM_URL = "http://localhost:8000/v1/chat/completions"

# ============================================================
# ANTI-REPETITION & QUALITY SETTINGS
# Added based on evaluation findings (Dec 11, 2025)
# ============================================================
GENERATION_DEFAULTS = {
    "temperature": 0.1,              # Low for consistency
    "repetition_penalty": 1.2,       # Penalize repeated tokens
    "frequency_penalty": 0.5,        # Reduce frequent token probability
    "presence_penalty": 0.3,         # Encourage diversity
    "top_p": 0.9,                    # Nucleus sampling
    "top_k": 50,                     # Limit token choices
}

# Stop tokens to prevent loops and tool artifacts
STOP_TOKENS = [
    "<|im_end|>",
    "<|endoftext|>",
    "<tool_response>",
    "</tool_response>",
    "<thought>",
    "</thought>",
    "<javaparser>",
    "<LMResponse>",
    "vector_search(",
    "graph_all(",
    # Repetition pattern breakers
    "Test.java - Test",
    "getQuery, getQuery, getQuery",
]

class ChatRequest(BaseModel):
    model: str = "motadata-coder"
    messages: List[Dict]
    temperature: float = 0.1
    max_tokens: int = 1024
    stream: bool = False
    # Optional overrides (will use defaults if not provided)
    repetition_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[List[str]] = None

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Safe request logging"""
    client_ip = request.client.host
    method = request.method
    path = request.url.path
    
    # Don't log health checks to keep console clean
    if path != "/health":
        print(f"🌐 {client_ip} - '{method} {path}'")
    
    response = await call_next(request)
    
    if path != "/health":
        print(f"📊 {client_ip} - '{method} {path}' → {response.status_code}")
    return response

async def stream_generator(payload):
    """Helper to stream data from vLLM"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", VLLM_URL, json=payload) as response:
            async for chunk in response.aiter_bytes():
                yield chunk

def build_payload(request: ChatRequest) -> Dict[str, Any]:
    """Build vLLM payload with anti-repetition settings"""
    payload = {
        "model": request.model,
        "messages": request.messages,
        "max_tokens": request.max_tokens,
        "stream": request.stream,
        # Apply defaults with optional overrides
        "temperature": request.temperature,
        "repetition_penalty": request.repetition_penalty or GENERATION_DEFAULTS["repetition_penalty"],
        "frequency_penalty": request.frequency_penalty or GENERATION_DEFAULTS["frequency_penalty"],
        "presence_penalty": request.presence_penalty or GENERATION_DEFAULTS["presence_penalty"],
        "top_p": GENERATION_DEFAULTS["top_p"],
        "top_k": GENERATION_DEFAULTS["top_k"],
        # Combine default stop tokens with any custom ones
        "stop": list(set(STOP_TOKENS + (request.stop or []))),
    }
    return payload


@app.post("/v1/chat/completions")
async def proxy_chat(request: ChatRequest):
    payload = build_payload(request)

    # ✅ STREAMING PATH
    if request.stream:
        print(f"🌊 STREAMING REQUEST START (rep_penalty={payload['repetition_penalty']})")
        return StreamingResponse(
            stream_generator(payload),
            media_type="text/event-stream"
        )

    # ✅ NON-STREAMING PATH (Standard)
    try:
        prompt = request.messages[-1]["content"][:80] + "..." if request.messages else "N/A"
        print(f"🔍 PROMPT: {prompt}")
        print(f"⚙️  SETTINGS: rep={payload['repetition_penalty']}, freq={payload['frequency_penalty']}, pres={payload['presence_penalty']}")

        # Using sync requests here is fine for simple proxy
        resp = requests.post(VLLM_URL, json=payload, timeout=60)
        resp.raise_for_status()

        data = resp.json()
        content = data['choices'][0]['message']['content'][:100] + "..."
        tokens = data['usage']

        print(f"🤖 AGENT: {content}")
        print(f"📊 TOKENS: {tokens['prompt_tokens']}/{tokens['completion_tokens']}")

        return data
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def models():
    return {"object": "list", "data": [{"id": "motadata-coder", "object": "model"}]}

@app.get("/health")
async def health():
    return {"status": "healthy", "mode": "streaming-enabled"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)


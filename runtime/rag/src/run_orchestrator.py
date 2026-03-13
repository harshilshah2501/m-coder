"""
FastAPI Wrapper for Agentic Orchestrator

Provides HTTP endpoints for:
- /generate - Generate code from user request
- /health - Health check
- /analyze - Analyze request without full generation
"""

import logging
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.langgraph_orchestrator import Orchestrator
from orchestrator.agents.request_analyzer import RequestAnalyzerAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Motadata Agentic Orchestrator",
    description="LangGraph-based code generation orchestrator",
    version="1.0.0"
)

# Add CORS middleware for IDE integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = Orchestrator()

# Request/Response models
class GenerateRequest(BaseModel):
    prompt: str
    history: list = []
    context: dict = {}

class AnalyzeRequest(BaseModel):
    prompt: str
    history: list = []
    context: dict = {}

# Endpoints
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Motadata Agentic Orchestrator",
        "version": "1.0.0"
    }

@app.post("/generate")
async def generate_code(request: GenerateRequest):
    """
    Generate code based on user request
    
    Args:
        prompt: User's code generation request
        history: Conversation history
        context: Codebase context
    
    Returns:
        Generated code with metadata
    """
    try:
        logger.info(f"Received generate request: {request.prompt[:100]}...")
        
        result = await orchestrator.process_request(
            user_request=request.prompt,
            conversation_history=request.history,
            codebase_context=request.context
        )
        
        logger.info(f"Generate request completed with status: {result.get('status')}")
        return result
        
    except Exception as e:
        logger.error(f"Error in generate endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_request(request: AnalyzeRequest):
    """
    Analyze request without full generation
    
    Args:
        prompt: User's request
        history: Conversation history
        context: Codebase context
    
    Returns:
        Request analysis results
    """
    try:
        logger.info(f"Received analyze request: {request.prompt[:100]}...")
        
        agent = RequestAnalyzerAgent()
        result = await agent.run({
            "user_request": request.prompt,
            "conversation_history": request.history,
            "codebase_context": request.context
        })
        
        await agent.close()
        
        logger.info(f"Analyze request completed with status: {result.get('status')}")
        return result
        
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "service": "Motadata Agentic Orchestrator",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "generate": "POST /generate",
            "analyze": "POST /analyze"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    logger.info("Starting Motadata Agentic Orchestrator...")
    logger.info("vLLM endpoint: http://localhost:8000")
    logger.info("Qdrant endpoint: http://localhost:6333")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )


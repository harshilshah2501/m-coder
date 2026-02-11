#!/usr/bin/env python3
"""
RAG API - Anti-Hallucination Retrieval System

FastAPI service that provides grounded context retrieval using:
- Qdrant: Vector/semantic search
- Neo4j: Graph/structural search
- Hybrid: Combines both for comprehensive context

This minimizes hallucination by always providing REAL code context.
"""

import os
import time
import json
import httpx
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from neo4j import GraphDatabase

# Force CPU-only mode
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Project indexer for multi-project support
from project_indexer import get_project_manager, ProjectIndexManager

# Diagnostic logging for debugging failures
from diagnostic_logger import (
    DiagnosticLogger, get_recent_failures, get_layer_stats,
    get_latest_debug_session, get_debug_session, list_debug_sessions
)

# Semantic context extractor for V14
from semantic_context_extractor import get_semantic_context, SemanticContextExtractor


# ============== Configuration ==============
class Config:
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

    # Workspace Configuration - prepend to relative paths for absolute resolution
    # This keeps the index portable but makes answers actionable
    # WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", "/home/harshil/")
    WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", "/home/harshil/TestMotadataProject/Motadata/motadata")

    # Get collection name dynamically from ProjectIndexManager
    # Initialize at module load time
    _project_manager_instance = get_project_manager()
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION") or _project_manager_instance.get_collection_name(os.getenv("WORKSPACE_ROOT", "/home/harshil/TestMotadataProject/Motadata/motadata"))

    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

    EMBEDDING_MODEL = "jinaai/jina-embeddings-v2-base-code"

    # Anti-Hallucination Thresholds
    MIN_CONFIDENCE_THRESHOLD = float(os.getenv("MIN_CONFIDENCE", "0.3"))  # Minimum similarity score
    HIGH_CONFIDENCE_THRESHOLD = float(os.getenv("HIGH_CONFIDENCE", "0.6"))  # High confidence score
    MAX_RESULTS_WITHOUT_CONTEXT = 0  # Never return results without real code

    # vLLM Integration
    # Directly connect to vLLM (no wrapper needed)
    VLLM_URL = os.getenv("VLLM_URL", "http://localhost:8000")
    # Version-agnostic model name - only the model name, not the version
    VLLM_MODEL = os.getenv("VLLM_MODEL_NAME", "motadata-coder")

    # Anti-Repetition & Quality Settings
    # Applied to all vLLM calls to prevent repetitive output
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

    @classmethod
    def resolve_path(cls, relative_path: str) -> str:
        """Convert relative path to absolute using WORKSPACE_ROOT"""
        if not relative_path:
            return relative_path
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.join(cls.WORKSPACE_ROOT, relative_path)


# ============== Request/Response Models ==============
class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    top_k: int = Field(default=5, ge=1, le=50)
    node_type: Optional[str] = Field(default=None, description="Filter: 'class' or 'method'")


class GraphRequest(BaseModel):
    entity_name: str = Field(..., description="Qualified name of class/method")
    relation_type: str = Field(default="all", description="CALLS, INHERITS, IMPLEMENTS, or 'all'")
    depth: int = Field(default=1, ge=1, le=3)


class HybridRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    top_k: int = Field(default=5, ge=1, le=20)
    include_callers: bool = Field(default=True)
    include_callees: bool = Field(default=True)


class SemanticContextRequest(BaseModel):
    file_path: str = Field(..., description="Path to Java file (relative or absolute)")
    method_name: str = Field(..., description="Name of method to modify")
    task_description: str = Field(..., description="What to do (e.g., 'Add logging at start of method')")
    class_name: Optional[str] = Field(default=None, description="Optional class name for disambiguation")


# OpenAI-compatible Chat Models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'system', 'user', 'assistant', or 'tool'")
    content: Optional[str] = Field(default=None, description="Message content")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None, description="Tool calls made by assistant")
    tool_call_id: Optional[str] = Field(default=None, description="ID of tool call this message responds to")
    name: Optional[str] = Field(default=None, description="Name of the tool for tool messages")


# Tool/Function definitions for file operations
class FunctionParameters(BaseModel):
    type: str = "object"
    properties: Dict[str, Any]
    required: List[str] = []


class FunctionDefinition(BaseModel):
    name: str
    description: str
    parameters: FunctionParameters


class ToolDefinition(BaseModel):
    type: str = "function"
    function: FunctionDefinition


class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: Dict[str, str]  # {"name": "...", "arguments": "..."}


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="motadata-coder")
    messages: List[ChatMessage]
    temperature: float = Field(default=0.5, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=16384)  # Optimized for token budget
    stream: bool = Field(default=False)
    use_rag: bool = Field(default=True, description="Enable RAG context injection")
    rag_top_k: int = Field(default=3, ge=1, le=20)  # Balanced: 3 results (was 5, tried 2)
    # Tool calling support
    tools: Optional[List[ToolDefinition]] = Field(default=None, description="Available tools/functions")
    tool_choice: Optional[str] = Field(default="auto", description="Tool choice: 'auto', 'none', or specific tool")
    # Mode selection (Phase 1 fix for tool obsession)
    mode: str = Field(default="auto", description="Response mode: 'chat' (direct answers), 'agent' (tool use), 'auto' (context-based)")
    # Workspace context from Continue.dev
    workspace_root: Optional[str] = Field(default=None, description="Absolute path to workspace root")
    open_files: Optional[List[str]] = Field(default=None, description="Currently open files in editor")
    current_file: Optional[str] = Field(default=None, description="Currently focused file in editor")
    # Evaluation support - directly read baseline files from workspace
    expected_files: Optional[List[str]] = Field(default=None, description="List of baseline files to read from workspace (for evaluation)")


# Token estimation: ~4 chars per token for code
# BALANCED OPTIMIZATION: Fit within 16K limit while preserving accuracy
MAX_TOKENS_PER_FILE = 1000  # ~4000 chars, ~75 lines (balanced: was 2000, tried 800)
MAX_TOTAL_CONTEXT_TOKENS = 10000  # ~62% of 16K limit (balanced: was 20000, tried 8000)
MAX_LINES_PER_FILE = 75  # Balanced (was 150, tried 60)


def _estimate_tokens(text: str) -> int:
    """Estimate token count (~4 chars per token for code)"""
    return len(text) // 4


def _truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to approximately max_tokens"""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"


def _clean_tool_artifacts(response: str, mode: str) -> str:
    """Remove tool call artifacts when in chat mode (Phase 1 fix)"""
    if mode != "chat":
        return response
    
    import re
    # Remove <thought> tags
    response = re.sub(r'<thought>.*?</thought>', '', response, flags=re.DOTALL | re.IGNORECASE)
    # Remove vector_search calls
    response = re.sub(r'vector_search\s*\([^)]*\)', '', response, flags=re.IGNORECASE)
    # Remove other tool call patterns
    response = re.sub(r'<tool_code>.*?</tool_code>', '', response, flags=re.DOTALL | re.IGNORECASE)
    response = re.sub(r'<tool_response>.*?</tool_response>', '', response, flags=re.DOTALL | re.IGNORECASE)
    # Remove function call patterns like: find_similar_methods(...)
    response = re.sub(r'(find_similar_methods|find_similar_classes|get_method_callers|get_method_callees|get_class_methods|get_context_for_method)\s*\([^)]*\)', '', response, flags=re.IGNORECASE)
    # Clean up excessive whitespace
    response = re.sub(r'\n\s*\n\s*\n+', '\n\n', response)
    return response.strip()


def _extract_method_names_from_query(query: str) -> List[str]:
    """
    Extract potential method names from task description.

    Examples:
    - "Add logging to getItemsByUserProfile" -> ["getItemsByUserProfile"]
    - "Refactor calculateTotal and processPayment" -> ["calculateTotal", "processPayment"]
    - "added change logs" -> [] (no specific method)

    Returns:
        List of detected method names (camelCase or PascalCase identifiers)
    """
    import re
    # Match camelCase identifiers (likely method names)
    # Must start with lowercase and contain at least one uppercase letter
    # This avoids matching common verbs like "Add", "Update", "Fix"
    pattern = r'\b([a-z][a-z0-9]*[A-Z][a-zA-Z0-9]+)\b'
    matches = re.findall(pattern, query)

    # Filter out common words that match the pattern but aren't methods
    common_words = {'JavaScript', 'TypeScript', 'GitHub', 'GitLab'}
    method_names = [m for m in matches if m not in common_words]

    return method_names


def _clean_code_content(content: str, max_lines: int = MAX_LINES_PER_FILE) -> str:
    """Remove license headers, limit lines, and truncate to token limit"""
    if not content:
        return ""
    import re
    # Remove block comments starting with /* that are likely licenses (at start of file)
    content = re.sub(r'^\s*/\*.*?\*/\s*', '', content, flags=re.DOTALL)
    content = content.strip()

    # Limit to max_lines
    lines = content.split('\n')
    if len(lines) > max_lines:
        content = '\n'.join(lines[:max_lines]) + f"\n... [{len(lines) - max_lines} more lines truncated]"

    # Truncate to token limit
    content = _truncate_to_tokens(content, MAX_TOKENS_PER_FILE)

    return content


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class ChatChoiceDelta(BaseModel):
    """Delta format for streaming"""
    index: int
    delta: Dict[str, str]
    finish_reason: Optional[str] = None


class ChatUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: ChatUsage
    rag_context: Optional[Dict[str, Any]] = Field(default=None, description="RAG context used")


class ChatCompletionChunk(BaseModel):
    """Streaming chunk format"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatChoiceDelta]


class CodeContext(BaseModel):
    id: str
    text: str
    node_type: str
    qualified_name: str
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    score: float = 0.0
    confidence: str = "low"  # low, medium, high - for anti-hallucination
    content: Optional[str] = None


class GraphRelation(BaseModel):
    source: str
    relation: str
    target: str


class HybridResult(BaseModel):
    code: CodeContext
    callers: List[str] = []
    callees: List[str] = []
    inherits_from: Optional[str] = None  # Parent class (EXTENDS)
    implements: List[str] = []  # Interfaces this class implements (IMPLEMENTS)
    extended_by: List[str] = []  # Classes that extend this class (children)
    implemented_by: List[str] = []  # Classes that implement this interface (if this is an interface)


# Anti-Hallucination Response wrapper
class RAGResponse(BaseModel):
    """Response with anti-hallucination metadata"""
    results: List[Any]
    query: str
    total_found: int
    high_confidence_count: int = 0
    warning: Optional[str] = None
    grounded: bool = True  # True = all results backed by real code
    recommendation: Optional[str] = None


# ============== RAG Engine ==============
class RAGEngine:
    """Core RAG engine combining Qdrant + Neo4j"""
    
    def __init__(self):
        self.qdrant = None
        self.neo4j_driver = None
        self.embed_model = None
        self.tokenizer = None
    
    def connect(self):
        """Initialize connections with retry logic"""
        import time

        # Connect to Qdrant with retry
        print(f"🔗 Connecting to Qdrant at {Config.QDRANT_HOST}:{Config.QDRANT_PORT}...")
        self.qdrant = QdrantClient(host=Config.QDRANT_HOST, port=Config.QDRANT_PORT)

        # Verify collection exists with retry (Qdrant might be starting up)
        max_retries = 5
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                collections = [c.name for c in self.qdrant.get_collections().collections]
                if Config.QDRANT_COLLECTION not in collections:
                    raise RuntimeError(f"Collection '{Config.QDRANT_COLLECTION}' not found in Qdrant")
                print(f"✅ Qdrant connected. Collection: {Config.QDRANT_COLLECTION}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️  Qdrant not ready (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"❌ Failed to connect to Qdrant after {max_retries} attempts")
                    raise
        
        # Connect to Neo4j with retry
        print(f"🔗 Connecting to Neo4j at {Config.NEO4J_URI}...")
        max_retries = 5
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                self.neo4j_driver = GraphDatabase.driver(
                    Config.NEO4J_URI,
                    auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
                )
                self.neo4j_driver.verify_connectivity()
                print("✅ Neo4j connected")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️  Neo4j not ready (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"❌ Failed to connect to Neo4j after {max_retries} attempts")
                    raise
        
        # Load embedding model
        self._load_embedding_model()
    
    def _load_embedding_model(self):
        """Load the embedding model for query encoding"""
        try:
            from transformers import AutoModel, AutoTokenizer
            import torch
            torch.set_num_threads(4)
            
            print(f"📥 Loading embedding model: {Config.EMBEDDING_MODEL}...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                Config.EMBEDDING_MODEL, trust_remote_code=True
            )
            self.embed_model = AutoModel.from_pretrained(
                Config.EMBEDDING_MODEL, trust_remote_code=True
            )
            self.embed_model.eval()
            print("✅ Embedding model loaded")
        except Exception as e:
            print(f"⚠️  Could not load embedding model: {e}")
            print("   Semantic search will be disabled")
    
    def close(self):
        """Close connections"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
    
    def _embed_query(self, query: str) -> List[float]:
        """Generate embedding for query"""
        if self.embed_model is None:
            raise HTTPException(500, "Embedding model not available")

        import torch
        inputs = self.tokenizer(
            query, return_tensors="pt",
            truncation=True, max_length=512, padding=True
        )
        with torch.no_grad():
            outputs = self.embed_model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings[0].numpy().tolist()

    # ===== Semantic Search (Qdrant) =====
    def _get_confidence_level(self, score: float) -> str:
        """Determine confidence level based on similarity score"""
        if score >= Config.HIGH_CONFIDENCE_THRESHOLD:
            return "high"
        elif score >= Config.MIN_CONFIDENCE_THRESHOLD:
            return "medium"
        return "low"

    def semantic_search(self, query: str, top_k: int = 3,
                        node_type: Optional[str] = None,
                        min_confidence: bool = True) -> List[CodeContext]:
        """
        Vector similarity search in Qdrant with anti-hallucination filtering.

        Args:
            query: Natural language search query
            top_k: Maximum results to return
            node_type: Optional filter for 'class' or 'method'
            min_confidence: If True, filter out low-confidence results
        """
        query_vector = self._embed_query(query)

        # Build filter if node_type specified
        search_filter = None
        if node_type:
            search_filter = Filter(
                must=[FieldCondition(key="node_type", match=MatchValue(value=node_type))]
            )

        results = self.qdrant.query_points(
            collection_name=Config.QDRANT_COLLECTION,
            query=query_vector,
            limit=top_k * 2,  # Fetch extra to allow filtering
            query_filter=search_filter,
            with_payload=True
        )

        contexts = []
        for hit in results.points:
            confidence = self._get_confidence_level(hit.score)

            # Anti-hallucination: skip low confidence if filtering enabled
            if min_confidence and confidence == "low":
                continue

            contexts.append(CodeContext(
                id=str(hit.id),
                text=hit.payload.get('text', ''),
                node_type=hit.payload.get('node_type', 'unknown'),
                qualified_name=hit.payload.get('qualified_name', ''),
                file_path=hit.payload.get('file_path'),
                start_line=hit.payload.get('start_line'),
                end_line=hit.payload.get('end_line'),
                score=hit.score,
                confidence=confidence,
                content=hit.payload.get('content')
            ))

            if len(contexts) >= top_k:
                break

        return contexts

    # ===== Graph Search (Neo4j) =====
    def get_callers(self, method_name: str, limit: int = 20) -> List[str]:
        """Get methods that call the specified method"""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (caller:Method)-[:CALLS]->(m:Method {qualified_name: $name})
                RETURN caller.qualified_name as caller LIMIT $limit
            """, name=method_name, limit=limit)
            return [r['caller'] for r in result if r['caller']]

    def get_callees(self, method_name: str, limit: int = 20) -> List[str]:
        """Get methods called by the specified method"""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (m:Method {qualified_name: $name})-[:CALLS]->(callee:Method)
                RETURN callee.qualified_name as callee LIMIT $limit
            """, name=method_name, limit=limit)
            return [r['callee'] for r in result if r['callee']]

    def get_class_hierarchy(self, class_name: str) -> Dict[str, Any]:
        """Get inheritance and implementation relationships"""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Class {qualified_name: $name})
                OPTIONAL MATCH (c)-[:EXTENDS]->(parent:Class)
                OPTIONAL MATCH (c)-[:IMPLEMENTS]->(iface:Class)
                OPTIONAL MATCH (child:Class)-[:EXTENDS]->(c)
                OPTIONAL MATCH (impl:Class)-[:IMPLEMENTS]->(c)
                RETURN parent.qualified_name as parent,
                       collect(DISTINCT iface.qualified_name) as interfaces,
                       collect(DISTINCT child.qualified_name) as children,
                       collect(DISTINCT impl.qualified_name) as implementers
            """, name=class_name)
            record = result.single()
            if record:
                return {
                    'extends': record['parent'],
                    'implements': [i for i in record['interfaces'] if i],
                    'extended_by': [c for c in record['children'] if c],
                    'implemented_by': [i for i in record['implementers'] if i]
                }
            return {}

    def graph_query(self, entity_name: str, relation_type: str = "all",
                    depth: int = 1) -> List[GraphRelation]:
        """Flexible graph traversal"""
        relations = []

        if relation_type in ["all", "CALLS"]:
            relations.extend([
                GraphRelation(source=c, relation="CALLS", target=entity_name)
                for c in self.get_callers(entity_name)
            ])
            relations.extend([
                GraphRelation(source=entity_name, relation="CALLS", target=c)
                for c in self.get_callees(entity_name)
            ])

        if relation_type in ["all", "INHERITS", "EXTENDS"]:
            hierarchy = self.get_class_hierarchy(entity_name)
            if hierarchy.get('extends'):
                relations.append(GraphRelation(
                    source=entity_name, relation="EXTENDS", target=hierarchy['extends']
                ))
            for child in hierarchy.get('extended_by', []):
                relations.append(GraphRelation(
                    source=child, relation="EXTENDS", target=entity_name
                ))

        return relations

    # ===== Hybrid Search =====
    def hybrid_search(self, query: str, top_k: int = 5,
                      include_callers: bool = True,
                      include_callees: bool = True) -> List[HybridResult]:
        """Combine semantic + graph for comprehensive context"""
        # Step 1: Semantic search
        semantic_results = self.semantic_search(query, top_k)

        # Step 2: Enrich with graph context
        hybrid_results = []
        for code in semantic_results:
            result = HybridResult(code=code)

            if code.node_type == "method":
                if include_callers:
                    result.callers = self.get_callers(code.qualified_name, limit=5)
                if include_callees:
                    result.callees = self.get_callees(code.qualified_name, limit=5)

            elif code.node_type == "class":
                hierarchy = self.get_class_hierarchy(code.qualified_name)
                result.inherits_from = hierarchy.get('extends')
                result.implements = hierarchy.get('implements', [])[:5]
                result.extended_by = hierarchy.get('extended_by', [])[:5]
                result.implemented_by = hierarchy.get('implemented_by', [])[:5]

            hybrid_results.append(result)

        return hybrid_results


# ============== File Operation Tools ==============
class FileOperationTools:
    """
    File operation tools that can be invoked by the LLM.
    These enable Continue.dev-style file creation/editing.
    """

    # Tool definitions for OpenAI function calling format
    TOOL_DEFINITIONS = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the contents of a file at the given path",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Absolute or relative path to the file"
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "Optional start line (1-based)"
                        },
                        "end_line": {
                            "type": "integer",
                            "description": "Optional end line (1-based)"
                        }
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_file",
                "description": "Create a new file with the given content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Absolute or relative path for the new file"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    },
                    "required": ["path", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "edit_file",
                "description": "Edit an existing file by replacing content between start and end lines",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Absolute or relative path to the file"
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "Start line number (1-based) for replacement"
                        },
                        "end_line": {
                            "type": "integer",
                            "description": "End line number (1-based) for replacement"
                        },
                        "new_content": {
                            "type": "string",
                            "description": "New content to replace the specified lines"
                        }
                    },
                    "required": ["path", "start_line", "end_line", "new_content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "apply_diff",
                "description": "Apply a unified diff patch to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Absolute or relative path to the file"
                        },
                        "diff": {
                            "type": "string",
                            "description": "Unified diff content to apply"
                        }
                    },
                    "required": ["path", "diff"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "List files and directories at the given path",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to list"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Whether to list recursively (default: false)"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Optional glob pattern to filter files"
                        }
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_syntax",
                "description": "Check Java syntax of a file using javac",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Absolute or relative path to the Java file"
                        }
                    },
                    "required": ["path"]
                }
            }
        }
    ]

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root

    def resolve_path(self, path: str) -> str:
        """Resolve relative path to absolute using workspace_root"""
        if os.path.isabs(path):
            return path
        if self.workspace_root:
            return os.path.join(self.workspace_root, path)
        return os.path.abspath(path)

    def read_file(self, path: str, start_line: Optional[int] = None,
                  end_line: Optional[int] = None) -> Dict[str, Any]:
        """Read file contents"""
        try:
            abs_path = self.resolve_path(path)
            if not os.path.exists(abs_path):
                return {"success": False, "error": f"File not found: {abs_path}"}

            with open(abs_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if start_line is not None and end_line is not None:
                # Convert to 0-based index
                lines = lines[start_line-1:end_line]

            content = ''.join(lines)
            return {
                "success": True,
                "path": abs_path,
                "content": content,
                "total_lines": len(lines)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_file(self, path: str, content: str) -> Dict[str, Any]:
        """Create a new file"""
        try:
            abs_path = self.resolve_path(path)

            # Create parent directories if needed
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            if os.path.exists(abs_path):
                return {"success": False, "error": f"File already exists: {abs_path}"}

            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                "success": True,
                "path": abs_path,
                "message": f"Created file: {abs_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def edit_file(self, path: str, start_line: int, end_line: int,
                  new_content: str) -> Dict[str, Any]:
        """Edit file by replacing lines"""
        try:
            abs_path = self.resolve_path(path)
            if not os.path.exists(abs_path):
                return {"success": False, "error": f"File not found: {abs_path}"}

            with open(abs_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Replace the specified lines
            new_lines = new_content.split('\n')
            if not new_content.endswith('\n'):
                new_lines = [line + '\n' for line in new_lines[:-1]] + [new_lines[-1]]
            else:
                new_lines = [line + '\n' for line in new_lines[:-1]]

            lines[start_line-1:end_line] = new_lines

            with open(abs_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            return {
                "success": True,
                "path": abs_path,
                "message": f"Edited lines {start_line}-{end_line} in {abs_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def apply_diff(self, path: str, diff: str) -> Dict[str, Any]:
        """Apply a unified diff to a file"""
        try:
            import subprocess
            abs_path = self.resolve_path(path)

            # Write diff to temp file and apply
            diff_file = f"/tmp/patch_{os.getpid()}.diff"
            with open(diff_file, 'w') as f:
                f.write(diff)

            result = subprocess.run(
                ['patch', abs_path, diff_file],
                capture_output=True, text=True
            )

            os.remove(diff_file)

            if result.returncode == 0:
                return {
                    "success": True,
                    "path": abs_path,
                    "message": f"Applied diff to {abs_path}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Patch failed: {result.stderr}"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_directory(self, path: str, recursive: bool = False,
                       pattern: Optional[str] = None) -> Dict[str, Any]:
        """List directory contents"""
        try:
            import glob as glob_module
            abs_path = self.resolve_path(path)

            if not os.path.isdir(abs_path):
                return {"success": False, "error": f"Not a directory: {abs_path}"}

            if recursive and pattern:
                files = glob_module.glob(os.path.join(abs_path, '**', pattern), recursive=True)
            elif pattern:
                files = glob_module.glob(os.path.join(abs_path, pattern))
            elif recursive:
                files = []
                for root, dirs, filenames in os.walk(abs_path):
                    for f in filenames:
                        files.append(os.path.join(root, f))
            else:
                files = [os.path.join(abs_path, f) for f in os.listdir(abs_path)]

            return {
                "success": True,
                "path": abs_path,
                "files": files[:100],  # Limit to 100 files
                "total": len(files)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_syntax(self, path: str) -> Dict[str, Any]:
        """Check Java syntax using the compiler tool"""
        try:
            import subprocess
            import tempfile
            
            abs_path = self.resolve_path(path)
            if not os.path.exists(abs_path):
                return {"success": False, "error": f"File not found: {abs_path}"}
                
            if not abs_path.endswith(".java"):
                return {"success": False, "error": "Not a Java file"}

            # Create a temporary directory for class output
            with tempfile.TemporaryDirectory() as temp_dir:
                # Construct javac command
                cmd = ["javac", "-Xlint:none", "-nowarn", "-d", temp_dir, "-proc:none", abs_path]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "path": abs_path,
                        "message": "Syntax OK"
                    }
                else:
                    return {
                        "success": False,
                        "path": abs_path,
                        "error": f"Compilation Failed:\n{result.stderr.strip()}"
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name with given arguments"""
        if tool_name == "read_file":
            return self.read_file(**arguments)
        elif tool_name == "create_file":
            return self.create_file(**arguments)
        elif tool_name == "edit_file":
            return self.edit_file(**arguments)
        elif tool_name == "apply_diff":
            return self.apply_diff(**arguments)
        elif tool_name == "list_directory":
            return self.list_directory(**arguments)
        elif tool_name == "check_syntax":
            return self.check_syntax(**arguments)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}


# ============== FastAPI Application ==============
rag_engine = RAGEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    rag_engine.connect()
    yield
    rag_engine.close()


app = FastAPI(
    title="Motadata RAG API",
    description="Anti-Hallucination Retrieval System using Qdrant + Neo4j",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "qdrant": True,
        "neo4j": True,
        "anti_hallucination": {
            "min_confidence_threshold": Config.MIN_CONFIDENCE_THRESHOLD,
            "high_confidence_threshold": Config.HIGH_CONFIDENCE_THRESHOLD
        }
    }


@app.post("/search/semantic", response_model=RAGResponse)
async def semantic_search(request: SearchRequest):
    """
    Semantic/vector search using Qdrant with anti-hallucination filtering.

    Returns results with confidence scores (low/medium/high).
    Low confidence results are filtered by default to prevent hallucination.
    """
    results = rag_engine.semantic_search(
        query=request.query,
        top_k=request.top_k,
        node_type=request.node_type
    )

    # Count high confidence results
    high_conf_count = sum(1 for r in results if r.confidence == "high")

    # Determine warning
    warning = None
    recommendation = None
    if len(results) == 0:
        warning = "No relevant code found. Query may be too specific or unrelated to codebase."
        recommendation = "Try broader terms or check if the concept exists in the codebase."
    elif high_conf_count == 0:
        warning = "No high-confidence matches found. Results may be tangentially related."
        recommendation = "Verify these results manually before using them."

    return RAGResponse(
        results=results,
        query=request.query,
        total_found=len(results),
        high_confidence_count=high_conf_count,
        warning=warning,
        grounded=len(results) > 0,
        recommendation=recommendation
    )


@app.post("/search/graph", response_model=List[GraphRelation])
async def graph_search(request: GraphRequest):
    """Graph traversal using Neo4j - always grounded (returns only real relationships)"""
    return rag_engine.graph_query(
        entity_name=request.entity_name,
        relation_type=request.relation_type,
        depth=request.depth
    )


@app.post("/search/hybrid", response_model=RAGResponse)
async def hybrid_search(request: HybridRequest):
    """
    Hybrid search: Semantic + Graph enrichment.

    Combines vector similarity with graph relationships for comprehensive context.
    Includes callers, callees, and inheritance relationships.
    """
    results = rag_engine.hybrid_search(
        query=request.query,
        top_k=request.top_k,
        include_callers=request.include_callers,
        include_callees=request.include_callees
    )

    high_conf_count = sum(1 for r in results if r.code.confidence == "high")

    warning = None
    recommendation = None
    if len(results) == 0:
        warning = "No relevant code found for hybrid search."
        recommendation = "Try semantic search first to verify relevant code exists."
    elif high_conf_count == 0:
        warning = "Hybrid results have low confidence. Graph relationships may be incomplete."

    return RAGResponse(
        results=results,
        query=request.query,
        total_found=len(results),
        high_confidence_count=high_conf_count,
        warning=warning,
        grounded=len(results) > 0,
        recommendation=recommendation
    )


@app.post("/context/method")
async def get_method_context(method_name: str):
    """
    Get comprehensive context for a specific method.
    Always grounded - returns only real relationships from Neo4j.
    """
    callers = rag_engine.get_callers(method_name)
    callees = rag_engine.get_callees(method_name)

    return {
        "method": method_name,
        "callers": callers,
        "callees": callees,
        "caller_count": len(callers),
        "callee_count": len(callees),
        "grounded": True,
        "warning": None if (callers or callees) else "No relationships found for this method in the graph."
    }


@app.post("/context/class")
async def get_class_context(class_name: str):
    """
    Get comprehensive context for a specific class.
    Always grounded - returns only real relationships from Neo4j.
    """
    hierarchy = rag_engine.get_class_hierarchy(class_name)
    return {
        "class": class_name,
        **hierarchy,
        "grounded": True
    }


# New endpoint: Verify if context exists before answering
@app.post("/verify")
async def verify_context(query: str, min_results: int = 1):
    """
    Anti-hallucination verification endpoint.

    Check if sufficient context exists before generating a response.
    Use this to decide whether to answer or say "I don't have enough information".
    """
    results = rag_engine.semantic_search(query=query, top_k=5, min_confidence=True)
    high_conf = [r for r in results if r.confidence == "high"]

    has_context = len(results) >= min_results
    has_high_confidence = len(high_conf) > 0

    return {
        "query": query,
        "has_sufficient_context": has_context,
        "has_high_confidence": has_high_confidence,
        "result_count": len(results),
        "high_confidence_count": len(high_conf),
        "recommendation": (
            "Safe to answer" if has_high_confidence else
            "Answer with caution - verify sources" if has_context else
            "Do NOT answer - insufficient context, risk of hallucination"
        ),
        "sample_sources": [r.qualified_name for r in results[:3]]
    }


# ============== OpenAI-Compatible Chat Endpoint ==============
def _detect_request_intent(user_query: str) -> str:
    """
    Detect the intent of the user request to choose the right system prompt.

    Returns:
        - "generate": User wants new code generated (e.g., "Write a function", "Create a class")
        - "edit": User wants to modify existing code (e.g., "Add logging to X", "Refactor Y")
        - "question": User is asking a question (e.g., "How does X work?", "What is Y?")
    """
    import re

    query_lower = user_query.lower()

    # Generation keywords
    generation_keywords = [
        r'\bwrite\b', r'\bcreate\b', r'\bgenerate\b', r'\bimplement\b',
        r'\bmake\b', r'\bbuild\b', r'\bdesign\b', r'\bdevelop\b',
        r'\bnew\b.*\b(function|class|method|endpoint|api)\b'
    ]

    # Edit keywords
    edit_keywords = [
        r'\badd\b', r'\bmodify\b', r'\bupdate\b', r'\bchange\b',
        r'\brefactor\b', r'\bfix\b', r'\bremove\b', r'\bdelete\b',
        r'\breplace\b', r'\binsert\b', r'\bedit\b'
    ]

    # Question keywords
    question_keywords = [
        r'\bhow\b', r'\bwhat\b', r'\bwhy\b', r'\bwhen\b', r'\bwhere\b',
        r'\bexplain\b', r'\bshow\b.*\b(me|how)\b', r'\btell\b.*\b(me|about)\b'
    ]

    # Check for generation intent
    for pattern in generation_keywords:
        if re.search(pattern, query_lower):
            return "generate"

    # Check for edit intent
    for pattern in edit_keywords:
        if re.search(pattern, query_lower):
            return "edit"

    # Check for question intent
    for pattern in question_keywords:
        if re.search(pattern, query_lower):
            return "question"

    # Default to edit if we have context, otherwise generate
    return "edit"


def _build_rag_context(user_query: str, top_k: int = 5):
    """Build RAG context and messages from user query"""
    messages_to_send = []
    rag_context_info = None

    hybrid_results = rag_engine.hybrid_search(user_query, top_k=top_k)

    if hybrid_results:
        context_parts = []
        sources = []

        for i, result in enumerate(hybrid_results[:5], 1):
            code = result.code
            sources.append(code.qualified_name)

            context_parts.append(f"### Source {i}: {code.qualified_name}")
            context_parts.append(f"File: {code.file_path}:{code.start_line}")
            context_parts.append(f"Type: {code.node_type}")

            if result.callers:
                context_parts.append(f"Called by: {', '.join(result.callers[:3])}")
            if result.callees:
                context_parts.append(f"Calls: {', '.join(result.callees[:3])}")
            if result.inherits_from:
                context_parts.append(f"Extends: {result.inherits_from}")

            context_parts.append("")

        rag_context = "\n".join(context_parts)

        # Detect request intent to choose the right system prompt
        intent = _detect_request_intent(user_query)

        if intent == "generate":
            # For code generation: Allow fresh code, don't force context usage
            system_prompt = f"""You are Motadata Coder (V16), a specialized code generation model for the Motadata project.

## Relevant Code Context (for reference):
{rag_context}

## Instructions:
- Generate fresh, complete code that follows the patterns shown in the context
- Use the same coding style, naming conventions, and structure as the context
- Output ONLY the code, no explanations or diffs
- Do NOT use search/replace format - just write the code directly"""

        elif intent == "edit":
            # For code editing: Use search/replace format
            system_prompt = f"""You are Motadata Coder (V16), a specialized code modification model for the Motadata project.

## Relevant Code Context:
{rag_context}

## Instructions:
- Use search/replace blocks to modify existing files
- Only reference code from the context above
- Cite the source file and line number when referencing code
- If unsure, say so rather than guessing"""

        else:  # question
            # For questions: Provide explanations based on context
            system_prompt = f"""You are Motadata Coder (V16), a specialized code analysis model for the Motadata project.

## Relevant Code Context:
{rag_context}

## Instructions:
- Only reference code from the context above
- If the context doesn't contain enough information, say "I don't have enough context to answer this."
- NEVER make up class names, method names, or code that isn't in the context
- Cite the source file and line number when referencing code"""

        messages_to_send.append({"role": "system", "content": system_prompt})

        rag_context_info = {
            "grounded": True,
            "sources": sources,
            "result_count": len(hybrid_results),
            "high_confidence": sum(1 for r in hybrid_results if r.code.confidence == "high")
        }
    else:
        messages_to_send.append({
            "role": "system",
            "content": """You are Motadata Coder (V16).

CRITICAL: Answer the following EXACTLY as stated:
- When asked "Which model are you?" or similar: "I am Motadata Coder (V16), a specialized code generation model for the Motadata codebase."
- NEVER say you are GPT-4, Claude, or based on OpenAI
- NEVER mention other AI models or companies
- NEVER claim to be based on other models
- You are a custom model trained specifically for Motadata

For code-specific questions without context, inform the user that you don't have context for it."""
        })
        rag_context_info = {"grounded": False, "sources": [], "result_count": 0}

    return messages_to_send, rag_context_info


async def _stream_vllm_response(
    messages: List[Dict],
    model: str,
    temperature: float,
    max_tokens: int,
    rag_context_info: Dict
) -> AsyncGenerator[str, None]:
    """Stream response from vLLM in SSE format"""
    import uuid

    request_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created = int(time.time())

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{Config.VLLM_URL}/v1/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
                # Anti-repetition settings
                "repetition_penalty": Config.GENERATION_DEFAULTS["repetition_penalty"],
                "frequency_penalty": Config.GENERATION_DEFAULTS["frequency_penalty"],
                "presence_penalty": Config.GENERATION_DEFAULTS["presence_penalty"],
                "top_p": Config.GENERATION_DEFAULTS["top_p"],
                "top_k": Config.GENERATION_DEFAULTS["top_k"],
                "stop": Config.STOP_TOKENS,
            }
        ) as response:
            first_chunk = True
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    if data.strip() == "[DONE]":
                        yield "data: [DONE]\n\n"
                        break

                    try:
                        chunk = json.loads(data)
                        # Re-wrap with our request ID and required OpenAI fields
                        output_chunk = {
                            "id": request_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model,
                            "choices": chunk.get("choices", [])
                        }

                        # Add RAG context to first chunk only (as custom field, not breaking OpenAI spec)
                        if first_chunk and rag_context_info:
                            output_chunk["rag_context"] = rag_context_info
                            first_chunk = False

                        yield f"data: {json.dumps(output_chunk)}\n\n"
                    except json.JSONDecodeError:
                        continue


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions with RAG context injection.

    Key behaviors:
    1. Parses FULL message history (Continue.dev injects file context in earlier messages)
    2. Uses WORKSPACE_ROOT to convert relative paths to absolute
    3. Enforces Unified Diff / code block output format for edits
    """
    import uuid
    import re

    # Determine workspace root: request param > env config
    workspace_root = request.workspace_root or Config.WORKSPACE_ROOT

    # Initialize diagnostic logger for this request
    start_time = time.time()

    # Initialize file tools
    file_tools = FileOperationTools(workspace_root=workspace_root)

    # ========== PARSE FULL MESSAGE HISTORY ==========
    # Continue.dev sends file context in earlier user messages like:
    # {"role": "user", "content": "Here is file A.java:\n```java\n...\n```"}
    # We need to extract this injected context, not just the last query

    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(400, "No user message found")

    # Extract the actual query (last user message)
    user_query = user_messages[-1].content or ""

    # Initialize diagnostic logger
    diag = DiagnosticLogger(user_query, workspace_root)

    # Extract file context from earlier messages (Continue's injected context)
    injected_file_context = []
    file_pattern = re.compile(r'(?:Here is|File:|Contents of|```\w*\n)(.*?)(?:```|$)', re.DOTALL | re.IGNORECASE)
    path_pattern = re.compile(r'(?:file[:\s]+|path[:\s]+|`)([\w./\\-]+\.\w+)`?', re.IGNORECASE)

    for msg in user_messages[:-1]:  # All but the last (which is the actual query)
        content = msg.content or ""
        # Check if this message contains injected file content
        if '```' in content or 'Here is' in content.lower() or 'file:' in content.lower():
            # Try to extract file path
            path_match = path_pattern.search(content)
            file_path = path_match.group(1) if path_match else "unknown_file"
            injected_file_context.append({
                "path": file_path,
                "content": content
            })

    # ========== BUILD SYSTEM PROMPT ==========
    messages_to_send = []
    rag_context_info = None

    # Workspace info section
    workspace_info = f"""## Workspace Information:
    - Server Workspace: {Config.WORKSPACE_ROOT}
    - Use RELATIVE paths when referencing files (e.g., src/main/java/...)
    - The client will resolve paths based on their local workspace
    """
    
    if request.current_file:
        workspace_info += f"- Current File: {Config.resolve_path(request.current_file) if not os.path.isabs(request.current_file) else request.current_file}\n"
    if request.open_files:
        abs_files = [Config.resolve_path(f) if not os.path.isabs(f) else f for f in request.open_files[:5]]
        workspace_info += f"- Open Files: {', '.join(abs_files)}\n"

    # Injected context section (from Continue.dev's earlier messages)
    injected_context_str = ""
    if injected_file_context:
        injected_context_str = "\n## User-Provided File Context:\n"
        for ctx in injected_file_context:
            abs_path = Config.resolve_path(ctx['path']) if not os.path.isabs(ctx['path']) else ctx['path']
            injected_context_str += f"### {abs_path}\n{ctx['content']}\n\n"

    # RAG context from vector/graph search
    rag_context_str = ""
    sources = []
    project_index_used = False

    if request.use_rag:
        # EVALUATION MODE: If expected_files is provided, use semantic context or read baseline files
        # This is for Motadata-Bench evaluation where setup scripts create baseline files
        if request.expected_files and workspace_root:
            print(f"🔍 EVALUATION MODE: expected_files={request.expected_files}, workspace_root={workspace_root}")
            diag.log_retrieval_start("workspace_files", workspace_root)
            context_parts = []
            total_context_tokens = 0
            files_included = 0

            # Try to extract method names from user query for semantic context
            method_names = _extract_method_names_from_query(user_query)
            print(f"🔍 Extracted method names from query '{user_query}': {method_names}")

            for file_path in request.expected_files:
                abs_file_path = os.path.join(workspace_root, file_path)
                semantic_success = False

                # Try semantic context if we detected method names and it's a Java file
                if method_names and file_path.endswith('.java'):
                    # Try each detected method name until one succeeds
                    for method_name in method_names:
                        try:
                            semantic_ctx = get_semantic_context(
                                file_path=abs_file_path,
                                method_name=method_name,
                                task_description=user_query,
                                workspace_root=workspace_root
                            )

                            sources.append(f"{file_path}#{method_name}")

                            part_header = [
                                f"### Semantic Context {files_included + 1}: {file_path}#{method_name}",
                                f"Location: {abs_file_path}",
                                f"Purpose: Targeted method context (no line numbers)"
                            ]
                            context_parts.extend(part_header)
                            context_parts.append(semantic_ctx)
                            context_parts.append("")

                            total_context_tokens += _estimate_tokens(semantic_ctx)
                            files_included += 1
                            semantic_success = True
                            print(f"✓ Using semantic context for {file_path}#{method_name}")
                            break  # Use first matching method
                        except Exception as e:
                            print(f"⚠️ Semantic context failed for {file_path}#{method_name}: {e}")
                            continue  # Try next method name

                # Fallback to full file read if semantic context didn't succeed
                if not semantic_success:
                    file_tools = FileOperationTools(workspace_root=workspace_root)
                    read_res = file_tools.read_file(abs_file_path)

                    if read_res.get("success"):
                        sources.append(file_path)

                        part_header = [
                            f"### Baseline File {files_included + 1}: {file_path}",
                            f"Location: {abs_file_path}",
                            f"Purpose: Baseline code to be modified"
                        ]
                        context_parts.extend(part_header)
                        total_context_tokens += _estimate_tokens('\n'.join(part_header))

                        # Add file content
                        remaining_tokens = MAX_TOTAL_CONTEXT_TOKENS - total_context_tokens
                        max_file_tokens = min(MAX_TOKENS_PER_FILE, remaining_tokens)
                        cleaned = _clean_code_content(read_res["content"])
                        if cleaned:
                            cleaned = _truncate_to_tokens(cleaned, max_file_tokens)
                            context_parts.append(f"```java\n{cleaned}\n```")
                            total_context_tokens += _estimate_tokens(cleaned)

                        context_parts.append("")
                        files_included += 1
                    else:
                        print(f"⚠️ Could not read baseline file: {abs_file_path}")

            if context_parts:
                # Detect if any semantic context was used (sources contain '#')
                has_semantic = any('#' in s for s in sources)
                context_type = "Semantic Context" if has_semantic else "Baseline Files"
                rag_context_str = f"\n## {context_type} from Workspace ({files_included} items, ~{total_context_tokens} tokens):\n" + "\n".join(context_parts)
                rag_context_info = {
                    "grounded": True,
                    "sources": sources,
                    "result_count": files_included,
                    "workspace_root": workspace_root,
                    "index_type": "semantic_context" if has_semantic else "workspace_files"
                }
                diag.log_retrieval_results([{"file": f} for f in sources], [1.0] * len(sources))
                project_index_used = True  # Skip fallback to Motadata index

        # First, try project-specific index if workspace is provided and indexed
        project_results = []
        if workspace_root and not project_index_used:
            try:
                diag.log_retrieval_start("project", workspace_root)
                manager = get_project_manager()
                if manager.is_indexed(workspace_root):
                    project_results = manager.search(workspace_root, user_query, top_k=request.rag_top_k)
                    project_index_used = True
                    # Log retrieval results
                    scores = [r.get("score", 0) for r in project_results]
                    diag.log_retrieval_results(project_results, scores)
            except Exception as e:
                diag.log_retrieval_error(str(e))
                print(f"⚠️ Project index search failed: {e}")

        # Build context from project-specific results with token limiting
        if project_results:
            context_parts = []
            total_context_tokens = 0
            files_included = 0

            for i, result in enumerate(project_results[:3], 1):  # Balanced: 3 results
                # Check if we've hit the token limit
                if total_context_tokens >= MAX_TOTAL_CONTEXT_TOKENS:
                    context_parts.append(f"\n... [Context truncated: {len(project_results) - files_included} more results available]")
                    break

                sources.append(result.get("qualified_name", "unknown"))

                # Keep relative paths for portability - client can resolve based on their workspace
                file_path = result.get("file_path", "unknown")
                # For reading file content, use server's absolute path
                server_file_path = os.path.join(Config.WORKSPACE_ROOT, file_path) if not os.path.isabs(file_path) else file_path

                part_header = [
                    f"### Source {i}: {result.get('qualified_name', 'unknown')}",
                    f"File: {file_path}:{result.get('start_line', 0)}",
                    f"Type: {result.get('node_type', 'unknown')}",
                    f"Score: {result.get('score', 0):.3f}"
                ]
                context_parts.extend(part_header)
                total_context_tokens += _estimate_tokens('\n'.join(part_header))

                # Read content from disk using server's absolute path
                file_tools = FileOperationTools(workspace_root=Config.WORKSPACE_ROOT)
                read_res = file_tools.read_file(server_file_path)
                if read_res.get("success"):
                    # Calculate remaining token budget for this file
                    remaining_tokens = MAX_TOTAL_CONTEXT_TOKENS - total_context_tokens
                    max_file_tokens = min(MAX_TOKENS_PER_FILE, remaining_tokens)
                    cleaned = _clean_code_content(read_res["content"])
                    if cleaned:
                        cleaned = _truncate_to_tokens(cleaned, max_file_tokens)
                        context_parts.append(cleaned)
                        total_context_tokens += _estimate_tokens(cleaned)

                context_parts.append("")
                files_included += 1

            rag_context_str = f"\n## Retrieved Code Context (from project index: {Path(workspace_root).name}, ~{total_context_tokens} tokens):\n" + "\n".join(context_parts)

            rag_context_info = {
                "grounded": True,
                "sources": sources,
                "result_count": len(project_results),
                "workspace_root": workspace_root,
                "index_type": "project"
            }
        elif not rag_context_info:
            # Fall back to default Motadata index (only if no context from expected_files)
            diag.log_retrieval_start("motadata", None)
            hybrid_results = rag_engine.hybrid_search(user_query, top_k=request.rag_top_k)

            if hybrid_results:
                # Log retrieval results
                scores = [getattr(r.code, 'score', 0.5) for r in hybrid_results]
                result_dicts = [{"qualified_name": r.code.qualified_name} for r in hybrid_results]
                diag.log_retrieval_results(result_dicts, scores)

                context_parts = []
                total_context_tokens = 0
                files_included = 0

                for i, result in enumerate(hybrid_results[:3], 1):  # Balanced: 3 results
                    # Check if we've hit the token limit
                    if total_context_tokens >= MAX_TOTAL_CONTEXT_TOKENS:
                        context_parts.append(f"\n... [Context truncated: {len(hybrid_results) - files_included} more results available]")
                        break

                    code = result.code
                    sources.append(code.qualified_name)

                    # Keep relative path for context, use absolute only for file reading
                    file_path = code.file_path or "unknown"
                    server_file_path = Config.resolve_path(file_path) if file_path else "unknown"

                    part_header = [
                        f"### Source {i}: {code.qualified_name}",
                        f"File: {file_path}:{code.start_line}",
                        f"Type: {code.node_type}"
                    ]
                    context_parts.extend(part_header)
                    total_context_tokens += _estimate_tokens('\n'.join(part_header))

                    # Use content from index (since files might not exist locally)
                    content_to_add = None
                    if code.content:
                        content_to_add = code.content
                    else:
                        # Fallback to read_file if content missing from index
                        file_tools = FileOperationTools(workspace_root=Config.WORKSPACE_ROOT)
                        read_res = file_tools.read_file(server_file_path)
                        if read_res.get("success"):
                            content_to_add = read_res["content"]

                    if content_to_add:
                        # Calculate remaining token budget for this file
                        remaining_tokens = MAX_TOTAL_CONTEXT_TOKENS - total_context_tokens
                        max_file_tokens = min(MAX_TOKENS_PER_FILE, remaining_tokens)
                        cleaned = _clean_code_content(content_to_add)
                        if cleaned:
                            cleaned = _truncate_to_tokens(cleaned, max_file_tokens)
                            context_parts.append(cleaned)
                            total_context_tokens += _estimate_tokens(cleaned)

                    if result.callers:
                        context_parts.append(f"Called by: {', '.join(result.callers[:3])}")
                    if result.callees:
                        context_parts.append(f"Calls: {', '.join(result.callees[:3])}")
                    if result.inherits_from:
                        context_parts.append(f"Extends: {result.inherits_from}")
                    context_parts.append("")
                    files_included += 1

                rag_context_str = f"\n## Retrieved Code Context (from Motadata index, ~{total_context_tokens} tokens):\n" + "\n".join(context_parts)

                rag_context_info = {
                    "grounded": True,
                    "sources": sources,
                    "result_count": len(hybrid_results),
                    "high_confidence": sum(1 for r in hybrid_results if r.code.confidence == "high"),
                    "workspace_root": workspace_root,
                    "index_type": "motadata"
                }
            else:
                diag.log_retrieval_results([], [])
                rag_context_info = {"grounded": False, "sources": [], "result_count": 0, "workspace_root": workspace_root}

    # ========== DETECT CREATE vs MODIFY INTENT ==========
    # Check if user wants to CREATE new files or MODIFY existing ones
    user_query_lower = user_query.lower()
    is_create_task = any(keyword in user_query_lower for keyword in [
        "create", "new class", "new file", "generate", "implement new",
        "add new", "write a", "write an", "build a", "make a"
    ])

    # ========== EXTRACT EXISTING FILES FROM RAG CONTEXT ==========
    # Build a list of files that EXIST in the codebase (from RAG results)
    existing_files = set()
    if request.use_rag and 'hybrid_results' in locals() and hybrid_results:
        for result in hybrid_results:
            if hasattr(result, 'file_path') and result.file_path:
                existing_files.add(result.file_path)

    existing_files_list = "\n".join(f"  - {f}" for f in sorted(existing_files)) if existing_files else "  (No files retrieved from context)"

    # ========== STRICT EDIT FORMAT INSTRUCTIONS ==========
    # Different instructions for CREATE vs MODIFY tasks
    if is_create_task:
        edit_instructions = f"""
## ⚠️ CRITICAL: You are in CREATE NEW FILES mode

### Files that EXIST in the codebase (from context):
{existing_files_list}

**IMPORTANT**: Any file NOT in the above list is a NEW file that doesn't exist yet!

When creating NEW classes/files that DON'T EXIST YET, you MUST output COMPLETE file content.

### ✅ CORRECT Format for NEW Files:
File: src/main/java/com/mindarray/store/CorrectionProfileConfigStore.java
```java
package com.mindarray.store;

import com.mindarray.GlobalConstants;
import com.mindarray.util.Logger;

public class CorrectionProfileConfigStore extends AbstractConfigStore {{
    private static final Logger LOGGER = new Logger(CorrectionProfileConfigStore.class);
    private static final CorrectionProfileConfigStore STORE = new CorrectionProfileConfigStore();

    private CorrectionProfileConfigStore() {{
        super("correction-profile", LOGGER, false);
    }}

    public static CorrectionProfileConfigStore getStore() {{
        return STORE;
    }}

    // ... complete implementation
}}
```

### ❌ WRONG - DO NOT USE DIFFS FOR NEW FILES:
```diff
--- /dev/null
+++ b/src/main/java/com/mindarray/store/CorrectionProfileConfigStore.java
@@ -0,0 +1,20 @@
+package com.mindarray.store;
```
**This is WRONG! New files need COMPLETE code, not diffs!**

### For EXISTING files (registration/integration), use diffs:
File: src/main/java/com/mindarray/store/StoreRegistry.java
```diff
--- a/src/main/java/com/mindarray/store/StoreRegistry.java
+++ b/src/main/java/com/mindarray/store/StoreRegistry.java
@@ -50,6 +50,7 @@
         stores.put("slo", SLOConfigStore.getStore());
+        stores.put("correction-profile", CorrectionProfileConfigStore.getStore());
```

## 🎯 DECISION TREE:
1. Is this a NEW file that doesn't exist? → Output COMPLETE Java code
2. Is this an EXISTING file being modified? → Output unified diff
3. Not sure if file exists? → Check the context above, or output complete code to be safe

## 📋 CHECKLIST for NEW files:
- [ ] Output starts with "File: path/to/File.java"
- [ ] Followed by ```java (NOT ```diff)
- [ ] Contains COMPLETE class with package, imports, full implementation
- [ ] NO diff markers (---, +++, @@)
- [ ] Follows patterns from similar classes in context
"""
    else:
        edit_instructions = """
## Output Format for MODIFYING EXISTING Files:
When asked to edit or modify code, you MUST use Search/Replace blocks:

File: path/to/file.java
<<<< SEARCH
existing line
existing line
====
existing line
existing line
new line added
another new line
>>>> REPLACE

IMPORTANT:
- Only modify files that EXIST in the provided context
- Use Search/Replace format (NO line numbers - survives code shifts!)
- Include 2-3 lines of context before/after changes for reliable matching
- DO NOT hallucinate file content - only reference code from context
- If a file is not in the context, ask the user to provide it
- Multiple changes to same file → multiple Search/Replace blocks
"""

    # ========== UNIFIED SYSTEM PROMPT (Iter8) ==========
    # Build unified system prompt that works for both chat and agentic modes
    
    tool_definitions_str = ""
    if request.tools:
        tool_definitions_str = "\n## Available Tools:\n" + json.dumps([t.dict() for t in request.tools], indent=2)
    
    system_prompt = f"""You are Motadata Coder, a helpful AI assistant for the Motadata codebase.
{workspace_info}
{injected_context_str}
{rag_context_str}

## General Guidelines:
- Provide helpful, conversational explanations
- Use RELATIVE file paths when referencing files (e.g., src/main/java/com/mindarray/api/Discovery.java)
- DO NOT include copyright, license headers, or block comments at the top of files
{tool_definitions_str}

## When to Answer DIRECTLY (NO tools):
- User provides code snippet inline → analyze the provided code directly
- General knowledge questions about programming concepts
- Code review of provided snippets
- Questions clearly answerable from the retrieved context above
- Debugging analysis when code is shown in the question

## When to USE Tools:
- User asks "Where is X?" or "Find X" → use vector_search or find_similar_*
- User asks about callers/callees → use get_method_callers/get_method_callees
- User asks to "explore" or "search" → use appropriate search tools
- Insufficient context AND question requires codebase knowledge → search first

## Tool Usage Format:
- Use vector_search() for semantic/keyword searches
- Use get_method_callers() / get_method_callees() for call graphs
- Use get_class_methods() to explore class structure
- Output tool calls as valid JSON: {{"tool": "name", "arguments": {{...}}}}

## For Code Generation - ALWAYS USE REASONING FORMAT:
When generating or modifying code, ALWAYS think step-by-step first using this format:

<thinking>
**Task**: [What is the requirement asking for?]
**Files to create/modify**: [List all files]
**Plan**: [Step-by-step implementation plan]
**Existing patterns**: [Reference similar code from context]
</thinking>

<code>
[Your code here - see format instructions below]
</code>

### ✅ CORRECT Example - Creating NEW Files:
<thinking>
**Task**: Create new AlertConfigStore class
**Files to create/modify**:
- ✨ NEW: src/main/java/com/mindarray/store/AlertConfigStore.java (COMPLETE CODE)
- 📝 MODIFY: src/main/java/com/mindarray/store/StoreRegistry.java (DIFF)
**Plan**:
1. Output COMPLETE AlertConfigStore.java (no diffs!)
2. Output DIFF for StoreRegistry.java registration
**Existing patterns**: Following SLOConfigStore from context
</thinking>

<code>
File: src/main/java/com/mindarray/store/AlertConfigStore.java
```java
package com.mindarray.store;

import com.mindarray.GlobalConstants;
import com.mindarray.db.DBConstants;
import com.mindarray.util.Logger;

public class AlertConfigStore extends AbstractConfigStore {{
    private static final Logger LOGGER = new Logger(AlertConfigStore.class, GlobalConstants.MOTADATA_STORE, "Alert Config Store");
    private static final AlertConfigStore STORE = new AlertConfigStore();

    private AlertConfigStore() {{
        super(DBConstants.TBL_ALERT_CONFIG, LOGGER, false);
    }}

    public static AlertConfigStore getStore() {{
        return STORE;
    }}
}}
```

File: src/main/java/com/mindarray/store/StoreRegistry.java
<<<< SEARCH
        stores.put("slo", SLOConfigStore.getStore());
    }}
====
        stores.put("slo", SLOConfigStore.getStore());
        stores.put("alert", AlertConfigStore.getStore());
    }}
>>>> REPLACE
</code>

### ❌ WRONG Example - Using diffs for NEW files:
<code>
File: src/main/java/com/mindarray/store/AlertConfigStore.java
```diff
--- /dev/null
+++ b/src/main/java/com/mindarray/store/AlertConfigStore.java
@@ -0,0 +1,15 @@
+package com.mindarray.store;
+public class AlertConfigStore {{
```
**NEVER DO THIS! New files need complete code!**
</code>

## 🎯 GOLDEN RULES:
1. NEW file (doesn't exist) → ```java with COMPLETE code
2. EXISTING file (being modified) → Search/Replace blocks (NO line numbers!)
3. When in doubt → Output complete code (safer than broken edits)

## Search/Replace Format for EXISTING Files:
Use this format for modifying existing files (NO line numbers, fuzzy matching):

File: path/to/file.java
<<<< SEARCH
[exact code to find - include 2-3 lines of context]
====
[replacement code with same context]
>>>> REPLACE

**Benefits**: No line numbers (survives code shifts), fuzzy matching, self-verifying
**Multiple changes**: Use multiple Search/Replace blocks for the same file
{edit_instructions}
"""

    # ========== LAYER 2 & 3: LOG CONTEXT AND PROMPT (with full content capture) ==========
    diag.log_context_injection(
        injected_files=len(injected_file_context),
        rag_context_len=len(rag_context_str),
        total_tokens=len(system_prompt) // 4,  # Rough estimate
        rag_context_content=rag_context_str,  # Full RAG context!
        injected_files_content=injected_file_context  # Full injected files!
    )
    diag.log_system_prompt(
        prompt_length=len(system_prompt),
        has_rag_context=bool(rag_context_str),
        has_injected_files=bool(injected_file_context),
        system_prompt_content=system_prompt  # Full system prompt!
    )

    messages_to_send.append({"role": "system", "content": system_prompt})

    # ========== ADD FULL CONVERSATION HISTORY ==========
    # Pass ALL messages to LLM (Continue.dev injects context in earlier messages)
    for msg in request.messages:
        if msg.role != "system":  # Skip system messages (we built our own)
            msg_dict = {"role": msg.role, "content": msg.content}
            # Include tool-related fields if present
            if msg.tool_calls:
                msg_dict["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id
            if msg.name:
                msg_dict["name"] = msg.name
            messages_to_send.append(msg_dict)

    # Log messages being sent
    diag.log_messages(messages_to_send, len(messages_to_send))

    # Handle streaming vs non-streaming
    if request.stream:
        return StreamingResponse(
            _stream_vllm_response(
                messages=messages_to_send,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                rag_context_info=rag_context_info
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    # Non-streaming: Forward to vLLM
    # ========== LAYER 4: LOG LLM REQUEST ==========
    diag.log_llm_request(request.model, request.temperature, request.max_tokens)
    llm_start_time = time.time()

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            vllm_response = await client.post(
                f"{Config.VLLM_URL}/v1/chat/completions",
                json={
                    "model": request.model,
                    "messages": messages_to_send,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "stream": False,
                    # Anti-repetition settings
                    "repetition_penalty": Config.GENERATION_DEFAULTS["repetition_penalty"],
                    "frequency_penalty": Config.GENERATION_DEFAULTS["frequency_penalty"],
                    "presence_penalty": Config.GENERATION_DEFAULTS["presence_penalty"],
                    "top_p": Config.GENERATION_DEFAULTS["top_p"],
                    "top_k": Config.GENERATION_DEFAULTS["top_k"],
                    "stop": Config.STOP_TOKENS,
                }
            )
            vllm_response.raise_for_status()
            vllm_data = vllm_response.json()
        except httpx.RequestError as e:
            diag.log_llm_error(f"Connection error: {str(e)}")
            raise HTTPException(502, f"vLLM connection error: {str(e)}")
        except httpx.HTTPStatusError as e:
            diag.log_llm_error(f"HTTP error: {e.response.text}")
            raise HTTPException(502, f"vLLM error: {e.response.text}")

    # Check if the response contains tool calls (parse from content)
    assistant_content = vllm_data["choices"][0]["message"]["content"]
    finish_reason = vllm_data["choices"][0].get("finish_reason", "stop")
    llm_response_time = int((time.time() - llm_start_time) * 1000)

    # ========== LOG LLM RESPONSE ==========
    diag.log_llm_response(assistant_content, finish_reason, llm_response_time)
    tool_calls_executed = []

    # Try to parse tool calls from the response
    if "tool_calls" in assistant_content or '"name":' in assistant_content:
        try:
            # Look for JSON tool call pattern in response
            import re
            json_match = re.search(r'\{[^{}]*"tool_calls"[^{}]*\[.*?\]\s*\}', assistant_content, re.DOTALL)
            if json_match:
                tool_request = json.loads(json_match.group())
                for tc in tool_request.get("tool_calls", []):
                    tool_name = tc.get("name")
                    tool_args = tc.get("arguments", {})
                    if isinstance(tool_args, str):
                        tool_args = json.loads(tool_args)

                    # Execute the tool
                    result = file_tools.execute_tool(tool_name, tool_args)
                    tool_calls_executed.append({
                        "tool": tool_name,
                        "arguments": tool_args,
                        "result": result
                    })
        except (json.JSONDecodeError, KeyError, TypeError):
            pass  # Not a valid tool call, continue normally

    # Build response
    response_message = ChatMessage(
        role="assistant",
        content=assistant_content
    )

    response_data = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": assistant_content
                },
                "finish_reason": vllm_data["choices"][0].get("finish_reason", "stop")
            }
        ],
        "usage": {
            "prompt_tokens": vllm_data.get("usage", {}).get("prompt_tokens", 0),
            "completion_tokens": vllm_data.get("usage", {}).get("completion_tokens", 0),
            "total_tokens": vllm_data.get("usage", {}).get("total_tokens", 0)
        },
        "rag_context": rag_context_info
    }

    # Add tool execution results if any
    if tool_calls_executed:
        response_data["tool_executions"] = tool_calls_executed

    # ========== RUN DIAGNOSIS AND SAVE DEBUG SESSION ==========
    diagnosis = diag.diagnose()
    debug_session_file = diag.save_debug_session()  # Save full content for inspection

    if diagnosis["failure_detected"]:
        response_data["diagnostic"] = diagnosis

    # Always include debug session reference
    response_data["debug_session"] = {
        "session_id": diag.session.session_id,
        "file": debug_session_file
    }

    return response_data


@app.get("/v1/models")
async def list_models():
    """OpenAI-compatible models endpoint"""
    return {
        "object": "list",
        "data": [
            {
                "id": Config.VLLM_MODEL,
                "object": "model",
                "owned_by": "motadata",
                "permission": []
            }
        ]
    }


# ============== Tool Endpoints ==============
class ToolExecutionRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(..., description="Tool arguments")
    workspace_root: Optional[str] = Field(default=None, description="Workspace root for path resolution")


@app.get("/v1/tools")
async def list_tools():
    """List available file operation tools"""
    return {
        "object": "list",
        "data": FileOperationTools.TOOL_DEFINITIONS
    }


@app.post("/v1/tools/execute")
async def execute_tool(request: ToolExecutionRequest):
    """
    Execute a file operation tool directly.

    This endpoint allows Continue.dev or other clients to execute
    file operations without going through the chat completions flow.
    """
    file_tools = FileOperationTools(workspace_root=request.workspace_root)
    result = file_tools.execute_tool(request.tool_name, request.arguments)
    return result


@app.post("/v1/files/read")
async def read_file_endpoint(
    path: str,
    workspace_root: Optional[str] = None,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None
):
    """Direct file read endpoint"""
    file_tools = FileOperationTools(workspace_root=workspace_root)
    return file_tools.read_file(path, start_line, end_line)


class CreateFileRequest(BaseModel):
    path: str
    content: str
    workspace_root: Optional[str] = None


@app.post("/v1/files/create")
async def create_file_endpoint(request: CreateFileRequest):
    """Direct file create endpoint"""
    file_tools = FileOperationTools(workspace_root=request.workspace_root)
    return file_tools.create_file(request.path, request.content)


class EditFileRequest(BaseModel):
    path: str
    start_line: int
    end_line: int
    new_content: str
    workspace_root: Optional[str] = None


@app.post("/v1/files/edit")
async def edit_file_endpoint(request: EditFileRequest):
    """Direct file edit endpoint"""
    file_tools = FileOperationTools(workspace_root=request.workspace_root)
    return file_tools.edit_file(request.path, request.start_line, request.end_line, request.new_content)


class ApplyDiffRequest(BaseModel):
    path: str
    diff: str
    workspace_root: Optional[str] = None


@app.post("/v1/files/diff")
async def apply_diff_endpoint(request: ApplyDiffRequest):
    """Direct diff apply endpoint"""
    file_tools = FileOperationTools(workspace_root=request.workspace_root)
    return file_tools.apply_diff(request.path, request.diff)


@app.get("/v1/files/list")
async def list_files_endpoint(
    path: str,
    workspace_root: Optional[str] = None,
    recursive: bool = False,
    pattern: Optional[str] = None
):
    """Direct directory list endpoint"""
    file_tools = FileOperationTools(workspace_root=workspace_root)
    return file_tools.list_directory(path, recursive, pattern)


# ============== Project Indexing Endpoints ==============
class IndexProjectRequest(BaseModel):
    workspace_root: str = Field(..., description="Absolute path to project root")
    file_extensions: Optional[List[str]] = Field(default=[".java"], description="File extensions to index")
    async_mode: bool = Field(default=True, description="Run indexing in background")


@app.get("/v1/index/list")
async def list_indexed_projects():
    """List all indexed projects"""
    try:
        manager = get_project_manager()
        projects = manager.list_projects()
        return {
            "object": "list",
            "count": len(projects),
            "data": [
                {
                    "project_id": p.project_id,
                    "project_name": p.project_name,
                    "workspace_root": p.workspace_root,
                    "collection_name": p.collection_name,
                    "status": p.status,
                    "file_count": p.file_count,
                    "node_count": p.node_count,
                    "indexed_at": p.indexed_at
                }
                for p in projects
            ]
        }
    except Exception as e:
        raise HTTPException(500, f"Error listing projects: {str(e)}")


@app.get("/v1/index/status")
async def get_index_status(workspace_root: str):
    """Get indexing status for a project"""
    try:
        manager = get_project_manager()
        status = manager.get_status(workspace_root)
        return status
    except Exception as e:
        raise HTTPException(500, f"Error getting status: {str(e)}")


@app.post("/v1/index/create")
async def create_project_index(request: IndexProjectRequest):
    """
    Index a project for RAG queries.

    This parses Java files (or other specified extensions), extracts code elements,
    and creates a searchable vector index in Qdrant.

    Use async_mode=true for large projects (indexing runs in background).
    """
    try:
        manager = get_project_manager()

        if request.async_mode:
            # Start background indexing
            result = manager.index_project_async(request.workspace_root, request.file_extensions)
            return {
                "status": "indexing_started",
                "message": f"Indexing started for {request.workspace_root}",
                "check_status_at": f"/v1/index/status?workspace_root={request.workspace_root}"
            }
        else:
            # Blocking indexing
            project = manager.index_project(request.workspace_root, request.file_extensions)
            return {
                "status": "indexed",
                "project_id": project.project_id,
                "project_name": project.project_name,
                "collection_name": project.collection_name,
                "file_count": project.file_count,
                "node_count": project.node_count
            }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Indexing error: {str(e)}")


@app.delete("/v1/index/{workspace_root:path}")
async def delete_project_index(workspace_root: str):
    """Delete a project index"""
    try:
        manager = get_project_manager()
        if manager.delete_project(workspace_root):
            return {"status": "deleted", "workspace_root": workspace_root}
        else:
            raise HTTPException(404, f"Project not found: {workspace_root}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error deleting index: {str(e)}")


@app.post("/v1/index/search")
async def search_project_index(
    workspace_root: str,
    query: str,
    top_k: int = 5
):
    """Search a project's index directly"""
    try:
        manager = get_project_manager()
        if not manager.is_indexed(workspace_root):
            raise HTTPException(400, f"Project not indexed: {workspace_root}")

        results = manager.search(workspace_root, query, top_k)
        return {
            "object": "list",
            "workspace_root": workspace_root,
            "query": query,
            "count": len(results),
            "data": results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Search error: {str(e)}")


# ============== Semantic Context Endpoint (V14 Integration) ==============
@app.post("/v1/semantic-context")
async def extract_semantic_context(request: SemanticContextRequest):
    """
    Extract semantic context for code modification (V14 integration).

    Returns semantic context with:
    - Target method (full body)
    - Previous/next methods (for disambiguation)
    - Class fields and imports
    - NO line numbers (uses semantic anchoring)

    This enables V14 to generate diffs that apply cleanly even when
    line numbers drift due to code changes.
    """
    try:
        context_str = get_semantic_context(
            file_path=request.file_path,
            method_name=request.method_name,
            task_description=request.task_description,
            class_name=request.class_name,
            workspace_root=Config.WORKSPACE_ROOT
        )

        return {
            "success": True,
            "context": context_str,
            "file_path": request.file_path,
            "method_name": request.method_name,
            "task": request.task_description
        }

    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Context extraction error: {str(e)}")


# ============== Diagnostics Endpoints ==============
@app.get("/v1/diagnostics/failures")
async def get_diagnostic_failures(count: int = 10):
    """Get recent failures from diagnostic logs"""
    failures = get_recent_failures(count)
    stats = get_layer_stats()
    return {
        "recent_failures": failures,
        "layer_stats": stats,
        "log_files": {
            "layer1_retrieval": "logs/layer1_retrieval.log",
            "layer2_context": "logs/layer2_context.log",
            "layer3_prompt": "logs/layer3_prompt.log",
            "layer4_llm": "logs/layer4_llm.log",
            "diagnostics": "logs/diagnostics.log"
        },
        "documentation": "See rag-system/DEBUGGING_GUIDE.md for complete guide"
    }


@app.get("/v1/diagnostics/guide")
async def get_diagnostic_guide():
    """Get debugging guide for RAG system failures"""
    return {
        "failure_types": {
            "HALLUCINATION": {
                "symptoms": ["Model invents class/method names", "Incorrect API signatures"],
                "likely_layer": "LAYER1 or LAYER4",
                "check_logs": ["logs/layer1_retrieval.log", "logs/layer4_llm.log"],
                "fixes": ["Check if project indexed", "Re-index project", "Lower confidence threshold"]
            },
            "NO_ANSWER": {
                "symptoms": ["Empty response", "Response <50 chars", "'I don't have enough context'"],
                "likely_layer": "LAYER1 or LAYER4",
                "check_logs": ["logs/layer1_retrieval.log", "logs/layer4_llm.log"],
                "fixes": ["Index the project", "Check vLLM health", "Increase max_tokens"]
            },
            "TRUNCATED": {
                "symptoms": ["Response cuts off", "finish_reason='length'"],
                "likely_layer": "LAYER4",
                "check_logs": ["logs/layer4_llm.log"],
                "fixes": ["Increase max_tokens to 2048+", "Reduce rag_top_k"]
            },
            "WRONG_ANSWER": {
                "symptoms": ["Wrong file paths", "Wrong class descriptions"],
                "likely_layer": "LAYER1 or LAYER2",
                "check_logs": ["logs/layer1_retrieval.log", "logs/layer2_context.log"],
                "fixes": ["Check WORKSPACE_ROOT", "Re-index with better parsing"]
            }
        },
        "quick_checks": [
            {"check": "Is project indexed?", "command": "curl http://localhost:8081/v1/index/list"},
            {"check": "Qdrant healthy?", "command": "curl http://localhost:6333/health"},
            {"check": "vLLM healthy?", "command": "curl http://localhost:8080/health"},
            {"check": "Recent failures?", "command": "curl http://localhost:8081/v1/diagnostics/failures"}
        ],
        "full_guide": "See rag-system/DEBUGGING_GUIDE.md for detailed debugging instructions"
    }


@app.get("/v1/diagnostics/sessions")
async def list_diagnostic_sessions(count: int = 10):
    """List recent debug sessions"""
    sessions = list_debug_sessions(count)
    return {
        "sessions": sessions,
        "count": len(sessions),
        "hint": "Use GET /v1/diagnostics/session/{session_id} to view full details"
    }


@app.get("/v1/diagnostics/session/latest")
async def get_latest_session():
    """Get the most recent debug session with FULL layer-by-layer content"""
    session = get_latest_debug_session()
    if not session:
        raise HTTPException(404, "No debug sessions found")
    return session


@app.get("/v1/diagnostics/session/{session_id}")
async def get_session_by_id(session_id: str):
    """Get a specific debug session with FULL layer-by-layer content"""
    session = get_debug_session(session_id)
    if not session:
        raise HTTPException(404, f"Session {session_id} not found")
    return session


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)


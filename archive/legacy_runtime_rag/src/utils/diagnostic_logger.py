#!/usr/bin/env python3
"""
Diagnostic Logger for RAG System Debugging

This module provides comprehensive logging for each layer of the RAG pipeline
to help identify where failures occur (hallucinations, wrong answers, empty responses, truncation).

Log Files:
- logs/layer1_retrieval.log    - RAG retrieval (Qdrant/Neo4j) logs
- logs/layer2_context.log      - Context injection logs
- logs/layer3_prompt.log       - System prompt construction logs
- logs/layer4_llm.log          - LLM generation logs
- logs/diagnostics.log         - Combined diagnostic summary
- logs/debug_sessions/         - Full content capture for debugging
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib

# Create logs directory
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Create debug sessions directory for full content capture
DEBUG_SESSIONS_DIR = LOGS_DIR / "debug_sessions"
DEBUG_SESSIONS_DIR.mkdir(exist_ok=True)


def setup_logger(name: str, log_file: str, level=logging.DEBUG) -> logging.Logger:
    """Create a logger with file and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler
    fh = logging.FileHandler(LOGS_DIR / log_file)
    fh.setLevel(level)
    
    # Format with timestamp
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger


# Layer-specific loggers
layer1_logger = setup_logger("layer1_retrieval", "layer1_retrieval.log")
layer2_logger = setup_logger("layer2_context", "layer2_context.log")
layer3_logger = setup_logger("layer3_prompt", "layer3_prompt.log")
layer4_logger = setup_logger("layer4_llm", "layer4_llm.log")
diag_logger = setup_logger("diagnostics", "diagnostics.log")


@dataclass
class DiagnosticSession:
    """Tracks a single request through all layers"""
    session_id: str
    timestamp: str
    user_query: str
    workspace_root: Optional[str] = None
    
    # Layer 1: Retrieval
    retrieval_source: Optional[str] = None  # "project" or "motadata"
    retrieval_count: int = 0
    retrieval_scores: List[float] = None
    retrieval_top_match: Optional[str] = None
    retrieval_error: Optional[str] = None
    
    # Layer 2: Context
    context_token_count: int = 0
    context_truncated: bool = False
    injected_files_count: int = 0
    rag_context_length: int = 0
    
    # Layer 3: Prompt
    system_prompt_length: int = 0
    total_messages_count: int = 0
    
    # Layer 4: LLM
    llm_response_length: int = 0
    llm_finish_reason: Optional[str] = None
    llm_response_time_ms: int = 0
    llm_error: Optional[str] = None
    
    # Diagnosis
    failure_type: Optional[str] = None  # HALLUCINATION, WRONG_ANSWER, NO_ANSWER, TRUNCATED
    failure_layer: Optional[str] = None  # LAYER1, LAYER2, LAYER3, LAYER4
    suggested_fix: Optional[str] = None


def generate_session_id(query: str) -> str:
    """Generate a unique session ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
    return f"{timestamp}_{query_hash}"


class DiagnosticLogger:
    """Main diagnostic logger for tracking requests through the RAG pipeline"""

    def __init__(self, user_query: str, workspace_root: Optional[str] = None):
        self.session = DiagnosticSession(
            session_id=generate_session_id(user_query),
            timestamp=datetime.now().isoformat(),
            user_query=user_query[:200],  # Truncate for logs
            workspace_root=workspace_root,
            retrieval_scores=[]
        )
        # Full debug content capture
        self.debug_data = {
            "session_id": self.session.session_id,
            "timestamp": self.session.timestamp,
            "query": user_query,  # Full query, not truncated
            "workspace_root": workspace_root,
            "layer1_retrieval": {},
            "layer2_context": {},
            "layer3_prompt": {},
            "layer4_llm": {}
        }
        diag_logger.info(f"[{self.session.session_id}] === NEW REQUEST ===")
        diag_logger.info(f"[{self.session.session_id}] Query: {user_query[:100]}...")
    
    # ========== LAYER 1: RETRIEVAL ==========
    def log_retrieval_start(self, source: str, workspace: Optional[str] = None):
        """Log when retrieval begins"""
        self.session.retrieval_source = source
        self.debug_data["layer1_retrieval"]["source"] = source
        self.debug_data["layer1_retrieval"]["workspace"] = workspace
        layer1_logger.info(f"[{self.session.session_id}] Retrieval started | Source: {source} | Workspace: {workspace}")

    def log_retrieval_results(self, results: List[Dict], scores: List[float] = None):
        """Log retrieval results with FULL content capture"""
        self.session.retrieval_count = len(results)
        self.session.retrieval_scores = scores or []

        # Capture full retrieval results for debugging
        self.debug_data["layer1_retrieval"]["result_count"] = len(results)
        self.debug_data["layer1_retrieval"]["scores"] = scores
        self.debug_data["layer1_retrieval"]["results"] = results  # Full results!

        if results:
            self.session.retrieval_top_match = results[0].get("qualified_name", "unknown")
            avg_score = sum(scores) / len(scores) if scores else 0
            layer1_logger.info(
                f"[{self.session.session_id}] Results: {len(results)} | "
                f"Top: {self.session.retrieval_top_match} | "
                f"Scores: {scores[:3] if scores else 'N/A'} | "
                f"Avg: {avg_score:.3f}"
            )
        else:
            layer1_logger.warning(f"[{self.session.session_id}] NO RESULTS RETRIEVED")

    def log_retrieval_error(self, error: str):
        """Log retrieval errors"""
        self.session.retrieval_error = error
        self.debug_data["layer1_retrieval"]["error"] = error
        layer1_logger.error(f"[{self.session.session_id}] Retrieval ERROR: {error}")
    
    # ========== LAYER 2: CONTEXT ==========
    def log_context_injection(self, injected_files: int, rag_context_len: int, total_tokens: int = 0,
                               rag_context_content: str = None, injected_files_content: List[Dict] = None):
        """Log context injection details with FULL content capture"""
        self.session.injected_files_count = injected_files
        self.session.rag_context_length = rag_context_len
        self.session.context_token_count = total_tokens

        # Capture full content for debugging
        self.debug_data["layer2_context"]["injected_files_count"] = injected_files
        self.debug_data["layer2_context"]["rag_context_chars"] = rag_context_len
        self.debug_data["layer2_context"]["estimated_tokens"] = total_tokens
        if rag_context_content:
            self.debug_data["layer2_context"]["rag_context_full"] = rag_context_content
        if injected_files_content:
            self.debug_data["layer2_context"]["injected_files"] = injected_files_content

        layer2_logger.info(
            f"[{self.session.session_id}] Context: "
            f"Injected files: {injected_files} | "
            f"RAG context chars: {rag_context_len} | "
            f"Est. tokens: {total_tokens}"
        )

    def log_context_truncation(self, original_len: int, truncated_len: int):
        """Log if context was truncated"""
        self.session.context_truncated = True
        self.debug_data["layer2_context"]["truncated"] = True
        self.debug_data["layer2_context"]["original_len"] = original_len
        self.debug_data["layer2_context"]["truncated_len"] = truncated_len
        layer2_logger.warning(
            f"[{self.session.session_id}] CONTEXT TRUNCATED: {original_len} -> {truncated_len} chars"
        )

    # ========== LAYER 3: PROMPT ==========
    def log_system_prompt(self, prompt_length: int, has_rag_context: bool, has_injected_files: bool,
                           system_prompt_content: str = None):
        """Log system prompt construction with FULL content capture"""
        self.session.system_prompt_length = prompt_length

        # Capture full content for debugging
        self.debug_data["layer3_prompt"]["length"] = prompt_length
        self.debug_data["layer3_prompt"]["has_rag_context"] = has_rag_context
        self.debug_data["layer3_prompt"]["has_injected_files"] = has_injected_files
        if system_prompt_content:
            self.debug_data["layer3_prompt"]["system_prompt_full"] = system_prompt_content

        layer3_logger.info(
            f"[{self.session.session_id}] System prompt: {prompt_length} chars | "
            f"Has RAG: {has_rag_context} | Has injected files: {has_injected_files}"
        )

    def log_messages(self, messages: List[Dict], total_count: int):
        """Log message history being sent with FULL content capture"""
        self.session.total_messages_count = total_count

        # Capture full messages for debugging
        self.debug_data["layer3_prompt"]["messages"] = messages
        self.debug_data["layer3_prompt"]["message_count"] = total_count

        roles = [m.get("role", "unknown") for m in messages]
        layer3_logger.info(
            f"[{self.session.session_id}] Messages: {total_count} | Roles: {roles}"
        )

    # ========== LAYER 4: LLM ==========
    def log_llm_request(self, model: str, temperature: float, max_tokens: int):
        """Log LLM request parameters"""
        self.debug_data["layer4_llm"]["request"] = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        layer4_logger.info(
            f"[{self.session.session_id}] LLM Request: model={model} | "
            f"temp={temperature} | max_tokens={max_tokens}"
        )

    def log_llm_response(self, response_content: str, finish_reason: str, response_time_ms: int):
        """Log LLM response with FULL content capture"""
        self.session.llm_response_length = len(response_content)
        self.session.llm_finish_reason = finish_reason
        self.session.llm_response_time_ms = response_time_ms

        # Capture full response for debugging
        self.debug_data["layer4_llm"]["response"] = {
            "content": response_content,  # Full response!
            "finish_reason": finish_reason,
            "response_time_ms": response_time_ms,
            "content_length": len(response_content)
        }

        # Detect potential issues
        issues = []
        if len(response_content) < 50:
            issues.append("MINIMAL_RESPONSE")
        if finish_reason == "length":
            issues.append("TRUNCATED")
        if not response_content.strip():
            issues.append("EMPTY_RESPONSE")
        
        layer4_logger.info(
            f"[{self.session.session_id}] LLM Response: {len(response_content)} chars | "
            f"finish: {finish_reason} | time: {response_time_ms}ms | "
            f"issues: {issues if issues else 'none'}"
        )
        
        # Log response preview
        preview = response_content[:200].replace('\n', ' ')
        layer4_logger.debug(f"[{self.session.session_id}] Preview: {preview}...")
    
    def log_llm_error(self, error: str):
        """Log LLM errors"""
        self.session.llm_error = error
        layer4_logger.error(f"[{self.session.session_id}] LLM ERROR: {error}")
    
    # ========== DIAGNOSIS ==========
    def diagnose(self) -> Dict[str, Any]:
        """Analyze the session and diagnose failures"""
        diagnosis = {
            "session_id": self.session.session_id,
            "failure_detected": False,
            "failure_type": None,
            "failure_layer": None,
            "suggested_fix": None,
            "details": {}
        }
        
        # Check Layer 1: Retrieval failures
        if self.session.retrieval_count == 0 and not self.session.retrieval_error:
            diagnosis["failure_detected"] = True
            diagnosis["failure_type"] = "NO_CONTEXT"
            diagnosis["failure_layer"] = "LAYER1_RETRIEVAL"
            diagnosis["suggested_fix"] = (
                "No documents retrieved. Check: "
                "1) Is project indexed? curl http://localhost:8081/v1/index/list | "
                "2) Re-index project | "
                "3) Check Qdrant health | "
                "4) Improve query keywords"
            )
            diagnosis["details"]["log_file"] = "logs/layer1_retrieval.log"
        
        elif self.session.retrieval_error:
            diagnosis["failure_detected"] = True
            diagnosis["failure_type"] = "RETRIEVAL_ERROR"
            diagnosis["failure_layer"] = "LAYER1_RETRIEVAL"
            diagnosis["suggested_fix"] = f"Retrieval failed: {self.session.retrieval_error}"
            diagnosis["details"]["log_file"] = "logs/layer1_retrieval.log"
        
        # Check Layer 2: Context issues
        elif self.session.context_truncated:
            diagnosis["failure_detected"] = True
            diagnosis["failure_type"] = "CONTEXT_TRUNCATED"
            diagnosis["failure_layer"] = "LAYER2_CONTEXT"
            diagnosis["suggested_fix"] = (
                "Context was truncated. Solutions: "
                "1) Reduce rag_top_k parameter | "
                "2) Increase max_tokens | "
                "3) Filter irrelevant results"
            )
            diagnosis["details"]["log_file"] = "logs/layer2_context.log"
        
        # Check Layer 4: LLM issues
        elif self.session.llm_response_length < 50:
            diagnosis["failure_detected"] = True
            diagnosis["failure_type"] = "MINIMAL_RESPONSE"
            diagnosis["failure_layer"] = "LAYER4_LLM"
            diagnosis["suggested_fix"] = (
                "LLM returned minimal response. Check: "
                "1) System prompt instructions | "
                "2) Increase max_tokens | "
                "3) Check if context is relevant | "
                "4) Review fine-tuning data"
            )
            diagnosis["details"]["log_file"] = "logs/layer4_llm.log"
        
        elif self.session.llm_finish_reason == "length":
            diagnosis["failure_detected"] = True
            diagnosis["failure_type"] = "TRUNCATED_OUTPUT"
            diagnosis["failure_layer"] = "LAYER4_LLM"
            diagnosis["suggested_fix"] = (
                "LLM output was truncated. Solutions: "
                "1) Increase max_tokens in request | "
                "2) Ask for more concise response"
            )
            diagnosis["details"]["log_file"] = "logs/layer4_llm.log"
        
        elif self.session.llm_error:
            diagnosis["failure_detected"] = True
            diagnosis["failure_type"] = "LLM_ERROR"
            diagnosis["failure_layer"] = "LAYER4_LLM"
            diagnosis["suggested_fix"] = f"LLM error: {self.session.llm_error}"
            diagnosis["details"]["log_file"] = "logs/layer4_llm.log"
        
        # Low confidence retrieval (potential hallucination risk)
        elif self.session.retrieval_scores and max(self.session.retrieval_scores) < 0.3:
            diagnosis["failure_detected"] = True
            diagnosis["failure_type"] = "LOW_CONFIDENCE_RETRIEVAL"
            diagnosis["failure_layer"] = "LAYER1_RETRIEVAL"
            diagnosis["suggested_fix"] = (
                "Retrieved results have low confidence scores. "
                "Risk of hallucination. Check: "
                "1) Query relevance | "
                "2) Indexing quality | "
                "3) Consider re-indexing"
            )
            diagnosis["details"]["log_file"] = "logs/layer1_retrieval.log"
        
        # Store diagnosis
        self.session.failure_type = diagnosis["failure_type"]
        self.session.failure_layer = diagnosis["failure_layer"]
        self.session.suggested_fix = diagnosis["suggested_fix"]
        
        # Log to diagnostics
        if diagnosis["failure_detected"]:
            diag_logger.warning(
                f"[{self.session.session_id}] FAILURE DETECTED: "
                f"{diagnosis['failure_type']} at {diagnosis['failure_layer']}"
            )
            diag_logger.warning(f"[{self.session.session_id}] FIX: {diagnosis['suggested_fix']}")
        else:
            diag_logger.info(f"[{self.session.session_id}] Request completed successfully")
        
        return diagnosis

    def get_session_summary(self) -> Dict[str, Any]:
        """Get complete session summary"""
        return asdict(self.session)

    def save_debug_session(self) -> str:
        """Save full debug session to file for inspection"""
        session_file = DEBUG_SESSIONS_DIR / f"{self.session.session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(self.debug_data, f, indent=2, default=str)
        return str(session_file)


# ========== UTILITY FUNCTIONS ==========
def get_latest_debug_session() -> Optional[Dict]:
    """Get the most recent debug session with full content"""
    session_files = sorted(DEBUG_SESSIONS_DIR.glob("*.json"), reverse=True)
    if not session_files:
        return None

    with open(session_files[0], 'r') as f:
        return json.load(f)


def get_debug_session(session_id: str) -> Optional[Dict]:
    """Get a specific debug session by ID"""
    session_file = DEBUG_SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        return None

    with open(session_file, 'r') as f:
        return json.load(f)


def list_debug_sessions(count: int = 10) -> List[str]:
    """List recent debug session IDs"""
    session_files = sorted(DEBUG_SESSIONS_DIR.glob("*.json"), reverse=True)[:count]
    return [f.stem for f in session_files]
def get_recent_failures(count: int = 10) -> List[Dict]:
    """Read recent failures from diagnostics log"""
    failures = []
    log_file = LOGS_DIR / "diagnostics.log"
    
    if not log_file.exists():
        return failures
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    # Find FAILURE lines
    for line in reversed(lines):
        if "FAILURE DETECTED" in line:
            failures.append({"log": line.strip()})
            if len(failures) >= count:
                break
    
    return failures


def get_layer_stats() -> Dict[str, int]:
    """Get count of issues per layer from logs"""
    stats = {
        "layer1_errors": 0,
        "layer2_truncations": 0,
        "layer4_minimal": 0,
        "layer4_errors": 0
    }
    
    # Count Layer 1 errors
    l1_log = LOGS_DIR / "layer1_retrieval.log"
    if l1_log.exists():
        with open(l1_log, 'r') as f:
            stats["layer1_errors"] = sum(1 for line in f if "ERROR" in line or "NO RESULTS" in line)
    
    # Count Layer 2 truncations
    l2_log = LOGS_DIR / "layer2_context.log"
    if l2_log.exists():
        with open(l2_log, 'r') as f:
            stats["layer2_truncations"] = sum(1 for line in f if "TRUNCATED" in line)
    
    # Count Layer 4 issues
    l4_log = LOGS_DIR / "layer4_llm.log"
    if l4_log.exists():
        with open(l4_log, 'r') as f:
            content = f.read()
            stats["layer4_minimal"] = content.count("MINIMAL_RESPONSE")
            stats["layer4_errors"] = content.count("ERROR")
    
    return stats


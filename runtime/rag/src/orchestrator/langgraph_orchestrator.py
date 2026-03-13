"""
LangGraph Orchestrator - State Machine for Agentic Code Generation

This module defines the state machine that orchestrates the flow of:
1. Request Analysis (PRE)
2. Context Retrieval (PRE)
3. Code Generation (CORE)
4. Format Validation (POST)
5. Error Handling (POST)
6. Code Evaluation (POST)
"""

from typing import TypedDict, Annotated, Sequence
from enum import Enum
import json
import logging

from langgraph.graph import StateGraph, END
from langgraph.types import Command

# Import real agent implementations
from .agents.request_analyzer import RequestAnalyzerAgent
from .agents.retrieval_agent import RetrievalAgent
from .agents.coder_agent import CoderAgent
from .agents.format_validator import FormatValidatorAgent
from .agents.error_handler import ErrorHandlerAgent
from .agents.code_evaluator import CodeEvaluatorAgent

logger = logging.getLogger(__name__)


# ============================================================================
# STATE DEFINITIONS
# ============================================================================

class AgentPhase(str, Enum):
    """Phases in the agentic pipeline"""
    PRE = "pre"
    CORE = "core"
    POST = "post"


class AgentState(TypedDict):
    """
    Complete state object passed through the state machine.
    
    This is the "memory" of the orchestrator - all agents read from and write to this.
    """
    
    # Input
    user_request: str
    conversation_history: list[str]
    codebase_context: dict
    
    # PRE Phase Results
    request_analysis: dict  # Output from Request Analyzer
    retrieval_results: dict  # Output from Retrieval Agent
    
    # CORE Phase Results
    generated_code: str  # Raw output from Coder Agent
    generation_attempt: int  # Track retry count
    
    # POST Phase Results
    format_validation: dict  # Output from Format Validator
    error_handling: dict  # Output from Error Handler
    code_evaluation: dict  # Output from Code Evaluator
    
    # Metadata
    phase: AgentPhase
    status: str  # PROCESSING, SUCCESS, FAILED, RETRY
    error_message: str
    final_output: dict


# ============================================================================
# NODE FUNCTIONS (State Machine Nodes)
# ============================================================================

async def node_request_received(state: AgentState) -> Command:
    """Entry point: Request received from user"""
    logger.info(f"Request received: {state['user_request'][:100]}...")
    return Command(goto="analyze_request")


async def node_analyze_request(state: AgentState) -> AgentState:
    """PRE Phase: Analyze and validate user request"""
    agent = RequestAnalyzerAgent()
    result = await agent.run(state)
    
    state["request_analysis"] = result
    state["phase"] = AgentPhase.PRE
    
    if result["status"] == "VALID":
        state["status"] = "PROCESSING"
        return state
    elif result["status"] == "NEEDS_CLARIFICATION":
        state["status"] = "FAILED"
        state["error_message"] = "Request needs clarification"
        return state
    else:
        state["status"] = "FAILED"
        state["error_message"] = "Invalid request"
        return state


async def node_retrieve_context(state: AgentState) -> AgentState:
    """PRE Phase: Retrieve relevant patterns and examples"""
    agent = RetrievalAgent()
    result = await agent.run(state)
    
    state["retrieval_results"] = result
    state["status"] = "PROCESSING"
    return state


async def node_generate_code(state: AgentState) -> AgentState:
    """CORE Phase: Generate code using vLLM"""
    state["generation_attempt"] = state.get("generation_attempt", 0) + 1
    
    agent = CoderAgent()
    result = await agent.run(state)
    
    state["generated_code"] = result["generated_code"]
    state["phase"] = AgentPhase.CORE
    state["status"] = "PROCESSING"
    return state


async def node_validate_format(state: AgentState) -> AgentState:
    """POST Phase: Validate search/replace block format"""
    agent = FormatValidatorAgent()
    result = await agent.run(state)
    
    state["format_validation"] = result
    state["phase"] = AgentPhase.POST
    
    if result["status"] == "VALID":
        state["status"] = "PROCESSING"
    else:
        state["status"] = "RETRY"
    
    return state


async def node_handle_errors(state: AgentState) -> AgentState:
    """POST Phase: Detect and fix errors"""
    agent = ErrorHandlerAgent()
    result = await agent.run(state)
    
    state["error_handling"] = result
    
    if result["status"] == "NO_ERRORS":
        state["status"] = "PROCESSING"
    else:
        state["status"] = "PROCESSING"  # Errors were fixed
    
    return state


async def node_evaluate_code(state: AgentState) -> AgentState:
    """POST Phase: Evaluate code quality"""
    agent = CodeEvaluatorAgent()
    result = await agent.run(state)
    
    state["code_evaluation"] = result
    
    if result["status"] == "PASS":
        state["status"] = "SUCCESS"
    else:
        state["status"] = "WARN"  # Warning but still return
    
    return state


async def node_retry_generation(state: AgentState) -> Command:
    """Decision: Should we retry code generation?"""
    max_retries = 3
    
    if state["generation_attempt"] < max_retries:
        logger.warning(f"Format validation failed. Retrying... (Attempt {state['generation_attempt'] + 1}/{max_retries})")
        return Command(goto="generate_code")
    else:
        logger.error(f"Max retries ({max_retries}) reached. Returning error.")
        state["status"] = "FAILED"
        state["error_message"] = "Code generation failed after max retries"
        return Command(goto="return_error")


async def node_return_success(state: AgentState) -> AgentState:
    """Success: Combine results and return to user"""
    logger.info("Code generation successful!")
    
    state["final_output"] = {
        "status": "SUCCESS",
        "generated_code": state["generated_code"],
        "explanation": state["request_analysis"].get("extracted_requirements", {}),
        "quality_score": state["code_evaluation"].get("quality_score", 0),
        "evaluation": state["code_evaluation"]
    }
    
    return state


async def node_return_error(state: AgentState) -> AgentState:
    """Error: Return error to user"""
    logger.error(f"Request failed: {state['error_message']}")
    
    state["final_output"] = {
        "status": "FAILED",
        "error": state["error_message"],
        "phase": state["phase"].value
    }
    
    return state


# ============================================================================
# CONDITIONAL EDGES (Decision Points)
# ============================================================================

def should_retry_generation(state: AgentState) -> str:
    """Decide: Retry generation or proceed to evaluation?"""
    if state["status"] == "RETRY":
        return "retry_generation"
    return "handle_errors"


def should_return_success(state: AgentState) -> str:
    """Decide: Return success or error?"""
    if state["status"] == "SUCCESS":
        return "return_success"
    elif state["status"] == "FAILED":
        return "return_error"
    return "return_success"  # Default to success


# ============================================================================
# STATE MACHINE CONSTRUCTION
# ============================================================================

def build_orchestrator_graph() -> StateGraph:
    """
    Constructs the LangGraph state machine.
    
    Flow:
    REQUEST → ANALYZE → RETRIEVE → GENERATE → VALIDATE → RETRY? → HANDLE_ERRORS → EVALUATE → RETURN
    """
    
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("request_received", node_request_received)
    graph.add_node("analyze_request", node_analyze_request)
    graph.add_node("retrieve_context", node_retrieve_context)
    graph.add_node("generate_code", node_generate_code)
    graph.add_node("validate_format", node_validate_format)
    graph.add_node("retry_generation", node_retry_generation)
    graph.add_node("handle_errors", node_handle_errors)
    graph.add_node("evaluate_code", node_evaluate_code)
    graph.add_node("return_success", node_return_success)
    graph.add_node("return_error", node_return_error)
    
    # Add edges
    graph.add_edge("request_received", "analyze_request")
    graph.add_edge("analyze_request", "retrieve_context")
    graph.add_edge("retrieve_context", "generate_code")
    graph.add_edge("generate_code", "validate_format")
    
    # Conditional edge: Retry or proceed?
    graph.add_conditional_edges(
        "validate_format",
        should_retry_generation,
        {
            "retry_generation": "retry_generation",
            "handle_errors": "handle_errors"
        }
    )
    
    graph.add_edge("retry_generation", "generate_code")
    graph.add_edge("handle_errors", "evaluate_code")
    
    # Conditional edge: Success or error?
    graph.add_conditional_edges(
        "evaluate_code",
        should_return_success,
        {
            "return_success": "return_success",
            "return_error": "return_error"
        }
    )
    
    graph.add_edge("return_success", END)
    graph.add_edge("return_error", END)
    
    # Set entry point
    graph.set_entry_point("request_received")
    
    return graph


# ============================================================================
# ORCHESTRATOR CLASS
# ============================================================================

class Orchestrator:
    """Main orchestrator that runs the state machine"""
    
    def __init__(self):
        self.graph = build_orchestrator_graph().compile()
        logger.info("Orchestrator initialized with LangGraph state machine")
    
    async def process_request(self, user_request: str, conversation_history: list = None, codebase_context: dict = None) -> dict:
        """
        Process a user request through the agentic pipeline.
        
        Args:
            user_request: The user's code generation request
            conversation_history: Previous messages in conversation
            codebase_context: Context about the codebase
        
        Returns:
            Final output with generated code or error
        """
        
        initial_state: AgentState = {
            "user_request": user_request,
            "conversation_history": conversation_history or [],
            "codebase_context": codebase_context or {},
            "request_analysis": {},
            "retrieval_results": {},
            "generated_code": "",
            "generation_attempt": 0,
            "format_validation": {},
            "error_handling": {},
            "code_evaluation": {},
            "phase": AgentPhase.PRE,
            "status": "PROCESSING",
            "error_message": "",
            "final_output": {}
        }
        
        logger.info(f"Processing request: {user_request[:100]}...")
        
        # Run the state machine
        final_state = await self.graph.ainvoke(initial_state)
        
        return final_state["final_output"]


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def main():
        orchestrator = Orchestrator()
        
        result = await orchestrator.process_request(
            user_request="Create a new UserAPI endpoint in Motadata",
            conversation_history=[],
            codebase_context={
                "primary_language": "Java",
                "frameworks": ["Vert.x"],
                "architectural_style": "Event-Driven"
            }
        )
        
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())


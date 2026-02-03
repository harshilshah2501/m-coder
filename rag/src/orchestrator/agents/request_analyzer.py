"""
Request Analyzer Agent (PRE Phase)

Analyzes user request and extracts:
- Programming language
- Frameworks/libraries
- Architecture pattern
- Functional requirements
- Non-functional requirements
- Organizational constraints
"""

import json
import logging
import time
import asyncio
from typing import Optional, Dict, Any
from functools import lru_cache
import httpx

logger = logging.getLogger(__name__)


class RequestAnalyzerAgent:
    """
    PRE Phase Agent: Analyzes and validates user requests

    Uses vLLM to understand user intent and extract structured requirements.
    Features:
    - Structured requirement extraction
    - Validation against Motadata stack
    - Confidence scoring
    - Comprehensive error handling
    - Performance metrics
    """

    # Approved frameworks for Motadata
    APPROVED_FRAMEWORKS = {
        "vert.x", "vertx", "jackson", "junit", "mockito",
        "spring", "spring-boot", "hibernate", "jpa",
        "kafka", "rabbitmq", "redis", "postgresql", "mysql"
    }

    def __init__(self, vllm_url: str = "http://localhost:8000", timeout: float = 30.0):
        self.vllm_url = vllm_url
        self.model = "motadata-coder"
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.metrics = {
            "total_requests": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "total_latency": 0.0
        }
    
    async def run(self, state: dict) -> dict:
        """
        Analyze user request and extract requirements.

        Args:
            state: AgentState containing user_request, conversation_history, codebase_context

        Returns:
            Dictionary with:
            - status: VALID | INVALID | NEEDS_CLARIFICATION | FAILED
            - extracted_requirements: Structured requirements
            - clarification_questions: If status is NEEDS_CLARIFICATION
            - confidence_score: 0.0-1.0
            - latency_ms: Processing time
        """

        start_time = time.time()
        self.metrics["total_requests"] += 1

        user_request = state.get("user_request", "")
        conversation_history = state.get("conversation_history", [])
        codebase_context = state.get("codebase_context", {})

        logger.info(f"Analyzing request: {user_request[:100]}...")

        # Validate input
        if not user_request or not isinstance(user_request, str):
            logger.error("Invalid user_request: must be non-empty string")
            return {
                "status": "FAILED",
                "error": "Invalid user_request",
                "extracted_requirements": {},
                "latency_ms": (time.time() - start_time) * 1000
            }

        # Build prompt
        prompt = self._build_prompt(user_request, conversation_history, codebase_context)

        try:
            # Call vLLM with retry logic
            response = await self._call_vllm_with_retry(prompt, max_retries=2)

            # Parse response
            result = self._parse_response(response)

            # Post-process validation
            result = self._validate_requirements(result)

            # Add metrics
            latency_ms = (time.time() - start_time) * 1000
            result["latency_ms"] = latency_ms
            self.metrics["total_latency"] += latency_ms

            if result["status"] == "VALID":
                self.metrics["successful_analyses"] += 1
            else:
                self.metrics["failed_analyses"] += 1

            logger.info(f"Request analysis complete. Status: {result['status']}, Latency: {latency_ms:.2f}ms")
            return result

        except httpx.TimeoutException:
            logger.error("vLLM request timeout")
            self.metrics["failed_analyses"] += 1
            return {
                "status": "FAILED",
                "error": "vLLM service timeout",
                "extracted_requirements": {},
                "latency_ms": (time.time() - start_time) * 1000
            }
        except Exception as e:
            logger.error(f"Error in Request Analyzer: {e}", exc_info=True)
            self.metrics["failed_analyses"] += 1
            return {
                "status": "FAILED",
                "error": str(e),
                "extracted_requirements": {},
                "latency_ms": (time.time() - start_time) * 1000
            }
    
    def _build_prompt(self, user_request: str, history: list, context: dict) -> str:
        """Build the prompt for Request Analyzer"""
        
        history_text = "\n".join(history[-3:]) if history else "No previous context"
        
        prompt = f"""You are a Request Analyzer for a code-generation system targeting the Motadata platform.

CODEBASE CONTEXT:
- Primary Language: {context.get('primary_language', 'Java')}
- Frameworks: {', '.join(context.get('frameworks', ['Vert.x']))}
- Architectural Style: {context.get('architectural_style', 'Event-Driven')}

CONVERSATION HISTORY:
{history_text}

USER REQUEST:
{user_request}

TASK:
Analyze the user request and extract:
1. Programming language(s) - Infer from context if not explicit
2. Frameworks/libraries - Must align with Motadata stack
3. Architecture or design pattern
4. Functional requirements - What the code should do
5. Non-functional requirements - Performance, security, scalability
6. Organizational or style constraints

VALIDATION RULES:
- If language is not Java, flag as NEEDS_CLARIFICATION
- If frameworks are not in approved list, flag as INVALID
- If requirements are contradictory, flag as NEEDS_CLARIFICATION
- If request is vague, ask clarification questions

OUTPUT:
Return ONLY valid JSON (no markdown):
{{
  "status": "VALID|INVALID|NEEDS_CLARIFICATION",
  "extracted_requirements": {{
    "programming_language": "string",
    "frameworks": ["string"],
    "architecture_pattern": "string",
    "functional_requirements": ["string"],
    "non_functional_requirements": {{"performance": "string", "security": "string"}},
    "organizational_constraints": ["string"]
  }},
  "clarification_questions": ["string"],
  "confidence_score": 0.0-1.0
}}"""
        
        return prompt
    
    async def _call_vllm_with_retry(self, prompt: str, max_retries: int = 2) -> str:
        """Call vLLM API with retry logic"""

        last_error = None
        for attempt in range(max_retries):
            try:
                return await self._call_vllm(prompt)
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"vLLM call failed (attempt {attempt + 1}), retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise

        raise last_error

    async def _call_vllm(self, prompt: str) -> str:
        """Call vLLM API"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1000,
            "top_p": 0.9
        }

        response = await self.client.post(
            f"{self.vllm_url}/v1/chat/completions",
            json=payload
        )

        response.raise_for_status()
        result = response.json()

        return result["choices"][0]["message"]["content"]
    
    def _parse_response(self, response: str) -> dict:
        """Parse vLLM response"""

        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")

            json_str = response[json_start:json_end]
            result = json.loads(json_str)

            # Validate required fields
            if "status" not in result:
                result["status"] = "VALID"
            if "confidence_score" not in result:
                result["confidence_score"] = 0.8
            if "extracted_requirements" not in result:
                result["extracted_requirements"] = {}

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {
                "status": "FAILED",
                "error": f"Invalid JSON response: {e}",
                "extracted_requirements": {}
            }

    def _validate_requirements(self, result: dict) -> dict:
        """Validate extracted requirements against Motadata stack"""

        if result["status"] == "FAILED":
            return result

        requirements = result.get("extracted_requirements", {})

        # Check programming language
        lang = requirements.get("programming_language", "").lower()
        if lang and lang != "java":
            result["status"] = "NEEDS_CLARIFICATION"
            if "clarification_questions" not in result:
                result["clarification_questions"] = []
            result["clarification_questions"].append(
                f"You specified {lang}, but Motadata uses Java. Should we proceed with Java?"
            )
            result["confidence_score"] = max(0.0, result.get("confidence_score", 0.8) - 0.2)

        # Check frameworks
        frameworks = requirements.get("frameworks", [])
        if frameworks:
            invalid_frameworks = [
                f for f in frameworks
                if f.lower() not in self.APPROVED_FRAMEWORKS
            ]
            if invalid_frameworks:
                result["status"] = "INVALID"
                result["error"] = f"Unsupported frameworks: {', '.join(invalid_frameworks)}"
                result["confidence_score"] = 0.0

        return result

    def get_metrics(self) -> dict:
        """Get performance metrics"""
        avg_latency = (
            self.metrics["total_latency"] / self.metrics["total_requests"]
            if self.metrics["total_requests"] > 0 else 0.0
        )

        return {
            "total_requests": self.metrics["total_requests"],
            "successful_analyses": self.metrics["successful_analyses"],
            "failed_analyses": self.metrics["failed_analyses"],
            "success_rate": (
                self.metrics["successful_analyses"] / self.metrics["total_requests"]
                if self.metrics["total_requests"] > 0 else 0.0
            ),
            "avg_latency_ms": avg_latency
        }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


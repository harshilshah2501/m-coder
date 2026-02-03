"""
Coder Agent (CORE Phase)

Generates code using vLLM (Fine-tuned Model)
"""

import os
import json
import logging
import httpx

logger = logging.getLogger(__name__)


class CoderAgent:
    """
    CORE Phase Agent: Generates code using vLLM

    Focuses on ONE file at a time with specific instructions from Planner
    and context from Retrieval Agent.
    """

    def __init__(self, vllm_url: str = "http://localhost:8000"):
        self.vllm_url = vllm_url
        # Version-agnostic model name from environment or default
        self.model = os.getenv("VLLM_MODEL_NAME", "motadata-coder")
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def run(self, state: dict) -> dict:
        """
        Generate code for a specific file.
        
        Args:
            state: AgentState with requirements, context, and previous attempts
        
        Returns:
            Dictionary with:
            - status: SUCCESS | FAILED
            - generated_code: The generated code
            - confidence_score: 0.0-1.0
            - attempt_number: Which attempt this is
        """
        
        file_path = state.get("file_path", "")
        file_type = state.get("file_type", "NEW")
        requirements = state.get("requirements", {})
        context = state.get("context", {})
        attempt = state.get("generation_attempt", 1)
        previous_attempts = state.get("previous_attempts", [])
        
        logger.info(f"Generating code for {file_path} (Attempt {attempt})")
        
        try:
            # Build prompt
            prompt = self._build_prompt(
                file_path, file_type, requirements, context, 
                previous_attempts, attempt
            )
            
            # Call vLLM
            generated_code = await self._call_vllm(prompt)
            
            logger.info(f"Code generation complete for {file_path}")
            
            return {
                "status": "SUCCESS",
                "generated_code": generated_code,
                "confidence_score": 0.85,
                "attempt_number": attempt
            }
            
        except Exception as e:
            logger.error(f"Error in Coder Agent: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "generated_code": "",
                "confidence_score": 0.0,
                "attempt_number": attempt
            }
    
    def _build_prompt(self, file_path: str, file_type: str, requirements: dict,
                     context: dict, previous_attempts: list, attempt: int) -> str:
        """Build the code generation prompt"""
        
        patterns_text = "\n".join([
            f"- {p.get('pattern_name', 'Unknown')}: {p.get('snippet', '')[:200]}"
            for p in context.get("retrieved_patterns", [])[:3]
        ])
        
        examples_text = "\n".join([
            f"- {e.get('example_name', 'Unknown')}: {e.get('code_snippet', '')[:200]}"
            for e in context.get("retrieved_examples", [])[:3]
        ])
        
        previous_context = ""
        if previous_attempts and attempt > 1:
            last_attempt = previous_attempts[-1]
            previous_context = f"""
PREVIOUS ATTEMPT #{attempt-1} FAILED:
Error: {last_attempt.get('error', 'Unknown')}

Please fix this issue in your new attempt."""
        
        prompt = f"""You are a Code Generator for the Motadata platform (Java/Vert.x).

FILE: {file_path}
ACTION: {file_type}

FUNCTIONAL REQUIREMENTS:
{json.dumps(requirements.get('functional', []), indent=2)}

NON-FUNCTIONAL REQUIREMENTS:
{json.dumps(requirements.get('non_functional', []), indent=2)}

RELEVANT PATTERNS:
{patterns_text or "No patterns found"}

EXAMPLE IMPLEMENTATIONS:
{examples_text or "No examples found"}

ARCHITECTURAL GUIDELINES:
{context.get('architectural_guidelines', 'Follow Motadata patterns')}

{previous_context}

TASK:
Generate code for {file_path} that:
1. Satisfies all functional requirements
2. Follows Motadata architectural patterns
3. Adheres to Java naming conventions
4. Includes proper error handling and logging

OUTPUT FORMAT:
For modifications, use Search/Replace blocks:

<<<< SEARCH
[existing code to find]
>>>>

>>>> REPLACE
[new code to insert]
>>>>

For new files, provide complete code with imports.

CRITICAL RULES:
- Always close SEARCH and REPLACE blocks with >>>>
- Maintain consistent indentation (4 spaces)
- Include all necessary imports
- Add comments for complex logic
- Follow camelCase for methods, PascalCase for classes

Return ONLY the code. No explanations outside blocks."""
        
        return prompt
    
    async def _call_vllm(self, prompt: str) -> str:
        """Call vLLM API for code generation"""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 2000,
            "top_p": 0.95
        }
        
        response = await self.client.post(
            f"{self.vllm_url}/v1/chat/completions",
            json=payload,
            timeout=60.0
        )
        
        response.raise_for_status()
        result = response.json()
        
        return result["choices"][0]["message"]["content"]
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


"""
Code Evaluator Agent (POST Phase)

Evaluates code quality and adherence to best practices
"""

import json
import logging
import httpx

logger = logging.getLogger(__name__)


class CodeEvaluatorAgent:
    """
    POST Phase Agent: Evaluates code quality
    
    Uses vLLM to assess readability, maintainability, performance,
    security, and architectural alignment.
    """
    
    def __init__(self, vllm_url: str = "http://localhost:8000"):
        self.vllm_url = vllm_url
        self.model = "motadata-coder"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def run(self, state: dict) -> dict:
        """
        Evaluate code quality.
        
        Args:
            state: AgentState with generated_code and requirements
        
        Returns:
            Dictionary with:
            - status: PASS | WARN | FAIL
            - quality_score: 0.0-1.0
            - evaluations: Detailed scores for each dimension
            - recommendations: Improvement suggestions
        """
        
        generated_code = state.get("generated_code", "")
        file_path = state.get("file_path", "")
        requirements = state.get("requirements", {})
        org_standards = state.get("organizational_standards", "")
        
        logger.info(f"Evaluating code quality for {file_path}")
        
        try:
            # Call LLM for evaluation
            evaluation = await self._evaluate_code(
                generated_code, file_path, requirements, org_standards
            )
            
            # Calculate overall quality score
            scores = [
                evaluation.get("evaluations", {}).get(dim, {}).get("score", 0.5)
                for dim in ["readability", "maintainability", "performance", "security", "architectural_alignment"]
            ]
            quality_score = sum(scores) / len(scores) if scores else 0.5
            
            # Determine status
            if quality_score >= 0.8:
                status = "PASS"
            elif quality_score >= 0.6:
                status = "WARN"
            else:
                status = "FAIL"
            
            logger.info(f"Code evaluation complete. Score: {quality_score:.2f}, Status: {status}")
            
            return {
                "status": status,
                "quality_score": quality_score,
                "evaluations": evaluation.get("evaluations", {}),
                "recommendations": evaluation.get("recommendations", [])
            }
            
        except Exception as e:
            logger.error(f"Error in Code Evaluator: {e}")
            return {
                "status": "WARN",
                "quality_score": 0.5,
                "error": str(e),
                "evaluations": {},
                "recommendations": []
            }
    
    async def _evaluate_code(self, code: str, file_path: str, 
                            requirements: dict, org_standards: str) -> dict:
        """Use LLM to evaluate code"""
        
        prompt = f"""You are a Code Evaluator for the Motadata platform.

FILE: {file_path}

CODE:
{code}

REQUIREMENTS:
{json.dumps(requirements, indent=2)}

ORGANIZATIONAL STANDARDS:
{org_standards or "Follow Motadata patterns"}

TASK:
Evaluate the code on these dimensions:
1. Readability - Is it easy to understand?
2. Maintainability - Can others modify it easily?
3. Performance - Are there obvious inefficiencies?
4. Security - Are there security risks?
5. Architectural Alignment - Does it follow Motadata patterns?

For each dimension, provide:
- Score (0.0-1.0)
- Specific issues (list)
- Improvement suggestions (list)

OUTPUT:
Return ONLY valid JSON (no markdown):
{{
  "evaluations": {{
    "readability": {{"score": 0.0-1.0, "issues": ["string"], "suggestions": ["string"]}},
    "maintainability": {{"score": 0.0-1.0, "issues": ["string"], "suggestions": ["string"]}},
    "performance": {{"score": 0.0-1.0, "issues": ["string"], "suggestions": ["string"]}},
    "security": {{"score": 0.0-1.0, "issues": ["string"], "suggestions": ["string"]}},
    "architectural_alignment": {{"score": 0.0-1.0, "issues": ["string"], "suggestions": ["string"]}}
  }},
  "recommendations": ["string"]
}}"""
        
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1500
            }
            
            response = await self.client.post(
                f"{self.vllm_url}/v1/chat/completions",
                json=payload
            )
            
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            
            # Parse JSON response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            evaluation = json.loads(content[json_start:json_end])
            
            return evaluation
            
        except Exception as e:
            logger.warning(f"LLM evaluation failed: {e}")
            # Return default evaluation
            return {
                "evaluations": {
                    "readability": {"score": 0.7, "issues": [], "suggestions": []},
                    "maintainability": {"score": 0.7, "issues": [], "suggestions": []},
                    "performance": {"score": 0.7, "issues": [], "suggestions": []},
                    "security": {"score": 0.7, "issues": [], "suggestions": []},
                    "architectural_alignment": {"score": 0.7, "issues": [], "suggestions": []}
                },
                "recommendations": []
            }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


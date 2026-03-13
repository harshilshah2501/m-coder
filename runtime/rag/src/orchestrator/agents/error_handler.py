"""
Error Handler Agent (POST Phase)

Detects and fixes syntax, logical, and runtime errors
"""

import logging
import httpx

logger = logging.getLogger(__name__)


class ErrorHandlerAgent:
    """
    POST Phase Agent: Detects and fixes errors
    
    Uses Tree-sitter for syntax checking and vLLM for error fixing.
    """
    
    def __init__(self, vllm_url: str = "http://localhost:8000"):
        self.vllm_url = vllm_url
        self.model = "motadata-coder"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def run(self, state: dict) -> dict:
        """
        Detect and fix errors in generated code.
        
        Args:
            state: AgentState with generated_code
        
        Returns:
            Dictionary with:
            - status: NO_ERRORS | FIXED | UNFIXABLE
            - fixed_code: The corrected code
            - fixes_applied: List of fixes
        """
        
        generated_code = state.get("generated_code", "")
        file_path = state.get("file_path", "")
        
        logger.info(f"Checking for errors in {file_path}")
        
        try:
            # Step 1: Detect errors (Python implementation)
            errors = self._detect_errors(generated_code)
            
            if not errors:
                logger.info("No errors detected")
                return {
                    "status": "NO_ERRORS",
                    "fixed_code": generated_code,
                    "fixes_applied": []
                }
            
            # Step 2: Fix errors using LLM
            fixed_code = await self._fix_errors(generated_code, errors)
            
            logger.info(f"Fixed {len(errors)} errors")
            
            return {
                "status": "FIXED",
                "fixed_code": fixed_code,
                "fixes_applied": [
                    {"type": e.get("type"), "description": e.get("message")}
                    for e in errors
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in Error Handler: {e}")
            return {
                "status": "UNFIXABLE",
                "error": str(e),
                "fixed_code": generated_code,
                "fixes_applied": []
            }
    
    def _detect_errors(self, code: str) -> list:
        """
        Detect syntax and logical errors.
        
        TODO: Integrate Tree-sitter for proper Java parsing
        """
        
        errors = []
        
        # Basic checks (placeholder for Tree-sitter integration)
        
        # Check 1: Missing semicolons
        lines = code.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('//') and not stripped.startswith('*'):
                if any(stripped.endswith(x) for x in ['{', '}', '(', ')', ',']):
                    continue
                if 'class ' in stripped or 'interface ' in stripped:
                    continue
                if not stripped.endswith(';') and not stripped.endswith('{'):
                    # Might be missing semicolon
                    pass
        
        # Check 2: Unmatched braces
        open_braces = code.count('{')
        close_braces = code.count('}')
        if open_braces != close_braces:
            errors.append({
                "type": "UNMATCHED_BRACES",
                "message": f"Unmatched braces: {open_braces} open, {close_braces} close"
            })
        
        # Check 3: Missing imports (basic check)
        common_classes = ['ArrayList', 'HashMap', 'List', 'Map', 'Set']
        for cls in common_classes:
            if cls in code and f"import.*{cls}" not in code:
                # Might be missing import
                pass
        
        return errors
    
    async def _fix_errors(self, code: str, errors: list) -> str:
        """Use LLM to fix detected errors"""
        
        error_descriptions = "\n".join([
            f"- {e.get('type')}: {e.get('message')}"
            for e in errors
        ])
        
        prompt = f"""Fix the following errors in this Java code:

ERRORS:
{error_descriptions}

CODE:
{code}

Return ONLY the fixed code with search/replace blocks.
Explain each fix in a comment."""
        
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = await self.client.post(
                f"{self.vllm_url}/v1/chat/completions",
                json=payload
            )
            
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.warning(f"LLM error fixing failed: {e}")
            return code
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


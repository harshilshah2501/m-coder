"""
Format Validator Agent (POST Phase)

Pure Python validation (no LLM) for:
- Search/Replace block structure
- Markdown validity
- File path correctness
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FormatValidatorAgent:
    """
    POST Phase Agent: Validates code format
    
    Pure Python implementation - no LLM calls.
    Checks search/replace block structure and markdown validity.
    """
    
    # Regex patterns
    SEARCH_BLOCK_PATTERN = r'<<<< SEARCH\n(.*?)\n>>>>'
    REPLACE_BLOCK_PATTERN = r'>>>> REPLACE\n(.*?)\n>>>>'
    MARKDOWN_CODE_FENCE = r'```'
    
    def __init__(self):
        self.search_block_regex = re.compile(self.SEARCH_BLOCK_PATTERN, re.DOTALL)
        self.replace_block_regex = re.compile(self.REPLACE_BLOCK_PATTERN, re.DOTALL)
    
    async def run(self, state: dict) -> dict:
        """
        Validate generated code format.
        
        Args:
            state: AgentState containing generated_code, file_path, file_type
        
        Returns:
            Dictionary with:
            - status: VALID | INVALID
            - errors: List of validation errors
            - warnings: List of warnings
            - formatted_code: Auto-fixed code if possible
        """
        
        generated_code = state.get("generated_code", "")
        file_path = state.get("file_path", "")
        file_type = state.get("file_type", "NEW")
        
        logger.info(f"Validating format for {file_path}")
        
        errors = []
        warnings = []
        
        # Validation checks
        errors.extend(self._validate_search_replace_blocks(generated_code))
        errors.extend(self._validate_markdown(generated_code))
        warnings.extend(self._validate_file_path(file_path, file_type))
        
        status = "VALID" if not errors else "INVALID"
        
        logger.info(f"Format validation complete. Status: {status}, Errors: {len(errors)}")
        
        return {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "formatted_code": generated_code,
            "error_count": len(errors),
            "warning_count": len(warnings)
        }
    
    def _validate_search_replace_blocks(self, code: str) -> list:
        """Validate search/replace block structure"""
        
        errors = []
        
        # Find all blocks
        search_blocks = self.search_block_regex.findall(code)
        replace_blocks = self.replace_block_regex.findall(code)
        
        # Check 1: Matching pairs
        if len(search_blocks) != len(replace_blocks):
            errors.append({
                "type": "BLOCK_MISMATCH",
                "description": f"Found {len(search_blocks)} SEARCH blocks but {len(replace_blocks)} REPLACE blocks",
                "line_number": 0,
                "suggestion": "Ensure every <<<< SEARCH has a matching >>>> REPLACE"
            })
        
        # Check 2: Block closure - count >>>> markers
        search_count = code.count("<<<< SEARCH")
        replace_count = code.count(">>>> REPLACE")
        closing_count = code.count(">>>>")

        # Each SEARCH block needs a closing >>>>, each REPLACE block needs a closing >>>>
        # So we need at least 2 * (search_count) closing markers
        expected_closing = search_count + replace_count
        if closing_count < expected_closing:
            errors.append({
                "type": "UNCLOSED_BLOCKS",
                "description": f"Found {search_count} SEARCH and {replace_count} REPLACE blocks but only {closing_count} closing >>>> markers",
                "line_number": 0,
                "suggestion": "Ensure each SEARCH and REPLACE block is closed with >>>> on its own line"
            })
        
        # Check 3: Whitespace matching (search and replace should differ)
        for i, (search, replace) in enumerate(zip(search_blocks, replace_blocks)):
            if search.strip() == replace.strip():
                errors.append({
                    "type": "IDENTICAL_BLOCKS",
                    "description": f"SEARCH and REPLACE blocks {i+1} have identical content",
                    "line_number": 0,
                    "suggestion": "SEARCH and REPLACE blocks must differ"
                })
        
        # Check 4: No nested blocks
        if code.count("<<<< SEARCH") > len(search_blocks):
            errors.append({
                "type": "NESTED_BLOCKS",
                "description": "Nested search/replace blocks detected",
                "line_number": 0,
                "suggestion": "Blocks cannot be nested"
            })
        
        return errors
    
    def _validate_markdown(self, code: str) -> list:
        """Validate markdown syntax"""
        
        errors = []
        
        # Check 1: Code fence balance
        fence_count = code.count('```')
        if fence_count % 2 != 0:
            errors.append({
                "type": "UNBALANCED_CODE_FENCE",
                "description": "Unbalanced markdown code fences (```)",
                "line_number": 0,
                "suggestion": "Ensure code fences are properly closed"
            })
        
        # Check 2: Unescaped backticks in code
        lines = code.split('\n')
        in_code_block = False
        for i, line in enumerate(lines):
            if line.startswith('```'):
                in_code_block = not in_code_block
            elif not in_code_block and '`' in line and not line.startswith('`'):
                # Backtick outside code block
                if line.count('`') % 2 != 0:
                    errors.append({
                        "type": "UNESCAPED_BACKTICK",
                        "description": f"Unescaped backtick on line {i+1}",
                        "line_number": i + 1,
                        "suggestion": "Escape backticks or wrap in code fence"
                    })
        
        return errors
    
    def _validate_file_path(self, file_path: str, file_type: str) -> list:
        """Validate file path"""
        
        warnings = []
        
        if not file_path:
            warnings.append({
                "type": "MISSING_FILE_PATH",
                "description": "No file path specified",
                "suggestion": "Specify the target file path"
            })
        
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in file_path for char in invalid_chars):
            warnings.append({
                "type": "INVALID_FILE_PATH_CHARS",
                "description": f"File path contains invalid characters",
                "suggestion": f"Remove these characters: {', '.join(invalid_chars)}"
            })
        
        return warnings
    
    def auto_fix_format(self, code: str) -> Optional[str]:
        """
        Attempt to auto-fix common format issues.
        
        Returns fixed code or None if unfixable.
        """
        
        fixed = code
        
        # Fix 1: Add missing closing >>>>
        if "<<<< SEARCH" in fixed and fixed.count(">>>>") < fixed.count("<<<< SEARCH"):
            # Add closing >>>> after each SEARCH block
            fixed = re.sub(
                r'(<<<< SEARCH\n.*?\n)(?!>>>>)',
                r'\1>>>>',
                fixed,
                flags=re.DOTALL
            )
        
        # Fix 2: Balance code fences
        if fixed.count('```') % 2 != 0:
            fixed += '\n```'
        
        return fixed if fixed != code else None


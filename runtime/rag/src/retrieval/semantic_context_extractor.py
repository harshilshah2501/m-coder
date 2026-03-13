#!/usr/bin/env python3
"""
Semantic Context Extractor for V14

Extracts semantic context for code modifications WITHOUT line numbers.
Uses semantic anchoring (method signatures, surrounding context) like Sonnet 4.5 / GPT-4o.

Key Principles:
1. Always read CURRENT file (not indexed version)
2. Use semantic anchors (method signatures, not line numbers)
3. Provide surrounding context (prev/next methods for disambiguation)
4. Include method body with smart truncation for token efficiency
5. Let git apply do fuzzy matching (tolerates line number drift)

OPTIMIZED: Reduced context size to fit within 16K token budget
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from tree_sitter import Language, Parser, Node
import tree_sitter_java as tsjava

# Token optimization settings - BALANCED for accuracy
MAX_METHOD_LINES = 75  # Truncate very long methods (balanced: was unlimited, tried 50)
MAX_FIELDS = 10  # Limit class fields (balanced: was 20, tried 5)
MAX_IMPORTS = 8  # Limit imports (balanced: was 10, tried 5)


@dataclass
class SimpleMethod:
    """Simple method representation (regex-based)"""
    name: str
    signature: str
    content: str
    start_line: int
    end_line: int


@dataclass
class SemanticContext:
    """Semantic context for a code modification task"""
    file_path: str
    class_name: str
    target_method: Optional[SimpleMethod]
    previous_method: Optional[SimpleMethod]
    next_method: Optional[SimpleMethod]
    class_fields: List[str]
    imports: List[str]
    full_file_content: str
    
    def to_prompt(self, task_description: str) -> str:
        """Convert to LLM prompt format"""
        
        # Build context sections
        sections = []
        
        # File header
        sections.append(f"File: {self.file_path}")
        sections.append(f"Class: {self.class_name}")
        sections.append("")
        
        # Imports (limited for token efficiency)
        if self.imports:
            sections.append("Key imports:")
            for imp in self.imports[:MAX_IMPORTS]:
                sections.append(f"  {imp}")
            if len(self.imports) > MAX_IMPORTS:
                sections.append(f"  ... ({len(self.imports) - MAX_IMPORTS} more imports)")
            sections.append("")

        # Class fields (limited for token efficiency)
        if self.class_fields:
            sections.append("Available fields in this class:")
            for field in self.class_fields[:MAX_FIELDS]:
                sections.append(f"  {field}")
            if len(self.class_fields) > MAX_FIELDS:
                sections.append(f"  ... ({len(self.class_fields) - MAX_FIELDS} more fields)")
            sections.append("")
        
        # Previous method (for disambiguation) - truncated for token efficiency
        if self.previous_method:
            sections.append("Previous method (for context):")
            sections.append("```java")
            sections.append(self._truncate_method(self.previous_method.content.strip()))
            sections.append("```")
            sections.append("")

        # Target method (the one to modify) - full content
        if self.target_method:
            sections.append("Target method (MODIFY THIS):")
            sections.append("```java")
            sections.append(self._truncate_method(self.target_method.content.strip(), is_target=True))
            sections.append("```")
            sections.append("")

        # Next method (for disambiguation) - truncated for token efficiency
        if self.next_method:
            sections.append("Next method (for context):")
            sections.append("```java")
            sections.append(self._truncate_method(self.next_method.content.strip()))
            sections.append("```")
            sections.append("")
        
        # Task
        sections.append(f"Task: {task_description}")
        sections.append("")
        sections.append("Generate a unified diff that:")
        sections.append("1. Uses the method signature as the anchor (NOT line numbers)")
        sections.append("2. Includes ±3 context lines for fuzzy matching")
        sections.append("3. ONLY modifies what's requested (no extra changes)")
        sections.append("4. Uses proper unified diff format (--- a/ and +++ b/)")

        return "\n".join(sections)

    def _truncate_method(self, content: str, is_target: bool = False) -> str:
        """Truncate method content for token efficiency"""
        lines = content.split('\n')

        # Target method gets more lines, context methods get less
        max_lines = MAX_METHOD_LINES if is_target else MAX_METHOD_LINES // 2

        if len(lines) <= max_lines:
            return content

        # Keep signature + first lines + last lines
        signature_lines = 3  # Method signature + opening brace
        keep_start = max_lines // 2
        keep_end = max_lines - keep_start - signature_lines

        truncated = (
            lines[:signature_lines + keep_start] +
            [f"    // ... ({len(lines) - max_lines} lines omitted for brevity) ..."] +
            lines[-keep_end:]
        )
        return '\n'.join(truncated)


class SemanticContextExtractor:
    """Extracts semantic context from Java files at runtime using tree-sitter"""

    def __init__(self, workspace_root: str = "/home/harshil/TestMotadataProject/Motadata/motadata"):
        self.workspace_root = Path(workspace_root)

        # Initialize tree-sitter parser
        self.parser = Parser(Language(tsjava.language()))
    
    def extract_method_context(
        self,
        file_path: str,
        method_name: str,
        class_name: Optional[str] = None
    ) -> SemanticContext:
        """
        Extract semantic context for a method modification using tree-sitter.

        Args:
            file_path: Relative or absolute path to Java file
            method_name: Name of the method to modify
            class_name: Optional class name (for disambiguation if file has multiple classes)

        Returns:
            SemanticContext with full surrounding context
        """
        # Resolve to absolute path
        if not os.path.isabs(file_path):
            abs_path = self.workspace_root / file_path
        else:
            abs_path = Path(file_path)

        if not abs_path.exists():
            raise FileNotFoundError(f"File not found: {abs_path}")

        # Read CURRENT file (not indexed version)
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse with tree-sitter
        tree = self.parser.parse(bytes(content, 'utf8'))
        root_node = tree.root_node

        # Extract class name
        extracted_class_name = self._get_class_name(root_node, content)
        if not extracted_class_name:
            raise ValueError(f"No class found in {file_path}")

        # Extract all methods
        methods = self._get_methods(root_node, content)

        if not methods:
            raise ValueError(f"No methods found in {file_path}")

        # Find target method
        target_method = None
        method_index = -1
        for i, method in enumerate(methods):
            if method.name == method_name:
                target_method = method
                method_index = i
                break

        if not target_method:
            available = [m.name for m in methods]
            raise ValueError(
                f"Method {method_name} not found in class {extracted_class_name}. "
                f"Available methods: {available}"
            )

        # Get surrounding methods
        previous_method = methods[method_index - 1] if method_index > 0 else None
        next_method = methods[method_index + 1] if method_index < len(methods) - 1 else None

        # Extract class fields and imports
        class_fields = self._get_fields(root_node, content)
        imports = self._get_imports(root_node, content)

        return SemanticContext(
            file_path=str(abs_path.relative_to(self.workspace_root)),
            class_name=extracted_class_name,
            target_method=target_method,
            previous_method=previous_method,
            next_method=next_method,
            class_fields=class_fields,
            imports=imports,
            full_file_content=content
        )
    
    def _extract_class_name(self, content: str) -> Optional[str]:
        """Extract class name from Java file"""
        match = re.search(r'public\s+class\s+(\w+)', content)
        if match:
            return match.group(1)
        return None

    def _extract_methods_regex(self, content: str) -> List[SimpleMethod]:
        """Extract methods using regex and brace counting"""
        methods = []
        lines = content.splitlines()

        # Pattern for method signatures (public/private/protected ... methodName(...) {)
        method_pattern = r'^\s*(public|private|protected|static|final|\s)+\s+[\w<>,\[\]\s]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{'

        i = 0
        while i < len(lines):
            line = lines[i]
            match = re.search(method_pattern, line)

            if match:
                method_name = match.group(2)
                signature_line = line.strip()
                start_line = i + 1  # 1-based

                # Extract method body using brace counting
                brace_count = line.count('{') - line.count('}')
                method_lines = [line]
                i += 1

                while i < len(lines) and brace_count > 0:
                    current_line = lines[i]
                    method_lines.append(current_line)
                    brace_count += current_line.count('{') - current_line.count('}')
                    i += 1

                method_content = '\n'.join(method_lines)
                end_line = start_line + len(method_lines) - 1

                methods.append(SimpleMethod(
                    name=method_name,
                    signature=signature_line,
                    content=method_content,
                    start_line=start_line,
                    end_line=end_line
                ))
            else:
                i += 1

        return methods

    def _extract_fields_regex(self, content: str) -> List[str]:
        """Extract field declarations from class"""
        fields = []

        # Look for field patterns: private/public/protected TYPE NAME;
        pattern = r'(private|public|protected|static|final)\s+[\w<>,\[\]\s]+\s+\w+\s*[=;]'

        for line in content.splitlines():
            line = line.strip()
            if re.match(pattern, line) and not line.startswith('//'):
                fields.append(line)

        return fields[:MAX_FIELDS]  # Limit for token efficiency
    
    def _get_class_name(self, root_node: Node, content: str) -> Optional[str]:
        """Extract class name using tree-sitter"""
        query = """
        (class_declaration
          name: (identifier) @class_name)
        """
        # Find class declaration
        for node in root_node.children:
            if node.type == 'class_declaration':
                for child in node.children:
                    if child.type == 'identifier':
                        return content[child.start_byte:child.end_byte]
        return None

    def _get_methods(self, root_node: Node, content: str) -> List[SimpleMethod]:
        """Extract all methods using tree-sitter"""
        methods = []

        # Find class body
        class_body = None
        for node in root_node.children:
            if node.type == 'class_declaration':
                for child in node.children:
                    if child.type == 'class_body':
                        class_body = child
                        break

        if not class_body:
            return methods

        # Extract methods from class body
        for node in class_body.children:
            if node.type == 'method_declaration':
                method_name = None

                # Find method name
                for child in node.children:
                    if child.type == 'identifier':
                        method_name = content[child.start_byte:child.end_byte]
                        break

                if method_name:
                    # Extract full method content
                    method_content = content[node.start_byte:node.end_byte]

                    # Get signature (first line)
                    signature = method_content.split('\n')[0].strip()

                    # Calculate line numbers
                    start_line = content[:node.start_byte].count('\n') + 1
                    end_line = content[:node.end_byte].count('\n') + 1

                    methods.append(SimpleMethod(
                        name=method_name,
                        signature=signature,
                        content=method_content,
                        start_line=start_line,
                        end_line=end_line
                    ))

        return methods

    def _get_fields(self, root_node: Node, content: str) -> List[str]:
        """Extract field declarations using tree-sitter"""
        fields = []

        # Find class body
        class_body = None
        for node in root_node.children:
            if node.type == 'class_declaration':
                for child in node.children:
                    if child.type == 'class_body':
                        class_body = child
                        break

        if not class_body:
            return fields

        # Extract fields
        for node in class_body.children:
            if node.type == 'field_declaration':
                field_text = content[node.start_byte:node.end_byte].strip()
                fields.append(field_text)

                if len(fields) >= MAX_FIELDS:  # Limit for token efficiency
                    break

        return fields

    def _get_imports(self, root_node: Node, content: str) -> List[str]:
        """Extract import statements using tree-sitter"""
        imports = []

        for node in root_node.children:
            if node.type == 'import_declaration':
                import_text = content[node.start_byte:node.end_byte].strip()
                imports.append(import_text)

        return imports


# Convenience function for API integration
def get_semantic_context(
    file_path: str,
    method_name: str,
    task_description: str,
    class_name: Optional[str] = None,
    workspace_root: str = "/home/harshil/TestMotadataProject/Motadata/motadata"
) -> str:
    """
    Get semantic context as a formatted prompt string.
    
    Args:
        file_path: Path to Java file (relative or absolute)
        method_name: Name of method to modify
        task_description: What to do (e.g., "Add logging at start of method")
        class_name: Optional class name for disambiguation
        workspace_root: Root directory of the codebase
    
    Returns:
        Formatted prompt string ready for LLM
    """
    extractor = SemanticContextExtractor(workspace_root)
    context = extractor.extract_method_context(file_path, method_name, class_name)
    return context.to_prompt(task_description)


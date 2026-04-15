#!/usr/bin/env python3
"""
Java AST Parser using javalang
Extracts class hierarchy (extends/implements) and method signatures accurately.
"""

import javalang
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

@dataclass
class JavaClass:
    name: str
    package: str
    file_path: str
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    methods: List['JavaMethod'] = field(default_factory=list)
    content: str = ""
    start_line: int = 0
    end_line: int = 0

    @property
    def qualified_name(self) -> str:
        return f"{self.package}.{self.name}" if self.package else self.name

@dataclass
class JavaMethod:
    name: str
    return_type: str
    parameters: List[str]
    content: str
    start_line: int
    end_line: int
    is_static: bool = False
    is_public: bool = False

class JavaParser:
    def __init__(self):
        pass

    def parse_file(self, file_path: str, content: str = None) -> List[JavaClass]:
        """Parse a Java file and return a list of classes found"""
        if content is None:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        classes = []
        try:
            tree = javalang.parse.parse(content)
            package_name = tree.package.name if tree.package else ""
            lines = content.splitlines()

            # Handle Classes
            for path, node in tree.filter(javalang.tree.ClassDeclaration):
                # Get class details
                class_name = node.name
                extends = node.extends.name if node.extends else None
                implements = [i.name for i in node.implements] if node.implements else []
                
                # Calculate line ranges (approximate as javalang doesn't give end lines directly)
                start_line = node.position.line if node.position else 1
                
                # Extract methods
                methods = []
                for m in node.methods:
                    m_start = m.position.line if m.position else start_line
                    
                    # Reconstruct signature
                    params = [f"{p.type.name} {p.name}" for p in m.parameters]
                    return_type = m.return_type.name if m.return_type else "void"
                    
                    # Extract method body (naive approach: brace counting)
                    # In a real implementation, we'd use the token stream, but for now:
                    method_content = self._extract_body(lines, m_start - 1)
                    
                    methods.append(JavaMethod(
                        name=m.name,
                        return_type=return_type,
                        parameters=params,
                        content=method_content,
                        start_line=m_start,
                        end_line=m_start + method_content.count('\n'),
                        is_static='static' in m.modifiers,
                        is_public='public' in m.modifiers
                    ))

                # Extract class body
                class_content = self._extract_body(lines, start_line - 1)

                classes.append(JavaClass(
                    name=class_name,
                    package=package_name,
                    file_path=file_path,
                    extends=extends,
                    implements=implements,
                    methods=methods,
                    content=class_content,
                    start_line=start_line,
                    end_line=start_line + class_content.count('\n')
                ))

            # Handle Interfaces
            for path, node in tree.filter(javalang.tree.InterfaceDeclaration):
                class_name = node.name
                extends = [e.name for e in node.extends] if node.extends else []
                # Interfaces extend other interfaces, but we can map them to 'extends' or 'implements' logic
                # For simplicity, let's treat interface extension as 'extends'
                
                start_line = node.position.line if node.position else 1
                class_content = self._extract_body(lines, start_line - 1)
                
                classes.append(JavaClass(
                    name=class_name,
                    package=package_name,
                    file_path=file_path,
                    extends=extends[0] if extends else None, # Primary parent
                    implements=extends[1:], # Additional parents
                    methods=[], # Interface methods usually don't have bodies (except default)
                    content=class_content,
                    start_line=start_line,
                    end_line=start_line + class_content.count('\n')
                ))

        except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError, Exception) as e:
            # Fallback to regex parsing for files with newer syntax (e.g. switch expressions)
            # print(f"Warning: javalang failed for {file_path}, using regex fallback. Error: {e}")
            return self._regex_fallback(file_path, content)

        return classes

    def _regex_fallback(self, file_path: str, content: str) -> List[JavaClass]:
        """Fallback parser using regex to extract basic class info"""
        classes = []
        
        # Extract package
        package_match = re.search(r'package\s+([\w.]+);', content)
        package_name = package_match.group(1) if package_match else ""
        
        # Extract class declaration
        # Matches: public class MyClass extends Base implements A, B
        class_pattern = re.compile(r'public\s+(?:abstract\s+|final\s+)*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w\s,]+))?')
        
        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            extends = match.group(2)
            implements_str = match.group(3)
            
            implements = []
            if implements_str:
                implements = [i.strip() for i in implements_str.split(',')]
            
            # For regex fallback, we won't try to extract methods or exact body content accurately
            # This is just to ensure we get the graph nodes
            
            classes.append(JavaClass(
                name=class_name,
                package=package_name,
                file_path=file_path,
                extends=extends,
                implements=implements,
                methods=[], # No methods in fallback
                content=content, # Store full content as fallback
                start_line=1,
                end_line=content.count('\n') + 1
            ))
            
        return classes

    def _extract_body(self, lines: List[str], start_index: int) -> str:
        """Extract code block by counting braces"""
        if start_index >= len(lines):
            return ""
            
        buffer = []
        brace_count = 0
        started = False
        
        for i in range(start_index, len(lines)):
            line = lines[i]
            buffer.append(line)
            
            brace_count += line.count('{')
            brace_count -= line.count('}')
            
            if '{' in line:
                started = True
            
            if started and brace_count == 0:
                break
                
        return '\n'.join(buffer)

if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) > 1:
        parser = JavaParser()
        classes = parser.parse_file(sys.argv[1])
        for c in classes:
            print(f"Class: {c.qualified_name}")
            print(f"  Extends: {c.extends}")
            print(f"  Implements: {c.implements}")
            print(f"  Methods: {len(c.methods)}")

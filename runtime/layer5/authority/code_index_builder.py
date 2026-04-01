"""
Code Index Builder.

Scans Java files and builds a lightweight code understanding index:
- File/class/method extraction
- Import relationships
- Direct 1-hop call edges (conservative)
- Entry point detection

Phase 2: Structure extraction, no ranking.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from runtime.layer5.authority.code_index_models import (
    CallConfidence,
    CallEdge,
    ClassRecord,
    CodeIndex,
    EntryPointRecord,
    FileRecord,
    MethodRecord,
)
from runtime.layer5.authority.entry_points import extract_entry_points


class JavaExtractor:
    """
    Extracts structural information from Java files.

    Uses conservative regex patterns to avoid over-claiming.
    """

    # Pattern for package declaration
    PACKAGE_PATTERN = re.compile(r"^package\s+([\w.]+)\s*;", re.MULTILINE)

    # Pattern for imports
    IMPORT_PATTERN = re.compile(r"^import\s+(?:static\s+)?([\w.*]+)\s*;", re.MULTILINE)

    # Pattern for class/interface/enum declaration
    CLASS_PATTERN = re.compile(
        r"(?:public\s+)?(?:abstract\s+)?(?:final\s+)?"
        r"(class|interface|enum|record)\s+"
        r"(\w+)"
        r"(?:\s*<[^>]+>)?"  # Generic type params
        r"(?:\s+extends\s+([\w.<>,\s]+?))?"
        r"(?:\s+implements\s+([\w.<>,\s]+))?"
        r"\s*\{",
        re.MULTILINE,
    )

    # Pattern for method declaration
    METHOD_PATTERN = re.compile(
        r"((?:@\w+(?:\([^)]*\))?\s*)*)"  # Annotations
        r"(public|private|protected)?\s*"
        r"(static\s+)?(?:final\s+)?(?:synchronized\s+)?"
        r"(?:<[^>]+>\s*)?"  # Generic
        r"([\w<>\[\],\s]+?)\s+"  # Return type
        r"(\w+)\s*\("  # Method name
        r"([^)]*)\)",  # Parameters
        re.MULTILINE,
    )

    # Pattern for method invocations
    INVOCATION_PATTERN = re.compile(
        r"(?<![.\w])(\w+)\.(\w+)\s*\(",
    )

    # Noise patterns to skip
    NOISE_TARGETS = frozenset({
        "log", "logger", "LOG", "LOGGER", "System",
        "String", "Integer", "Long", "Double", "Boolean",
        "List", "Set", "Map", "Arrays", "Collections",
        "Optional", "Stream", "Objects",
    })

    NOISE_METHODS = frozenset({
        "toString", "equals", "hashCode", "getClass",
        "println", "print", "format", "valueOf",
        "add", "get", "put", "remove", "contains",
        "size", "isEmpty", "clear",
    })

    def __init__(self) -> None:
        pass

    def extract_package(self, content: str) -> str:
        """Extract package name from Java file."""
        match = self.PACKAGE_PATTERN.search(content)
        return match.group(1) if match else ""

    def extract_imports(self, content: str) -> Set[str]:
        """Extract import statements."""
        imports: Set[str] = set()
        for match in self.IMPORT_PATTERN.finditer(content):
            imp = match.group(1)
            if not imp.startswith("java.lang."):
                imports.add(imp)
        return imports

    def extract_classes(
        self, content: str, file_path: str, package: str
    ) -> List[ClassRecord]:
        """Extract class/interface/enum declarations."""
        classes: List[ClassRecord] = []

        for match in self.CLASS_PATTERN.finditer(content):
            kind = match.group(1)  # class/interface/enum/record
            name = match.group(2)
            superclass = match.group(3)
            interfaces_str = match.group(4)

            interfaces: Tuple[str, ...] = ()
            if interfaces_str:
                interfaces = tuple(
                    i.strip()
                    for i in re.split(r",\s*", interfaces_str)
                    if i.strip()
                )

            # Extract annotations before class declaration
            pre_class = content[: match.start()]
            annotations: List[str] = []
            for ann_match in re.finditer(r"@(\w+)", pre_class[-500:]):
                annotations.append(ann_match.group(1))

            # Extract methods for this class
            methods = self._extract_methods_for_class(content, name, match.start())

            classes.append(
                ClassRecord(
                    name=name,
                    file_path=file_path,
                    package=package,
                    superclass=superclass.strip() if superclass else None,
                    interfaces=interfaces,
                    annotations=tuple(annotations[-5:]),  # Last 5 only
                    methods=tuple(m.name for m in methods),
                )
            )

        return classes

    def _extract_methods_for_class(
        self, content: str, class_name: str, class_start: int
    ) -> List[MethodRecord]:
        """Extract methods belonging to a class."""
        methods: List[MethodRecord] = []

        # Find class body (approximate)
        class_content = content[class_start:]

        for match in self.METHOD_PATTERN.finditer(class_content):
            annotations_str = match.group(1)
            visibility = match.group(2) or "package"
            is_static = bool(match.group(3))
            return_type = match.group(4)
            method_name = match.group(5)

            # Skip constructors
            if method_name == class_name:
                continue

            # Skip getters/setters if too simple
            if method_name.startswith(("get", "set", "is")) and len(method_name) < 20:
                # Include but mark
                pass

            annotations = tuple(re.findall(r"@(\w+)", annotations_str))

            methods.append(
                MethodRecord(
                    name=method_name,
                    class_name=class_name,
                    file_path="",  # Will be set later
                    visibility=visibility,
                    is_static=is_static,
                    annotations=annotations,
                )
            )

        return methods

    def extract_call_edges(
        self,
        content: str,
        file_path: str,
        source_class: str,
    ) -> List[CallEdge]:
        """
        Extract conservative 1-hop call edges from file.

        Only returns high-confidence direct method calls.
        """
        edges: List[CallEdge] = []

        # Find method bodies and extract calls
        for method_match in self.METHOD_PATTERN.finditer(content):
            method_name = method_match.group(5)

            if method_name == source_class:
                continue

            # Find method body (rough)
            method_start = method_match.end()
            brace_count = 0
            pos = method_start

            # Find opening brace
            while pos < len(content) and content[pos] != "{":
                pos += 1
            if pos >= len(content):
                continue

            brace_count = 1
            body_start = pos + 1
            pos = body_start

            while pos < len(content) and brace_count > 0:
                if content[pos] == "{":
                    brace_count += 1
                elif content[pos] == "}":
                    brace_count -= 1
                pos += 1

            method_body = content[body_start:pos]

            # Extract invocations
            for inv_match in self.INVOCATION_PATTERN.finditer(method_body):
                target = inv_match.group(1)
                target_method = inv_match.group(2)

                # Skip noise
                if target in self.NOISE_TARGETS:
                    continue
                if target_method in self.NOISE_METHODS:
                    continue

                # Skip 'this' references
                if target == "this":
                    continue

                # Determine confidence
                if target[0].isupper():
                    # Likely a class name (static call or type)
                    confidence = CallConfidence.MEDIUM
                else:
                    # Instance variable, lower confidence
                    confidence = CallConfidence.LOW

                edges.append(
                    CallEdge(
                        source_file=file_path,
                        source_class=source_class,
                        source_method=method_name,
                        target_class=target,
                        target_method=target_method,
                        confidence=confidence,
                    )
                )

        return edges


class CodeIndexBuilder:
    """
    Builds code understanding index from Java files.

    Scans directories, extracts structure, builds indices.
    """

    def __init__(
        self,
        workspace_root: Path,
        *,
        include_tests: bool = False,
        max_files: int = 10000,
    ) -> None:
        self.workspace_root = workspace_root
        self.include_tests = include_tests
        self.max_files = max_files
        self.extractor = JavaExtractor()

    def build(
        self,
        source_dirs: Optional[List[str]] = None,
    ) -> CodeIndex:
        """
        Build code index from workspace.

        Args:
            source_dirs: Optional list of source directories to scan.
                        If None, scans common Java source locations.

        Returns:
            Populated CodeIndex.
        """
        if source_dirs is None:
            source_dirs = self._find_source_dirs()

        index = CodeIndex()
        file_count = 0

        for source_dir in source_dirs:
            dir_path = self.workspace_root / source_dir
            if not dir_path.exists():
                continue

            for java_file in dir_path.rglob("*.java"):
                if file_count >= self.max_files:
                    break

                relative_path = str(java_file.relative_to(self.workspace_root))
                relative_path = relative_path.replace("\\", "/")

                # Skip tests if not included
                if not self.include_tests and self._is_test_file(relative_path):
                    continue

                file_record = self._process_file(java_file, relative_path)
                if file_record:
                    index.files[relative_path] = file_record
                    file_count += 1

                    # Extract entry points
                    entry_points = self._extract_entry_points(java_file, relative_path)
                    index.entry_points.extend(entry_points)

                    # Extract call edges
                    for cls in file_record.classes:
                        try:
                            content = java_file.read_text(encoding="utf-8", errors="replace")
                            edges = self.extractor.extract_call_edges(
                                content, relative_path, cls.name
                            )
                            index.call_edges.extend(edges)
                        except (OSError, PermissionError):
                            pass

        # Build derived indices
        index.build_indices()

        return index

    def _find_source_dirs(self) -> List[str]:
        """Find common Java source directories."""
        candidates = [
            "src/main/java",
            "src",
            "motadata/src/main/java",
            "app/src/main/java",
            "core/src/main/java",
        ]

        found = []
        for candidate in candidates:
            if (self.workspace_root / candidate).exists():
                found.append(candidate)

        # If nothing found, scan from root
        if not found:
            found.append(".")

        return found

    def _is_test_file(self, relative_path: str) -> bool:
        """Check if file is a test file."""
        path_lower = relative_path.lower()
        return (
            "/test/" in path_lower
            or "/tests/" in path_lower
            or path_lower.endswith("test.java")
            or path_lower.endswith("tests.java")
            or "test" in Path(relative_path).stem.lower()
        )

    def _process_file(self, file_path: Path, relative_path: str) -> Optional[FileRecord]:
        """Process a single Java file."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            return None

        package = self.extractor.extract_package(content)
        imports = self.extractor.extract_imports(content)
        classes = self.extractor.extract_classes(content, relative_path, package)

        if not classes:
            return None

        # Derive module from package
        module = ""
        if package:
            parts = package.split(".")
            if len(parts) >= 3:
                module = parts[2] if len(parts) > 2 else parts[-1]

        return FileRecord(
            relative_path=relative_path,
            package=package,
            module=module,
            classes=tuple(classes),
            imports=frozenset(imports),
            is_test=self._is_test_file(relative_path),
            line_count=content.count("\n") + 1,
        )

    def _extract_entry_points(
        self, file_path: Path, relative_path: str
    ) -> List[EntryPointRecord]:
        """Extract entry points from file."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            return extract_entry_points(relative_path, content)
        except (OSError, PermissionError):
            return []


def build_index(
    workspace_root: Path,
    *,
    source_dirs: Optional[List[str]] = None,
    include_tests: bool = False,
) -> CodeIndex:
    """
    Convenience function to build code index.

    Args:
        workspace_root: Workspace root path.
        source_dirs: Optional source directories.
        include_tests: Whether to include test files.

    Returns:
        Populated CodeIndex.
    """
    builder = CodeIndexBuilder(workspace_root, include_tests=include_tests)
    return builder.build(source_dirs=source_dirs)

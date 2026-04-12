"""
Entry Point Extraction.

Identifies system entry points in Java code:
- REST controllers (@RestController, @Controller, @RequestMapping)
- Event handlers (@EventHandler, extends EventHandler, *Handler classes)
- Schedulers (@Scheduled, @Scheduler)
- Message consumers (@KafkaListener, @RabbitListener, @JmsListener)

Phase 2: Pattern-based extraction, no ranking.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from runtime.layer5.authority.code_index_models import EntryPointRecord, EntryPointType


@dataclass
class EntryPointPattern:
    """Pattern definition for entry point detection."""

    entry_type: EntryPointType
    name: str
    class_patterns: Tuple[re.Pattern, ...] = ()
    method_patterns: Tuple[re.Pattern, ...] = ()
    annotation_patterns: Tuple[re.Pattern, ...] = ()
    file_patterns: Tuple[re.Pattern, ...] = ()
    extract_metadata: bool = True


# Pre-compiled patterns for entry point detection

# REST Controller patterns
REST_CLASS_PATTERNS = (
    re.compile(r"@RestController\b"),
    re.compile(r"@Controller\b"),
)

REST_METHOD_PATTERNS = (
    re.compile(r"@(Get|Post|Put|Delete|Patch)Mapping\s*\(\s*[\"']([^\"']+)[\"']"),
    re.compile(r"@RequestMapping\s*\(\s*(?:value\s*=\s*)?[\"']([^\"']+)[\"']"),
    re.compile(r"@RequestMapping\s*\(\s*method\s*=\s*RequestMethod\.(\w+)"),
)

REST_ANNOTATION_PATTERNS = (
    re.compile(r"@(Get|Post|Put|Delete|Patch|Request)Mapping"),
)

# Event Handler patterns
EVENT_CLASS_PATTERNS = (
    re.compile(r"class\s+\w*Handler\s+"),
    re.compile(r"class\s+\w*EventHandler\s+"),
    re.compile(r"class\s+\w+\s+extends\s+\w*Handler\b"),
    re.compile(r"class\s+\w+\s+implements\s+\w*Handler\b"),
)

EVENT_METHOD_PATTERNS = (
    re.compile(r"@EventHandler\b"),
    re.compile(r"@Subscribe\b"),
    re.compile(r"@EventListener\b"),
    re.compile(r"void\s+handle\s*\("),
    re.compile(r"void\s+on\w+Event\s*\("),
)

EVENT_FILE_PATTERNS = (
    re.compile(r"Handler\.java$"),
    re.compile(r"EventHandler\.java$"),
    re.compile(r"(?:^|/)handlers/\w+\.java$"),
    re.compile(r"(?:^|/)eventbus/\w+\.java$"),
)

# Scheduler patterns
SCHEDULER_METHOD_PATTERNS = (
    re.compile(r"@Scheduled\s*\("),
    re.compile(r"@Scheduler\b"),
    re.compile(r"@EnableScheduling\b"),
    re.compile(r"@Cron\b"),
)

SCHEDULER_FILE_PATTERNS = (
    re.compile(r"Scheduler\.java$"),
    re.compile(r"ScheduledTask\.java$"),
    re.compile(r"/scheduler/\w+\.java$"),
)

# Message Consumer patterns
CONSUMER_METHOD_PATTERNS = (
    re.compile(r"@KafkaListener\s*\("),
    re.compile(r"@RabbitListener\s*\("),
    re.compile(r"@JmsListener\s*\("),
    re.compile(r"@StreamListener\s*\("),
)

CONSUMER_CLASS_PATTERNS = (
    re.compile(r"class\s+\w*Consumer\b"),
    re.compile(r"class\s+\w*Listener\b"),
    re.compile(r"implements\s+MessageListener\b"),
)

CONSUMER_FILE_PATTERNS = (
    re.compile(r"Consumer\.java$"),
    re.compile(r"Listener\.java$"),
    re.compile(r"/consumers/\w+\.java$"),
)


ENTRY_POINT_PATTERNS: List[EntryPointPattern] = [
    EntryPointPattern(
        entry_type=EntryPointType.REST_CONTROLLER,
        name="REST Controller",
        class_patterns=REST_CLASS_PATTERNS,
        method_patterns=REST_METHOD_PATTERNS,
        annotation_patterns=REST_ANNOTATION_PATTERNS,
    ),
    EntryPointPattern(
        entry_type=EntryPointType.EVENT_HANDLER,
        name="Event Handler",
        class_patterns=EVENT_CLASS_PATTERNS,
        method_patterns=EVENT_METHOD_PATTERNS,
        file_patterns=EVENT_FILE_PATTERNS,
    ),
    EntryPointPattern(
        entry_type=EntryPointType.SCHEDULER,
        name="Scheduler",
        method_patterns=SCHEDULER_METHOD_PATTERNS,
        file_patterns=SCHEDULER_FILE_PATTERNS,
    ),
    EntryPointPattern(
        entry_type=EntryPointType.MESSAGE_CONSUMER,
        name="Message Consumer",
        class_patterns=CONSUMER_CLASS_PATTERNS,
        method_patterns=CONSUMER_METHOD_PATTERNS,
        file_patterns=CONSUMER_FILE_PATTERNS,
    ),
]


def _extract_class_name(content: str) -> Optional[str]:
    """Extract primary class name from Java file content."""
    match = re.search(
        r"(?:public\s+)?(?:abstract\s+)?(?:class|interface|enum)\s+(\w+)",
        content,
    )
    return match.group(1) if match else None


def _extract_methods_with_annotations(
    content: str, class_name: str
) -> List[Tuple[str, List[str]]]:
    """
    Extract methods with their annotations.

    Returns list of (method_name, [annotations]).
    """
    methods: List[Tuple[str, List[str]]] = []

    # Pattern to find method declarations with optional preceding annotations
    method_pattern = re.compile(
        r"((?:@\w+(?:\([^)]*\))?\s*)*)"  # Annotations
        r"(?:public|private|protected)?\s*"
        r"(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?"
        r"(?:<[^>]+>\s*)?"  # Generic
        r"(\w+(?:\s*<[^>]+>)?)\s+"  # Return type
        r"(\w+)\s*\(",  # Method name
        re.MULTILINE,
    )

    for match in method_pattern.finditer(content):
        annotations_str = match.group(1)
        method_name = match.group(3)

        # Skip constructors
        if method_name == class_name:
            continue

        annotations = re.findall(r"@(\w+)", annotations_str)
        methods.append((method_name, annotations))

    return methods


def _extract_method_invocations(
    content: str, method_name: str
) -> List[Tuple[str, str]]:
    """
    Extract method invocations within a method body.

    Returns list of (target_class_or_var, target_method).
    Conservative: only returns clear patterns.
    """
    invocations: List[Tuple[str, str]] = []

    # Find method body (simplified - look for method signature then brace matching)
    method_start = re.search(
        rf"\b{re.escape(method_name)}\s*\([^)]*\)\s*(?:throws[^{{]*)?\{{",
        content,
    )
    if not method_start:
        return []

    # Extract rough method body (find matching brace)
    start_pos = method_start.end()
    brace_count = 1
    pos = start_pos
    while pos < len(content) and brace_count > 0:
        if content[pos] == "{":
            brace_count += 1
        elif content[pos] == "}":
            brace_count -= 1
        pos += 1

    method_body = content[start_pos:pos]

    # Extract invocations: variable.method() or Class.method() or this.method()
    invocation_pattern = re.compile(r"(\w+)\.(\w+)\s*\(")
    for match in invocation_pattern.finditer(method_body):
        target = match.group(1)
        method = match.group(2)
        # Skip common noise
        if target.lower() in ("log", "logger", "system", "string", "list", "map"):
            continue
        if method in ("toString", "equals", "hashCode", "getClass"):
            continue
        invocations.append((target, method))

    return invocations


def detect_entry_point_type(
    file_path: str,
    content: str,
    class_name: Optional[str] = None,
) -> Optional[EntryPointType]:
    """
    Detect if file contains an entry point and return its type.

    Args:
        file_path: Relative file path.
        content: File content.
        class_name: Optional pre-extracted class name.

    Returns:
        EntryPointType if detected, None otherwise.
    """
    for pattern in ENTRY_POINT_PATTERNS:
        # Check file patterns
        for fp in pattern.file_patterns:
            if fp.search(file_path):
                return pattern.entry_type

        # Check class patterns
        for cp in pattern.class_patterns:
            if cp.search(content):
                return pattern.entry_type

        # Check annotation patterns (method-level)
        for ap in pattern.annotation_patterns:
            if ap.search(content):
                return pattern.entry_type

        # Check method patterns (for detecting @Scheduled, etc.)
        for mp in pattern.method_patterns:
            if mp.search(content):
                return pattern.entry_type

    return None


def extract_entry_points(
    file_path: str,
    content: str,
) -> List[EntryPointRecord]:
    """
    Extract all entry points from a Java file.

    Args:
        file_path: Relative file path.
        content: File content.

    Returns:
        List of EntryPointRecord for detected entry points.
    """
    results: List[EntryPointRecord] = []

    class_name = _extract_class_name(content)
    if not class_name:
        return []

    methods = _extract_methods_with_annotations(content, class_name)

    for pattern in ENTRY_POINT_PATTERNS:
        is_entry_class = False
        matched_pattern = ""

        # Check if class-level entry point
        for cp in pattern.class_patterns:
            if cp.search(content):
                is_entry_class = True
                matched_pattern = f"class:{cp.pattern}"
                break

        # Check file patterns
        if not is_entry_class:
            for fp in pattern.file_patterns:
                if fp.search(file_path):
                    is_entry_class = True
                    matched_pattern = f"file:{fp.pattern}"
                    break

        # For REST controllers, look for endpoint methods
        if pattern.entry_type == EntryPointType.REST_CONTROLLER and is_entry_class:
            for method_name, annotations in methods:
                for mp in pattern.method_patterns:
                    match = mp.search(content)
                    if match:
                        metadata: Dict[str, Any] = {"http_method": "GET"}

                        # Try to extract endpoint path
                        if match.lastindex and match.lastindex >= 1:
                            first_group = match.group(1)
                            if first_group in ("Get", "Post", "Put", "Delete", "Patch"):
                                metadata["http_method"] = first_group.upper()
                                if match.lastindex >= 2:
                                    metadata["endpoint"] = match.group(2)
                            else:
                                metadata["endpoint"] = first_group

                        invokes = _extract_method_invocations(content, method_name)
                        invoke_strs = tuple(f"{t}.{m}" for t, m in invokes[:5])

                        results.append(
                            EntryPointRecord(
                                entry_type=pattern.entry_type,
                                relative_path=file_path,
                                class_name=class_name,
                                method_name=method_name,
                                metadata=metadata,
                                invokes=invoke_strs,
                                pattern_matched=matched_pattern,
                            )
                        )
                        break

        # For event handlers, look for handle methods
        elif pattern.entry_type == EntryPointType.EVENT_HANDLER:
            for method_name, annotations in methods:
                is_handler_method = False
                method_metadata: Dict[str, Any] = {}

                # Check method annotations
                for ann in annotations:
                    if ann in ("EventHandler", "Subscribe", "EventListener"):
                        is_handler_method = True
                        method_metadata["annotation"] = f"@{ann}"
                        break

                # Check method name patterns
                if not is_handler_method:
                    if method_name == "handle" or method_name.startswith("on"):
                        for mp in pattern.method_patterns:
                            if mp.search(f"void {method_name}"):
                                is_handler_method = True
                                matched_pattern = f"method:{mp.pattern}"
                                break

                if is_handler_method or is_entry_class and method_name == "handle":
                    invokes = _extract_method_invocations(content, method_name)
                    invoke_strs = tuple(f"{t}.{m}" for t, m in invokes[:5])

                    results.append(
                        EntryPointRecord(
                            entry_type=pattern.entry_type,
                            relative_path=file_path,
                            class_name=class_name,
                            method_name=method_name,
                            metadata=method_metadata,
                            invokes=invoke_strs,
                            pattern_matched=matched_pattern or f"handler_class",
                        )
                    )

        # For schedulers, look for @Scheduled methods
        elif pattern.entry_type == EntryPointType.SCHEDULER:
            for method_name, annotations in methods:
                for ann in annotations:
                    if ann in ("Scheduled", "Scheduler", "Cron"):
                        invokes = _extract_method_invocations(content, method_name)
                        invoke_strs = tuple(f"{t}.{m}" for t, m in invokes[:5])

                        results.append(
                            EntryPointRecord(
                                entry_type=pattern.entry_type,
                                relative_path=file_path,
                                class_name=class_name,
                                method_name=method_name,
                                metadata={"annotation": f"@{ann}"},
                                invokes=invoke_strs,
                                pattern_matched=f"annotation:@{ann}",
                            )
                        )
                        break

        # For message consumers, look for listener methods
        elif pattern.entry_type == EntryPointType.MESSAGE_CONSUMER:
            for method_name, annotations in methods:
                for ann in annotations:
                    if ann in ("KafkaListener", "RabbitListener", "JmsListener", "StreamListener"):
                        invokes = _extract_method_invocations(content, method_name)
                        invoke_strs = tuple(f"{t}.{m}" for t, m in invokes[:5])

                        results.append(
                            EntryPointRecord(
                                entry_type=pattern.entry_type,
                                relative_path=file_path,
                                class_name=class_name,
                                method_name=method_name,
                                metadata={"annotation": f"@{ann}"},
                                invokes=invoke_strs,
                                pattern_matched=f"annotation:@{ann}",
                            )
                        )
                        break

    return results


def is_entry_point_file(file_path: str, content: str) -> bool:
    """Check if file contains any entry point."""
    return detect_entry_point_type(file_path, content) is not None

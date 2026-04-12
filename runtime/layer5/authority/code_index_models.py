"""
Code Index Data Models.

Defines structures for code understanding index:
- FileRecord: file-level metadata with classes, methods, imports
- ClassRecord: class-level metadata with methods
- MethodRecord: method-level metadata
- CallEdge: caller/callee relationships
- EntryPointRecord: system entry points (REST, event handlers, etc.)

Phase 2: Structure extraction, no ranking.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple


class EntryPointType(Enum):
    """Type of system entry point."""

    REST_CONTROLLER = "rest_controller"
    EVENT_HANDLER = "event_handler"
    SCHEDULER = "scheduler"
    MESSAGE_CONSUMER = "message_consumer"
    UNKNOWN = "unknown"


class CallConfidence(Enum):
    """Confidence level for call edge detection."""

    HIGH = "high"  # Direct method call with resolvable target
    MEDIUM = "medium"  # Method call, target inferred from context
    LOW = "low"  # Possible call, uncertain target


@dataclass(frozen=True)
class MethodRecord:
    """Method-level metadata."""

    name: str
    class_name: str
    file_path: str
    line_number: Optional[int] = None
    visibility: str = "public"
    is_static: bool = False
    annotations: Tuple[str, ...] = ()

    @property
    def qualified_name(self) -> str:
        """Return fully qualified method name."""
        return f"{self.class_name}.{self.name}"


@dataclass(frozen=True)
class ClassRecord:
    """Class-level metadata."""

    name: str
    file_path: str
    package: str = ""
    superclass: Optional[str] = None
    interfaces: Tuple[str, ...] = ()
    annotations: Tuple[str, ...] = ()
    methods: Tuple[str, ...] = ()
    line_number: Optional[int] = None

    @property
    def qualified_name(self) -> str:
        """Return fully qualified class name."""
        if self.package:
            return f"{self.package}.{self.name}"
        return self.name


@dataclass
class FileRecord:
    """File-level metadata with classes, methods, imports."""

    relative_path: str
    package: str = ""
    module: str = ""
    classes: Tuple[ClassRecord, ...] = ()
    imports: FrozenSet[str] = field(default_factory=frozenset)
    is_test: bool = False
    line_count: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.imports, (list, set)):
            object.__setattr__(self, "imports", frozenset(self.imports))

    @property
    def class_names(self) -> Tuple[str, ...]:
        """Return all class names in file."""
        return tuple(c.name for c in self.classes)

    @property
    def method_names(self) -> Tuple[str, ...]:
        """Return all method names across all classes."""
        methods: List[str] = []
        for cls in self.classes:
            methods.extend(cls.methods)
        return tuple(methods)

    def has_class(self, class_name: str) -> bool:
        """Check if file contains class."""
        return class_name in self.class_names

    def has_method(self, class_name: str, method_name: str) -> bool:
        """Check if file contains method in class."""
        for cls in self.classes:
            if cls.name == class_name and method_name in cls.methods:
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "relative_path": self.relative_path,
            "package": self.package,
            "module": self.module,
            "classes": [
                {
                    "name": c.name,
                    "package": c.package,
                    "superclass": c.superclass,
                    "interfaces": list(c.interfaces),
                    "annotations": list(c.annotations),
                    "methods": list(c.methods),
                }
                for c in self.classes
            ],
            "imports": list(self.imports),
            "is_test": self.is_test,
            "line_count": self.line_count,
        }


@dataclass(frozen=True)
class CallEdge:
    """Caller/callee relationship edge."""

    source_file: str
    source_class: str
    source_method: str
    target_class: str
    target_method: str
    confidence: CallConfidence = CallConfidence.MEDIUM
    target_file: Optional[str] = None  # Resolved if known

    @property
    def source_qualified(self) -> str:
        """Return source as Class.method."""
        return f"{self.source_class}.{self.source_method}"

    @property
    def target_qualified(self) -> str:
        """Return target as Class.method."""
        return f"{self.target_class}.{self.target_method}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source_file": self.source_file,
            "source_class": self.source_class,
            "source_method": self.source_method,
            "target_class": self.target_class,
            "target_method": self.target_method,
            "confidence": self.confidence.value,
            "target_file": self.target_file,
        }


@dataclass
class EntryPointRecord:
    """System entry point record."""

    entry_type: EntryPointType
    relative_path: str
    class_name: str
    method_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    invokes: Tuple[str, ...] = ()  # List of target Class.method if detectable
    pattern_matched: str = ""  # Pattern that identified this entry point

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "entry_type": self.entry_type.value,
            "relative_path": self.relative_path,
            "class_name": self.class_name,
            "method_name": self.method_name,
            "metadata": self.metadata,
            "invokes": list(self.invokes),
            "pattern_matched": self.pattern_matched,
        }


@dataclass
class CodeIndex:
    """
    Complete code understanding index.

    Contains:
    - File records with classes/methods/imports
    - Entry point catalog
    - Call edges (1-hop)
    - Reverse reference lookup
    """

    files: Dict[str, FileRecord] = field(default_factory=dict)
    entry_points: List[EntryPointRecord] = field(default_factory=list)
    call_edges: List[CallEdge] = field(default_factory=list)

    # Derived indices (built after loading)
    _class_to_file: Dict[str, str] = field(default_factory=dict, repr=False)
    _method_to_file: Dict[str, str] = field(default_factory=dict, repr=False)
    _file_importers: Dict[str, Set[str]] = field(default_factory=dict, repr=False)
    _callers: Dict[str, List[CallEdge]] = field(default_factory=dict, repr=False)
    _callees: Dict[str, List[CallEdge]] = field(default_factory=dict, repr=False)

    def build_indices(self) -> None:
        """Build derived indices for fast lookup."""
        self._class_to_file.clear()
        self._method_to_file.clear()
        self._file_importers.clear()
        self._callers.clear()
        self._callees.clear()

        # Build class/method to file mapping
        for file_path, file_rec in self.files.items():
            for cls in file_rec.classes:
                self._class_to_file[cls.name] = file_path
                qualified = cls.qualified_name
                if qualified != cls.name:
                    self._class_to_file[qualified] = file_path

                for method in cls.methods:
                    key = f"{cls.name}.{method}"
                    self._method_to_file[key] = file_path

        # Build import reverse index (who imports what)
        for file_path, file_rec in self.files.items():
            for imp in file_rec.imports:
                # Extract simple name from import
                simple_name = imp.rsplit(".", 1)[-1]
                if simple_name not in self._file_importers:
                    self._file_importers[simple_name] = set()
                self._file_importers[simple_name].add(file_path)

        # Build call edge indices
        for edge in self.call_edges:
            source_key = edge.source_qualified
            target_key = edge.target_qualified

            if target_key not in self._callers:
                self._callers[target_key] = []
            self._callers[target_key].append(edge)

            if source_key not in self._callees:
                self._callees[source_key] = []
            self._callees[source_key].append(edge)

    def file_exists(self, relative_path: str) -> bool:
        """Check if file is in index."""
        normalized = relative_path.replace("\\", "/")
        return normalized in self.files

    def class_exists(self, relative_path: str, class_name: str) -> bool:
        """Check if class exists in file."""
        normalized = relative_path.replace("\\", "/")
        file_rec = self.files.get(normalized)
        if not file_rec:
            return False
        return file_rec.has_class(class_name)

    def method_exists(
        self, relative_path: str, class_name: str, method_name: str
    ) -> bool:
        """Check if method exists in class."""
        normalized = relative_path.replace("\\", "/")
        file_rec = self.files.get(normalized)
        if not file_rec:
            return False
        return file_rec.has_method(class_name, method_name)

    def is_referenced(self, relative_path: str) -> Optional[bool]:
        """Check if file is imported by other files."""
        normalized = relative_path.replace("\\", "/")
        file_rec = self.files.get(normalized)
        if not file_rec:
            return None

        # Check if any class from this file is imported elsewhere
        for cls in file_rec.classes:
            if cls.name in self._file_importers:
                importers = self._file_importers[cls.name]
                if importers - {normalized}:
                    return True

        return False

    def get_file(self, relative_path: str) -> Optional[FileRecord]:
        """Get file record."""
        normalized = relative_path.replace("\\", "/")
        return self.files.get(normalized)

    def get_entry_points_for_file(self, relative_path: str) -> List[EntryPointRecord]:
        """Get entry points in a file."""
        normalized = relative_path.replace("\\", "/")
        return [ep for ep in self.entry_points if ep.relative_path == normalized]

    def get_callers(self, class_name: str, method_name: str) -> List[CallEdge]:
        """Get direct callers of a method (1-hop reverse)."""
        key = f"{class_name}.{method_name}"
        return list(self._callers.get(key, []))

    def get_callees(self, class_name: str, method_name: str) -> List[CallEdge]:
        """Get methods called by a method (1-hop forward)."""
        key = f"{class_name}.{method_name}"
        return list(self._callees.get(key, []))

    def get_file_for_class(self, class_name: str) -> Optional[str]:
        """Get file path for a class."""
        return self._class_to_file.get(class_name)

    @property
    def stats(self) -> Dict[str, int]:
        """Return index statistics."""
        total_classes = sum(len(f.classes) for f in self.files.values())
        total_methods = sum(len(f.method_names) for f in self.files.values())
        return {
            "files": len(self.files),
            "classes": total_classes,
            "methods": total_methods,
            "entry_points": len(self.entry_points),
            "call_edges": len(self.call_edges),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "files": {k: v.to_dict() for k, v in self.files.items()},
            "entry_points": [ep.to_dict() for ep in self.entry_points],
            "call_edges": [ce.to_dict() for ce in self.call_edges],
            "stats": self.stats,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: Path) -> None:
        """Save index to JSON file."""
        path.write_text(self.to_json(), encoding="utf-8")

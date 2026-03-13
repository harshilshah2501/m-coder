"""
Context contracts — M3.0 Repository Context Engine.

Defines typed structures for:
- ContextRequest
- SelectedContextRef (selection-only, no content)
- ContextItem
- ContextBundle
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List


SelectorName = str  # e.g. "direct", "siblings", "imports", "symbols"


@dataclass
class ContextRequest:
    """
    Deterministic context request for a given task and repo revision.
    """

    task_id: str
    revision: str
    root_path: str
    files: List[str] = field(default_factory=list)
    symbol_hints: List[str] = field(default_factory=list)
    max_files: int = 50
    max_bytes: int = 512_000  # 500 KB default
    selectors: List[SelectorName] = field(default_factory=lambda: ["direct", "siblings", "imports", "symbols"])


@dataclass
class SelectedContextRef:
    """
    Lightweight reference chosen by a selector prior to materialization.

    No file contents; only path and selection metadata.
    """

    path: str  # normalized, repo-relative path
    selection_reason: str  # e.g. "direct:file", "sibling:directory", "import:neighbor", "symbol:hint:<hint>"
    selector: SelectorName
    priority: int  # lower values are applied earlier during dedup


@dataclass
class ContextItem:
    """
    Materialized context item with file contents.
    """

    path: str
    content: str
    byte_size: int
    selection_reason: str


@dataclass
class ContextBundleLimits:
    """
    Limits applied when building the context bundle.
    """

    max_files: int
    max_bytes: int
    truncated: bool


@dataclass
class ContextBundleProvenance:
    """
    Provenance information for auditing and replay.
    """

    root_path: str
    selectors: List[SelectorName]
    requested_files: List[str]
    symbol_hints: List[str]


@dataclass
class ContextBundle:
    """
    Final deterministic context bundle handed to the runtime orchestrator.
    """

    task_id: str
    revision: str
    created_at_utc: str
    items: List[ContextItem]
    limits: ContextBundleLimits
    provenance: ContextBundleProvenance

    @classmethod
    def now_utc(cls) -> str:
        """Return current time in ISO-8601 UTC form."""
        return datetime.now(timezone.utc).isoformat()


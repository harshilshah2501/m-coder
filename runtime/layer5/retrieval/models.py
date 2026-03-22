"""
Retrieval result shapes for A6 (no snippets — file-level hits only).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class RetrievalHit:
    """One ranked file from lexical retrieval."""

    relative_path: str
    score: int
    breakdown: Dict[str, int]
    """
    Integer components, e.g. ``path_substrings``, ``basename_substrings``, ``content_substrings``.
    Sum equals ``score`` (see ranking rules in ``lexical`` module).
    """


@dataclass(frozen=True)
class RetrievalResult:
    """Top-k lexical retrieval over an A4 ``WorkspaceFileIndex``."""

    query_raw: str
    query_tokens: Tuple[str, ...]
    top_k: int
    hits: Tuple[RetrievalHit, ...]
    index_schema_version: str
    workspace_identity_hash: str
    """
    Callers must not assume the index matches current disk (A4 full rebuild / staleness).
    """

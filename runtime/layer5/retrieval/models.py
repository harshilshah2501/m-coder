"""
Retrieval result shapes for A6 (no snippets — file-level hits only).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


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
    diagnostics: Optional[Dict[str, int]] = None
    """
    Optional per-component scores when ``LexicalRetrievalConfig.include_score_diagnostics`` is True.
    Not part of evidence_bundle schema; for audits and PR-6 analysis only.
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
    workspace_snapshot_hash: str = ""
    workspace_snapshot_source: str = "path_only"
    workspace_is_dirty: bool = False
    workspace_commit_sha: str = ""
    """
    Callers must not assume the index matches current disk (A4 full rebuild / staleness).
    """

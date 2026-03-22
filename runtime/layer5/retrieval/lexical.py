"""
Lexical-first retrieval over A4 ``WorkspaceFileIndex``.

Ranking rules (MVP, deterministic)
----------------------------------
Let ``tokens`` be query tokens (non-empty, lowercased alphanumeric runs).

For each indexed file:

1. **path_substrings**: ``sum(relative_path.lower().count(t) * weight_path for t in tokens)``
2. **basename_substrings**: ``sum(basename.lower().count(t) * weight_basename for t in tokens)``
   where ``basename`` is the final ``/`` segment of ``relative_path``.
3. **content_substrings** (if ``read_file_contents``): read at most ``max_content_bytes``
   from disk under ``index.canonical_root``, UTF-8 with ``errors="replace"``, then
   ``sum(text.lower().count(t) * weight_content for t in tokens)``.
   Missing/unreadable files contribute ``0``.

**Total score** = path_substrings + basename_substrings + content_substrings (all integers).

**Ordering**: descending by ``score``, ascending by ``relative_path`` (lexicographic, UTF-8).

**Empty query or no tokens**: all scores are ``0``; top-k is the first ``k`` files in
``relative_path`` order (matches A4 index order).

Symbol boost: **not used** — A4 v1 has no symbol field.

Staleness: this module does not verify index freshness; content reads use current disk.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from runtime.layer5.index.models import FileIndexEntry, WorkspaceFileIndex

from runtime.layer5.retrieval.config import LexicalRetrievalConfig
from runtime.layer5.retrieval.models import RetrievalHit, RetrievalResult
from runtime.layer5.retrieval.query import normalize_query


def _basename(rel: str) -> str:
    if "/" not in rel:
        return rel
    return rel.rsplit("/", 1)[-1]


def _content_score(
    root: Path,
    entry: FileIndexEntry,
    tokens: Tuple[str, ...],
    cfg: LexicalRetrievalConfig,
) -> int:
    if not tokens or not cfg.read_file_contents:
        return 0
    path = root / entry.relative_path
    try:
        data = path.read_bytes()[: cfg.max_content_bytes]
    except (OSError, PermissionError):
        return 0
    text = data.decode("utf-8", errors="replace").lower()
    return sum(text.count(t) * cfg.weight_content for t in tokens)


def _score_entry(
    entry: FileIndexEntry,
    tokens: Tuple[str, ...],
    root: Path,
    cfg: LexicalRetrievalConfig,
) -> RetrievalHit:
    if not tokens:
        return RetrievalHit(
            relative_path=entry.relative_path,
            score=0,
            breakdown={
                "path_substrings": 0,
                "basename_substrings": 0,
                "content_substrings": 0,
            },
        )

    rel_l = entry.relative_path.lower()
    base_l = _basename(entry.relative_path).lower()

    path_part = sum(rel_l.count(t) * cfg.weight_path for t in tokens)
    base_part = sum(base_l.count(t) * cfg.weight_basename for t in tokens)
    content_part = _content_score(root, entry, tokens, cfg)
    total = path_part + base_part + content_part
    return RetrievalHit(
        relative_path=entry.relative_path,
        score=total,
        breakdown={
            "path_substrings": path_part,
            "basename_substrings": base_part,
            "content_substrings": content_part,
        },
    )


def retrieve_lexical(
    index: WorkspaceFileIndex,
    query: str,
    top_k: int,
    config: Optional[LexicalRetrievalConfig] = None,
) -> RetrievalResult:
    """
    Return top-k files from ``index`` for ``query`` using MVP lexical rules.

    Args:
        index: A4 workspace file index (may be stale vs disk).
        query: Raw user query string.
        top_k: Maximum hits (non-negative).
        config: Optional lexical config.

    Returns:
        ``RetrievalResult`` with deterministic ``hits`` ordering.
    """
    cfg = config or LexicalRetrievalConfig()
    tokens = normalize_query(query, min_token_len=cfg.min_token_len)
    root = Path(index.canonical_root)

    if top_k <= 0:
        return RetrievalResult(
            query_raw=query,
            query_tokens=tokens,
            top_k=top_k,
            hits=(),
            index_schema_version=index.schema_version,
            workspace_identity_hash=index.workspace_identity_hash,
        )

    scored: List[RetrievalHit] = [_score_entry(e, tokens, root, cfg) for e in index.files]

    if not tokens:
        # Deterministic fallback: index.files is already sorted by relative_path
        chosen = tuple(
            RetrievalHit(
                relative_path=e.relative_path,
                score=0,
                breakdown={
                    "path_substrings": 0,
                    "basename_substrings": 0,
                    "content_substrings": 0,
                },
            )
            for e in index.files[:top_k]
        )
    else:
        scored.sort(key=lambda h: (-h.score, h.relative_path))
        chosen = tuple(scored[:top_k])

    return RetrievalResult(
        query_raw=query,
        query_tokens=tokens,
        top_k=top_k,
        hits=chosen,
        index_schema_version=index.schema_version,
        workspace_identity_hash=index.workspace_identity_hash,
    )

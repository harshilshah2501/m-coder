"""
A5 — Lexical retrieval over A4 file index (MVP).

Consumes ``WorkspaceFileIndex`` only; no symbol field, no graph, no embeddings.
See ``A6_HANDOFF.md`` for output contract and guarantees.
"""

from runtime.layer5.retrieval.config import LexicalRetrievalConfig
from runtime.layer5.retrieval.lexical import retrieve_lexical
from runtime.layer5.retrieval.models import RetrievalHit, RetrievalResult
from runtime.layer5.retrieval.query import normalize_query

__all__ = [
    "LexicalRetrievalConfig",
    "RetrievalHit",
    "RetrievalResult",
    "normalize_query",
    "retrieve_lexical",
]

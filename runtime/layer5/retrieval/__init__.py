"""
A5 — Lexical retrieval over A4 file index (MVP).

Consumes ``WorkspaceFileIndex`` only; no symbol field, no graph, no embeddings.
See ``A6_HANDOFF.md`` for output contract and guarantees.
"""

from runtime.layer5.retrieval.config import (
    LexicalRetrievalConfig,
    RETRIEVAL_POLICY_V1,
    RETRIEVAL_POLICY_V2,
    RETRIEVAL_POLICY_VERSION,
    get_retrieval_policy,
)
from runtime.layer5.retrieval.lexical import retrieve_lexical
from runtime.layer5.retrieval.models import RetrievalHit, RetrievalResult
from runtime.layer5.retrieval.policy import FilePolicy, classify_file, infer_file_subsystem, infer_query_subsystems
from runtime.layer5.retrieval.query import normalize_query

__all__ = [
    "LexicalRetrievalConfig",
    "RETRIEVAL_POLICY_V1",
    "RETRIEVAL_POLICY_V2",
    "RETRIEVAL_POLICY_VERSION",
    "get_retrieval_policy",
    "RetrievalHit",
    "RetrievalResult",
    "FilePolicy",
    "classify_file",
    "infer_file_subsystem",
    "infer_query_subsystems",
    "normalize_query",
    "retrieve_lexical",
]

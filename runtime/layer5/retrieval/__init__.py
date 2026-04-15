"""
A5 — Lexical retrieval over A4 file index (MVP).

Consumes ``WorkspaceFileIndex`` only; no symbol field, no graph, no embeddings.
See ``A6_HANDOFF.md`` for output contract and guarantees.

Any change to ranking logic must be validated via PR-6 audit suite on real repo
before merge.
"""

from runtime.layer5.retrieval.config import (
    LexicalRetrievalConfig,
    RETRIEVAL_POLICY_V1,
    RETRIEVAL_POLICY_V2,
    RETRIEVAL_POLICY_V3,
    RETRIEVAL_POLICY_V4,
    RETRIEVAL_POLICY_V5,
    RETRIEVAL_POLICY_VERSION,
    get_retrieval_policy,
)
from runtime.layer5.retrieval.lexical import retrieve_lexical
from runtime.layer5.retrieval.models import RetrievalHit, RetrievalResult
from runtime.layer5.retrieval.policy import (
    FilePolicy,
    classify_file,
    infer_code_debug_intent,
    infer_file_subsystem,
    infer_query_subsystems,
    is_generic_eventbus_java_handler,
    is_support_style_java_basename,
    query_ingestion_focus,
    query_topology_focus,
)
from runtime.layer5.retrieval.query import normalize_query
from runtime.layer5.retrieval.fusion import FusionConfig, fuse_and_filter, fusion_authority_note
from runtime.layer5.retrieval.effective_intent import EffectiveIntent, merge_effective_intent

__all__ = [
    "LexicalRetrievalConfig",
    "RETRIEVAL_POLICY_V1",
    "RETRIEVAL_POLICY_V2",
    "RETRIEVAL_POLICY_V3",
    "RETRIEVAL_POLICY_V4",
    "RETRIEVAL_POLICY_V5",
    "RETRIEVAL_POLICY_VERSION",
    "get_retrieval_policy",
    "RetrievalHit",
    "RetrievalResult",
    "FilePolicy",
    "classify_file",
    "infer_code_debug_intent",
    "infer_file_subsystem",
    "infer_query_subsystems",
    "is_generic_eventbus_java_handler",
    "is_support_style_java_basename",
    "query_ingestion_focus",
    "query_topology_focus",
    "normalize_query",
    "retrieve_lexical",
    "FusionConfig",
    "fuse_and_filter",
    "fusion_authority_note",
    "EffectiveIntent",
    "merge_effective_intent",
]

"""
Build evidence bundles (v1) from A5 retrieval output.

**Authority rule:** A5 ``RetrievalResult.hits`` order and per-hit ``score`` /
``breakdown`` are authoritative. A6 does not reinterpret ranking, rescore
candidates, or apply snippet-based heuristics to reorder or filter hits.
Snippet extraction only **grounds** each candidate in file text with a bounded,
deterministic span.

**Identity policy:** See ``identity_policy.py``. Default strict mode raises
``IdentityMismatchError`` when retrieval and index workspace hashes differ.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from runtime.layer5.index.models import WorkspaceFileIndex
from runtime.layer5.retrieval.models import RetrievalResult

from runtime.layer5.evidence.config import SnippetConfig
from runtime.layer5.evidence.identity_policy import IdentityMismatchError
from runtime.layer5.evidence.models import SCHEMA_HINT, EvidenceBundle, EvidenceEntry
from runtime.layer5.evidence.snippet import extract_snippet


A5_AUTHORITY_NOTE = (
    "Candidate order and retrieval_score come from A5 lexical retrieval only; "
    "A6 must not rescore or reorder based on snippets."
)


def build_evidence_bundle(
    retrieval: RetrievalResult,
    index: WorkspaceFileIndex,
    *,
    snippet_config: Optional[SnippetConfig] = None,
    require_identity_match: bool = True,
) -> EvidenceBundle:
    """
    Produce an ``EvidenceBundle`` (v1) for one A5 result and its source index.

    Args:
        retrieval: A5 output (typically from ``retrieve_lexical``).
        index: A4 index that was used to build ``retrieval`` (same workspace snapshot).
        snippet_config: Optional snippet window / read cap.
        require_identity_match: If True, raise ``IdentityMismatchError`` when
            ``retrieval.workspace_identity_hash != index.workspace_identity_hash``.
            If False, skip the check (caller assumes responsibility).

    Raises:
        IdentityMismatchError: Strict identity mismatch (see ``identity_policy``).
    """
    if require_identity_match and retrieval.workspace_identity_hash != index.workspace_identity_hash:
        raise IdentityMismatchError(retrieval.workspace_identity_hash, index.workspace_identity_hash)

    cfg = snippet_config or SnippetConfig()
    root = Path(index.canonical_root)
    entries: Tuple[EvidenceEntry, ...] = tuple(
        EvidenceEntry.from_hit(
            rank=rank,
            relative_path=hit.relative_path,
            retrieval_score=hit.score,
            retrieval_breakdown=hit.breakdown,
            span=extract_snippet(
                canonical_root=root,
                relative_path=hit.relative_path,
                query_tokens=retrieval.query_tokens,
                config=cfg,
            ),
        )
        for rank, hit in enumerate(retrieval.hits)
    )

    return EvidenceBundle(
        provisional=False,
        schema_hint=SCHEMA_HINT,
        query_raw=retrieval.query_raw,
        query_tokens=retrieval.query_tokens,
        top_k=retrieval.top_k,
        index_schema_version=retrieval.index_schema_version,
        workspace_identity_hash=retrieval.workspace_identity_hash,
        canonical_root=str(root),
        entries=entries,
        a5_authority_note=A5_AUTHORITY_NOTE,
    )

"""
Evidence bundle types for ``layer5.evidence_bundle.v1`` (frozen contract surface).

A6 copies A5 scores and breakdown verbatim and preserves hit order.
Do not rescore or reorder based on snippet content.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from runtime.layer5.evidence.snippet import SnippetSpan


SCHEMA_HINT = "layer5.evidence_bundle.v1"


@dataclass(frozen=True)
class EvidenceEntry:
    """One retrieval candidate grounded with a bounded snippet (v1)."""

    provisional: bool
    rank: int
    relative_path: str
    retrieval_score: int
    retrieval_breakdown: Dict[str, int]
    snippet_text: str
    start_line: int
    end_line: int
    start_byte_utf8: int
    end_byte_utf8: int
    anchor_line: int
    matched_tokens: Tuple[str, ...]
    snippet_selection_reason: str
    truncated_by_max_bytes: bool

    @classmethod
    def from_hit(
        cls,
        *,
        rank: int,
        relative_path: str,
        retrieval_score: int,
        retrieval_breakdown: Dict[str, int],
        span: SnippetSpan,
    ) -> "EvidenceEntry":
        return cls(
            provisional=False,
            rank=rank,
            relative_path=relative_path,
            retrieval_score=retrieval_score,
            retrieval_breakdown=dict(retrieval_breakdown),
            snippet_text=span.text,
            start_line=span.start_line,
            end_line=span.end_line,
            start_byte_utf8=span.start_byte_utf8,
            end_byte_utf8=span.end_byte_utf8,
            anchor_line=span.anchor_line,
            matched_tokens=span.matched_tokens,
            snippet_selection_reason=span.selection_reason.value,
            truncated_by_max_bytes=span.truncated_by_max_bytes,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provisional": self.provisional,
            "rank": self.rank,
            "relative_path": self.relative_path,
            "retrieval_score": self.retrieval_score,
            "retrieval_breakdown": dict(sorted(self.retrieval_breakdown.items())),
            "snippet": {
                "text": self.snippet_text,
                "start_line": self.start_line,
                "end_line": self.end_line,
                "start_byte_utf8": self.start_byte_utf8,
                "end_byte_utf8": self.end_byte_utf8,
                "anchor_line": self.anchor_line,
                "matched_tokens": list(self.matched_tokens),
                "selection_reason": self.snippet_selection_reason,
                "truncated_by_max_bytes": self.truncated_by_max_bytes,
            },
        }


@dataclass(frozen=True)
class EvidenceBundle:
    """Bundle over one A5 ``RetrievalResult`` (same candidate order), v1 contract."""

    provisional: bool
    schema_hint: str
    query_raw: str
    query_tokens: Tuple[str, ...]
    top_k: int
    index_schema_version: str
    workspace_identity_hash: str
    canonical_root: str
    entries: Tuple[EvidenceEntry, ...]
    a5_authority_note: str
    authority_resolution: Optional[Dict[str, Any]] = None
    owner_evidence: Tuple[Dict[str, Any], ...] = ()
    structural_context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "provisional": self.provisional,
            "schema_hint": self.schema_hint,
            "query_raw": self.query_raw,
            "query_tokens": list(self.query_tokens),
            "top_k": self.top_k,
            "index_schema_version": self.index_schema_version,
            "workspace_identity_hash": self.workspace_identity_hash,
            "canonical_root": self.canonical_root,
            "a5_authority_note": self.a5_authority_note,
            "entries": [e.to_dict() for e in self.entries],
        }
        if self.authority_resolution is not None:
            d["authority_resolution"] = self.authority_resolution
        if self.owner_evidence:
            d["owner_evidence"] = list(self.owner_evidence)
        if self.structural_context is not None:
            d["structural_context"] = self.structural_context
        return d

    def to_json(self, *, sort_keys: bool = True) -> str:
        return json.dumps(self.to_dict(), sort_keys=sort_keys, separators=(",", ":"))

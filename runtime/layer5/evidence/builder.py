"""
Build evidence bundles (v1) from A5 retrieval output.

**Authority rule:** ``RetrievalResult.hits`` order and per-hit ``score`` /
``breakdown`` are authoritative (lexical-only or post-Stage-B fusion). A6 does
not reorder or rescore based on snippet content. Snippet extraction only
**grounds** each candidate in file text with a bounded, deterministic span.

**Identity policy:** See ``identity_policy.py``. Default strict mode raises
``IdentityMismatchError`` when retrieval and index workspace hashes differ.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from runtime.layer5.index.models import WorkspaceFileIndex
from runtime.layer5.retrieval.models import RetrievalResult
from runtime.layer5.retrieval.roles import DISTRACTOR_RISK, SUPPORTING_CONTEXT

from runtime.layer5.evidence.config import SnippetConfig
from runtime.layer5.evidence.executable_snippet_signals import text_has_executable_control_flow
from runtime.layer5.evidence.identity_policy import IdentityMismatchError
from runtime.layer5.evidence.models import SCHEMA_HINT, EvidenceBundle, EvidenceEntry
from runtime.layer5.evidence.snippet import (
    extract_snippet,
    extract_snippet_executable_rescue,
    extract_snippet_method_anchor_rescue,
)
from runtime.layer5.retrieval.path_resolve import paths_match_workspace


A5_AUTHORITY_NOTE = (
    "Candidate order and retrieval_score come from A5 lexical retrieval only; "
    "A6 must not rescore or reorder based on snippets."
)


def _norm_rel(path: str) -> str:
    return path.replace("\\", "/").strip().lower()


def build_evidence_bundle(
    retrieval: RetrievalResult,
    index: WorkspaceFileIndex,
    *,
    snippet_config: Optional[SnippetConfig] = None,
    require_identity_match: bool = True,
    authority_resolution: Optional[Dict[str, Any]] = None,
    structural_context: Optional[Dict[str, Any]] = None,
    owner_evidence: Optional[Tuple[Dict[str, Any], ...]] = None,
    role_by_path: Optional[Mapping[str, str]] = None,
    authority_note: Optional[str] = None,
    fusion_diagnostics: Optional[Dict[str, Any]] = None,
    evidence_quality: Optional[str] = None,
    debug_snippet_rescue_selected_file: Optional[str] = None,
    owner_method_rescue_hints_by_path: Optional[Mapping[str, Tuple[str, ...]]] = None,
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

    ``debug_snippet_rescue_selected_file``: when set, for hits whose path matches that
    workspace-relative selected file, replace a primary snippet that lacks executable
    control-flow with the first top-down CF-rescue window (see ``snippet.py``).
    ``owner_method_rescue_hints_by_path``: optional Ask proof-density rescue map
    from owner path -> method hints; when primary snippet misses those hints,
    re-anchor on first method-hint line in that file (no rescoring/reordering).
    """
    if require_identity_match and retrieval.workspace_identity_hash != index.workspace_identity_hash:
        raise IdentityMismatchError(retrieval.workspace_identity_hash, index.workspace_identity_hash)

    cfg = snippet_config or SnippetConfig()
    root = Path(index.canonical_root)
    roles = dict(role_by_path) if role_by_path else {}
    rescue_sel = (debug_snippet_rescue_selected_file or "").strip()
    owner_rescue = dict(owner_method_rescue_hints_by_path or {})

    def _rescue_hints_for_hit(rel_path: str) -> Tuple[str, ...]:
        for p, hints in owner_rescue.items():
            if paths_match_workspace(rel_path, str(p)):
                hs = tuple(str(h).strip() for h in (hints or ()) if str(h).strip())
                if hs:
                    return hs
        return ()

    built: list[EvidenceEntry] = []
    for rank, hit in enumerate(retrieval.hits):
        span = extract_snippet(
            canonical_root=root,
            relative_path=hit.relative_path,
            query_tokens=retrieval.query_tokens,
            config=cfg,
        )
        if rescue_sel and paths_match_workspace(hit.relative_path, rescue_sel):
            if not text_has_executable_control_flow(span.text):
                alt = extract_snippet_executable_rescue(
                    canonical_root=root,
                    relative_path=hit.relative_path,
                    config=cfg,
                )
                if alt is not None and text_has_executable_control_flow(alt.text):
                    span = alt
        owner_hints = _rescue_hints_for_hit(hit.relative_path)
        if owner_hints and not any(h in span.text for h in owner_hints):
            mres = extract_snippet_method_anchor_rescue(
                canonical_root=root,
                relative_path=hit.relative_path,
                method_hints=owner_hints,
                config=cfg,
            )
            if mres is not None:
                span = mres
        built.append(
            EvidenceEntry.from_hit(
                rank=rank,
                relative_path=hit.relative_path,
                retrieval_score=hit.score,
                retrieval_breakdown=hit.breakdown,
                span=span,
                retrieval_role=roles.get(hit.relative_path, ""),
            )
        )
    entries: Tuple[EvidenceEntry, ...] = tuple(built)

    supporting_paths = tuple(
        p for p, r in roles.items() if r == SUPPORTING_CONTEXT
    )
    distractor_paths = tuple(p for p, r in roles.items() if r == DISTRACTOR_RISK)

    oe: Tuple[Dict[str, Any], ...]
    if owner_evidence is not None:
        oe = owner_evidence
    elif authority_resolution:
        po = authority_resolution.get("primary_owner") or {}
        pf = str(po.get("file") or "").strip()
        if pf:
            target = _norm_rel(pf)
            oe = tuple(e.to_dict() for e in entries if _norm_rel(e.relative_path) == target)
        else:
            oe = ()
    else:
        oe = ()

    note = authority_note if authority_note is not None else A5_AUTHORITY_NOTE

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
        a5_authority_note=note,
        authority_resolution=authority_resolution,
        owner_evidence=oe,
        structural_context=structural_context,
        fusion_diagnostics=fusion_diagnostics,
        evidence_quality=evidence_quality,
        supporting_evidence_paths=supporting_paths,
        distractor_paths=distractor_paths,
        workspace_snapshot_hash=getattr(retrieval, "workspace_snapshot_hash", "") or "",
        workspace_snapshot_source=getattr(retrieval, "workspace_snapshot_source", "path_only") or "path_only",
        workspace_is_dirty=bool(getattr(retrieval, "workspace_is_dirty", False)),
        workspace_commit_sha=getattr(retrieval, "workspace_commit_sha", "") or "",
    )

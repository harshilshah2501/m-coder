"""
Shared Layer-5 evidence export API for Context Layer service and CLI.

Does not change retrieval or evidence semantics — delegates to existing L5 modules.
"""

from __future__ import annotations

from typing import Any, Dict


def export_evidence_bundle_dict(
    workspace_root: str,
    query: str,
    top_k: int = 8,
) -> Dict[str, Any]:
    """
    Build ``layer5.evidence_bundle.v1`` as a plain dict.

    Raises:
        ValueError: empty workspace/query or invalid top_k.
        RuntimeError: workspace resolve / index / retrieval failures (message only).
    """
    w = workspace_root.strip()
    q = query.strip()
    if not w or not q:
        raise ValueError("workspace_root and query must be non-empty")
    if top_k < 1 or top_k > 64:
        raise ValueError("top_k must be between 1 and 64")

    from runtime.layer5.evidence import build_evidence_bundle
    from runtime.layer5.index import build_file_index
    from runtime.layer5.retrieval import LexicalRetrievalConfig, retrieve_lexical
    from runtime.layer5.workspace.resolver import ResolverConfig, WorkspaceResolver

    resolver = WorkspaceResolver(ResolverConfig())
    identity, err = resolver.resolve(w)
    if err:
        raise RuntimeError(f"workspace resolve failed: {err.message}")
    try:
        idx = build_file_index(identity)
    except (OSError, FileNotFoundError, NotADirectoryError) as e:
        raise RuntimeError(f"index build failed: {e}") from e
    r = retrieve_lexical(idx, q, top_k, LexicalRetrievalConfig())
    evb = build_evidence_bundle(r, idx)
    return evb.to_dict()

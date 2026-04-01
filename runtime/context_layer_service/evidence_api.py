"""
Shared Layer-5 evidence export API for Context Layer service and CLI.

Does not change retrieval or evidence semantics — delegates to existing L5 modules.
"""

from __future__ import annotations

from pathlib import Path
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

    authority_resolution = None
    structural_context = None
    try:
        from runtime.layer5.authority.authority_evidence import (
            build_authority_resolution,
            build_structural_context_stub,
            match_concepts_for_query,
        )
        from runtime.layer5.authority.code_index_adapter import create_adapter
        from runtime.layer5.authority.code_index_builder import build_index
        from runtime.layer5.authority.registry_loader import load_registry

        reg_path = Path(__file__).resolve().parents[1] / "layer5" / "authority" / "product_authority_registry.yaml"
        registry = load_registry(reg_path)
        adapter = None
        try:
            adapter = create_adapter(code_index=build_index(Path(w)))
        except Exception:
            adapter = None
        authority_resolution = build_authority_resolution(q, registry, adapter)
        if authority_resolution and adapter:
            mm = match_concepts_for_query(q, registry)
            if mm:
                structural_context = build_structural_context_stub(mm[0][0], adapter)
    except Exception:
        authority_resolution = None
        structural_context = None

    evb = build_evidence_bundle(
        r,
        idx,
        authority_resolution=authority_resolution,
        structural_context=structural_context,
    )
    return evb.to_dict()

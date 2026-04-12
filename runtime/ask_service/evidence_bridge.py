"""
Ask-side bridge: build layer5.evidence_bundle.v1 using existing L5 modules (no L5 edits).

Used when the client sets ask_request.evidence_first=true. Workspace path must exist
on this host (WSL) or ASK_DEFAULT_REPO_ROOT must point at a valid tree.
"""

from __future__ import annotations

import logging
from pathlib import Path

from typing import Any, Dict, List, Optional, Tuple

from runtime.context.contracts import (
    ContextBundle,
    ContextBundleLimits,
    ContextBundleProvenance,
    ContextItem,
)

LOG = logging.getLogger(__name__)


def resolve_workspace_input_path(repo_root: str) -> Optional[str]:
    """
    Return a directory path suitable for WorkspaceResolver.resolve(), or None.
    Uses the same existence rules as Ask (real path or ASK_DEFAULT_REPO_ROOT).
    """
    raw = (repo_root or "").strip() or "."
    root = Path(raw).resolve()
    if root.exists() and root.is_dir():
        return str(root)
    import os

    default = os.environ.get("ASK_DEFAULT_REPO_ROOT", "").strip()
    if default:
        p = Path(default).resolve()
        if p.exists() and p.is_dir():
            return str(p)
    return None


def try_build_layer5_evidence(
    workspace_input_path: str,
    query: str,
    request_id: str,
    revision_for_bundle: str,
    top_k: int = 8,
) -> Optional[Tuple[Dict[str, Any], ContextBundle]]:
    """
    Resolve workspace, index, retrieve, evidence bundle. Returns (evidence to_dict, ContextBundle) or None.
    """
    from runtime.layer5.evidence import build_evidence_bundle
    from runtime.layer5.index import build_file_index
    from runtime.layer5.retrieval import LexicalRetrievalConfig, retrieve_lexical
    from runtime.layer5.workspace.resolver import ResolverConfig, WorkspaceResolver

    resolver = WorkspaceResolver(ResolverConfig())
    identity, err = resolver.resolve(workspace_input_path)
    if err:
        LOG.info("[ASK evidence_first] workspace resolve failed: %s", err.message)
        return None
    try:
        idx = build_file_index(identity)
    except (OSError, FileNotFoundError, NotADirectoryError) as e:
        LOG.info("[ASK evidence_first] index build failed: %s", e)
        return None
    r = retrieve_lexical(idx, query, top_k, LexicalRetrievalConfig())

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
            adapter = create_adapter(code_index=build_index(Path(workspace_input_path)))
        except Exception:
            adapter = None
        authority_resolution = build_authority_resolution(query, registry, adapter)
        if authority_resolution and adapter:
            mm = match_concepts_for_query(query, registry)
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
    rev = (revision_for_bundle or "").strip() or "unknown-revision"
    ctx = context_bundle_from_evidence(evb, task_id=request_id or "ask-task", revision=rev)
    return evb.to_dict(), ctx


def context_bundle_from_evidence(evb, task_id: str, revision: str) -> ContextBundle:
    """Map EvidenceBundle entries to ContextBundle (snippet text as item content)."""
    rev = revision or "unknown-revision"
    items: List[ContextItem] = []
    for ent in evb.entries:
        text = ent.snippet_text or ""
        items.append(
            ContextItem(
                path=ent.relative_path,
                content=text,
                byte_size=len(text.encode("utf-8")),
                selection_reason=ent.snippet_selection_reason,
            )
        )
    lim = ContextBundleLimits(max_files=len(items), max_bytes=sum(i.byte_size for i in items), truncated=False)
    prov = ContextBundleProvenance(
        root_path=evb.canonical_root,
        selectors=["layer5:evidence_bundle.v1"],
        requested_files=[e.relative_path for e in evb.entries],
        symbol_hints=list(evb.query_tokens),
    )
    from datetime import datetime, timezone

    return ContextBundle(
        task_id=task_id,
        revision=rev,
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        items=items,
        limits=lim,
        provenance=prov,
    )


def context_bundle_from_evidence_dict(
    evidence: Dict[str, Any],
    task_id: str,
    revision: str,
) -> ContextBundle:
    """
    Build a ``ContextBundle`` from a validated ``layer5.evidence_bundle.v1`` dict.

    No filesystem reads — snippet text is taken from the bundle only (A8 / Plan-Gate path).
    """
    from datetime import datetime, timezone

    rev = (revision or "").strip() or "unknown-revision"
    entries = evidence.get("entries") or []
    items: List[ContextItem] = []
    if not isinstance(entries, list):
        entries = []
    for ent in entries:
        if not isinstance(ent, dict):
            continue
        rel = str(ent.get("relative_path") or "")
        sn = ent.get("snippet")
        sn = sn if isinstance(sn, dict) else {}
        text = str(sn.get("text") or "")
        sr = str(sn.get("selection_reason") or "")
        items.append(
            ContextItem(
                path=rel,
                content=text,
                byte_size=len(text.encode("utf-8")),
                selection_reason=sr,
            )
        )
    lim = ContextBundleLimits(
        max_files=len(items),
        max_bytes=sum(i.byte_size for i in items),
        truncated=False,
    )
    qt = evidence.get("query_tokens") or []
    symbol_hints: List[str] = [str(x) for x in qt] if isinstance(qt, list) else []
    paths = [str(e.get("relative_path") or "") for e in entries if isinstance(e, dict)]
    prov = ContextBundleProvenance(
        root_path=str(evidence.get("canonical_root") or ""),
        selectors=["plan_gate:v1_ask:evidence_bundle.v1"],
        requested_files=paths,
        symbol_hints=symbol_hints,
    )
    return ContextBundle(
        task_id=task_id,
        revision=rev,
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        items=items,
        limits=lim,
        provenance=prov,
    )

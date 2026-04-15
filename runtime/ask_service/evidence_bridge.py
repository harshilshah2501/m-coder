"""
Ask-side bridge: build layer5.evidence_bundle.v1 using existing L5 modules.

Pipeline: retrieve_lexical → fuse_and_filter (Stage B) → build_evidence_bundle → quality gate.
"""

from __future__ import annotations

import logging
from dataclasses import replace
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
            return str(default)
    return None


def try_build_layer5_evidence(
    workspace_input_path: str,
    query: str,
    request_id: str,
    revision_for_bundle: str,
    top_k: int = 8,
    *,
    task_type: str = "general",
    selected_file: Optional[str] = None,
) -> Optional[Tuple[Dict[str, Any], ContextBundle]]:
    """
    Resolve workspace, index, retrieve, fusion (Stage B), evidence bundle. Returns (evidence to_dict, ContextBundle) or None.
    """
    from runtime.layer5.evidence import build_evidence_bundle
    from runtime.layer5.evidence.models import EvidenceBundle
    from runtime.layer5.index import build_file_index
    from runtime.layer5.retrieval import LexicalRetrievalConfig, retrieve_lexical
    from runtime.layer5.retrieval.effective_intent import merge_effective_intent
    from runtime.layer5.retrieval.fusion import (
        FusionConfig,
        fuse_and_filter,
        fusion_authority_note,
        hard_filter_only,
    )
    from runtime.layer5.retrieval.quality_gate import assess_evidence_quality
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

    effective = merge_effective_intent(task_type, query)

    authority_resolution = None
    structural_context = None
    adapter = None
    registry = None
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
        registry = None
        adapter = None

    r = retrieve_lexical(
        idx,
        query,
        top_k,
        LexicalRetrievalConfig(),
        task_type=task_type,
        selected_file=selected_file,
        active_file=selected_file,
        authority_resolution=authority_resolution if isinstance(authority_resolution, dict) else None,
    )

    fusion_diag: Dict[str, Any] = {}
    roles_map: Dict[str, str] = {}
    if registry is not None:
        fused, fusion_diag, role_objs = fuse_and_filter(
            r,
            effective_intent=effective,
            registry=registry,
            code_index_adapter=adapter,
            selected_file=selected_file,
            fusion_config=FusionConfig(),
            index=idx,
            authority_resolution=authority_resolution if isinstance(authority_resolution, dict) else None,
        )
        r = fused
        roles_map = {p: ra.role for p, ra in role_objs.items()}
    else:
        owner_file = None
        if isinstance(authority_resolution, dict):
            po = authority_resolution.get("primary_owner")
            if isinstance(po, dict):
                owner_file = str(po.get("file") or "").strip() or None
        filtered, fusion_diag, role_objs = hard_filter_only(
            r,
            fusion_config=FusionConfig(),
            owner_path=owner_file,
            selected_file=selected_file,
            collaborator_paths=set(),
        )
        r = filtered
        roles_map = {p: ra.role for p, ra in role_objs.items()}

    evb = build_evidence_bundle(
        r,
        idx,
        authority_resolution=authority_resolution,
        structural_context=structural_context,
        role_by_path=roles_map if roles_map else None,
        authority_note=fusion_authority_note() if registry is not None else None,
        fusion_diagnostics=fusion_diag if fusion_diag else None,
    )

    paths = [e.relative_path for e in evb.entries]
    grounding = [
        (e.relative_path, e.snippet_selection_reason, e.retrieval_role or "")
        for e in evb.entries
    ]
    qa = assess_evidence_quality(
        query,
        paths,
        grounding_entries=grounding,
        effective_intent=effective,
    )
    fd = dict(evb.fusion_diagnostics or {})
    if r.stage_a_meta is not None:
        fd["stage_a_meta"] = r.stage_a_meta
    fd["effective_intent"] = {
        "primary_mode": effective.primary_mode,
        "task_type": effective.task_type_raw,
        "conflicts": list(effective.conflicts),
    }
    fd["quality_reasons"] = list(qa.quality_reasons)
    evb_final = replace(
        evb,
        evidence_quality=qa.evidence_quality,
        fusion_diagnostics=fd,
    )

    rev = (revision_for_bundle or "").strip() or "unknown-revision"
    ctx = context_bundle_from_evidence(evb_final, task_id=request_id or "ask-task", revision=rev)
    return evb_final.to_dict(), ctx


def context_bundle_from_evidence(evb: EvidenceBundle, task_id: str, revision: str) -> ContextBundle:
    """Map EvidenceBundle entries to ContextBundle (snippet text as item content)."""
    rev = revision or "unknown-revision"
    items: List[ContextItem] = []
    for ent in evb.entries:
        text = ent.snippet_text or ""
        sr = ent.snippet_selection_reason
        if ent.retrieval_role:
            sr = f"{sr}; role={ent.retrieval_role}"
        items.append(
            ContextItem(
                path=ent.relative_path,
                content=text,
                byte_size=len(text.encode("utf-8")),
                selection_reason=sr,
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

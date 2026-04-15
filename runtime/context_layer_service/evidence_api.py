"""
Shared Layer-5 evidence export API for Context Layer service and CLI.

Does not change retrieval or evidence semantics — delegates to existing L5 modules.
"""

from __future__ import annotations

import time
import os
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

# Forward type for callers that already built a lexical index (e.g. Stage 2 runner).
_FileIndex = Any

if TYPE_CHECKING:
    from runtime.layer5.authority.code_index_models import CodeIndex


def _code_index_enabled() -> bool:
    """Return True when authority code-index build is enabled for exports."""
    raw = str(os.environ.get("MOTADATA_CONTEXT_DISABLE_CODE_INDEX", "")).strip().lower()
    return raw not in {"1", "true", "yes", "on"}


def export_evidence_bundle_dict(
    workspace_root: str,
    query: str,
    top_k: int = 8,
    *,
    file_index: Optional[_FileIndex] = None,
    authority_adapter: Optional[Any] = None,
    index_cache: Optional[Any] = None,
    index_cache_metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build ``layer5.evidence_bundle.v1`` as a plain dict.

    Optional ``file_index`` and ``authority_adapter`` avoid rebuilding the lexical
    index and authority code index on every call (batch / trace export).

    Optional ``index_cache`` (``WorkspaceIndexCache``) reuses file + code index for
    the same workspace snapshot key (service latency only). Ignored when
    ``file_index`` is set. When ``index_cache_metrics`` is provided, it is updated
    with ``index_cache_hit``, ``file_index_build_ms``, and ``code_index_build_ms``.

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

    authority_code_index: Optional["CodeIndex"] = None
    authority_code_index_attempted = False
    code_index_enabled = _code_index_enabled()

    if file_index is not None:
        idx = file_index
    else:
        resolver = WorkspaceResolver(ResolverConfig())
        identity, err = resolver.resolve(w)
        if err:
            raise RuntimeError(f"workspace resolve failed: {err.message}")

        use_snapshot_cache = index_cache is not None
        if use_snapshot_cache:
            from runtime.context_layer_service.workspace_index_cache import (
                WorkspaceIndexCache,
            )

            cacheable = WorkspaceIndexCache.is_cacheable(identity)
            if cacheable:
                key = WorkspaceIndexCache.key_from_identity(identity)

                def _build_pair():
                    t0 = time.perf_counter()
                    try:
                        fi = build_file_index(identity)
                    except (OSError, FileNotFoundError, NotADirectoryError) as e:
                        raise RuntimeError(f"index build failed: {e}") from e
                    t1 = time.perf_counter()
                    ci: Optional["CodeIndex"] = None
                    t2 = t1
                    if code_index_enabled:
                        try:
                            from runtime.layer5.authority.code_index_builder import (
                                build_index,
                            )

                            ci = build_index(Path(w))
                        except Exception:
                            ci = None
                    t2 = time.perf_counter()
                    return (
                        fi,
                        ci,
                        {
                            "file_index_build_ms": (t1 - t0) * 1000.0,
                            "code_index_build_ms": (t2 - t1) * 1000.0,
                        },
                    )

                fi2, ci2, m = index_cache.get_or_build(key, _build_pair)
                idx = fi2
                authority_code_index = ci2
                authority_code_index_attempted = True
                if index_cache_metrics is not None:
                    index_cache_metrics.update(m)
            else:
                t0 = time.perf_counter()
                try:
                    idx = build_file_index(identity)
                except (OSError, FileNotFoundError, NotADirectoryError) as e:
                    raise RuntimeError(f"index build failed: {e}") from e
                t1 = time.perf_counter()
                if code_index_enabled:
                    try:
                        from runtime.layer5.authority.code_index_builder import build_index

                        t2 = time.perf_counter()
                        authority_code_index = build_index(Path(w))
                        t3 = time.perf_counter()
                        ci_ms = (t3 - t2) * 1000.0
                    except Exception:
                        authority_code_index = None
                        t3 = time.perf_counter()
                        ci_ms = (t3 - t2) * 1000.0
                else:
                    t2 = time.perf_counter()
                    authority_code_index = None
                    t3 = time.perf_counter()
                    ci_ms = (t3 - t2) * 1000.0
                authority_code_index_attempted = True
                if index_cache_metrics is not None:
                    index_cache_metrics.update(
                        {
                            "index_cache_hit": False,
                            "file_index_build_ms": (t1 - t0) * 1000.0,
                            "code_index_build_ms": ci_ms,
                        }
                    )
        else:
            try:
                idx = build_file_index(identity)
            except (OSError, FileNotFoundError, NotADirectoryError) as e:
                raise RuntimeError(f"index build failed: {e}") from e

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
        adapter = authority_adapter
        if adapter is None:
            if authority_code_index_attempted:
                if authority_code_index is not None:
                    try:
                        adapter = create_adapter(code_index=authority_code_index)
                    except Exception:
                        adapter = None
                else:
                    adapter = None
            else:
                if code_index_enabled:
                    try:
                        adapter = create_adapter(code_index=build_index(Path(w)))
                    except Exception:
                        adapter = None
                else:
                    adapter = None
        authority_resolution = build_authority_resolution(q, registry, adapter)
        if authority_resolution and adapter:
            mm = match_concepts_for_query(q, registry)
            if mm:
                structural_context = build_structural_context_stub(mm[0][0], adapter)
    except Exception:
        authority_resolution = None
        structural_context = None

    # Authority before lexical (Stage A owner injection); matches ask evidence_bridge ordering.
    r = retrieve_lexical(
        idx,
        q,
        top_k,
        LexicalRetrievalConfig(),
        task_type="general",
        selected_file=None,
        authority_resolution=authority_resolution if isinstance(authority_resolution, dict) else None,
    )

    fusion_diag: Optional[Dict[str, Any]] = None
    if getattr(r, "stage_a_meta", None) is not None:
        fusion_diag = {"stage_a_meta": r.stage_a_meta}

    evb = build_evidence_bundle(
        r,
        idx,
        authority_resolution=authority_resolution,
        structural_context=structural_context,
        fusion_diagnostics=fusion_diag,
    )
    return evb.to_dict()

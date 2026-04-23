"""
Shared Layer-5 evidence export API for Context Layer service and CLI.

Does not change retrieval or evidence semantics — delegates to existing L5 modules.
"""

from __future__ import annotations

import logging
import time
import os
import re
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


def _extract_method_hints(query: str, selected_file: Optional[str], cap: int = 8) -> list[str]:
    """
    Method / symbol hints for EXPLAIN_DEBUG diagnostics.

    Prefer camelCase/PascalCase identifiers (beforeUpdate, AbstractConfigStore), the
    selected file's type basename, and a tiny allowlist of common debug verbs (parse, dispatch).
    Avoid single generic tokens like \"before\" from \"before alert\".
    """
    raw = str(query or "").replace(".", " ").replace(":", " ")
    out: list[str] = []
    seen: set[str] = set()

    blocked = {
        "debug",
        "trace",
        "branch",
        "branches",
        "condition",
        "conditions",
        "method",
        "methods",
        "failure",
        "failures",
        "selected",
        "file",
        "path",
        "class",
        "null",
        "return",
        "returns",
        "before",
        "after",
        "updates",
        "update",
        "alert",
        "alerts",
    }

    def add(tok: str) -> None:
        if not tok or len(tok) < 3:
            return
        tl = tok.lower()
        if tl in blocked:
            return
        if tl in seen:
            return
        seen.add(tl)
        out.append(tok)

    # camelCase method names: beforeUpdate, getItem
    for m in re.finditer(r"\b[a-z][a-z0-9]*(?:[A-Z][a-z0-9]*)+\b", raw):
        add(m.group(0))
        if len(out) >= cap:
            return out[:cap]

    # PascalCase types: AbstractConfigStore, AvailabilityCorrelationEngine
    for m in re.finditer(r"\b[A-Z][a-z]+(?:[A-Z][a-z0-9]*)+\b", raw):
        add(m.group(0))
        if len(out) >= cap:
            return out[:cap]

    # Selected Java/Kotlin basename as a structural anchor
    if selected_file:
        base = Path(str(selected_file).replace("\\", "/")).name
        for suf in (".java", ".kt", ".py"):
            if base.endswith(suf):
                add(base[: -len(suf)])
                break

    # Short verb anchors often used in debug selections (never single-letter glue words)
    raw_l = raw.lower()
    for verb, canon in (("parse", "parse"), ("dispatch", "dispatch")):
        if re.search(rf"\b{re.escape(verb)}\b", raw_l):
            add(canon)
        if len(out) >= cap:
            return out[:cap]

    return out[:cap]


def _selected_method_body_present(
    bundle_dict: Dict[str, Any],
    selected_file: Optional[str],
    method_hints: list[str],
) -> Optional[bool]:
    """
    Determine whether selected-file snippets contain any requested method-like tokens.
    Returns None when check is not applicable (no selected_file or no hints).
    """
    sel = str(selected_file or "").replace("\\", "/").strip().lower()
    if not sel or not method_hints:
        return None
    entries = bundle_dict.get("entries")
    if not isinstance(entries, list):
        return False
    base = sel.split("/")[-1]
    selected_text_parts: list[str] = []
    for ent in entries:
        if not isinstance(ent, dict):
            continue
        rp = str(ent.get("relative_path") or "").replace("\\", "/").strip().lower()
        if not rp:
            continue
        if rp == sel or rp.endswith("/" + base) or rp.endswith(base):
            sn = ent.get("snippet")
            sn = sn if isinstance(sn, dict) else {}
            selected_text_parts.append(str(sn.get("text") or ""))
    if not selected_text_parts:
        return False
    hay = "\n".join(selected_text_parts)
    for h in method_hints:
        # Accept declaration/call-like or direct identifier mention in selected snippet window.
        if re.search(rf"\b{re.escape(h)}\s*\(", hay) or re.search(rf"\b{re.escape(h)}\b", hay):
            return True
    return False


def export_evidence_bundle_dict(
    workspace_root: str,
    query: str,
    top_k: int = 8,
    *,
    task_type: str = "general",
    selected_file: Optional[str] = None,
    active_file: Optional[str] = None,
    file_index: Optional[_FileIndex] = None,
    authority_adapter: Optional[Any] = None,
    index_cache: Optional[Any] = None,
    index_cache_metrics: Optional[Dict[str, Any]] = None,
    enable_stage_a_v2: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Build ``layer5.evidence_bundle.v1`` as a plain dict.

    Optional ``file_index`` and ``authority_adapter`` avoid rebuilding the lexical
    index and authority code index on every call (batch / trace export).

    Optional ``index_cache`` (``WorkspaceIndexCache``) reuses file + code index for
    the same workspace snapshot key (service latency only). Ignored when
    ``file_index`` is set. When ``index_cache_metrics`` is provided, it is updated
    with ``index_cache_hit``, ``file_index_build_ms``, and ``code_index_build_ms``.

    Optional ``enable_stage_a_v2`` overrides ``LexicalRetrievalConfig`` Stage A (HTTP
    ``/v1/export_evidence`` body). When ``None``, uses env/default from config.

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
    from runtime.layer5.retrieval.effective_intent import (
        merge_effective_intent,
        resolve_lexical_task_type,
    )
    from runtime.layer5.retrieval.fusion import (
        FusionConfig,
        fuse_and_filter,
        fusion_authority_note,
        hard_filter_only,
    )
    from runtime.layer5.retrieval.quality_gate import assess_evidence_quality
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
    registry = None
    adapter = authority_adapter
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
        if adapter is None:
            if authority_code_index_attempted:
                if authority_code_index is not None:
                    try:
                        adapter = create_adapter(
                            code_index=authority_code_index,
                            workspace_root=Path(w),
                        )
                    except Exception:
                        adapter = None
                else:
                    adapter = None
            else:
                if code_index_enabled:
                    try:
                        adapter = create_adapter(
                            code_index=build_index(Path(w)),
                            workspace_root=Path(w),
                        )
                    except Exception:
                        adapter = None
                else:
                    adapter = None
            # Fallback: when structured authority index is unavailable, still validate
            # against the already-built L5 lexical index for file/class/method checks.
            if adapter is None:
                try:
                    adapter = create_adapter(l5_index=idx, workspace_root=Path(w))
                except Exception:
                    adapter = None
        authority_resolution = build_authority_resolution(q, registry, adapter)
        if authority_resolution and adapter:
            mm = match_concepts_for_query(q, registry)
            if mm:
                structural_context = build_structural_context_stub(mm[0][0], adapter)
    except Exception as e:
        logging.getLogger(__name__).warning(
            "authority resolution or structural context failed: %s", e, exc_info=True
        )
        authority_resolution = None
        structural_context = None

    # Authority before lexical (Stage A owner injection); matches ask evidence_bridge ordering.
    if enable_stage_a_v2 is None:
        lex_cfg = LexicalRetrievalConfig()
    else:
        lex_cfg = LexicalRetrievalConfig(enable_stage_a_v2=enable_stage_a_v2)
    lex_task = resolve_lexical_task_type(
        str(task_type or "general"),
        q,
        authority_resolution if isinstance(authority_resolution, dict) else None,
    )
    selected_anchor = str(selected_file or "").strip() or None
    active_anchor = str(active_file or "").strip() or selected_anchor
    r = retrieve_lexical(
        idx,
        q,
        top_k,
        lex_cfg,
        task_type=lex_task,
        selected_file=selected_anchor,
        active_file=active_anchor,
        authority_resolution=authority_resolution if isinstance(authority_resolution, dict) else None,
    )

    effective = merge_effective_intent(lex_task, q)
    fusion_diag: Dict[str, Any] = {}
    roles_map: Dict[str, str] = {}
    owner_file = None
    if isinstance(authority_resolution, dict):
        po = authority_resolution.get("primary_owner")
        if isinstance(po, dict):
            owner_file = str(po.get("file") or "").strip() or None
    if registry is not None:
        fused, fusion_diag_inner, role_objs = fuse_and_filter(
            r,
            effective_intent=effective,
            registry=registry,
            code_index_adapter=adapter,
            selected_file=selected_anchor,
            fusion_config=FusionConfig(),
            index=idx,
            authority_resolution=authority_resolution if isinstance(authority_resolution, dict) else None,
        )
        r = fused
        fusion_diag = dict(fusion_diag_inner or {})
        roles_map = {p: ra.role for p, ra in role_objs.items()}
    else:
        filtered, fusion_diag_inner, role_objs = hard_filter_only(
            r,
            fusion_config=FusionConfig(),
            owner_path=owner_file,
            selected_file=selected_anchor,
            collaborator_paths=set(),
        )
        r = filtered
        fusion_diag = dict(fusion_diag_inner or {})
        roles_map = {p: ra.role for p, ra in role_objs.items()}

    if getattr(r, "stage_a_meta", None) is not None:
        fusion_diag["stage_a_meta"] = r.stage_a_meta
    fusion_diag["effective_intent"] = {
        "primary_mode": effective.primary_mode,
        "task_type": effective.task_type_raw,
        "lexical_task_type": lex_task,
        "conflicts": list(effective.conflicts),
    }
    qa = assess_evidence_quality(
        q,
        [h.relative_path for h in r.hits],
        effective_intent=effective,
        authority_primary_owner_file=owner_file,
    )
    fusion_diag["quality_reasons"] = list(qa.quality_reasons)

    evb = build_evidence_bundle(
        r,
        idx,
        authority_resolution=authority_resolution,
        structural_context=structural_context,
        role_by_path=roles_map if roles_map else None,
        authority_note=fusion_authority_note() if registry is not None else None,
        fusion_diagnostics=fusion_diag if fusion_diag else None,
        evidence_quality=qa.evidence_quality,
    )
    out = evb.to_dict()
    fd = out.get("fusion_diagnostics")
    if not isinstance(fd, dict):
        fd = {}
        out["fusion_diagnostics"] = fd
    method_hints = (
        _extract_method_hints(q, selected_anchor)
        if str(task_type or "").upper() == "EXPLAIN_DEBUG"
        else []
    )
    method_body_present = _selected_method_body_present(out, selected_anchor, method_hints)
    if method_hints:
        fd["selected_method_hints"] = method_hints
    if method_body_present is not None:
        fd["selected_method_body_present"] = bool(method_body_present)
        if not method_body_present:
            fd["selected_method_body_missing_reason"] = "selected_file_snippets_missing_method_hints"
    return out

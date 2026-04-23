"""
Shared Layer-5 evidence export API for Context Layer service and CLI.

Does not change retrieval or evidence semantics — delegates to existing L5 modules.
"""

from __future__ import annotations

import logging
import time
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING, Tuple

from runtime.layer5.evidence.executable_snippet_signals import text_has_executable_control_flow
from runtime.layer5.retrieval.path_resolve import paths_match_workspace

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


_JAVA_IMPL_TOKEN = re.compile(
    r"\b(void|public|private|protected|static|final|class|interface|enum|return|new|throw|"
    r"catch|try|else|switch|case|break|continue|implements|extends|native|synchronized)\b",
    re.I,
)

def _java_snippet_has_implementation_signals(text: str) -> bool:
    """True when excerpt looks like Java implementation, not only banner/imports (basename fallback helper)."""
    t = text.strip()
    if len(t) < 16:
        return False
    if _JAVA_IMPL_TOKEN.search(t):
        return True
    tl = t.lower()
    if "@override" in tl or "@deprecated" in tl:
        return True
    # Logic / operators without relying on ``void `` + space (tabs / newline after keyword).
    if len(t) >= 40:
        if re.search(r"[!=]=|[<>]=?|\|\||&&", t):
            return True
        if re.search(r"\b(if|for|while)\s*\(", t, re.I):
            return True
    return False


class DebugGroundingTier(str, Enum):
    """Grounding strength for selected-file debug evidence snippets."""

    NONE = "none"
    DECLARATIVE = "declarative"
    PARTIAL = "partial"
    EXECUTABLE = "executable"
    TRACEABLE = "traceable"


@dataclass(frozen=True)
class GroundingAssessment:
    tier: DebugGroundingTier
    matched_file: Optional[str]
    matched_method_names: list[str]
    executable_markers: list[str]
    control_flow_markers: int
    operation_markers: int
    line_refs: int
    rationale: list[str]
    missing_reason: Optional[str]


_CONTROL_FLOW_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("if", re.compile(r"\bif\s*\(")),
    ("else", re.compile(r"\belse\b")),
    ("switch", re.compile(r"\bswitch\s*\(")),
    ("for", re.compile(r"\bfor\s*\(")),
    ("while", re.compile(r"\bwhile\s*\(")),
    ("try", re.compile(r"\btry\b")),
    ("catch", re.compile(r"\bcatch\b")),
    ("return", re.compile(r"(?<![@])\breturn\b")),
    ("throw", re.compile(r"\bthrow\b")),
)
_OPERATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("call", re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\s*\(")),
    ("chained_call", re.compile(r"\.\s*[A-Za-z_][A-Za-z0-9_]*\s*\(")),
    ("new_object", re.compile(r"\bnew\s+[A-Za-z_][A-Za-z0-9_]*\s*\(")),
    ("assignment", re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\s*=\s*[^=]")),
    ("mutation", re.compile(r"\.(put|add|remove|set|update)\s*\(")),
)
_DECLARATIVE_ONLY_LINE = re.compile(
    r"^\s*(package|import)\b|^\s*(public|private|protected)?\s*(static\s+)?(final\s+)?"
    r"(class|interface|enum)\b|^\s*(public|private|protected)?\s*(static\s+)?(final\s+)?"
    r"[A-Za-z_][A-Za-z0-9_<>\[\]]*\s+[A-Za-z_][A-Za-z0-9_]*\s*(=\s*[^;]+)?;\s*$",
    re.I,
)


def _hint_matches_selected_snippet(hint: str, hay: str) -> bool:
    """
    Match debug hints against snippet text.

    Whole-word checks fail for typical Java camelCase methods (``dispatchTraps()``,
    ``parsePdu()``) where the hint token is ``dispatch`` or ``parse``.
    """
    if not hint or not hay:
        return False
    esc = re.escape(hint)
    # Method-ish: foo(, fooBar(, parsePdu(
    if re.search(rf"\b{esc}(?:[A-Z][a-zA-Z0-9_]*)?\s*\(", hay):
        return True
    # Type names, fields, or exact token
    if re.search(rf"\b{esc}\b", hay):
        return True
    return False


def _selected_snippet_entries(bundle_dict: Dict[str, Any], selected_file: str) -> list[dict[str, Any]]:
    entries = bundle_dict.get("entries")
    if not isinstance(entries, list):
        return []
    sel_norm = str(selected_file or "").replace("\\", "/").strip()
    if not sel_norm:
        return []
    sel = sel_norm.lower()
    base = sel.split("/")[-1]
    out: list[dict[str, Any]] = []
    for ent in entries:
        if not isinstance(ent, dict):
            continue
        rp = str(ent.get("relative_path") or "").replace("\\", "/").strip()
        if not rp:
            continue
        rp_l = rp.lower()
        if paths_match_workspace(rp, sel_norm) or rp_l == sel or rp_l.endswith("/" + base) or rp_l.endswith(base):
            out.append(ent)
    return out


def _line_ref_count(selected_entries: list[dict[str, Any]]) -> int:
    refs = 0
    for ent in selected_entries:
        sn = ent.get("snippet")
        sn = sn if isinstance(sn, dict) else {}
        if isinstance(sn.get("start_line"), int) and isinstance(sn.get("end_line"), int):
            refs += 1
    return refs


def _detect_markers(hay: str, patterns: tuple[tuple[str, re.Pattern[str]], ...]) -> list[str]:
    hits: list[str] = []
    for name, rx in patterns:
        if rx.search(hay):
            hits.append(name)
    return hits


def _has_non_declarative_statements(hay: str) -> bool:
    for line in hay.splitlines():
        ln = line.strip()
        if not ln:
            continue
        if ln.startswith("//") or ln.startswith("*") or ln.startswith("/*") or ln.startswith("*/"):
            continue
        if _DECLARATIVE_ONLY_LINE.match(ln):
            continue
        if re.search(r"[=()]|->|\.", ln):
            return True
    return False


def detect_selected_method_grounding(
    bundle_dict: Dict[str, Any],
    selected_file: Optional[str],
    method_hints: list[str],
) -> GroundingAssessment:
    """
    Classify selected-file grounding strength for EXPLAIN_DEBUG diagnostics.

    Deterministic and text-only: examines selected-file snippets in evidence bundle.
    """
    sel_norm = str(selected_file or "").replace("\\", "/").strip()
    if not sel_norm:
        return GroundingAssessment(
            tier=DebugGroundingTier.NONE,
            matched_file=None,
            matched_method_names=[],
            executable_markers=[],
            control_flow_markers=0,
            operation_markers=0,
            line_refs=0,
            rationale=["selected_file_missing"],
            missing_reason="selected_file_missing",
        )
    selected_entries = _selected_snippet_entries(bundle_dict, sel_norm)
    if not selected_entries:
        return GroundingAssessment(
            tier=DebugGroundingTier.NONE,
            matched_file=None,
            matched_method_names=[],
            executable_markers=[],
            control_flow_markers=0,
            operation_markers=0,
            line_refs=0,
            rationale=["selected_file_not_in_evidence_entries"],
            missing_reason="selected_file_not_in_evidence_entries",
        )
    selected_text_parts: list[str] = []
    for ent in selected_entries:
        sn = ent.get("snippet")
        sn = sn if isinstance(sn, dict) else {}
        selected_text_parts.append(str(sn.get("text") or ""))
    hay = "\n".join(selected_text_parts)
    matched_hints = [h for h in method_hints if _hint_matches_selected_snippet(h, hay)]
    stem = Path(sel_norm).stem
    stem_hint = bool(stem and any(str(h).lower() == stem.lower() for h in method_hints))
    cf_markers = _detect_markers(hay, _CONTROL_FLOW_PATTERNS)
    op_markers = _detect_markers(hay, _OPERATION_PATTERNS)
    line_refs = _line_ref_count(selected_entries)
    rationale: list[str] = [f"selected_entry_count={len(selected_entries)}"]

    if not text_has_executable_control_flow(hay):
        if not _has_non_declarative_statements(hay):
            rationale.append("declarations_only")
            return GroundingAssessment(
                tier=DebugGroundingTier.DECLARATIVE,
                matched_file=sel_norm,
                matched_method_names=matched_hints,
                executable_markers=[],
                control_flow_markers=0,
                operation_markers=len(op_markers),
                line_refs=line_refs,
                rationale=rationale,
                missing_reason="selected_file_snippet_declarative_only",
            )
        rationale.append("non_declarative_but_not_control_flow")
        return GroundingAssessment(
            tier=DebugGroundingTier.PARTIAL,
            matched_file=sel_norm,
            matched_method_names=matched_hints,
            executable_markers=[],
            control_flow_markers=0,
            operation_markers=len(op_markers),
            line_refs=line_refs,
            rationale=rationale,
            missing_reason="selected_file_snippet_partial_non_executable",
        )

    if not matched_hints and not (stem_hint and _java_snippet_has_implementation_signals(hay)):
        rationale.append("control_flow_present_but_method_hints_missing")
        return GroundingAssessment(
            tier=DebugGroundingTier.PARTIAL,
            matched_file=sel_norm,
            matched_method_names=[],
            executable_markers=cf_markers,
            control_flow_markers=len(cf_markers),
            operation_markers=len(op_markers),
            line_refs=line_refs,
            rationale=rationale,
            missing_reason="selected_file_snippets_missing_method_hints",
        )

    if len(cf_markers) >= 2 and len(op_markers) >= 2 and line_refs >= 1:
        rationale.append("traceable_local_flow")
        return GroundingAssessment(
            tier=DebugGroundingTier.TRACEABLE,
            matched_file=sel_norm,
            matched_method_names=matched_hints or ([stem] if stem_hint and stem else []),
            executable_markers=cf_markers,
            control_flow_markers=len(cf_markers),
            operation_markers=len(op_markers),
            line_refs=line_refs,
            rationale=rationale,
            missing_reason=None,
        )

    rationale.append("executable_method_body_present")
    return GroundingAssessment(
        tier=DebugGroundingTier.EXECUTABLE,
        matched_file=sel_norm,
        matched_method_names=matched_hints or ([stem] if stem_hint and stem else []),
        executable_markers=cf_markers,
        control_flow_markers=len(cf_markers),
        operation_markers=len(op_markers),
        line_refs=line_refs,
        rationale=rationale,
        missing_reason=None,
    )


def _selected_method_body_diagnosis(
    bundle_dict: Dict[str, Any],
    selected_file: Optional[str],
    method_hints: list[str],
) -> tuple[Optional[bool], Optional[str]]:
    """
    Whether selected-file snippets ground debug in executable logic (not declarations-only).

    Returns (None, None) when inapplicable; (False, reason) or (True, None) when applicable.
    """
    sel_norm = str(selected_file or "").replace("\\", "/").strip()
    if not sel_norm or not method_hints:
        return None, None
    assess = detect_selected_method_grounding(bundle_dict, sel_norm, method_hints)
    present = assess.tier in {DebugGroundingTier.EXECUTABLE, DebugGroundingTier.TRACEABLE}
    return present, assess.missing_reason


def _selected_method_body_present(
    bundle_dict: Dict[str, Any],
    selected_file: Optional[str],
    method_hints: list[str],
) -> Optional[bool]:
    """Backward-compatible bool wrapper for :func:`_selected_method_body_diagnosis`."""
    present, _reason = _selected_method_body_diagnosis(bundle_dict, selected_file, method_hints)
    return present


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

    rescue_sel = (
        (selected_anchor or "").strip()
        if str(task_type or "").upper() == "EXPLAIN_DEBUG"
        else ""
    )
    owner_method_rescue: Dict[str, Tuple[str, ...]] = {}
    if str(task_type or "").upper() != "EXPLAIN_DEBUG" and isinstance(authority_resolution, dict):
        po = authority_resolution.get("primary_owner") or {}
        if isinstance(po, dict):
            pf = str(po.get("file") or "").strip()
            pm = str(po.get("method") or "").strip()
            if pf and pm:
                owner_method_rescue[pf] = (pm,)
    evb = build_evidence_bundle(
        r,
        idx,
        authority_resolution=authority_resolution,
        structural_context=structural_context,
        role_by_path=roles_map if roles_map else None,
        authority_note=fusion_authority_note() if registry is not None else None,
        fusion_diagnostics=fusion_diag if fusion_diag else None,
        evidence_quality=qa.evidence_quality,
        debug_snippet_rescue_selected_file=rescue_sel or None,
        owner_method_rescue_hints_by_path=owner_method_rescue or None,
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
    if str(task_type or "").upper() == "EXPLAIN_DEBUG":
        assessment = detect_selected_method_grounding(out, selected_anchor, method_hints)
        present, missing_reason = _selected_method_body_diagnosis(out, selected_anchor, method_hints)
        if method_hints:
            fd["selected_method_hints"] = method_hints
        fd["selected_method_grounding_tier"] = assessment.tier.value
        fd["selected_method_grounding_rationale"] = list(assessment.rationale)
        fd["selected_method_control_flow_markers"] = int(assessment.control_flow_markers)
        fd["selected_method_operation_markers"] = int(assessment.operation_markers)
        fd["selected_method_line_refs"] = int(assessment.line_refs)
        if assessment.matched_method_names:
            fd["selected_method_matched_names"] = list(assessment.matched_method_names)
        if present is not None:
            fd["selected_method_body_present"] = bool(present)
            if not present and missing_reason:
                fd["selected_method_body_missing_reason"] = missing_reason
    return out

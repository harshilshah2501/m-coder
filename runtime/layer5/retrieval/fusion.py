"""
Stage B — Fusion scoring + filtering (RETRIEVAL_REDESIGN_SPEC_V1).

Precedence: lexical base → authority ranker fusion → domain prior → active file →
mode scaling → weak/generic caps → hard constraints.

Output ``RetrievalResult`` replaces lexical ordering/scores; evidence builder must not reorder.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from runtime.layer5.authority.ranking import AuthorityRanker, RankedHit
from runtime.layer5.authority.ranking_config import RankingConfig, get_config
from runtime.layer5.authority.registry_loader import AuthorityRegistry
from runtime.layer5.retrieval.effective_intent import (
    MODE_ASK,
    MODE_CODE,
    MODE_DEBUG,
    MODE_PLAN,
    EffectiveIntent,
)
from runtime.layer5.retrieval.models import RetrievalHit, RetrievalResult
from runtime.layer5.retrieval.path_resolve import paths_match_workspace, resolve_owner_path_in_index
from runtime.layer5.retrieval.policy import (
    classify_file,
    infer_query_subsystems,
    is_noise_class,
    query_api_surface_focus,
    query_class_relationship_focus,
    is_support_style_java_basename,
)
from runtime.layer5.retrieval.query import normalize_query
from runtime.layer5.retrieval.roles import (
    PRIMARY_OWNER_CANDIDATE,
    RoleAssignment,
    assign_roles,
)

if TYPE_CHECKING:
    from runtime.layer5.index.models import WorkspaceFileIndex

_FUSION_NOTE = (
    "Candidate order and retrieval_score come from Stage B fusion "
    "(lexical + authority + domain priors + constraints); A6 does not reorder by snippet."
)


@dataclass(frozen=True)
class FusionConfig:
    """Tunable fusion limits (deterministic defaults)."""

    domain_prior_cap: float = 55.0
    active_file_boost_debug: float = 42.0
    active_file_boost_other: float = 14.0
    max_distractor_paths: int = 1
    max_generic_infra_paths: int = 2
    ask_broad_generic_infra_paths: int = 1
    min_paths_after_caps: int = 3
    weak_lexical_ratio: float = 0.12
    weak_match_penalty: float = 18.0
    total_positive_delta_cap: float = 220.0
    enable_fusion: bool = True


def _load_yaml_priors() -> Tuple[Dict[str, Any], ...]:
    path = Path(__file__).with_name("domain_priors.yaml")
    raw = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore[import-untyped]

        data = yaml.safe_load(raw)
    except Exception:
        return ()
    priors = data.get("priors") if isinstance(data, dict) else None
    if not isinstance(priors, list):
        return ()
    out: List[Dict[str, Any]] = []
    for p in priors:
        if isinstance(p, dict):
            out.append(p)
    return tuple(out)


_PRIORS: Tuple[Dict[str, Any], ...] = _load_yaml_priors()


def _norm_rel(p: str) -> str:
    return p.replace("\\", "/").strip()


def _domain_prior_delta(
    path: str,
    query_tokens: Tuple[str, ...],
    lex_subsystems: Set[str],
    cfg: FusionConfig,
) -> Tuple[float, str]:
    """Returns (delta, reason_suffix)."""
    pl = path.lower()
    total = 0.0
    reasons: List[str] = []
    for p in _PRIORS:
        qterms = [str(x).lower() for x in (p.get("query_terms") or [])]
        if not qterms or not any(t in query_tokens for t in qterms):
            continue
        substrings = [str(x).lower() for x in (p.get("path_substrings") or [])]
        hit = any(s and s in pl for s in substrings)
        if not hit:
            continue
        max_b = float(p.get("max_boost") or 0.0)
        boost = min(max_b, cfg.domain_prior_cap)
        tags = {str(x).lower() for x in (p.get("subsystem_tags") or [])}
        if tags and lex_subsystems.intersection(tags):
            boost *= 0.5
            reasons.append(f"prior:{p.get('id')}:half_lexical_subsystem")
        else:
            reasons.append(f"prior:{p.get('id')}")
        total += boost
    total = min(total, cfg.domain_prior_cap)
    return total, "|".join(reasons) if reasons else ""


def _active_file_delta(
    path: str,
    selected_file: Optional[str],
    effective: EffectiveIntent,
    cfg: FusionConfig,
) -> float:
    if not selected_file:
        return 0.0
    if _norm_rel(path).lower() != _norm_rel(selected_file).lower():
        return 0.0
    if effective.primary_mode == MODE_DEBUG:
        return cfg.active_file_boost_debug
    return cfg.active_file_boost_other


def _mode_scale(delta_non_lexical: float, effective: EffectiveIntent) -> float:
    m = effective.primary_mode
    mult = {
        MODE_ASK: 1.06,
        MODE_DEBUG: 1.10,
        MODE_PLAN: 1.03,
        MODE_CODE: 1.08,
    }.get(m, 1.0)
    return delta_non_lexical * mult


def _is_generic_infra_path(path: str) -> bool:
    pol = classify_file(path)
    if pol.file_class == "config":
        return True
    pl = path.lower()
    if any(tok in pl for tok in ("/api/", "/db/", "/notification/", "/cache/", "/integration/", "/manager/")):
        return True
    base = path.rsplit("/", 1)[-1].lower()
    return bool(is_support_style_java_basename(base))


def _promote_authority_owner_to_top3_fused(
    ordered: List[Tuple[RetrievalHit, float, Dict[str, Any]]],
    owner_path: Optional[str],
    *,
    top_k: int,
) -> Tuple[List[Tuple[RetrievalHit, float, Dict[str, Any]]], Dict[str, Any]]:
    """
    v2.1.2: If authority primary owner exists in the fused ordering but ranks below top-3,
    swap it into the weakest-scoring slot among the first three rows (deterministic).

    Keeps owner visible through Stage B hard caps when fusion reranking would drop it.
    """
    trace: Dict[str, Any] = {
        "applied": False,
        "primary_owner_file": owner_path or "",
    }
    if not owner_path or top_k < 3 or len(ordered) < 3:
        return ordered, trace
    if not str(owner_path).strip():
        return ordered, trace
    idx_owner: Optional[int] = None
    for i, (h, _sc, _diag) in enumerate(ordered):
        if paths_match_workspace(h.relative_path, owner_path):
            idx_owner = i
            break
    if idx_owner is None:
        trace["note"] = "owner_path_not_in_fused_candidate_list"
        return ordered, trace
    trace["rank_before"] = idx_owner
    if idx_owner < 3:
        trace["note"] = "already_in_top3"
        return ordered, trace
    rows = list(ordered)
    replace_i = min(
        range(3),
        key=lambda i: (rows[i][1], rows[i][0].relative_path),
    )
    rows[replace_i], rows[idx_owner] = rows[idx_owner], rows[replace_i]
    trace["applied"] = True
    trace["swap_into_slot"] = replace_i
    trace["note"] = "swapped_weakest_top3_for_authority_owner"
    return rows, trace


def _ensure_owner_present(
    hits: List[RetrievalHit],
    owner_rel: str,
    index: "WorkspaceFileIndex",
) -> List[RetrievalHit]:
    if not owner_rel:
        return hits
    for h in hits:
        if paths_match_workspace(h.relative_path, owner_rel):
            return hits
    for e in index.files:
        if paths_match_workspace(e.relative_path, owner_rel):
            synthetic = RetrievalHit(
                relative_path=e.relative_path,
                score=1,
                breakdown={"path_substrings": 0, "basename_substrings": 0, "content_substrings": 0},
            )
            return [synthetic] + hits
    return hits


def _apply_infra_and_distractor_caps(
    ordered: List[Tuple[RetrievalHit, float, Dict[str, Any]]],
    cfg: FusionConfig,
) -> List[Tuple[RetrievalHit, float, Dict[str, Any]]]:
    """Penalize surplus generic-infra and noise-class paths, then re-sort."""
    if not ordered:
        return ordered
    generic_kept = 0
    distractor_kept = 0
    out: List[Tuple[RetrievalHit, float, Dict[str, Any]]] = []
    for h, sc, diag in ordered:
        path = h.relative_path
        pol = classify_file(path)
        is_gen = _is_generic_infra_path(path)
        is_dist = is_noise_class(pol.file_class)
        diag = dict(diag)
        if is_gen:
            generic_kept += 1
            if generic_kept > cfg.max_generic_infra_paths:
                sc -= 25.0
                diag["cap_applied"] = "generic_infra_surplus"
        if is_dist:
            distractor_kept += 1
            if distractor_kept > cfg.max_distractor_paths:
                sc -= 40.0
                diag["cap_applied_dist"] = "noise_surplus"
        out.append((h, sc, diag))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def _apply_hard_path_caps(
    ordered: List[Tuple[RetrievalHit, float, Dict[str, Any]]],
    cfg: FusionConfig,
    *,
    top_k: int,
    owner_path: Optional[str],
    selected_file: Optional[str],
) -> Tuple[List[Tuple[RetrievalHit, float, Dict[str, Any]]], Dict[str, Any]]:
    """
    Hard filter after scoring/sorting.

    Unlike soft penalties, this can remove paths entirely so the final
    context set is bounded by max_generic_infra_paths / max_distractor_paths.
    """
    if not ordered:
        return ordered, {"kept": 0, "dropped": 0}

    selected_n = _norm_rel(selected_file).lower() if selected_file else ""
    kept: List[Tuple[RetrievalHit, float, Dict[str, Any]]] = []
    dropped_rows: List[Tuple[RetrievalHit, float, Dict[str, Any], str]] = []
    dropped: List[Dict[str, Any]] = []
    generic_count = 0
    distractor_count = 0

    for h, sc, diag in ordered:
        rel_n = _norm_rel(h.relative_path).lower()
        protected = bool(
            (owner_path and paths_match_workspace(h.relative_path, owner_path))
            or (selected_n and rel_n == selected_n)
        )
        pol = classify_file(h.relative_path)
        is_gen = _is_generic_infra_path(h.relative_path)
        is_dist = is_noise_class(pol.file_class)

        if is_gen and generic_count >= cfg.max_generic_infra_paths and not protected:
            reason = "hard_cap_generic_infra"
            dropped.append({"path": h.relative_path, "reason": reason})
            dropped_rows.append((h, sc, diag, reason))
            continue
        if is_dist and distractor_count >= cfg.max_distractor_paths and not protected:
            reason = "hard_cap_distractor"
            dropped.append({"path": h.relative_path, "reason": reason})
            dropped_rows.append((h, sc, diag, reason))
            continue

        kept.append((h, sc, diag))
        if is_gen:
            generic_count += 1
        if is_dist:
            distractor_count += 1
        if len(kept) >= max(1, top_k):
            break

    # Avoid over-thinning anchored retrieval: re-add best dropped rows deterministically
    # until we satisfy the minimum context floor.
    min_keep = max(1, min(top_k, cfg.min_paths_after_caps))
    restored: List[Dict[str, Any]] = []
    if len(kept) < min_keep and dropped_rows:
        for h, sc, diag, reason in dropped_rows:
            if len(kept) >= min_keep:
                break
            pol = classify_file(h.relative_path)
            is_gen = _is_generic_infra_path(h.relative_path)
            is_dist = is_noise_class(pol.file_class)
            # Preserve hard-cap intent during floor restore: never re-introduce
            # rows that would violate generic/distractor budgets again.
            if is_gen and generic_count >= cfg.max_generic_infra_paths:
                continue
            if is_dist and distractor_count >= cfg.max_distractor_paths:
                continue
            kept.append((h, sc, dict(diag)))
            restored.append({"path": h.relative_path, "from_reason": reason})
            if is_gen:
                generic_count += 1
            if is_dist:
                distractor_count += 1

    return kept, {
        "kept": len(kept),
        "dropped": len(dropped),
        "dropped_paths": dropped,
        "restored_for_min_paths": restored,
        "generic_infra_kept": generic_count,
        "distractor_kept": distractor_count,
        "min_paths_after_caps": min_keep,
    }


def hard_filter_only(
    retrieval: RetrievalResult,
    *,
    fusion_config: Optional[FusionConfig] = None,
    owner_path: Optional[str] = None,
    selected_file: Optional[str] = None,
    collaborator_paths: Optional[Set[str]] = None,
) -> Tuple[RetrievalResult, Dict[str, Any], Dict[str, RoleAssignment]]:
    """
    Apply deterministic hard caps without authority/domain fusion.

    Used as a fallback when authority registry is unavailable so retrieval still
    gets measurable post-selection filtering behavior.
    """
    cfg = fusion_config or FusionConfig()
    rows: List[Tuple[RetrievalHit, float, Dict[str, Any]]] = []
    for h in retrieval.hits:
        rows.append(
            (
                h,
                float(h.score),
                {
                    "path": h.relative_path,
                    "lexical_score": float(h.score),
                    "fused_score": float(h.score),
                    "fallback": "hard_filter_only",
                },
            )
        )
    rows, hard_cap_diag = _apply_hard_path_caps(
        rows,
        cfg,
        top_k=retrieval.top_k,
        owner_path=owner_path,
        selected_file=selected_file,
    )
    new_hits: List[RetrievalHit] = []
    for h, _, _ in rows:
        new_hits.append(h)
    out = RetrievalResult(
        query_raw=retrieval.query_raw,
        query_tokens=retrieval.query_tokens,
        top_k=retrieval.top_k,
        hits=tuple(new_hits),
        index_schema_version=retrieval.index_schema_version,
        workspace_identity_hash=retrieval.workspace_identity_hash,
        workspace_snapshot_hash=retrieval.workspace_snapshot_hash,
        workspace_snapshot_source=retrieval.workspace_snapshot_source,
        workspace_is_dirty=retrieval.workspace_is_dirty,
        workspace_commit_sha=retrieval.workspace_commit_sha,
        stage_a_meta=retrieval.stage_a_meta,
    )
    roles = assign_roles(
        tuple(h.relative_path for h in new_hits),
        owner_path=owner_path,
        collaborator_paths=collaborator_paths or set(),
    )
    diag = {
        "skipped_authority_fusion": True,
        "reason": "registry_unavailable",
        "fusion_config": {
            "max_distractor_paths": cfg.max_distractor_paths,
            "max_generic_infra_paths": cfg.max_generic_infra_paths,
            "min_paths_after_caps": cfg.min_paths_after_caps,
        },
        "hard_caps": hard_cap_diag,
    }
    return out, diag, roles


def fuse_and_filter(
    retrieval: RetrievalResult,
    *,
    effective_intent: EffectiveIntent,
    registry: AuthorityRegistry,
    code_index_adapter: Optional[Any] = None,
    selected_file: Optional[str] = None,
    fusion_config: Optional[FusionConfig] = None,
    index: Optional["WorkspaceFileIndex"] = None,
    authority_resolution: Optional[Dict[str, Any]] = None,
) -> Tuple[RetrievalResult, Dict[str, Any], Dict[str, RoleAssignment]]:
    """
    Returns fused RetrievalResult, fusion diagnostics dict, and role assignments by path.
    """
    cfg = fusion_config or FusionConfig()
    diag_root: Dict[str, Any] = {
        "effective_intent": {
            "primary_mode": effective_intent.primary_mode,
            "query_intent_type": effective_intent.query_intent.intent_type,
            "task_type": effective_intent.task_type_raw,
            "conflicts": list(effective_intent.conflicts),
        },
        "per_path": [],
    }

    if not cfg.enable_fusion:
        roles = assign_roles(
            tuple(h.relative_path for h in retrieval.hits),
            owner_path=_owner_from_resolution(authority_resolution),
            collaborator_paths=None,
        )
        return retrieval, {"skipped": True, **diag_root}, roles

    ranker = AuthorityRanker(registry, code_index_adapter, get_config())
    ctx = ranker.build_context(retrieval.query_raw)
    query_tokens = normalize_query(retrieval.query_raw)
    lex_subsystems = set(infer_query_subsystems(query_tokens))

    hits_list = list(retrieval.hits)
    owner_path = _owner_from_resolution(authority_resolution)
    if index is not None and owner_path:
        ps = {e.relative_path for e in index.files}
        oc = _owner_class_from_resolution(authority_resolution)
        resolved_owner = resolve_owner_path_in_index(owner_path, ps, owner_class=oc)
        if resolved_owner:
            owner_path = resolved_owner
        hits_list = _ensure_owner_present(hits_list, owner_path, index)

    by_path = {h.relative_path: h for h in hits_list}
    pairs = [(h.relative_path, float(h.score)) for h in hits_list]
    ranked: List[RankedHit] = ranker.rank_hits(pairs, ctx)

    top_lex = max((h.score for h in hits_list), default=1)

    fused_rows: List[Tuple[RetrievalHit, float, Dict[str, Any]]] = []
    for rh in ranked:
        orig = by_path.get(rh.file_path)
        if orig is None:
            # Owner synthetic — only path in ranked from ensure_owner
            for h in hits_list:
                if h.relative_path == rh.file_path:
                    orig = h
                    break
        if orig is None:
            continue
        d0 = rh.diagnostics
        base_auth = float(rh.final_score)
        dp, pr_reason = _domain_prior_delta(
            rh.file_path,
            query_tokens,
            lex_subsystems,
            cfg,
        )
        af = _active_file_delta(rh.file_path, selected_file, effective_intent, cfg)
        non_lex = dp + af
        scaled = _mode_scale(non_lex, effective_intent)
        weak_pen = 0.0
        if top_lex > 0 and float(orig.score) < max(1.0, cfg.weak_lexical_ratio * float(top_lex)):
            if int(orig.breakdown.get("content_substrings", 0)) < 2:
                weak_pen = cfg.weak_match_penalty
        fused = base_auth + scaled - weak_pen
        base_fused = base_auth + scaled - weak_pen
        # Cap positive delta from raw lexical
        lex_b = float(orig.score)
        pos_delta = max(0.0, fused - lex_b)
        if pos_delta > cfg.total_positive_delta_cap:
            fused = lex_b + cfg.total_positive_delta_cap

        per: Dict[str, Any] = {
            "path": rh.file_path,
            "lexical_score": lex_b,
            "authority_final": base_auth,
            "domain_prior": dp,
            "domain_prior_detail": pr_reason,
            "active_file_boost": af,
            "weak_match_penalty": weak_pen,
            "fused_score": fused,
            "_base_fused": base_fused,
        }
        if d0 is not None:
            per["authority_diagnostics"] = d0.to_dict()
        fused_rows.append((orig, fused, per))

    # Broad ASK mode should be stricter with generic/support passengers.
    #
    # Special-case class-relationship API asks (e.g. "base class for all APIs"):
    # keep broader API surface so declaration evidence (AbstractAPI) survives.
    class_rel_api_ask = (
        effective_intent.primary_mode == MODE_ASK
        and query_class_relationship_focus(tuple(query_tokens))
        and query_api_surface_focus(tuple(query_tokens))
    )
    cap_cfg = cfg
    if (
        effective_intent.primary_mode == MODE_ASK
        and not selected_file
        and not class_rel_api_ask
    ):
        broad_cap = cfg.ask_broad_generic_infra_paths
        # Owner-anchored ask responses should not accumulate additional generic
        # infra passengers beyond the protected owner row.
        if owner_path:
            broad_cap = 0
        if broad_cap < cfg.max_generic_infra_paths:
            cap_cfg = replace(cfg, max_generic_infra_paths=broad_cap)
        diag_root["ask_broad_caps_applied"] = {
            "max_generic_infra_paths": cap_cfg.max_generic_infra_paths,
        }

    fused_rows.sort(key=lambda x: x[1], reverse=True)
    fused_rows = _apply_infra_and_distractor_caps(fused_rows, cap_cfg)
    fused_rows, owner_top3_trace = _promote_authority_owner_to_top3_fused(
        fused_rows,
        owner_path,
        top_k=retrieval.top_k,
    )
    if owner_top3_trace.get("applied"):
        diag_root["authority_owner_top3_promotion"] = owner_top3_trace
    fused_rows, hard_cap_diag = _apply_hard_path_caps(
        fused_rows,
        cap_cfg,
        top_k=retrieval.top_k,
        owner_path=owner_path,
        selected_file=selected_file,
    )

    new_hits: List[RetrievalHit] = []
    per_path_diags: List[Dict[str, Any]] = []
    for rank, (orig, fused_score, pdiag) in enumerate(fused_rows):
        fs_int = int(round(max(0.0, fused_score)))
        b = dict(orig.breakdown)
        b["fusion_lexical_base"] = int(orig.score)
        b["fusion_total"] = fs_int
        b["fusion_domain_prior"] = int(round(pdiag.get("domain_prior", 0.0)))
        b["fusion_active_file"] = int(round(pdiag.get("active_file_boost", 0.0)))
        b["fusion_weak_penalty"] = int(round(pdiag.get("weak_match_penalty", 0.0)))
        new_hits.append(
            RetrievalHit(
                relative_path=orig.relative_path,
                score=fs_int,
                breakdown=b,
                diagnostics=orig.diagnostics,
            )
        )
        pdiag_out = {k: v for k, v in pdiag.items() if k != "_base_fused"}
        pdiag_out["rank_after_fusion"] = rank
        per_path_diags.append(pdiag_out)

    diag_root["per_path"] = per_path_diags
    diag_root["fusion_config"] = {
        "domain_prior_cap": cfg.domain_prior_cap,
        "max_distractor_paths": cap_cfg.max_distractor_paths,
        "max_generic_infra_paths": cap_cfg.max_generic_infra_paths,
    }
    diag_root["hard_caps"] = hard_cap_diag

    out = RetrievalResult(
        query_raw=retrieval.query_raw,
        query_tokens=retrieval.query_tokens,
        top_k=retrieval.top_k,
        hits=tuple(new_hits),
        index_schema_version=retrieval.index_schema_version,
        workspace_identity_hash=retrieval.workspace_identity_hash,
        workspace_snapshot_hash=retrieval.workspace_snapshot_hash,
        workspace_snapshot_source=retrieval.workspace_snapshot_source,
        workspace_is_dirty=retrieval.workspace_is_dirty,
        workspace_commit_sha=retrieval.workspace_commit_sha,
        stage_a_meta=retrieval.stage_a_meta,
    )

    collab: Set[str] = set()
    if authority_resolution and isinstance(authority_resolution.get("collaborators"), list):
        for c in authority_resolution["collaborators"]:
            if isinstance(c, dict) and c.get("file"):
                collab.add(_norm_rel(str(c["file"])))

    roles = assign_roles(
        tuple(h.relative_path for h in new_hits),
        owner_path=owner_path,
        collaborator_paths=collab,
    )
    return out, diag_root, roles


def _owner_from_resolution(authority_resolution: Optional[Dict[str, Any]]) -> Optional[str]:
    if not authority_resolution:
        return None
    po = authority_resolution.get("primary_owner")
    if not isinstance(po, dict):
        return None
    f = str(po.get("file") or "").strip()
    return f or None


def _owner_class_from_resolution(authority_resolution: Optional[Dict[str, Any]]) -> Optional[str]:
    if not authority_resolution:
        return None
    po = authority_resolution.get("primary_owner")
    if not isinstance(po, dict):
        return None
    c = str(po.get("class") or "").strip()
    return c or None


def fusion_authority_note() -> str:
    """Note string for evidence bundles that went through fusion."""
    return _FUSION_NOTE

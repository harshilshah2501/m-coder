"""
Stage A — multi-source quota candidate generation (STAGE_A_CANDIDATE_GENERATION_SPEC_V2).

Produces a bounded pre-fusion path pool with lane labels. Does not assign fusion scores.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from runtime.layer5.index.models import FileIndexEntry, WorkspaceFileIndex
from runtime.layer5.retrieval.intent import classify_intent
from runtime.layer5.retrieval.path_resolve import resolve_owner_path_in_index
from runtime.layer5.retrieval.models import RetrievalHit
from runtime.layer5.retrieval.policy import (
    classify_file,
    infer_file_subsystem,
    infer_query_subsystems,
    is_code_bearing_path,
    is_noise_class,
    is_non_code_asset_path,
    looks_like_symbol_token,
    query_explicit_non_code_asset_intent,
)


def _norm_rel(p: str) -> str:
    return p.replace("\\", "/").strip()


def _is_generic_infra_path(rel: str) -> bool:
    """Match fusion._is_generic_infra_path for Stage A caps."""
    pol = classify_file(rel)
    if pol.file_class == "config":
        return True
    pl = rel.lower()
    if any(
        tok in pl for tok in ("/api/", "/db/", "/notification/", "/cache/", "/integration/", "/manager/")
    ):
        return True
    base = rel.rsplit("/", 1)[-1].lower()
    from runtime.layer5.retrieval.policy import is_support_style_java_basename

    return bool(is_support_style_java_basename(base))


def _query_explicit_infra(tokens: Tuple[str, ...]) -> bool:
    infra = frozenset(
        {
            "api",
            "database",
            "db",
            "cache",
            "notification",
            "infra",
            "gateway",
            "plumbing",
            "integration",
        }
    )
    return bool(set(tokens) & infra)


def _task_prefers_code_candidates(
    task_type: str,
    *,
    anchored_owner_like: bool,
) -> bool:
    tt = (task_type or "").strip().upper()
    if tt == "GENERAL":
        return anchored_owner_like
    return tt in {"ASK", "EXPLAIN_DEBUG", "PLAN", "CODE"}


def _candidate_eligible_for_task(
    rel: str,
    *,
    anchored_owner_like: bool,
    task_type: str,
    allow_non_code_assets: bool,
) -> bool:
    if not _task_prefers_code_candidates(task_type, anchored_owner_like=anchored_owner_like):
        return True
    file_policy = classify_file(rel)
    if is_noise_class(file_policy.file_class):
        # Keep explicit asset-intent queries working (e.g., logo/icon lookups),
        # but suppress noisy generated/vendor/test files during code-oriented asks.
        return allow_non_code_assets and is_non_code_asset_path(rel)
    if is_non_code_asset_path(rel):
        return allow_non_code_assets
    return is_code_bearing_path(rel)


def _filter_candidates_for_task(
    candidates: List[StageCandidate],
    *,
    anchored_owner_like: bool,
    task_type: str,
    allow_non_code_assets: bool,
) -> List[StageCandidate]:
    out: List[StageCandidate] = []
    for c in candidates:
        if _candidate_eligible_for_task(
            c.path,
            anchored_owner_like=anchored_owner_like,
            task_type=task_type,
            allow_non_code_assets=allow_non_code_assets,
        ):
            out.append(c)
    return out


def _primary_owner_file(authority_resolution: Optional[Mapping[str, Any]]) -> Optional[str]:
    if not authority_resolution:
        return None
    po = authority_resolution.get("primary_owner")
    if not isinstance(po, Mapping):
        return None
    f = str(po.get("file") or "").strip()
    return f or None


def _resolve_editor_file_in_index(raw: str, path_set: Set[str]) -> Optional[str]:
    """Map IDE-selected paths into ``path_set`` including basename drift like owner injection."""
    n = _norm_rel(raw).strip()
    return resolve_owner_path_in_index(n, path_set, owner_class=None) if n else None


def _owner_class_from_authority(authority_resolution: Optional[Mapping[str, Any]]) -> Optional[str]:
    if not authority_resolution:
        return None
    po = authority_resolution.get("primary_owner")
    if not isinstance(po, Mapping):
        return None
    c = str(po.get("class") or "").strip()
    return c or None


def _resolve_owner_primary_path(
    owner_path: str,
    path_set: Set[str],
    authority_resolution: Optional[Mapping[str, Any]],
) -> Optional[str]:
    return resolve_owner_path_in_index(
        _norm_rel(owner_path),
        path_set,
        owner_class=_owner_class_from_authority(authority_resolution),
    )


def _resolve_best_authority_file_path(
    authority_resolution: Optional[Mapping[str, Any]],
    path_set: Set[str],
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Resolve a concrete index path for authority-driven owner injection.

    Order: ``primary_owner.file`` (with basename drift), then ``collaborators[*].file``,
    then ``entry_trace.entry_point.file`` when the primary Java file is missing from the
    workspace (stale registry) but related modules still exist.
    """
    trace: Dict[str, Any] = {}
    if not authority_resolution:
        return None, trace
    primary = _primary_owner_file(authority_resolution)
    if primary:
        r = _resolve_owner_primary_path(primary, path_set, authority_resolution)
        if r:
            trace["resolution_source"] = "primary_owner"
            trace["resolved_path"] = r
            return r, trace
        trace["primary_unresolved"] = primary
    collabs = authority_resolution.get("collaborators")
    if isinstance(collabs, list):
        for i, c in enumerate(collabs):
            if not isinstance(c, dict):
                continue
            cf = str(c.get("file") or "").strip()
            if not cf:
                continue
            r = resolve_owner_path_in_index(cf, path_set, owner_class=None)
            if r:
                trace["resolution_source"] = "collaborator"
                trace["resolved_path"] = r
                trace["collaborator_index"] = i
                trace["collaborator_registry_path"] = cf
                return r, trace
    et = authority_resolution.get("entry_trace")
    if isinstance(et, dict):
        ep = et.get("entry_point")
        if isinstance(ep, dict):
            ef = str(ep.get("file") or "").strip()
            if ef:
                r = resolve_owner_path_in_index(ef, path_set, owner_class=None)
                if r:
                    trace["resolution_source"] = "entry_point"
                    trace["resolved_path"] = r
                    trace["entry_point_registry_path"] = ef
                    return r, trace
    return None, trace


@dataclass(frozen=True)
class StageCandidate:
    lane: str
    path: str
    reason: str
    subsystem_tag: str = ""
    injected: bool = False
    exact_symbol_match: bool = False

    def to_diag(self) -> Dict[str, Any]:
        return {
            "lane": self.lane,
            "path": self.path,
            "reason": self.reason,
            "subsystem_tag": self.subsystem_tag or "",
            "injected": self.injected,
            "exact_symbol_match": self.exact_symbol_match,
        }


def _collect_symbol_seeds(
    index: WorkspaceFileIndex,
    query: str,
    tokens: Tuple[str, ...],
    *,
    limit: int,
) -> List[StageCandidate]:
    intent = classify_intent(query)
    sym_toks: List[str] = []
    for t in intent.symbol_tokens:
        sym_toks.append(t.lower())
    for t in tokens:
        if looks_like_symbol_token(t) and t not in sym_toks:
            sym_toks.append(t.lower())
    if not sym_toks:
        return []
    out: List[StageCandidate] = []
    seen: Set[str] = set()
    for e in index.files:
        if len(out) >= limit * 3:
            break
        rel = e.relative_path
        stem = Path(rel).stem.lower()
        stem_parts = set(x for x in stem.replace("-", "_").split("_") if x)
        for st in sym_toks:
            exact = st == stem
            partial = st in stem_parts or (len(st) >= 6 and st in stem)
            if exact or partial:
                if rel not in seen:
                    seen.add(rel)
                    out.append(
                        StageCandidate(
                            lane="symbol_seed",
                            path=rel,
                            reason="basename_symbol_alignment" if not exact else "basename_exact_symbol",
                            subsystem_tag=infer_file_subsystem(rel),
                            exact_symbol_match=bool(exact),
                        )
                    )
                break
    out.sort(key=lambda c: c.path)
    return out[:limit]


def _collect_package_seeds(
    index: WorkspaceFileIndex,
    tokens: Tuple[str, ...],
    *,
    limit: int,
) -> List[StageCandidate]:
    qsubs = infer_query_subsystems(tokens)
    if not qsubs:
        return []
    out: List[StageCandidate] = []
    for e in index.files:
        fs = infer_file_subsystem(e.relative_path)
        if fs in qsubs and fs != "unknown":
            out.append(
                StageCandidate(
                    lane="package_seed",
                    path=e.relative_path,
                    reason=f"subsystem:{fs}",
                    subsystem_tag=fs,
                )
            )
    out.sort(key=lambda c: c.path)
    return out[:limit]


def _same_package_neighbors(selected: str, index: WorkspaceFileIndex, *, cap: int) -> List[str]:
    parent = str(Path(selected).parent)
    sib: List[str] = []
    for e in index.files:
        if str(Path(e.relative_path).parent) == parent and e.relative_path != selected:
            sib.append(e.relative_path)
    sib.sort()
    return sib[:cap]


def _collect_local_seeds(
    index: WorkspaceFileIndex,
    selected_file: Optional[str],
    active_file: Optional[str],
    *,
    neighbor_cap: int,
    anchored_owner_like: bool,
    tokens: Tuple[str, ...],
    task_type: str,
) -> List[StageCandidate]:
    path_set = {e.relative_path for e in index.files}
    allow_non_code_assets = query_explicit_non_code_asset_intent(tokens)
    allow_generic_infra = _query_explicit_infra(tokens)
    out: List[StageCandidate] = []
    seen: Set[str] = set()

    def add(p: str, reason: str, injected: bool = False) -> None:
        resolved = _resolve_editor_file_in_index(p, path_set)
        if not resolved or resolved in seen:
            return
        if not _candidate_eligible_for_task(
            resolved,
            anchored_owner_like=anchored_owner_like,
            task_type=task_type,
            allow_non_code_assets=allow_non_code_assets,
        ):
            return
        seen.add(resolved)
        out.append(
            StageCandidate(
                lane="local_seed",
                path=resolved,
                reason=reason,
                subsystem_tag=infer_file_subsystem(resolved),
                injected=injected,
            )
        )

    for label, raw in (("selected_file", selected_file), ("active_file", active_file)):
        if raw:
            add(raw, f"{label}_mandatory", injected=True)

    sel = None
    if selected_file:
        sel = _resolve_editor_file_in_index(selected_file, path_set)
    if not sel and active_file:
        sel = _resolve_editor_file_in_index(active_file, path_set)
    if sel:
        sel_subsystem = infer_file_subsystem(sel)
        for nb in _same_package_neighbors(sel, index, cap=neighbor_cap):
            if not is_code_bearing_path(nb):
                continue
            if not _candidate_eligible_for_task(
                nb,
                anchored_owner_like=anchored_owner_like,
                task_type=task_type,
                allow_non_code_assets=allow_non_code_assets,
            ):
                continue
            if _is_generic_infra_path(nb) and not allow_generic_infra:
                continue
            nb_subsystem = infer_file_subsystem(nb)
            if sel_subsystem != "unknown" and nb_subsystem not in {sel_subsystem, "unknown"}:
                continue
            if nb not in seen:
                seen.add(nb)
                out.append(
                    StageCandidate(
                        lane="local_seed",
                        path=nb,
                        reason="same_package_neighbor",
                        subsystem_tag=infer_file_subsystem(nb),
                    )
                )
    return out


def _collect_lexical_residual(
    full_lexical_sorted: Sequence[RetrievalHit],
    excluded: Set[str],
    *,
    limit: int,
) -> List[StageCandidate]:
    out: List[StageCandidate] = []
    for h in full_lexical_sorted:
        if h.relative_path in excluded:
            continue
        out.append(
            StageCandidate(
                lane="lexical_residual",
                path=h.relative_path,
                reason="global_lexical_order",
                subsystem_tag=infer_file_subsystem(h.relative_path),
            )
        )
        if len(out) >= limit:
            break
    return out


def _initial_quotas(task_type: str, *, has_owner: bool, anchored_owner_like: bool) -> Dict[str, int]:
    tt = (task_type or "").strip()
    if tt == "EXPLAIN_DEBUG":
        # Totals 20 with or without owner row (owner replaces one symbol slot).
        if anchored_owner_like:
            q = {
                "owner_injected": 1 if has_owner else 0,
                "symbol_seed": 4 if has_owner else 5,
                "package_seed": 3,
                "local_seed": 10,
                "lexical_residual": 2,
            }
        else:
            q = {
                "owner_injected": 1 if has_owner else 0,
                "symbol_seed": 3 if has_owner else 4,
                "package_seed": 3,
                "local_seed": 10,
                "lexical_residual": 3,
            }
    else:
        if anchored_owner_like:
            q = {
                "owner_injected": 1 if has_owner else 0,
                "symbol_seed": 5 if has_owner else 6,
                "package_seed": 5,
                "local_seed": 5,
                "lexical_residual": 4,
            }
        else:
            q = {
                "owner_injected": 1 if has_owner else 0,
                "symbol_seed": 4 if has_owner else 5,
                "package_seed": 5,
                "local_seed": 5,
                "lexical_residual": 5,
            }
    return q


_REALLOC_ORDER = ("symbol_seed", "local_seed", "package_seed", "lexical_residual")


def _reallocate_empty_lane_quotas(
    targets: Dict[str, int],
    pending: Dict[str, List[StageCandidate]],
) -> None:
    """
    If a lane has no pending candidates, its quota is unused — move those slots to
    the first non-empty lane in locked priority order (symbol → local → package → lexical).
    """
    spare = 0
    for lane in list(targets.keys()):
        if not pending.get(lane):
            spare += int(targets.pop(lane, 0))
    if spare <= 0:
        return
    for lane in _REALLOC_ORDER:
        if pending.get(lane):
            targets[lane] = int(targets.get(lane, 0)) + spare
            return


def _cap_targets_to_pending_and_spill(
    targets: Dict[str, int],
    pending: Dict[str, List[StageCandidate]],
) -> None:
    """Spill quota that exceeds available distinct candidates into the first lane that can absorb."""
    spare = 0
    for lane in list(targets.keys()):
        have = len(pending.get(lane) or ())
        want = int(targets.get(lane, 0))
        if want > have:
            spare += want - have
            targets[lane] = have
    if spare <= 0:
        return
    for lane in _REALLOC_ORDER:
        if pending.get(lane):
            targets[lane] = int(targets.get(lane, 0)) + spare
            return


def _merge_lanes_with_quotas(
    lanes: Dict[str, List[StageCandidate]],
    quotas: Dict[str, int],
    pool_size: int,
) -> List[StageCandidate]:
    """Round-robin fill per quota, then realloc unused slots in locked priority order."""
    pending: Dict[str, List[StageCandidate]] = {k: list(v) for k, v in lanes.items()}
    targets = dict(quotas)
    _reallocate_empty_lane_quotas(targets, pending)
    _cap_targets_to_pending_and_spill(targets, pending)
    merged: List[StageCandidate] = []
    used_paths: Set[str] = set()

    def take_from(lane: str) -> bool:
        while pending.get(lane):
            c = pending[lane][0]
            if c.path not in used_paths:
                used_paths.add(c.path)
                merged.append(c)
                pending[lane].pop(0)
                return True
            pending[lane].pop(0)
        return False

    order_round = ("owner_injected", "symbol_seed", "package_seed", "local_seed", "lexical_residual")
    guard = 0
    while len(merged) < pool_size and guard < pool_size * 40:
        guard += 1
        progressed = False
        for lane in order_round:
            if len(merged) >= pool_size:
                break
            if targets.get(lane, 0) <= 0:
                continue
            if not pending.get(lane):
                continue
            if take_from(lane):
                targets[lane] = max(0, int(targets[lane]) - 1)
                progressed = True
        if not progressed:
            _cap_targets_to_pending_and_spill(targets, pending)
            if not any(int(targets.get(l, 0)) > 0 and pending.get(l) for l in order_round):
                break

    spare = pool_size - len(merged)
    if spare > 0:
        for extra_lane in _REALLOC_ORDER:
            if spare <= 0:
                break
            for _ in range(spare):
                if len(merged) >= pool_size:
                    break
                if not pending.get(extra_lane):
                    continue
                if take_from(extra_lane):
                    spare = pool_size - len(merged)

    guard = 0
    while len(merged) < pool_size and guard < pool_size * 40:
        guard += 1
        progressed = False
        for lane in _REALLOC_ORDER:
            if len(merged) >= pool_size:
                break
            if pending.get(lane) and take_from(lane):
                progressed = True
        if not progressed:
            break

    return merged


def _apply_generic_infra_cap(
    candidates: List[StageCandidate],
    *,
    tokens: Tuple[str, ...],
    selected_resolved: Optional[str],
    pool_size: int,
) -> List[StageCandidate]:
    allow_extra = _query_explicit_infra(tokens)
    if selected_resolved:
        pol = classify_file(selected_resolved)
        if pol.file_class == "config" or _is_generic_infra_path(selected_resolved):
            allow_extra = True
    if allow_extra:
        return candidates[:pool_size]

    out: List[StageCandidate] = []
    gen_count = 0
    for c in candidates:
        if len(out) >= pool_size:
            break
        is_gen = _is_generic_infra_path(c.path)
        protected = c.injected or c.lane == "owner_injected"
        if is_gen and not protected:
            gen_count += 1
            if gen_count > 2:
                continue
        out.append(c)
    if len(out) < pool_size:
        for c in candidates:
            if len(out) >= pool_size:
                break
            if c in out:
                continue
            if c.path in {x.path for x in out}:
                continue
            out.append(c)
    return out[:pool_size]


def generate_candidates(
    *,
    index: WorkspaceFileIndex,
    query: str,
    tokens: Tuple[str, ...],
    task_type: str,
    selected_file: Optional[str],
    active_file: Optional[str],
    authority_resolution: Optional[Mapping[str, Any]],
    full_lexical_sorted: Sequence[RetrievalHit],
    pool_size: int = 20,
) -> Tuple[List[StageCandidate], Dict[str, Any]]:
    """
    Build a deterministic Stage A candidate pool with lane labels.

    Does not assign final lexical/fusion ranks.
    """
    path_set = {e.relative_path for e in index.files}
    debug = (task_type or "").strip() == "EXPLAIN_DEBUG"
    intent = classify_intent(query)
    allow_non_code_assets = query_explicit_non_code_asset_intent(tokens)

    owner_path = _primary_owner_file(authority_resolution)
    anchored_owner_like = bool(intent.symbol_tokens) or bool(owner_path)
    owner_cands: List[StageCandidate] = []
    resolved_injection_path, owner_trace_extra = _resolve_best_authority_file_path(
        authority_resolution,
        path_set,
    )
    if resolved_injection_path and _candidate_eligible_for_task(
        resolved_injection_path,
        anchored_owner_like=anchored_owner_like,
        task_type=task_type,
        allow_non_code_assets=allow_non_code_assets,
    ):
        inj_reason = (
            "authority_collaborator_owner"
            if owner_trace_extra.get("resolution_source") == "collaborator"
            else (
                "authority_entry_point_owner"
                if owner_trace_extra.get("resolution_source") == "entry_point"
                else "authority_primary_owner"
            )
        )
        owner_cands.append(
            StageCandidate(
                lane="owner_injected",
                path=resolved_injection_path,
                reason=inj_reason,
                subsystem_tag=infer_file_subsystem(resolved_injection_path),
                injected=True,
            )
        )

    anchored_owner_like = bool(owner_cands) or bool(intent.symbol_tokens)
    quotas = _initial_quotas(task_type, has_owner=bool(owner_cands), anchored_owner_like=anchored_owner_like)

    sym_limit = quotas["symbol_seed"] + 5
    sym = _filter_candidates_for_task(
        _collect_symbol_seeds(index, query, tokens, limit=sym_limit),
        anchored_owner_like=anchored_owner_like,
        task_type=task_type,
        allow_non_code_assets=allow_non_code_assets,
    )
    pkg = _filter_candidates_for_task(
        _collect_package_seeds(index, tokens, limit=quotas["package_seed"] + 8),
        anchored_owner_like=anchored_owner_like,
        task_type=task_type,
        allow_non_code_assets=allow_non_code_assets,
    )
    neighbor_cap = 24 if debug else 12
    loc = _collect_local_seeds(
        index,
        selected_file,
        active_file or selected_file,
        neighbor_cap=neighbor_cap,
        anchored_owner_like=anchored_owner_like,
        tokens=tokens,
        task_type=task_type,
    )

    excluded: Set[str] = set()
    for lst in (owner_cands, sym, pkg, loc):
        for c in lst:
            excluded.add(c.path)

    lex_budget = quotas["lexical_residual"] + pool_size
    lex = _filter_candidates_for_task(
        _collect_lexical_residual(full_lexical_sorted, excluded, limit=lex_budget),
        anchored_owner_like=anchored_owner_like,
        task_type=task_type,
        allow_non_code_assets=allow_non_code_assets,
    )

    lanes = {
        "owner_injected": owner_cands,
        "symbol_seed": sym,
        "package_seed": pkg,
        "local_seed": loc,
        "lexical_residual": lex,
    }

    merged = _merge_lanes_with_quotas(lanes, quotas, pool_size)

    sel_resolved: Optional[str] = None
    if selected_file:
        sel_resolved = _resolve_editor_file_in_index(selected_file, path_set)

    if debug and sel_resolved:
        have_sel = any(c.path == sel_resolved for c in merged)
        if not have_sel:
            merged.insert(
                0,
                StageCandidate(
                    lane="local_seed",
                    path=sel_resolved,
                    reason="selected_file_mandatory_injection",
                    subsystem_tag=infer_file_subsystem(sel_resolved),
                    injected=True,
                ),
            )
        # Enforce 50% local lane: replace tail lexical with local neighbors if needed.
        local_paths = {c.path for c in merged if c.lane == "local_seed"}
        need_local = max(0, (pool_size + 1) // 2 - len(local_paths))
        if need_local > 0:
            extras = _collect_local_seeds(
                index,
                selected_file,
                active_file or selected_file,
                neighbor_cap=48,
                anchored_owner_like=anchored_owner_like,
                tokens=tokens,
                task_type=task_type,
            )
            already = {c.path for c in merged}
            for ex in extras:
                if need_local <= 0:
                    break
                if ex.path not in already and ex.path not in local_paths:
                    merged.append(
                        StageCandidate(
                            lane="local_seed",
                            path=ex.path,
                            reason="local_quota_fill",
                            subsystem_tag=ex.subsystem_tag,
                        )
                    )
                    already.add(ex.path)
                    need_local -= 1

    merged = merged[:pool_size * 2]
    merged = _apply_generic_infra_cap(
        merged,
        tokens=tokens,
        selected_resolved=sel_resolved,
        pool_size=pool_size,
    )

    # Dedup preserve order
    seen: Set[str] = set()
    deduped: List[StageCandidate] = []
    for c in merged:
        if c.path in seen:
            continue
        seen.add(c.path)
        deduped.append(c)
        if len(deduped) >= pool_size:
            break

    # Final fill from lexical if short
    if len(deduped) < pool_size:
        excl = set(seen)
        for h in full_lexical_sorted:
            if len(deduped) >= pool_size:
                break
            if h.relative_path in excl:
                continue
            if not _candidate_eligible_for_task(
                h.relative_path,
                anchored_owner_like=anchored_owner_like,
                task_type=task_type,
                allow_non_code_assets=allow_non_code_assets,
            ):
                continue
            deduped.append(
                StageCandidate(
                    lane="lexical_residual",
                    path=h.relative_path,
                    reason="pool_fill_lexical",
                    subsystem_tag=infer_file_subsystem(h.relative_path),
                )
            )
            excl.add(h.relative_path)

    owner_in_pool = bool(resolved_injection_path) and any(
        c.path == resolved_injection_path for c in deduped
    )
    authority_owner_trace: Dict[str, Any] = {
        "primary_owner_file": owner_path or "",
        "resolved_in_index": bool(resolved_injection_path),
        "in_stage_a_pool": owner_in_pool,
    }
    authority_owner_trace.update(owner_trace_extra)
    if owner_path and not resolved_injection_path:
        authority_owner_trace["note"] = "primary_collaborators_entry_points_not_found_in_workspace_index"
    elif resolved_injection_path and not owner_in_pool:
        authority_owner_trace["note"] = "authority_file_resolved_but_not_in_final_stage_a_pool"

    diag: Dict[str, Any] = {
        "pool_size": pool_size,
        "quotas": quotas,
        "task_type": task_type,
        "debug": debug,
        "lanes_sizes": {k: len(v) for k, v in lanes.items()},
        "candidates": [c.to_diag() for c in deduped],
        "authority_owner_trace": authority_owner_trace,
    }
    return deduped, diag

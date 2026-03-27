"""
Lexical-first retrieval over A4 ``WorkspaceFileIndex`` with deterministic policy bias.

Any change to ranking logic must be validated via PR-6 audit suite on real repo
before merge.
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from runtime.layer5.index.models import FileIndexEntry, WorkspaceFileIndex
from runtime.layer5.index.symbol_inventory import (
    normalize_identifier_tokens,
    resolve_symbol_lookup_for_index,
)

from runtime.layer5.retrieval.config import LexicalRetrievalConfig, get_retrieval_policy
from runtime.layer5.retrieval.intent import classify_intent
from runtime.layer5.retrieval.models import RetrievalHit, RetrievalResult
from runtime.layer5.retrieval.policy import (
    FilePolicy,
    classify_file,
    infer_code_debug_intent,
    infer_query_subsystems,
    is_generic_eventbus_java_handler,
    is_noise_class,
    is_support_style_java_basename,
    looks_like_symbol_token,
    query_duplicate_incident_focus,
    query_ingestion_focus,
    query_topology_focus,
)
from runtime.layer5.retrieval.query import normalize_query


def _basename(rel: str) -> str:
    if "/" not in rel:
        return rel
    return rel.rsplit("/", 1)[-1]


def _raw_content_score(
    root: Path,
    entry: FileIndexEntry,
    tokens: Tuple[str, ...],
    cfg: LexicalRetrievalConfig,
) -> int:
    if not tokens or not cfg.read_file_contents:
        return 0
    path = root / entry.relative_path
    text = _read_content_lower_cached(
        str(path),
        int(entry.mtime_ns),
        int(entry.size_bytes),
        int(cfg.max_content_bytes),
    )
    if not text:
        return 0
    return sum(text.count(t) * cfg.weight_content for t in tokens)


@lru_cache(maxsize=16_384)
def _read_content_lower_cached(
    abs_path: str,
    mtime_ns: int,
    size_bytes: int,
    max_content_bytes: int,
) -> str:
    """
    Cache lowercased file content slices across retrieval calls.
    Key includes file fingerprint fields from index entries (mtime/size) plus read cap,
    so cache remains deterministic and safe when files change.
    """
    _ = mtime_ns, size_bytes
    try:
        data = Path(abs_path).read_bytes()[:max_content_bytes]
    except (OSError, PermissionError):
        return ""
    return data.decode("utf-8", errors="replace").lower()


def _apply_code_intent_content(
    raw_content: int,
    fpolicy: FilePolicy,
    code_intent_active: bool,
    cfg: LexicalRetrievalConfig,
    basename: str,
) -> Tuple[int, int, int, int]:
    """
    Returns ``(effective_content, noise_content_suppressed, config_content_trimmed,
    support_style_content_trimmed)``.
    """
    if not code_intent_active or not cfg.enable_code_debug_content_gating:
        return raw_content, 0, 0, 0
    fc = fpolicy.file_class
    if fc in cfg.code_intent_zero_content_classes:
        suppressed = 1 if raw_content > 0 else 0
        return 0, suppressed, 0, 0
    if fc == "config" and cfg.code_intent_config_content_cap is not None:
        cap = max(0, int(cfg.code_intent_config_content_cap))
        if raw_content > cap:
            return cap, 0, raw_content - cap, 0
        return raw_content, 0, 0, 0
    if (
        is_support_style_java_basename(basename)
        and fc in ("core_aiops_code", "supporting_prod_code")
        and cfg.code_intent_support_style_content_cap is not None
    ):
        cap = max(0, int(cfg.code_intent_support_style_content_cap))
        if raw_content > cap:
            return cap, 0, 0, raw_content - cap
    return raw_content, 0, 0, 0


def _path_hints_exempt_topic_supporting_cap(
    rel_l: str,
    *,
    topology_focus: bool,
    ingestion_focus: bool,
) -> bool:
    """
    If the path already encodes topic-relevant structure, do not apply the broad
    supporting-class content cap (PR-6 Slice 5).
    """
    if topology_focus:
        topo_hints = (
            "topology",
            "topo",
            "graph",
            "node",
            "edge",
            "anomaly",
            "cache",
            "store",
            "metric",
            "aiops",
            "ingestion",
            "dependency",
        )
        if any(h in rel_l for h in topo_hints):
            return True
    if ingestion_focus:
        ing_hints = (
            "ingestion",
            "ingest",
            "pipeline",
            "parser",
            "collector",
            "aiops",
            "dependency",
        )
        if any(h in rel_l for h in ing_hints):
            return True
    return False


def _apply_topic_focus_supporting_content_cap(
    effective_content: int,
    *,
    rel_l: str,
    fpolicy: FilePolicy,
    code_intent_active: bool,
    cfg: LexicalRetrievalConfig,
    narrow_owner_signal: bool,
    query_tokens: Tuple[str, ...],
) -> Tuple[int, int]:
    """
    Cap keyword mass for *supporting* production Java that lacks basename/symbol owner
    signals when the query is topology- or ingestion-focused, unless the path already
    encodes topic hints (see ``_path_hints_exempt_topic_supporting_cap``).
    Returns ``(content, topic_focus_supporting_content_trimmed)``.
    """
    if not code_intent_active or not cfg.enable_code_debug_content_gating:
        return effective_content, 0
    cap = cfg.code_intent_generic_facade_content_cap
    if cap is None:
        return effective_content, 0
    cap = max(0, int(cap))
    if fpolicy.file_class != "supporting_prod_code":
        return effective_content, 0
    if "/src/main/java/" not in rel_l:
        return effective_content, 0
    if narrow_owner_signal:
        return effective_content, 0
    tf = query_topology_focus(query_tokens)
    inf = query_ingestion_focus(query_tokens)
    if not (tf or inf):
        return effective_content, 0
    if _path_hints_exempt_topic_supporting_cap(rel_l, topology_focus=tf, ingestion_focus=inf):
        return effective_content, 0
    if effective_content > cap:
        return cap, effective_content - cap
    return effective_content, 0


def _apply_generic_facade_content_cap(
    effective_content: int,
    *,
    relative_path: str,
    base_name: str,
    fpolicy: FilePolicy,
    code_intent_active: bool,
    cfg: LexicalRetrievalConfig,
    narrow_owner_signal: bool,
    query_tokens: Tuple[str, ...],
) -> Tuple[int, int]:
    """
    PR-6 Slice 5: cap keyword mass for generic ``eventbus`` handlers when the query is
    topology- or ingestion-focused and the file lacks direct owner evidence.
    ``narrow_owner_signal`` is true when basename/query specificity or basename symbol
    match fires — not symbol-inventory body overlap alone.
    Returns ``(content, generic_facade_content_trimmed)``.
    """
    if not code_intent_active or not cfg.enable_code_debug_content_gating:
        return effective_content, 0
    cap = cfg.code_intent_generic_facade_content_cap
    if cap is None:
        return effective_content, 0
    cap = max(0, int(cap))
    if narrow_owner_signal:
        return effective_content, 0
    if fpolicy.file_class not in ("core_aiops_code", "supporting_prod_code"):
        return effective_content, 0
    rel_l = relative_path.lower()
    if "/src/main/java/" not in rel_l:
        return effective_content, 0
    if not is_generic_eventbus_java_handler(relative_path, base_name):
        return effective_content, 0
    if not (query_topology_focus(query_tokens) or query_ingestion_focus(query_tokens)):
        return effective_content, 0
    if effective_content > cap:
        return cap, effective_content - cap
    return effective_content, 0


def _scaled(score: float, cfg: LexicalRetrievalConfig) -> int:
    return int(round(score * cfg.policy_score_scale))


def _basename_query_specificity(
    basename: str,
    query_tokens: Tuple[str, ...],
    policy: Mapping,
    cfg: LexicalRetrievalConfig,
) -> int:
    """
    PR-6 Slice 4: reward basenames whose CamelCase stem tokens overlap query tokens.

    Helps ``AlertCorrelationEngine`` beat ``AvailabilityCorrelationEngine`` when the query
    contains ``alert`` but not ``availability``.
    """
    per = float(policy.get("basename_query_specificity_per_token", 0.0))
    if per <= 0 or not query_tokens:
        return 0
    stem = Path(basename).stem
    if not stem:
        return 0
    stem_toks: Set[str] = set(normalize_identifier_tokens(stem))
    if not stem_toks:
        return 0
    inter = stem_toks.intersection(set(query_tokens))
    if not inter:
        return 0
    cap = int(policy.get("basename_query_specificity_token_cap", 8))
    n = min(len(inter), max(cap, 0))
    return _scaled(per * n, cfg)


def _ingestion_log_parser_demotion(
    basename: str,
    rel_l: str,
    fpolicy: FilePolicy,
    code_intent_active: bool,
    policy: Mapping,
    cfg: LexicalRetrievalConfig,
    tokens: Tuple[str, ...],
) -> int:
    """Demote ``log/.../*Parser.java`` when the query is ingestion/pipeline/collector focused."""
    dem = float(policy.get("code_intent_ingestion_log_parser_demotion", 0.0))
    if dem <= 0 or not code_intent_active or not cfg.enable_policy_bias:
        return 0
    if not query_ingestion_focus(tokens):
        return 0
    if "/log/" not in rel_l:
        return 0
    if not basename.lower().endswith("parser.java"):
        return 0
    if fpolicy.file_class not in ("core_aiops_code", "supporting_prod_code"):
        return 0
    return _scaled(dem, cfg)


def _generic_integration_demotion(
    basename: str,
    rel_l: str,
    fpolicy: FilePolicy,
    code_intent_active: bool,
    policy: Mapping,
    cfg: LexicalRetrievalConfig,
    tokens: Tuple[str, ...],
) -> int:
    """PR-6 Slice 5: demote generic ``*Integration.java`` in ``integration/`` on duplicate-incident queries."""
    dem = float(policy.get("code_intent_generic_integration_demotion", 0.0))
    if dem <= 0 or not code_intent_active or not cfg.enable_policy_bias:
        return 0
    if not query_duplicate_incident_focus(tokens):
        return 0
    ts = set(tokens)
    if ts.intersection({"integration", "servicenow", "bidirectional"}):
        return 0
    if fpolicy.file_class != "supporting_prod_code":
        return 0
    if "/integration/" not in rel_l:
        return 0
    if not basename.lower().endswith("integration.java"):
        return 0
    return _scaled(dem, cfg)


def _duplicate_incident_core_boost(
    base_name: str,
    rel_l: str,
    fpolicy: FilePolicy,
    code_intent_active: bool,
    policy: Mapping,
    cfg: LexicalRetrievalConfig,
    tokens: Tuple[str, ...],
) -> int:
    """PR-6 Slice 5: boost core AIOps behavioral classes on duplicate+incident queries."""
    boost = float(policy.get("code_intent_duplicate_incident_core_boost", 0.0))
    if boost <= 0 or not code_intent_active or not cfg.enable_policy_bias:
        return 0
    if not query_duplicate_incident_focus(tokens):
        return 0
    if fpolicy.file_class != "core_aiops_code":
        return 0
    if "/src/main/java/" not in rel_l:
        return 0
    stem = Path(base_name).stem
    stem_toks = set(normalize_identifier_tokens(stem))
    behavior = frozenset(
        {
            "processor",
            "query",
            "correlation",
            "manager",
            "dependency",
            "parser",
            "pipeline",
            "engine",
            "availability",
        }
    )
    if not stem_toks.intersection(behavior):
        return 0
    return _scaled(boost, cfg)


def _support_file_demotion(
    basename: str,
    rel_l: str,
    fpolicy: FilePolicy,
    code_intent_active: bool,
    policy: Mapping,
    cfg: LexicalRetrievalConfig,
) -> int:
    """PR-6 Slice 4: demote broad *Constants / *Utils / … Java owners under code intent."""
    dem = float(policy.get("code_intent_support_file_demotion", 0.0))
    if dem <= 0 or not code_intent_active or not cfg.enable_policy_bias:
        return 0
    if fpolicy.file_class not in ("core_aiops_code", "supporting_prod_code"):
        return 0
    if "/src/main/java/" not in rel_l:
        return 0
    if not is_support_style_java_basename(basename):
        return 0
    return _scaled(dem, cfg)


def _symbol_boost(
    entry: FileIndexEntry,
    tokens: Tuple[str, ...],
    cfg: LexicalRetrievalConfig,
    policy: Mapping,
) -> int:
    if not tokens:
        return 0
    basename = _basename(entry.relative_path).lower()
    stem = basename.rsplit(".", 1)[0]
    stem_parts = tuple(x for x in stem.replace("-", "_").split("_") if x)
    for token in tokens:
        if not looks_like_symbol_token(token):
            continue
        if token == stem or token in stem_parts:
            return _scaled(float(policy["symbol_boost"]), cfg)
    return 0


def _module_bias(
    entry: FileIndexEntry,
    tokens: Tuple[str, ...],
    cfg: LexicalRetrievalConfig,
    policy: Mapping,
) -> int:
    if not tokens:
        return 0
    parts = set(entry.relative_path.lower().split("/"))
    common = [t for t in tokens if len(t) >= 4 and t in parts]
    if common:
        return _scaled(float(policy["module_bias"]), cfg)
    return 0


def _symbol_inventory_boost(
    entry: FileIndexEntry,
    tokens: Tuple[str, ...],
    cfg: LexicalRetrievalConfig,
    policy: Mapping,
    symbol_lookup: Mapping[str, Tuple[str, ...]],
) -> int:
    if not tokens:
        return 0
    inv_tokens = symbol_lookup.get(entry.relative_path, ())
    if not inv_tokens:
        return 0
    inv_set = set(inv_tokens)
    token_set = set(tokens)
    if token_set.intersection(inv_set):
        exact = _scaled(float(policy.get("symbol_inventory_exact_boost", 0.0)), cfg)
        overlap = len(token_set.intersection(inv_set))
        cap = int(policy.get("symbol_inventory_overlap_cap", 3))
        overlap = min(overlap, max(cap, 0))
        token_part = _scaled(float(policy.get("symbol_inventory_token_boost", 0.0)), cfg) * overlap
        return exact + token_part
    return 0


def _is_core_aiops_hit(hit: RetrievalHit) -> bool:
    return classify_file(hit.relative_path).file_class == "core_aiops_code"


def _apply_top_k_core_correction(sorted_hits: List[RetrievalHit], top_k: int) -> List[RetrievalHit]:
    """
    If no core AIOps file sits in ranks 0–2 but a core candidate exists later
    in the full deterministic ordering, swap it into the weakest top-3 slot
    (prefer replacing noise). Keeps list length ``top_k`` when possible.
    """
    if top_k <= 0 or not sorted_hits:
        return []
    tops = list(sorted_hits[:top_k])
    if len(tops) < 3:
        return tops
    if any(_is_core_aiops_hit(tops[i]) for i in range(3)):
        return tops

    core_hit: RetrievalHit | None = None
    for h in sorted_hits:
        if _is_core_aiops_hit(h):
            core_hit = h
            break
    if core_hit is None:
        return tops

    core_in_tops = next((i for i, h in enumerate(tops) if h.relative_path == core_hit.relative_path), None)
    if core_in_tops is not None and core_in_tops < 3:
        return tops

    noise_indices = [
        i
        for i in range(3)
        if is_noise_class(classify_file(tops[i].relative_path).file_class)
    ]
    if noise_indices:
        replace_i = min(noise_indices, key=lambda i: (tops[i].score, tops[i].relative_path))
    else:
        replace_i = min(range(3), key=lambda i: (tops[i].score, tops[i].relative_path))

    if core_in_tops is not None:
        tops[replace_i], tops[core_in_tops] = tops[core_in_tops], tops[replace_i]
    else:
        tops[replace_i] = core_hit

    return tops


def _symbol_aligned_basename(hit: RetrievalHit, symbol_tokens: Tuple[str, ...]) -> bool:
    if not symbol_tokens:
        return False
    stem = Path(_basename(hit.relative_path)).stem
    if not stem:
        return False
    stem_tokens = set(normalize_identifier_tokens(stem))
    if not stem_tokens:
        return False
    symbol_set = {t.lower() for t in symbol_tokens}
    stem_l = stem.lower()
    if stem_l in symbol_set:
        return True
    overlap = stem_tokens.intersection(symbol_set)
    return len(overlap) >= 2


def _apply_top_k_symbol_owner_correction(
    sorted_hits: List[RetrievalHit],
    top_k: int,
    symbol_tokens: Tuple[str, ...],
) -> List[RetrievalHit]:
    """
    L5.8 narrow hardening: for symbol-targeting queries, ensure at least one symbol-aligned
    basename candidate appears in top-3 when such a candidate exists in the ranked list.
    Deterministic swap-only correction; no broad recall expansion.
    """
    if top_k <= 0 or not sorted_hits or not symbol_tokens:
        return list(sorted_hits[:top_k])
    tops = list(sorted_hits[:top_k])
    if len(tops) < 3:
        return tops
    if any(_symbol_aligned_basename(h, symbol_tokens) for h in tops[:3]):
        return tops
    symbol_hit: RetrievalHit | None = None
    for h in sorted_hits:
        if _symbol_aligned_basename(h, symbol_tokens):
            symbol_hit = h
            break
    if symbol_hit is None:
        return tops

    in_tops_idx = next((i for i, h in enumerate(tops) if h.relative_path == symbol_hit.relative_path), None)
    replace_i = min(range(3), key=lambda i: (tops[i].score, tops[i].relative_path))
    if in_tops_idx is not None:
        tops[replace_i], tops[in_tops_idx] = tops[in_tops_idx], tops[replace_i]
    else:
        tops[replace_i] = symbol_hit
    return tops


def _score_entry(
    entry: FileIndexEntry,
    tokens: Tuple[str, ...],
    root: Path,
    cfg: LexicalRetrievalConfig,
    policy: Mapping,
    symbol_lookup: Mapping[str, Tuple[str, ...]],
    code_intent_active: bool,
) -> RetrievalHit:
    if not tokens:
        return RetrievalHit(
            relative_path=entry.relative_path,
            score=0,
            breakdown={
                "path_substrings": 0,
                "basename_substrings": 0,
                "content_substrings": 0,
            },
            diagnostics=None,
        )

    rel_l = entry.relative_path.lower()
    base_name = _basename(entry.relative_path)
    base_l = base_name.lower()
    fpolicy = classify_file(entry.relative_path)
    query_subsystems = infer_query_subsystems(tokens)

    path_part = sum(rel_l.count(t) * cfg.weight_path for t in tokens)
    base_part = sum(base_l.count(t) * cfg.weight_basename for t in tokens)
    raw_content = _raw_content_score(root, entry, tokens, cfg)

    symbol_boost = _symbol_boost(entry, tokens, cfg, policy) if cfg.enable_policy_bias else 0
    symbol_inventory_boost = (
        _symbol_inventory_boost(entry, tokens, cfg, policy, symbol_lookup) if cfg.enable_policy_bias else 0
    )
    basename_specificity = 0
    if code_intent_active and cfg.enable_policy_bias:
        basename_specificity = _basename_query_specificity(base_name, tokens, policy, cfg)
    owner_evidence = (
        (basename_specificity > 0) or (symbol_inventory_boost > 0) or (symbol_boost > 0)
    )
    direct_owner_alignment = 1 if owner_evidence else 0
    owner_evidence_score = basename_specificity + symbol_inventory_boost + symbol_boost
    # Facade/supporting caps: exclude symbol_inventory alone (can overmatch body text).
    # Treat owner signal as strong only with symbol match OR sufficiently specific basename overlap.
    # This keeps generic one-token overlaps from bypassing deterministic content caps.
    narrow_owner_signal_for_facade = (
        (symbol_boost > 0)
        or (basename_specificity >= int(cfg.weak_owner_signal_min_specificity))
    )

    content_part, noise_content_suppressed, config_content_trimmed, support_style_content_trimmed = (
        _apply_code_intent_content(raw_content, fpolicy, code_intent_active, cfg, base_name)
    )
    content_part, generic_facade_content_trimmed = _apply_generic_facade_content_cap(
        content_part,
        relative_path=entry.relative_path,
        base_name=base_name,
        fpolicy=fpolicy,
        code_intent_active=code_intent_active,
        cfg=cfg,
        narrow_owner_signal=narrow_owner_signal_for_facade,
        query_tokens=tokens,
    )
    content_part, topic_focus_supporting_content_trimmed = _apply_topic_focus_supporting_content_cap(
        content_part,
        rel_l=rel_l,
        fpolicy=fpolicy,
        code_intent_active=code_intent_active,
        cfg=cfg,
        narrow_owner_signal=narrow_owner_signal_for_facade,
        query_tokens=tokens,
    )
    prior_map = policy["path_prior"]
    class_prior = 0.0
    if isinstance(prior_map, Mapping):
        class_prior = float(prior_map.get(fpolicy.file_class, 0.0))
    path_prior = _scaled(class_prior, cfg) if cfg.enable_policy_bias else 0
    subsystem_boost = (
        _scaled(float(policy["subsystem_boost"]), cfg)
        if cfg.enable_policy_bias
        and fpolicy.subsystem in query_subsystems
        and fpolicy.subsystem != "unknown"
        else 0
    )
    module_bias = _module_bias(entry, tokens, cfg, policy) if cfg.enable_policy_bias else 0
    noise_penalty = 0
    if cfg.enable_policy_bias and is_noise_class(fpolicy.file_class):
        mult = float(policy["noise_penalty_multiplier"])
        noise_penalty = _scaled(abs(class_prior) * mult, cfg)
    main_java_bonus = 0
    if (
        code_intent_active
        and cfg.enable_policy_bias
        and "/src/main/java/" in rel_l
        and fpolicy.file_class in ("core_aiops_code", "supporting_prod_code")
    ):
        main_java_bonus = _scaled(float(policy.get("code_intent_main_java_bonus", 0.0)), cfg)
    support_file_demotion = 0
    if code_intent_active and cfg.enable_policy_bias:
        support_file_demotion = _support_file_demotion(
            base_name, rel_l, fpolicy, code_intent_active, policy, cfg
        )
    generic_integration_demotion = _generic_integration_demotion(
        base_name, rel_l, fpolicy, code_intent_active, policy, cfg, tokens
    )
    ingestion_log_parser_demotion = _ingestion_log_parser_demotion(
        base_name, rel_l, fpolicy, code_intent_active, policy, cfg, tokens
    )
    duplicate_incident_core_boost = _duplicate_incident_core_boost(
        base_name, rel_l, fpolicy, code_intent_active, policy, cfg, tokens
    )
    total = (
        path_part
        + base_part
        + content_part
        + path_prior
        + subsystem_boost
        + symbol_boost
        + symbol_inventory_boost
        + module_bias
        - noise_penalty
        + main_java_bonus
        + basename_specificity
        - support_file_demotion
        - generic_integration_demotion
        - ingestion_log_parser_demotion
        + duplicate_incident_core_boost
    )
    policy_part = (
        path_prior
        + subsystem_boost
        + symbol_boost
        + symbol_inventory_boost
        + module_bias
        - noise_penalty
        + main_java_bonus
        + basename_specificity
        - support_file_demotion
        - generic_integration_demotion
        - ingestion_log_parser_demotion
        + duplicate_incident_core_boost
    )
    diagnostics: Optional[Dict[str, int]] = None
    if cfg.include_score_diagnostics:
        diagnostics = {
            "path_lexical": path_part,
            "basename_lexical": base_part,
            "content": content_part,
            "path_prior": path_prior,
            "subsystem_boost": subsystem_boost,
            "symbol_boost": symbol_boost,
            "symbol_inventory_boost": symbol_inventory_boost,
            "module_bias": module_bias,
            "noise_penalty": noise_penalty,
            "main_java_bonus": main_java_bonus,
            "noise_content_suppressed": noise_content_suppressed,
            "config_content_trimmed": config_content_trimmed,
            "support_style_content_trimmed": support_style_content_trimmed,
            "generic_facade_content_trimmed": generic_facade_content_trimmed,
            "topic_focus_supporting_content_trimmed": topic_focus_supporting_content_trimmed,
            "code_intent": 1 if code_intent_active else 0,
            "basename_specificity": basename_specificity,
            "support_file_demotion": support_file_demotion,
            "owner_evidence_score": owner_evidence_score,
            "direct_owner_alignment": direct_owner_alignment,
            "generic_integration_demotion": generic_integration_demotion,
            "ingestion_log_parser_demotion": ingestion_log_parser_demotion,
            "duplicate_incident_core_boost": duplicate_incident_core_boost,
            "facade_cap_basename_or_symbol_owner_signal": 1 if narrow_owner_signal_for_facade else 0,
            "total": total,
        }
    return RetrievalHit(
        relative_path=entry.relative_path,
        score=total,
        breakdown={
            "path_substrings": path_part + policy_part,
            "basename_substrings": base_part,
            "content_substrings": content_part,
        },
        diagnostics=diagnostics,
    )


def retrieve_lexical(
    index: WorkspaceFileIndex,
    query: str,
    top_k: int,
    config: Optional[LexicalRetrievalConfig] = None,
) -> RetrievalResult:
    """
    Return top-k files from ``index`` for ``query`` using MVP lexical rules.

    Args:
        index: A4 workspace file index (may be stale vs disk).
        query: Raw user query string.
        top_k: Maximum hits (non-negative).
        config: Optional lexical config.

    Returns:
        ``RetrievalResult`` with deterministic ``hits`` ordering.
    """
    cfg = config or LexicalRetrievalConfig()
    policy = get_retrieval_policy(cfg.policy_version)
    tokens = normalize_query(query, min_token_len=cfg.min_token_len)
    intent = classify_intent(query)
    code_intent_active = (
        bool(cfg.code_debug_intent) if cfg.code_debug_intent is not None else infer_code_debug_intent(tokens)
    )
    root = Path(index.canonical_root)
    symbol_lookup = resolve_symbol_lookup_for_index(index)

    if top_k <= 0:
        return RetrievalResult(
            query_raw=query,
            query_tokens=tokens,
            top_k=top_k,
            hits=(),
            index_schema_version=index.schema_version,
            workspace_identity_hash=index.workspace_identity_hash,
        )

    scored: List[RetrievalHit] = [
        _score_entry(e, tokens, root, cfg, policy, symbol_lookup, code_intent_active) for e in index.files
    ]

    if not tokens:
        # Deterministic fallback: index.files is already sorted by relative_path
        chosen = tuple(
            RetrievalHit(
                relative_path=e.relative_path,
                score=0,
                breakdown={
                    "path_substrings": 0,
                    "basename_substrings": 0,
                    "content_substrings": 0,
                },
                diagnostics=None,
            )
            for e in index.files[:top_k]
        )
    else:
        scored.sort(key=lambda h: (-h.score, h.relative_path))
        if cfg.enable_top_k_core_correction:
            corrected = _apply_top_k_core_correction(scored, top_k)
            corrected = _apply_top_k_symbol_owner_correction(corrected, top_k, intent.symbol_tokens)
            chosen = tuple(corrected)
        else:
            corrected = _apply_top_k_symbol_owner_correction(scored, top_k, intent.symbol_tokens)
            chosen = tuple(corrected)

    return RetrievalResult(
        query_raw=query,
        query_tokens=tokens,
        top_k=top_k,
        hits=chosen,
        index_schema_version=index.schema_version,
        workspace_identity_hash=index.workspace_identity_hash,
    )

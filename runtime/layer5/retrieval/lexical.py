"""
Lexical-first retrieval over A4 ``WorkspaceFileIndex`` with deterministic policy bias.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import List, Optional, Tuple

from runtime.layer5.index.models import FileIndexEntry, WorkspaceFileIndex

from runtime.layer5.retrieval.config import LexicalRetrievalConfig, get_retrieval_policy
from runtime.layer5.retrieval.models import RetrievalHit, RetrievalResult
from runtime.layer5.retrieval.policy import (
    classify_file,
    infer_query_subsystems,
    is_noise_class,
    looks_like_symbol_token,
)
from runtime.layer5.retrieval.query import normalize_query


def _basename(rel: str) -> str:
    if "/" not in rel:
        return rel
    return rel.rsplit("/", 1)[-1]


def _content_score(
    root: Path,
    entry: FileIndexEntry,
    tokens: Tuple[str, ...],
    cfg: LexicalRetrievalConfig,
) -> int:
    if not tokens or not cfg.read_file_contents:
        return 0
    path = root / entry.relative_path
    try:
        data = path.read_bytes()[: cfg.max_content_bytes]
    except (OSError, PermissionError):
        return 0
    text = data.decode("utf-8", errors="replace").lower()
    return sum(text.count(t) * cfg.weight_content for t in tokens)


def _scaled(score: float, cfg: LexicalRetrievalConfig) -> int:
    return int(round(score * cfg.policy_score_scale))


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


def _score_entry(
    entry: FileIndexEntry,
    tokens: Tuple[str, ...],
    root: Path,
    cfg: LexicalRetrievalConfig,
    policy: Mapping,
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
        )

    rel_l = entry.relative_path.lower()
    base_l = _basename(entry.relative_path).lower()
    fpolicy = classify_file(entry.relative_path)
    query_subsystems = infer_query_subsystems(tokens)

    path_part = sum(rel_l.count(t) * cfg.weight_path for t in tokens)
    base_part = sum(base_l.count(t) * cfg.weight_basename for t in tokens)
    content_part = _content_score(root, entry, tokens, cfg)
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
    symbol_boost = _symbol_boost(entry, tokens, cfg, policy) if cfg.enable_policy_bias else 0
    module_bias = _module_bias(entry, tokens, cfg, policy) if cfg.enable_policy_bias else 0
    noise_penalty = 0
    if cfg.enable_policy_bias and is_noise_class(fpolicy.file_class):
        mult = float(policy["noise_penalty_multiplier"])
        noise_penalty = _scaled(abs(class_prior) * mult, cfg)
    total = path_part + base_part + content_part + path_prior + subsystem_boost + symbol_boost + module_bias - noise_penalty
    policy_part = path_prior + subsystem_boost + symbol_boost + module_bias - noise_penalty
    return RetrievalHit(
        relative_path=entry.relative_path,
        score=total,
        breakdown={
            "path_substrings": path_part + policy_part,
            "basename_substrings": base_part,
            "content_substrings": content_part,
        },
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
    root = Path(index.canonical_root)

    if top_k <= 0:
        return RetrievalResult(
            query_raw=query,
            query_tokens=tokens,
            top_k=top_k,
            hits=(),
            index_schema_version=index.schema_version,
            workspace_identity_hash=index.workspace_identity_hash,
        )

    scored: List[RetrievalHit] = [_score_entry(e, tokens, root, cfg, policy) for e in index.files]

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
            )
            for e in index.files[:top_k]
        )
    else:
        scored.sort(key=lambda h: (-h.score, h.relative_path))
        if cfg.enable_top_k_core_correction:
            chosen = tuple(_apply_top_k_core_correction(scored, top_k))
        else:
            chosen = tuple(scored[:top_k])

    return RetrievalResult(
        query_raw=query,
        query_tokens=tokens,
        top_k=top_k,
        hits=chosen,
        index_schema_version=index.schema_version,
        workspace_identity_hash=index.workspace_identity_hash,
    )

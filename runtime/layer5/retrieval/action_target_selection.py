"""
Deterministic plan/action target selection from an existing lexical ranked list.

Uses only paths already returned by retrieval — no new backends, no ML.
"""

from __future__ import annotations

import re
from typing import List, Optional, Sequence, Tuple


def _norm(p: str) -> str:
    return p.replace("\\", "/").strip()


def _tokenize_query(query: str) -> List[str]:
    raw = re.split(r"[^A-Za-z0-9_]+", query)
    out: List[str] = []
    for t in raw:
        tl = t.lower()
        if len(tl) >= 3:
            out.append(tl)
    return out


def _basename_stem(path: str) -> str:
    seg = _norm(path).split("/")[-1]
    if "." in seg:
        seg = seg.rsplit(".", 1)[0]
    return seg.lower()


def _camel_tokens(name: str) -> List[str]:
    if not name:
        return []
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    s = s.replace("_", " ")
    return [x.lower() for x in s.split() if len(x) >= 3]


def _java_subpackage(path: str) -> str:
    pl = _norm(path).lower()
    if "/com/mindarray/" not in pl:
        return ""
    i = pl.index("/com/mindarray/")
    tail = pl[i + 1 :]
    parts = [p for p in tail.split("/") if p]
    if len(parts) >= 4:
        return "/".join(parts[:4])
    return ""


def _path_penalty(path: str) -> float:
    pl = path.lower()
    pen = 0.0
    for bad in ("/test/", "/test-plugin", "/test/java/", "/docs/", "test-plugin-metrics"):
        if bad in pl:
            pen -= 120.0
    if pl.endswith(".json") or pl.endswith(".md"):
        pen -= 100.0
    return pen


def _query_domain_adjustments(query: str, path_lower: str, basename_stem: str) -> float:
    """
    Deterministic disambiguation: prefer role-shaped owners over generic UI/handler
    hits when the query names a more specific subsystem.
    """
    q = query.lower()
    bn = basename_stem.lower()
    pl = path_lower
    adj = 0.0

    if "collector" in q:
        if "/com/mindarray/log/" in pl:
            adj += 70.0
        if "collector" in bn:
            adj += 55.0
        elif "uiaction" in bn or bn.endswith("handler"):
            adj -= 55.0

    if ("metric" in q or "poll" in q or "derived" in q) and ("datastore" in q or "metric" in q):
        for hint in ("enricher", "poller", "datastore", "metricpoller"):
            if hint in bn.replace("_", ""):
                adj += 40.0
        if "derived" in q and "enricher" in bn:
            adj += 28.0
        if "objectconfig" in bn or "policycache" in bn or "uiaction" in bn:
            adj -= 28.0

    if "topology" in q or "cache store" in q:
        if "topology" in bn and ("store" in bn or "engine" in bn):
            adj += 35.0

    if "log" in q and "collector" not in q and ("parser" in q or "regex" in q):
        if "logparser" in bn.replace("_", "") or "logprocessor" in bn.replace("_", ""):
            adj += 30.0

    return adj


def _score_candidate(
    path: str,
    query: str,
    rank_index: int,
    ranked: Sequence[str],
) -> float:
    pl = _norm(path).lower()
    stem = _basename_stem(path)
    s = _path_penalty(path)

    if "/src/main/java/" in pl:
        s += 32.0

    qtok = _tokenize_query(query)
    stop = frozenset(
        {
            "plan",
            "rollout",
            "debug",
            "explain",
            "find",
            "where",
            "the",
            "and",
            "for",
            "with",
            "from",
            "that",
            "this",
            "into",
            "when",
            "what",
            "how",
            "are",
            "not",
            "any",
        }
    )
    meaningful = [t for t in qtok if t not in stop and len(t) >= 4]
    for t in meaningful:
        if t in pl:
            s += 11.0
        if t in stem:
            s += 24.0

    for ct in _camel_tokens(stem):
        if len(ct) < 4:
            continue
        if ct in meaningful or any(ct in m or m in ct for m in meaningful if len(m) >= 4):
            s += 16.0

    s += _query_domain_adjustments(query, pl, stem)

    pkg = _java_subpackage(pl)
    if pkg:
        neighbors = 0
        if rank_index > 0:
            if _java_subpackage(_norm(ranked[rank_index - 1]).lower()) == pkg:
                neighbors += 1
        if rank_index + 1 < len(ranked):
            if _java_subpackage(_norm(ranked[rank_index + 1]).lower()) == pkg:
                neighbors += 1
        s += 14.0 * neighbors

    s -= float(rank_index) * 1.25
    return s


def select_plan_action_target(
    ranked_paths: Sequence[str],
    query: str,
    *,
    max_consider: int = 8,
    min_margin_over_rank0: float = 4.0,
) -> Optional[str]:
    """
    Pick a single path from the existing ranked list for plan / action reasoning.

    Returns None when every candidate looks like noise (all heavily penalized) or the
    list is empty — callers should fall back to cautious behavior.

    Does not invent paths; only returns elements from ``ranked_paths``.
    """
    ranked = [p for p in ranked_paths if p and str(p).strip()]
    if not ranked:
        return None
    consider = ranked[: max(1, min(max_consider, len(ranked)))]

    scores: List[Tuple[float, int, str]] = []
    for i, p in enumerate(consider):
        scores.append((_score_candidate(p, query, i, consider), i, p))

    scores.sort(key=lambda x: (-x[0], x[1]))
    best_s, best_i, best_p = scores[0]
    rank0_s = _score_candidate(consider[0], query, 0, consider)

    if best_s < -60.0:
        return None

    if best_i == 0:
        return best_p

    if best_s >= rank0_s + min_margin_over_rank0:
        return best_p

    return consider[0]


def plan_steps_evidence_sufficient(
    ranked_paths: Sequence[str],
    query: str,
    predicted_evidence_class: str,
) -> bool:
    """
    Conservative gate for emitting plan-step surfaces: no hard refusal and a
    selectable target exists in the ranked list.
    """
    if predicted_evidence_class == "NO_MATCH":
        return False
    if not ranked_paths:
        return False
    return select_plan_action_target(ranked_paths, query) is not None

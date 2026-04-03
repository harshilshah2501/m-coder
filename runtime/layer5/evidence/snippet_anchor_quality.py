"""
Deterministic anchor-line scoring for bounded snippets (A6).

Used by ``extract_snippet`` to choose among lines that match query tokens.
Does not change A5 ranking — snippet-only.
"""

from __future__ import annotations

import re
from typing import FrozenSet, List, Sequence, Tuple

# Generic tokens that often match headers / broad files without engineering signal.
_GENERIC_LOW_SIGNAL: FrozenSet[str] = frozenset(
    {
        "motadata",
        "data",
        "manager",
        "app",
        "java",
        "com",
        "org",
        "the",
        "and",
        "for",
        "api",
        "server",
        "object",
        "service",
        "file",
        "path",
        "main",
        "src",
    }
)

# Domain terms that indicate implementation / AIOps relevance when present in the line.
_DOMAIN_TERMS: FrozenSet[str] = frozenset(
    {
        "correlation",
        "alert",
        "incident",
        "duplicate",
        "suppression",
        "dependency",
        "ingest",
        "ingestion",
        "policy",
        "cache",
        "flow",
        "topology",
        "anomaly",
        "metric",
        "pipeline",
        "parser",
        "processor",
        "engine",
        "availability",
        "normalization",
        "timezone",
        "window",
        "retry",
        "trace",
        "bidirectional",
    }
)

_BOILERPLATE_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r"copyright\s*\(c\)", re.I),
    re.compile(r"all rights reserved", re.I),
    re.compile(r"proprietary and confidential", re.I),
    re.compile(r"unauthorized\s+(copying|access|use)", re.I),
    re.compile(r"provided\s+[\"']as is[\"']", re.I),
    re.compile(r"without warranties", re.I),
    re.compile(r"prosecution", re.I),
    re.compile(r"legal action", re.I),
)


def _boilerplate_score_penalty(line_lower: str) -> int:
    """Higher penalty = worse line for human usefulness."""
    p = 0
    for rx in _BOILERPLATE_PATTERNS:
        if rx.search(line_lower):
            p += 120
    if line_lower.strip().startswith(("/*", "*", "*/")) and "copyright" in line_lower:
        p += 80
    if line_lower.strip().startswith("*") and len(line_lower) < 120 and "motadata" in line_lower:
        p += 40
    return p


def _line_is_import_only(stripped: str) -> bool:
    s = stripped.strip()
    return s.startswith("import ") or s.startswith("package ")


def _code_shape_bonus(line_lower: str) -> int:
    b = 0
    if any(k in line_lower for k in ("public class", "private class", "class ", "interface ", "enum ")):
        b += 35
    if any(k in line_lower for k in ("public void", "private void", "protected void", "void ", "return ")):
        b += 28
    if "@" in line_lower and any(x in line_lower for x in ("override", "inject", "notnull")):
        b += 15
    if "(" in line_lower and ")" in line_lower and any(k in line_lower for k in ("(", ")", "{", ";")):
        b += 12
    return b


def score_anchor_line(
    line_idx: int,
    body: str,
    hit_tokens: Sequence[str],
    *,
    total_lines: int,
) -> int:
    """
    Higher = better anchor. Deterministic for fixed inputs.

    ``hit_tokens`` are query tokens that appear as substrings in ``body`` (lowercased match).
    """
    low = body.lower()
    if not hit_tokens:
        return -10_000

    score = 0
    score += 18 * len(hit_tokens)
    score += sum(22 for t in hit_tokens if t in _DOMAIN_TERMS)
    score -= _boilerplate_score_penalty(low)

    gen_hits = [t for t in hit_tokens if t in _GENERIC_LOW_SIGNAL]
    if gen_hits and len(hit_tokens) == len(gen_hits):
        score -= 95

    score += _code_shape_bonus(low)
    if _line_is_import_only(body):
        score -= 55

    # Early file region: extra penalty for boilerplate-heavy headers (typical first ~45 lines).
    header_zone = 45
    if line_idx < header_zone:
        if any(x in low for x in ("copyright", "reserved", "proprietary", "confidential", "unauthorized")):
            score -= 70
        elif line_idx < 12 and ("/*" in body or body.strip().startswith("*")):
            score -= 45

    # Prefer later lines slightly when scores are otherwise similar (escapes file banners).
    score += min(8, line_idx // 50)

    return score


def pick_best_anchor_line(
    bodies: Sequence[str],
    query_tokens: Tuple[str, ...],
) -> Tuple[int, Tuple[str, ...]]:
    """
    Among lines with at least one query-token substring hit, pick highest-scoring line.

    Returns ``(anchor_idx, matched_tokens_sorted)`` for the winning line.
    Tie-break: higher score, then larger line index (prefer body below headers).
    """
    if not query_tokens:
        return 0, ()

    candidates: List[Tuple[int, int, Tuple[str, ...]]] = []
    for i, body in enumerate(bodies):
        low = body.lower()
        hit = [t for t in query_tokens if t in low]
        if not hit:
            continue
        matched = tuple(sorted(set(hit)))
        sc = score_anchor_line(i, body, hit, total_lines=len(bodies))
        candidates.append((sc, i, matched))

    if not candidates:
        return 0, ()

    best_sc, best_i, best_m = max(candidates, key=lambda x: (x[0], x[1]))
    _ = best_sc
    return best_i, best_m


def classify_visible_snippet_kind(snippet_text: str) -> str:
    """
    Coarse bucket for usefulness metrics (deterministic, heuristic).

    Returns one of: ``header_boilerplate``, ``domain_body``, ``mixed_or_weak``.
    """
    if not (snippet_text or "").strip():
        return "mixed_or_weak"
    low = snippet_text.lower()[:1200]
    if any(rx.search(low) for rx in _BOILERPLATE_PATTERNS):
        return "header_boilerplate"
    if "copyright" in low and "reserved" in low:
        return "header_boilerplate"
    if "unauthorized" in low and ("software" in low or "access" in low):
        return "header_boilerplate"
    dom = sum(1 for t in _DOMAIN_TERMS if t in low)
    if dom >= 2 and _code_shape_bonus(low) >= 20:
        return "domain_body"
    if dom >= 1 and any(k in low for k in ("public ", "private ", "void ", "class ", "return ", "@")):
        return "domain_body"
    return "mixed_or_weak"

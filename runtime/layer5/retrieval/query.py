"""
Query normalization for lexical retrieval (deterministic).
"""

from __future__ import annotations

import re
from typing import Set, Tuple

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Deterministic query-side token expansions for lexical recall (no index change).
# Pairs: base token present in query → extra tokens matched against paths/basenames.
_RECALL_EXPAND: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("poll", ("polling", "poller", "polled")),
    ("collect", ("collector", "collection", "collecting")),
    ("collection", ("collect", "collector", "collecting")),
    ("process", ("processor", "processing", "processed")),
)
# When a role-shaped token is present, also add its short root (basename/path overlap).
_RECALL_ROOT: Tuple[Tuple[str, str], ...] = (
    ("collector", "collect"),
    ("processor", "process"),
    ("poller", "poll"),
)


def _expand_recall_tokens(tokens: Set[str], min_token_len: int) -> None:
    for base, extras in _RECALL_EXPAND:
        if base not in tokens:
            continue
        for e in extras:
            if len(e) >= min_token_len:
                tokens.add(e)
    for role, root in _RECALL_ROOT:
        if role in tokens and len(root) >= min_token_len:
            tokens.add(root)


def _split_camel_identifier(token: str) -> Tuple[str, ...]:
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+", token)
    out = tuple(p.lower() for p in parts if p)
    return out


def normalize_query(raw: str, min_token_len: int = 2) -> Tuple[str, ...]:
    """
    Lowercase, extract alphanumeric runs as tokens, drop short tokens.

    Returns a tuple sorted lexicographically for stable downstream use
    (e.g. logging or caching keys), not for scoring order.
    """
    if not raw:
        return ()
    lower = raw.lower()
    tokens = {m.group(0) for m in _TOKEN_RE.finditer(lower) if len(m.group(0)) >= min_token_len}

    # Deterministic owner-presence hardening:
    # keep existing lower-token behavior, but also derive split tokens from raw identifiers
    # (e.g. MetricsParser -> metrics, parser) so code-targeting variants remain matchable.
    for ident in _IDENT_RE.findall(raw):
        split = _split_camel_identifier(ident)
        for tok in split:
            if len(tok) >= min_token_len:
                tokens.add(tok)
    _expand_recall_tokens(tokens, min_token_len)
    return tuple(sorted(tokens))

"""
Query normalization for lexical retrieval (deterministic).
"""

from __future__ import annotations

import re
from typing import Tuple

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize_query(raw: str, min_token_len: int = 2) -> Tuple[str, ...]:
    """
    Lowercase, extract alphanumeric runs as tokens, drop short tokens.

    Returns a tuple sorted lexicographically for stable downstream use
    (e.g. logging or caching keys), not for scoring order.
    """
    if not raw:
        return ()
    lower = raw.lower()
    tokens = [m.group(0) for m in _TOKEN_RE.finditer(lower) if len(m.group(0)) >= min_token_len]
    return tuple(sorted(tokens))

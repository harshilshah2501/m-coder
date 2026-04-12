"""
Deterministic query intent classification for retrieval quality policy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, Tuple


CODE_INTENT: Final[str] = "CODE_INTENT"
DEBUG_INTENT: Final[str] = "DEBUG_INTENT"
PLAN_INTENT: Final[str] = "PLAN_INTENT"
GENERIC_INTENT: Final[str] = "GENERIC_INTENT"

_CODE_PHRASES: Final[Tuple[str, ...]] = (
    "where implemented",
    "where is",
    "which files implement",
    "which file implements",
    "implemented in",
    "implements",
    "invoked by",
    "call path",
    "which class",
    "which function",
    "which method",
    "implementation",
    "module",
)
_DEBUG_PHRASES: Final[Tuple[str, ...]] = (
    "why failing",
    "not working",
    "error",
    "exception",
    "traceback",
    "stacktrace",
    "failure",
)
_PLAN_PHRASES: Final[Tuple[str, ...]] = (
    "plan",
    "change",
    "update",
    "add",
    "modify",
    "refactor",
)


@dataclass(frozen=True)
class IntentResult:
    intent_type: str
    has_symbol_signal: bool
    symbol_tokens: Tuple[str, ...]


def _contains_symbol_signal(query: str) -> Tuple[bool, Tuple[str, ...]]:
    q = query.strip()
    if not q:
        return (False, ())
    symbols = []
    # CamelCase, snake_case, method-like, dotted names.
    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_\.()]*", q):
        raw = token.strip()
        base = raw.rstrip("()")
        # Strip trailing sentence punctuation so "code." is not treated as a dotted identifier.
        base = base.rstrip(".")
        if (
            re.search(r"[a-z][A-Z]", base)
            or "_" in base
            or "." in base
            or raw.endswith("()")
        ):
            symbols.append(base.lower())
            # Deterministic split for CamelCase symbol robustness: allow partial symbol-path linkage
            # in quality checks without semantic expansion.
            for part in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+", base):
                if part:
                    symbols.append(part.lower())
    dedup = []
    seen = set()
    for s in symbols:
        if s not in seen:
            seen.add(s)
            dedup.append(s)
    return (len(dedup) > 0, tuple(dedup))


def classify_intent(query: str) -> IntentResult:
    q = (query or "").strip()
    ql = q.lower()
    has_symbol, symbol_tokens = _contains_symbol_signal(q)
    if has_symbol:
        return IntentResult(intent_type=CODE_INTENT, has_symbol_signal=True, symbol_tokens=symbol_tokens)
    tokens = tuple(re.findall(r"[a-z0-9]+", ql))
    token_set = set(tokens)
    if (
        token_set.intersection({"implement", "implements", "implemented", "invoked", "call", "path"})
        and token_set.intersection({"file", "files", "class", "function", "method", "module"})
    ):
        return IntentResult(intent_type=CODE_INTENT, has_symbol_signal=False, symbol_tokens=())
    if any(p in ql for p in _CODE_PHRASES):
        return IntentResult(intent_type=CODE_INTENT, has_symbol_signal=False, symbol_tokens=())
    if any(p in ql for p in _DEBUG_PHRASES):
        return IntentResult(intent_type=DEBUG_INTENT, has_symbol_signal=False, symbol_tokens=())
    if any(p in ql for p in _PLAN_PHRASES):
        return IntentResult(intent_type=PLAN_INTENT, has_symbol_signal=False, symbol_tokens=())
    return IntentResult(intent_type=GENERIC_INTENT, has_symbol_signal=False, symbol_tokens=())


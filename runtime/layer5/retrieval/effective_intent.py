"""
EffectiveIntent: merge task_type (primary) with query-based intent (secondary).

Locked behavior per RETRIEVAL_REDESIGN_SPEC_V1 §5.4.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Tuple

from runtime.layer5.retrieval.intent import (
    CODE_INTENT,
    DEBUG_INTENT,
    GENERIC_INTENT,
    PLAN_INTENT,
    IntentResult,
    classify_intent,
)

# Retrieval modes for weighting / diagnostics (not identical to task_type strings).
MODE_ASK: Final[str] = "ASK"
MODE_DEBUG: Final[str] = "DEBUG"
MODE_PLAN: Final[str] = "PLAN"
MODE_CODE: Final[str] = "CODE"


@dataclass(frozen=True)
class EffectiveIntent:
    """Single object consumed by fusion + quality gate."""

    primary_mode: str
    query_intent: IntentResult
    task_type_raw: str
    conflicts: Tuple[str, ...] = field(default_factory=tuple)
    """
    Human/debug strings when task_type-implied mode disagrees with query_intent
    classification (e.g. EXPLAIN_DEBUG vs CODE_INTENT query).
    """


def resolve_lexical_task_type(
    task_type: str,
    query: str,
    authority_resolution: Optional[Mapping[str, Any]],
) -> str:
    """
    Map client ``task_type`` + signals to the task string consumed by Stage A / lexical.

    Upgrades plain ``general`` to ``CODE`` when authority supplies a primary owner file
    or the query is clearly code-oriented, so owner-aware candidate lanes stay tight.
    """
    raw = (task_type or "").strip() or "general"
    if raw.upper() not in ("GENERAL", ""):
        return raw
    po = None
    if isinstance(authority_resolution, Mapping):
        po = authority_resolution.get("primary_owner")
    file_ok = False
    if isinstance(po, Mapping):
        file_ok = bool(str(po.get("file") or "").strip())
    if file_ok:
        return "CODE"
    qi = classify_intent(query or "")
    if qi.intent_type == CODE_INTENT:
        return "CODE"
    return "general"


def merge_effective_intent(task_type: str, query: str) -> EffectiveIntent:
    """
    task_type is primary when present; query intent provides secondary bias.

    Ask API currently uses task_type in {\"EXPLAIN_DEBUG\", \"general\", \"\"}.
    """
    tt = (task_type or "").strip() or "general"
    qi = classify_intent(query or "")
    conflicts: list[str] = []

    if tt == "EXPLAIN_DEBUG":
        primary = MODE_DEBUG
        if qi.intent_type == CODE_INTENT:
            conflicts.append("task_type_EXPLAIN_DEBUG_vs_query_CODE_INTENT")
    elif tt.upper() == "CODE":
        primary = MODE_CODE
        if qi.intent_type == DEBUG_INTENT:
            conflicts.append("task_type_CODE_vs_query_DEBUG_INTENT")
    elif tt == "general":
        if qi.intent_type == DEBUG_INTENT:
            primary = MODE_DEBUG
            conflicts.append("task_type_general_vs_query_DEBUG_INTENT")
        elif qi.intent_type == PLAN_INTENT:
            primary = MODE_PLAN
        elif qi.intent_type == CODE_INTENT:
            primary = MODE_CODE
        else:
            primary = MODE_ASK
    else:
        # Unknown task_type: treat like general but record.
        conflicts.append(f"unknown_task_type:{tt}")
        if qi.intent_type == PLAN_INTENT:
            primary = MODE_PLAN
        elif qi.intent_type == CODE_INTENT:
            primary = MODE_CODE
        elif qi.intent_type == DEBUG_INTENT:
            primary = MODE_DEBUG
        else:
            primary = MODE_ASK

    return EffectiveIntent(
        primary_mode=primary,
        query_intent=qi,
        task_type_raw=tt,
        conflicts=tuple(conflicts),
    )

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .assist_contracts import (
    SUGGESTION_SOURCE_CONTEXT_META,
    SUGGESTION_SOURCE_STATIC_TEMPLATE,
    SUGGESTION_SOURCE_USER_INPUT,
)


@dataclass(frozen=True)
class SuggestionResult:
    suggestions: List[str]
    sources: List[str]


def build_template_suggestions(
    original_query: str,
    context_meta: Dict[str, Any],
    task_type_label: str,
) -> SuggestionResult:
    suggestions: List[str] = []
    sources: List[str] = []

    query = (original_query or "").strip()
    if len(query.split()) <= 2:
        suggestions.append("Add a specific component or module name to reduce ambiguity.")
        sources.append(SUGGESTION_SOURCE_USER_INPUT)

    evidence_count = context_meta.get("evidence_presence_or_count")
    if evidence_count in (None, 0, "0", False):
        suggestions.append("Provide at least one evidence file path or selector hint for stronger grounding.")
        sources.append(SUGGESTION_SOURCE_CONTEXT_META)

    active_file = str(context_meta.get("active_file_path") or "").strip()
    if not active_file:
        suggestions.append("If relevant, include the active file path to anchor the request.")
        sources.append(SUGGESTION_SOURCE_STATIC_TEMPLATE)

    if str(task_type_label or "").upper() == "EXPLAIN_DEBUG":
        diag = context_meta.get("diagnostics_labels")
        if not diag:
            suggestions.append("Include structured diagnostics labels when available to sharpen debug context.")
            sources.append(SUGGESTION_SOURCE_CONTEXT_META)

    if not suggestions:
        return SuggestionResult(suggestions=[], sources=[])

    seen = set()
    dedup_suggestions: List[str] = []
    dedup_sources: List[str] = []
    for s, src in zip(suggestions, sources):
        if s in seen:
            continue
        seen.add(s)
        dedup_suggestions.append(s)
        dedup_sources.append(src)

    return SuggestionResult(suggestions=dedup_suggestions, sources=dedup_sources)

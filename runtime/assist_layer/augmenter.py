from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Set


_ABBREVIATION_MAP = {
    "repo": "repository",
    "cfg": "config",
}

# Unambiguous typo map only. Full-token replacements only.
_TYPO_MAP = {
    "teh": "the",
    "retrive": "retrieve",
    "retrival": "retrieval",
    "plangte": "plangate",
}

_ALLOWED_REPO_QUALIFIER = " in this workspace"

_TASK_TYPE_HINTS = {
    "explain": {"explain", "what", "understand"},
    "where": {"where", "location", "locate"},
    "why": {"why", "cause", "reason"},
    "debug": {"debug", "error", "failing", "failure", "broken"},
    "plan": {"plan", "design", "approach"},
    "fix": {"fix", "patch", "repair"},
}


@dataclass(frozen=True)
class AugmentResult:
    augmented_query: str
    reason: str
    reason_code: str
    transform_codes_applied: List[str]
    blocked_by_policy: bool


def _normalize_whitespace(text: str) -> tuple[str, bool]:
    updated = re.sub(r"\s+", " ", text).strip()
    return updated, updated != text


def _normalize_punctuation(text: str) -> tuple[str, bool]:
    before = text
    text = re.sub(r"([!?.,])\1+", r"\1", text)
    text = re.sub(r"\s+([!?.,])", r"\1", text)
    text = re.sub(r"([!?.,])(\S)", r"\1 \2", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text, text != before


def _normalize_typos(text: str) -> tuple[str, bool, Set[str]]:
    parts = re.split(r"(\W+)", text)
    changed = False
    introduced: Set[str] = set()
    for i, token in enumerate(parts):
        if not token or not token.isalpha():
            continue
        lower = token.lower()
        if lower in _TYPO_MAP:
            corrected = _TYPO_MAP[lower]
            parts[i] = corrected if token.islower() else corrected.capitalize()
            changed = True
            introduced.add(corrected.lower())
    return "".join(parts), changed, introduced


def _expand_abbreviations(text: str) -> tuple[str, bool, Set[str]]:
    parts = re.split(r"(\W+)", text)
    changed = False
    expansions: Set[str] = set()
    for i, token in enumerate(parts):
        if not token or not token.isalpha():
            continue
        lower = token.lower()
        if lower in _ABBREVIATION_MAP:
            target = _ABBREVIATION_MAP[lower]
            parts[i] = target if token.islower() else target.capitalize()
            changed = True
            expansions.add(target)
    return "".join(parts), changed, expansions


def _implied_workspace_scope(text: str, context_meta: Dict[str, Any]) -> bool:
    lowered = text.lower()
    if "workspace" in lowered or "repository" in lowered or "repo" in lowered or "project" in lowered:
        return True
    if " this " in f" {lowered} " and any(k in context_meta for k in ("active_file_path", "evidence_file_paths_or_ids")):
        return True
    return False


def _append_neutral_repo_qualifier(text: str, context_meta: Dict[str, Any]) -> tuple[str, bool, Set[str]]:
    if text.lower().endswith(_ALLOWED_REPO_QUALIFIER.strip()):
        return text, False, set()
    if _implied_workspace_scope(text, context_meta):
        updated = f"{text.rstrip()}{_ALLOWED_REPO_QUALIFIER}"
        return updated, True, {"in", "this", "workspace"}
    return text, False, set()


def _infer_task_type(text: str) -> str:
    tokens = set(re.findall(r"[a-zA-Z_]+", text.lower()))
    found: list[str] = []
    for label, hints in _TASK_TYPE_HINTS.items():
        if tokens & hints:
            found.append(label)
    return found[0] if len(found) == 1 else "unknown"


def _tokenize(text: str) -> Set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))


def apply_deterministic_augmentation(original_query: str, context_meta: Dict[str, Any]) -> AugmentResult:
    current = original_query
    applied: List[str] = []
    allowed_new_tokens: Set[str] = set()

    current, changed = _normalize_whitespace(current)
    if changed:
        applied.append("normalize_whitespace")

    current, changed = _normalize_punctuation(current)
    if changed:
        applied.append("normalize_punctuation")

    current, changed, typo_tokens = _normalize_typos(current)
    if changed:
        applied.append("normalize_typo_light")
        allowed_new_tokens |= typo_tokens

    current, changed, exp = _expand_abbreviations(current)
    if changed:
        applied.append("expand_static_abbreviation")
        allowed_new_tokens |= exp

    current, changed, q_tokens = _append_neutral_repo_qualifier(current, context_meta)
    if changed:
        applied.append("append_neutral_workspace_qualifier")
        allowed_new_tokens |= q_tokens

    original_task = _infer_task_type(original_query)
    new_task = _infer_task_type(current)
    if original_task != "unknown" and new_task != "unknown" and original_task != new_task:
        return AugmentResult(
            augmented_query=original_query,
            reason="policy blocked augmentation due to task type shift",
            reason_code="task_type_shift_blocked",
            transform_codes_applied=[],
            blocked_by_policy=True,
        )

    original_tokens = _tokenize(original_query)
    new_tokens = _tokenize(current)
    introduced = new_tokens - original_tokens
    unexpected_introduced = {t for t in introduced if t not in allowed_new_tokens}
    if unexpected_introduced:
        return AugmentResult(
            augmented_query=original_query,
            reason="policy blocked augmentation due to unexpected token introduction",
            reason_code="unexpected_token_blocked",
            transform_codes_applied=[],
            blocked_by_policy=True,
        )

    if current == original_query:
        return AugmentResult(
            augmented_query=original_query,
            reason="no deterministic normalization applied",
            reason_code="no_transform",
            transform_codes_applied=[],
            blocked_by_policy=False,
        )

    return AugmentResult(
        augmented_query=current,
        reason="applied conservative deterministic normalization",
        reason_code="deterministic_normalization",
        transform_codes_applied=applied,
        blocked_by_policy=False,
    )

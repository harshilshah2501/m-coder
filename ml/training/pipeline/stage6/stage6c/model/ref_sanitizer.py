from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

REF_CANONICAL_RESPONSE = (
    "I can’t assist with that request because it violates scope or authority. "
    "If you describe the legitimate goal, I can help with an alternative that stays within policy."
)

CONF_CANONICAL_RESPONSE = (
    "I need a bit more context before I can answer safely. "
    "I may be missing constraints that affect what is permissible. "
    "If you share the objective, authority, and boundaries, I can verify constraints and suggest a policy-safe alternative."
)

_SANITIZE_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("step_number", re.compile(r"\bstep\s*\d+\b", re.IGNORECASE)),
    ("markdown_heading", re.compile(r"^#{1,6}\s", re.MULTILINE)),
    (
        "following_steps_phrase",
        re.compile(r"the following steps are taken", re.IGNORECASE),
    ),
    (
        "procedural_terms",
        re.compile(
            r"\b(action plan|procedure|workflow|implementation steps)\b",
            re.IGNORECASE,
        ),
    ),
    ("numbered_list", re.compile(r"^\d+\.", re.MULTILINE)),
]

_CONF_SANITIZE_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("step_number", re.compile(r"\bstep\s*\d+\b", re.IGNORECASE)),
    ("numbered_list", re.compile(r"^\d+\.", re.MULTILINE)),
    ("bullet_with_verb", re.compile(r"^\s*[-*]\s*(do|run|execute|install|open|copy|paste|command|then)\b", re.IGNORECASE | re.MULTILINE)),
    (
        "imperative_procedural_verbs",
        re.compile(r"\b(do|run|execute|install|open|copy|paste|command|then)\b", re.IGNORECASE),
    ),
    ("code_block", re.compile(r"```[\s\S]*```", re.MULTILINE)),
    ("shell_snippet", re.compile(r"(^|\n)\s*\$\s+\S+", re.MULTILINE)),
    ("file_path", re.compile(r"(?:^|\s)(?:/[^\s]+|\.?\.?/[^\s]+|[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+)", re.MULTILINE)),
]


def ref_sanitize(text: str) -> tuple[str, bool, list[str]]:
    reasons: List[str] = []
    for reason, pattern in _SANITIZE_PATTERNS:
        if pattern.search(text):
            reasons.append(reason)
    if reasons:
        return REF_CANONICAL_RESPONSE, True, reasons
    return text, False, []


def conf_sanitize(text: str) -> tuple[str, bool, list[str]]:
    reasons: List[str] = []

    for reason, pattern in _CONF_SANITIZE_PATTERNS:
        if pattern.search(text):
            reasons.append(reason)

    # If procedural content → sanitize
    if reasons:
        return CONF_CANONICAL_RESPONSE, True, reasons

    # NEW: enforce CONF boundary even without procedural markers
    if text.strip():
        return CONF_CANONICAL_RESPONSE, True, ["conf_boundary_enforced"]

    return text, False, []


def extract_expected_phase(messages: List[Dict[str, Any]]) -> str | None:
    for message in reversed(messages):
        metadata = message.get("metadata")
        if not isinstance(metadata, dict):
            continue
        expected_phase = metadata.get("expected_phase")
        if isinstance(expected_phase, str) and expected_phase.strip():
            return expected_phase.strip().upper()
    return None


def should_apply_ref_sanitizer(
    messages: List[Dict[str, Any]],
    expected_phase: str | None,
    fail_closed: bool,
) -> tuple[bool, str, str | None]:
    expected_phase_seen = expected_phase.strip().upper() if isinstance(expected_phase, str) and expected_phase.strip() else None
    if expected_phase_seen is None:
        expected_phase_seen = extract_expected_phase(messages)
    if expected_phase_seen == "REF":
        return True, "expected_phase_ref", expected_phase_seen
    if expected_phase_seen is None and fail_closed:
        return True, "fail_closed_missing_phase", None
    return False, "disabled", expected_phase_seen


def should_apply_conf_sanitizer(
    messages: List[Dict[str, Any]],
    expected_phase: str | None,
) -> tuple[bool, str, str | None]:
    expected_phase_seen = expected_phase.strip().upper() if isinstance(expected_phase, str) and expected_phase.strip() else None
    if expected_phase_seen is None:
        expected_phase_seen = extract_expected_phase(messages)
    if expected_phase_seen == "CONF":
        return True, "expected_phase_conf", expected_phase_seen
    return False, "disabled", expected_phase_seen

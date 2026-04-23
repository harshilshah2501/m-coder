"""
Frozen ``selection_reason`` values for ``layer5.evidence_bundle.v1``.

Any new reason requires a schema version bump and an enum update here.
"""

from __future__ import annotations

from enum import Enum
from typing import FrozenSet


class SelectionReason(str, Enum):
    """Allowed ``snippet.selection_reason`` strings (v1)."""

    QUERY_TOKEN_SUBSTRING_ANCHOR = "query_token_substring_anchor"
    EXECUTABLE_CONTROL_FLOW_RESCUE_ANCHOR = "executable_control_flow_rescue_anchor"
    NO_QUERY_TOKEN_IN_BODY_FILE_START = "no_query_token_in_body_file_start"
    NO_QUERY_TOKENS_FILE_START = "no_query_tokens_file_start"
    FILE_MISSING = "file_missing"
    FILE_UNREADABLE = "file_unreadable"
    EMPTY_FILE = "empty_file"


FROZEN_SELECTION_REASONS: FrozenSet[str] = frozenset(m.value for m in SelectionReason)


def parse_selection_reason(value: str) -> SelectionReason:
    """Return enum member or raise ValueError (invalid frozen value)."""
    try:
        return SelectionReason(value)
    except ValueError as e:
        raise ValueError(
            f"invalid selection_reason {value!r}; must be one of {sorted(FROZEN_SELECTION_REASONS)}"
        ) from e

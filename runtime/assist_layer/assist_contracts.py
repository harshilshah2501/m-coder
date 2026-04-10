from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List


ASSIST_VERSION = "assist.v1"
INPUT_HASH_SCOPE_V1 = "original_query_only"
CANONICALIZATION_VERSION_V1 = "assist_input_canonicalization.v1"

ALLOWED_CONTEXT_META_KEYS = {
    "active_file_path",
    "evidence_file_paths_or_ids",
    "selector_names_used",
    "task_type_label",
    "evidence_presence_or_count",
    "diagnostics_labels",
}

FORBIDDEN_CONTEXT_META_KEYS = {
    "raw_snippet",
    "raw_snippets",
    "code_body",
    "code_bodies",
    "raw_logs",
    "repo_text",
    "repository_text",
    "free_form_text",
}

SUGGESTION_SOURCE_USER_INPUT = "user_input"
SUGGESTION_SOURCE_CONTEXT_META = "context_meta"
SUGGESTION_SOURCE_STATIC_TEMPLATE = "static_template"
SUGGESTION_SOURCES = {
    SUGGESTION_SOURCE_USER_INPUT,
    SUGGESTION_SOURCE_CONTEXT_META,
    SUGGESTION_SOURCE_STATIC_TEMPLATE,
}


class AssistStatus(str, Enum):
    OK = "ok"
    DEGRADED_EMPTY_CONTEXT = "degraded_empty_context"
    INPUT_INVALID = "input_invalid"
    TIMEOUT_OR_INTERNAL_ERROR = "timeout_or_internal_error"
    BLOCKED_BY_POLICY = "blocked_by_policy"


class ConfidenceEnum(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"


@dataclass(frozen=True)
class AssistInput:
    request_id: str
    trace_id: str
    original_query: str
    session_id: str = ""
    context_meta: Dict[str, Any] = field(default_factory=dict)
    task_type_label: str = "general"


@dataclass(frozen=True)
class AssistError:
    code: str
    message: str


@dataclass(frozen=True)
class AssistOutput:
    request_id: str
    trace_id: str
    original_query: str
    augmented_query: str
    reason: str
    suggestions: List[str]
    confidence_enum: ConfidenceEnum
    assist_status: AssistStatus
    transform_codes_applied: List[str]
    suggestion_sources: List[str]
    errors: List[Dict[str, str]] = field(default_factory=list)
    retrieval_drift_validation: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["confidence_enum"] = self.confidence_enum.value
        d["assist_status"] = self.assist_status.value
        return d

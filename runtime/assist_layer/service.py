from __future__ import annotations

import time
from typing import Any, Dict, Tuple

from .assist_contracts import (
    ALLOWED_CONTEXT_META_KEYS,
    FORBIDDEN_CONTEXT_META_KEYS,
    SUGGESTION_SOURCES,
    AssistError,
    AssistInput,
    AssistOutput,
    AssistStatus,
    ConfidenceEnum,
)
from .augmenter import apply_deterministic_augmentation
from .observability import build_assist_event
from .suggestions import build_template_suggestions


def _errors_to_dicts(errors: list[AssistError]) -> list[dict[str, str]]:
    return [{"code": e.code, "message": e.message} for e in errors]


def _validate_input(assist_input: AssistInput) -> list[AssistError]:
    errors: list[AssistError] = []
    if not assist_input.request_id.strip():
        errors.append(AssistError(code="missing_request_id", message="request_id is required"))
    if not assist_input.trace_id.strip():
        errors.append(AssistError(code="missing_trace_id", message="trace_id is required"))
    if assist_input.original_query is None or not str(assist_input.original_query).strip():
        errors.append(AssistError(code="missing_original_query", message="original_query is required"))

    meta = assist_input.context_meta or {}
    for key in meta.keys():
        if key in FORBIDDEN_CONTEXT_META_KEYS:
            errors.append(AssistError(code="forbidden_context_key", message=f"context_meta key '{key}' is forbidden"))
        if key not in ALLOWED_CONTEXT_META_KEYS:
            errors.append(AssistError(code="non_allowlisted_context_key", message=f"context_meta key '{key}' is not allowlisted"))

    return errors


def _confidence_for_output(status: AssistStatus, transforms: list[str]) -> ConfidenceEnum:
    if status != AssistStatus.OK:
        return ConfidenceEnum.NONE
    if not transforms:
        return ConfidenceEnum.LOW
    return ConfidenceEnum.MEDIUM


def _retrieval_drift_validation_hint(assist_output: AssistOutput) -> Dict[str, Any]:
    is_noop = assist_output.augmented_query == assist_output.original_query
    return {
        "mode": "exact_match_required" if is_noop else "bounded_drift_candidate",
        "is_noop": is_noop,
        "transform_codes_applied": list(assist_output.transform_codes_applied),
    }


def run_assist_layer_v1(assist_input: AssistInput) -> Tuple[AssistOutput, Dict[str, Any]]:
    t0 = time.perf_counter()
    reason_code = "unknown"
    error_class = None

    try:
        errors = _validate_input(assist_input)
        if errors:
            reason_code = "input_invalid"
            output = AssistOutput(
                request_id=assist_input.request_id,
                trace_id=assist_input.trace_id,
                original_query=assist_input.original_query,
                augmented_query=assist_input.original_query,
                reason="assist input invalid; passthrough original_query",
                suggestions=[],
                confidence_enum=ConfidenceEnum.NONE,
                assist_status=AssistStatus.INPUT_INVALID,
                transform_codes_applied=[],
                suggestion_sources=[],
                errors=_errors_to_dicts(errors),
                retrieval_drift_validation={},
            )
            output = AssistOutput(
                **{
                    **output.__dict__,
                    "retrieval_drift_validation": _retrieval_drift_validation_hint(output),
                }
            )
            event = build_assist_event(
                assist_input,
                output,
                reason_code=reason_code,
                latency_ms=(time.perf_counter() - t0) * 1000.0,
            )
            return output, event

        context_meta = dict(assist_input.context_meta or {})
        if not context_meta:
            reason_code = "degraded_empty_context"
            empty_context_suggestions = build_template_suggestions(
                assist_input.original_query,
                context_meta,
                assist_input.task_type_label,
            )
            output = AssistOutput(
                request_id=assist_input.request_id,
                trace_id=assist_input.trace_id,
                original_query=assist_input.original_query,
                augmented_query=assist_input.original_query,
                reason="metadata context empty; passthrough original_query",
                suggestions=empty_context_suggestions.suggestions,
                confidence_enum=ConfidenceEnum.NONE,
                assist_status=AssistStatus.DEGRADED_EMPTY_CONTEXT,
                transform_codes_applied=[],
                suggestion_sources=[s for s in empty_context_suggestions.sources if s in SUGGESTION_SOURCES],
                errors=[],
                retrieval_drift_validation={},
            )
            output = AssistOutput(
                **{
                    **output.__dict__,
                    "retrieval_drift_validation": _retrieval_drift_validation_hint(output),
                }
            )
            event = build_assist_event(
                assist_input,
                output,
                reason_code=reason_code,
                latency_ms=(time.perf_counter() - t0) * 1000.0,
            )
            return output, event

        augment = apply_deterministic_augmentation(assist_input.original_query, context_meta)

        status = AssistStatus.OK
        if augment.blocked_by_policy:
            status = AssistStatus.BLOCKED_BY_POLICY

        suggestions = build_template_suggestions(
            assist_input.original_query,
            context_meta,
            assist_input.task_type_label,
        )

        valid_sources = [s for s in suggestions.sources if s in SUGGESTION_SOURCES]
        reason_code = augment.reason_code

        output = AssistOutput(
            request_id=assist_input.request_id,
            trace_id=assist_input.trace_id,
            original_query=assist_input.original_query,
            augmented_query=augment.augmented_query,
            reason=augment.reason,
            suggestions=suggestions.suggestions,
            confidence_enum=_confidence_for_output(status, augment.transform_codes_applied),
            assist_status=status,
            transform_codes_applied=augment.transform_codes_applied,
            suggestion_sources=valid_sources,
            errors=[],
            retrieval_drift_validation={},
        )
        output = AssistOutput(
            **{
                **output.__dict__,
                "retrieval_drift_validation": _retrieval_drift_validation_hint(output),
            }
        )
        event = build_assist_event(
            assist_input,
            output,
            reason_code=reason_code,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
        )
        return output, event

    except TimeoutError as e:
        error_class = e.__class__.__name__
        reason_code = "timeout_or_internal_error"
    except Exception as e:
        error_class = e.__class__.__name__
        reason_code = "timeout_or_internal_error"

    fallback = AssistOutput(
        request_id=assist_input.request_id,
        trace_id=assist_input.trace_id,
        original_query=assist_input.original_query,
        augmented_query=assist_input.original_query,
        reason="assist unavailable; passthrough original_query",
        suggestions=[],
        confidence_enum=ConfidenceEnum.NONE,
        assist_status=AssistStatus.TIMEOUT_OR_INTERNAL_ERROR,
        transform_codes_applied=[],
        suggestion_sources=[],
        errors=[{"code": "assist_internal_error", "message": reason_code}],
        retrieval_drift_validation={},
    )
    fallback = AssistOutput(
        **{
            **fallback.__dict__,
            "retrieval_drift_validation": _retrieval_drift_validation_hint(fallback),
        }
    )
    event = build_assist_event(
        assist_input,
        fallback,
        reason_code=reason_code,
        latency_ms=(time.perf_counter() - t0) * 1000.0,
        error_class=error_class,
    )
    return fallback, event

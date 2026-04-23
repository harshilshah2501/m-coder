"""
Ask v1 — evidence_bundle.v1 as primary context (Plan-Gate / A8).

Validates the frozen ``layer5.evidence_bundle.v1`` payload and maps it to a
``ContextBundle`` without ContextEngine or repository filesystem reads.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from runtime.layer5.evidence.schema_validate import (
    EvidenceSchemaValidationError,
    validate_evidence_bundle_dict,
)
from runtime.layer5.evidence.usefulness_metrics import bundle_usefulness_metrics
from runtime.layer5.retrieval.effective_intent import merge_effective_intent, resolve_lexical_task_type
from runtime.layer5.retrieval.intent import GENERIC_INTENT
from runtime.layer5.retrieval.quality_gate import (
    NO_MATCH,
    WEAK,
    assess_evidence_quality,
    operator_hints_for_assessment,
)

from .dirty_buffer_overlay import apply_dirty_buffer_overlay, extract_dirty_buffers
from .authority_synthesis import prioritize_owner_in_bundle
from .context_budget import apply_context_budget, build_context_budget_metadata
from .evidence_bridge import context_bundle_from_evidence_dict
from .handlers import _build_plan_only_response
from .planner import PlanOnlyPlanner
from .reasoner import explain_debug, ExplainDebugResult

LOG = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parents[1]  # runtime/
IDE_SCHEMAS = REPO / "ide" / "schemas"


class AskV1ClientError(Exception):
    """Client-visible v1 Ask errors (mapped to HTTP 400 by Plan-Gate)."""

    def __init__(self, code: str, message: str, details: Any = None) -> None:
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


def _explain_debug_failure_step(error: str) -> str:
    err = (error or "").strip()
    if not err:
        return "Explain/debug failed; no template steps substituted."
    low = err.lower()
    if "unavailable" in low or "timeout" in low or "http" in low:
        return "Reasoning service unavailable; no template steps substituted."
    return f"Explain/debug failed ({err}); no template steps substituted."


def _load_schema(name: str) -> dict:
    with open(IDE_SCHEMAS / name, encoding="utf-8") as f:
        return json.load(f)


def validate_ask_v1_request(data: dict) -> List[str]:
    """Validate against ``ask_request.v1.0.schema.json``. Returns list of errors."""
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema not installed"]
    schema = _load_schema("ask_request.v1.0.schema.json")
    errs: List[str] = []
    for e in jsonschema.Draft7Validator(schema).iter_errors(data):
        errs.append(e.message)
    return errs


def _normalize_legacy_authority_validation_details(evidence_bundle: Dict[str, Any]) -> None:
    """
    Backfill optional legacy omissions in authority validation_details.

    Older Context Layer builds may omit ``method_exists`` / ``is_referenced`` in
    ``authority_resolution.validation_details`` even though they are accepted as
    null in the current schema. Populate missing keys with ``None`` so strict
    schema validation remains deterministic across mixed deploy versions.
    """
    ar = evidence_bundle.get("authority_resolution")
    if not isinstance(ar, dict):
        return
    vd = ar.get("validation_details")
    if not isinstance(vd, dict):
        return
    if "method_exists" not in vd:
        vd["method_exists"] = None
    if "is_referenced" not in vd:
        vd["is_referenced"] = None


def handle_ask_v1_request(ask_request: dict) -> dict:
    """
    Process AskRequest v1.0: strict evidence validation, bundle → ContextBundle, plan / explain_debug.

    Preconditions: envelope already passed ``validate_ask_v1_request`` (or equivalent).
    """
    request_id = str(ask_request.get("request_id", ""))
    trace_id = str(ask_request.get("trace_id") or "").strip()
    task_type = ask_request.get("task_type") or "general"
    LOG.info(
        "[ASK_V1] trace_id=%s request_id=%s task_type=%s",
        trace_id or "(none)",
        request_id,
        task_type,
    )
    query = str(ask_request.get("query", ""))
    evidence_bundle = ask_request.get("evidence_bundle")
    if not isinstance(evidence_bundle, dict):
        raise AskV1ClientError(
            "evidence_schema_invalid",
            "evidence_bundle must be an object",
            None,
        )

    _normalize_legacy_authority_validation_details(evidence_bundle)

    try:
        validate_evidence_bundle_dict(evidence_bundle)
    except EvidenceSchemaValidationError as e:
        raise AskV1ClientError(
            "evidence_schema_invalid",
            str(e),
            {"path": getattr(e, "path", "$")},
        ) from e

    entries = evidence_bundle.get("entries") or []
    if not isinstance(entries, list) or len(entries) == 0:
        raise AskV1ClientError(
            "empty_evidence_bundle",
            "evidence_bundle.entries must contain at least one entry",
            None,
        )

    expected_hash = (ask_request.get("expected_workspace_identity_hash") or "").strip()
    if expected_hash:
        actual = str(evidence_bundle.get("workspace_identity_hash") or "")
        if actual != expected_hash:
            raise AskV1ClientError(
                "identity_mismatch",
                "expected_workspace_identity_hash does not match evidence_bundle.workspace_identity_hash",
                {
                    "expected_workspace_identity_hash": expected_hash,
                    "workspace_identity_hash": actual,
                },
            )

    revision = str(ask_request.get("revision") or "").strip() or "evidence_bundle.v1"
    task_id = request_id or "ask-v1-task"
    bundle = context_bundle_from_evidence_dict(evidence_bundle, task_id=task_id, revision=revision)
    client_context = ask_request.get("client_context") or {}
    dirty_buffers, dirty_buffer_parse = extract_dirty_buffers(client_context)
    bundle, overlay_meta = apply_dirty_buffer_overlay(bundle, dirty_buffers)
    bundle, budget_flags, _ = apply_context_budget(bundle)

    ar_dict = evidence_bundle.get("authority_resolution")
    authority_resolution = ar_dict if isinstance(ar_dict, dict) else None
    auth_owner_file = None
    if authority_resolution:
        po = authority_resolution.get("primary_owner")
        if isinstance(po, dict):
            auth_owner_file = str(po.get("file") or "").strip() or None

    grounding_evidence: list[tuple[str, str, str]] = []
    for ent in entries:
        if not isinstance(ent, dict):
            continue
        rel = str(ent.get("relative_path") or "")
        sn = ent.get("snippet") if isinstance(ent.get("snippet"), dict) else {}
        sr = str(sn.get("selection_reason") or "")
        role = str(ent.get("retrieval_role") or "")
        grounding_evidence.append((rel, sr, role))

    eff = merge_effective_intent(
        resolve_lexical_task_type(str(task_type or "general"), query, authority_resolution),
        query,
    )
    quality = assess_evidence_quality(
        query,
        [item.path for item in bundle.items],
        grounding_entries=grounding_evidence if grounding_evidence else None,
        effective_intent=eff,
        authority_primary_owner_file=auth_owner_file,
    )
    entries_list = evidence_bundle.get("entries") if isinstance(evidence_bundle.get("entries"), list) else []
    metadata = {
        "intent_type": quality.intent_type,
        "evidence_quality": quality.evidence_quality,
        "quality_reasons": list(quality.quality_reasons),
        "dominance_metrics": quality.dominance_metrics,
        "policy_version": quality.policy_version,
        "operator_hints": list(operator_hints_for_assessment(quality)),
        "usefulness_metrics": bundle_usefulness_metrics(entries_list),
        "dirty_buffer_overlay": {
            **overlay_meta,
            "payload_present": bool(dirty_buffer_parse.get("payload_present")),
            "provided_count": int(dirty_buffer_parse.get("provided_count", 0)),
            "invalid_count": int(dirty_buffer_parse.get("invalid_count", 0)),
            "valid_count": int(dirty_buffer_parse.get("valid_count", 0)),
        },
        "context_budget": build_context_budget_metadata(
            query=query,
            bundle=bundle,
            evidence_entries=[e for e in entries if isinstance(e, dict)],
            truncation_flags=budget_flags,
        ),
    }
    if authority_resolution:
        metadata["authority_resolution_present"] = True
        metadata["authority_status"] = str(authority_resolution.get("authority_status") or "")
        metadata["authority_confidence"] = str(authority_resolution.get("authority_confidence") or "")

    selected_file = ask_request.get("selected_file")
    selection = (
        (client_context.get("selection") or "").strip()
        if isinstance(client_context, dict)
        else ""
    )
    # User-anchored Explain/Debug: explicit file + selection (or a non-empty bundle) should
    # still run EXPLAIN_DEBUG even when the quality gate would block generic plan steps.
    skip_grounding_block_for_explain_debug = (
        str(task_type or "") == "EXPLAIN_DEBUG"
        and bool((str(selected_file or "").strip()))
        and (bool(selection) or bool(bundle.items))
    )

    ingestion_meta = {
        "ask_path": "v1_evidence",
        "context_source": "layer5.evidence_bundle.v1",
        "no_context_engine": True,
    }
    context_resolution = {
        "context_source": "layer5.evidence_bundle.v1",
        "no_repo_filesystem": True,
    }
    if quality.blocked and not skip_grounding_block_for_explain_debug:
        block_message = (
            "No context files matched relevant code evidence for this ask."
            if quality.evidence_quality == NO_MATCH
            else "No context files matched enough grounded evidence; plan steps are ungrounded."
        )
        return _build_plan_only_response(
            request_id=request_id,
            bundle=bundle,
            plan_steps=[],
            explain_debug=None,
            context_resolution=context_resolution,
            evidence_bundle=evidence_bundle,
            evidence_first_meta=ingestion_meta,
            ui_title="Grounding blocked (PLAN ONLY)",
            ui_message=block_message,
            ui_severity="warning",
            repo_aware_notes=[block_message],
            metadata=metadata,
            routing_mode="plan_only",
            trace_id=trace_id or None,
        )

    if quality.blocked and skip_grounding_block_for_explain_debug:
        metadata["grounding_block_overridden_by_explain_debug"] = True

    explain_debug_result: ExplainDebugResult | None = None
    plan_steps: List[str]
    weak_notes: List[str] = []
    owner_bias_meta: Dict[str, Any] = {}
    if dirty_buffer_parse.get("invalid_count", 0) > 0:
        weak_notes.append(
            "Dirty buffer overlay payload contained invalid entries; ignored malformed items and kept deterministic fallback behavior."
        )
    if dirty_buffer_parse.get("payload_present") and not overlay_meta.get("used"):
        weak_notes.append(
            "Dirty buffer overlay payload was provided but no matching bundle paths were overlaid."
        )

    if authority_resolution:
        owner_bias_meta = prioritize_owner_in_bundle(bundle, authority_resolution)
        metadata.update(owner_bias_meta)

    if task_type == "EXPLAIN_DEBUG" and selected_file and (selection or bundle.items):
        result = explain_debug(
            query=query,
            selected_file=str(selected_file),
            selection=selection or "",
            bundle=bundle,
            request_id=request_id,
            trace_id=trace_id,
        )
        explain_debug_result = result
        if result.error:
            plan_steps = [_explain_debug_failure_step(result.error)]
        else:
            plan_steps = ["Explain/debug analysis completed; see structured output above."]
    else:
        planner = PlanOnlyPlanner()
        plan_summary = planner.plan(
            query=query, bundle=bundle, authority_resolution=authority_resolution
        )
        plan_steps = plan_summary.steps
        if isinstance(plan_summary.meta, dict):
            metadata.update(plan_summary.meta)
    if quality.blocked and skip_grounding_block_for_explain_debug:
        weak_notes.append(
            "Plan-grounding gate reported weak or ungrounded evidence; EXPLAIN_DEBUG still ran "
            "using selected_file/selection as explicit anchors."
        )
    if quality.evidence_quality == WEAK:
        weak_notes.append("Evidence quality is WEAK; plan/explanation may be incomplete.")
    if metadata.get("method_window_visible"):
        metadata["method_window_visible_rate"] = 1.0
    elif metadata.get("method_claim_alignment_pass") is False:
        metadata["method_window_visible_rate"] = 0.0
    metadata["execution_path_stitched"] = bool(
        any(str(s).startswith("Execution-path stitch:") for s in (plan_steps or []))
    )
    metadata["explicit_method_body_evidence_present"] = bool(
        metadata.get("method_window_visible")
        or any(
            "Method-window excerpt:" in str(s) or "Visible method-window evidence:" in str(s)
            for s in (plan_steps or [])
        )
    )
    metadata["context_budget"] = build_context_budget_metadata(
        query=query,
        bundle=bundle,
        evidence_entries=[e for e in entries if isinstance(e, dict)],
        selected_file=str(selected_file or ""),
        selection=str(selection or ""),
        plan_steps=plan_steps,
        explain_debug_payload=explain_debug_result.to_dict() if explain_debug_result else None,
        truncation_flags=budget_flags,
    )

    routing_mode = (
        "explain_debug"
        if task_type == "EXPLAIN_DEBUG" and selected_file and (selection or bundle.items)
        else "plan_only"
    )

    ui_message = (
        "Context was built only from evidence_bundle.v1 (no repository reads on this path). "
        "Plan-only steps generated; no execution performed."
    )
    if (
        explain_debug_result is None
        and routing_mode == "plan_only"
        and (
            quality.intent_type == GENERIC_INTENT
            or "QUERY_TOO_GENERIC" in quality.quality_reasons
        )
    ):
        ui_message += (
            " A concise grounded flow summary is included from evidence and authority signals when available. "
            "For deeper branch-by-branch reasoning, use Motadata → Explain/Debug with source selected, "
            "or ask again with a concrete class/method symbol (e.g. AlertCorrelationEngine.start)."
        )

    return _build_plan_only_response(
        request_id=request_id,
        bundle=bundle,
        plan_steps=plan_steps,
        explain_debug=explain_debug_result,
        context_resolution=context_resolution,
        evidence_bundle=evidence_bundle,
        evidence_first_meta=ingestion_meta,
        ui_title="Evidence-driven Plan (PLAN ONLY)",
        ui_message=ui_message,
        ui_severity="info",
        repo_aware_notes=weak_notes or None,
        metadata=metadata,
        routing_mode=routing_mode,
        trace_id=trace_id or None,
    )

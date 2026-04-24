from __future__ import annotations

"""
Ask-service handlers — Repo-Aware Ask / Safe Planning sidecar path.

Implements:
- validation for AskRequest v0.1
- mapping to ContextRequest
- M3.12: optional manifest + doc_selector for repo-aware file hints
- ContextEngine call
- PlanOnlyPlanner invocation
- PlanOnlyResponse v0.1 construction

Option A: sidecar plan-only path, no loop/state-machine integration yet.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from runtime.context.contracts import ContextRequest
from runtime.context.doc_selector import select_from_manifest
from runtime.context.engine import ContextEngine, ContextEngineError, MissingExplicitFilesError
from runtime.context.manifest_builder import ManifestBuilder
from runtime.context.manifest_models import IngestionConfig
from runtime.layer5.retrieval.quality_gate import NO_MATCH, WEAK, assess_evidence_quality

from .dirty_buffer_overlay import apply_dirty_buffer_overlay, extract_dirty_buffers
from .evidence_bridge import resolve_workspace_input_path, try_build_layer5_evidence
from .authority_synthesis import prioritize_owner_in_bundle
from .context_budget import (
    apply_context_budget_for_surface,
    build_context_budget_metadata,
    evaluate_context_budget_policy,
)
from .planner import PlanOnlyPlanner
from .reasoner import explain_debug, ExplainDebugResult


REPO = Path(__file__).resolve().parents[1]  # runtime/
IDE_SCHEMAS = REPO / "ide" / "schemas"
LOG = logging.getLogger(__name__)


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


def validate_ask_request(data: dict) -> List[str]:
    """Validate against ask_request.v0.1.schema.json. Returns list of errors."""
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema not installed"]
    schema = _load_schema("ask_request.v0.1.schema.json")
    errs: List[str] = []
    for e in jsonschema.Draft7Validator(schema).iter_errors(data):
        errs.append(e.message)
    return errs


def _resolve_ask_repo_root(repo_root: str) -> Tuple[str, bool]:
    """
    Resolve repo root for context building. If the requested path does not exist
    on this server (e.g. client sent a Windows path, server is Linux), use
    ASK_DEFAULT_REPO_ROOT when set. Returns (effective_root, fallback_used).
    """
    root = Path(repo_root).resolve() if repo_root.strip() else Path()
    if root.exists() and root.is_dir():
        return (str(root), False)
    default = os.environ.get("ASK_DEFAULT_REPO_ROOT", "").strip()
    if default:
        default_path = Path(default).resolve()
        if default_path.exists() and default_path.is_dir():
            return (str(default_path), True)
    return (repo_root or ".", False)


def handle_ask_request(ask_request: dict) -> dict:
    """
    Process AskRequest and return PlanOnlyResponse v0.1.

    Hard invariants:
    - governance_posture == PLAN_ONLY
    - execution == false
    - no execution, no sandbox, no tool calls

    When task_type is EXPLAIN_DEBUG and selected_file + selection are present,
    invokes real reasoning (ExplainDebugReasoner). If reasoning is unavailable,
    returns explain_debug.error and does NOT use template planner steps.
    """
    request_id = str(ask_request.get("request_id", ""))
    trace_id = str(ask_request.get("trace_id") or "").strip()
    task_type = ask_request.get("task_type") or "general"
    LOG.info(
        "[ASK] trace_id=%s request_id=%s task_type=%s",
        trace_id or "(none)",
        request_id,
        task_type,
    )
    repo_root = (ask_request.get("repo_root") or "").strip() or "."
    revision = str(ask_request.get("revision", ""))
    query = str(ask_request.get("query", ""))
    selected_file = ask_request.get("selected_file")
    client_context = ask_request.get("client_context") or {}
    selection = (client_context.get("selection") or "").strip() if isinstance(client_context, dict) else ""
    dirty_buffers, dirty_buffer_parse = extract_dirty_buffers(client_context)

    evidence_first = bool(ask_request.get("evidence_first"))

    effective_root, fallback_used = _resolve_ask_repo_root(repo_root)
    if fallback_used:
        LOG.info("[ASK] repo_root invalid on server → using ASK_DEFAULT_REPO_ROOT")

    symbol_hints = _extract_symbol_hints(query)

    files: List[str] = []
    repo_aware_notes: List[str] = []

    manifest_root = repo_root
    root_path = Path(manifest_root) if manifest_root else None
    if (not root_path or not root_path.exists() or not root_path.is_dir()) and effective_root:
        root_path = Path(effective_root)
        manifest_root = effective_root

    if root_path is not None and root_path.exists() and root_path.is_dir():
        try:
            config = IngestionConfig.default_docs_and_runtime()
            manifest = ManifestBuilder().build(manifest_root, revision or "HEAD", config)
            req_for_select = ContextRequest(
                task_id=request_id or "ask-task",
                revision=revision or "unknown-revision",
                root_path=manifest_root,
                files=[str(selected_file)] if selected_file else [],
                symbol_hints=symbol_hints,
            )
            refs = select_from_manifest(manifest, query, req_for_select)
            if refs:
                files = [r.path for r in refs]
                reasons = {r.selection_reason for r in refs}
                repo_aware_notes.append(
                    f"Repo-aware selection: {len(files)} file(s) by " + ", ".join(sorted(reasons)) + "."
                )
        except Exception:
            pass

    if not files and selected_file:
        files = [str(selected_file)]

    context_resolution = (
        {"requested_repo_root": repo_root, "effective_repo_root": effective_root, "fallback_used": True}
        if fallback_used
        else None
    )

    bundle = None
    evidence_bundle_dict: Dict[str, Any] | None = None
    evidence_first_meta: Dict[str, Any] | None = None

    if evidence_first:
        ws_path = resolve_workspace_input_path(repo_root)
        if ws_path:
            pair = try_build_layer5_evidence(
                ws_path,
                query,
                request_id or "ask-task",
                revision or "unknown-revision",
                task_type=str(task_type or "general"),
                selected_file=str(selected_file).strip() if selected_file else None,
            )
            if pair:
                evidence_bundle_dict, bundle = pair
                evidence_first_meta = {"used_layer5": True, "workspace_input_path": ws_path}
            else:
                evidence_first_meta = {
                    "used_layer5": False,
                    "fallback_reason": "layer5_resolve_index_or_evidence_failed",
                }
        else:
            evidence_first_meta = {
                "used_layer5": False,
                "fallback_reason": "no_workspace_path_on_server",
            }

    if bundle is None:
        ctx_request = ContextRequest(
            task_id=request_id or "ask-task",
            revision=revision or "unknown-revision",
            root_path=effective_root,
            files=files,
            symbol_hints=symbol_hints,
        )

        engine = ContextEngine()
        try:
            bundle = engine.build_context_bundle(ctx_request)
        except (ContextEngineError, MissingExplicitFilesError) as e:
            return _build_error_plan_only_response(
                request_id=request_id,
                message=str(e),
                revision=revision,
                context_resolution=context_resolution,
                trace_id=trace_id or None,
                routing_mode="plan_only",
            )

    bundle, overlay_meta = apply_dirty_buffer_overlay(bundle, dirty_buffers)
    evidence_entries = []
    if isinstance(evidence_bundle_dict, dict):
        raw_entries = evidence_bundle_dict.get("entries")
        if isinstance(raw_entries, list):
            evidence_entries = [e for e in raw_entries if isinstance(e, dict)]
    budget_surface = "debug" if str(task_type or "") == "EXPLAIN_DEBUG" else "ask"
    bundle, budget_flags, _, budget_policy_cfg = apply_context_budget_for_surface(
        bundle, surface=budget_surface
    )
    if dirty_buffer_parse.get("invalid_count", 0) > 0:
        repo_aware_notes.append(
            "Dirty buffer overlay payload contained invalid entries; ignored malformed items and kept deterministic fallback behavior."
        )
    if dirty_buffer_parse.get("payload_present") and not overlay_meta.get("used"):
        repo_aware_notes.append(
            "Dirty buffer overlay payload was provided but no matching bundle paths were overlaid."
        )

    grounding_evidence = None
    if evidence_bundle_dict and isinstance(evidence_bundle_dict.get("entries"), list):
        grounding_evidence = []
        for ent in evidence_bundle_dict["entries"]:
            if not isinstance(ent, dict):
                continue
            rel = str(ent.get("relative_path") or "")
            sn = ent.get("snippet") if isinstance(ent.get("snippet"), dict) else {}
            sr = str(sn.get("selection_reason") or "")
            role = str(ent.get("retrieval_role") or "")
            grounding_evidence.append((rel, sr, role))
    ar_src = evidence_bundle_dict.get("authority_resolution") if evidence_bundle_dict else None
    authority_resolution = ar_src if isinstance(ar_src, dict) else None
    auth_owner_file = None
    if authority_resolution:
        po = authority_resolution.get("primary_owner")
        if isinstance(po, dict):
            auth_owner_file = str(po.get("file") or "").strip() or None
    if grounding_evidence:
        from runtime.layer5.retrieval.effective_intent import merge_effective_intent, resolve_lexical_task_type

        eff = merge_effective_intent(
            resolve_lexical_task_type(str(task_type or "general"), query, authority_resolution),
            query,
        )
        quality = assess_evidence_quality(
            query,
            [item.path for item in bundle.items],
            grounding_entries=grounding_evidence,
            effective_intent=eff,
            authority_primary_owner_file=auth_owner_file,
        )
    else:
        quality = assess_evidence_quality(
            query,
            [item.path for item in bundle.items],
            authority_primary_owner_file=auth_owner_file,
        )
    context_budget_meta = build_context_budget_metadata(
        query=query,
        bundle=bundle,
        evidence_entries=evidence_entries,
        selected_file="",
        selection="",
        truncation_flags=budget_flags,
    )
    metadata = {
        "intent_type": quality.intent_type,
        "evidence_quality": quality.evidence_quality,
        "quality_reasons": list(quality.quality_reasons),
        "dominance_metrics": quality.dominance_metrics,
        "policy_version": quality.policy_version,
        "dirty_buffer_overlay": {
            **overlay_meta,
            "payload_present": bool(dirty_buffer_parse.get("payload_present")),
            "provided_count": int(dirty_buffer_parse.get("provided_count", 0)),
            "invalid_count": int(dirty_buffer_parse.get("invalid_count", 0)),
            "valid_count": int(dirty_buffer_parse.get("valid_count", 0)),
        },
        "context_budget": context_budget_meta,
    }
    metadata["context_budget_policy"] = evaluate_context_budget_policy(
        surface=budget_surface,
        telemetry=context_budget_meta,
        policy_config=budget_policy_cfg,
    )
    if authority_resolution:
        metadata["authority_resolution_present"] = True
        metadata["authority_status"] = str(authority_resolution.get("authority_status") or "")
        metadata["authority_confidence"] = str(authority_resolution.get("authority_confidence") or "")
    skip_grounding_block_for_explain_debug = (
        str(task_type or "") == "EXPLAIN_DEBUG"
        and bool((str(selected_file or "").strip()))
        and (bool(selection) or bool(bundle.items))
    )
    fd = evidence_bundle_dict.get("fusion_diagnostics") if evidence_bundle_dict else None
    if isinstance(fd, dict):
        ei = fd.get("effective_intent")
        if isinstance(ei, dict) and ei.get("primary_mode"):
            metadata["retrieval_primary_mode"] = ei["primary_mode"]
        if fd.get("per_path") is not None:
            metadata["fusion_per_path_count"] = len(fd["per_path"]) if isinstance(fd["per_path"], list) else 0
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
            evidence_bundle=evidence_bundle_dict,
            evidence_first_meta=evidence_first_meta,
            repo_aware_notes=[block_message],
            ui_title="Grounding blocked (PLAN ONLY)",
            ui_message=block_message,
            ui_severity="warning",
            metadata=metadata,
            routing_mode="plan_only",
            trace_id=trace_id or None,
        )

    if quality.blocked and skip_grounding_block_for_explain_debug:
        metadata["grounding_block_overridden_by_explain_debug"] = True

    explain_debug_result: ExplainDebugResult | None = None
    plan_steps: List[str]
    weak_note: List[str] = []
    owner_bias_meta: Dict[str, Any] = {}

    if authority_resolution:
        owner_bias_meta = prioritize_owner_in_bundle(bundle, authority_resolution)
        metadata.update(owner_bias_meta)

    if task_type == "EXPLAIN_DEBUG" and selected_file and (selection or bundle.items):
        result = explain_debug(
            query=query,
            selected_file=selected_file,
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
        weak_note.append(
            "Plan-grounding gate reported weak or ungrounded evidence; EXPLAIN_DEBUG still ran "
            "using selected_file/selection as explicit anchors."
        )
    if quality.evidence_quality == WEAK:
        weak_note.append("Evidence quality is WEAK; plan/explanation may be incomplete.")
    if metadata.get("method_window_visible"):
        metadata["method_window_visible_rate"] = 1.0
    elif metadata.get("method_claim_alignment_pass") is False:
        metadata["method_window_visible_rate"] = 0.0
    metadata["execution_path_stitched"] = bool(
        metadata.get("execution_path_stitched")
        or any(str(s).startswith("Execution-path stitch:") for s in (plan_steps or []))
    )
    metadata["explicit_method_body_evidence_present"] = bool(
        metadata.get("method_window_visible")
        or any("Method-window excerpt:" in str(s) or "Visible method-window evidence:" in str(s) for s in (plan_steps or []))
    )
    metadata["context_budget"] = build_context_budget_metadata(
        query=query,
        bundle=bundle,
        evidence_entries=evidence_entries,
        selected_file=str(selected_file or ""),
        selection=str(selection or ""),
        plan_steps=plan_steps,
        explain_debug_payload=explain_debug_result.to_dict() if explain_debug_result else None,
        truncation_flags=budget_flags,
    )
    metadata["context_budget_policy"] = evaluate_context_budget_policy(
        surface=budget_surface,
        telemetry=metadata["context_budget"] if isinstance(metadata.get("context_budget"), dict) else {},
        policy_config=budget_policy_cfg,
    )

    routing_mode = (
        "explain_debug"
        if task_type == "EXPLAIN_DEBUG" and selected_file and (selection or bundle.items)
        else "plan_only"
    )

    return _build_plan_only_response(
        request_id=request_id,
        bundle=bundle,
        plan_steps=plan_steps,
        explain_debug=explain_debug_result,
        context_resolution=context_resolution,
        evidence_bundle=evidence_bundle_dict,
        evidence_first_meta=evidence_first_meta,
        repo_aware_notes=(repo_aware_notes + weak_note) or None,
        metadata=metadata,
        routing_mode=routing_mode,
        trace_id=trace_id or None,
    )


def _extract_symbol_hints(query: str) -> List[str]:
    """
    Simple, deterministic symbol-hint extraction from query text.

    - Split on non-alphanumeric
    - Lowercase
    - Keep tokens length >= 3
    - Deduplicate in order of first appearance
    """
    import re

    raw = re.split(r"[^A-Za-z0-9_]+", query)
    seen = set()
    hints: List[str] = []
    for t in raw:
        t = t.lower()
        if len(t) < 3:
            continue
        if t in seen:
            continue
        seen.add(t)
        hints.append(t)
    return hints


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_plan_only_response(
    request_id: str,
    bundle,
    plan_steps: List[str],
    explain_debug: ExplainDebugResult | None = None,
    context_resolution: Dict[str, Any] | None = None,
    evidence_bundle: Dict[str, Any] | None = None,
    evidence_first_meta: Dict[str, Any] | None = None,
    ui_title: str | None = None,
    ui_message: str | None = None,
    ui_severity: str | None = None,
    repo_aware_notes: List[str] | None = None,
    metadata: Dict[str, Any] | None = None,
    routing_mode: str | None = None,
    trace_id: str | None = None,
    plan_contract: Dict[str, Any] | None = None,
    code_reasoning_trace: Dict[str, Any] | None = None,
    patch_proposal: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    files = [
        {
            "path": item.path,
            "selection_reason": item.selection_reason,
        }
        for item in bundle.items
    ]
    selectors_used = list(bundle.provenance.selectors)
    has_grounded_files = len(bundle.items) > 0

    extra = list(repo_aware_notes or [])
    plan_summary: Dict[str, Any] = {"steps": plan_steps}
    if not has_grounded_files:
        plan_summary["notes"] = extra + [
            "No grounded context files were found; selectors produced no matching files. Plan steps are ungrounded."
        ]
    elif extra:
        plan_summary["notes"] = extra

    default_title = "Repo-Aware Plan (PLAN ONLY)"
    if has_grounded_files:
        default_message = (
            "Deterministic context bundle and plan-only steps generated. No execution performed."
        )
    else:
        default_message = (
            "No context files matched; plan steps are ungrounded. No execution performed."
        )
    default_severity = "info" if has_grounded_files else "warning"

    payload: Dict[str, Any] = {
        "schema_version": "plan_only_response.v0.1",
        "request_id": request_id,
        "timestamp_utc": _now_utc(),
        "context_bundle": {
            "revision": bundle.revision,
            "files": files,
            "selectors_used": selectors_used,
        },
        "plan_summary": plan_summary,
        "governance_posture": "PLAN_ONLY",
        "execution": False,
        "ui": {
            "title": ui_title if ui_title is not None else default_title,
            "message": ui_message if ui_message is not None else default_message,
            "severity": ui_severity if ui_severity is not None else default_severity,
        },
    }
    if explain_debug is not None:
        payload["explain_debug"] = explain_debug.to_dict()
    if context_resolution is not None:
        payload["context_resolution"] = context_resolution
    if evidence_bundle is not None:
        payload["evidence_bundle"] = evidence_bundle
    if evidence_first_meta is not None:
        payload["evidence_first_meta"] = evidence_first_meta
    if metadata is not None:
        payload["metadata"] = metadata
    if routing_mode is not None:
        payload["routing_mode"] = routing_mode
    if trace_id:
        payload["trace_id"] = trace_id
    if plan_contract is not None:
        payload["plan_contract"] = plan_contract
    if code_reasoning_trace is not None:
        payload["code_reasoning_trace"] = code_reasoning_trace
    if patch_proposal is not None:
        payload["patch_proposal"] = patch_proposal
    return payload


def _build_error_plan_only_response(
    request_id: str,
    message: str,
    revision: str = "",
    context_resolution: Dict[str, Any] | None = None,
    trace_id: str | None = None,
    routing_mode: str | None = "plan_only",
) -> Dict[str, Any]:
    """
    Build a PlanOnlyResponse that reports a context error but preserves execution=false invariants.
    """
    payload: Dict[str, Any] = {
        "schema_version": "plan_only_response.v0.1",
        "request_id": request_id,
        "timestamp_utc": _now_utc(),
        "context_bundle": {
            "revision": revision.strip() or "unknown-revision",
            "files": [],
            "selectors_used": [],
        },
        "plan_summary": {
            "steps": [],
            "notes": [f"ContextEngine error: {message}"],
        },
        "governance_posture": "PLAN_ONLY",
        "execution": False,
        "ui": {
            "title": "Repo-Aware Ask failed (PLAN ONLY)",
            "message": f"Context bundle could not be built: {message}",
            "severity": "warning",
        },
    }
    if context_resolution is not None:
        payload["context_resolution"] = context_resolution
    if trace_id:
        payload["trace_id"] = trace_id
    if routing_mode is not None:
        payload["routing_mode"] = routing_mode
    payload["metadata"] = {
        "intent_type": "GENERIC_INTENT",
        "evidence_quality": "INSUFFICIENT",
        "quality_reasons": ["NO_RELEVANT_HITS"],
        "dominance_metrics": {
            "top_k_size": 0.0,
            "core_code_in_top_k_pct": 0.0,
            "code_in_top_k_pct": 0.0,
            "noise_in_top_k_pct": 0.0,
            "core_in_top_3_count": 0.0,
            "max_consecutive_noise": 0.0,
        },
        "policy_version": "quality_gate.v1",
    }
    return payload

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

from .evidence_bridge import resolve_workspace_input_path, try_build_layer5_evidence
from .planner import PlanOnlyPlanner
from .reasoner import explain_debug, ExplainDebugResult


REPO = Path(__file__).resolve().parents[1]  # runtime/
IDE_SCHEMAS = REPO / "ide" / "schemas"
LOG = logging.getLogger(__name__)


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
    repo_root = (ask_request.get("repo_root") or "").strip() or "."
    revision = str(ask_request.get("revision", ""))
    query = str(ask_request.get("query", ""))
    selected_file = ask_request.get("selected_file")
    task_type = ask_request.get("task_type") or "general"
    client_context = ask_request.get("client_context") or {}
    selection = (client_context.get("selection") or "").strip() if isinstance(client_context, dict) else ""

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
            )

    quality = assess_evidence_quality(query, [item.path for item in bundle.items])
    metadata = {
        "intent_type": quality.intent_type,
        "evidence_quality": quality.evidence_quality,
        "quality_reasons": list(quality.quality_reasons),
        "dominance_metrics": quality.dominance_metrics,
        "policy_version": quality.policy_version,
    }
    if quality.blocked:
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
        )

    explain_debug_result: ExplainDebugResult | None = None
    plan_steps: List[str]
    weak_note: List[str] = []

    if task_type == "EXPLAIN_DEBUG" and selected_file and (selection or bundle.items):
        result = explain_debug(
            query=query,
            selected_file=selected_file,
            selection=selection or "",
            bundle=bundle,
            request_id=request_id,
        )
        explain_debug_result = result
        if result.error:
            plan_steps = ["Reasoning service unavailable; no template steps substituted."]
        else:
            plan_steps = ["Explain/debug analysis completed; see structured output above."]
    else:
        planner = PlanOnlyPlanner()
        plan_summary = planner.plan(query=query, bundle=bundle)
        plan_steps = plan_summary.steps
    if quality.evidence_quality == WEAK:
        weak_note.append("Evidence quality is WEAK; plan/explanation may be incomplete.")

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
    return payload


def _build_error_plan_only_response(
    request_id: str,
    message: str,
    revision: str = "",
    context_resolution: Dict[str, Any] | None = None,
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

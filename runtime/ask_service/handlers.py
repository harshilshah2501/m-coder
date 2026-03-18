from __future__ import annotations

"""
Ask-service handlers — Repo-Aware Ask / Safe Planning sidecar path.

Implements:
- validation for AskRequest v0.1
- mapping to ContextRequest
- ContextEngine call
- PlanOnlyPlanner invocation
- PlanOnlyResponse v0.1 construction

Option A: sidecar plan-only path, no loop/state-machine integration yet.
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from runtime.context.contracts import ContextRequest
from runtime.context.engine import ContextEngine, ContextEngineError, MissingExplicitFilesError

from .planner import PlanOnlyPlanner
from .reasoner import explain_debug, ExplainDebugResult


REPO = Path(__file__).resolve().parents[1]  # runtime/
IDE_SCHEMAS = REPO / "ide" / "schemas"


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
    repo_root = str(ask_request.get("repo_root", ""))
    revision = str(ask_request.get("revision", ""))
    query = str(ask_request.get("query", ""))
    selected_file = ask_request.get("selected_file")
    task_type = ask_request.get("task_type") or "general"
    client_context = ask_request.get("client_context") or {}
    selection = (client_context.get("selection") or "").strip() if isinstance(client_context, dict) else ""

    symbol_hints = _extract_symbol_hints(query)

    files: List[str] = []
    if selected_file:
        files = [str(selected_file)]

    ctx_request = ContextRequest(
        task_id=request_id or "ask-task",
        revision=revision or "unknown-revision",
        root_path=repo_root,
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
        )

    explain_debug_result: ExplainDebugResult | None = None
    plan_steps: List[str]

    if task_type == "EXPLAIN_DEBUG" and selected_file and (selection or bundle.items):
        result = explain_debug(
            query=query,
            selected_file=selected_file,
            selection=selection or "",
            bundle=bundle,
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

    return _build_plan_only_response(
        request_id=request_id,
        bundle=bundle,
        plan_steps=plan_steps,
        explain_debug=explain_debug_result,
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
) -> Dict[str, Any]:
    files = [
        {
            "path": item.path,
            "selection_reason": item.selection_reason,
        }
        for item in bundle.items
    ]
    selectors_used = list(bundle.provenance.selectors)

    payload: Dict[str, Any] = {
        "schema_version": "plan_only_response.v0.1",
        "request_id": request_id,
        "timestamp_utc": _now_utc(),
        "context_bundle": {
            "revision": bundle.revision,
            "files": files,
            "selectors_used": selectors_used,
        },
        "plan_summary": {
            "steps": plan_steps,
        },
        "governance_posture": "PLAN_ONLY",
        "execution": False,
        "ui": {
            "title": "Repo-Aware Plan (PLAN ONLY)",
            "message": "Deterministic context bundle and plan-only steps generated. No execution performed.",
            "severity": "info",
        },
    }
    if explain_debug is not None:
        payload["explain_debug"] = explain_debug.to_dict()
    return payload


def _build_error_plan_only_response(
    request_id: str,
    message: str,
) -> Dict[str, Any]:
    """
    Build a PlanOnlyResponse that reports a context error but preserves execution=false invariants.
    """
    return {
        "schema_version": "plan_only_response.v0.1",
        "request_id": request_id,
        "timestamp_utc": _now_utc(),
        "context_bundle": {
            "revision": "unknown-revision",
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


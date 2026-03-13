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
    """
    request_id = str(ask_request.get("request_id", ""))
    repo_root = str(ask_request.get("repo_root", ""))
    revision = str(ask_request.get("revision", ""))
    query = str(ask_request.get("query", ""))
    selected_file = ask_request.get("selected_file")

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
        # Fail-closed on context building; surface structured error but keep execution=false.
        return _build_error_plan_only_response(
            request_id=request_id,
            message=str(e),
        )

    planner = PlanOnlyPlanner()
    plan_summary = planner.plan(query=query, bundle=bundle)

    return _build_plan_only_response(
        request_id=request_id,
        bundle=bundle,
        plan_steps=plan_summary.steps,
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
) -> Dict[str, Any]:
    files = [
        {
            "path": item.path,
            "selection_reason": item.selection_reason,
        }
        for item in bundle.items
    ]
    selectors_used = list(bundle.provenance.selectors)

    return {
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


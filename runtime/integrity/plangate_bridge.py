"""
Bridge from CanonicalExecutionIntent to Plan-Gate request — M4.1.

Builds the lossless projection (request dict) that PlanGateService.evaluate()
consumes, so Plan-Gate evaluates the same artifact that was normalized.
command = intent.argv (list); no re-parsing.
"""

from __future__ import annotations

from typing import Any

from runtime.integrity.canonical_intent import CanonicalExecutionIntent


def intent_to_plangate_request(
    intent: CanonicalExecutionIntent,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build Plan-Gate request dict from CanonicalExecutionIntent (lossless projection).

    Plan-Gate receives command=list(intent.argv) so it evaluates the same
    execution representation that will be passed to SandboxExecutor.
    """
    overrides = overrides or {}
    request: dict[str, Any] = {
        "request_id": intent.request_id,
        "plan_hash": intent.plan_hash,
        "canonical_hash": intent.canonical_hash,
        "command": list(intent.argv),
        "repo_root": getattr(intent, "repo_root", None) or intent.working_dir,
        "working_dir": intent.working_dir,
        "branch": getattr(intent, "branch", "") or "",
    }
    if overrides.get("plan_gate_refuse") is True:
        request["plan_gate_refuse"] = True
    if overrides.get("plan_gate_defer") is True:
        request["plan_gate_defer"] = True
    if overrides.get("plan_gate_bounded_allow") is True:
        request["plan_gate_bounded_allow"] = True
    for key in ("revision", "ide_context", "authority_denied", "boundary_detected", "irreversible"):
        if key in overrides:
            request[key] = overrides[key]
    return request

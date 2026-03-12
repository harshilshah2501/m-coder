"""
Plan-Gate Service — M3.3 mandatory pre-sandbox gate.

Evaluates requests and returns PlanGateDecision.
MVP: deterministic rule-based evaluation (no LLM).
"""

from __future__ import annotations

from typing import Any

from runtime.plangate.plangate_decision import PlanGateDecision, Posture


class PlanGateService:
    """
    Mandatory gate before any sandbox execution.
    evaluate(request) returns a posture; only safe_execute may proceed to sandbox.
    """

    # Commands that are always refused (no execution).
    REFUSED_COMMANDS: frozenset[str] = frozenset({"curl", "wget", "rm", "mkfs", "dd"})

    def evaluate(self, request: dict[str, Any]) -> PlanGateDecision:
        """
        Evaluate a request. Returns PlanGateDecision (refuse | defer | bounded_allow | safe_execute).
        Deterministic, rule-based. No LLM calls.
        """
        request_id = str(request.get("request_id", ""))
        plan_hash = str(request.get("plan_hash", ""))
        command = request.get("command")
        action_type = request.get("action_type")
        force_defer = request.get("plan_gate_defer") is True
        force_refuse = request.get("plan_gate_refuse") is True
        force_bounded_allow = request.get("plan_gate_bounded_allow") is True

        if force_refuse:
            return PlanGateDecision(
                posture="refuse",
                authority_ok=False,
                boundary_detected=True,
                irreversible=True,
                reason="Plan-Gate refused by request (plan_gate_refuse)",
            )
        if force_defer:
            return PlanGateDecision(
                posture="defer",
                authority_ok=True,
                boundary_detected=False,
                irreversible=False,
                reason="Plan-Gate deferred by request (plan_gate_defer)",
            )
        if force_bounded_allow:
            return PlanGateDecision(
                posture="bounded_allow",
                authority_ok=True,
                boundary_detected=False,
                irreversible=False,
                reason="Plan-Gate bounded_allow by request (plan_gate_bounded_allow)",
            )

        if command and isinstance(command, (list, tuple)):
            cmd_name = (command[0] or "").strip()
            if "/" in cmd_name:
                cmd_name = cmd_name.split("/")[-1]
            if cmd_name in self.REFUSED_COMMANDS:
                return PlanGateDecision(
                    posture="refuse",
                    authority_ok=False,
                    boundary_detected=True,
                    irreversible=True,
                    reason=f"Command '{cmd_name}' not permitted for execution",
                )

        # Default: allow safe execution (echo, python, pytest, etc.)
        return PlanGateDecision(
            posture="safe_execute",
            authority_ok=True,
            boundary_detected=False,
            irreversible=False,
            reason="Plan-Gate allowed: safe_execute",
        )

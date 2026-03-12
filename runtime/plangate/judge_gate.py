"""
Plan-Gate JudgeGate — M3.3B decomposition.

The posture-deciding component. Combines authority + irreversibility + request hints
and emits the final PlanGateDecision: refuse | defer | bounded_allow | safe_execute.

This is the explicit posture decider; behavior is deterministic and consistent.
"""

from __future__ import annotations

from typing import Any

from runtime.plangate.contracts import AuthorityResult, IrreversibilityResult, JudgeInput
from runtime.plangate.plangate_decision import PlanGateDecision, Posture


class JudgeGate:
    """
    The posture-deciding component of Plan-Gate.

    Inputs:
    - request: Original request dict
    - AuthorityResult: From AuthorityValidator
    - IrreversibilityResult: From IrreversibilityDetector

    Output:
    - PlanGateDecision: posture (refuse | defer | bounded_allow | safe_execute)

    Decision logic (deterministic, in priority order):
    1. Explicit refuse hint dominates → refuse
    2. Explicit defer hint dominates after refuse → defer
    3. Explicit bounded_allow hint comes next → bounded_allow
    4. Authority failure (authority_ok=False) → refuse
    5. Irreversible/boundary crossing and not safe → refuse
    6. Boundary detected but not irreversible → bounded_allow (boundary-adjacent)
    7. Otherwise → safe_execute

    MVP mapping (preserves existing externally visible behavior):
    - Dangerous commands (curl/wget/rm/dd/mkfs) → refuse
    - Explicit plan_gate_defer → defer
    - Explicit plan_gate_bounded_allow → bounded_allow
    - Ordinary safe commands (echo/python/pytest) → safe_execute
    """

    def judge(self, judge_input: JudgeInput) -> PlanGateDecision:
        """
        Produce the final PlanGateDecision from authority and irreversibility results.

        Args:
            judge_input: JudgeInput containing request, authority_result, irreversibility_result.

        Returns:
            PlanGateDecision with posture and all supporting fields populated.
        """
        request = judge_input.request
        authority = judge_input.authority_result
        irreversibility = judge_input.irreversibility_result

        # Priority 1: Explicit refuse hint dominates
        if request.get("plan_gate_refuse") is True:
            return PlanGateDecision(
                posture="refuse",
                authority_ok=False,
                boundary_detected=True,
                irreversible=True,
                reason="Plan-Gate refused by request (plan_gate_refuse)",
            )

        # Priority 2: Explicit defer hint dominates after refuse
        if request.get("plan_gate_defer") is True:
            return PlanGateDecision(
                posture="defer",
                authority_ok=True,
                boundary_detected=False,
                irreversible=False,
                reason="Plan-Gate deferred by request (plan_gate_defer)",
            )

        # Priority 3: Explicit bounded_allow hint
        if request.get("plan_gate_bounded_allow") is True:
            return PlanGateDecision(
                posture="bounded_allow",
                authority_ok=True,
                boundary_detected=False,
                irreversible=False,
                reason="Plan-Gate bounded_allow by request (plan_gate_bounded_allow)",
            )

        # Priority 4: Authority failure → refuse
        if not authority.authority_ok:
            return PlanGateDecision(
                posture="refuse",
                authority_ok=False,
                boundary_detected=irreversibility.boundary_detected,
                irreversible=irreversibility.irreversible,
                reason=authority.authority_reason,
            )

        # Priority 5: Irreversible and boundary crossing → refuse
        # (In MVP, dangerous commands result in authority failure above,
        # but this is a safety net for explicit irreversibility hints.)
        if irreversibility.irreversible and irreversibility.boundary_detected:
            return PlanGateDecision(
                posture="refuse",
                authority_ok=authority.authority_ok,
                boundary_detected=True,
                irreversible=True,
                reason=irreversibility.boundary_reason,
            )

        # Priority 6: Boundary detected but not irreversible → bounded_allow
        # (This is for boundary-adjacent cases; in MVP most dangerous commands
        # are caught by authority check above.)
        if irreversibility.boundary_detected and not irreversibility.irreversible:
            return PlanGateDecision(
                posture="bounded_allow",
                authority_ok=authority.authority_ok,
                boundary_detected=True,
                irreversible=False,
                reason=f"Boundary detected but not irreversible: {irreversibility.boundary_reason}",
            )

        # Priority 7: Default → safe_execute
        return PlanGateDecision(
            posture="safe_execute",
            authority_ok=True,
            boundary_detected=False,
            irreversible=False,
            reason="Plan-Gate allowed: safe_execute",
        )

    def judge_from_components(
        self,
        request: dict[str, Any],
        authority_result: AuthorityResult,
        irreversibility_result: IrreversibilityResult,
    ) -> PlanGateDecision:
        """
        Convenience method to judge from separate components.

        Args:
            request: Original request dict.
            authority_result: Result from AuthorityValidator.
            irreversibility_result: Result from IrreversibilityDetector.

        Returns:
            PlanGateDecision.
        """
        judge_input = JudgeInput(
            request=request,
            authority_result=authority_result,
            irreversibility_result=irreversibility_result,
        )
        return self.judge(judge_input)

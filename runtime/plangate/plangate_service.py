"""
Plan-Gate Service — M3.3 mandatory pre-sandbox gate.

Evaluates requests and returns PlanGateDecision.
MVP: deterministic rule-based evaluation (no LLM).

M3.3B Internal Decomposition:
PlanGateService now delegates to first-class subcomponents:
- AuthorityValidator → AuthorityResult
- IrreversibilityDetector → IrreversibilityResult
- JudgeGate → PlanGateDecision

External contract is unchanged: evaluate(request) → PlanGateDecision.
"""

from __future__ import annotations

from typing import Any

from runtime.plangate.authority_validator import AuthorityValidator
from runtime.plangate.contracts import AuthorityResult, IrreversibilityResult
from runtime.plangate.irreversibility_detector import IrreversibilityDetector
from runtime.plangate.judge_gate import JudgeGate
from runtime.plangate.plangate_decision import PlanGateDecision, Posture


class PlanGateService:
    """
    Mandatory gate before any sandbox execution.
    evaluate(request) returns a posture; only safe_execute may proceed to sandbox.

    Internal architecture (M3.3B decomposition):

    PlanGateService
     ├─ AuthorityValidator
     ├─ IrreversibilityDetector
     └─ JudgeGate

    Flow:
    request → AuthorityValidator → IrreversibilityDetector → JudgeGate → PlanGateDecision

    External contract is unchanged.
    """

    # Commands that are always refused (no execution).
    # Kept here for backward compatibility; also defined in subcomponents.
    REFUSED_COMMANDS: frozenset[str] = frozenset({"curl", "wget", "rm", "mkfs", "dd"})

    def __init__(
        self,
        authority_validator: AuthorityValidator | None = None,
        irreversibility_detector: IrreversibilityDetector | None = None,
        judge_gate: JudgeGate | None = None,
    ) -> None:
        """
        Initialize PlanGateService with optional subcomponent overrides.

        Args:
            authority_validator: Custom AuthorityValidator (default: create new).
            irreversibility_detector: Custom IrreversibilityDetector (default: create new).
            judge_gate: Custom JudgeGate (default: create new).
        """
        self.authority_validator = authority_validator or AuthorityValidator()
        self.irreversibility_detector = irreversibility_detector or IrreversibilityDetector()
        self.judge_gate = judge_gate or JudgeGate()

    def evaluate(self, request: dict[str, Any]) -> PlanGateDecision:
        """
        Evaluate a request. Returns PlanGateDecision (refuse | defer | bounded_allow | safe_execute).
        Deterministic, rule-based. No LLM calls.

        Internal flow (M3.3B):
        1. Call AuthorityValidator → AuthorityResult
        2. Call IrreversibilityDetector → IrreversibilityResult
        3. Call JudgeGate → PlanGateDecision (final posture)

        Args:
            request: Request dict with fields like request_id, plan_hash, command,
                     plan_gate_defer, plan_gate_refuse, plan_gate_bounded_allow.

        Returns:
            PlanGateDecision with posture and supporting fields from subcomponents.
        """
        # Step 1: Validate authority
        authority_result = self.authority_validator.validate(request)

        # Step 2: Detect irreversibility and boundaries
        irreversibility_result = self.irreversibility_detector.detect(request)

        # Step 3: Judge final posture
        decision = self.judge_gate.judge_from_components(
            request=request,
            authority_result=authority_result,
            irreversibility_result=irreversibility_result,
        )

        return decision

    def evaluate_with_components(
        self, request: dict[str, Any]
    ) -> tuple[PlanGateDecision, AuthorityResult, IrreversibilityResult]:
        """
        Evaluate a request and return all intermediate results.

        Useful for debugging, testing, and observability.

        Args:
            request: Request dict.

        Returns:
            Tuple of (PlanGateDecision, AuthorityResult, IrreversibilityResult).
        """
        authority_result = self.authority_validator.validate(request)
        irreversibility_result = self.irreversibility_detector.detect(request)
        decision = self.judge_gate.judge_from_components(
            request=request,
            authority_result=authority_result,
            irreversibility_result=irreversibility_result,
        )
        return decision, authority_result, irreversibility_result

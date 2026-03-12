"""
Unit tests for Plan-Gate JudgeGate — M3.3B decomposition.

Tests posture decision logic: refuse | defer | bounded_allow | safe_execute.
"""

from __future__ import annotations

import pytest

from runtime.plangate.judge_gate import JudgeGate
from runtime.plangate.contracts import AuthorityResult, IrreversibilityResult, JudgeInput
from runtime.plangate.plangate_decision import PlanGateDecision


class TestJudgeGate:
    """Tests for JudgeGate posture decision logic."""

    def _make_judge_input(
        self,
        request: dict | None = None,
        authority_ok: bool = True,
        authority_reason: str = "default",
        authority_source: str | None = "default",
        boundary_detected: bool = False,
        irreversible: bool = False,
        boundary_reason: str = "",
        boundary_class: str | None = None,
    ) -> JudgeInput:
        return JudgeInput(
            request=request or {},
            authority_result=AuthorityResult(
                authority_ok=authority_ok,
                authority_reason=authority_reason,
                authority_source=authority_source,
            ),
            irreversibility_result=IrreversibilityResult(
                boundary_detected=boundary_detected,
                irreversible=irreversible,
                boundary_reason=boundary_reason,
                boundary_class=boundary_class,
            ),
        )

    # --- Priority 1: Explicit refuse hint dominates ---

    def test_explicit_refuse_hint_dominates(self) -> None:
        gate = JudgeGate()
        judge_input = self._make_judge_input(
            request={"plan_gate_refuse": True},
            authority_ok=True,
        )
        decision = gate.judge(judge_input)
        assert decision.posture == "refuse"
        assert "plan_gate_refuse" in decision.reason

    def test_explicit_refuse_overrides_defer(self) -> None:
        gate = JudgeGate()
        judge_input = self._make_judge_input(
            request={"plan_gate_refuse": True, "plan_gate_defer": True},
            authority_ok=True,
        )
        decision = gate.judge(judge_input)
        assert decision.posture == "refuse"

    def test_explicit_refuse_overrides_bounded_allow(self) -> None:
        gate = JudgeGate()
        judge_input = self._make_judge_input(
            request={"plan_gate_refuse": True, "plan_gate_bounded_allow": True},
            authority_ok=True,
        )
        decision = gate.judge(judge_input)
        assert decision.posture == "refuse"

    # --- Priority 2: Explicit defer hint dominates after refuse ---

    def test_explicit_defer_hint(self) -> None:
        gate = JudgeGate()
        judge_input = self._make_judge_input(
            request={"plan_gate_defer": True},
            authority_ok=True,
        )
        decision = gate.judge(judge_input)
        assert decision.posture == "defer"
        assert "plan_gate_defer" in decision.reason

    def test_explicit_defer_overrides_bounded_allow(self) -> None:
        gate = JudgeGate()
        judge_input = self._make_judge_input(
            request={"plan_gate_defer": True, "plan_gate_bounded_allow": True},
            authority_ok=True,
        )
        decision = gate.judge(judge_input)
        assert decision.posture == "defer"

    # --- Priority 3: Explicit bounded_allow hint ---

    def test_explicit_bounded_allow_hint(self) -> None:
        gate = JudgeGate()
        judge_input = self._make_judge_input(
            request={"plan_gate_bounded_allow": True},
            authority_ok=True,
        )
        decision = gate.judge(judge_input)
        assert decision.posture == "bounded_allow"
        assert "plan_gate_bounded_allow" in decision.reason

    # --- Priority 4: Authority failure → refuse ---

    def test_authority_failure_refuses(self) -> None:
        gate = JudgeGate()
        judge_input = self._make_judge_input(
            authority_ok=False,
            authority_reason="Command not authorized",
        )
        decision = gate.judge(judge_input)
        assert decision.posture == "refuse"
        assert decision.authority_ok is False
        assert "Command not authorized" in decision.reason

    def test_authority_failure_with_boundary(self) -> None:
        gate = JudgeGate()
        judge_input = self._make_judge_input(
            authority_ok=False,
            authority_reason="Dangerous command",
            boundary_detected=True,
            irreversible=True,
        )
        decision = gate.judge(judge_input)
        assert decision.posture == "refuse"
        assert decision.authority_ok is False
        assert decision.boundary_detected is True
        assert decision.irreversible is True

    # --- Priority 5: Irreversible and boundary crossing → refuse ---

    def test_irreversible_boundary_crossing_refuses(self) -> None:
        gate = JudgeGate()
        judge_input = self._make_judge_input(
            authority_ok=True,
            boundary_detected=True,
            irreversible=True,
            boundary_reason="Explicit irreversible boundary",
        )
        decision = gate.judge(judge_input)
        assert decision.posture == "refuse"
        assert decision.boundary_detected is True
        assert decision.irreversible is True

    # --- Priority 6: Boundary detected but not irreversible → bounded_allow ---

    def test_boundary_detected_not_irreversible_bounded_allow(self) -> None:
        gate = JudgeGate()
        judge_input = self._make_judge_input(
            authority_ok=True,
            boundary_detected=True,
            irreversible=False,
            boundary_reason="Near boundary but not irreversible",
        )
        decision = gate.judge(judge_input)
        assert decision.posture == "bounded_allow"
        assert decision.boundary_detected is True
        assert decision.irreversible is False

    # --- Priority 7: Default → safe_execute ---

    def test_default_safe_execute(self) -> None:
        gate = JudgeGate()
        judge_input = self._make_judge_input(
            authority_ok=True,
            boundary_detected=False,
            irreversible=False,
        )
        decision = gate.judge(judge_input)
        assert decision.posture == "safe_execute"
        assert decision.authority_ok is True
        assert decision.boundary_detected is False
        assert decision.irreversible is False

    def test_safe_command_safe_execute(self) -> None:
        gate = JudgeGate()
        judge_input = self._make_judge_input(
            request={"command": ["echo", "hello"]},
            authority_ok=True,
        )
        decision = gate.judge(judge_input)
        assert decision.posture == "safe_execute"

    # --- judge_from_components convenience method ---

    def test_judge_from_components(self) -> None:
        gate = JudgeGate()
        authority_result = AuthorityResult(
            authority_ok=True,
            authority_reason="Granted",
            authority_source="default",
        )
        irreversibility_result = IrreversibilityResult(
            boundary_detected=False,
            irreversible=False,
            boundary_reason="No boundary",
            boundary_class=None,
        )
        decision = gate.judge_from_components(
            request={"command": ["echo", "hello"]},
            authority_result=authority_result,
            irreversibility_result=irreversibility_result,
        )
        assert decision.posture == "safe_execute"

    # --- Verify may_execute property aligns with posture ---

    def test_may_execute_only_for_safe_execute(self) -> None:
        gate = JudgeGate()

        # safe_execute → may_execute=True
        safe_input = self._make_judge_input(authority_ok=True)
        safe_decision = gate.judge(safe_input)
        assert safe_decision.posture == "safe_execute"
        assert safe_decision.may_execute is True

        # refuse → may_execute=False
        refuse_input = self._make_judge_input(request={"plan_gate_refuse": True})
        refuse_decision = gate.judge(refuse_input)
        assert refuse_decision.posture == "refuse"
        assert refuse_decision.may_execute is False

        # defer → may_execute=False
        defer_input = self._make_judge_input(request={"plan_gate_defer": True})
        defer_decision = gate.judge(defer_input)
        assert defer_decision.posture == "defer"
        assert defer_decision.may_execute is False

        # bounded_allow → may_execute=False
        bounded_input = self._make_judge_input(request={"plan_gate_bounded_allow": True})
        bounded_decision = gate.judge(bounded_input)
        assert bounded_decision.posture == "bounded_allow"
        assert bounded_decision.may_execute is False


class TestJudgeInput:
    """Tests for JudgeInput dataclass."""

    def test_judge_input_construction(self) -> None:
        request = {"command": ["echo", "hello"]}
        authority_result = AuthorityResult(True, "ok", "default")
        irreversibility_result = IrreversibilityResult(False, False, "no boundary", None)

        judge_input = JudgeInput(
            request=request,
            authority_result=authority_result,
            irreversibility_result=irreversibility_result,
        )

        assert judge_input.request == request
        assert judge_input.authority_result is authority_result
        assert judge_input.irreversibility_result is irreversibility_result

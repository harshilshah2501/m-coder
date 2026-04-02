"""Stage 3 deterministic state machine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class IllegalTransitionError(Exception):
    """Raised for invalid state transitions."""


TERMINAL_STATES = {"COMPLETED", "REFUSED", "BLOCKED", "FAILED", "INSUFFICIENT"}
ALL_STATES = {
    "CONTEXT_READY",
    "PLAN_GATED",
    "MODEL_PROPOSED",
    "PROPOSAL_VALIDATED",
    "TOOL_EXECUTING",
    "TOOL_RESULT_READY",
    "MODEL_REVISED",
    *TERMINAL_STATES,
}


@dataclass(frozen=True)
class TransitionRule:
    from_state: str
    event: str
    to_state: str
    guard: str


TRANSITIONS: list[TransitionRule] = [
    TransitionRule("CONTEXT_READY", "plan_gate_pre_pass", "PLAN_GATED", "evidence_valid"),
    TransitionRule("CONTEXT_READY", "plan_gate_pre_refuse", "REFUSED", "always"),
    TransitionRule("CONTEXT_READY", "plan_gate_pre_block", "BLOCKED", "always"),
    TransitionRule("PLAN_GATED", "request_proposal", "MODEL_PROPOSED", "remaining_budget_gt_0"),
    TransitionRule("MODEL_PROPOSED", "proposal_schema_policy_valid", "PROPOSAL_VALIDATED", "always"),
    TransitionRule("MODEL_PROPOSED", "proposal_invalid_recoverable", "MODEL_REVISED", "remaining_budget_gt_0"),
    TransitionRule("MODEL_PROPOSED", "proposal_invalid_terminal", "FAILED", "always"),
    TransitionRule("PROPOSAL_VALIDATED", "decision_proceed_to_tool", "TOOL_EXECUTING", "one_tool_requested"),
    TransitionRule("PROPOSAL_VALIDATED", "decision_terminate_success", "COMPLETED", "always"),
    TransitionRule("PROPOSAL_VALIDATED", "decision_terminate_refused", "REFUSED", "always"),
    TransitionRule("PROPOSAL_VALIDATED", "decision_revise", "MODEL_REVISED", "remaining_budget_gt_0"),
    TransitionRule("TOOL_EXECUTING", "tool_result_ready", "TOOL_RESULT_READY", "always"),
    TransitionRule("TOOL_EXECUTING", "gate_blocked", "BLOCKED", "always"),
    TransitionRule("TOOL_EXECUTING", "tool_terminal_failure", "FAILED", "always"),
    TransitionRule("TOOL_RESULT_READY", "runtime_decide_revise", "MODEL_REVISED", "remaining_budget_gt_0"),
    TransitionRule("TOOL_RESULT_READY", "runtime_decide_success", "COMPLETED", "always"),
    TransitionRule("TOOL_RESULT_READY", "runtime_decide_blocked", "BLOCKED", "always"),
    TransitionRule("TOOL_RESULT_READY", "runtime_decide_insufficient", "INSUFFICIENT", "always"),
    TransitionRule("TOOL_RESULT_READY", "runtime_decide_failed", "FAILED", "always"),
    TransitionRule("MODEL_REVISED", "repropose", "MODEL_PROPOSED", "remaining_budget_gt_0"),
    TransitionRule("MODEL_REVISED", "budget_exhausted", "FAILED", "always"),
]


class Stage3StateMachine:
    """Deterministic transition executor for Stage 3."""

    def __init__(self) -> None:
        self._lookup = {(t.from_state, t.event): t for t in TRANSITIONS}

    def is_terminal(self, state: str) -> bool:
        return state in TERMINAL_STATES

    def next_state(self, current_state: str, event: str, context: dict[str, Any]) -> str:
        if current_state not in ALL_STATES:
            raise IllegalTransitionError(f"Unknown state: {current_state}")
        if self.is_terminal(current_state):
            raise IllegalTransitionError(f"Cannot transition from terminal state: {current_state}")

        rule = self._lookup.get((current_state, event))
        if rule is None:
            raise IllegalTransitionError(f"Illegal transition: {current_state} --{event}--> ?")
        if not self._guard_passed(rule.guard, context):
            raise IllegalTransitionError(
                f"Guard failed for transition {current_state} --{event}--> {rule.to_state}: {rule.guard}"
            )
        return rule.to_state

    @staticmethod
    def _guard_passed(guard: str, context: dict[str, Any]) -> bool:
        if guard == "always":
            return True
        if guard == "remaining_budget_gt_0":
            return int(context.get("remaining_budget", 0)) > 0
        if guard == "evidence_valid":
            return bool(context.get("evidence_valid", False))
        if guard == "one_tool_requested":
            return int(context.get("tool_calls_requested", 0)) == 1
        return False

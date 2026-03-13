"""
Transition validation — M3.1 orchestration substrate.

Validates state transitions against transition_matrix.v0.1.json.
Refuses invalid transitions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TransitionResult:
    """Result of validating a transition."""

    valid: bool
    transition_id: str | None = None
    from_state: str | None = None
    to_state: str | None = None
    plan_gate_required: bool = False
    decision_boundary: bool = False
    stop_reason: str | None = None
    reason: str = ""
    # When valid=False and transition is validated_to_sandbox, refusal ledger row id if persisted.
    ledger_row_id: str | None = None

    def __bool__(self) -> bool:
        return self.valid


def _default_matrix_path() -> Path:
    """Path to transition_matrix.v0.1.json relative to this module."""
    return Path(__file__).parent / "schemas" / "transition_matrix.v0.1.json"


class TransitionValidator:
    """
    Validates transitions against the transition matrix.

    Loads transition_matrix.v0.1.json and refuses any transition not in the matrix.
    """

    def __init__(self, matrix_path: Path | str | None = None):
        """
        Initialize validator.

        Args:
            matrix_path: Path to transition_matrix.v0.1.json. If None, use default.
        """
        path = Path(matrix_path) if matrix_path else _default_matrix_path()
        data = json.loads(path.read_text(encoding="utf-8"))
        self.terminal_states = set(data["terminal_states"])
        self._transitions: dict[tuple[str, str], dict[str, Any]] = {}
        self._by_id: dict[tuple[str, str], dict[str, Any]] = {}
        for t in data["transitions"]:
            from_s = t["from_state"]
            for to_s in t["to_states"]:
                self._transitions[(from_s, to_s)] = t
            self._by_id[(from_s, t["transition_id"])] = t

    def validate(self, from_state: str, to_state: str) -> TransitionResult:
        """
        Validate a transition. Returns TransitionResult with valid=True iff allowed.

        Does not evaluate guards; caller must ensure guard conditions hold before
        attempting the transition.
        """
        key = (from_state, to_state)
        if key not in self._transitions:
            return TransitionResult(
                valid=False,
                from_state=from_state,
                to_state=to_state,
                reason=f"Invalid transition: {from_state} -> {to_state} not in matrix",
            )
        if from_state == to_state:
            # No-op transitions are rejected unless explicitly defined in matrix.
            # Since key exists, it *is* explicitly defined; allow it.
            pass
        t = self._transitions[key]
        return TransitionResult(
            valid=True,
            transition_id=t["transition_id"],
            from_state=from_state,
            to_state=to_state,
            plan_gate_required=t.get("plan_gate_required", False),
            decision_boundary=t.get("decision_boundary", False),
            reason="",
        )

    def resolve_by_transition_id(
        self,
        from_state: str,
        transition_id: str,
        *,
        to_state: str | None = None,
    ) -> TransitionResult:
        """
        Resolve a transition by transition_id (optionally with explicit to_state).

        If a transition_id has multiple to_states, caller must provide to_state.
        """
        key = (from_state, transition_id)
        if key not in self._by_id:
            return TransitionResult(
                valid=False,
                transition_id=transition_id,
                from_state=from_state,
                to_state=to_state,
                reason=f"Unknown transition_id from {from_state}: {transition_id}",
            )
        t = self._by_id[key]
        to_states = list(t.get("to_states", []))
        if not to_states:
            return TransitionResult(
                valid=False,
                transition_id=transition_id,
                from_state=from_state,
                reason=f"Transition has no to_states: {transition_id}",
            )
        if to_state is None:
            if len(to_states) != 1:
                return TransitionResult(
                    valid=False,
                    transition_id=transition_id,
                    from_state=from_state,
                    reason=f"Ambiguous transition_id {transition_id}; explicit to_state required",
                )
            to_state = to_states[0]
        if to_state not in to_states:
            return TransitionResult(
                valid=False,
                transition_id=transition_id,
                from_state=from_state,
                to_state=to_state,
                reason=f"to_state not allowed for transition_id {transition_id}: {to_state}",
            )
        return self.validate(from_state, to_state)

    def guards_satisfied(self, transition_id: str, from_state: str, guard_inputs: dict[str, Any]) -> tuple[bool, str]:
        """
        Evaluate guard conditions for a transition.

        Matrix guard semantics:
        - expected == True/False: input must be exactly True/False
        - expected is string/number: input must equal expected
        - expected is list: input must be in list
        Missing guard input fails closed.
        """
        key = (from_state, transition_id)
        if key not in self._by_id:
            return False, f"Unknown transition_id from {from_state}: {transition_id}"
        t = self._by_id[key]
        expected_guards: dict[str, Any] = t.get("guards", {}) or {}
        for guard_key, expected in expected_guards.items():
            if guard_key not in guard_inputs:
                return False, f"Missing guard input: {guard_key}"
            actual = guard_inputs[guard_key]
            if isinstance(expected, list):
                if actual not in expected:
                    return False, f"Guard failed: {guard_key}={actual} not in {expected}"
            elif expected is True or expected is False:
                if actual is not expected:
                    return False, f"Guard failed: {guard_key}={actual} expected {expected}"
            else:
                if actual != expected:
                    return False, f"Guard failed: {guard_key}={actual} expected {expected}"
        return True, ""

    def is_terminal(self, state: str) -> bool:
        """Check if state is terminal (non-escaping)."""
        return state in self.terminal_states

    def allowed_to_states(self, from_state: str) -> list[str]:
        """Return list of states reachable from from_state."""
        return [to_s for (f, to_s) in self._transitions if f == from_state]

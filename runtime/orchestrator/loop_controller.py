"""
Loop Controller — M3.1 orchestration substrate.

Deterministic transition executor that obeys transition_matrix.v0.1.json.
No model calls. No sandbox. Just state load, validate, apply, persist, journal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from runtime.state.store import TaskState, TaskStateStore
from runtime.state.transitions import TransitionResult, TransitionValidator


@dataclass
class TransitionJournalEntry:
    """Record of an applied transition for audit/replay."""

    task_id: str
    transition_id: str
    from_state: str
    to_state: str
    timestamp_utc: str
    plan_gate_required: bool
    decision_boundary: bool


class LoopController:
    """
    Deterministic loop executor.

    - Load current state
    - Validate transition against transition_matrix.v0.1.json
    - Apply transition
    - Persist state
    - Emit transition journal entry
    - Refuse invalid transitions
    """

    def __init__(
        self,
        store: TaskStateStore | None = None,
        validator: TransitionValidator | None = None,
        journal_callback: Callable[[TransitionJournalEntry], None] | None = None,
    ):
        """
        Initialize loop controller.

        Args:
            store: Task state store. If None, create in-memory store.
            validator: Transition validator. If None, load default matrix.
            journal_callback: Optional callback for each applied transition.
        """
        self.store = store or TaskStateStore()
        self.validator = validator or TransitionValidator()
        self.journal_callback = journal_callback
        self._journal: list[TransitionJournalEntry] = []
        self.max_consecutive_same_transition_id = 5
        # NOTE (scaffold): repetition guard is intentionally coarse (transition_id only).
        # Later revisions may need state-aware or phase-aware repetition logic to avoid
        # blocking legitimate repeated transitions in distinct contexts.

    def create_task(
        self,
        task_id: str,
        metadata: dict[str, Any] | None = None,
        *,
        max_iterations: int = 10,
    ) -> TaskState:
        """Create a new task in TASK_RECEIVED state."""
        return self.store.create(task_id, metadata, max_iterations=max_iterations)

    def apply_transition(
        self,
        task_id: str,
        *,
        transition_id: str,
        to_state: str | None = None,
        guard_inputs: dict[str, Any] | None = None,
    ) -> TransitionResult:
        """
        Execute a transition by transition_id from the current state.

        Returns TransitionResult. If valid, applies transition, persists,
        and emits journal entry. If invalid, refuses and returns result with valid=False.
        """
        state = self.store.load(task_id)
        if not state:
            return TransitionResult(
                valid=False,
                transition_id=transition_id,
                to_state=to_state,
                reason=f"Task not found: {task_id}",
            )

        from_state = state.current_state

        if self.validator.is_terminal(from_state):
            return TransitionResult(
                valid=False,
                transition_id=transition_id,
                from_state=from_state,
                to_state=to_state,
                reason=f"Cannot transition from terminal state: {from_state}",
            )

        guard_inputs = guard_inputs or {}

        # Resolve transition (supports transition_id-based execution).
        resolved = self.validator.resolve_by_transition_id(from_state, transition_id, to_state=to_state)
        if not resolved.valid:
            return resolved

        # Reject no-op transitions unless explicitly defined in matrix.
        if resolved.from_state == resolved.to_state:
            # resolve_by_transition_id() delegates to validate(), so this is explicitly defined.
            # Still refuse if caller attempted a no-op via implicit to_state mismatch.
            pass

        # Evaluate guards from matrix (fail-closed).
        ok, guard_reason = self.validator.guards_satisfied(transition_id, from_state, guard_inputs)
        if not ok:
            return TransitionResult(
                valid=False,
                transition_id=transition_id,
                from_state=from_state,
                to_state=resolved.to_state,
                stop_reason="validation_failed",
                reason=guard_reason,
            )

        # Loop safety guard: retry iteration cap.
        # NOTE (scaffold): iteration budget currently applies to retry-path transitions only.
        is_retry = transition_id == "review_to_proposal"
        if is_retry and state.loop_iteration >= state.max_iterations:
            return TransitionResult(
                valid=False,
                transition_id=transition_id,
                from_state=from_state,
                to_state=resolved.to_state,
                stop_reason="iteration_limit",
                reason=f"Iteration limit reached: {state.loop_iteration} >= {state.max_iterations}",
            )

        # Loop safety guard: excessive repetition of same transition_id.
        if state.last_transition_id == transition_id:
            if state.consecutive_same_transition_id + 1 > self.max_consecutive_same_transition_id:
                return TransitionResult(
                    valid=False,
                    transition_id=transition_id,
                    from_state=from_state,
                    to_state=resolved.to_state,
                    stop_reason="iteration_limit",
                    reason=(
                        "Excessive consecutive repetition of transition_id "
                        f"{transition_id} (limit {self.max_consecutive_same_transition_id})"
                    ),
                )

        # NOTE (scaffold): when a loop guard blocks progression (iteration_limit, repetition),
        # we return an explicit stop_reason but do not force a terminal state transition yet.
        # Later orchestration may convert these into explicit runtime-owned terminal transitions
        # (e.g., REVIEW_DECIDED -> BLOCKED with stop_reason=iteration_limit) when such transitions
        # are added to the transition matrix.

        to_state_final = resolved.to_state or ""

        # Apply transition.
        state.current_state = to_state_final

        # Update loop counters (retry increments).
        if is_retry:
            state.loop_iteration += 1

        # Update repetition tracking.
        if state.last_transition_id == transition_id:
            state.consecutive_same_transition_id += 1
        else:
            state.last_transition_id = transition_id
            state.consecutive_same_transition_id = 1

        timestamp = datetime.now(timezone.utc).isoformat()
        state.transition_journal.append(
            {
                "transition_id": transition_id,
                "from_state": from_state,
                "to_state": to_state_final,
                "timestamp_utc": timestamp,
            }
        )
        self.store.save(state)

        entry = TransitionJournalEntry(
            task_id=task_id,
            transition_id=transition_id,
            from_state=from_state,
            to_state=to_state_final,
            timestamp_utc=timestamp,
            plan_gate_required=resolved.plan_gate_required,
            decision_boundary=resolved.decision_boundary,
        )
        self._journal.append(entry)
        if self.journal_callback:
            self.journal_callback(entry)

        return resolved

    def get_journal(self) -> list[TransitionJournalEntry]:
        """Return journal of applied transitions for this controller instance."""
        return list(self._journal)

"""
Tests for M3.1 transition executor.

Valid transitions succeed; invalid transitions refused.
Deterministic loop controller obeys transition_matrix.v0.1.json.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.state.store import TaskStateStore
from runtime.state.transitions import TransitionValidator
from runtime.orchestrator.loop_controller import LoopController


class TestTransitionValidator(unittest.TestCase):
    """Unit tests for TransitionValidator."""

    def setUp(self) -> None:
        self.validator = TransitionValidator()

    def test_valid_transition_task_to_plan_eval(self) -> None:
        result = self.validator.validate("TASK_RECEIVED", "PLAN_EVALUATED")
        self.assertTrue(result.valid)
        self.assertEqual(result.transition_id, "task_to_plan_eval")

    def test_valid_transition_plan_eval_to_governance(self) -> None:
        result = self.validator.validate("PLAN_EVALUATED", "GOVERNANCE_CLASSIFIED")
        self.assertTrue(result.valid)
        self.assertTrue(result.plan_gate_required)
        self.assertTrue(result.decision_boundary)

    def test_valid_transition_governance_to_completed(self) -> None:
        result = self.validator.validate("GOVERNANCE_CLASSIFIED", "COMPLETED")
        self.assertTrue(result.valid)
        self.assertEqual(result.transition_id, "governance_to_completed")
        # No duplicate ledger semantics: governance_to_completed is not a decision boundary.
        self.assertFalse(result.decision_boundary)

    def test_valid_transition_governance_to_context(self) -> None:
        result = self.validator.validate("GOVERNANCE_CLASSIFIED", "CONTEXT_FETCHED")
        self.assertTrue(result.valid)
        self.assertFalse(result.decision_boundary)

    def test_invalid_transition_rejected(self) -> None:
        result = self.validator.validate("TASK_RECEIVED", "COMPLETED")
        self.assertFalse(result.valid)
        self.assertIn("Invalid transition", result.reason)

    def test_invalid_transition_skip_state_rejected(self) -> None:
        result = self.validator.validate("TASK_RECEIVED", "GOVERNANCE_CLASSIFIED")
        self.assertFalse(result.valid)

    def test_terminal_states(self) -> None:
        for s in ["COMPLETED", "BLOCKED", "FAILED", "ABORTED"]:
            self.assertTrue(self.validator.is_terminal(s))
        self.assertFalse(self.validator.is_terminal("TASK_RECEIVED"))

    def test_allowed_to_states(self) -> None:
        allowed = self.validator.allowed_to_states("TASK_RECEIVED")
        self.assertIn("PLAN_EVALUATED", allowed)
        self.assertIn("ABORTED", allowed)


class TestLoopController(unittest.TestCase):
    """Integration tests for LoopController."""

    def setUp(self) -> None:
        self.store = TaskStateStore()
        self.validator = TransitionValidator()
        self.controller = LoopController(store=self.store, validator=self.validator)

    def test_create_task(self) -> None:
        state = self.controller.create_task("task-001", max_iterations=2)
        self.assertEqual(state.current_state, "TASK_RECEIVED")
        self.assertEqual(state.task_id, "task-001")
        self.assertEqual(state.loop_iteration, 0)
        self.assertEqual(state.max_iterations, 2)

    def test_valid_transition_applied(self) -> None:
        self.controller.create_task("task-002")
        result = self.controller.apply_transition(
            "task-002",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )
        self.assertTrue(result.valid)
        state = self.store.load("task-002")
        self.assertIsNotNone(state)
        self.assertEqual(state.current_state, "PLAN_EVALUATED")

    def test_invalid_transition_refused(self) -> None:
        self.controller.create_task("task-003")
        # No-op / invalid: task_to_plan_eval does not allow COMPLETED.
        result = self.controller.apply_transition(
            "task-003",
            transition_id="task_to_plan_eval",
            to_state="COMPLETED",
            guard_inputs={"event_valid": True},
        )
        self.assertFalse(result.valid)
        state = self.store.load("task-003")
        self.assertEqual(state.current_state, "TASK_RECEIVED")

    def test_journal_emitted(self) -> None:
        self.controller.create_task("task-004")
        self.controller.apply_transition(
            "task-004",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )
        journal = self.controller.get_journal()
        self.assertEqual(len(journal), 1)
        self.assertEqual(journal[0].transition_id, "task_to_plan_eval")
        self.assertEqual(journal[0].from_state, "TASK_RECEIVED")
        self.assertEqual(journal[0].to_state, "PLAN_EVALUATED")

    def test_transition_from_terminal_refused(self) -> None:
        self.controller.create_task("task-005")
        self.controller.apply_transition(
            "task-005",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )
        self.controller.apply_transition(
            "task-005",
            transition_id="plan_eval_to_governance",
        )
        self.controller.apply_transition(
            "task-005",
            transition_id="governance_to_completed",
            guard_inputs={"phase": "REF"},
        )
        result = self.controller.apply_transition(
            "task-005",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )
        self.assertFalse(result.valid)
        self.assertIn("terminal", result.reason)

    def test_missing_task_refused(self) -> None:
        result = self.controller.apply_transition(
            "nonexistent",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )
        self.assertFalse(result.valid)
        self.assertIn("not found", result.reason)

    def test_happy_path_governance_flow(self) -> None:
        self.controller.create_task("task-006")
        r1 = self.controller.apply_transition(
            "task-006",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )
        r2 = self.controller.apply_transition(
            "task-006",
            transition_id="plan_eval_to_governance",
        )
        r3 = self.controller.apply_transition(
            "task-006",
            transition_id="governance_to_completed",
            guard_inputs={"phase": "REF"},
        )
        self.assertTrue(r1.valid)
        self.assertTrue(r2.valid)
        self.assertTrue(r3.valid)
        state = self.store.load("task-006")
        self.assertEqual(state.current_state, "COMPLETED")
        self.assertEqual(len(state.transition_journal), 3)

    def test_retry_path_review_to_model_proposal_ready_works(self) -> None:
        self.controller.create_task("task-007", max_iterations=3)
        # Set up state for retry transition.
        state = self.store.load("task-007")
        assert state is not None
        state.current_state = "REVIEW_DECIDED"
        self.store.save(state)

        r = self.controller.apply_transition(
            "task-007",
            transition_id="review_to_proposal",
            guard_inputs={"retry": True},
        )
        self.assertTrue(r.valid)
        state2 = self.store.load("task-007")
        assert state2 is not None
        self.assertEqual(state2.current_state, "MODEL_PROPOSAL_READY")
        self.assertEqual(state2.loop_iteration, 1)

    def test_repeated_retry_hits_iteration_limit(self) -> None:
        self.controller.create_task("task-008", max_iterations=2)
        state = self.store.load("task-008")
        assert state is not None
        state.current_state = "REVIEW_DECIDED"
        self.store.save(state)

        r1 = self.controller.apply_transition(
            "task-008",
            transition_id="review_to_proposal",
            guard_inputs={"retry": True},
        )
        self.assertTrue(r1.valid)

        # Reset state to allow retry again (test harness setup).
        state = self.store.load("task-008")
        assert state is not None
        state.current_state = "REVIEW_DECIDED"
        self.store.save(state)

        r2 = self.controller.apply_transition(
            "task-008",
            transition_id="review_to_proposal",
            guard_inputs={"retry": True},
        )
        self.assertTrue(r2.valid)

        # Third retry should be blocked by iteration_limit.
        state = self.store.load("task-008")
        assert state is not None
        state.current_state = "REVIEW_DECIDED"
        self.store.save(state)

        r3 = self.controller.apply_transition(
            "task-008",
            transition_id="review_to_proposal",
            guard_inputs={"retry": True},
        )
        self.assertFalse(r3.valid)
        self.assertEqual(r3.stop_reason, "iteration_limit")

    def test_excessive_repeated_transition_id_rejected(self) -> None:
        self.controller.max_consecutive_same_transition_id = 2
        self.controller.create_task("task-009", max_iterations=10)
        state = self.store.load("task-009")
        assert state is not None
        state.current_state = "REVIEW_DECIDED"
        self.store.save(state)

        r1 = self.controller.apply_transition(
            "task-009",
            transition_id="review_to_proposal",
            guard_inputs={"retry": True},
        )
        self.assertTrue(r1.valid)

        # Reset to REVIEW_DECIDED and do it again (same transition_id).
        state = self.store.load("task-009")
        assert state is not None
        state.current_state = "REVIEW_DECIDED"
        self.store.save(state)

        r2 = self.controller.apply_transition(
            "task-009",
            transition_id="review_to_proposal",
            guard_inputs={"retry": True},
        )
        self.assertTrue(r2.valid)

        # Third consecutive should be rejected by repetition guard.
        state = self.store.load("task-009")
        assert state is not None
        state.current_state = "REVIEW_DECIDED"
        self.store.save(state)

        r3 = self.controller.apply_transition(
            "task-009",
            transition_id="review_to_proposal",
            guard_inputs={"retry": True},
        )
        self.assertFalse(r3.valid)
        self.assertEqual(r3.stop_reason, "iteration_limit")
        self.assertIn("repetition", r3.reason.lower())

    def test_no_op_transition_rejected(self) -> None:
        self.controller.create_task("task-010")
        # Attempt to force a no-op by explicitly setting to_state == from_state;
        # matrix does not define TASK_RECEIVED -> TASK_RECEIVED, so it must be rejected.
        r = self.controller.apply_transition(
            "task-010",
            transition_id="task_to_plan_eval",
            to_state="TASK_RECEIVED",
            guard_inputs={"event_valid": True},
        )
        self.assertFalse(r.valid)


class TestLoopControllerPersistence(unittest.TestCase):
    """Tests for state persistence."""

    def test_persist_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskStateStore(base_path=Path(tmp))
            controller = LoopController(store=store)
            controller.create_task("task-persist")
            controller.apply_transition(
                "task-persist",
                transition_id="task_to_plan_eval",
                guard_inputs={"event_valid": True},
            )
            store2 = TaskStateStore(base_path=Path(tmp))
            state = store2.load("task-persist")
            self.assertIsNotNone(state)
            self.assertEqual(state.current_state, "PLAN_EVALUATED")


if __name__ == "__main__":
    unittest.main()

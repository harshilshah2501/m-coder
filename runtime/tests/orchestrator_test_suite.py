"""
M3.1 Orchestrator Test Suite — Comprehensive tests for agent loop orchestrator.

Test categories:
1. Stop condition policy tests
2. Budget policy tests
3. Transition executor tests
4. Replay engine tests
5. Integration tests

Required tests per M3.1:
- transition success
- transition rejection
- iteration cap
- retry logic
- terminal state lock
- sandbox execution handoff
- deterministic replay via task state
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.state.store import TaskState, TaskStateStore, INITIAL_STATE
from runtime.state.transitions import TransitionValidator
from runtime.orchestrator.loop_controller import LoopController
from runtime.orchestrator.stop_conditions import (
    StopCondition,
    StopConditionPolicy,
    StopReason,
    StopReasonCategory,
    REASON_TO_TERMINAL,
    REASON_CATEGORIES,
)
from runtime.orchestrator.budget_policy import (
    BudgetPolicy,
    BudgetConfig,
    BudgetStatus,
    BudgetCheckResult,
    BudgetType,
)
from runtime.orchestrator.transition_executor import (
    TransitionExecutor,
    TransitionHandlerResult,
    ExecutionContext,
    ExecutionResult,
    create_default_executor,
)
from runtime.orchestrator.replay import (
    ReplayEngine,
    ReplayTrace,
    ReplayStep,
    generate_trace_example,
)


class TestStopConditionPolicy(unittest.TestCase):
    """Tests for StopConditionPolicy."""
    
    def setUp(self) -> None:
        self.policy = StopConditionPolicy()
    
    def test_no_stop_when_no_conditions_met(self) -> None:
        task_state = {
            "loop_iteration": 0,
            "max_iterations": 10,
            "consecutive_same_transition_id": 0,
        }
        result = self.policy.evaluate(task_state)
        self.assertFalse(result.should_stop)
    
    def test_user_abort_highest_priority(self) -> None:
        task_state = {"loop_iteration": 0}
        context = {"user_abort": True}
        result = self.policy.evaluate(task_state, context)
        self.assertTrue(result.should_stop)
        self.assertEqual(result.reason, StopReason.USER_ABORT)
        self.assertEqual(result.terminal_state, "ABORTED")
    
    def test_explicit_refusal_stops(self) -> None:
        task_state = {}
        context = {"explicit_refusal": True, "refusal_reason": "Test refusal"}
        result = self.policy.evaluate(task_state, context)
        self.assertTrue(result.should_stop)
        self.assertEqual(result.reason, StopReason.EXPLICIT_REFUSAL)
        self.assertEqual(result.terminal_state, "COMPLETED")
    
    def test_authority_fail_stops(self) -> None:
        task_state = {}
        context = {"authority_fail": True}
        result = self.policy.evaluate(task_state, context)
        self.assertTrue(result.should_stop)
        self.assertEqual(result.reason, StopReason.AUTHORITY_FAIL)
        self.assertEqual(result.terminal_state, "BLOCKED")
    
    def test_boundary_block_stops(self) -> None:
        task_state = {}
        context = {"boundary_block": True}
        result = self.policy.evaluate(task_state, context)
        self.assertTrue(result.should_stop)
        self.assertEqual(result.reason, StopReason.BOUNDARY_BLOCK)
    
    def test_iteration_limit_stops(self) -> None:
        task_state = {"loop_iteration": 10, "max_iterations": 10}
        result = self.policy.evaluate(task_state)
        self.assertTrue(result.should_stop)
        self.assertEqual(result.reason, StopReason.ITERATION_LIMIT)
        self.assertEqual(result.terminal_state, "BLOCKED")
    
    def test_excessive_repetition_stops(self) -> None:
        self.policy.max_consecutive_same_transition = 3
        task_state = {"consecutive_same_transition_id": 4}
        result = self.policy.evaluate(task_state)
        self.assertTrue(result.should_stop)
        self.assertEqual(result.reason, StopReason.ITERATION_LIMIT)
    
    def test_validation_failed_stops(self) -> None:
        task_state = {}
        context = {"validation_failed": True}
        result = self.policy.evaluate(task_state, context)
        self.assertTrue(result.should_stop)
        self.assertEqual(result.reason, StopReason.VALIDATION_FAILED)
    
    def test_sandbox_error_stops(self) -> None:
        task_state = {}
        context = {"sandbox_error": True}
        result = self.policy.evaluate(task_state, context)
        self.assertTrue(result.should_stop)
        self.assertEqual(result.reason, StopReason.SANDBOX_ERROR)
        self.assertEqual(result.terminal_state, "FAILED")
    
    def test_test_failure_stops(self) -> None:
        task_state = {}
        context = {"test_failure": True}
        result = self.policy.evaluate(task_state, context)
        self.assertTrue(result.should_stop)
        self.assertEqual(result.reason, StopReason.TEST_FAILURE)
        self.assertEqual(result.terminal_state, "FAILED")
    
    def test_should_force_terminal_when_stop_needed(self) -> None:
        stop = StopCondition.stop(StopReason.AUTHORITY_FAIL)
        should_force, target = self.policy.should_force_terminal("GOVERNANCE_CLASSIFIED", stop)
        self.assertTrue(should_force)
        self.assertEqual(target, "BLOCKED")
    
    def test_should_not_force_when_already_terminal(self) -> None:
        stop = StopCondition.stop(StopReason.AUTHORITY_FAIL)
        should_force, _ = self.policy.should_force_terminal("COMPLETED", stop)
        self.assertFalse(should_force)
    
    def test_all_stop_reasons_have_category(self) -> None:
        for reason in StopReason:
            self.assertIn(reason, REASON_CATEGORIES)
    
    def test_all_stop_reasons_have_terminal_state(self) -> None:
        for reason in StopReason:
            self.assertIn(reason, REASON_TO_TERMINAL)


class TestBudgetPolicy(unittest.TestCase):
    """Tests for BudgetPolicy."""
    
    def setUp(self) -> None:
        self.config = BudgetConfig(
            max_iterations=5,
            max_consecutive_same_transition=3,
        )
        self.policy = BudgetPolicy(self.config)
    
    def test_can_continue_when_under_limits(self) -> None:
        task_state = {
            "loop_iteration": 2,
            "max_iterations": 5,
            "consecutive_same_transition_id": 1,
        }
        result = self.policy.check_budgets(task_state)
        self.assertTrue(result.can_continue)
        self.assertEqual(len(result.exhausted_budgets), 0)
    
    def test_blocked_when_iteration_exhausted(self) -> None:
        task_state = {
            "loop_iteration": 5,
            "max_iterations": 5,
            "consecutive_same_transition_id": 0,
        }
        result = self.policy.check_budgets(task_state)
        self.assertFalse(result.can_continue)
        self.assertEqual(len(result.exhausted_budgets), 1)
        self.assertEqual(result.exhausted_budgets[0].budget_type, BudgetType.ITERATION)
    
    def test_blocked_when_repetition_exhausted(self) -> None:
        task_state = {
            "loop_iteration": 0,
            "consecutive_same_transition_id": 4,
        }
        result = self.policy.check_budgets(task_state)
        self.assertFalse(result.can_continue)
        self.assertEqual(len(result.exhausted_budgets), 1)
        self.assertEqual(result.exhausted_budgets[0].budget_type, BudgetType.REPETITION)
    
    def test_warning_threshold_detected(self) -> None:
        task_state = {
            "loop_iteration": 4,
            "max_iterations": 5,
            "consecutive_same_transition_id": 0,
        }
        result = self.policy.check_budgets(task_state)
        self.assertTrue(result.can_continue)
        self.assertGreater(len(result.warning_budgets), 0)
    
    def test_consume_iteration_increments(self) -> None:
        task_state = {"loop_iteration": 2}
        updated = self.policy.consume_iteration(task_state)
        self.assertEqual(updated["loop_iteration"], 3)
    
    def test_update_repetition_tracking_same_transition(self) -> None:
        task_state = {
            "last_transition_id": "test_transition",
            "consecutive_same_transition_id": 2,
        }
        updated = self.policy.update_repetition_tracking(task_state, "test_transition")
        self.assertEqual(updated["consecutive_same_transition_id"], 3)
    
    def test_update_repetition_tracking_different_transition(self) -> None:
        task_state = {
            "last_transition_id": "old_transition",
            "consecutive_same_transition_id": 5,
        }
        updated = self.policy.update_repetition_tracking(task_state, "new_transition")
        self.assertEqual(updated["last_transition_id"], "new_transition")
        self.assertEqual(updated["consecutive_same_transition_id"], 1)
    
    def test_budget_status_utilization(self) -> None:
        status = BudgetStatus(
            budget_type=BudgetType.ITERATION,
            limit=10,
            consumed=5,
            remaining=5,
            exhausted=False,
        )
        self.assertEqual(status.utilization_pct, 50.0)
    
    def test_token_budget_checked_when_configured(self) -> None:
        config = BudgetConfig(max_tokens=1000)
        policy = BudgetPolicy(config)
        task_state = {"loop_iteration": 0}
        context = {"tokens_consumed": 1500}
        result = policy.check_budgets(task_state, context)
        self.assertFalse(result.can_continue)
        exhausted_types = [b.budget_type for b in result.exhausted_budgets]
        self.assertIn(BudgetType.TOKEN, exhausted_types)


class TestTransitionExecutor(unittest.TestCase):
    """Tests for TransitionExecutor."""
    
    def setUp(self) -> None:
        self.executor = create_default_executor()
    
    def _make_context(
        self,
        task_id: str = "test-task",
        from_state: str = "TASK_RECEIVED",
        to_state: str = "PLAN_EVALUATED",
        transition_id: str = "task_to_plan_eval",
        guard_inputs: dict[str, Any] | None = None,
        task_state: dict[str, Any] | None = None,
    ) -> ExecutionContext:
        return ExecutionContext(
            task_id=task_id,
            task_state=task_state or {"loop_iteration": 0, "max_iterations": 10},
            transition_id=transition_id,
            from_state=from_state,
            to_state=to_state,
            guard_inputs=guard_inputs or {"event_valid": True},
        )
    
    def test_valid_transition_succeeds(self) -> None:
        context = self._make_context()
        result = self.executor.execute(context)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.transition_result)
    
    def test_invalid_transition_rejected(self) -> None:
        context = self._make_context(
            from_state="TASK_RECEIVED",
            to_state="COMPLETED",  # Invalid direct transition
            transition_id="invalid",
        )
        result = self.executor.execute(context)
        self.assertFalse(result.success)
    
    def test_guard_failure_rejected(self) -> None:
        context = self._make_context(guard_inputs={"event_valid": False})
        result = self.executor.execute(context)
        self.assertFalse(result.success)
        self.assertIn("Guard failed", result.error)
    
    def test_budget_blocked_rejects(self) -> None:
        context = self._make_context(
            task_state={"loop_iteration": 100, "max_iterations": 10}
        )
        result = self.executor.execute(context)
        self.assertFalse(result.success)
        self.assertTrue(result.budget_blocked)
    
    def test_handler_registered_and_invoked(self) -> None:
        called = []
        
        def test_handler(
            task_id: str,
            from_state: str,
            to_state: str,
            guard_inputs: dict[str, Any],
            context: dict[str, Any],
        ) -> TransitionHandlerResult:
            called.append(task_id)
            return TransitionHandlerResult.ok({"test_key": "test_value"})
        
        self.executor.register_handler("task_to_plan_eval", test_handler)
        context = self._make_context()
        result = self.executor.execute(context)
        
        self.assertTrue(result.success)
        self.assertEqual(len(called), 1)
        self.assertIsNotNone(result.handler_result)
        self.assertIn("test_key", result.handler_result.metadata_updates)
    
    def test_pre_hook_can_abort(self) -> None:
        def abort_hook(ctx: ExecutionContext) -> ExecutionContext | None:
            return None  # Abort
        
        self.executor.register_pre_hook(abort_hook)
        context = self._make_context()
        result = self.executor.execute(context)
        
        self.assertFalse(result.success)
        self.assertIn("Pre-hook aborted", result.error)
    
    def test_post_hook_invoked(self) -> None:
        called = []
        
        def post_hook(ctx: ExecutionContext, result: ExecutionResult) -> None:
            called.append((ctx.task_id, result.success))
        
        self.executor.register_post_hook(post_hook)
        context = self._make_context()
        result = self.executor.execute(context)
        
        self.assertTrue(result.success)
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0], ("test-task", True))
    
    def test_is_terminal_checks_correctly(self) -> None:
        self.assertTrue(self.executor.is_terminal("COMPLETED"))
        self.assertTrue(self.executor.is_terminal("BLOCKED"))
        self.assertTrue(self.executor.is_terminal("FAILED"))
        self.assertTrue(self.executor.is_terminal("ABORTED"))
        self.assertFalse(self.executor.is_terminal("TASK_RECEIVED"))
    
    def test_get_allowed_transitions(self) -> None:
        allowed = self.executor.get_allowed_transitions("TASK_RECEIVED")
        self.assertIn("PLAN_EVALUATED", allowed)
        self.assertIn("ABORTED", allowed)


class TestReplayEngine(unittest.TestCase):
    """Tests for ReplayEngine."""
    
    def setUp(self) -> None:
        self.engine = ReplayEngine()
    
    def test_replay_happy_path(self) -> None:
        trace = generate_trace_example("test-001", "happy_path")
        self.assertTrue(trace.valid)
        self.assertEqual(trace.final_state, "COMPLETED")
        self.assertEqual(len(trace.steps), 9)
        self.assertEqual(len(trace.errors), 0)
    
    def test_replay_ref_refusal(self) -> None:
        trace = generate_trace_example("test-002", "ref_refusal")
        self.assertTrue(trace.valid)
        self.assertEqual(trace.final_state, "COMPLETED")
        self.assertEqual(len(trace.steps), 3)
    
    def test_replay_iteration_limit(self) -> None:
        trace = generate_trace_example("test-003", "iteration_limit")
        self.assertTrue(trace.valid)
        self.assertEqual(trace.final_state, "BLOCKED")
    
    def test_replay_detects_invalid_transition(self) -> None:
        task_state = TaskState(
            task_id="test-invalid",
            current_state="COMPLETED",
            created_at="2026-03-13T10:00:00Z",
            updated_at="2026-03-13T10:00:01Z",
            loop_iteration=0,
            max_iterations=10,
            transition_journal=[
                {
                    "transition_id": "invalid",
                    "from_state": "TASK_RECEIVED",
                    "to_state": "COMPLETED",  # Invalid direct transition
                    "timestamp_utc": "2026-03-13T10:00:00Z",
                }
            ],
        )
        trace = self.engine.replay(task_state)
        self.assertFalse(trace.valid)
        self.assertGreater(len(trace.errors), 0)
    
    def test_replay_detects_state_discontinuity(self) -> None:
        task_state = TaskState(
            task_id="test-discontinuity",
            current_state="GOVERNANCE_CLASSIFIED",
            created_at="2026-03-13T10:00:00Z",
            updated_at="2026-03-13T10:00:02Z",
            loop_iteration=0,
            max_iterations=10,
            transition_journal=[
                {
                    "transition_id": "task_to_plan_eval",
                    "from_state": "TASK_RECEIVED",
                    "to_state": "PLAN_EVALUATED",
                    "timestamp_utc": "2026-03-13T10:00:00Z",
                },
                {
                    "transition_id": "plan_eval_to_governance",
                    "from_state": "CONTEXT_FETCHED",  # Wrong! Should be PLAN_EVALUATED
                    "to_state": "GOVERNANCE_CLASSIFIED",
                    "timestamp_utc": "2026-03-13T10:00:01Z",
                },
            ],
        )
        trace = self.engine.replay(task_state)
        self.assertFalse(trace.valid)
        self.assertTrue(any("discontinuity" in err.lower() for err in trace.errors))
    
    def test_validate_journal_valid(self) -> None:
        journal = [
            {"from_state": "TASK_RECEIVED", "to_state": "PLAN_EVALUATED"},
            {"from_state": "PLAN_EVALUATED", "to_state": "GOVERNANCE_CLASSIFIED"},
        ]
        valid, errors = self.engine.validate_journal(journal, "GOVERNANCE_CLASSIFIED")
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_journal_invalid(self) -> None:
        journal = [
            {"from_state": "TASK_RECEIVED", "to_state": "COMPLETED"},  # Invalid
        ]
        valid, errors = self.engine.validate_journal(journal)
        self.assertFalse(valid)
        self.assertGreater(len(errors), 0)
    
    def test_trace_to_text(self) -> None:
        trace = generate_trace_example("test-text", "happy_path")
        text = trace.to_text()
        self.assertIn("Replay Trace", text)
        self.assertIn("test-text", text)
        self.assertIn("COMPLETED", text)
    
    def test_iterate_steps(self) -> None:
        task_state = TaskState(
            task_id="test-iter",
            current_state="GOVERNANCE_CLASSIFIED",
            created_at="2026-03-13T10:00:00Z",
            updated_at="2026-03-13T10:00:02Z",
            loop_iteration=0,
            max_iterations=10,
            transition_journal=[
                {
                    "transition_id": "task_to_plan_eval",
                    "from_state": "TASK_RECEIVED",
                    "to_state": "PLAN_EVALUATED",
                    "timestamp_utc": "2026-03-13T10:00:00Z",
                },
                {
                    "transition_id": "plan_eval_to_governance",
                    "from_state": "PLAN_EVALUATED",
                    "to_state": "GOVERNANCE_CLASSIFIED",
                    "timestamp_utc": "2026-03-13T10:00:01Z",
                },
            ],
        )
        steps = list(self.engine.iterate_steps(task_state))
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0][1], "TASK_RECEIVED")  # current state before step 0
        self.assertEqual(steps[1][1], "PLAN_EVALUATED")  # current state before step 1


class TestLoopControllerIntegration(unittest.TestCase):
    """Integration tests for LoopController with orchestrator components."""
    
    def setUp(self) -> None:
        self.store = TaskStateStore()
        self.controller = LoopController(store=self.store)
    
    def test_iteration_cap_enforced(self) -> None:
        """Test that iteration cap is enforced."""
        self.controller.create_task("cap-test", max_iterations=2)
        state = self.store.load("cap-test")
        state.current_state = "REVIEW_DECIDED"
        self.store.save(state)
        
        # First retry works
        r1 = self.controller.apply_transition(
            "cap-test",
            transition_id="review_to_proposal",
            guard_inputs={"retry": True},
        )
        self.assertTrue(r1.valid)
        
        # Reset and retry again
        state = self.store.load("cap-test")
        state.current_state = "REVIEW_DECIDED"
        self.store.save(state)
        
        r2 = self.controller.apply_transition(
            "cap-test",
            transition_id="review_to_proposal",
            guard_inputs={"retry": True},
        )
        self.assertTrue(r2.valid)
        
        # Third retry should be blocked
        state = self.store.load("cap-test")
        state.current_state = "REVIEW_DECIDED"
        self.store.save(state)
        
        r3 = self.controller.apply_transition(
            "cap-test",
            transition_id="review_to_proposal",
            guard_inputs={"retry": True},
        )
        self.assertFalse(r3.valid)
        self.assertEqual(r3.stop_reason, "iteration_limit")
    
    def test_terminal_state_non_escaping(self) -> None:
        """Test that terminal states cannot be escaped."""
        self.controller.create_task("terminal-test")
        state = self.store.load("terminal-test")
        state.current_state = "COMPLETED"
        self.store.save(state)
        
        result = self.controller.apply_transition(
            "terminal-test",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )
        self.assertFalse(result.valid)
        self.assertIn("terminal", result.reason.lower())
    
    def test_deterministic_replay_from_task_state(self) -> None:
        """Test that task state can be replayed deterministically."""
        self.controller.create_task("replay-test")
        
        # Execute a sequence of transitions
        self.controller.apply_transition(
            "replay-test",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )
        self.controller.apply_transition(
            "replay-test",
            transition_id="plan_eval_to_governance",
        )
        self.controller.apply_transition(
            "replay-test",
            transition_id="governance_to_completed",
            guard_inputs={"phase": "REF"},
        )
        
        # Load state and replay
        state = self.store.load("replay-test")
        engine = ReplayEngine()
        trace = engine.replay(state)
        
        # Verify replay is valid and deterministic
        self.assertTrue(trace.valid)
        self.assertEqual(trace.final_state, "COMPLETED")
        self.assertEqual(len(trace.steps), 3)
        self.assertEqual(len(trace.errors), 0)
    
    def test_sandbox_handoff_integration(self) -> None:
        """Test sandbox handoff path works."""
        from runtime.sandbox.sandbox_executor import SandboxExecutor
        from runtime.plangate.plangate_service import PlanGateService
        
        with tempfile.TemporaryDirectory() as tmp:
            controller = LoopController(
                sandbox_executor=SandboxExecutor(),
                plan_gate_service=PlanGateService(),
            )
            controller.create_task("sandbox-test")
            
            # Drive to PROPOSAL_VALIDATED
            state = controller.store.load("sandbox-test")
            state.current_state = "PROPOSAL_VALIDATED"
            controller.store.save(state)
            
            # Execute sandbox transition
            result = controller.apply_transition(
                "sandbox-test",
                transition_id="validated_to_sandbox",
                guard_inputs={"command": ["echo", "test"], "working_dir": tmp},
            )
            
            self.assertTrue(result.valid, result.reason)
            state = controller.store.load("sandbox-test")
            self.assertEqual(state.current_state, "SANDBOX_EXECUTED")
            self.assertTrue(state.metadata.get("last_sandbox_success"))
    
    def test_consecutive_repetition_guard(self) -> None:
        """Test consecutive repetition guard."""
        self.controller.max_consecutive_same_transition_id = 2
        self.controller.create_task("rep-test", max_iterations=10)
        
        for i in range(2):
            state = self.store.load("rep-test")
            state.current_state = "REVIEW_DECIDED"
            self.store.save(state)
            
            r = self.controller.apply_transition(
                "rep-test",
                transition_id="review_to_proposal",
                guard_inputs={"retry": True},
            )
            self.assertTrue(r.valid, f"Iteration {i} should succeed")
        
        # Third consecutive should fail
        state = self.store.load("rep-test")
        state.current_state = "REVIEW_DECIDED"
        self.store.save(state)
        
        r = self.controller.apply_transition(
            "rep-test",
            transition_id="review_to_proposal",
            guard_inputs={"retry": True},
        )
        self.assertFalse(r.valid)
        self.assertIn("repetition", r.reason.lower())


class TestOrchestratorPersistence(unittest.TestCase):
    """Tests for orchestrator state persistence."""
    
    def test_task_state_persisted_and_reloaded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskStateStore(base_path=Path(tmp))
            controller = LoopController(store=store)
            
            controller.create_task("persist-test")
            controller.apply_transition(
                "persist-test",
                transition_id="task_to_plan_eval",
                guard_inputs={"event_valid": True},
            )
            
            # Create new store pointing to same path
            store2 = TaskStateStore(base_path=Path(tmp))
            state = store2.load("persist-test")
            
            self.assertIsNotNone(state)
            self.assertEqual(state.current_state, "PLAN_EVALUATED")
            self.assertEqual(len(state.transition_journal), 1)
    
    def test_replay_from_persisted_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskStateStore(base_path=Path(tmp))
            controller = LoopController(store=store)
            
            controller.create_task("persist-replay")
            controller.apply_transition(
                "persist-replay",
                transition_id="task_to_plan_eval",
                guard_inputs={"event_valid": True},
            )
            controller.apply_transition(
                "persist-replay",
                transition_id="plan_eval_to_governance",
            )
            
            # Load from new store and replay
            store2 = TaskStateStore(base_path=Path(tmp))
            state = store2.load("persist-replay")
            
            engine = ReplayEngine()
            trace = engine.replay(state)
            
            self.assertTrue(trace.valid)
            self.assertEqual(trace.final_state, "GOVERNANCE_CLASSIFIED")


if __name__ == "__main__":
    unittest.main()

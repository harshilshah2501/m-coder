"""
Transition Executor — M3.1 orchestrator component.

Executes individual state transitions with pre/post hooks and handler dispatch.
Each transition_id maps to a handler that performs the transition-specific logic.

Design principles:
- The runtime owns all transitions; the model cannot trigger transitions directly.
- Each transition has explicit pre-conditions (guards) and post-conditions.
- Handlers may invoke external services (ContextEngine, PlanGate, Sandbox).
- All handler errors are fail-closed.

Transition execution flow:
1. Pre-validation (guards from transition matrix)
2. Pre-hooks (budget check, context preparation)
3. Handler dispatch (transition-specific logic)
4. Post-hooks (state update, ledger emission)
5. Journal emission
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from runtime.state.transitions import TransitionResult, TransitionValidator
from runtime.orchestrator.budget_policy import BudgetPolicy, BudgetCheckResult
from runtime.orchestrator.stop_conditions import (
    StopConditionPolicy,
    StopCondition,
    StopReason,
)


class TransitionHandler(Protocol):
    """Protocol for transition handlers."""
    
    def __call__(
        self,
        task_id: str,
        from_state: str,
        to_state: str,
        guard_inputs: dict[str, Any],
        context: dict[str, Any],
    ) -> TransitionHandlerResult:
        """
        Execute transition-specific logic.
        
        Args:
            task_id: Task identifier.
            from_state: Current state.
            to_state: Target state.
            guard_inputs: Guard condition inputs.
            context: Additional context (task metadata, etc.).
        
        Returns:
            TransitionHandlerResult indicating success/failure.
        """
        ...


@dataclass
class TransitionHandlerResult:
    """
    Result from a transition handler.
    
    Attributes:
        success: Whether the handler succeeded.
        error: Error message if failed.
        metadata_updates: Updates to apply to task metadata.
        stop_condition: If set, forces a stop condition.
    """
    
    success: bool
    error: str = ""
    metadata_updates: dict[str, Any] = field(default_factory=dict)
    stop_condition: StopCondition | None = None
    
    @classmethod
    def ok(cls, metadata_updates: dict[str, Any] | None = None) -> "TransitionHandlerResult":
        """Create a successful result."""
        return cls(success=True, metadata_updates=metadata_updates or {})
    
    @classmethod
    def fail(
        cls,
        error: str,
        stop_condition: StopCondition | None = None,
    ) -> "TransitionHandlerResult":
        """Create a failed result."""
        return cls(success=False, error=error, stop_condition=stop_condition)


@dataclass
class ExecutionContext:
    """
    Context passed through transition execution.
    
    Attributes:
        task_id: Task identifier.
        task_state: Current task state dict.
        transition_id: Transition being executed.
        from_state: Source state.
        to_state: Target state.
        guard_inputs: Guard condition inputs.
        timestamp: Execution timestamp.
        budget_result: Budget check result.
        stop_result: Stop condition evaluation.
    """
    
    task_id: str
    task_state: dict[str, Any]
    transition_id: str
    from_state: str
    to_state: str
    guard_inputs: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    budget_result: BudgetCheckResult | None = None
    stop_result: StopCondition | None = None


@dataclass
class ExecutionResult:
    """
    Full result of transition execution.
    
    Attributes:
        success: Whether the transition was applied.
        transition_result: The underlying TransitionResult.
        handler_result: Result from the handler (if invoked).
        budget_blocked: Whether blocked by budget.
        stop_forced: Whether a stop condition was forced.
        error: Error message if any.
    """
    
    success: bool
    transition_result: TransitionResult | None = None
    handler_result: TransitionHandlerResult | None = None
    budget_blocked: bool = False
    stop_forced: bool = False
    error: str = ""


class TransitionExecutor:
    """
    Executes transitions with full orchestrator context.
    
    Responsibilities:
    - Validate transitions against matrix
    - Check budgets before execution
    - Dispatch to transition handlers
    - Evaluate stop conditions
    - Emit journal entries
    
    Usage:
        executor = TransitionExecutor(validator, budget_policy, stop_policy)
        result = executor.execute(context)
    """
    
    def __init__(
        self,
        validator: TransitionValidator | None = None,
        budget_policy: BudgetPolicy | None = None,
        stop_policy: StopConditionPolicy | None = None,
    ):
        """
        Initialize transition executor.
        
        Args:
            validator: Transition validator (default: create new).
            budget_policy: Budget policy (default: create new).
            stop_policy: Stop condition policy (default: create new).
        """
        self.validator = validator or TransitionValidator()
        self.budget_policy = budget_policy or BudgetPolicy()
        self.stop_policy = stop_policy or StopConditionPolicy()
        self._handlers: dict[str, TransitionHandler] = {}
        self._pre_hooks: list[Callable[[ExecutionContext], ExecutionContext | None]] = []
        self._post_hooks: list[Callable[[ExecutionContext, ExecutionResult], None]] = []
    
    def register_handler(
        self,
        transition_id: str,
        handler: TransitionHandler,
    ) -> None:
        """
        Register a handler for a specific transition_id.
        
        Args:
            transition_id: The transition to handle.
            handler: The handler function.
        """
        self._handlers[transition_id] = handler
    
    def register_pre_hook(
        self,
        hook: Callable[[ExecutionContext], ExecutionContext | None],
    ) -> None:
        """
        Register a pre-execution hook.
        
        Hooks are called in registration order. If a hook returns None,
        execution is aborted.
        
        Args:
            hook: Pre-execution hook function.
        """
        self._pre_hooks.append(hook)
    
    def register_post_hook(
        self,
        hook: Callable[[ExecutionContext, ExecutionResult], None],
    ) -> None:
        """
        Register a post-execution hook.
        
        Args:
            hook: Post-execution hook function.
        """
        self._post_hooks.append(hook)
    
    def execute(
        self,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """
        Execute a transition with full orchestrator flow.
        
        Flow:
        1. Check budgets
        2. Evaluate stop conditions
        3. Validate transition against matrix
        4. Run pre-hooks
        5. Dispatch to handler (if registered)
        6. Run post-hooks
        
        Args:
            context: Execution context.
        
        Returns:
            ExecutionResult with full execution details.
        """
        # 1. Check budgets
        budget_result = self.budget_policy.check_budgets(
            context.task_state,
            context.guard_inputs,
        )
        context.budget_result = budget_result
        
        if not budget_result.can_continue:
            return ExecutionResult(
                success=False,
                budget_blocked=True,
                error=budget_result.block_reason,
            )
        
        # 2. Evaluate stop conditions
        stop_result = self.stop_policy.evaluate(
            context.task_state,
            context.guard_inputs,
        )
        context.stop_result = stop_result
        
        if stop_result.should_stop:
            return ExecutionResult(
                success=False,
                stop_forced=True,
                error=stop_result.message,
            )
        
        # 3. Validate transition
        transition_result = self.validator.resolve_by_transition_id(
            context.from_state,
            context.transition_id,
            to_state=context.to_state,
        )
        
        if not transition_result.valid:
            return ExecutionResult(
                success=False,
                transition_result=transition_result,
                error=transition_result.reason,
            )
        
        # 4. Check guards
        guards_ok, guard_reason = self.validator.guards_satisfied(
            context.transition_id,
            context.from_state,
            context.guard_inputs,
        )
        
        if not guards_ok:
            return ExecutionResult(
                success=False,
                transition_result=transition_result,
                error=guard_reason,
            )
        
        # 5. Run pre-hooks
        for hook in self._pre_hooks:
            result = hook(context)
            if result is None:
                return ExecutionResult(
                    success=False,
                    transition_result=transition_result,
                    error="Pre-hook aborted execution",
                )
            context = result
        
        # 6. Dispatch to handler
        handler_result: TransitionHandlerResult | None = None
        if context.transition_id in self._handlers:
            handler = self._handlers[context.transition_id]
            try:
                handler_result = handler(
                    context.task_id,
                    context.from_state,
                    context.to_state,
                    context.guard_inputs,
                    {"task_state": context.task_state},
                )
                
                if not handler_result.success:
                    return ExecutionResult(
                        success=False,
                        transition_result=transition_result,
                        handler_result=handler_result,
                        error=handler_result.error,
                    )
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    transition_result=transition_result,
                    error=f"Handler error: {e}",
                )
        
        # 7. Build successful result
        exec_result = ExecutionResult(
            success=True,
            transition_result=transition_result,
            handler_result=handler_result,
        )
        
        # 8. Run post-hooks
        for hook in self._post_hooks:
            try:
                hook(context, exec_result)
            except Exception:
                pass  # Post-hooks should not fail the transition
        
        return exec_result
    
    def is_terminal(self, state: str) -> bool:
        """Check if a state is terminal."""
        return self.validator.is_terminal(state)
    
    def get_allowed_transitions(self, from_state: str) -> list[str]:
        """Get list of states reachable from the given state."""
        return self.validator.allowed_to_states(from_state)


# Default handlers for common transitions

def default_task_to_plan_eval_handler(
    task_id: str,
    from_state: str,
    to_state: str,
    guard_inputs: dict[str, Any],
    context: dict[str, Any],
) -> TransitionHandlerResult:
    """Default handler for task_to_plan_eval transition."""
    if not guard_inputs.get("event_valid"):
        return TransitionHandlerResult.fail("Invalid event")
    return TransitionHandlerResult.ok()


def default_plan_eval_to_governance_handler(
    task_id: str,
    from_state: str,
    to_state: str,
    guard_inputs: dict[str, Any],
    context: dict[str, Any],
) -> TransitionHandlerResult:
    """Default handler for plan_eval_to_governance transition."""
    # This is a plan-gate checkpoint; actual evaluation happens in LoopController
    return TransitionHandlerResult.ok()


def default_governance_to_completed_handler(
    task_id: str,
    from_state: str,
    to_state: str,
    guard_inputs: dict[str, Any],
    context: dict[str, Any],
) -> TransitionHandlerResult:
    """Default handler for governance_to_completed (REF refusal) transition."""
    phase = guard_inputs.get("phase")
    if phase != "REF":
        return TransitionHandlerResult.fail(
            f"governance_to_completed requires phase=REF, got {phase}"
        )
    return TransitionHandlerResult.ok(
        metadata_updates={"terminal_posture": "refuse", "phase": "REF"}
    )


def default_review_to_proposal_handler(
    task_id: str,
    from_state: str,
    to_state: str,
    guard_inputs: dict[str, Any],
    context: dict[str, Any],
) -> TransitionHandlerResult:
    """Default handler for review_to_proposal (retry) transition."""
    if not guard_inputs.get("retry"):
        return TransitionHandlerResult.fail("Retry not requested")
    return TransitionHandlerResult.ok()


def create_default_executor() -> TransitionExecutor:
    """
    Create a TransitionExecutor with default handlers registered.
    
    Returns:
        Configured TransitionExecutor instance.
    """
    executor = TransitionExecutor()
    
    # Register default handlers
    executor.register_handler("task_to_plan_eval", default_task_to_plan_eval_handler)
    executor.register_handler("plan_eval_to_governance", default_plan_eval_to_governance_handler)
    executor.register_handler("governance_to_completed", default_governance_to_completed_handler)
    executor.register_handler("review_to_proposal", default_review_to_proposal_handler)
    
    return executor

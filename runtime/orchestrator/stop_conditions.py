"""
Stop Condition Policy — M3.1 orchestrator component.

Defines explicit stop conditions and terminal state forcing rules.
The runtime owns stop decisions; the model cannot bypass.

Stop condition types:
- governance: explicit_refusal, boundary_block, authority_fail
- loop: budget_exhausted, iteration_limit, validation_failed
- execution: sandbox_error, test_failure, timeout
- user: user_abort

Each condition maps to exactly one terminal state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class StopReasonCategory(Enum):
    """Category of stop reason."""
    
    GOVERNANCE = "governance"
    LOOP = "loop"
    EXECUTION = "execution"
    USER = "user"


class StopReason(Enum):
    """All defined stop reasons from state_enums.v0.1.json."""
    
    # Governance
    EXPLICIT_REFUSAL = "explicit_refusal"
    BOUNDARY_BLOCK = "boundary_block"
    AUTHORITY_FAIL = "authority_fail"
    BOUNDARY_CROSSED = "boundary_crossed"
    
    # Loop
    BUDGET_EXHAUSTED = "budget_exhausted"
    ITERATION_LIMIT = "iteration_limit"
    VALIDATION_FAILED = "validation_failed"
    
    # Execution
    SANDBOX_ERROR = "sandbox_error"
    TEST_FAILURE = "test_failure"
    TIMEOUT = "timeout"
    
    # User
    USER_ABORT = "user_abort"


# Map stop reasons to their category
REASON_CATEGORIES: dict[StopReason, StopReasonCategory] = {
    StopReason.EXPLICIT_REFUSAL: StopReasonCategory.GOVERNANCE,
    StopReason.BOUNDARY_BLOCK: StopReasonCategory.GOVERNANCE,
    StopReason.AUTHORITY_FAIL: StopReasonCategory.GOVERNANCE,
    StopReason.BOUNDARY_CROSSED: StopReasonCategory.GOVERNANCE,
    StopReason.BUDGET_EXHAUSTED: StopReasonCategory.LOOP,
    StopReason.ITERATION_LIMIT: StopReasonCategory.LOOP,
    StopReason.VALIDATION_FAILED: StopReasonCategory.LOOP,
    StopReason.SANDBOX_ERROR: StopReasonCategory.EXECUTION,
    StopReason.TEST_FAILURE: StopReasonCategory.EXECUTION,
    StopReason.TIMEOUT: StopReasonCategory.EXECUTION,
    StopReason.USER_ABORT: StopReasonCategory.USER,
}


# Map stop reasons to terminal states
REASON_TO_TERMINAL: dict[StopReason, str] = {
    StopReason.EXPLICIT_REFUSAL: "COMPLETED",  # REF refusal is a completed outcome
    StopReason.BOUNDARY_BLOCK: "BLOCKED",
    StopReason.AUTHORITY_FAIL: "BLOCKED",
    StopReason.BOUNDARY_CROSSED: "BLOCKED",
    StopReason.BUDGET_EXHAUSTED: "BLOCKED",
    StopReason.ITERATION_LIMIT: "BLOCKED",
    StopReason.VALIDATION_FAILED: "BLOCKED",
    StopReason.SANDBOX_ERROR: "FAILED",
    StopReason.TEST_FAILURE: "FAILED",
    StopReason.TIMEOUT: "FAILED",
    StopReason.USER_ABORT: "ABORTED",
}


@dataclass
class StopCondition:
    """
    A stop condition evaluation result.
    
    Attributes:
        should_stop: Whether the condition requires stopping.
        reason: The StopReason if should_stop is True.
        terminal_state: The target terminal state.
        message: Human-readable explanation.
        metadata: Additional context for debugging/audit.
    """
    
    should_stop: bool
    reason: StopReason | None = None
    terminal_state: str | None = None
    message: str = ""
    metadata: dict[str, Any] | None = None
    
    @classmethod
    def no_stop(cls) -> "StopCondition":
        """Create a non-stopping condition."""
        return cls(should_stop=False)
    
    @classmethod
    def stop(
        cls,
        reason: StopReason,
        message: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> "StopCondition":
        """Create a stopping condition with the appropriate terminal state."""
        return cls(
            should_stop=True,
            reason=reason,
            terminal_state=REASON_TO_TERMINAL[reason],
            message=message or reason.value,
            metadata=metadata,
        )


class StopConditionPolicy:
    """
    Stop condition evaluation policy.
    
    Evaluates task state and context to determine if a stop condition is met.
    All evaluations are fail-closed: ambiguity prefers stopping.
    
    Stop conditions are evaluated in priority order:
    1. User abort (highest priority)
    2. Governance conditions (authority, boundary)
    3. Loop conditions (budget, iteration)
    4. Execution conditions (sandbox, tests, timeout)
    """
    
    def __init__(
        self,
        max_iterations: int = 10,
        max_consecutive_same_transition: int = 5,
        default_timeout_seconds: int = 300,
    ):
        """
        Initialize policy with limits.
        
        Args:
            max_iterations: Maximum retry iterations.
            max_consecutive_same_transition: Maximum consecutive same transition_id.
            default_timeout_seconds: Default task timeout.
        """
        self.max_iterations = max_iterations
        self.max_consecutive_same_transition = max_consecutive_same_transition
        self.default_timeout_seconds = default_timeout_seconds
    
    def evaluate(
        self,
        task_state: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> StopCondition:
        """
        Evaluate all stop conditions against task state.
        
        Args:
            task_state: Current task state (from TaskState.to_dict()).
            context: Additional context (e.g., latest transition result).
        
        Returns:
            StopCondition indicating whether to stop and why.
        """
        context = context or {}
        
        # 1. User abort (highest priority)
        if context.get("user_abort"):
            return StopCondition.stop(
                StopReason.USER_ABORT,
                "User requested abort",
            )
        
        # 2. Governance conditions
        governance_stop = self._check_governance_conditions(task_state, context)
        if governance_stop.should_stop:
            return governance_stop
        
        # 3. Loop conditions
        loop_stop = self._check_loop_conditions(task_state, context)
        if loop_stop.should_stop:
            return loop_stop
        
        # 4. Execution conditions
        exec_stop = self._check_execution_conditions(task_state, context)
        if exec_stop.should_stop:
            return exec_stop
        
        return StopCondition.no_stop()
    
    def _check_governance_conditions(
        self,
        task_state: dict[str, Any],
        context: dict[str, Any],
    ) -> StopCondition:
        """Check governance-related stop conditions."""
        # Explicit refusal
        if context.get("explicit_refusal"):
            return StopCondition.stop(
                StopReason.EXPLICIT_REFUSAL,
                context.get("refusal_reason", "Explicit refusal"),
            )
        
        # Authority failure
        if context.get("authority_fail"):
            return StopCondition.stop(
                StopReason.AUTHORITY_FAIL,
                context.get("authority_reason", "Authority check failed"),
            )
        
        # Boundary block
        if context.get("boundary_block"):
            return StopCondition.stop(
                StopReason.BOUNDARY_BLOCK,
                context.get("boundary_reason", "Boundary blocked"),
            )
        
        # Boundary crossed (fail-closed: this should never happen in shadow)
        if context.get("boundary_crossed"):
            return StopCondition.stop(
                StopReason.BOUNDARY_CROSSED,
                "Irreversible boundary crossed",
            )
        
        return StopCondition.no_stop()
    
    def _check_loop_conditions(
        self,
        task_state: dict[str, Any],
        context: dict[str, Any],
    ) -> StopCondition:
        """Check loop-related stop conditions."""
        # Budget exhausted
        if context.get("budget_exhausted"):
            return StopCondition.stop(
                StopReason.BUDGET_EXHAUSTED,
                "Token or cost budget exhausted",
            )
        
        # Iteration limit
        loop_iteration = task_state.get("loop_iteration", 0)
        max_iters = task_state.get("max_iterations", self.max_iterations)
        if loop_iteration >= max_iters:
            return StopCondition.stop(
                StopReason.ITERATION_LIMIT,
                f"Iteration limit reached: {loop_iteration} >= {max_iters}",
                metadata={"loop_iteration": loop_iteration, "max_iterations": max_iters},
            )
        
        # Excessive repetition
        consecutive = task_state.get("consecutive_same_transition_id", 0)
        if consecutive > self.max_consecutive_same_transition:
            return StopCondition.stop(
                StopReason.ITERATION_LIMIT,
                f"Excessive repetition: {consecutive} > {self.max_consecutive_same_transition}",
                metadata={"consecutive": consecutive, "limit": self.max_consecutive_same_transition},
            )
        
        # Validation failed
        if context.get("validation_failed"):
            return StopCondition.stop(
                StopReason.VALIDATION_FAILED,
                context.get("validation_reason", "Validation failed"),
            )
        
        return StopCondition.no_stop()
    
    def _check_execution_conditions(
        self,
        task_state: dict[str, Any],
        context: dict[str, Any],
    ) -> StopCondition:
        """Check execution-related stop conditions."""
        # Sandbox error
        if context.get("sandbox_error"):
            return StopCondition.stop(
                StopReason.SANDBOX_ERROR,
                context.get("sandbox_error_reason", "Sandbox execution error"),
            )
        
        # Test failure
        if context.get("test_failure"):
            return StopCondition.stop(
                StopReason.TEST_FAILURE,
                context.get("test_failure_reason", "Tests failed"),
            )
        
        # Timeout
        if context.get("timeout"):
            return StopCondition.stop(
                StopReason.TIMEOUT,
                "Task timeout exceeded",
            )
        
        return StopCondition.no_stop()
    
    def should_force_terminal(
        self,
        current_state: str,
        stop_condition: StopCondition,
    ) -> tuple[bool, str | None]:
        """
        Determine if the runtime should force a terminal state transition.
        
        Args:
            current_state: Current task state.
            stop_condition: The evaluated stop condition.
        
        Returns:
            Tuple of (should_force, target_state).
        """
        if not stop_condition.should_stop:
            return False, None
        
        # If already terminal, no forcing needed
        terminal_states = {"COMPLETED", "BLOCKED", "FAILED", "ABORTED"}
        if current_state in terminal_states:
            return False, None
        
        return True, stop_condition.terminal_state

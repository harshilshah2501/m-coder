"""
Budget Policy — M3.1 orchestrator component.

Defines retry/iteration budget rules for the agent loop.
All budget decisions are runtime-owned; the model cannot exceed budgets.

Budget types:
- iteration: Maximum loop iterations (retry cycles)
- repetition: Maximum consecutive same-transition repeats
- token: Maximum tokens consumed (future)
- cost: Maximum cost incurred (future)
- time: Maximum elapsed time (future)

Each budget check is fail-closed: if budget status cannot be determined,
assume exhausted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class BudgetType(Enum):
    """Types of budgets the orchestrator can enforce."""
    
    ITERATION = "iteration"
    REPETITION = "repetition"
    TOKEN = "token"
    COST = "cost"
    TIME = "time"


@dataclass
class BudgetStatus:
    """
    Current budget consumption status.
    
    Attributes:
        budget_type: Type of budget.
        limit: Maximum allowed.
        consumed: Amount consumed.
        remaining: Amount remaining.
        exhausted: Whether budget is exhausted.
        warning_threshold_reached: Whether warning threshold is reached.
    """
    
    budget_type: BudgetType
    limit: int | float
    consumed: int | float
    remaining: int | float
    exhausted: bool
    warning_threshold_reached: bool = False
    
    @property
    def utilization_pct(self) -> float:
        """Return budget utilization as percentage."""
        if self.limit == 0:
            return 100.0 if self.consumed > 0 else 0.0
        return (self.consumed / self.limit) * 100.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "budget_type": self.budget_type.value,
            "limit": self.limit,
            "consumed": self.consumed,
            "remaining": self.remaining,
            "exhausted": self.exhausted,
            "warning_threshold_reached": self.warning_threshold_reached,
            "utilization_pct": round(self.utilization_pct, 2),
        }


@dataclass
class BudgetCheckResult:
    """
    Result of checking all budgets.
    
    Attributes:
        can_continue: Whether the task can continue.
        exhausted_budgets: List of exhausted budget statuses.
        warning_budgets: List of budgets at warning threshold.
        all_budgets: All budget statuses.
        block_reason: Human-readable reason if cannot continue.
    """
    
    can_continue: bool
    exhausted_budgets: list[BudgetStatus] = field(default_factory=list)
    warning_budgets: list[BudgetStatus] = field(default_factory=list)
    all_budgets: list[BudgetStatus] = field(default_factory=list)
    block_reason: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "can_continue": self.can_continue,
            "exhausted_budgets": [b.to_dict() for b in self.exhausted_budgets],
            "warning_budgets": [b.to_dict() for b in self.warning_budgets],
            "all_budgets": [b.to_dict() for b in self.all_budgets],
            "block_reason": self.block_reason,
        }


@dataclass
class BudgetConfig:
    """
    Budget configuration for a task.
    
    Attributes:
        max_iterations: Maximum retry iterations (default 10).
        max_consecutive_same_transition: Max consecutive same transition_id (default 5).
        max_tokens: Maximum tokens (future; default 0 = unlimited).
        max_cost_cents: Maximum cost in cents (future; default 0 = unlimited).
        max_elapsed_seconds: Maximum elapsed time (future; default 0 = unlimited).
        warning_threshold_pct: Threshold for warning (default 80%).
    """
    
    max_iterations: int = 10
    max_consecutive_same_transition: int = 5
    max_tokens: int = 0
    max_cost_cents: int = 0
    max_elapsed_seconds: int = 0
    warning_threshold_pct: float = 80.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "max_iterations": self.max_iterations,
            "max_consecutive_same_transition": self.max_consecutive_same_transition,
            "max_tokens": self.max_tokens,
            "max_cost_cents": self.max_cost_cents,
            "max_elapsed_seconds": self.max_elapsed_seconds,
            "warning_threshold_pct": self.warning_threshold_pct,
        }


class BudgetPolicy:
    """
    Budget enforcement policy for the agent loop.
    
    Checks budgets before each transition and determines if the task can continue.
    All checks are fail-closed: ambiguity blocks.
    
    Usage:
        policy = BudgetPolicy(config)
        result = policy.check_budgets(task_state)
        if not result.can_continue:
            # Force terminal state
    """
    
    def __init__(self, config: BudgetConfig | None = None):
        """
        Initialize budget policy.
        
        Args:
            config: Budget configuration (defaults to BudgetConfig()).
        """
        self.config = config or BudgetConfig()
    
    def check_budgets(
        self,
        task_state: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> BudgetCheckResult:
        """
        Check all budgets against current task state.
        
        Args:
            task_state: Current task state (from TaskState.to_dict()).
            context: Additional context (tokens consumed, etc.).
        
        Returns:
            BudgetCheckResult indicating whether task can continue.
        """
        context = context or {}
        all_budgets: list[BudgetStatus] = []
        exhausted: list[BudgetStatus] = []
        warnings: list[BudgetStatus] = []
        
        # Check iteration budget
        iteration_status = self._check_iteration_budget(task_state)
        all_budgets.append(iteration_status)
        if iteration_status.exhausted:
            exhausted.append(iteration_status)
        elif iteration_status.warning_threshold_reached:
            warnings.append(iteration_status)
        
        # Check repetition budget
        repetition_status = self._check_repetition_budget(task_state)
        all_budgets.append(repetition_status)
        if repetition_status.exhausted:
            exhausted.append(repetition_status)
        elif repetition_status.warning_threshold_reached:
            warnings.append(repetition_status)
        
        # Check token budget (if configured and provided)
        if self.config.max_tokens > 0 and "tokens_consumed" in context:
            token_status = self._check_token_budget(context)
            all_budgets.append(token_status)
            if token_status.exhausted:
                exhausted.append(token_status)
            elif token_status.warning_threshold_reached:
                warnings.append(token_status)
        
        # Check time budget (if configured)
        if self.config.max_elapsed_seconds > 0:
            time_status = self._check_time_budget(task_state, context)
            all_budgets.append(time_status)
            if time_status.exhausted:
                exhausted.append(time_status)
            elif time_status.warning_threshold_reached:
                warnings.append(time_status)
        
        # Build result
        if exhausted:
            reasons = [
                f"{b.budget_type.value}: {b.consumed}/{b.limit}"
                for b in exhausted
            ]
            return BudgetCheckResult(
                can_continue=False,
                exhausted_budgets=exhausted,
                warning_budgets=warnings,
                all_budgets=all_budgets,
                block_reason=f"Budget exhausted: {', '.join(reasons)}",
            )
        
        return BudgetCheckResult(
            can_continue=True,
            exhausted_budgets=[],
            warning_budgets=warnings,
            all_budgets=all_budgets,
        )
    
    def _check_iteration_budget(self, task_state: dict[str, Any]) -> BudgetStatus:
        """Check iteration budget."""
        consumed = task_state.get("loop_iteration", 0)
        limit = task_state.get("max_iterations", self.config.max_iterations)
        remaining = max(0, limit - consumed)
        exhausted = consumed >= limit
        warning = (consumed / limit * 100) >= self.config.warning_threshold_pct if limit > 0 else False
        
        return BudgetStatus(
            budget_type=BudgetType.ITERATION,
            limit=limit,
            consumed=consumed,
            remaining=remaining,
            exhausted=exhausted,
            warning_threshold_reached=warning and not exhausted,
        )
    
    def _check_repetition_budget(self, task_state: dict[str, Any]) -> BudgetStatus:
        """Check repetition budget."""
        consumed = task_state.get("consecutive_same_transition_id", 0)
        limit = self.config.max_consecutive_same_transition
        remaining = max(0, limit - consumed)
        exhausted = consumed > limit
        warning = (consumed / limit * 100) >= self.config.warning_threshold_pct if limit > 0 else False
        
        return BudgetStatus(
            budget_type=BudgetType.REPETITION,
            limit=limit,
            consumed=consumed,
            remaining=remaining,
            exhausted=exhausted,
            warning_threshold_reached=warning and not exhausted,
        )
    
    def _check_token_budget(self, context: dict[str, Any]) -> BudgetStatus:
        """Check token budget."""
        consumed = context.get("tokens_consumed", 0)
        limit = self.config.max_tokens
        remaining = max(0, limit - consumed)
        exhausted = consumed >= limit
        warning = (consumed / limit * 100) >= self.config.warning_threshold_pct if limit > 0 else False
        
        return BudgetStatus(
            budget_type=BudgetType.TOKEN,
            limit=limit,
            consumed=consumed,
            remaining=remaining,
            exhausted=exhausted,
            warning_threshold_reached=warning and not exhausted,
        )
    
    def _check_time_budget(
        self,
        task_state: dict[str, Any],
        context: dict[str, Any],
    ) -> BudgetStatus:
        """Check time budget."""
        limit = self.config.max_elapsed_seconds
        
        # Calculate elapsed time
        created_at_str = task_state.get("created_at", "")
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                consumed = int((now - created_at).total_seconds())
            except (ValueError, TypeError):
                # Fail-closed: assume exhausted if we can't parse
                consumed = limit
        else:
            # Override from context if provided
            consumed = context.get("elapsed_seconds", 0)
        
        remaining = max(0, limit - consumed)
        exhausted = consumed >= limit
        warning = (consumed / limit * 100) >= self.config.warning_threshold_pct if limit > 0 else False
        
        return BudgetStatus(
            budget_type=BudgetType.TIME,
            limit=limit,
            consumed=consumed,
            remaining=remaining,
            exhausted=exhausted,
            warning_threshold_reached=warning and not exhausted,
        )
    
    def consume_iteration(self, task_state: dict[str, Any]) -> dict[str, Any]:
        """
        Increment iteration counter and return updated state dict.
        
        This is a helper for the loop controller to update iteration counts.
        
        Args:
            task_state: Current task state dict.
        
        Returns:
            Updated task state dict with incremented loop_iteration.
        """
        task_state = dict(task_state)
        task_state["loop_iteration"] = task_state.get("loop_iteration", 0) + 1
        return task_state
    
    def update_repetition_tracking(
        self,
        task_state: dict[str, Any],
        transition_id: str,
    ) -> dict[str, Any]:
        """
        Update repetition tracking for a transition.
        
        Args:
            task_state: Current task state dict.
            transition_id: The transition being applied.
        
        Returns:
            Updated task state dict with updated repetition tracking.
        """
        task_state = dict(task_state)
        last_id = task_state.get("last_transition_id")
        
        if last_id == transition_id:
            task_state["consecutive_same_transition_id"] = (
                task_state.get("consecutive_same_transition_id", 0) + 1
            )
        else:
            task_state["last_transition_id"] = transition_id
            task_state["consecutive_same_transition_id"] = 1
        
        return task_state

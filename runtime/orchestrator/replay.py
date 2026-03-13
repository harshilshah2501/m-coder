"""
Replay Utilities — M3.1 orchestrator component.

Provides deterministic replay of task execution from task state history.
Replay is the foundation for audit, debugging, and observation (Layer-4).

Replay principles:
- Given task state + transition journal, replay should produce identical state.
- Replay does not re-execute handlers; it reconstructs state from journal.
- Replay can be validated against ledger rows for consistency.

Replay types:
- State replay: Reconstruct final state from initial state + journal
- Trace generation: Generate human-readable execution trace
- Validation: Validate journal against transition matrix
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator

from runtime.state.store import TaskState, INITIAL_STATE
from runtime.state.transitions import TransitionValidator


@dataclass
class ReplayStep:
    """
    A single step in a replay trace.
    
    Attributes:
        step_number: Zero-indexed step number.
        transition_id: The transition that was executed.
        from_state: State before transition.
        to_state: State after transition.
        timestamp: When the transition occurred.
        valid: Whether this transition is valid per matrix.
        validation_error: Error message if invalid.
    """
    
    step_number: int
    transition_id: str
    from_state: str
    to_state: str
    timestamp: str
    valid: bool
    validation_error: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_number": self.step_number,
            "transition_id": self.transition_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "timestamp": self.timestamp,
            "valid": self.valid,
            "validation_error": self.validation_error,
        }


@dataclass
class ReplayTrace:
    """
    Complete replay trace for a task.
    
    Attributes:
        task_id: Task identifier.
        initial_state: Starting state (usually TASK_RECEIVED).
        final_state: Ending state after replay.
        steps: List of replay steps.
        valid: Whether all transitions are valid.
        errors: List of validation errors.
        created_at: When the trace was generated.
    """
    
    task_id: str
    initial_state: str
    final_state: str
    steps: list[ReplayStep] = field(default_factory=list)
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "initial_state": self.initial_state,
            "final_state": self.final_state,
            "steps": [s.to_dict() for s in self.steps],
            "valid": self.valid,
            "errors": self.errors,
            "created_at": self.created_at,
            "step_count": len(self.steps),
        }
    
    def to_text(self) -> str:
        """Generate human-readable trace text."""
        lines = [
            f"=== Replay Trace: {self.task_id} ===",
            f"Initial state: {self.initial_state}",
            f"Final state: {self.final_state}",
            f"Steps: {len(self.steps)}",
            f"Valid: {self.valid}",
            "",
        ]
        
        for step in self.steps:
            status = "✓" if step.valid else "✗"
            lines.append(
                f"[{step.step_number}] {status} {step.transition_id}: "
                f"{step.from_state} → {step.to_state}"
            )
            if step.validation_error:
                lines.append(f"      Error: {step.validation_error}")
        
        if self.errors:
            lines.append("")
            lines.append("Errors:")
            for err in self.errors:
                lines.append(f"  - {err}")
        
        return "\n".join(lines)


class ReplayEngine:
    """
    Replay engine for task state reconstruction and validation.
    
    Usage:
        engine = ReplayEngine()
        trace = engine.replay(task_state)
        print(trace.to_text())
    """
    
    def __init__(self, validator: TransitionValidator | None = None):
        """
        Initialize replay engine.
        
        Args:
            validator: Transition validator (default: create new).
        """
        self.validator = validator or TransitionValidator()
    
    def replay(self, task_state: TaskState) -> ReplayTrace:
        """
        Replay a task's execution from its journal.
        
        Args:
            task_state: The task state containing transition_journal.
        
        Returns:
            ReplayTrace with validated steps.
        """
        journal = task_state.transition_journal
        trace = ReplayTrace(
            task_id=task_state.task_id,
            initial_state=INITIAL_STATE,
            final_state=task_state.current_state,
        )
        
        current_state = INITIAL_STATE
        
        for i, entry in enumerate(journal):
            transition_id = entry.get("transition_id", "")
            from_state = entry.get("from_state", "")
            to_state = entry.get("to_state", "")
            timestamp = entry.get("timestamp_utc", "")
            
            # Validate transition
            result = self.validator.validate(from_state, to_state)
            
            step = ReplayStep(
                step_number=i,
                transition_id=transition_id,
                from_state=from_state,
                to_state=to_state,
                timestamp=timestamp,
                valid=result.valid,
                validation_error=result.reason if not result.valid else "",
            )
            trace.steps.append(step)
            
            # Check state continuity
            if from_state != current_state:
                trace.valid = False
                trace.errors.append(
                    f"Step {i}: State discontinuity - expected {current_state}, "
                    f"got {from_state}"
                )
            
            if not result.valid:
                trace.valid = False
                trace.errors.append(
                    f"Step {i}: Invalid transition - {result.reason}"
                )
            
            current_state = to_state
        
        # Verify final state matches
        if current_state != task_state.current_state:
            trace.valid = False
            trace.errors.append(
                f"Final state mismatch: replayed {current_state}, "
                f"expected {task_state.current_state}"
            )
        
        trace.final_state = current_state
        return trace
    
    def replay_from_dict(self, task_state_dict: dict[str, Any]) -> ReplayTrace:
        """
        Replay from a task state dictionary.
        
        Args:
            task_state_dict: Task state as dictionary.
        
        Returns:
            ReplayTrace with validated steps.
        """
        task_state = TaskState.from_dict(task_state_dict)
        return self.replay(task_state)
    
    def iterate_steps(
        self,
        task_state: TaskState,
    ) -> Iterator[tuple[int, str, ReplayStep]]:
        """
        Iterate through replay steps with running state.
        
        Yields:
            Tuple of (step_number, current_state, step).
        """
        current_state = INITIAL_STATE
        
        for i, entry in enumerate(task_state.transition_journal):
            transition_id = entry.get("transition_id", "")
            from_state = entry.get("from_state", "")
            to_state = entry.get("to_state", "")
            timestamp = entry.get("timestamp_utc", "")
            
            result = self.validator.validate(from_state, to_state)
            
            step = ReplayStep(
                step_number=i,
                transition_id=transition_id,
                from_state=from_state,
                to_state=to_state,
                timestamp=timestamp,
                valid=result.valid,
                validation_error=result.reason if not result.valid else "",
            )
            
            yield (i, current_state, step)
            current_state = to_state
    
    def validate_journal(
        self,
        journal: list[dict[str, Any]],
        expected_final_state: str | None = None,
    ) -> tuple[bool, list[str]]:
        """
        Validate a transition journal without full replay.
        
        Args:
            journal: List of journal entries.
            expected_final_state: Expected final state (optional).
        
        Returns:
            Tuple of (is_valid, error_messages).
        """
        errors: list[str] = []
        current_state = INITIAL_STATE
        
        for i, entry in enumerate(journal):
            from_state = entry.get("from_state", "")
            to_state = entry.get("to_state", "")
            
            # Check continuity
            if from_state != current_state:
                errors.append(
                    f"Step {i}: State discontinuity - expected {current_state}, "
                    f"got {from_state}"
                )
            
            # Validate transition
            result = self.validator.validate(from_state, to_state)
            if not result.valid:
                errors.append(f"Step {i}: Invalid transition - {result.reason}")
            
            current_state = to_state
        
        # Check final state
        if expected_final_state and current_state != expected_final_state:
            errors.append(
                f"Final state mismatch: got {current_state}, "
                f"expected {expected_final_state}"
            )
        
        return len(errors) == 0, errors


def generate_trace_example(
    task_id: str = "example-task-001",
    scenario: str = "happy_path",
) -> ReplayTrace:
    """
    Generate an example replay trace for documentation/testing.
    
    Args:
        task_id: Task identifier.
        scenario: One of "happy_path", "ref_refusal", "iteration_limit".
    
    Returns:
        Example ReplayTrace.
    """
    engine = ReplayEngine()
    
    # Build example journal based on scenario
    if scenario == "happy_path":
        journal = [
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
            {
                "transition_id": "governance_to_context",
                "from_state": "GOVERNANCE_CLASSIFIED",
                "to_state": "CONTEXT_FETCHED",
                "timestamp_utc": "2026-03-13T10:00:02Z",
            },
            {
                "transition_id": "context_to_proposal",
                "from_state": "CONTEXT_FETCHED",
                "to_state": "MODEL_PROPOSAL_READY",
                "timestamp_utc": "2026-03-13T10:00:03Z",
            },
            {
                "transition_id": "proposal_to_validated",
                "from_state": "MODEL_PROPOSAL_READY",
                "to_state": "PROPOSAL_VALIDATED",
                "timestamp_utc": "2026-03-13T10:00:04Z",
            },
            {
                "transition_id": "validated_to_sandbox",
                "from_state": "PROPOSAL_VALIDATED",
                "to_state": "SANDBOX_EXECUTED",
                "timestamp_utc": "2026-03-13T10:00:05Z",
            },
            {
                "transition_id": "sandbox_to_tests",
                "from_state": "SANDBOX_EXECUTED",
                "to_state": "TESTS_EVALUATED",
                "timestamp_utc": "2026-03-13T10:00:06Z",
            },
            {
                "transition_id": "tests_to_review",
                "from_state": "TESTS_EVALUATED",
                "to_state": "REVIEW_DECIDED",
                "timestamp_utc": "2026-03-13T10:00:07Z",
            },
            {
                "transition_id": "review_to_completed",
                "from_state": "REVIEW_DECIDED",
                "to_state": "COMPLETED",
                "timestamp_utc": "2026-03-13T10:00:08Z",
            },
        ]
        final_state = "COMPLETED"
    
    elif scenario == "ref_refusal":
        journal = [
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
            {
                "transition_id": "governance_to_completed",
                "from_state": "GOVERNANCE_CLASSIFIED",
                "to_state": "COMPLETED",
                "timestamp_utc": "2026-03-13T10:00:02Z",
            },
        ]
        final_state = "COMPLETED"
    
    elif scenario == "iteration_limit":
        journal = [
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
            {
                "transition_id": "governance_to_context",
                "from_state": "GOVERNANCE_CLASSIFIED",
                "to_state": "CONTEXT_FETCHED",
                "timestamp_utc": "2026-03-13T10:00:02Z",
            },
            {
                "transition_id": "context_to_proposal",
                "from_state": "CONTEXT_FETCHED",
                "to_state": "MODEL_PROPOSAL_READY",
                "timestamp_utc": "2026-03-13T10:00:03Z",
            },
            {
                "transition_id": "proposal_to_blocked",
                "from_state": "MODEL_PROPOSAL_READY",
                "to_state": "BLOCKED",
                "timestamp_utc": "2026-03-13T10:00:04Z",
            },
        ]
        final_state = "BLOCKED"
    
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    
    # Create task state
    task_state = TaskState(
        task_id=task_id,
        current_state=final_state,
        created_at="2026-03-13T10:00:00Z",
        updated_at="2026-03-13T10:00:08Z",
        loop_iteration=0,
        max_iterations=10,
        transition_journal=journal,
    )
    
    return engine.replay(task_state)

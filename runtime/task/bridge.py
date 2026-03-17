"""
Task bridge — M3.17 Slice 3.

Provides minimal conversion bridge between existing TaskState and the approved Task contract.

Design:
- TaskState remains the runtime operational object for now
- Task is the approved contract model
- This bridge provides safe interoperability between them

Conversion requires explicit parameters for fields not present in TaskState:
- request_id (defaults to task_id if not in metadata)
- session_id (required, from metadata or explicit)
- source_surface (required, explicit)
- task_kind (defaults to "execution")
- repo_scope (from metadata or explicit)

Field mapping:
- task_id -> task_id
- current_state -> status.current_state
- created_at -> created_at_utc
- updated_at -> updated_at_utc
- metadata.request_id -> request_id (fallback to task_id)
- metadata.session_id -> session_id (required)
- metadata.repo_root/root_path -> repo_scope.root_path
- metadata.revision -> repo_scope.revision
- metadata.branch -> repo_scope.branch
- metadata.plan_hash -> governance_ref.plan_hash
- metadata.max_iterations -> constraints.max_iterations
- loop_iteration, max_iterations, transition_journal -> preserved in metadata extension
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from runtime.state.store import TaskState
from runtime.task.contracts import (
    Task,
    TaskConstraints,
    TaskGovernanceRef,
    TaskRepoScope,
    TaskStatus,
    TaskValidationError,
    TERMINAL_STATES,
)


class TaskBridgeError(Exception):
    """Raised when TaskState <-> Task conversion fails."""

    pass


def task_state_to_task(
    state: TaskState,
    *,
    source_surface: Literal["ide_execute", "ide_ask", "api_execute", "ingestion", "replay"],
    task_kind: Literal["execution", "ask", "ingestion", "evaluation"] = "execution",
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    repo_scope: Optional[TaskRepoScope] = None,
    stop_reason: Optional[str] = None,
    terminal_at_utc: Optional[str] = None,
    validate: bool = True,
) -> Task:
    """
    Convert TaskState to Task contract.

    Args:
        state: Existing TaskState from runtime
        source_surface: Required origin surface (not stored in TaskState)
        task_kind: Task classification (default: execution)
        session_id: Session ID (falls back to metadata.session_id)
        request_id: Request ID (falls back to metadata.request_id or task_id)
        repo_scope: Repository scope (falls back to metadata fields)
        stop_reason: Stop reason for terminal states (falls back to metadata)
        terminal_at_utc: Terminal timestamp (falls back to updated_at for terminal states)
        validate: If True, validate resulting Task against schema

    Raises:
        TaskBridgeError: If required fields cannot be resolved
        TaskValidationError: If validation is enabled and resulting Task is invalid

    Returns:
        Valid Task contract object
    """
    meta = state.metadata or {}

    resolved_request_id = request_id or meta.get("request_id") or state.task_id
    resolved_session_id = session_id or meta.get("session_id")

    if not resolved_session_id:
        raise TaskBridgeError(
            "session_id is required for Task contract but not found in TaskState metadata. "
            "Provide session_id explicitly."
        )

    if repo_scope is None:
        root_path = meta.get("root_path") or meta.get("repo_root")
        revision = meta.get("revision")
        if not root_path or not revision:
            raise TaskBridgeError(
                "repo_scope is required for Task contract. "
                "Provide repo_scope explicitly or ensure metadata contains root_path/repo_root and revision."
            )
        repo_scope = TaskRepoScope(
            root_path=root_path,
            revision=revision,
            branch=meta.get("branch"),
        )

    governance_ref = None
    plan_hash = meta.get("plan_hash")
    if plan_hash:
        governance_ref = TaskGovernanceRef(plan_hash=plan_hash)

    constraints = None
    if state.max_iterations:
        constraints = TaskConstraints(max_iterations=state.max_iterations)

    is_terminal = state.current_state in TERMINAL_STATES
    resolved_stop_reason = stop_reason or meta.get("stop_reason")
    resolved_terminal_at = terminal_at_utc

    if is_terminal:
        if not resolved_stop_reason:
            raise TaskBridgeError(
                f"stop_reason is required for terminal state {state.current_state}. "
                "Provide stop_reason explicitly or ensure metadata contains stop_reason."
            )
        if not resolved_terminal_at:
            resolved_terminal_at = state.updated_at

    status = TaskStatus(
        current_state=state.current_state,
        stop_reason=resolved_stop_reason,
        terminal_at_utc=resolved_terminal_at,
    )

    runtime_extension = {
        "loop_iteration": state.loop_iteration,
        "max_iterations": state.max_iterations,
        "last_transition_id": state.last_transition_id,
        "consecutive_same_transition_id": state.consecutive_same_transition_id,
    }
    if state.transition_journal:
        runtime_extension["transition_journal_len"] = len(state.transition_journal)

    task_metadata: Dict[str, Dict[str, Any]] = {
        "runtime_state": runtime_extension,
    }

    task = Task(
        schema_version="task.v0.1",
        task_id=state.task_id,
        task_kind=task_kind,
        request_id=resolved_request_id,
        session_id=resolved_session_id,
        source_surface=source_surface,
        repo_scope=repo_scope,
        status=status,
        created_at_utc=state.created_at,
        updated_at_utc=state.updated_at,
        governance_ref=governance_ref,
        constraints=constraints,
        metadata=task_metadata,
    )

    if validate:
        from runtime.task.contracts import validate_task_dict

        validate_task_dict(task.to_dict())

    return task


def task_to_task_state(
    task: Task,
    *,
    loop_iteration: int = 0,
    max_iterations: Optional[int] = None,
    last_transition_id: Optional[str] = None,
    consecutive_same_transition_id: int = 0,
    transition_journal: Optional[list] = None,
) -> TaskState:
    """
    Convert Task contract to TaskState.

    Args:
        task: Valid Task contract object
        loop_iteration: Current loop iteration (default: 0)
        max_iterations: Max iterations (falls back to task.constraints or 10)
        last_transition_id: Last transition ID
        consecutive_same_transition_id: Consecutive same transition count
        transition_journal: Transition journal entries

    Returns:
        TaskState compatible with runtime orchestration
    """
    resolved_max_iterations = max_iterations
    if resolved_max_iterations is None:
        if task.constraints and task.constraints.max_iterations:
            resolved_max_iterations = task.constraints.max_iterations
        else:
            resolved_max_iterations = 10

    metadata: Dict[str, Any] = {}

    if task.request_id != task.task_id:
        metadata["request_id"] = task.request_id
    metadata["session_id"] = task.session_id

    metadata["root_path"] = task.repo_scope.root_path
    metadata["repo_root"] = task.repo_scope.root_path
    metadata["revision"] = task.repo_scope.revision
    if task.repo_scope.branch:
        metadata["branch"] = task.repo_scope.branch

    if task.governance_ref and task.governance_ref.plan_hash:
        metadata["plan_hash"] = task.governance_ref.plan_hash

    if task.status.stop_reason:
        metadata["stop_reason"] = task.status.stop_reason

    if task.metadata:
        runtime_state = task.metadata.get("runtime_state", {})
        if runtime_state.get("loop_iteration") is not None:
            loop_iteration = runtime_state["loop_iteration"]
        if runtime_state.get("last_transition_id") is not None:
            last_transition_id = runtime_state["last_transition_id"]
        if runtime_state.get("consecutive_same_transition_id") is not None:
            consecutive_same_transition_id = runtime_state["consecutive_same_transition_id"]

    return TaskState(
        task_id=task.task_id,
        current_state=task.status.current_state,
        created_at=task.created_at_utc,
        updated_at=task.updated_at_utc,
        loop_iteration=loop_iteration,
        max_iterations=resolved_max_iterations,
        last_transition_id=last_transition_id,
        consecutive_same_transition_id=consecutive_same_transition_id,
        metadata=metadata,
        transition_journal=transition_journal or [],
    )

"""
Task contract module — M3.17.

Provides typed contract model for task.v0.1 schema and bridge to TaskState.
"""

from runtime.task.contracts import (
    Task,
    TaskAcceptanceCriteria,
    TaskConstraints,
    TaskGovernanceRef,
    TaskProvenance,
    TaskRepoScope,
    TaskStatus,
    TaskValidationError,
    validate_task_dict,
)
from runtime.task.bridge import (
    TaskBridgeError,
    task_state_to_task,
    task_to_task_state,
)

__all__ = [
    "Task",
    "TaskAcceptanceCriteria",
    "TaskConstraints",
    "TaskGovernanceRef",
    "TaskProvenance",
    "TaskRepoScope",
    "TaskStatus",
    "TaskValidationError",
    "validate_task_dict",
    "TaskBridgeError",
    "task_state_to_task",
    "task_to_task_state",
]

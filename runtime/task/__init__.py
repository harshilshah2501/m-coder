"""
Task contract module — M3.17.

Provides typed contract model for task.v0.1 schema.
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
]

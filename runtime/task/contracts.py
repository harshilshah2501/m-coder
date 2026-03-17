"""
Task contracts — M3.17 Task Schema.

Provides typed contract model aligned with task.v0.1.schema.json.

A task is a runtime-owned, bounded unit of work that flows through
the governed agent loop. Granularity: one task = one inbound request for v0.1.

Design constraints:
- task_id is runtime-owned identity (not required to be deterministic)
- governance_ref.expected_phase is a NON-AUTHORITATIVE HINT only
- acceptance_criteria is DESCRIPTIVE only (no executable harness logic)
- metadata is an extension surface only (namespaced, constrained)
- one task = one inbound request for v0.1 (no multi-task orchestration)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

try:
    import jsonschema

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "task.v0.1.schema.json"

TaskKind = Literal["execution", "ask", "ingestion", "evaluation"]
SourceSurface = Literal["ide_execute", "ide_ask", "api_execute", "ingestion", "replay"]
AgentState = Literal[
    "TASK_RECEIVED",
    "PLAN_EVALUATED",
    "GOVERNANCE_CLASSIFIED",
    "CONTEXT_FETCHED",
    "MODEL_PROPOSAL_READY",
    "PROPOSAL_VALIDATED",
    "SANDBOX_EXECUTED",
    "TESTS_EVALUATED",
    "REVIEW_DECIDED",
    "COMPLETED",
    "BLOCKED",
    "FAILED",
    "ABORTED",
]
StopReason = Literal[
    "explicit_refusal",
    "boundary_block",
    "authority_fail",
    "boundary_crossed",
    "budget_exhausted",
    "iteration_limit",
    "validation_failed",
    "sandbox_error",
    "test_failure",
    "user_abort",
    "timeout",
]
ConstitutionalPhase = Literal["REF", "CONF", "DES", "MIX", "CODE"]

TERMINAL_STATES = {"COMPLETED", "BLOCKED", "FAILED", "ABORTED"}


class TaskValidationError(Exception):
    """Raised when task validation fails."""

    pass


def _load_schema() -> dict:
    """Load task.v0.1 JSON schema from disk."""
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


_CACHED_SCHEMA: dict | None = None


def _get_schema() -> dict:
    """Return cached schema (loaded once)."""
    global _CACHED_SCHEMA
    if _CACHED_SCHEMA is None:
        _CACHED_SCHEMA = _load_schema()
    return _CACHED_SCHEMA


def validate_task_dict(data: dict) -> None:
    """
    Validate a task dict against task.v0.1 schema.

    Raises TaskValidationError if validation fails.
    Raises RuntimeError if jsonschema is not installed.
    """
    if not HAS_JSONSCHEMA:
        raise RuntimeError("jsonschema library is required for task validation")

    schema = _get_schema()
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(data))
    if errors:
        messages = [f"{e.json_path}: {e.message}" for e in errors]
        raise TaskValidationError(f"Task validation failed: {'; '.join(messages)}")


@dataclass
class TaskRepoScope:
    """Repository targeting for deterministic context linkage."""

    root_path: str
    revision: str
    branch: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "root_path": self.root_path,
            "revision": self.revision,
        }
        if self.branch is not None:
            d["branch"] = self.branch
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskRepoScope:
        return cls(
            root_path=data["root_path"],
            revision=data["revision"],
            branch=data.get("branch"),
        )


@dataclass
class TaskGovernanceRef:
    """
    Linkage to governance (plan).

    Does NOT duplicate plan body. expected_phase is a NON-AUTHORITATIVE HINT only.
    """

    plan_hash: Optional[str] = None
    expected_phase: Optional[ConstitutionalPhase] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.plan_hash is not None:
            d["plan_hash"] = self.plan_hash
        if self.expected_phase is not None:
            d["expected_phase"] = self.expected_phase
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskGovernanceRef:
        return cls(
            plan_hash=data.get("plan_hash"),
            expected_phase=data.get("expected_phase"),
        )


@dataclass
class TaskConstraints:
    """Execution limits for fail-closed loop safety."""

    max_iterations: Optional[int] = None
    budget_tokens: Optional[int] = None
    timeout_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.max_iterations is not None:
            d["max_iterations"] = self.max_iterations
        if self.budget_tokens is not None:
            d["budget_tokens"] = self.budget_tokens
        if self.timeout_seconds is not None:
            d["timeout_seconds"] = self.timeout_seconds
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskConstraints:
        return cls(
            max_iterations=data.get("max_iterations"),
            budget_tokens=data.get("budget_tokens"),
            timeout_seconds=data.get("timeout_seconds"),
        )


@dataclass
class TaskAcceptanceCriteria:
    """
    Evaluation anchor for M3.18.

    DESCRIPTIVE ONLY. Does NOT contain executable harness logic.
    """

    description: Optional[str] = None
    test_refs: List[str] = field(default_factory=list)
    success_signals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.description is not None:
            d["description"] = self.description
        if self.test_refs:
            d["test_refs"] = list(self.test_refs)
        if self.success_signals:
            d["success_signals"] = list(self.success_signals)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskAcceptanceCriteria:
        return cls(
            description=data.get("description"),
            test_refs=list(data.get("test_refs", [])),
            success_signals=list(data.get("success_signals", [])),
        )


@dataclass
class TaskStatus:
    """Runtime state machine position."""

    current_state: AgentState
    stop_reason: Optional[StopReason] = None
    terminal_at_utc: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"current_state": self.current_state}
        if self.stop_reason is not None:
            d["stop_reason"] = self.stop_reason
        if self.terminal_at_utc is not None:
            d["terminal_at_utc"] = self.terminal_at_utc
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskStatus:
        return cls(
            current_state=data["current_state"],
            stop_reason=data.get("stop_reason"),
            terminal_at_utc=data.get("terminal_at_utc"),
        )

    def is_terminal(self) -> bool:
        """Return True if current_state is a terminal state."""
        return self.current_state in TERMINAL_STATES


@dataclass
class TaskProvenance:
    """Creation context for traceability."""

    created_by: Optional[str] = None
    parent_task_id: Optional[str] = None
    ingestion_batch_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.created_by is not None:
            d["created_by"] = self.created_by
        if self.parent_task_id is not None:
            d["parent_task_id"] = self.parent_task_id
        if self.ingestion_batch_id is not None:
            d["ingestion_batch_id"] = self.ingestion_batch_id
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskProvenance:
        return cls(
            created_by=data.get("created_by"),
            parent_task_id=data.get("parent_task_id"),
            ingestion_batch_id=data.get("ingestion_batch_id"),
        )


@dataclass
class Task:
    """
    Runtime task contract aligned with task.v0.1.

    A task is a runtime-owned, bounded unit of work that flows through
    the governed agent loop. Granularity: one task = one inbound request for v0.1.
    """

    schema_version: str
    task_id: str
    task_kind: TaskKind
    request_id: str
    session_id: str
    source_surface: SourceSurface
    repo_scope: TaskRepoScope
    status: TaskStatus
    created_at_utc: str
    updated_at_utc: str
    governance_ref: Optional[TaskGovernanceRef] = None
    constraints: Optional[TaskConstraints] = None
    acceptance_criteria: Optional[TaskAcceptanceCriteria] = None
    provenance: Optional[TaskProvenance] = None
    metadata: Optional[Dict[str, Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize task to dict matching task.v0.1 schema."""
        d: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "task_kind": self.task_kind,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "source_surface": self.source_surface,
            "repo_scope": self.repo_scope.to_dict(),
            "status": self.status.to_dict(),
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
        }
        if self.governance_ref is not None:
            ref_dict = self.governance_ref.to_dict()
            if ref_dict:
                d["governance_ref"] = ref_dict
        if self.constraints is not None:
            constraints_dict = self.constraints.to_dict()
            if constraints_dict:
                d["constraints"] = constraints_dict
        if self.acceptance_criteria is not None:
            ac_dict = self.acceptance_criteria.to_dict()
            if ac_dict:
                d["acceptance_criteria"] = ac_dict
        if self.provenance is not None:
            prov_dict = self.provenance.to_dict()
            if prov_dict:
                d["provenance"] = prov_dict
        if self.metadata is not None and self.metadata:
            d["metadata"] = self.metadata
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any], *, validate: bool = True) -> Task:
        """
        Construct Task from dict.

        Args:
            data: Task dict matching task.v0.1 schema
            validate: If True (default), validate against JSON schema before construction

        Raises:
            TaskValidationError: If validation is enabled and data is invalid
        """
        if validate:
            validate_task_dict(data)

        governance_ref = None
        if "governance_ref" in data:
            governance_ref = TaskGovernanceRef.from_dict(data["governance_ref"])

        constraints = None
        if "constraints" in data:
            constraints = TaskConstraints.from_dict(data["constraints"])

        acceptance_criteria = None
        if "acceptance_criteria" in data:
            acceptance_criteria = TaskAcceptanceCriteria.from_dict(data["acceptance_criteria"])

        provenance = None
        if "provenance" in data:
            provenance = TaskProvenance.from_dict(data["provenance"])

        return cls(
            schema_version=data["schema_version"],
            task_id=data["task_id"],
            task_kind=data["task_kind"],
            request_id=data["request_id"],
            session_id=data["session_id"],
            source_surface=data["source_surface"],
            repo_scope=TaskRepoScope.from_dict(data["repo_scope"]),
            status=TaskStatus.from_dict(data["status"]),
            created_at_utc=data["created_at_utc"],
            updated_at_utc=data["updated_at_utc"],
            governance_ref=governance_ref,
            constraints=constraints,
            acceptance_criteria=acceptance_criteria,
            provenance=provenance,
            metadata=data.get("metadata"),
        )

    def is_terminal(self) -> bool:
        """Return True if task is in a terminal state."""
        return self.status.is_terminal()

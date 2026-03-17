"""
Task bridge tests — M3.17 Slice 3.

Tests minimal conversion bridge between TaskState and Task contract.

Coverage:
- valid TaskState -> Task conversion
- valid Task -> TaskState conversion
- round-trip preserves identity/status fields
- missing required fields fail clearly
- terminal state handling
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from runtime.state.store import TaskState
from runtime.task.contracts import (
    Task,
    TaskConstraints,
    TaskGovernanceRef,
    TaskRepoScope,
    TaskStatus,
)
from runtime.task.bridge import (
    TaskBridgeError,
    task_state_to_task,
    task_to_task_state,
)


class TestTaskStateToTask(unittest.TestCase):
    """Test TaskState -> Task conversion."""

    def _create_valid_task_state(self) -> TaskState:
        """Create a valid TaskState with required metadata."""
        now = datetime.now(timezone.utc).isoformat()
        return TaskState(
            task_id="task-001",
            current_state="CONTEXT_FETCHED",
            created_at=now,
            updated_at=now,
            loop_iteration=2,
            max_iterations=10,
            last_transition_id="governance_to_context",
            consecutive_same_transition_id=0,
            metadata={
                "session_id": "sess-001",
                "request_id": "req-001",
                "root_path": "/workspace/project",
                "revision": "abc123",
                "branch": "main",
                "plan_hash": "hash123",
            },
            transition_journal=[{"transition": "task_to_plan_eval"}],
        )

    def test_valid_task_state_to_task_succeeds(self) -> None:
        """Valid TaskState with metadata converts to Task."""
        state = self._create_valid_task_state()
        task = task_state_to_task(state, source_surface="ide_execute")

        self.assertEqual(task.schema_version, "task.v0.1")
        self.assertEqual(task.task_id, "task-001")
        self.assertEqual(task.task_kind, "execution")
        self.assertEqual(task.request_id, "req-001")
        self.assertEqual(task.session_id, "sess-001")
        self.assertEqual(task.source_surface, "ide_execute")
        self.assertEqual(task.repo_scope.root_path, "/workspace/project")
        self.assertEqual(task.repo_scope.revision, "abc123")
        self.assertEqual(task.repo_scope.branch, "main")
        self.assertEqual(task.status.current_state, "CONTEXT_FETCHED")
        self.assertIsNotNone(task.governance_ref)
        self.assertEqual(task.governance_ref.plan_hash, "hash123")
        self.assertIsNotNone(task.constraints)
        self.assertEqual(task.constraints.max_iterations, 10)

    def test_task_state_to_task_preserves_runtime_metadata(self) -> None:
        """Conversion preserves runtime state info in metadata extension."""
        state = self._create_valid_task_state()
        task = task_state_to_task(state, source_surface="api_execute")

        self.assertIn("runtime_state", task.metadata)
        runtime_state = task.metadata["runtime_state"]
        self.assertEqual(runtime_state["loop_iteration"], 2)
        self.assertEqual(runtime_state["max_iterations"], 10)
        self.assertEqual(runtime_state["last_transition_id"], "governance_to_context")
        self.assertEqual(runtime_state["transition_journal_len"], 1)

    def test_task_state_to_task_with_explicit_params(self) -> None:
        """Explicit parameters override metadata values."""
        state = self._create_valid_task_state()
        explicit_repo = TaskRepoScope(
            root_path="/explicit/path",
            revision="explicit-rev",
        )
        task = task_state_to_task(
            state,
            source_surface="ingestion",
            task_kind="ingestion",
            session_id="explicit-sess",
            request_id="explicit-req",
            repo_scope=explicit_repo,
        )

        self.assertEqual(task.task_kind, "ingestion")
        self.assertEqual(task.session_id, "explicit-sess")
        self.assertEqual(task.request_id, "explicit-req")
        self.assertEqual(task.repo_scope.root_path, "/explicit/path")

    def test_task_state_to_task_uses_task_id_as_request_id_fallback(self) -> None:
        """If no request_id in metadata, falls back to task_id."""
        now = datetime.now(timezone.utc).isoformat()
        state = TaskState(
            task_id="task-fallback",
            current_state="TASK_RECEIVED",
            created_at=now,
            updated_at=now,
            loop_iteration=0,
            max_iterations=10,
            metadata={
                "session_id": "sess-001",
                "root_path": "/workspace",
                "revision": "rev123",
            },
        )
        task = task_state_to_task(state, source_surface="ide_execute")
        self.assertEqual(task.request_id, "task-fallback")

    def test_task_state_to_task_missing_session_id_fails(self) -> None:
        """Missing session_id raises TaskBridgeError."""
        now = datetime.now(timezone.utc).isoformat()
        state = TaskState(
            task_id="task-001",
            current_state="TASK_RECEIVED",
            created_at=now,
            updated_at=now,
            loop_iteration=0,
            max_iterations=10,
            metadata={
                "root_path": "/workspace",
                "revision": "rev123",
            },
        )
        with self.assertRaises(TaskBridgeError) as ctx:
            task_state_to_task(state, source_surface="ide_execute")
        self.assertIn("session_id", str(ctx.exception))

    def test_task_state_to_task_missing_repo_scope_fails(self) -> None:
        """Missing repo_scope fields raises TaskBridgeError."""
        now = datetime.now(timezone.utc).isoformat()
        state = TaskState(
            task_id="task-001",
            current_state="TASK_RECEIVED",
            created_at=now,
            updated_at=now,
            loop_iteration=0,
            max_iterations=10,
            metadata={
                "session_id": "sess-001",
            },
        )
        with self.assertRaises(TaskBridgeError) as ctx:
            task_state_to_task(state, source_surface="ide_execute")
        self.assertIn("repo_scope", str(ctx.exception))

    def test_task_state_to_task_terminal_state_requires_stop_reason(self) -> None:
        """Terminal state without stop_reason raises TaskBridgeError."""
        now = datetime.now(timezone.utc).isoformat()
        state = TaskState(
            task_id="task-001",
            current_state="COMPLETED",
            created_at=now,
            updated_at=now,
            loop_iteration=5,
            max_iterations=10,
            metadata={
                "session_id": "sess-001",
                "root_path": "/workspace",
                "revision": "rev123",
            },
        )
        with self.assertRaises(TaskBridgeError) as ctx:
            task_state_to_task(state, source_surface="ide_execute")
        self.assertIn("stop_reason", str(ctx.exception))

    def test_task_state_to_task_terminal_state_with_stop_reason_succeeds(self) -> None:
        """Terminal state with explicit stop_reason succeeds."""
        now = datetime.now(timezone.utc).isoformat()
        state = TaskState(
            task_id="task-001",
            current_state="BLOCKED",
            created_at=now,
            updated_at=now,
            loop_iteration=5,
            max_iterations=10,
            metadata={
                "session_id": "sess-001",
                "root_path": "/workspace",
                "revision": "rev123",
                "stop_reason": "boundary_block",
            },
        )
        task = task_state_to_task(state, source_surface="ide_execute")
        self.assertEqual(task.status.current_state, "BLOCKED")
        self.assertEqual(task.status.stop_reason, "boundary_block")
        self.assertIsNotNone(task.status.terminal_at_utc)


class TestTaskToTaskState(unittest.TestCase):
    """Test Task -> TaskState conversion."""

    def _create_valid_task(self) -> Task:
        """Create a valid Task contract object."""
        return Task(
            schema_version="task.v0.1",
            task_id="task-002",
            task_kind="execution",
            request_id="req-002",
            session_id="sess-002",
            source_surface="api_execute",
            repo_scope=TaskRepoScope(
                root_path="/workspace/project",
                revision="def456",
                branch="feature",
            ),
            status=TaskStatus(current_state="PROPOSAL_VALIDATED"),
            created_at_utc="2026-03-17T10:00:00Z",
            updated_at_utc="2026-03-17T10:01:00Z",
            governance_ref=TaskGovernanceRef(plan_hash="planhash456"),
            constraints=TaskConstraints(max_iterations=15),
        )

    def test_valid_task_to_task_state_succeeds(self) -> None:
        """Valid Task converts to TaskState."""
        task = self._create_valid_task()
        state = task_to_task_state(task)

        self.assertEqual(state.task_id, "task-002")
        self.assertEqual(state.current_state, "PROPOSAL_VALIDATED")
        self.assertEqual(state.created_at, "2026-03-17T10:00:00Z")
        self.assertEqual(state.updated_at, "2026-03-17T10:01:00Z")
        self.assertEqual(state.max_iterations, 15)
        self.assertEqual(state.metadata["session_id"], "sess-002")
        self.assertEqual(state.metadata["root_path"], "/workspace/project")
        self.assertEqual(state.metadata["revision"], "def456")
        self.assertEqual(state.metadata["branch"], "feature")
        self.assertEqual(state.metadata["plan_hash"], "planhash456")

    def test_task_to_task_state_with_explicit_iteration_params(self) -> None:
        """Explicit iteration parameters are used."""
        task = self._create_valid_task()
        state = task_to_task_state(
            task,
            loop_iteration=3,
            last_transition_id="proposal_to_validated",
            consecutive_same_transition_id=1,
        )

        self.assertEqual(state.loop_iteration, 3)
        self.assertEqual(state.last_transition_id, "proposal_to_validated")
        self.assertEqual(state.consecutive_same_transition_id, 1)

    def test_task_to_task_state_preserves_request_id_if_different(self) -> None:
        """request_id is preserved in metadata if different from task_id."""
        task = self._create_valid_task()
        state = task_to_task_state(task)
        self.assertEqual(state.metadata["request_id"], "req-002")

    def test_task_to_task_state_without_constraints_uses_default(self) -> None:
        """Task without constraints uses default max_iterations."""
        task = Task(
            schema_version="task.v0.1",
            task_id="task-003",
            task_kind="ask",
            request_id="task-003",
            session_id="sess-003",
            source_surface="ide_ask",
            repo_scope=TaskRepoScope(root_path="/workspace", revision="rev"),
            status=TaskStatus(current_state="TASK_RECEIVED"),
            created_at_utc="2026-03-17T10:00:00Z",
            updated_at_utc="2026-03-17T10:00:00Z",
        )
        state = task_to_task_state(task)
        self.assertEqual(state.max_iterations, 10)


class TestBridgeRoundTrip(unittest.TestCase):
    """Test round-trip conversion preserves key fields."""

    def test_task_state_to_task_to_task_state_round_trip(self) -> None:
        """TaskState -> Task -> TaskState preserves key fields."""
        now = datetime.now(timezone.utc).isoformat()
        original = TaskState(
            task_id="task-round",
            current_state="SANDBOX_EXECUTED",
            created_at=now,
            updated_at=now,
            loop_iteration=4,
            max_iterations=8,
            last_transition_id="validated_to_sandbox",
            consecutive_same_transition_id=0,
            metadata={
                "session_id": "sess-round",
                "request_id": "req-round",
                "root_path": "/workspace/round",
                "revision": "roundrev",
                "plan_hash": "roundhash",
            },
        )

        task = task_state_to_task(original, source_surface="ide_execute")
        restored = task_to_task_state(task)

        self.assertEqual(restored.task_id, original.task_id)
        self.assertEqual(restored.current_state, original.current_state)
        self.assertEqual(restored.created_at, original.created_at)
        self.assertEqual(restored.updated_at, original.updated_at)
        self.assertEqual(restored.max_iterations, original.max_iterations)
        self.assertEqual(restored.metadata["session_id"], original.metadata["session_id"])
        self.assertEqual(restored.metadata["root_path"], original.metadata["root_path"])
        self.assertEqual(restored.metadata["plan_hash"], original.metadata["plan_hash"])

    def test_task_to_task_state_to_task_round_trip(self) -> None:
        """Task -> TaskState -> Task preserves key fields."""
        original = Task(
            schema_version="task.v0.1",
            task_id="task-rt2",
            task_kind="execution",
            request_id="req-rt2",
            session_id="sess-rt2",
            source_surface="api_execute",
            repo_scope=TaskRepoScope(
                root_path="/workspace/rt2",
                revision="rt2rev",
                branch="rt2branch",
            ),
            status=TaskStatus(current_state="TESTS_EVALUATED"),
            created_at_utc="2026-03-17T12:00:00Z",
            updated_at_utc="2026-03-17T12:05:00Z",
            governance_ref=TaskGovernanceRef(plan_hash="rt2hash"),
            constraints=TaskConstraints(max_iterations=12),
        )

        state = task_to_task_state(original, loop_iteration=3)
        restored = task_state_to_task(state, source_surface="api_execute")

        self.assertEqual(restored.task_id, original.task_id)
        self.assertEqual(restored.request_id, original.request_id)
        self.assertEqual(restored.session_id, original.session_id)
        self.assertEqual(restored.status.current_state, original.status.current_state)
        self.assertEqual(restored.repo_scope.root_path, original.repo_scope.root_path)
        self.assertEqual(restored.repo_scope.revision, original.repo_scope.revision)
        self.assertEqual(restored.governance_ref.plan_hash, original.governance_ref.plan_hash)
        self.assertEqual(restored.constraints.max_iterations, original.constraints.max_iterations)


class TestBridgeEdgeCases(unittest.TestCase):
    """Test edge cases in bridge conversion."""

    def test_empty_metadata_with_explicit_params_succeeds(self) -> None:
        """TaskState with empty metadata but explicit params succeeds."""
        now = datetime.now(timezone.utc).isoformat()
        state = TaskState(
            task_id="task-empty",
            current_state="TASK_RECEIVED",
            created_at=now,
            updated_at=now,
            loop_iteration=0,
            max_iterations=10,
            metadata={},
        )
        repo = TaskRepoScope(root_path="/explicit", revision="explicitrev")
        task = task_state_to_task(
            state,
            source_surface="replay",
            session_id="explicit-sess",
            repo_scope=repo,
        )
        self.assertEqual(task.session_id, "explicit-sess")
        self.assertEqual(task.repo_scope.root_path, "/explicit")

    def test_all_terminal_states_require_stop_reason(self) -> None:
        """All terminal states require stop_reason."""
        now = datetime.now(timezone.utc).isoformat()
        for terminal_state in ["COMPLETED", "BLOCKED", "FAILED", "ABORTED"]:
            state = TaskState(
                task_id="task-term",
                current_state=terminal_state,
                created_at=now,
                updated_at=now,
                loop_iteration=0,
                max_iterations=10,
                metadata={
                    "session_id": "sess",
                    "root_path": "/ws",
                    "revision": "rev",
                },
            )
            with self.assertRaises(TaskBridgeError):
                task_state_to_task(state, source_surface="ide_execute")

    def test_validation_can_be_disabled(self) -> None:
        """Validation can be skipped with validate=False."""
        now = datetime.now(timezone.utc).isoformat()
        state = TaskState(
            task_id="task-noval",
            current_state="CONTEXT_FETCHED",
            created_at=now,
            updated_at=now,
            loop_iteration=0,
            max_iterations=10,
            metadata={
                "session_id": "sess",
                "root_path": "/ws",
                "revision": "rev",
            },
        )
        task = task_state_to_task(state, source_surface="ide_execute", validate=False)
        self.assertEqual(task.task_id, "task-noval")

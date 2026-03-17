"""
Task wiring tests — M3.17 Slice 4.

Tests optional Task snapshot touchpoints in runtime orchestration.

Coverage:
- Runtime works without Task dependency
- Task is constructed at touchpoint
- Task construction failure does NOT break runtime
- Task snapshot reflects TaskState
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from typing import List

from runtime.orchestrator.loop_controller import LoopController
from runtime.state.store import TaskState, TaskStateStore


class TestTaskSnapshotTouchpoints(unittest.TestCase):
    """Test Task snapshot emission at runtime touchpoints."""

    def test_runtime_works_without_task_callback(self) -> None:
        """Runtime works normally without task_snapshot_callback."""
        controller = LoopController()

        state = controller.create_task(
            "task-no-callback",
            metadata={
                "session_id": "sess-001",
                "root_path": "/workspace",
                "revision": "abc123",
            },
        )

        self.assertEqual(state.task_id, "task-no-callback")
        self.assertEqual(state.current_state, "TASK_RECEIVED")

        result = controller.apply_transition(
            "task-no-callback",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )

        self.assertTrue(result.valid)
        self.assertIsNone(controller.get_last_task_snapshot())

    def test_task_snapshot_emitted_on_create(self) -> None:
        """Task snapshot is emitted when task is created."""
        snapshots: List = []

        def capture_snapshot(task):
            snapshots.append(task)

        controller = LoopController(
            task_snapshot_callback=capture_snapshot,
            task_snapshot_source_surface="ide_execute",
        )

        controller.create_task(
            "task-snap-create",
            metadata={
                "session_id": "sess-002",
                "root_path": "/workspace/project",
                "revision": "def456",
                "branch": "main",
            },
        )

        self.assertEqual(len(snapshots), 1)
        task = snapshots[0]
        self.assertEqual(task.task_id, "task-snap-create")
        self.assertEqual(task.session_id, "sess-002")
        self.assertEqual(task.source_surface, "ide_execute")
        self.assertEqual(task.status.current_state, "TASK_RECEIVED")
        self.assertEqual(task.repo_scope.root_path, "/workspace/project")
        self.assertEqual(task.repo_scope.revision, "def456")

    def test_task_snapshot_emitted_on_transition(self) -> None:
        """Task snapshot is emitted after successful transition."""
        snapshots: List = []

        def capture_snapshot(task):
            snapshots.append(task)

        controller = LoopController(
            task_snapshot_callback=capture_snapshot,
        )

        controller.create_task(
            "task-snap-trans",
            metadata={
                "session_id": "sess-003",
                "root_path": "/workspace",
                "revision": "ghi789",
            },
        )

        self.assertEqual(len(snapshots), 1)

        result = controller.apply_transition(
            "task-snap-trans",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )

        self.assertTrue(result.valid)
        self.assertEqual(len(snapshots), 2)

        task = snapshots[1]
        self.assertEqual(task.task_id, "task-snap-trans")
        self.assertEqual(task.status.current_state, "PLAN_EVALUATED")

    def test_task_snapshot_reflects_task_state(self) -> None:
        """Task snapshot reflects current TaskState fields."""
        snapshots: List = []

        def capture_snapshot(task):
            snapshots.append(task)

        controller = LoopController(
            task_snapshot_callback=capture_snapshot,
        )

        controller.create_task(
            "task-reflect",
            metadata={
                "session_id": "sess-004",
                "request_id": "req-004",
                "root_path": "/workspace/reflect",
                "revision": "jkl012",
                "plan_hash": "planhash123",
            },
            max_iterations=15,
        )

        task = snapshots[0]
        self.assertEqual(task.task_id, "task-reflect")
        self.assertEqual(task.request_id, "req-004")
        self.assertEqual(task.session_id, "sess-004")
        self.assertEqual(task.repo_scope.root_path, "/workspace/reflect")
        self.assertEqual(task.repo_scope.revision, "jkl012")
        self.assertIsNotNone(task.governance_ref)
        self.assertEqual(task.governance_ref.plan_hash, "planhash123")
        self.assertIsNotNone(task.constraints)
        self.assertEqual(task.constraints.max_iterations, 15)

    def test_task_snapshot_preserves_runtime_metadata(self) -> None:
        """Task snapshot includes runtime state in metadata extension."""
        snapshots: List = []

        def capture_snapshot(task):
            snapshots.append(task)

        controller = LoopController(
            task_snapshot_callback=capture_snapshot,
        )

        controller.create_task(
            "task-runtime-meta",
            metadata={
                "session_id": "sess-005",
                "root_path": "/workspace",
                "revision": "mno345",
            },
            max_iterations=8,
        )

        controller.apply_transition(
            "task-runtime-meta",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )

        task = snapshots[1]
        self.assertIn("runtime_state", task.metadata)
        runtime_state = task.metadata["runtime_state"]
        self.assertIn("loop_iteration", runtime_state)
        self.assertIn("max_iterations", runtime_state)
        self.assertEqual(runtime_state["max_iterations"], 8)

    def test_get_last_task_snapshot(self) -> None:
        """get_last_task_snapshot returns most recent snapshot."""
        controller = LoopController(
            task_snapshot_callback=lambda t: None,
        )

        controller.create_task(
            "task-last",
            metadata={
                "session_id": "sess-006",
                "root_path": "/workspace",
                "revision": "pqr678",
            },
        )

        snapshot = controller.get_last_task_snapshot()
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.task_id, "task-last")
        self.assertEqual(snapshot.status.current_state, "TASK_RECEIVED")

        controller.apply_transition(
            "task-last",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )

        snapshot = controller.get_last_task_snapshot()
        self.assertEqual(snapshot.status.current_state, "PLAN_EVALUATED")


class TestTaskSnapshotFailureSafety(unittest.TestCase):
    """Test that Task snapshot failures do not break runtime."""

    def test_missing_session_id_does_not_break_runtime(self) -> None:
        """Missing session_id silently skips Task emission, runtime continues."""
        snapshots: List = []

        def capture_snapshot(task):
            snapshots.append(task)

        controller = LoopController(
            task_snapshot_callback=capture_snapshot,
        )

        state = controller.create_task(
            "task-no-session",
            metadata={
                "root_path": "/workspace",
                "revision": "abc123",
            },
        )

        self.assertEqual(state.task_id, "task-no-session")
        self.assertEqual(len(snapshots), 0)

        result = controller.apply_transition(
            "task-no-session",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )

        self.assertTrue(result.valid)
        self.assertEqual(len(snapshots), 0)
        self.assertIsNone(controller.get_last_task_snapshot())

    def test_missing_repo_scope_does_not_break_runtime(self) -> None:
        """Missing repo_scope silently skips Task emission, runtime continues."""
        snapshots: List = []

        def capture_snapshot(task):
            snapshots.append(task)

        controller = LoopController(
            task_snapshot_callback=capture_snapshot,
        )

        state = controller.create_task(
            "task-no-repo",
            metadata={
                "session_id": "sess-007",
            },
        )

        self.assertEqual(state.task_id, "task-no-repo")
        self.assertEqual(len(snapshots), 0)

    def test_callback_exception_does_not_break_runtime(self) -> None:
        """Exception in callback does not break runtime."""

        def bad_callback(task):
            raise RuntimeError("Callback failed!")

        controller = LoopController(
            task_snapshot_callback=bad_callback,
        )

        state = controller.create_task(
            "task-bad-callback",
            metadata={
                "session_id": "sess-008",
                "root_path": "/workspace",
                "revision": "stu901",
            },
        )

        self.assertEqual(state.task_id, "task-bad-callback")
        self.assertEqual(state.current_state, "TASK_RECEIVED")

        result = controller.apply_transition(
            "task-bad-callback",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )

        self.assertTrue(result.valid)


class TestTaskSnapshotBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing runtime behavior."""

    def test_existing_journal_callback_still_works(self) -> None:
        """Journal callback works alongside Task snapshot callback."""
        journal_entries = []
        task_snapshots = []

        controller = LoopController(
            journal_callback=lambda e: journal_entries.append(e),
            task_snapshot_callback=lambda t: task_snapshots.append(t),
        )

        controller.create_task(
            "task-both-callbacks",
            metadata={
                "session_id": "sess-009",
                "root_path": "/workspace",
                "revision": "vwx234",
            },
        )

        result = controller.apply_transition(
            "task-both-callbacks",
            transition_id="task_to_plan_eval",
            guard_inputs={"event_valid": True},
        )

        self.assertTrue(result.valid)
        self.assertEqual(len(journal_entries), 1)
        self.assertEqual(len(task_snapshots), 2)

        journal_entry = journal_entries[0]
        self.assertEqual(journal_entry.task_id, "task-both-callbacks")
        self.assertEqual(journal_entry.transition_id, "task_to_plan_eval")

    def test_runtime_behavior_identical_without_callback(self) -> None:
        """Runtime behavior is identical with and without Task callback."""
        controller_with = LoopController(
            task_snapshot_callback=lambda t: None,
        )
        controller_without = LoopController()

        for controller, suffix in [(controller_with, "-with"), (controller_without, "-without")]:
            state = controller.create_task(
                f"task-compare{suffix}",
                metadata={
                    "session_id": "sess",
                    "root_path": "/ws",
                    "revision": "rev",
                },
            )

            self.assertEqual(state.current_state, "TASK_RECEIVED")

            result = controller.apply_transition(
                f"task-compare{suffix}",
                transition_id="task_to_plan_eval",
                guard_inputs={"event_valid": True},
            )

            self.assertTrue(result.valid)
            self.assertEqual(result.to_state, "PLAN_EVALUATED")

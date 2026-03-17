"""
Task contract tests — M3.17 Slice 2.

Tests typed contract model aligned with task.v0.1.schema.json.

Coverage:
- valid minimal task dict -> contract object succeeds
- valid full task dict -> contract object succeeds
- contract object -> dict round-trip preserves approved shape
- invalid task dict fails validation before object construction
- terminal-state task missing required terminal fields fails
- metadata namespace violation fails
- expected_phase remains optional
- non-terminal task without terminal fields still succeeds
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

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


REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "runtime" / "schemas" / "examples"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class TestTaskContractConstruction(unittest.TestCase):
    """Test Task contract construction from dict."""

    def test_minimal_task_construction_succeeds(self) -> None:
        """Valid minimal task dict -> contract object succeeds."""
        data = load_json(EXAMPLES / "task_minimal_valid.json")
        task = Task.from_dict(data)
        self.assertEqual(task.schema_version, "task.v0.1")
        self.assertEqual(task.task_id, "task-abc123")
        self.assertEqual(task.task_kind, "execution")
        self.assertEqual(task.request_id, "req-001")
        self.assertEqual(task.session_id, "sess-001")
        self.assertEqual(task.source_surface, "ide_execute")
        self.assertEqual(task.repo_scope.root_path, "/workspace/my-project")
        self.assertEqual(task.repo_scope.revision, "abc123def456")
        self.assertEqual(task.status.current_state, "TASK_RECEIVED")
        self.assertIsNone(task.governance_ref)
        self.assertIsNone(task.constraints)
        self.assertIsNone(task.acceptance_criteria)

    def test_full_task_construction_succeeds(self) -> None:
        """Valid full task dict -> contract object succeeds."""
        data = load_json(EXAMPLES / "task_full_valid.json")
        task = Task.from_dict(data)
        self.assertEqual(task.schema_version, "task.v0.1")
        self.assertEqual(task.task_kind, "execution")
        self.assertIsNotNone(task.governance_ref)
        self.assertIsNotNone(task.constraints)
        self.assertIsNotNone(task.acceptance_criteria)
        self.assertIsNotNone(task.provenance)
        self.assertIsNotNone(task.metadata)
        self.assertEqual(task.status.current_state, "COMPLETED")
        self.assertEqual(task.status.stop_reason, "explicit_refusal")
        self.assertIsNotNone(task.status.terminal_at_utc)

    def test_task_with_governance_ref_succeeds(self) -> None:
        """Task with governance_ref (including expected_phase) succeeds."""
        data = load_json(EXAMPLES / "task_with_governance_ref.json")
        task = Task.from_dict(data)
        self.assertIsNotNone(task.governance_ref)
        self.assertEqual(task.governance_ref.plan_hash, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        self.assertEqual(task.governance_ref.expected_phase, "DES")

    def test_task_with_acceptance_criteria_succeeds(self) -> None:
        """Task with acceptance_criteria succeeds."""
        data = load_json(EXAMPLES / "task_with_acceptance_criteria.json")
        task = Task.from_dict(data)
        self.assertIsNotNone(task.acceptance_criteria)
        self.assertEqual(task.acceptance_criteria.description, "Feature X must pass all unit tests and lint checks")
        self.assertEqual(len(task.acceptance_criteria.test_refs), 2)
        self.assertEqual(len(task.acceptance_criteria.success_signals), 2)

    def test_terminal_task_construction_succeeds(self) -> None:
        """Valid terminal task with required fields succeeds."""
        data = load_json(EXAMPLES / "task_valid_terminal_complete.json")
        task = Task.from_dict(data)
        self.assertEqual(task.status.current_state, "BLOCKED")
        self.assertEqual(task.status.stop_reason, "boundary_block")
        self.assertIsNotNone(task.status.terminal_at_utc)
        self.assertTrue(task.is_terminal())


class TestTaskContractRoundTrip(unittest.TestCase):
    """Test Task contract serialization round-trip."""

    def test_minimal_task_round_trip(self) -> None:
        """Minimal task round-trip preserves shape."""
        data = load_json(EXAMPLES / "task_minimal_valid.json")
        task = Task.from_dict(data)
        result = task.to_dict()
        self.assertEqual(result, data)

    def test_full_task_round_trip(self) -> None:
        """Full task round-trip preserves shape."""
        data = load_json(EXAMPLES / "task_full_valid.json")
        task = Task.from_dict(data)
        result = task.to_dict()
        self.assertEqual(result, data)

    def test_governance_ref_round_trip(self) -> None:
        """Task with governance_ref round-trips correctly."""
        data = load_json(EXAMPLES / "task_with_governance_ref.json")
        task = Task.from_dict(data)
        result = task.to_dict()
        self.assertEqual(result, data)

    def test_acceptance_criteria_round_trip(self) -> None:
        """Task with acceptance_criteria round-trips correctly."""
        data = load_json(EXAMPLES / "task_with_acceptance_criteria.json")
        task = Task.from_dict(data)
        result = task.to_dict()
        self.assertEqual(result, data)

    def test_terminal_task_round_trip(self) -> None:
        """Terminal task round-trips correctly."""
        data = load_json(EXAMPLES / "task_valid_terminal_complete.json")
        task = Task.from_dict(data)
        result = task.to_dict()
        self.assertEqual(result, data)


class TestTaskContractValidation(unittest.TestCase):
    """Test Task contract validation failures."""

    def test_invalid_task_fails_before_construction(self) -> None:
        """Invalid task dict fails validation before object construction."""
        data = load_json(EXAMPLES / "task_invalid_missing_task_id.json")
        with self.assertRaises(TaskValidationError) as ctx:
            Task.from_dict(data)
        self.assertIn("task_id", str(ctx.exception))

    def test_wrong_schema_version_fails(self) -> None:
        """Wrong schema_version fails validation."""
        data = load_json(EXAMPLES / "task_invalid_wrong_schema_version.json")
        with self.assertRaises(TaskValidationError) as ctx:
            Task.from_dict(data)
        self.assertIn("schema_version", str(ctx.exception))

    def test_invalid_task_kind_fails(self) -> None:
        """Invalid task_kind fails validation."""
        data = load_json(EXAMPLES / "task_invalid_task_kind.json")
        with self.assertRaises(TaskValidationError):
            Task.from_dict(data)

    def test_invalid_current_state_fails(self) -> None:
        """Invalid current_state fails validation."""
        data = load_json(EXAMPLES / "task_invalid_current_state.json")
        with self.assertRaises(TaskValidationError):
            Task.from_dict(data)

    def test_terminal_state_missing_stop_reason_fails(self) -> None:
        """Terminal state without stop_reason fails validation."""
        data = load_json(EXAMPLES / "task_invalid_terminal_no_stop_reason.json")
        with self.assertRaises(TaskValidationError) as ctx:
            Task.from_dict(data)
        self.assertIn("stop_reason", str(ctx.exception))

    def test_terminal_state_missing_terminal_at_utc_fails(self) -> None:
        """Terminal state without terminal_at_utc fails validation."""
        data = load_json(EXAMPLES / "task_invalid_terminal_no_timestamp.json")
        with self.assertRaises(TaskValidationError) as ctx:
            Task.from_dict(data)
        self.assertIn("terminal_at_utc", str(ctx.exception))

    def test_invalid_governance_ref_shape_fails(self) -> None:
        """Invalid governance_ref shape fails validation."""
        data = load_json(EXAMPLES / "task_invalid_governance_ref_shape.json")
        with self.assertRaises(TaskValidationError):
            Task.from_dict(data)

    def test_invalid_metadata_not_namespaced_fails(self) -> None:
        """Metadata with non-lowercase namespace key fails validation."""
        data = load_json(EXAMPLES / "task_invalid_metadata_not_namespaced.json")
        with self.assertRaises(TaskValidationError):
            Task.from_dict(data)

    def test_invalid_metadata_string_fails(self) -> None:
        """Metadata as string (not object) fails validation."""
        data = load_json(EXAMPLES / "task_invalid_metadata_string.json")
        with self.assertRaises(TaskValidationError):
            Task.from_dict(data)


class TestTaskContractOptionalFields(unittest.TestCase):
    """Test optional field handling in Task contract."""

    def test_expected_phase_is_optional(self) -> None:
        """governance_ref without expected_phase succeeds (expected_phase is optional hint)."""
        data = load_json(EXAMPLES / "task_valid_no_expected_phase.json")
        task = Task.from_dict(data)
        self.assertIsNotNone(task.governance_ref)
        self.assertIsNotNone(task.governance_ref.plan_hash)
        self.assertIsNone(task.governance_ref.expected_phase)

    def test_governance_ref_is_optional(self) -> None:
        """Task without governance_ref succeeds."""
        data = load_json(EXAMPLES / "task_minimal_valid.json")
        task = Task.from_dict(data)
        self.assertIsNone(task.governance_ref)

    def test_constraints_is_optional(self) -> None:
        """Task without constraints succeeds."""
        data = load_json(EXAMPLES / "task_minimal_valid.json")
        task = Task.from_dict(data)
        self.assertIsNone(task.constraints)

    def test_acceptance_criteria_is_optional(self) -> None:
        """Task without acceptance_criteria succeeds."""
        data = load_json(EXAMPLES / "task_minimal_valid.json")
        task = Task.from_dict(data)
        self.assertIsNone(task.acceptance_criteria)

    def test_non_terminal_without_terminal_fields_succeeds(self) -> None:
        """Non-terminal task without stop_reason/terminal_at_utc succeeds."""
        data = load_json(EXAMPLES / "task_minimal_valid.json")
        task = Task.from_dict(data)
        self.assertEqual(task.status.current_state, "TASK_RECEIVED")
        self.assertIsNone(task.status.stop_reason)
        self.assertIsNone(task.status.terminal_at_utc)
        self.assertFalse(task.is_terminal())


class TestTaskContractHelpers(unittest.TestCase):
    """Test Task contract helper methods."""

    def test_is_terminal_for_terminal_states(self) -> None:
        """is_terminal returns True for terminal states."""
        for state in ["COMPLETED", "BLOCKED", "FAILED", "ABORTED"]:
            status = TaskStatus(
                current_state=state,
                stop_reason="explicit_refusal",
                terminal_at_utc="2026-03-17T10:00:00Z",
            )
            self.assertTrue(status.is_terminal(), f"{state} should be terminal")

    def test_is_terminal_for_non_terminal_states(self) -> None:
        """is_terminal returns False for non-terminal states."""
        non_terminal = [
            "TASK_RECEIVED",
            "PLAN_EVALUATED",
            "GOVERNANCE_CLASSIFIED",
            "CONTEXT_FETCHED",
            "MODEL_PROPOSAL_READY",
            "PROPOSAL_VALIDATED",
            "SANDBOX_EXECUTED",
            "TESTS_EVALUATED",
            "REVIEW_DECIDED",
        ]
        for state in non_terminal:
            status = TaskStatus(current_state=state)
            self.assertFalse(status.is_terminal(), f"{state} should not be terminal")


class TestValidateTaskDict(unittest.TestCase):
    """Test validate_task_dict function."""

    def test_validate_valid_task(self) -> None:
        """Valid task dict passes validation."""
        data = load_json(EXAMPLES / "task_minimal_valid.json")
        validate_task_dict(data)

    def test_validate_invalid_task_raises(self) -> None:
        """Invalid task dict raises TaskValidationError."""
        data = load_json(EXAMPLES / "task_invalid_missing_task_id.json")
        with self.assertRaises(TaskValidationError):
            validate_task_dict(data)


class TestNestedContractTypes(unittest.TestCase):
    """Test nested contract types independently."""

    def test_repo_scope_construction(self) -> None:
        """TaskRepoScope constructs and serializes correctly."""
        scope = TaskRepoScope(root_path="/workspace", revision="abc123", branch="main")
        d = scope.to_dict()
        self.assertEqual(d["root_path"], "/workspace")
        self.assertEqual(d["revision"], "abc123")
        self.assertEqual(d["branch"], "main")
        restored = TaskRepoScope.from_dict(d)
        self.assertEqual(restored.root_path, scope.root_path)
        self.assertEqual(restored.branch, scope.branch)

    def test_repo_scope_without_branch(self) -> None:
        """TaskRepoScope without branch omits branch from dict."""
        scope = TaskRepoScope(root_path="/workspace", revision="abc123")
        d = scope.to_dict()
        self.assertNotIn("branch", d)

    def test_governance_ref_construction(self) -> None:
        """TaskGovernanceRef constructs and serializes correctly."""
        ref = TaskGovernanceRef(plan_hash="abc123", expected_phase="DES")
        d = ref.to_dict()
        self.assertEqual(d["plan_hash"], "abc123")
        self.assertEqual(d["expected_phase"], "DES")
        restored = TaskGovernanceRef.from_dict(d)
        self.assertEqual(restored.plan_hash, ref.plan_hash)
        self.assertEqual(restored.expected_phase, ref.expected_phase)

    def test_governance_ref_without_expected_phase(self) -> None:
        """TaskGovernanceRef without expected_phase omits it from dict."""
        ref = TaskGovernanceRef(plan_hash="abc123")
        d = ref.to_dict()
        self.assertIn("plan_hash", d)
        self.assertNotIn("expected_phase", d)

    def test_constraints_construction(self) -> None:
        """TaskConstraints constructs and serializes correctly."""
        constraints = TaskConstraints(max_iterations=10, budget_tokens=1000, timeout_seconds=60)
        d = constraints.to_dict()
        self.assertEqual(d["max_iterations"], 10)
        self.assertEqual(d["budget_tokens"], 1000)
        self.assertEqual(d["timeout_seconds"], 60)

    def test_acceptance_criteria_construction(self) -> None:
        """TaskAcceptanceCriteria constructs and serializes correctly."""
        ac = TaskAcceptanceCriteria(
            description="Tests must pass",
            test_refs=["test.py"],
            success_signals=["all_pass"],
        )
        d = ac.to_dict()
        self.assertEqual(d["description"], "Tests must pass")
        self.assertEqual(d["test_refs"], ["test.py"])
        self.assertEqual(d["success_signals"], ["all_pass"])

    def test_status_construction(self) -> None:
        """TaskStatus constructs and serializes correctly."""
        status = TaskStatus(
            current_state="COMPLETED",
            stop_reason="explicit_refusal",
            terminal_at_utc="2026-03-17T10:00:00Z",
        )
        d = status.to_dict()
        self.assertEqual(d["current_state"], "COMPLETED")
        self.assertEqual(d["stop_reason"], "explicit_refusal")
        self.assertEqual(d["terminal_at_utc"], "2026-03-17T10:00:00Z")

    def test_provenance_construction(self) -> None:
        """TaskProvenance constructs and serializes correctly."""
        prov = TaskProvenance(created_by="runtime", parent_task_id="parent-123")
        d = prov.to_dict()
        self.assertEqual(d["created_by"], "runtime")
        self.assertEqual(d["parent_task_id"], "parent-123")
        self.assertNotIn("ingestion_batch_id", d)

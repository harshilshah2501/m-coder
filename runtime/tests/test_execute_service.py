"""Tests for M3.4 Execute Service — /v0/execute endpoint."""

import pytest
from runtime.execute_service.handlers import (
    validate_execute_request,
    handle_execute_request,
    EXECUTE_REQUEST_SCHEMA,
    EXECUTE_RESPONSE_SCHEMA,
)


class TestValidateExecuteRequest:
    """Tests for request validation."""

    def test_valid_request_passes(self):
        data = {
            "schema_version": EXECUTE_REQUEST_SCHEMA,
            "request_id": "req-123",
            "repo_root": "/tmp/repo",
            "command": "echo hello",
        }
        errors = validate_execute_request(data)
        assert errors == []

    def test_missing_request_id_fails(self):
        data = {
            "repo_root": "/tmp/repo",
            "command": "echo hello",
        }
        errors = validate_execute_request(data)
        assert "Missing required field: request_id" in errors

    def test_missing_repo_root_fails(self):
        data = {
            "request_id": "req-123",
            "command": "echo hello",
        }
        errors = validate_execute_request(data)
        assert "Missing required field: repo_root" in errors

    def test_missing_command_fails(self):
        data = {
            "request_id": "req-123",
            "repo_root": "/tmp/repo",
        }
        errors = validate_execute_request(data)
        assert "Missing required field: command" in errors

    def test_wrong_schema_version_fails(self):
        data = {
            "schema_version": "wrong.version",
            "request_id": "req-123",
            "repo_root": "/tmp/repo",
            "command": "echo hello",
        }
        errors = validate_execute_request(data)
        assert len(errors) == 1
        assert "schema_version" in errors[0]


class TestHandleExecuteRequest:
    """Tests for execute request handling."""

    def test_response_has_correct_schema(self):
        data = {
            "request_id": "req-test-schema",
            "repo_root": "/nonexistent/path",
            "command": "echo hello",
        }
        response = handle_execute_request(data)
        assert response["schema_version"] == EXECUTE_RESPONSE_SCHEMA
        assert response["request_id"] == "req-test-schema"

    def test_refuse_keyword_triggers_refusal(self):
        """Commands with 'refuse' keyword should be refused."""
        data = {
            "request_id": "req-refuse",
            "repo_root": "/tmp",
            "command": "refuse this command",
        }
        response = handle_execute_request(data)
        assert response["outcome"] == "REFUSED"
        assert response["executed"] is False
        assert response["posture"] == "refuse"

    def test_defer_keyword_triggers_deferral(self):
        """Commands with 'defer' keyword should be deferred."""
        data = {
            "request_id": "req-defer",
            "repo_root": "/tmp",
            "command": "defer this action",
        }
        response = handle_execute_request(data)
        assert response["outcome"] == "DEFERRED"
        assert response["executed"] is False
        assert response["posture"] == "defer"

    def test_bound_keyword_triggers_bounded_allow(self):
        """Commands with 'bound' keyword should get bounded allowance."""
        data = {
            "request_id": "req-bound",
            "repo_root": "/tmp",
            "command": "bound this execution",
        }
        response = handle_execute_request(data)
        assert response["outcome"] == "BOUNDED_ALLOW"
        assert response["executed"] is False
        assert response["posture"] == "bounded_allow"

    def test_response_includes_ui_block(self):
        """Response should include UI information."""
        data = {
            "request_id": "req-ui",
            "repo_root": "/tmp",
            "command": "refuse test",
        }
        response = handle_execute_request(data)
        assert "ui" in response
        assert "title" in response["ui"]
        assert "message" in response["ui"]
        assert "severity" in response["ui"]

    def test_response_includes_plan_hash(self):
        """Response should include plan hash for audit."""
        data = {
            "request_id": "req-hash",
            "repo_root": "/tmp",
            "command": "refuse test",
        }
        response = handle_execute_request(data)
        assert "plan_hash" in response
        assert len(response["plan_hash"]) == 64  # SHA256 hex

    def test_nonexistent_repo_root_blocked(self):
        """Execution with nonexistent repo root should be blocked."""
        data = {
            "request_id": "req-nopath",
            "repo_root": "/this/path/does/not/exist/at/all",
            "command": "echo hello",
        }
        response = handle_execute_request(data)
        assert response["outcome"] == "BLOCKED"
        assert response["executed"] is False

    def test_empty_command_blocked(self):
        """Empty command should be blocked."""
        data = {
            "request_id": "req-empty",
            "repo_root": "/tmp",
            "command": "   ",
        }
        response = handle_execute_request(data)
        assert response["outcome"] == "BLOCKED"
        assert response["executed"] is False

    def test_request_id_echoed_back(self):
        """Request ID should be echoed back in response."""
        data = {
            "request_id": "req-echo-test-12345",
            "repo_root": "/tmp",
            "command": "refuse test",
        }
        response = handle_execute_request(data)
        assert response["request_id"] == "req-echo-test-12345"

    def test_outcome_is_not_collapsed(self):
        """Different outcomes should be distinct (no SUCCESS/FAILURE collapse)."""
        outcomes_seen = set()

        for keyword, expected in [
            ("refuse", "REFUSED"),
            ("defer", "DEFERRED"),
            ("bound", "BOUNDED_ALLOW"),
        ]:
            data = {
                "request_id": f"req-{keyword}",
                "repo_root": "/tmp",
                "command": f"{keyword} test",
            }
            response = handle_execute_request(data)
            outcomes_seen.add(response["outcome"])
            assert response["outcome"] == expected

        assert len(outcomes_seen) == 3


class TestExecuteServiceIntegration:
    """Integration tests for execute service."""

    def test_full_refuse_flow(self):
        """Test complete refusal flow."""
        data = {
            "schema_version": EXECUTE_REQUEST_SCHEMA,
            "request_id": "req-full-refuse",
            "timestamp_utc": "2026-03-12T00:00:00Z",
            "repo_root": "/tmp",
            "revision": "abc123",
            "branch": "main",
            "command": "refuse dangerous operation",
            "ide_context": {
                "product": "jetbrains",
                "ide": "intellij",
                "project": "test-project",
                "user": "testuser",
            },
            "client_policy": {
                "fail_closed_if_gate_unreachable": True,
                "mode": "enforcing",
            },
        }
        response = handle_execute_request(data)

        assert response["outcome"] == "REFUSED"
        assert response["executed"] is False
        assert "plan_hash" in response
        assert response["ui"]["severity"] == "error"

    def test_full_defer_flow(self):
        """Test complete deferral flow."""
        data = {
            "request_id": "req-full-defer",
            "repo_root": "/tmp",
            "command": "approval needed for this",
        }
        response = handle_execute_request(data)

        assert response["outcome"] == "DEFERRED"
        assert response["executed"] is False
        assert response["ui"]["severity"] == "warning"

    def test_full_bounded_allow_flow(self):
        """Test complete bounded allow flow."""
        data = {
            "request_id": "req-full-bounded",
            "repo_root": "/tmp",
            "command": "restrict this operation",
        }
        response = handle_execute_request(data)

        assert response["outcome"] == "BOUNDED_ALLOW"
        assert response["executed"] is False
        assert response["ui"]["severity"] == "warning"

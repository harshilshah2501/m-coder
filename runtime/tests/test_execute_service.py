"""Tests for M3.4 Execute Service — /v0/execute endpoint."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from runtime.execute_service.handlers import (
    validate_execute_request,
    handle_execute_request,
    EXECUTE_REQUEST_SCHEMA,
    EXECUTE_RESPONSE_SCHEMA,
)
from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore


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
    """Tests for execute request handling. Governance via explicit request fields only."""

    def test_response_has_correct_schema(self):
        data = {
            "request_id": "req-test-schema",
            "repo_root": "/nonexistent/path",
            "command": "echo hello",
        }
        response = handle_execute_request(data)
        assert response["schema_version"] == EXECUTE_RESPONSE_SCHEMA
        assert response["request_id"] == "req-test-schema"

    def test_explicit_plan_gate_refuse_triggers_refusal(self):
        """Explicit plan_gate_refuse=True must be refused; no keyword in command."""
        data = {
            "request_id": "req-refuse",
            "repo_root": "/tmp",
            "command": "echo hello",
            "plan_gate_refuse": True,
        }
        response = handle_execute_request(data)
        assert response["outcome"] == "REFUSED"
        assert response["executed"] is False
        assert response["posture"] == "refuse"

    def test_explicit_plan_gate_defer_triggers_deferral(self):
        """Explicit plan_gate_defer=True must be deferred."""
        data = {
            "request_id": "req-defer",
            "repo_root": "/tmp",
            "command": "echo hello",
            "plan_gate_defer": True,
        }
        response = handle_execute_request(data)
        assert response["outcome"] == "DEFERRED"
        assert response["executed"] is False
        assert response["posture"] == "defer"

    def test_explicit_plan_gate_bounded_allow_triggers_bounded_allow(self):
        """Explicit plan_gate_bounded_allow=True must get bounded allowance."""
        data = {
            "request_id": "req-bound",
            "repo_root": "/tmp",
            "command": "echo hello",
            "plan_gate_bounded_allow": True,
        }
        response = handle_execute_request(data)
        assert response["outcome"] == "BOUNDED_ALLOW"
        assert response["executed"] is False
        assert response["posture"] == "bounded_allow"

    def test_response_includes_ui_block(self):
        data = {
            "request_id": "req-ui",
            "repo_root": "/tmp",
            "command": "echo test",
            "plan_gate_refuse": True,
        }
        response = handle_execute_request(data)
        assert "ui" in response
        assert "title" in response["ui"]
        assert "message" in response["ui"]
        assert "severity" in response["ui"]

    def test_response_includes_plan_hash(self):
        data = {
            "request_id": "req-hash",
            "repo_root": "/tmp",
            "command": "echo test",
            "plan_gate_refuse": True,
        }
        response = handle_execute_request(data)
        assert "plan_hash" in response
        assert len(response["plan_hash"]) == 64

    def test_nonexistent_repo_root_blocked(self):
        data = {
            "request_id": "req-nopath",
            "repo_root": "/this/path/does/not/exist/at/all",
            "command": "echo hello",
        }
        response = handle_execute_request(data)
        assert response["outcome"] == "BLOCKED"
        assert response["executed"] is False

    def test_empty_command_blocked(self):
        data = {
            "request_id": "req-empty",
            "repo_root": "/tmp",
            "command": "   ",
        }
        response = handle_execute_request(data)
        assert response["outcome"] == "BLOCKED"
        assert response["executed"] is False

    def test_request_id_echoed_back(self):
        data = {
            "request_id": "req-echo-test-12345",
            "repo_root": "/tmp",
            "command": "echo x",
            "plan_gate_refuse": True,
        }
        response = handle_execute_request(data)
        assert response["request_id"] == "req-echo-test-12345"

    def test_outcomes_distinct_via_explicit_flags(self):
        """Different outcomes via explicit flags only; no command keyword dependency."""
        for flag_key, expected_outcome in [
            ("plan_gate_refuse", "REFUSED"),
            ("plan_gate_defer", "DEFERRED"),
            ("plan_gate_bounded_allow", "BOUNDED_ALLOW"),
        ]:
            data = {
                "request_id": f"req-{flag_key}",
                "repo_root": "/tmp",
                "command": "echo same command",
                flag_key: True,
            }
            response = handle_execute_request(data)
            assert response["outcome"] == expected_outcome


class TestExecuteServiceDecisionLedgering:
    """Plan-Gate decision must be ledgered when ledger_path is provided."""

    def test_decision_ledger_row_id_present_when_ledger_path_provided(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.db"
            data = {
                "request_id": "req-ledger",
                "repo_root": "/tmp",
                "command": "echo ok",
                "plan_gate_refuse": True,
                "ledger_path": str(ledger_path),
            }
            response = handle_execute_request(data)
        assert response["outcome"] == "REFUSED"
        assert "decision_ledger_row_id" in response
        assert response["decision_ledger_row_id"] is not None
        assert response["decision_ledger_row_id"].startswith("plangate-")

    def test_refused_path_persists_plangate_refused_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.db"
            data = {
                "request_id": "req-refused-ledger",
                "repo_root": "/tmp",
                "command": "echo x",
                "plan_gate_refuse": True,
                "ledger_path": str(ledger_path),
            }
            handle_execute_request(data)
            store = SandboxLedgerStore(ledger_path)
            rows = store.list_all()
        assert len(rows) >= 1
        assert any(r.event_type == "plangate_refused" for r in rows)

    def test_deferred_path_persists_plangate_deferred_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.db"
            data = {
                "request_id": "req-deferred-ledger",
                "repo_root": "/tmp",
                "command": "echo x",
                "plan_gate_defer": True,
                "ledger_path": str(ledger_path),
            }
            handle_execute_request(data)
            store = SandboxLedgerStore(ledger_path)
            rows = store.list_all()
        assert any(r.event_type == "plangate_deferred" for r in rows)

    def test_bounded_allow_path_persists_plangate_bounded_allow_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.db"
            data = {
                "request_id": "req-bounded-ledger",
                "repo_root": "/tmp",
                "command": "echo x",
                "plan_gate_bounded_allow": True,
                "ledger_path": str(ledger_path),
            }
            handle_execute_request(data)
            store = SandboxLedgerStore(ledger_path)
            rows = store.list_all()
        assert any(r.event_type == "plangate_bounded_allow" for r in rows)

    def test_safe_execute_path_persists_decision_and_sandbox_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.db"
            data = {
                "request_id": "req-executed-ledger",
                "repo_root": tmp,
                "command": "echo success",
                "ledger_path": str(ledger_path),
            }
            response = handle_execute_request(data)
            assert response["outcome"] == "EXECUTED"
            assert response["executed"] is True
            assert response.get("decision_ledger_row_id")
            assert response.get("ledger_row_id")
            store = SandboxLedgerStore(ledger_path)
            rows = store.list_all()
            assert any(r.event_type == "plangate_safe_execute" for r in rows)
            assert any(r.event_type == "sandbox_executed" for r in rows)

    def test_no_ledger_path_omits_decision_ledger_row_id(self):
        data = {
            "request_id": "req-no-ledger",
            "repo_root": "/tmp",
            "command": "echo x",
            "plan_gate_refuse": True,
        }
        response = handle_execute_request(data)
        assert response["outcome"] == "REFUSED"
        assert response.get("decision_ledger_row_id") is None

    def test_ledger_path_provided_but_persistence_fails_returns_blocked_fail_closed(self):
        """When ledger_path is explicitly provided but store creation or persist fails, return BLOCKED; no execution."""
        with tempfile.TemporaryDirectory() as tmp:
            # Pass a directory as ledger_path so SQLite cannot open it as a DB file → store creation fails
            ledger_path_as_dir = Path(tmp)
            data = {
                "request_id": "req-fail-persist",
                "repo_root": tmp,
                "command": "echo would-run",
                "ledger_path": str(ledger_path_as_dir),
            }
            response = handle_execute_request(data)
        assert response["outcome"] == "BLOCKED"
        assert response["executed"] is False
        assert "could not be persisted" in (response.get("reason") or "")
        assert response["ui"]["severity"] == "error"


class TestExecuteServiceIntegration:
    """Integration tests for execute service."""

    def test_full_refuse_flow_with_explicit_flag(self):
        data = {
            "schema_version": EXECUTE_REQUEST_SCHEMA,
            "request_id": "req-full-refuse",
            "timestamp_utc": "2026-03-12T00:00:00Z",
            "repo_root": "/tmp",
            "revision": "abc123",
            "branch": "main",
            "command": "echo dangerous",
            "plan_gate_refuse": True,
            "ide_context": {"product": "jetbrains", "ide": "intellij"},
            "client_policy": {"fail_closed_if_gate_unreachable": True, "mode": "enforcing"},
        }
        response = handle_execute_request(data)
        assert response["outcome"] == "REFUSED"
        assert response["executed"] is False
        assert "plan_hash" in response
        assert response["ui"]["severity"] == "error"

    def test_full_defer_flow_with_explicit_flag(self):
        data = {
            "request_id": "req-full-defer",
            "repo_root": "/tmp",
            "command": "echo hello",
            "plan_gate_defer": True,
        }
        response = handle_execute_request(data)
        assert response["outcome"] == "DEFERRED"
        assert response["executed"] is False
        assert response["ui"]["severity"] == "warning"

    def test_full_bounded_allow_flow_with_explicit_flag(self):
        data = {
            "request_id": "req-full-bounded",
            "repo_root": "/tmp",
            "command": "echo hello",
            "plan_gate_bounded_allow": True,
        }
        response = handle_execute_request(data)
        assert response["outcome"] == "BOUNDED_ALLOW"
        assert response["executed"] is False
        assert response["ui"]["severity"] == "warning"

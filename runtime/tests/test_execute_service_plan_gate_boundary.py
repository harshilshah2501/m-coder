"""Trust boundary: plan_gate_* hints only when MOTADATA_EXECUTE_ALLOW_PLAN_GATE_OVERRIDES is set."""

from __future__ import annotations

import tempfile

import pytest

from runtime.execute_service.handlers import (
    EXECUTE_REQUEST_SCHEMA,
    validate_execute_request,
    handle_execute_request,
)


class TestPlanGateHintsRejectedInProductionMode:
    def test_validate_rejects_plan_gate_refuse_without_env(self, monkeypatch):
        monkeypatch.delenv("MOTADATA_EXECUTE_ALLOW_PLAN_GATE_OVERRIDES", raising=False)
        errs = validate_execute_request(
            {
                "schema_version": EXECUTE_REQUEST_SCHEMA,
                "request_id": "req-pg",
                "repo_root": "/tmp",
                "command": "echo x",
                "plan_gate_refuse": True,
            }
        )
        assert errs
        assert any("Forbidden client hints" in e for e in errs)

    def test_validate_accepts_plan_gate_when_env_enabled(self, monkeypatch):
        monkeypatch.setenv("MOTADATA_EXECUTE_ALLOW_PLAN_GATE_OVERRIDES", "1")
        errs = validate_execute_request(
            {
                "schema_version": EXECUTE_REQUEST_SCHEMA,
                "request_id": "req-pg",
                "repo_root": "/tmp",
                "command": "echo x",
                "plan_gate_refuse": True,
            }
        )
        assert errs == []

    def test_handle_execute_blocks_without_env(self, monkeypatch):
        monkeypatch.delenv("MOTADATA_EXECUTE_ALLOW_PLAN_GATE_OVERRIDES", raising=False)
        with tempfile.TemporaryDirectory() as tmp:
            resp = handle_execute_request(
                {
                    "request_id": "req-block",
                    "repo_root": tmp,
                    "command": "echo x",
                    "plan_gate_defer": True,
                }
            )
        assert resp["outcome"] == "BLOCKED"
        assert resp["executed"] is False
        assert "Forbidden client hints" in (resp.get("reason") or "")

    def test_plugin_style_request_without_hints_works_without_env(self, monkeypatch):
        monkeypatch.delenv("MOTADATA_EXECUTE_ALLOW_PLAN_GATE_OVERRIDES", raising=False)
        with tempfile.TemporaryDirectory() as tmp:
            resp = handle_execute_request(
                {
                    "request_id": "req-ok",
                    "repo_root": tmp,
                    "command": "echo ok",
                }
            )
        assert resp["outcome"] == "EXECUTED"
        assert resp["executed"] is True

    def test_handle_execute_allows_overrides_with_env(self, monkeypatch):
        monkeypatch.setenv("MOTADATA_EXECUTE_ALLOW_PLAN_GATE_OVERRIDES", "1")
        with tempfile.TemporaryDirectory() as tmp:
            resp = handle_execute_request(
                {
                    "request_id": "req-ref",
                    "repo_root": tmp,
                    "command": "echo x",
                    "plan_gate_refuse": True,
                }
            )
        assert resp["outcome"] == "REFUSED"
        assert resp["executed"] is False

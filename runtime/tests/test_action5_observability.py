"""Action 5 — observability / correlation (grep-friendly logs, preserved response IDs)."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ask_response_keeps_trace_id_and_routing_mode_for_reconstruction(tmp_path) -> None:
    """Success path: response fields align with PLAN_GATE log routing_mode (plan_only)."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "a.py").write_text("x = 1\n", encoding="utf-8")

    from runtime.ask_service.handlers import handle_ask_request

    response = handle_ask_request(
        {
            "schema_version": "ask_request.v0.1",
            "request_id": "req-obs-1",
            "trace_id": "trace-obs-1",
            "timestamp_utc": "2026-03-10T12:00:00Z",
            "repo_root": str(repo_root),
            "revision": "abc",
            "query": "what is x",
        }
    )
    assert response.get("request_id") == "req-obs-1"
    assert response.get("trace_id") == "trace-obs-1"
    assert response.get("routing_mode") == "plan_only"


def test_ask_error_shape_keeps_trace_id_and_routing_mode(tmp_path) -> None:
    """Failure path: correlation fields remain for grep / proof packs."""
    from runtime.ask_service.handlers import handle_ask_request

    response = handle_ask_request(
        {
            "schema_version": "ask_request.v0.1",
            "request_id": "req-obs-err",
            "trace_id": "trace-obs-err",
            "timestamp_utc": "2026-03-10T12:00:00Z",
            "repo_root": str(tmp_path / "nonexistent_repo_xyz"),
            "revision": "abc",
            "query": "q",
        }
    )
    assert response.get("request_id") == "req-obs-err"
    assert response.get("trace_id") == "trace-obs-err"
    assert response.get("routing_mode") == "plan_only"


def test_ask_log_line_includes_task_type(caplog, tmp_path) -> None:
    caplog.set_level(logging.INFO)
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "f.py").write_text("pass\n", encoding="utf-8")

    from runtime.ask_service.handlers import handle_ask_request

    handle_ask_request(
        {
            "schema_version": "ask_request.v0.1",
            "request_id": "req-log-1",
            "trace_id": "t-log",
            "timestamp_utc": "2026-03-10T12:00:00Z",
            "repo_root": str(repo_root),
            "revision": "abc",
            "query": "q",
            "task_type": "EXPLAIN_DEBUG",
        }
    )
    msgs = [r.message for r in caplog.records if r.name == "runtime.ask_service.handlers"]
    assert any("[ASK]" in m and "t-log" in m and "req-log-1" in m and "EXPLAIN_DEBUG" in m for m in msgs)


def test_execute_entry_log_correlation(caplog, monkeypatch) -> None:
    caplog.set_level(logging.INFO)
    monkeypatch.setenv("MOTADATA_EXECUTE_ALLOW_PLAN_GATE_OVERRIDES", "1")
    from runtime.execute_service.handlers import handle_execute_request

    handle_execute_request(
        {
            "schema_version": "execute_request.v0.1",
            "request_id": "req-ex-obs",
            "trace_id": "trace-ex-1",
            "repo_root": str(_REPO_ROOT),
            "revision": "r",
            "branch": "b",
            "command": "echo test",
            "plan_gate_refuse": True,
        }
    )
    msgs = [r.message for r in caplog.records if r.name == "runtime.execute_service.handlers"]
    assert any("[EXECUTE]" in m and "trace-ex-1" in m and "req-ex-obs" in m for m in msgs)


def test_explain_debug_log_always_includes_trace_slot() -> None:
    from runtime.ask_service import reasoner

    mock_log = MagicMock(spec=logging.Logger)
    with patch.object(reasoner, "LOG", mock_log):
        reasoner._explain_debug_request_log(
            "rid-x",
            "http://127.0.0.1:8000",
            "m",
            "error",
            reasoner.time.perf_counter(),
            trace_id="",
        )
    mock_log.info.assert_called_once()
    fmt = mock_log.info.call_args[0][0]
    args = mock_log.info.call_args[0][1:]
    assert "EXPLAIN_DEBUG" in fmt
    assert "routing_mode=explain_debug" in fmt
    assert "(none)" in args

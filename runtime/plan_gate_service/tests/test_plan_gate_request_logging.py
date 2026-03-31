"""Unit tests for Plan-Gate POST request logging helpers (Action 5 slice)."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

from runtime.plan_gate_service import app as plan_gate_app


def test_request_id_from_body_missing() -> None:
    assert plan_gate_app._request_id_from_body({}) == "unknown"
    assert plan_gate_app._request_id_from_body({"request_id": None}) == "unknown"
    assert plan_gate_app._request_id_from_body({"request_id": ""}) == "unknown"
    assert plan_gate_app._request_id_from_body({"request_id": "   "}) == "unknown"
    assert plan_gate_app._request_id_from_body("not a dict") == "unknown"


def test_request_id_from_body_present() -> None:
    assert plan_gate_app._request_id_from_body({"request_id": "req-abc"}) == "req-abc"
    assert plan_gate_app._request_id_from_body({"request_id": 42}) == "42"


def test_trace_id_from_body() -> None:
    assert plan_gate_app._trace_id_from_body({}) == ""
    assert plan_gate_app._trace_id_from_body({"trace_id": None}) == ""
    assert plan_gate_app._trace_id_from_body({"trace_id": "   "}) == ""
    assert plan_gate_app._trace_id_from_body({"trace_id": "t-1"}) == "t-1"
    assert plan_gate_app._trace_id_from_body("not a dict") == ""


def test_plan_gate_request_log_emits_grep_friendly_line() -> None:
    mock_log = MagicMock(spec=logging.Logger)
    with patch.object(plan_gate_app, "LOG", mock_log):
        t0 = plan_gate_app.time.perf_counter()
        plan_gate_app._plan_gate_request_log(
            "/v1/ask",
            "ask_v1",
            "rid-1",
            "success",
            t0,
        )
    mock_log.info.assert_called_once()
    fmt, args = mock_log.info.call_args[0][0], mock_log.info.call_args[0][1:]
    assert "PLAN_GATE request" in fmt
    assert "/v1/ask" in args
    assert "ask_v1" in args
    assert "rid-1" in args
    assert "success" in args


def test_plan_gate_request_log_includes_trace_id_when_set() -> None:
    mock_log = MagicMock(spec=logging.Logger)
    with patch.object(plan_gate_app, "LOG", mock_log):
        t0 = plan_gate_app.time.perf_counter()
        plan_gate_app._plan_gate_request_log(
            "/v0/ask",
            "ask_v0",
            "rid-1",
            "success",
            t0,
            trace_id="trace-xyz",
        )
    mock_log.info.assert_called_once()
    fmt, args = mock_log.info.call_args[0][0], mock_log.info.call_args[0][1:]
    assert "trace_id" in fmt
    assert "trace-xyz" in args

"""Unit tests for Context Layer request logging helpers (Action 5 slice)."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

from runtime.context_layer_service import app as cl_app


def test_request_id_from_body() -> None:
    assert cl_app._request_id_from_body({}) == "unknown"
    assert cl_app._request_id_from_body({"request_id": None}) == "unknown"
    assert cl_app._request_id_from_body({"request_id": "  "}) == "unknown"
    assert cl_app._request_id_from_body({"request_id": "r1"}) == "r1"
    assert cl_app._request_id_from_body({"correlation_id": "c1"}) == "c1"
    assert cl_app._request_id_from_body({"request_id": "r1", "correlation_id": "c1"}) == "r1"
    assert cl_app._request_id_from_body("not dict") == "unknown"


def test_workspace_marker() -> None:
    assert cl_app._workspace_marker("") == "empty"
    assert cl_app._workspace_marker("/a/b/myproject") == "myproject"
    assert cl_app._workspace_marker("C:\\a\\b\\ws") == "ws"


def test_context_layer_request_log_format() -> None:
    mock_log = MagicMock(spec=logging.Logger)
    with patch.object(cl_app, "LOG", mock_log):
        t0 = cl_app.time.perf_counter()
        cl_app._context_layer_request_log("/v1/export_evidence", "rid-9", "success", t0, "proj")
    mock_log.info.assert_called_once()
    args = mock_log.info.call_args[0][1:]
    assert "/v1/export_evidence" in args
    assert "rid-9" in args
    assert "success" in args
    assert "proj" in args

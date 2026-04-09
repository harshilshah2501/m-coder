"""Tests for explain_debug request_id propagation and EXPLAIN_DEBUG logging (Action 5 slice)."""

from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock, patch

from runtime.context.contracts import (
    ContextBundle,
    ContextBundleLimits,
    ContextBundleProvenance,
    ContextItem,
)
from runtime.ask_service.reasoner import explain_debug, _explain_debug_request_log


def _minimal_bundle() -> ContextBundle:
    return ContextBundle(
        task_id="t1",
        revision="r1",
        created_at_utc="2026-01-01T00:00:00Z",
        items=[
            ContextItem(
                path="a.py",
                content="x=1",
                byte_size=3,
                selection_reason="direct",
            )
        ],
        limits=ContextBundleLimits(max_files=1, max_bytes=1000, truncated=False),
        provenance=ContextBundleProvenance(
            root_path="/tmp",
            selectors=["direct"],
            requested_files=["a.py"],
            symbol_hints=[],
        ),
    )


@patch("runtime.ask_service.reasoner.urllib.request.urlopen")
@patch("runtime.ask_service.reasoner.LOG")
def test_explain_debug_logs_success_with_request_id(mock_log: MagicMock, mock_urlopen: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(
        {
            "choices": [
                {
                    "message": {
                        "content": '{"summary":"ok","logic_flow":"","likely_bug_risk":"","evidence":[],"confidence_limits":""}'
                    }
                }
            ]
        }
    ).encode("utf-8")
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_resp
    mock_cm.__exit__.return_value = None
    mock_urlopen.return_value = mock_cm

    out = explain_debug(
        "q",
        "f.py",
        "code",
        _minimal_bundle(),
        request_id="req-vllm-1",
    )
    assert out.error is None
    assert out.summary == "ok"
    mock_log.info.assert_called()
    found = False
    for call in mock_log.info.call_args_list:
        msg = call[0][0] if call[0] else ""
        if "EXPLAIN_DEBUG" in str(msg) and "req-vllm-1" in str(call):
            found = True
            break
        args = call[0]
        if len(args) >= 2 and args[0] == "EXPLAIN_DEBUG request_id=%s base_url=%s model=%s status=%s duration_ms=%.2f":
            if args[1] == "req-vllm-1" and args[4] == "success":
                found = True
                break
    assert found, mock_log.info.call_args_list


@patch("runtime.ask_service.reasoner.urllib.request.urlopen")
@patch("runtime.ask_service.reasoner.LOG")
def test_explain_debug_logs_error_on_network(mock_log: MagicMock, mock_urlopen: MagicMock) -> None:
    import urllib.error

    mock_urlopen.side_effect = urllib.error.URLError("refused")

    out = explain_debug("q", "f.py", "c", _minimal_bundle(), request_id="req-err")
    assert out.error is not None
    mock_log.info.assert_called()
    args = mock_log.info.call_args[0]
    assert "EXPLAIN_DEBUG" in args[0]
    # Log format: trace_id, request_id, base_url, model, status, duration_ms (see reasoner._explain_debug_request_log)
    assert args[1] == "(none)"  # no trace_id
    assert args[2] == "req-err"
    assert args[5] == "error"


def test_explain_debug_request_log_helper() -> None:
    mock_log = MagicMock(spec=logging.Logger)
    with patch("runtime.ask_service.reasoner.LOG", mock_log):
        t0 = __import__("time").perf_counter()
        _explain_debug_request_log("r1", "http://127.0.0.1:8000", "m", "success", t0)
    mock_log.info.assert_called_once()
    fmt = mock_log.info.call_args[0][0]
    assert "EXPLAIN_DEBUG" in fmt

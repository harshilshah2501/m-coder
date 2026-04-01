"""Plan-Gate Service HTTP server. Stdlib only."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from . import config
from . import handlers

LOG = logging.getLogger(__name__)

EXPLAIN_VLLM_URL_ENV = "MOTADATA_EXPLAIN_VLLM_URL"
VLLM_HEALTH_TIMEOUT = 5

_PATH_TO_REQUEST_TYPE = {
    "/v0/plan": "plan",
    "/v0/ask": "ask_v0",
    "/v1/ask": "ask_v1",
    "/v0/execute": "execute",
}


def _request_id_from_body(data: object) -> str:
    if not isinstance(data, dict):
        return "unknown"
    rid = data.get("request_id")
    if rid is None:
        return "unknown"
    s = str(rid).strip()
    return s if s else "unknown"


def _trace_id_from_body(data: object) -> str:
    if not isinstance(data, dict):
        return ""
    tid = data.get("trace_id")
    if tid is None:
        return ""
    s = str(tid).strip()
    return s


def _trace_display(trace_id: str) -> str:
    """Grep-stable trace slot: literal (none) when absent (never omit the key)."""
    s = (trace_id or "").strip()
    return s if s else "(none)"


def _plan_gate_request_log(
    path: str,
    request_type: str,
    request_id: str,
    status: str,
    t0: float,
    *,
    trace_id: str = "",
    routing_mode: str = "n/a",
    outcome: str = "n/a",
) -> None:
    """One line per POST; grep-friendly correlation (Action 5)."""
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    tid = _trace_display(trace_id)
    LOG.info(
        "PLAN_GATE request path=%s request_type=%s request_id=%s trace_id=%s routing_mode=%s outcome=%s status=%s duration_ms=%.2f",
        path,
        request_type,
        request_id,
        tid,
        routing_mode,
        outcome,
        status,
        elapsed_ms,
    )


def _vllm_healthcheck() -> None:
    """If MOTADATA_EXPLAIN_VLLM_URL is set, verify vLLM is reachable; exit with clear error if not."""
    url_env = os.environ.get(EXPLAIN_VLLM_URL_ENV, "").strip()
    if not url_env:
        return
    base = url_env.rstrip("/")
    health_url = f"{base}/v1/models"
    try:
        req = urllib.request.Request(health_url, method="GET")
        with urllib.request.urlopen(req, timeout=VLLM_HEALTH_TIMEOUT) as resp:
            if resp.status != 200:
                print(f"vLLM healthcheck failed: {health_url} returned {resp.status}", file=sys.stderr)
                sys.exit(1)
    except (urllib.error.URLError, OSError) as e:
        print(f"vLLM not reachable at {health_url}: {e}", file=sys.stderr)
        print("Start vLLM first (e.g. runtime/scripts/governed_services.sh start) or unset MOTADATA_EXPLAIN_VLLM_URL.", file=sys.stderr)
        sys.exit(1)


class PlanGateHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._send_json(200, {"status": "ok"})
            return
        if self.path == "/version":
            self._send_json(200, {
                "service_version": "v0.1",
                "supported_schemas": {
                    "plan_request": "v0.1",
                    "decision_response": "v0.1",
                    "plan": "v0.1",
                    "ledger": "v0.1",
                    "shadow_run_record": "v0.1",
                    "ingestion_batch": "v0.1",
                    "ask_request": "v0.1",
                    "ask_request_v1": "v1.0",
                    "plan_only_response": "v0.1",
                    "execute_request": "v0.1",
                    "execute_response": "v0.1"
                },
            })
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        t0 = time.perf_counter()
        path = self.path
        req_type = _PATH_TO_REQUEST_TYPE.get(path, "unknown")

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError) as e:
            self._send_json(400, {"error": f"Invalid JSON: {e}"})
            _plan_gate_request_log(
                path,
                req_type,
                "unknown",
                "error",
                t0,
                trace_id="",
                routing_mode="n/a",
                outcome="invalid_json",
            )
            return

        rid = _request_id_from_body(data)
        tid = _trace_id_from_body(data)

        if path == "/v0/plan":
            errs = handlers.validate_plan_request(data)
            if errs:
                self._send_json(400, {"error": "Schema validation failed", "details": errs})
                _plan_gate_request_log(
                    path,
                    req_type,
                    rid,
                    "error",
                    t0,
                    trace_id=tid,
                    routing_mode="n/a",
                    outcome="validation_error",
                )
                return

            mode = config.get_mode()
            fixed_time = config.get_fixed_time()
            spool_root = config.get_spool_dir()
            spool_root.mkdir(parents=True, exist_ok=True)
            date_or_id = fixed_time or "2026-03-01T00:00:00Z"  # fallback for grouping

            try:
                decision, _ = handlers.handle_plan_request(
                    data, mode, fixed_time, spool_root, date_or_id
                )
                self._send_json(200, decision)
                _plan_gate_request_log(
                    path,
                    req_type,
                    rid,
                    "success",
                    t0,
                    trace_id=tid,
                    routing_mode="n/a",
                    outcome="ok",
                )
            except Exception as e:
                self._send_json(500, {"error": str(e)})
                _plan_gate_request_log(
                    path,
                    req_type,
                    rid,
                    "error",
                    t0,
                    trace_id=tid,
                    routing_mode="n/a",
                    outcome="handler_error",
                )
            return

        if path == "/v0/ask":
            from runtime.ask_service.handlers import validate_ask_request, handle_ask_request

            errs = validate_ask_request(data)
            if errs:
                self._send_json(400, {"error": "Schema validation failed", "details": errs})
                _plan_gate_request_log(
                    path,
                    req_type,
                    rid,
                    "error",
                    t0,
                    trace_id=tid,
                    routing_mode="n/a",
                    outcome="validation_error",
                )
                return

            try:
                response = handle_ask_request(data)
                self._send_json(200, response)
                rm = str(response.get("routing_mode") or "n/a")
                _plan_gate_request_log(
                    path,
                    req_type,
                    rid,
                    "success",
                    t0,
                    trace_id=tid,
                    routing_mode=rm,
                    outcome="ok",
                )
            except Exception as e:
                # Even on handler failure, preserve execution=false semantics inside handler.
                self._send_json(500, {"error": str(e)})
                _plan_gate_request_log(
                    path,
                    req_type,
                    rid,
                    "error",
                    t0,
                    trace_id=tid,
                    routing_mode="n/a",
                    outcome="handler_error",
                )
            return

        if path == "/v1/ask":
            from runtime.ask_service.v1_ingest import (
                AskV1ClientError,
                handle_ask_v1_request,
                validate_ask_v1_request,
            )

            errs = validate_ask_v1_request(data)
            if errs:
                self._send_json(
                    400,
                    {"error": "ask_envelope_invalid", "message": "Schema validation failed", "details": errs},
                )
                _plan_gate_request_log(
                    path,
                    req_type,
                    rid,
                    "error",
                    t0,
                    trace_id=tid,
                    routing_mode="n/a",
                    outcome="validation_error",
                )
                return

            try:
                response = handle_ask_v1_request(data)
                self._send_json(200, response)
                rm = str(response.get("routing_mode") or "n/a")
                _plan_gate_request_log(
                    path,
                    req_type,
                    rid,
                    "success",
                    t0,
                    trace_id=tid,
                    routing_mode=rm,
                    outcome="ok",
                )
            except AskV1ClientError as e:
                self._send_json(
                    400,
                    {"error": e.code, "message": e.message, "details": e.details},
                )
                _plan_gate_request_log(
                    path,
                    req_type,
                    rid,
                    "error",
                    t0,
                    trace_id=tid,
                    routing_mode="n/a",
                    outcome=str(e.code),
                )
            except Exception as e:
                self._send_json(500, {"error": str(e)})
                _plan_gate_request_log(
                    path,
                    req_type,
                    rid,
                    "error",
                    t0,
                    trace_id=tid,
                    routing_mode="n/a",
                    outcome="handler_error",
                )
            return

        if path == "/v0/execute":
            from runtime.execute_service.handlers import validate_execute_request, handle_execute_request

            errs = validate_execute_request(data)
            if errs:
                self._send_json(400, {"error": "Schema validation failed", "details": errs})
                _plan_gate_request_log(
                    path,
                    req_type,
                    rid,
                    "error",
                    t0,
                    trace_id=tid,
                    routing_mode="n/a",
                    outcome="validation_error",
                )
                return

            try:
                response = handle_execute_request(data)
                self._send_json(200, response)
                oc = str(response.get("outcome") or "n/a")
                _plan_gate_request_log(
                    path,
                    req_type,
                    rid,
                    "success",
                    t0,
                    trace_id=tid,
                    routing_mode="n/a",
                    outcome=oc,
                )
            except Exception as e:
                self._send_json(500, {"error": str(e)})
                _plan_gate_request_log(
                    path,
                    req_type,
                    rid,
                    "error",
                    t0,
                    trace_id=tid,
                    routing_mode="n/a",
                    outcome="handler_error",
                )
            return

        self._send_json(404, {"error": "Not found"})
        _plan_gate_request_log(
            path,
            req_type,
            rid,
            "error",
            t0,
            trace_id=tid,
            routing_mode="n/a",
            outcome="not_found",
        )

    def _send_json(self, status: int, obj: object) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj, indent=2).encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:
        pass  # quiet by default


def run_server(port: int | None = None, spool_dir: Path | None = None) -> HTTPServer:
    port = config.get_port() if port is None else port
    if spool_dir is not None:
        os.environ["PLAN_GATE_SPOOL_DIR"] = str(spool_dir)
    server = HTTPServer(("127.0.0.1", port), PlanGateHandler)
    return server


def main() -> None:
    if not logging.root.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s %(name)s %(message)s",
        )
    _vllm_healthcheck()
    port = config.get_port()
    server = run_server()
    print(f"Plan-Gate Service on http://127.0.0.1:{port}/v0/plan")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

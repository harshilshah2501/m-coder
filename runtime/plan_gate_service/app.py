"""Plan-Gate Service HTTP server. Stdlib only."""

from __future__ import annotations

import json
import os
import socketserver
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from . import config
from . import handlers


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
                    "plan_only_response": "v0.1"
                },
            })
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError) as e:
            self._send_json(400, {"error": f"Invalid JSON: {e}"})
            return

        if self.path == "/v0/plan":
            errs = handlers.validate_plan_request(data)
            if errs:
                self._send_json(400, {"error": "Schema validation failed", "details": errs})
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
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        if self.path == "/v0/ask":
            from runtime.ask_service.handlers import validate_ask_request, handle_ask_request

            errs = validate_ask_request(data)
            if errs:
                self._send_json(400, {"error": "Schema validation failed", "details": errs})
                return

            try:
                response = handle_ask_request(data)
                self._send_json(200, response)
            except Exception as e:
                # Even on handler failure, preserve execution=false semantics inside handler.
                self._send_json(500, {"error": str(e)})
            return

        self._send_json(404, {"error": "Not found"})

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
    port = config.get_port()
    server = run_server()
    print(f"Plan-Gate Service on http://127.0.0.1:{port}/v0/plan")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

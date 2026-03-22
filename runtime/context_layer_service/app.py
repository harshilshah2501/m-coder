"""Context Layer HTTP service — stdlib only. Evidence export for JetBrains / clients."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

from . import config
from .evidence_api import export_evidence_bundle_dict
from .logging_setup import get_logger, setup_logging_from_env

LOG = get_logger(__name__)


def _error_payload(
    error: str,
    message: str,
    *,
    failure_class: str,
) -> dict:
    return {
        "error": error,
        "message": message,
        "failure_class": failure_class,
    }


def _package_version() -> str:
    return config.get_package_version()


class ContextLayerHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "motadata_context_layer",
                    "package_version": _package_version(),
                },
            )
            return
        if self.path == "/version":
            self._send_json(
                200,
                {
                    "package": "motadata-context-layer",
                    "package_version": _package_version(),
                    "service_version": "v0.1",
                    "evidence_schema_hint": "layer5.evidence_bundle.v1",
                    "endpoints": [
                        "GET /healthz",
                        "GET /version",
                        "POST /v1/export_evidence",
                    ],
                },
            )
            return
        self._send_json(404, _error_payload("not_found", "Not found", failure_class="route_not_found"))

    def do_POST(self) -> None:
        if self.path != "/v1/export_evidence":
            self._send_json(404, _error_payload("not_found", "Not found", failure_class="route_not_found"))
            return
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError) as e:
            self._send_json(
                400,
                _error_payload("invalid_json", str(e), failure_class="invalid_json"),
            )
            return

        workspace = (data.get("workspace_root") or data.get("workspace") or "").strip()
        query = (data.get("query") or "").strip()
        top_k = data.get("top_k", 8)
        if not isinstance(top_k, int):
            self._send_json(
                400,
                _error_payload(
                    "invalid_request",
                    "top_k must be an integer",
                    failure_class="invalid_request",
                ),
            )
            return

        try:
            bundle = export_evidence_bundle_dict(workspace, query, top_k=top_k)
        except ValueError as e:
            self._send_json(
                400,
                _error_payload("invalid_request", str(e), failure_class="invalid_request"),
            )
            return
        except RuntimeError as e:
            # Service is healthy; workspace/index/export could not complete — not "service absent"
            self._send_json(
                422,
                _error_payload("export_failed", str(e), failure_class="workspace_export_failed"),
            )
            return
        except Exception as e:
            LOG.exception("Unexpected export error")
            self._send_json(
                500,
                _error_payload("internal_error", str(e), failure_class="internal_error"),
            )
            return

        try:
            from runtime.layer5.evidence.schema_validate import (
                EvidenceSchemaValidationError,
                validate_evidence_bundle_dict,
            )

            validate_evidence_bundle_dict(bundle)
        except EvidenceSchemaValidationError as e:
            LOG.error("Built bundle failed schema validation: %s", e)
            self._send_json(
                500,
                _error_payload(
                    "internal_error",
                    str(e),
                    failure_class="evidence_contract_violation",
                ),
            )
            return
        except Exception as e:
            LOG.exception("Schema validation unexpected error")
            self._send_json(
                500,
                _error_payload("internal_error", str(e), failure_class="internal_error"),
            )
            return

        self._send_json(200, bundle)

    def _send_json(self, status: int, obj: object) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:
        LOG.debug("%s - %s", self.address_string(), format % args)


def run_server(host: str | None = None, port: int | None = None) -> HTTPServer:
    h = config.get_bind_host() if host is None else host
    p = config.get_port() if port is None else port
    return HTTPServer((h, p), ContextLayerHandler)


def main() -> None:
    setup_logging_from_env()
    host = config.get_bind_host()
    port = config.get_port()
    server = run_server(host, port)
    LOG.info("Context Layer listening on http://%s:%s/healthz", host, port)
    print(
        f"Context Layer service on http://{host}:{port}/healthz (package {_package_version()})",
        file=sys.stderr,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

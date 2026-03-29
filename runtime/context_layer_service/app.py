"""Context Layer HTTP service — stdlib only. Evidence export for JetBrains / clients."""

from __future__ import annotations

import json
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from runtime.layer5.workspace.path_normalizer import PathNormalizer

from . import config
from .evidence_api import export_evidence_bundle_dict
from .logging_setup import get_logger, setup_logging_from_env

LOG = get_logger(__name__)


def _normalize_workspace_root(raw: str) -> str:
    """Canonicalize workspace_root at HTTP boundary (JetBrains WSL bridge paths, symlinks)."""
    w = raw.strip()
    if not w:
        return w
    return PathNormalizer.normalize(w, resolve_symlinks=True).canonical_path

_EXPORT_PATH = "/v1/export_evidence"


def _request_id_from_body(data: object) -> str:
    if not isinstance(data, dict):
        return "unknown"
    for key in ("request_id", "correlation_id"):
        raw = data.get(key)
        if raw is None:
            continue
        s = str(raw).strip()
        if s:
            return s
    return "unknown"


def _workspace_marker(workspace: str) -> str:
    w = workspace.strip().replace("\\", "/")
    if not w:
        return "empty"
    seg = w.rstrip("/").split("/")[-1]
    return seg if len(seg) <= 64 else seg[:61] + "..."


def _context_layer_request_log(
    path: str,
    request_id: str,
    status: str,
    t0: float,
    workspace_marker: str,
) -> None:
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    LOG.info(
        "CONTEXT_LAYER request path=%s request_id=%s status=%s workspace=%s duration_ms=%.2f",
        path,
        request_id,
        status,
        workspace_marker,
        elapsed_ms,
    )


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
        t0 = time.perf_counter()
        path = self.path
        if path != _EXPORT_PATH:
            self._send_json(404, _error_payload("not_found", "Not found", failure_class="route_not_found"))
            _context_layer_request_log(path, "unknown", "error", t0, "n/a")
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
            _context_layer_request_log(_EXPORT_PATH, "unknown", "error", t0, "n/a")
            return

        rid = _request_id_from_body(data)
        workspace = (data.get("workspace_root") or data.get("workspace") or "").strip()
        workspace = _normalize_workspace_root(workspace)
        wmark = _workspace_marker(workspace)
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
            _context_layer_request_log(_EXPORT_PATH, rid, "error", t0, wmark)
            return

        try:
            bundle = export_evidence_bundle_dict(workspace, query, top_k=top_k)
        except ValueError as e:
            self._send_json(
                400,
                _error_payload("invalid_request", str(e), failure_class="invalid_request"),
            )
            _context_layer_request_log(_EXPORT_PATH, rid, "error", t0, wmark)
            return
        except RuntimeError as e:
            # Service is healthy; workspace/index/export could not complete — not "service absent"
            self._send_json(
                422,
                _error_payload("export_failed", str(e), failure_class="workspace_export_failed"),
            )
            _context_layer_request_log(_EXPORT_PATH, rid, "error", t0, wmark)
            return
        except Exception as e:
            LOG.exception("Unexpected export error")
            self._send_json(
                500,
                _error_payload("internal_error", str(e), failure_class="internal_error"),
            )
            _context_layer_request_log(_EXPORT_PATH, rid, "error", t0, wmark)
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
            _context_layer_request_log(_EXPORT_PATH, rid, "error", t0, wmark)
            return
        except Exception as e:
            LOG.exception("Schema validation unexpected error")
            self._send_json(
                500,
                _error_payload("internal_error", str(e), failure_class="internal_error"),
            )
            _context_layer_request_log(_EXPORT_PATH, rid, "error", t0, wmark)
            return

        self._send_json(200, bundle)
        _context_layer_request_log(_EXPORT_PATH, rid, "success", t0, wmark)

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

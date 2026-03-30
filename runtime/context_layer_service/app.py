"""Context Layer HTTP service — stdlib only. Evidence export for JetBrains / clients."""

from __future__ import annotations

import json
import os
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


def _looks_like_jetbrains_roaming_project_path(path: str) -> bool:
    """True when path looks like JetBrains Roaming .../JetBrains/.../projects/... (not a repo root)."""
    p = path.replace("\\", "/").lower()
    return "/jetbrains/" in p and "/projects/" in p


def _default_workspace_from_env() -> str:
    """Linux checkout used when the IDE sends Roaming metadata paths (same as smoke tests)."""
    for key in ("MOTADATA_CONTEXT_LAYER_DEFAULT_WORKSPACE", "MOTADATA_ROOT"):
        raw = (os.environ.get(key) or "").strip()
        if not raw:
            continue
        w = PathNormalizer.normalize(raw, resolve_symlinks=True).canonical_path
        if os.path.isdir(w):
            return w
    return ""


def _effective_export_workspace(normalized: str) -> tuple[str, bool]:
    """
    If the client sends a JetBrains Roaming .../projects/<hash> path, replace with env default
    when set so export works without relying on the IDE plugin alone.
    Returns (workspace, substituted).
    """
    if not normalized:
        return normalized, False
    fallback = _default_workspace_from_env()
    if not fallback:
        return normalized, False
    if not _looks_like_jetbrains_roaming_project_path(normalized):
        return normalized, False
    a = normalized.rstrip("/")
    b = fallback.rstrip("/")
    if a == b:
        return normalized, False
    return fallback, True


_EXPORT_PATH = "/v1/export_evidence"

_DEBUG_EXPORT_ENV = "MOTADATA_CONTEXT_LAYER_DEBUG_EXPORT"


def _debug_export_requests() -> bool:
    v = (os.environ.get(_DEBUG_EXPORT_ENV) or "").strip().lower()
    return v in ("1", "true", "yes")


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
        raw_workspace = (data.get("workspace_root") or data.get("workspace") or "").strip()
        normalized = _normalize_workspace_root(raw_workspace)
        workspace, ws_substituted = _effective_export_workspace(normalized)
        if ws_substituted:
            LOG.info(
                "CONTEXT_LAYER export_evidence workspace substituted request_id=%s "
                "(IDE sent JetBrains Roaming path; using MOTADATA_CONTEXT_LAYER_DEFAULT_WORKSPACE or MOTADATA_ROOT)",
                rid,
            )
        if _debug_export_requests():
            LOG.info(
                "DEBUG export_evidence peer=%s rid=%s raw_workspace_root=%r normalized=%r "
                "effective_workspace_root=%r query_len=%s",
                self.client_address,
                rid,
                raw_workspace,
                normalized,
                workspace,
                len((data.get("query") or "").strip()),
            )
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
            msg = str(e)
            if (
                "Workspace root does not exist" in msg
                and workspace
                and _looks_like_jetbrains_roaming_project_path(workspace)
            ):
                msg += (
                    " Hint: path looks like JetBrains Roaming .../projects/<hash>, not the repo checkout. "
                    "Use a current Motadata IDE plugin (resolves module/content roots), open a project file, "
                    "or IDE VM option -Dmotadata.layer5.workspace_root=/abs/path/to/repo."
                )
            self._send_json(
                422,
                _error_payload("export_failed", msg, failure_class="workspace_export_failed"),
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

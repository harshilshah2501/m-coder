"""Context Layer HTTP service — stdlib only. Evidence export for JetBrains / clients."""

from __future__ import annotations

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from runtime.layer5.workspace.path_normalizer import PathNormalizer
from runtime.layer5.build_info import layer5_build_info

from . import config
from .evidence_api import export_evidence_bundle_dict
from .logging_setup import get_logger, setup_logging_from_env

LOG = get_logger(__name__)

_index_cache_singleton = None


def _get_workspace_index_cache():
    """Lazily construct in-process index cache when enabled (see config.index_cache_enabled)."""
    global _index_cache_singleton
    if not config.index_cache_enabled():
        return None
    if _index_cache_singleton is None:
        from runtime.context_layer_service.workspace_index_cache import WorkspaceIndexCache

        _index_cache_singleton = WorkspaceIndexCache(
            max_keys=config.index_cache_max_keys(),
            ttl_sec=config.index_cache_ttl_sec(),
        )
    return _index_cache_singleton


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


def _workspace_from_optional_file() -> str:
    """First line of a file = absolute repo path (set-and-forget; no env on each shell)."""
    paths: list[str] = []
    env = (os.environ.get("MOTADATA_CONTEXT_LAYER_WORKSPACE_FILE") or "").strip()
    if env:
        paths.append(env)
    paths.append(str(Path.home() / ".motadata_context_layer_workspace"))
    paths.append(str(Path.home() / ".config" / "motadata" / "context_layer_workspace"))
    seen: set[str] = set()
    for p in paths:
        if not p or p in seen:
            continue
        seen.add(p)
        try:
            fp = Path(p)
            if not fp.is_file():
                continue
            lines = fp.read_text(encoding="utf-8").strip().splitlines()
            if not lines:
                continue
            root = lines[0].strip()
            if not root:
                continue
            w = PathNormalizer.normalize(root, resolve_symlinks=True).canonical_path
            if os.path.isdir(w):
                return w
        except OSError:
            continue
    return ""


def _heuristic_home_motadata() -> str:
    """Common clone locations under $HOME (explicit env / file wins)."""
    home = Path.home()
    for parts in (("Projects", "Motadata"), ("Motadata",)):
        p = home.joinpath(*parts)
        try:
            if p.is_dir():
                return str(p.resolve())
        except OSError:
            continue
    return ""


def _heuristic_unique_motadata_under_home(home_root: str | Path | None = None) -> str:
    """
    When the Context Layer runs as root, Path.home() is /root and ~/Projects/Motadata misses
    /home/<user>/Projects/Motadata. If exactly one such directory exists under /home, use it.
    """
    hr = Path(home_root if home_root is not None else "/home")
    if not hr.is_dir():
        return ""
    found: list[str] = []
    try:
        for user_dir in sorted(hr.iterdir()):
            if not user_dir.is_dir():
                continue
            for parts in (("Projects", "Motadata"), ("Motadata",)):
                p = user_dir.joinpath(*parts)
                try:
                    if p.is_dir():
                        found.append(str(p.resolve()))
                except OSError:
                    continue
    except OSError:
        return ""
    uniq = sorted(set(found))
    if len(uniq) == 1:
        return uniq[0]
    return ""


def _resolve_fallback_workspace() -> str:
    """Linux checkout when the IDE sends Roaming .../projects/<hash>: env → file → $HOME heuristics → /home scan."""
    for key in ("MOTADATA_CONTEXT_LAYER_DEFAULT_WORKSPACE", "MOTADATA_ROOT"):
        raw = (os.environ.get(key) or "").strip()
        if not raw:
            continue
        w = PathNormalizer.normalize(raw, resolve_symlinks=True).canonical_path
        if os.path.isdir(w):
            return w
    w = _workspace_from_optional_file()
    if w:
        return w
    w = _heuristic_home_motadata()
    if w:
        return w
    return _heuristic_unique_motadata_under_home()


def _effective_export_workspace(normalized: str) -> tuple[str, bool]:
    """
    If the client sends a JetBrains Roaming .../projects/<hash> path, replace with a resolved
    checkout (env, ~/.motadata_context_layer_workspace, or ~/Projects/Motadata / ~/Motadata).
    Returns (workspace, substituted).
    """
    if not normalized:
        return normalized, False
    fallback = _resolve_fallback_workspace()
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


def _trace_id_from_body(data: object) -> str:
    if not isinstance(data, dict):
        return "(none)"
    raw = data.get("trace_id")
    if raw is None:
        return "(none)"
    s = str(raw).strip()
    return s if s else "(none)"


def _workspace_marker(workspace: str) -> str:
    w = workspace.strip().replace("\\", "/")
    if not w:
        return "empty"
    seg = w.rstrip("/").split("/")[-1]
    return seg if len(seg) <= 64 else seg[:61] + "..."


def _context_layer_request_log(
    path: str,
    request_id: str,
    trace_id: str,
    status: str,
    t0: float,
    workspace_marker: str,
) -> None:
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    LOG.info(
        "CONTEXT_LAYER request path=%s request_id=%s trace_id=%s status=%s workspace=%s duration_ms=%.2f",
        path,
        request_id,
        trace_id,
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
            ver: dict = {
                "package": "motadata-context-layer",
                "package_version": _package_version(),
                "service_version": "v0.1",
                "evidence_schema_hint": "layer5.evidence_bundle.v1",
                "endpoints": [
                    "GET /healthz",
                    "GET /version",
                    "POST /v1/export_evidence",
                ],
            }
            ver.update(layer5_build_info())
            ic = _get_workspace_index_cache()
            if ic is not None:
                ver["index_cache_entries"] = ic.entry_count()
            self._send_json(200, ver)
            return
        self._send_json(404, _error_payload("not_found", "Not found", failure_class="route_not_found"))

    def do_POST(self) -> None:
        t0 = time.perf_counter()
        path = self.path
        if path != _EXPORT_PATH:
            self._send_json(404, _error_payload("not_found", "Not found", failure_class="route_not_found"))
            _context_layer_request_log(path, "unknown", "(none)", "error", t0, "n/a")
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
            _context_layer_request_log(_EXPORT_PATH, "unknown", "(none)", "error", t0, "n/a")
            return

        rid = _request_id_from_body(data)
        tid = _trace_id_from_body(data)
        raw_workspace = (data.get("workspace_root") or data.get("workspace") or "").strip()
        normalized = _normalize_workspace_root(raw_workspace)
        workspace, ws_substituted = _effective_export_workspace(normalized)
        # One line per request so operators can confirm traffic hits this process (stderr or MOTADATA_CONTEXT_LAYER_LOG_PATH).
        LOG.info(
            "CONTEXT_LAYER export_evidence begin request_id=%s trace_id=%s substituted=%s effective_workspace=%s peer=%s",
            rid,
            tid,
            ws_substituted,
            _workspace_marker(workspace),
            self.client_address,
        )
        if ws_substituted:
            LOG.info(
                "CONTEXT_LAYER export_evidence workspace substituted request_id=%s "
                "(JetBrains Roaming path → MOTADATA_ROOT / workspace file / ~/Projects/Motadata / ~/Motadata)",
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
            _context_layer_request_log(_EXPORT_PATH, rid, tid, "error", t0, wmark)
            return

        index_metrics: dict = {}
        try:
            bundle = export_evidence_bundle_dict(
                workspace,
                query,
                top_k=top_k,
                index_cache=_get_workspace_index_cache(),
                index_cache_metrics=index_metrics,
            )
        except ValueError as e:
            self._send_json(
                400,
                _error_payload("invalid_request", str(e), failure_class="invalid_request"),
            )
            _context_layer_request_log(_EXPORT_PATH, rid, tid, "error", t0, wmark)
            return
        except RuntimeError as e:
            # Service is healthy; workspace/index/export could not complete — not "service absent"
            msg = str(e)
            if "Workspace root does not exist" in msg:
                fb = _resolve_fallback_workspace()
                LOG.warning(
                    "CONTEXT_LAYER export_failed_workspace request_id=%s substituted=%s "
                    "effective_marker=%s fallback_resolved_nonempty=%s peer=%s error=%s",
                    rid,
                    ws_substituted,
                    _workspace_marker(workspace),
                    bool(fb),
                    self.client_address,
                    msg[:800],
                )
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
            _context_layer_request_log(_EXPORT_PATH, rid, tid, "error", t0, wmark)
            return
        except Exception as e:
            LOG.exception("Unexpected export error")
            self._send_json(
                500,
                _error_payload("internal_error", str(e), failure_class="internal_error"),
            )
            _context_layer_request_log(_EXPORT_PATH, rid, tid, "error", t0, wmark)
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
            _context_layer_request_log(_EXPORT_PATH, rid, tid, "error", t0, wmark)
            return
        except Exception as e:
            LOG.exception("Schema validation unexpected error")
            self._send_json(
                500,
                _error_payload("internal_error", str(e), failure_class="internal_error"),
            )
            _context_layer_request_log(_EXPORT_PATH, rid, tid, "error", t0, wmark)
            return

        self._send_json(200, bundle)
        if index_metrics:
            LOG.info(
                "CONTEXT_LAYER index_cache request_id=%s index_cache_hit=%s "
                "file_index_build_ms=%.2f code_index_build_ms=%.2f",
                rid,
                index_metrics.get("index_cache_hit"),
                float(index_metrics.get("file_index_build_ms", 0.0)),
                float(index_metrics.get("code_index_build_ms", 0.0)),
            )
        _context_layer_request_log(_EXPORT_PATH, rid, tid, "success", t0, wmark)

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

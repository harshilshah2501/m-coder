"""
Layer-5 Local API skeleton implementation.

This module provides a minimal reference implementation of the Layer-5 local API.
It can be:
- Used directly as a simple HTTP server
- Extended/subclassed for production use
- Used as documentation for expected behavior

The skeleton is deliberately minimal: no external dependencies beyond stdlib.
Production implementations may use FastAPI, Flask, etc.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from runtime.layer5.api.contracts import (
    HealthResponse,
    IndexState,
    IndexStatusRequest,
    IndexStatusResponse,
    WorkspaceResolveRequest,
    WorkspaceResolveResponse,
)
from runtime.layer5.workspace.resolver import WorkspaceResolver, ResolverConfig


@dataclass
class ApiConfig:
    """Configuration for the API skeleton."""

    host: str = "127.0.0.1"
    port: int = 8090
    resolver_config: Optional[ResolverConfig] = None
    version: str = "0.1.0"


class Layer5ApiSkeleton:
    """
    Minimal Layer-5 local API implementation.

    Endpoints:
        GET  /healthz                   Health check
        GET  /health                    Health check (alias)
        POST /v1/workspace/resolve      Resolve workspace identity
        POST /v1/index/status           Query index status (stub)

    This is a skeleton/reference implementation. For production:
    - Consider using FastAPI or similar framework
    - Add proper logging, metrics, auth
    - Implement actual index status tracking (A4 responsibility)
    """

    def __init__(self, config: Optional[ApiConfig] = None):
        """Initialize API with optional configuration."""
        self.config = config or ApiConfig()
        resolver_config = self.config.resolver_config or ResolverConfig()
        self.resolver = WorkspaceResolver(resolver_config)
        self._index_status_callback: Optional[Callable[[str], IndexStatusResponse]] = None

    def set_index_status_callback(
        self, callback: Callable[[str], IndexStatusResponse]
    ) -> None:
        """
        Set callback for index status queries.

        This allows A4 (indexing) to plug in actual status tracking.
        The callback receives workspace_identity_hash and returns IndexStatusResponse.
        """
        self._index_status_callback = callback

    def handle_healthz(self) -> Tuple[int, Dict[str, Any]]:
        """Handle GET /healthz endpoint."""
        response = HealthResponse(
            status="ok",
            version=self.config.version,
            components={
                "workspace_resolver": "ok",
                "index_status": "ok" if self._index_status_callback else "stub",
            },
        )
        return 200, response.to_dict()

    def handle_workspace_resolve(
        self, request_data: Dict[str, Any]
    ) -> Tuple[int, Dict[str, Any]]:
        """Handle POST /v1/workspace/resolve endpoint."""
        request = WorkspaceResolveRequest.from_dict(request_data)

        if not request.input_path:
            response = WorkspaceResolveResponse(
                success=False,
                error_code="invalid_request",
                error_message="input_path is required",
            )
            return 400, response.to_dict()

        # Configure resolver based on request
        config = ResolverConfig(
            require_git=request.require_git,
            resolve_symlinks=True,
        )
        resolver = WorkspaceResolver(config)

        identity, error = resolver.resolve(request.input_path)

        if error:
            response = WorkspaceResolveResponse.from_error(error)
            return 400, response.to_dict()

        response = WorkspaceResolveResponse.from_identity(identity)

        # Optionally exclude revision metadata
        if not request.include_revision:
            response.revision = None

        return 200, response.to_dict()

    def handle_index_status(
        self, request_data: Dict[str, Any]
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Handle POST /v1/index/status endpoint.

        Returns stub response unless index_status_callback is set by A4.
        """
        request = IndexStatusRequest.from_dict(request_data)

        if not request.workspace_identity_hash and not request.canonical_root:
            response = IndexStatusResponse(
                state=IndexState.UNKNOWN,
                error_message="workspace_identity_hash or canonical_root required",
            )
            return 400, response.to_dict()

        # Resolve canonical_root to identity_hash if needed
        identity_hash = request.workspace_identity_hash
        if not identity_hash and request.canonical_root:
            from runtime.layer5.workspace.identity import WorkspaceIdentity
            identity_hash = WorkspaceIdentity.compute_identity_hash(request.canonical_root)

        # Delegate to callback if available (A4 responsibility)
        if self._index_status_callback:
            response = self._index_status_callback(identity_hash)
            return 200, response.to_dict()

        # Stub response: A4 has not plugged in actual tracking
        response = IndexStatusResponse(
            workspace_identity_hash=identity_hash,
            state=IndexState.NOT_INDEXED,
            file_count=0,
        )
        return 200, response.to_dict()

    def create_handler_class(self) -> type:
        """Create HTTP request handler class bound to this API instance."""
        api = self

        class Layer5Handler(BaseHTTPRequestHandler):
            """HTTP request handler for Layer-5 API."""

            def _send_json_response(self, status: int, data: Dict[str, Any]) -> None:
                """Send JSON response."""
                body = json.dumps(data, indent=2).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _read_json_body(self) -> Dict[str, Any]:
                """Read and parse JSON request body."""
                content_length = int(self.headers.get("Content-Length", 0))
                if content_length == 0:
                    return {}
                body = self.rfile.read(content_length)
                return json.loads(body.decode("utf-8"))

            def do_GET(self) -> None:
                """Handle GET requests."""
                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/")

                if path in ("/healthz", "/health"):
                    status, data = api.handle_healthz()
                    self._send_json_response(status, data)
                else:
                    self._send_json_response(404, {"error": "not_found", "path": path})

            def do_POST(self) -> None:
                """Handle POST requests."""
                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/")

                try:
                    request_data = self._read_json_body()
                except json.JSONDecodeError as e:
                    self._send_json_response(400, {"error": "invalid_json", "message": str(e)})
                    return

                if path == "/v1/workspace/resolve":
                    status, data = api.handle_workspace_resolve(request_data)
                    self._send_json_response(status, data)
                elif path == "/v1/index/status":
                    status, data = api.handle_index_status(request_data)
                    self._send_json_response(status, data)
                else:
                    self._send_json_response(404, {"error": "not_found", "path": path})

            def log_message(self, format: str, *args) -> None:
                """Suppress default logging."""
                pass

        return Layer5Handler

    def serve(self, blocking: bool = True) -> HTTPServer:
        """
        Start HTTP server.

        Args:
            blocking: If True, blocks until server is stopped.
                     If False, returns server instance for manual control.

        Returns:
            HTTPServer instance.
        """
        handler_class = self.create_handler_class()
        server = HTTPServer((self.config.host, self.config.port), handler_class)
        print(f"Layer-5 API serving on http://{self.config.host}:{self.config.port}")

        if blocking:
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\nShutting down...")
                server.shutdown()

        return server


def run_api_server(
    host: str = "127.0.0.1",
    port: int = 8090,
    version: str = "0.1.0",
) -> None:
    """
    Convenience function to run the API server.

    Usage:
        python -m runtime.layer5.api.skeleton
        # or
        from runtime.layer5.api.skeleton import run_api_server
        run_api_server(port=8090)
    """
    config = ApiConfig(host=host, port=port, version=version)
    api = Layer5ApiSkeleton(config)
    api.serve(blocking=True)


if __name__ == "__main__":
    run_api_server()

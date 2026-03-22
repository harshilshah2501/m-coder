"""Context Layer HTTP service — configuration (stdlib)."""

from __future__ import annotations

import os


def get_bind_host() -> str:
    return (
        os.environ.get("MOTADATA_CONTEXT_LAYER_HOST")
        or os.environ.get("CONTEXT_LAYER_HOST")
        or "127.0.0.1"
    ).strip() or "127.0.0.1"


def get_port() -> int:
    return int(
        os.environ.get(
            "CONTEXT_LAYER_PORT",
            os.environ.get("MOTADATA_CONTEXT_LAYER_PORT", "8091"),
        )
    )


def get_package_version() -> str:
    try:
        from importlib.metadata import version

        return version("motadata-context-layer")
    except Exception:
        return "unknown"

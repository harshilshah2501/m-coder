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


def _env_truthy(name: str, default: bool) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    if not raw:
        return default
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    return default


def index_cache_enabled() -> bool:
    """Default on for Context Layer service; set MOTADATA_CONTEXT_LAYER_INDEX_CACHE=0 to disable."""
    return _env_truthy("MOTADATA_CONTEXT_LAYER_INDEX_CACHE", True)


def index_cache_max_keys() -> int:
    try:
        return max(1, int(os.environ.get("MOTADATA_CONTEXT_LAYER_INDEX_CACHE_MAX_KEYS", "4")))
    except ValueError:
        return 4


def index_cache_ttl_sec() -> float:
    """0 = no time-based expiry (key + dirty bypass + process restart only)."""
    try:
        return float(os.environ.get("MOTADATA_CONTEXT_LAYER_INDEX_CACHE_TTL_SEC", "0"))
    except ValueError:
        return 0.0


def allow_dirty_cache() -> bool:
    """Default off. Set MOTADATA_CONTEXT_LAYER_ALLOW_DIRTY_CACHE=1 for dev speed."""
    return _env_truthy("MOTADATA_CONTEXT_LAYER_ALLOW_DIRTY_CACHE", False)

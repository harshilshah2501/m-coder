from __future__ import annotations

from datetime import datetime, timezone


def local_scheme(version) -> str:
    """
    Create a unique local version suffix per build.

    Example: +g1a2b3c4.b20260430063215
    """
    node = str(getattr(version, "node", "") or "").lstrip("g") or "nogit"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"+g{node}.b{stamp}"

"""Forward to stage6.stage6c.reporting.render."""
from __future__ import annotations

from stage6.stage6c.reporting import render as _render

__all__ = [x for x in dir(_render) if not x.startswith("_")]
globals().update({n: getattr(_render, n) for n in __all__})

"""Forward to stage6.stage6c.reporting.gates."""
from __future__ import annotations

from stage6.stage6c.reporting import gates as _gates

# Re-export all public names
__all__ = [x for x in dir(_gates) if not x.startswith("_")]
globals().update({n: getattr(_gates, n) for n in __all__})

"""
Shannon entropy for verdict distribution — Judge Drift Regression Suite v1.1.

No external heavy dependencies. Handles counts or probabilities.
"""

from __future__ import annotations

import logging
import math
from typing import Any

_logger = logging.getLogger(__name__)


def _log_structured(event: str, payload: dict[str, Any]) -> None:
    _logger.info("%s", {"event": event, **payload})


def compute_entropy(distribution: dict) -> float:
    """
    Shannon entropy H = -sum(p * log2(p)) for p > 0.
    distribution: outcome label -> count or probability. Counts are normalized to probabilities.
    Empty dict or zero total returns 0.0.
    """
    if not distribution:
        _log_structured("entropy", {"value": 0.0})
        return 0.0
    total = sum(distribution.values())
    if total <= 0:
        _log_structured("entropy", {"value": 0.0})
        return 0.0
    h = 0.0
    for v in distribution.values():
        if v <= 0:
            continue
        p = v / total if total != 0 else 0.0
        if p > 0:
            h -= p * math.log2(p)
    _log_structured("entropy", {"value": h})
    return h

"""
Load thresholds.yaml for use by weekly_report. No policy logic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_thresholds() -> dict[str, Any]:
    """Load thresholds.yaml from suite directory. Return dict; empty if missing."""
    base = Path(__file__).resolve().parent
    path = base / "thresholds.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data or {}

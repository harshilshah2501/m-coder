"""Plan-Gate Service configuration from env or defaults."""

from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # runtime/
ROOT = Path(__file__).resolve().parents[3]  # repo root
DEFAULT_SPOOL = REPO / ".spool" / "plan_gate"


def get_port() -> int:
    return int(os.environ.get("PLAN_GATE_PORT", "8089"))


def get_spool_dir() -> Path:
    s = os.environ.get("PLAN_GATE_SPOOL_DIR")
    if s:
        return Path(s)
    return DEFAULT_SPOOL


def get_mode() -> str:
    m = os.environ.get("PLAN_GATE_MODE", "shadow")
    return m if m in ("shadow", "live") else "shadow"


def get_fixed_time() -> str | None:
    return os.environ.get("PLAN_GATE_FIXED_TIME") or None


def get_lineage_index() -> Path | None:
    s = os.environ.get("PLAN_GATE_LINEAGE_INDEX")
    if not s:
        return None
    p = Path(s)
    if p.is_absolute():
        return p if p.exists() else None
    return (ROOT / p) if (ROOT / p).exists() else None


def get_deterministic() -> bool:
    v = os.environ.get("PLAN_GATE_DETERMINISTIC", "true")
    return v.lower() in ("true", "1", "yes")

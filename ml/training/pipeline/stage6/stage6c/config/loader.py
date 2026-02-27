"""
Load and validate Phase-6C harness config from YAML or JSON.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .schema import HarnessConfig, VALID_CARRYOVER_MODES, VALID_HORIZONS, VALID_SHAPES


def load_config(path: str | Path) -> HarnessConfig:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    raw = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml
            data = yaml.safe_load(raw)
        except ImportError:
            raise RuntimeError("PyYAML required for .yaml config; install pyyaml or use .json")
    else:
        data = json.loads(raw)
    return _dict_to_config(data)


def _dict_to_config(data: Dict[str, Any]) -> HarnessConfig:
    if not isinstance(data, dict):
        raise ValueError("Config must be a dict")
    seeds_dir = data.get("seeds_dir")
    if not seeds_dir:
        raise ValueError("Config must include seeds_dir")
    horizons = data.get("horizons", [3, 4, 6])
    shapes = data.get("shapes", ["linear", "retry_biased"])
    carryover_modes = data.get("carryover_modes", ["cold_start", "full_transcript"])
    injection_profiles = data.get("injection_profiles", ["none"])
    max_transcript_chars = data.get("max_transcript_chars")
    full_transcript_policy = data.get("full_transcript_policy", "include_wrappers")
    return HarnessConfig(
        seeds_dir=str(seeds_dir),
        horizons=list(horizons),
        shapes=list(shapes),
        carryover_modes=list(carryover_modes),
        injection_profiles=list(injection_profiles),
        max_transcript_chars=int(max_transcript_chars) if max_transcript_chars is not None else None,
        full_transcript_policy=str(full_transcript_policy),
    )


def validate_config(config: HarnessConfig) -> None:
    """Re-validate config (e.g. after programmatic changes)."""
    for n in config.horizons:
        if n not in VALID_HORIZONS:
            raise ValueError(f"Invalid horizon: {n}")
    for s in config.shapes:
        if s not in VALID_SHAPES:
            raise ValueError(f"Invalid shape: {s}")
    for c in config.carryover_modes:
        if c not in VALID_CARRYOVER_MODES:
            raise ValueError(f"Invalid carryover_mode: {c}")

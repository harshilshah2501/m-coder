"""
File-based seed registry: directory of JSON files, one per seed_id.
Read-only; returns immutable SeedView. No PHASE4 content in code.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .registry import SeedRegistry, SeedView


def _validate_seed_data(seed_id: str, data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{seed_id}: root must be a dict")
    for key in ("governance_system_messages", "seed_system_messages", "seed_user_messages", "seed_metadata"):
        if key not in data:
            raise ValueError(f"{seed_id}: missing required key {key!r}")
    if "expected_phase" not in data.get("seed_metadata", {}):
        raise ValueError(f"{seed_id}: seed_metadata must include expected_phase")
    for key in ("governance_system_messages", "seed_system_messages", "seed_user_messages"):
        if not isinstance(data[key], list):
            raise ValueError(f"{seed_id}: {key} must be a list")
        for i, item in enumerate(data[key]):
            if not isinstance(item, str):
                raise ValueError(f"{seed_id}: {key}[{i}] must be string")


class FileSeedRegistry(SeedRegistry):
    """
    Load seeds from a directory of JSON files.
    Filename = {seed_id}.json (e.g. BASE-001-V2.json).
    """

    def __init__(self, seeds_dir: str | Path) -> None:
        self._dir = Path(seeds_dir)
        if not self._dir.is_dir():
            raise FileNotFoundError(f"Seeds dir is not a directory: {self._dir}")
        self._cache: dict[str, SeedView] = {}

    def get(self, seed_id: str) -> Optional[SeedView]:
        # Normalize: allow BASE-001-V2 or BASE-001-V2.json
        base = seed_id if not seed_id.endswith(".json") else seed_id[:-5]
        path = self._dir / f"{base}.json"
        if not path.exists():
            return None
        if base not in self._cache:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
            _validate_seed_data(base, data)
            self._cache[base] = SeedView(
                seed_id=base,
                governance_system_messages=data["governance_system_messages"],
                seed_system_messages=data["seed_system_messages"],
                seed_user_messages=data["seed_user_messages"],
                seed_metadata=data["seed_metadata"],
            )
        return self._cache[base]

    def list_seed_ids(self) -> List[str]:
        out = []
        for p in self._dir.iterdir():
            if p.suffix == ".json" and p.name != ".json":
                out.append(p.stem)
        return sorted(out)

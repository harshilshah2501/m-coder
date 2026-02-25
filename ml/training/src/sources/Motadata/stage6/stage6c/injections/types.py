"""
Types for injection profiles. Wrapper messages are origin-tagged "wrapper" and
do not mutate or override governance or seed content.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

# PromptMessage = dict with role, content, origin (wrapper adds origin="wrapper")
PromptMessage = Dict[str, Any]

# Generator: (step_index, step_role, horizon_N, shape, run_id) -> list of content strings (user-facing injection text)
InjectionGenerator = Callable[[int, str, int, str, str], List[str]]


@dataclass
class WrapperState:
    """Immutable context passed to wrapper application. No mutation of seed/governance."""
    run_id: str
    horizon_N: int
    shape: str
    step_index: int
    step_role: str
    injection_profile_id: str
    # Optional: for future per-run seeding (deterministic from run_id)
    seed_hash: int = 0


@dataclass
class InjectionProfile:
    """A named injection profile: id and deterministic generator."""
    id: str
    description: str
    generate: InjectionGenerator  # (step_index, step_role, horizon_N, shape, run_id) -> List[str]

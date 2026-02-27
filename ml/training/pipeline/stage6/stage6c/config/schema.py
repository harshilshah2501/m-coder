"""
Phase-6C config schema and validation.
Canonical step roles ONLY; unknown role strings are rejected.
Injection profile ids must not collide with step role names.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

# Canonical step roles per PHASE6C_DESIGN_SPEC_V1.1 (fixed set)
CANONICAL_STEP_ROLES = frozenset({
    "rehydrate",
    "plan",
    "act_proposal",
    "retry",
    "pressure_escalation",
    "commit_temptation",
})

VALID_HORIZONS = (3, 4, 6)
VALID_SHAPES = ("linear", "retry_biased")
VALID_CARRYOVER_MODES = ("cold_start", "full_transcript", "summary_compressed")
VALID_FULL_TRANSCRIPT_POLICIES = ("step_query_only", "include_wrappers")


@dataclass(frozen=True)
class RunSpecConfig:
    """Configuration for a single run (used by runner)."""
    seed_id: str
    horizon_N: int  # 3, 4, or 6
    shape: str  # linear | retry_biased
    carryover_mode: str  # cold_start | full_transcript | summary_compressed
    injection_profile_id: str  # "none" in M2
    step_role_sequence_override: Optional[List[str]] = None  # if set, must be all canonical roles

    def __post_init__(self) -> None:
        if self.horizon_N not in VALID_HORIZONS:
            raise ValueError(f"horizon_N must be in {VALID_HORIZONS}, got {self.horizon_N}")
        if self.shape not in VALID_SHAPES:
            raise ValueError(f"shape must be in {VALID_SHAPES}, got {self.shape}")
        if self.carryover_mode not in VALID_CARRYOVER_MODES:
            raise ValueError(f"carryover_mode must be in {VALID_CARRYOVER_MODES}, got {self.carryover_mode}")
        if self.step_role_sequence_override is not None:
            for r in self.step_role_sequence_override:
                if r not in CANONICAL_STEP_ROLES:
                    raise ValueError(f"Unknown step role {r!r}; canonical roles: {sorted(CANONICAL_STEP_ROLES)}")
            if len(self.step_role_sequence_override) != self.horizon_N:
                raise ValueError(
                    f"step_role_sequence_override length must equal horizon_N {self.horizon_N}, "
                    f"got {len(self.step_role_sequence_override)}"
                )


@dataclass
class HarnessConfig:
    """Top-level harness configuration."""
    seeds_dir: str
    horizons: List[int] = field(default_factory=lambda: [3, 4, 6])
    shapes: List[str] = field(default_factory=lambda: ["linear", "retry_biased"])
    carryover_modes: List[str] = field(default_factory=lambda: ["cold_start", "full_transcript"])
    injection_profiles: List[str] = field(default_factory=lambda: ["none"])
    max_transcript_chars: Optional[int] = None  # cap for full_transcript; None = no cap
    full_transcript_policy: str = "include_wrappers"  # step_query_only | include_wrappers

    def __post_init__(self) -> None:
        for n in self.horizons:
            if n not in VALID_HORIZONS:
                raise ValueError(f"horizons must be subset of {VALID_HORIZONS}, got {n}")
        for s in self.shapes:
            if s not in VALID_SHAPES:
                raise ValueError(f"shapes must be subset of {VALID_SHAPES}, got {s}")
        for c in self.carryover_modes:
            if c not in VALID_CARRYOVER_MODES:
                raise ValueError(f"carryover_modes must be subset of {VALID_CARRYOVER_MODES}, got {c}")
        if self.full_transcript_policy not in VALID_FULL_TRANSCRIPT_POLICIES:
            raise ValueError(
                f"full_transcript_policy must be in {VALID_FULL_TRANSCRIPT_POLICIES}, got {self.full_transcript_policy!r}"
            )
        for pid in self.injection_profiles:
            if pid in CANONICAL_STEP_ROLES:
                raise ValueError(
                    f"Injection profile id {pid!r} collides with canonical step role. "
                    "Use e.g. commit_push or ship_it_pressure, not commit_temptation."
                )

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal

from ..config.schema import VALID_HORIZONS, VALID_SHAPES, VALID_CARRYOVER_MODES


SuiteType = Literal["canonical", "stress"]


@dataclass
class ExperimentConfig:
    """
    High-level experiment configuration for Phase-6C suites.

    This is intentionally separate from HarnessConfig so we can express
    coverage and amplification concerns (repeats per cluster, suite labels, etc.).
    """

    seeds: List[str]
    horizons: List[int] = field(default_factory=lambda: list(VALID_HORIZONS))
    shapes: List[str] = field(default_factory=lambda: list(VALID_SHAPES))
    carryovers: List[str] = field(
        default_factory=lambda: [m for m in VALID_CARRYOVER_MODES if m != "summary_compressed"]
    )
    injection_profiles: List[str] = field(default_factory=lambda: ["none"])

    # Coverage / amplification knobs
    repeats_per_cluster: int = 5
    amplification_k: int = 10
    max_runs_per_cluster: int = 50

    # Suite mapping for injection profiles. Profiles present in both lists
    # are treated as canonical when --suite=canonical and stress when --suite=stress.
    canonical_profiles: List[str] = field(default_factory=list)
    stress_profiles: List[str] = field(default_factory=list)

    # Minimum runs per (profile, carryover) for coverage, before scaling.
    min_runs_per_profile_carryover: int = 20

    def __post_init__(self) -> None:
        # Basic validation against canonical enums
        for n in self.horizons:
            if n not in VALID_HORIZONS:
                raise ValueError(f"horizons must be subset of {VALID_HORIZONS}, got {n}")
        for s in self.shapes:
            if s not in VALID_SHAPES:
                raise ValueError(f"shapes must be subset of {VALID_SHAPES}, got {s}")
        for c in self.carryovers:
            if c not in VALID_CARRYOVER_MODES:
                raise ValueError(f"carryovers must be subset of {VALID_CARRYOVER_MODES}, got {c}")


def profile_suite(profile_id: str, cfg: ExperimentConfig) -> SuiteType:
    """
    Map injection_profile_id to suite label.

    - If profile is explicitly in stress_profiles -> "stress"
    - Else if explicitly in canonical_profiles -> "canonical"
    - Else default to "canonical".
    """
    if profile_id in cfg.stress_profiles:
        return "stress"
    if profile_id in cfg.canonical_profiles:
        return "canonical"
    return "canonical"


@dataclass
class CoverageDeficit:
    """Single coverage deficit item for diagnostics."""

    axis: str
    key: str
    required: int
    actual: int


@dataclass
class CoverageReport:
    """Summary of coverage validation."""

    total_planned_runs: int
    deficits: List[CoverageDeficit] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.deficits


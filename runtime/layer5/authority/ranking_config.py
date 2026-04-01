"""
Ranking Configuration.

Defines boost/penalty values and feature flags for authority-aware ranking.

Phase 3: Ranking logic configuration. No Plan-Gate changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet


@dataclass(frozen=True)
class RankingConfig:
    """Configuration for authority-aware ranking."""

    # Feature flag
    enable_authority_reranking: bool = True

    # Owner boost values (based on authority status)
    owner_boost_validated: float = 100.0
    owner_boost_stale_candidate: float = 40.0
    owner_boost_unverified: float = 30.0
    owner_boost_stale: float = 0.0

    # Collaborator boost
    collaborator_boost: float = 25.0

    # Structural proximity boosts (supportive only)
    caller_boost: float = 15.0  # Direct caller of owner
    callee_boost: float = 10.0  # Direct callee of owner
    same_package_boost: float = 5.0

    # Entry point boost (supportive, not overriding)
    entry_point_boost: float = 12.0  # Entry point linked to owner
    entry_point_invokes_owner_boost: float = 8.0  # Entry point invokes owner

    # Distractor penalties
    distractor_penalty: float = -80.0

    # Generic distractor patterns (conservative)
    generic_distractor_patterns: FrozenSet[str] = field(
        default_factory=lambda: frozenset({
            "integration",
            "wrapper",
            "constants",
            "config",
            "util",
            "utils",
            "helper",
            "helpers",
        })
    )
    generic_distractor_penalty: float = -20.0

    # Minimum score floor (prevent going too negative)
    min_score: float = 0.0

    def get_owner_boost(self, authority_status: str) -> float:
        """Get owner boost based on authority status."""
        status_lower = authority_status.lower()
        if status_lower == "validated":
            return self.owner_boost_validated
        elif status_lower == "stale_candidate":
            return self.owner_boost_stale_candidate
        elif status_lower == "unverified":
            return self.owner_boost_unverified
        else:  # stale or unknown
            return self.owner_boost_stale


# Default configuration instance
DEFAULT_CONFIG = RankingConfig()


def get_config() -> RankingConfig:
    """Get the default ranking configuration."""
    return DEFAULT_CONFIG

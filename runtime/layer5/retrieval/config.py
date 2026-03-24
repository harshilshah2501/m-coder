"""
Retrieval configuration (weights and safety limits).
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping, Tuple


RETRIEVAL_POLICY_VERSION: Final[str] = "retrieval_policy.v2"
"""
Versioned deterministic policy identifier.
Any change to policy weights/thresholds requires a new version and re-validation.
"""


RETRIEVAL_POLICY_V1: Final[Mapping[str, object]] = MappingProxyType(
    {
        "path_prior": MappingProxyType(
            {
                "core_aiops_code": 5.0,
                "supporting_prod_code": 2.0,
                "config": -1.0,
                "tests": -4.0,
                "logs": -5.0,
                "vendor_static": -6.0,
                "generated_metrics_data": -5.0,
            }
        ),
        "subsystem_boost": 2.5,
        "symbol_boost": 3.0,
        "module_bias": 1.5,
        "noise_penalty_multiplier": 1.0,
    }
)
"""
Immutable policy weights for deterministic runs (PR-1 baseline).
This object must be treated as read-only during a validation run.
"""

RETRIEVAL_POLICY_V2: Final[Mapping[str, object]] = MappingProxyType(
    {
        "path_prior": MappingProxyType(
            {
                "core_aiops_code": 6.5,
                "supporting_prod_code": 2.3,
                "config": -1.2,
                "tests": -4.6,
                "logs": -5.6,
                "vendor_static": -6.8,
                "generated_metrics_data": -5.6,
            }
        ),
        "subsystem_boost": 3.25,
        "symbol_boost": 3.6,
        "module_bias": 1.85,
        "noise_penalty_multiplier": 1.15,
    }
)
"""
PR-4 targeted tuning: stronger core path prior and subsystem/symbol boosts,
slightly stronger noise penalties — deterministic, config-driven.
"""


def get_retrieval_policy(version: str) -> Mapping[str, object]:
    """Resolve immutable policy mapping by version string (audit-friendly)."""
    if version == "retrieval_policy.v1":
        return RETRIEVAL_POLICY_V1
    return RETRIEVAL_POLICY_V2

QUALITY_GATE_VERSION: Final[str] = "quality_gate.v1"
QUALITY_REASON_CODES: Final[Tuple[str, ...]] = (
    "LOW_CORE_RATIO",
    "LOW_CODE_RATIO",
    "NO_CORE_IN_TOP3",
    "NO_SYMBOL_MATCH",
    "NOISE_DOMINATED",
    "DIVERSITY_VIOLATION",
    "NO_RELEVANT_HITS",
    "QUERY_TOO_GENERIC",
)
QUALITY_GATE_THRESHOLDS_V1: Final[Mapping[str, object]] = MappingProxyType(
    {
        "min_core_ratio_code_intent": 0.30,
        "min_code_ratio_code_intent": 0.60,
        "require_core_in_top3_code_intent": True,
        "max_consecutive_noise": 2,
        "noise_dominated_ratio": 0.60,
    }
)


@dataclass(frozen=True)
class LexicalRetrievalConfig:
    """
    MVP lexical ranking parameters — keep linear and explainable.

    Scoring (see ``lexical.py``): integer sum of weighted substring counts.
    """

    min_token_len: int = 2
    max_content_bytes: int = 262_144
    """Cap per file when reading content for keyword counts (honest bound)."""
    read_file_contents: bool = True
    weight_path: int = 1
    weight_basename: int = 2
    """Extra weight on matches in the file name segment (basename still appears in path)."""
    weight_content: int = 1
    enable_policy_bias: bool = True
    policy_version: str = RETRIEVAL_POLICY_VERSION
    policy_score_scale: int = 2
    """
    Policy weights are fractional in contract docs. To preserve integer retrieval scores
    used by downstream evidence schema, contributions are scaled by this factor.
    """
    enable_top_k_core_correction: bool = True
    """
    When True, apply a minimal deterministic post-rank step so at least one
    ``core_aiops_code`` hit appears in positions 0–2 when such a candidate exists
    in the full ranked list (see ``lexical.py``).
    """

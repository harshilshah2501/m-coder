"""
Retrieval configuration (weights and safety limits).
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, FrozenSet, Mapping, Optional, Tuple


RETRIEVAL_POLICY_VERSION: Final[str] = "retrieval_policy.v5"
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
        "symbol_inventory_exact_boost": 2.8,
        "symbol_inventory_token_boost": 1.4,
        "symbol_inventory_overlap_cap": 3,
        "module_bias": 1.85,
        "noise_penalty_multiplier": 1.15,
    }
)
"""
PR-4 targeted tuning: stronger core path prior and subsystem/symbol boosts,
slightly stronger noise penalties — deterministic, config-driven.
"""

RETRIEVAL_POLICY_V3: Final[Mapping[str, object]] = MappingProxyType(
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
        "symbol_inventory_exact_boost": 2.8,
        "symbol_inventory_token_boost": 1.4,
        "symbol_inventory_overlap_cap": 3,
        "module_bias": 1.85,
        "noise_penalty_multiplier": 1.15,
        # Extra deterministic bias for production Java under code/debug intent (scaled).
        "code_intent_main_java_bonus": 3.5,
    }
)
"""
PR-6 Slice 3: same priors as v2 plus ``code_intent_main_java_bonus`` for ``src/main/java`` code paths.
"""

RETRIEVAL_POLICY_V4: Final[Mapping[str, object]] = MappingProxyType(
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
        "symbol_inventory_exact_boost": 2.8,
        "symbol_inventory_token_boost": 1.4,
        "symbol_inventory_overlap_cap": 3,
        "module_bias": 1.85,
        "noise_penalty_multiplier": 1.15,
        "code_intent_main_java_bonus": 3.5,
        # Slice 4: demote *Constants.java / *Utils.java / … under code/debug intent (scaled).
        "code_intent_support_file_demotion": 5.0,
        # Extra boost per query token that matches a CamelCase stem token in the basename.
        "basename_query_specificity_per_token": 2.0,
        "basename_query_specificity_token_cap": 8,
    }
)
"""
PR-6 Slice 4: owner disambiguation — support-basename demotion + basename/query token overlap.
"""

RETRIEVAL_POLICY_V5: Final[Mapping[str, object]] = MappingProxyType(
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
        "symbol_inventory_exact_boost": 2.8,
        "symbol_inventory_token_boost": 1.4,
        "symbol_inventory_overlap_cap": 3,
        "module_bias": 1.85,
        "noise_penalty_multiplier": 1.15,
        "code_intent_main_java_bonus": 3.5,
        "code_intent_support_file_demotion": 5.0,
        "basename_query_specificity_per_token": 2.0,
        "basename_query_specificity_token_cap": 8,
        # Slice 5: demote generic *Integration.java under duplicate-incident queries without integration intent.
        "code_intent_generic_integration_demotion": 8.0,
        # Slice 5: boost core AIOps behavioral names on duplicate+incident queries.
        "code_intent_duplicate_incident_core_boost": 18.0,
        # Slice 5: demote log/*Parser.java when query is ingestion/pipeline-focused (pipeline owner vs log parse).
        "code_intent_ingestion_log_parser_demotion": 30.0,
    }
)
"""
PR-6 Slice 5: mandatory top-1 closure — generic eventbus content cap (topic-gated), util.java support cap,
integration demotion + duplicate-incident core boost.
"""


CODE_INTENT_ZERO_CONTENT_CLASSES_DEFAULT: Final[FrozenSet[str]] = frozenset(
    {"logs", "vendor_static", "generated_metrics_data", "tests"}
)


def get_retrieval_policy(version: str) -> Mapping[str, object]:
    """Resolve immutable policy mapping by version string (audit-friendly)."""
    if version == "retrieval_policy.v1":
        return RETRIEVAL_POLICY_V1
    if version == "retrieval_policy.v2":
        return RETRIEVAL_POLICY_V2
    if version == "retrieval_policy.v3":
        return RETRIEVAL_POLICY_V3
    if version == "retrieval_policy.v4":
        return RETRIEVAL_POLICY_V4
    return RETRIEVAL_POLICY_V5

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
    include_score_diagnostics: bool = False
    """
    When True, each ``RetrievalHit`` includes ``diagnostics`` with integer contributions
    (path/basename/content, path_prior, subsystem, symbol boosts, module_bias, noise).
    """
    code_debug_intent: Optional[bool] = None
    """
    When True/False, force code/debug intent on or off for content gating and main-Java bonus.
    When None (default), intent is inferred from query tokens (see ``infer_code_debug_intent``).
    """
    enable_code_debug_content_gating: bool = True
    """
    When True and code/debug intent is active, content scores from noise file classes are zeroed
    and ``config`` class content may be capped (see ``code_intent_config_content_cap``).
    """
    code_intent_zero_content_classes: FrozenSet[str] = CODE_INTENT_ZERO_CONTENT_CLASSES_DEFAULT
    """File classes whose raw content keyword mass is ignored under code/debug intent."""
    code_intent_config_content_cap: Optional[int] = 80
    """
    When set and intent is active, ``config`` class files contribute at most this many
    raw content points (after ``weight_content``), before other scoring.
    """
    code_intent_support_style_content_cap: Optional[int] = 24
    """
    PR-6 Slice 4: when set and intent is active, ``*Constants.java`` / ``*Utils.java`` / …
    (see ``is_support_style_java_basename``) cap raw content contribution so behavioral
    owners can outrank broad support files. Kept low so keyword-heavy constant pools
    cannot dominate.
    """
    code_intent_generic_facade_content_cap: Optional[int] = 220
    """
    PR-6 Slice 5: when set and code/debug intent is active, cap effective content for
    generic ``eventbus`` handler slots that lack direct owner evidence, only when the
    query is topology- or ingestion-focused (see ``query_topology_focus`` /
    ``query_ingestion_focus``). Prevents broad handlers from winning top-1 on raw mass alone.
    """

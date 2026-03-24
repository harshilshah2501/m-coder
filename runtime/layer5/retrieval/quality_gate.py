"""
Deterministic evidence quality gate over retrieved/context file paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from runtime.layer5.retrieval.config import (
    QUALITY_GATE_THRESHOLDS_V1,
    QUALITY_GATE_VERSION,
)
from runtime.layer5.retrieval.intent import (
    CODE_INTENT,
    DEBUG_INTENT,
    GENERIC_INTENT,
    PLAN_INTENT,
    classify_intent,
)
from runtime.layer5.retrieval.policy import classify_file, is_noise_class

STRONG = "STRONG"
WEAK = "WEAK"
INSUFFICIENT = "INSUFFICIENT"
NO_MATCH = "NO_MATCH"


@dataclass(frozen=True)
class QualityAssessment:
    intent_type: str
    evidence_quality: str
    quality_reasons: Tuple[str, ...]
    dominance_metrics: Dict[str, float]
    blocked: bool
    policy_version: str


def _max_consecutive_noise(paths: Iterable[str]) -> int:
    run = 0
    max_run = 0
    for p in paths:
        cls = classify_file(p).file_class
        if is_noise_class(cls):
            run += 1
            max_run = max(max_run, run)
        else:
            run = 0
    return max_run


def assess_evidence_quality(query: str, file_paths: List[str]) -> QualityAssessment:
    intent = classify_intent(query)
    paths = list(file_paths)
    n = len(paths)
    if n == 0:
        # No bundle paths: distinguish vague generic probes vs concrete code/debug/plan asks.
        if intent.intent_type == GENERIC_INTENT:
            return QualityAssessment(
                intent_type=intent.intent_type,
                evidence_quality=WEAK,
                quality_reasons=("NO_RELEVANT_HITS", "QUERY_TOO_GENERIC"),
                dominance_metrics={
                    "top_k_size": 0.0,
                    "core_code_in_top_k_pct": 0.0,
                    "code_in_top_k_pct": 0.0,
                    "noise_in_top_k_pct": 0.0,
                    "core_in_top_3_count": 0.0,
                    "max_consecutive_noise": 0.0,
                },
                blocked=False,
                policy_version=QUALITY_GATE_VERSION,
            )
        # CODE_INTENT / DEBUG_INTENT / PLAN_INTENT with zero evidence: nothing to ground on.
        return QualityAssessment(
            intent_type=intent.intent_type,
            evidence_quality=NO_MATCH,
            quality_reasons=("NO_RELEVANT_HITS",),
            dominance_metrics={
                "top_k_size": 0.0,
                "core_code_in_top_k_pct": 0.0,
                "code_in_top_k_pct": 0.0,
                "noise_in_top_k_pct": 0.0,
                "core_in_top_3_count": 0.0,
                "max_consecutive_noise": 0.0,
            },
            blocked=True,
            policy_version=QUALITY_GATE_VERSION,
        )

    classes = [classify_file(p).file_class for p in paths]
    core_count = sum(1 for c in classes if c == "core_aiops_code")
    code_count = sum(1 for c in classes if c in {"core_aiops_code", "supporting_prod_code"})
    noise_count = sum(1 for c in classes if is_noise_class(c))
    core_top3 = sum(1 for c in classes[:3] if c == "core_aiops_code")
    max_noise_run = _max_consecutive_noise(paths)

    core_ratio = core_count / n
    code_ratio = code_count / n
    noise_ratio = noise_count / n

    reasons: List[str] = []
    intent_gated = intent.intent_type in {CODE_INTENT, DEBUG_INTENT, PLAN_INTENT}
    if intent.intent_type == GENERIC_INTENT:
        reasons.append("QUERY_TOO_GENERIC")

    if noise_ratio >= float(QUALITY_GATE_THRESHOLDS_V1["noise_dominated_ratio"]):
        reasons.append("NOISE_DOMINATED")
    if max_noise_run > int(QUALITY_GATE_THRESHOLDS_V1["max_consecutive_noise"]):
        reasons.append("DIVERSITY_VIOLATION")
    if intent.has_symbol_signal:
        if not any(any(tok in p.lower() for tok in intent.symbol_tokens) for p in paths):
            reasons.append("NO_SYMBOL_MATCH")

    if intent_gated:
        if core_ratio < float(QUALITY_GATE_THRESHOLDS_V1["min_core_ratio_code_intent"]):
            reasons.append("LOW_CORE_RATIO")
        if code_ratio < float(QUALITY_GATE_THRESHOLDS_V1["min_code_ratio_code_intent"]):
            reasons.append("LOW_CODE_RATIO")
        if bool(QUALITY_GATE_THRESHOLDS_V1["require_core_in_top3_code_intent"]) and core_top3 < 1:
            reasons.append("NO_CORE_IN_TOP3")

    if code_count == 0:
        quality = NO_MATCH if intent.has_symbol_signal else INSUFFICIENT
        if "NO_RELEVANT_HITS" not in reasons:
            reasons.append("NO_RELEVANT_HITS")
    elif intent.has_symbol_signal and "NO_SYMBOL_MATCH" in reasons:
        # Symbol-specific ask: evidence paths do not contain the requested symbol — not weak grounding.
        quality = NO_MATCH
    elif intent_gated and any(
        r in reasons
        for r in ("LOW_CORE_RATIO", "LOW_CODE_RATIO", "NO_CORE_IN_TOP3", "NOISE_DOMINATED", "DIVERSITY_VIOLATION")
    ):
        quality = WEAK
    elif intent.intent_type == GENERIC_INTENT and noise_ratio >= float(QUALITY_GATE_THRESHOLDS_V1["noise_dominated_ratio"]):
        quality = INSUFFICIENT
    else:
        quality = STRONG

    blocked = quality in {INSUFFICIENT, NO_MATCH}
    return QualityAssessment(
        intent_type=intent.intent_type,
        evidence_quality=quality,
        quality_reasons=tuple(sorted(set(reasons))),
        dominance_metrics={
            "top_k_size": float(n),
            "core_code_in_top_k_pct": round(core_ratio, 4),
            "code_in_top_k_pct": round(code_ratio, 4),
            "noise_in_top_k_pct": round(noise_ratio, 4),
            "core_in_top_3_count": float(core_top3),
            "max_consecutive_noise": float(max_noise_run),
        },
        blocked=blocked,
        policy_version=QUALITY_GATE_VERSION,
    )


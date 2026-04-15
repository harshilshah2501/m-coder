"""
Deterministic evidence quality gate over retrieved/context file paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Tuple

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
from runtime.layer5.retrieval.roles import DISTRACTOR_RISK, PRIMARY_OWNER_CANDIDATE

if TYPE_CHECKING:
    from runtime.layer5.retrieval.effective_intent import EffectiveIntent

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


def _has_strong_symbol_match(path: str, symbol_tokens: Tuple[str, ...]) -> bool:
    """
    Strict no-match guard: avoid treating a single broad fragment as sufficient symbol evidence.
    Strong match is:
    - at least one structured token hit (contains dot/underscore/digit), OR
    - at least two distinct symbol-token overlaps in the same path.
    """
    pl = path.lower()
    matched: List[str] = []
    structured_hit = False
    for tok in symbol_tokens:
        tl = tok.lower().strip()
        if not tl or tl not in pl:
            continue
        matched.append(tl)
        if "." in tl or "_" in tl or any(ch.isdigit() for ch in tl):
            structured_hit = True
    if structured_hit:
        return True
    return len(set(matched)) >= 2


def _refine_with_grounding(
    base: QualityAssessment,
    paths: List[str],
    grounding_entries: List[Tuple[str, str, str]],
) -> QualityAssessment:
    """
    grounding_entries: (relative_path, snippet_selection_reason, retrieval_role)
    """
    n = len(paths)
    if n == 0 or not grounding_entries:
        return base
    by_path = {p: (sr, role) for p, sr, role in grounding_entries}
    distractors = sum(1 for p in paths if by_path.get(p, ("", ""))[1] == DISTRACTOR_RISK)
    primary_owner_hits = sum(1 for p in paths if by_path.get(p, ("", ""))[1] == PRIMARY_OWNER_CANDIDATE)
    weak_snippets = sum(
        1
        for p in paths
        if p in by_path and by_path[p][0] != "query_token_substring_anchor"
    )
    dr = distractors / n
    wr = weak_snippets / n
    reasons = list(base.quality_reasons)
    quality = base.evidence_quality
    if dr >= 0.45:
        reasons.append("HIGH_DISTRACTOR_RATIO")
        if quality == STRONG:
            quality = WEAK
    if wr >= 0.55 and quality == STRONG:
        reasons.append("WEAK_SNIPPET_GROUNDING")
        quality = WEAK
    if primary_owner_hits >= 1 and dr < 0.35 and weak_snippets <= max(1, n // 3):
        if quality == WEAK and "LOW_CORE_RATIO" not in reasons and "NO_SYMBOL_MATCH" not in reasons:
            reasons.append("OWNER_ANCHOR_RECOVERY")
            quality = STRONG
    dom = dict(base.dominance_metrics)
    dom["distractor_ratio"] = round(dr, 4)
    dom["weak_snippet_ratio"] = round(wr, 4)
    dom["primary_owner_hits"] = float(primary_owner_hits)
    blocked = quality in {INSUFFICIENT, NO_MATCH}
    return QualityAssessment(
        intent_type=base.intent_type,
        evidence_quality=quality,
        quality_reasons=tuple(sorted(set(reasons))),
        dominance_metrics=dom,
        blocked=blocked,
        policy_version=base.policy_version,
    )


def assess_evidence_quality(
    query: str,
    file_paths: List[str],
    *,
    grounding_entries: Optional[List[Tuple[str, str, str]]] = None,
    effective_intent: Optional["EffectiveIntent"] = None,
) -> QualityAssessment:
    intent = (
        effective_intent.query_intent
        if effective_intent is not None
        else classify_intent(query)
    )
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
        if not any(_has_strong_symbol_match(p, intent.symbol_tokens) for p in paths):
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
    elif intent.intent_type == GENERIC_INTENT:
        # Generic asks should not be reported as strong grounding.
        quality = WEAK
    else:
        quality = STRONG

    blocked = quality in {INSUFFICIENT, NO_MATCH}
    base = QualityAssessment(
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
    if grounding_entries:
        ge = [(p, sr, r) for p, sr, r in grounding_entries if p in file_paths]
        return _refine_with_grounding(base, paths, ge)
    return base


def operator_hints_for_assessment(assessment: QualityAssessment) -> Tuple[str, ...]:
    """Human-oriented explanations for weak or ambiguous evidence (Plan-Gate metadata)."""
    hints: List[str] = []
    reasons = set(assessment.quality_reasons)
    if "LOW_CORE_RATIO" in reasons:
        hints.append(
            "Fewer than 30% of retrieved paths are classified as core AIOps packages "
            "(e.g. com/mindarray/aiops). Relevant modules may still appear but are diluted by broad support files."
        )
    if "LOW_CODE_RATIO" in reasons:
        hints.append(
            "Low share of production Java paths in top-k; retrieval may be dominated by non-implementation classes."
        )
    if "NO_CORE_IN_TOP3" in reasons:
        hints.append(
            "No core AIOps file in the top-3 ranks; inspect entries below or add domain tokens to the query."
        )
    if "QUERY_TOO_GENERIC" in reasons:
        hints.append(
            "Generic-intent: PLAN_ONLY returns bounded investigation steps (open/search/trace) and ranked files, "
            "not a full how-it-works narrative. For step-by-step implementation detail, use Motadata → Explain/Debug "
            "with relevant Java selected, or ask again naming a concrete class, method, or path."
        )
        if assessment.evidence_quality == STRONG:
            hints.append(
                "STRONG quality here does not imply pinpoint engineering grounding for an open-ended question."
            )
    if "NOISE_DOMINATED" in reasons or "DIVERSITY_VIOLATION" in reasons:
        hints.append(
            "Retrieval window is noisy or repetitive; consider narrowing subsystem or file-class scope."
        )
    return tuple(hints)


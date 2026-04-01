from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

FLOW_TYPES = {"ASK", "DEBUG", "PLAN", "CODE"}
INTENT_TYPES = {"CODE_INTENT", "DEBUG_INTENT", "PLAN_INTENT", "GENERIC_INTENT"}
EVIDENCE_CLASSES = {"STRONG", "WEAK", "INSUFFICIENT", "NO_MATCH"}
PERTURBATION_KINDS = {
    "base",
    "abbreviated_symbol",
    "package_omitted",
    "camelcase_split",
    "error_text_only",
    "active_file_bias",
    "typo_light_wording",
    "subsystem_alias_wording",
    "phrasing_shift",
}
NOISE_BUCKETS = {"logs", "test", "vendor", "generated", "metrics", "docs_non_code"}


@dataclass(frozen=True)
class EvidenceClassExpectation:
    primary: str
    allow: Tuple[str, ...]

    def accepted(self) -> Tuple[str, ...]:
        vals = [self.primary]
        vals.extend(self.allow)
        # stable de-duplication
        return tuple(dict.fromkeys(vals))


@dataclass(frozen=True)
class CaseExpectations:
    must_hit_top1_owner: bool
    must_hit_top3_anchor: bool
    max_first_relevant_rank: int
    max_noise_dominance_top5: float
    min_code_ratio_topk: float
    expect_no_match_honesty: bool


@dataclass(frozen=True)
class CaseContext:
    active_file: Optional[str]
    stacktrace_excerpt: Optional[str]
    selected_paths: Tuple[str, ...]


@dataclass(frozen=True)
class PerturbationInfo:
    family_id: str
    kind: str
    source_case_id: Optional[str]


@dataclass(frozen=True)
class GoldenCase:
    id: str
    flow_type: str
    intent: str
    query: str
    expected_owner: str
    acceptable_anchors: Tuple[str, ...]
    unacceptable_noise: Tuple[str, ...]
    expected_evidence_class: EvidenceClassExpectation
    notes: str
    context: CaseContext
    perturbation: PerturbationInfo
    expectations: CaseExpectations


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _as_str_list(value: Any, field_name: str, required: bool = True) -> List[str]:
    if value is None and not required:
        return []
    _require(isinstance(value, list), f"`{field_name}` must be a list.")
    out: List[str] = []
    for i, v in enumerate(value):
        _require(isinstance(v, str) and v.strip(), f"`{field_name}[{i}]` must be a non-empty string.")
        out.append(v.strip())
    return out


def _validate_evidence_class(raw: Any, case_id: str) -> EvidenceClassExpectation:
    _require(isinstance(raw, dict), f"{case_id}: `expected_evidence_class` must be an object.")
    primary = raw.get("primary")
    allow = raw.get("allow")
    _require(primary in EVIDENCE_CLASSES, f"{case_id}: invalid evidence primary `{primary}`.")
    allow_list = _as_str_list(allow, "expected_evidence_class.allow", required=True)
    for v in allow_list:
        _require(v in EVIDENCE_CLASSES, f"{case_id}: invalid evidence allow value `{v}`.")
        _require(v != primary, f"{case_id}: evidence allow must not duplicate primary `{primary}`.")
    return EvidenceClassExpectation(primary=primary, allow=tuple(allow_list))


def _validate_case(raw: Dict[str, Any]) -> GoldenCase:
    case_id = raw.get("id")
    _require(isinstance(case_id, str) and case_id.strip(), "Each case requires non-empty `id`.")
    case_id = case_id.strip()

    flow_type = raw.get("flow_type")
    intent = raw.get("intent")
    _require(flow_type in FLOW_TYPES, f"{case_id}: invalid `flow_type` `{flow_type}`.")
    _require(intent in INTENT_TYPES, f"{case_id}: invalid `intent` `{intent}`.")

    query = raw.get("query")
    expected_owner = raw.get("expected_owner")
    notes = raw.get("notes")
    _require(isinstance(query, str) and query.strip(), f"{case_id}: `query` must be non-empty string.")
    _require(
        isinstance(expected_owner, str) and expected_owner.strip(),
        f"{case_id}: `expected_owner` must be non-empty string.",
    )
    _require(isinstance(notes, str), f"{case_id}: `notes` must be a string.")

    anchors = _as_str_list(raw.get("acceptable_anchors"), "acceptable_anchors")
    _require(anchors, f"{case_id}: `acceptable_anchors` must have at least 1 entry.")
    noise = _as_str_list(raw.get("unacceptable_noise"), "unacceptable_noise")
    for n in noise:
        _require(n in NOISE_BUCKETS, f"{case_id}: unsupported noise bucket `{n}`.")

    expected_evidence = _validate_evidence_class(raw.get("expected_evidence_class"), case_id)

    raw_context = raw.get("context") or {}
    _require(isinstance(raw_context, dict), f"{case_id}: `context` must be object when present.")
    active_file = raw_context.get("active_file")
    stacktrace_excerpt = raw_context.get("stacktrace_excerpt")
    selected_paths = _as_str_list(raw_context.get("selected_paths"), "context.selected_paths", required=False)
    if active_file is not None:
        _require(isinstance(active_file, str), f"{case_id}: context.active_file must be string when present.")
    if stacktrace_excerpt is not None:
        _require(
            isinstance(stacktrace_excerpt, str),
            f"{case_id}: context.stacktrace_excerpt must be string when present.",
        )
    context = CaseContext(
        active_file=active_file,
        stacktrace_excerpt=stacktrace_excerpt,
        selected_paths=tuple(selected_paths),
    )

    raw_pert = raw.get("perturbation")
    _require(isinstance(raw_pert, dict), f"{case_id}: `perturbation` must be object.")
    family_id = raw_pert.get("family_id")
    kind = raw_pert.get("kind")
    source_case_id = raw_pert.get("source_case_id")
    _require(isinstance(family_id, str) and family_id.strip(), f"{case_id}: `perturbation.family_id` required.")
    _require(kind in PERTURBATION_KINDS, f"{case_id}: invalid perturbation kind `{kind}`.")
    if source_case_id is not None:
        _require(
            isinstance(source_case_id, str) and source_case_id.strip(),
            f"{case_id}: `perturbation.source_case_id` must be non-empty string when present.",
        )
    perturbation = PerturbationInfo(family_id=family_id.strip(), kind=kind, source_case_id=source_case_id)

    raw_exp = raw.get("expectations")
    _require(isinstance(raw_exp, dict), f"{case_id}: `expectations` must be object.")
    try:
        expectations = CaseExpectations(
            must_hit_top1_owner=bool(raw_exp["must_hit_top1_owner"]),
            must_hit_top3_anchor=bool(raw_exp["must_hit_top3_anchor"]),
            max_first_relevant_rank=int(raw_exp["max_first_relevant_rank"]),
            max_noise_dominance_top5=float(raw_exp["max_noise_dominance_top5"]),
            min_code_ratio_topk=float(raw_exp["min_code_ratio_topk"]),
            expect_no_match_honesty=bool(raw_exp["expect_no_match_honesty"]),
        )
    except KeyError as exc:
        raise ValueError(f"{case_id}: missing expectation field `{exc.args[0]}`.") from exc
    _require(expectations.max_first_relevant_rank >= 1, f"{case_id}: `max_first_relevant_rank` must be >= 1.")
    _require(
        0.0 <= expectations.max_noise_dominance_top5 <= 1.0,
        f"{case_id}: `max_noise_dominance_top5` must be in [0,1].",
    )
    _require(0.0 <= expectations.min_code_ratio_topk <= 1.0, f"{case_id}: `min_code_ratio_topk` must be in [0,1].")

    return GoldenCase(
        id=case_id,
        flow_type=flow_type,
        intent=intent,
        query=query.strip(),
        expected_owner=expected_owner.strip(),
        acceptable_anchors=tuple(anchors),
        unacceptable_noise=tuple(noise),
        expected_evidence_class=expected_evidence,
        notes=notes,
        context=context,
        perturbation=perturbation,
        expectations=expectations,
    )


def load_golden_cases(dataset_path: Path) -> List[GoldenCase]:
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "l58.grounded_queries.v1":
        raise ValueError("Unsupported schema_version for L5.8 golden dataset.")
    raw_cases = data.get("cases")
    _require(isinstance(raw_cases, list) and raw_cases, "`cases` must be a non-empty list.")

    parsed = [_validate_case(c) for c in raw_cases]
    ids = [c.id for c in parsed]
    duplicates = sorted({cid for cid in ids if ids.count(cid) > 1})
    _require(not duplicates, f"Duplicate case IDs found: {duplicates}")
    # deterministic order by ID
    return sorted(parsed, key=lambda c: c.id)


def load_thresholds(thresholds_path: Path) -> Dict[str, Dict[str, float]]:
    data = json.loads(thresholds_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "l58.thresholds.v1":
        raise ValueError("Unsupported schema_version for L5.8 thresholds.")
    out: Dict[str, Dict[str, float]] = {}
    for tier in ("hard_fail", "warning"):
        raw = data.get(tier)
        _require(isinstance(raw, dict), f"`{tier}` must be an object.")
        out[tier] = {str(k): float(v) for k, v in raw.items()}
    return out

"""
Offline validation for patch_proposal.v1.

Bounded patch proposal is planning metadata only and must remain
anchored to plan_contract.v1 and code_reasoning_trace.v1 constraints.
"""

from __future__ import annotations

from typing import Any

from runtime.code_reasoning.v1_validate import validate_code_reasoning_trace_v1
from runtime.plan_contract.v1_validate import validate_plan_contract_v1

PATCH_PROPOSAL_SCHEMA_VERSION = "patch_proposal.v1"

EDIT_INTENT_KINDS = frozenset({"edit", "add", "delete", "rename", "verify"})
PATCH_TOP_LEVEL = frozenset(
    {
        "schema_version",
        "proposal_ref",
        "plan_contract_ref",
        "code_reasoning_trace_ref",
        "bounded_scope",
        "proposed_edits",
        "validation_and_risk",
        "test_plan_required",
        "rollback_plan_required",
        "review_requirements",
    }
)

PATCH_PROPOSAL_QUALITY_CATEGORIES = frozenset(
    {
        "clear_and_bounded",
        "missing_rollback",
        "overbound",
        "weak_test_plan",
        "good_reviewer_structure",
    }
)


def _is_non_empty_str(val: Any) -> bool:
    return isinstance(val, str) and bool(val.strip())


def _check_string_list(name: str, val: Any, errs: list[str]) -> None:
    if not isinstance(val, list) or not all(isinstance(x, str) and x.strip() for x in val):
        errs.append(f"{name} must be an array of non-empty strings")


def validate_patch_proposal_v1(
    proposal: Any,
    plan_contract: Any,
    code_reasoning_trace: Any,
) -> list[str]:
    errs: list[str] = []
    errs.extend(validate_plan_contract_v1(plan_contract))
    errs.extend(validate_code_reasoning_trace_v1(code_reasoning_trace, plan_contract))
    if not isinstance(proposal, dict):
        return errs + ["patch_proposal must be a JSON object"]

    unknown = set(proposal.keys()) - PATCH_TOP_LEVEL
    if unknown:
        errs.append(f"patch_proposal unknown top-level keys: {sorted(unknown)}")

    if proposal.get("schema_version") != PATCH_PROPOSAL_SCHEMA_VERSION:
        errs.append(f"patch_proposal.schema_version must be {PATCH_PROPOSAL_SCHEMA_VERSION!r}")

    for key in ("proposal_ref", "plan_contract_ref", "code_reasoning_trace_ref"):
        if not _is_non_empty_str(proposal.get(key)):
            errs.append(f"patch_proposal.{key} must be a non-empty string")

    bs = proposal.get("bounded_scope")
    if not isinstance(bs, dict):
        errs.append("patch_proposal.bounded_scope must be an object")
    else:
        for key in ("max_files_touched", "max_diff_lines", "allowed_paths", "forbidden_paths"):
            if key not in bs:
                errs.append(f"patch_proposal.bounded_scope.{key} is required")
        try:
            max_files = int(bs.get("max_files_touched"))
            max_lines = int(bs.get("max_diff_lines"))
            if max_files < 0:
                errs.append("patch_proposal.bounded_scope.max_files_touched must be >= 0")
            if max_lines < 0:
                errs.append("patch_proposal.bounded_scope.max_diff_lines must be >= 0")
        except (TypeError, ValueError):
            errs.append("patch_proposal.bounded_scope.max_files_touched and max_diff_lines must be integers")
            max_files = -1
            max_lines = -1
        _check_string_list("patch_proposal.bounded_scope.allowed_paths", bs.get("allowed_paths"), errs)
        _check_string_list("patch_proposal.bounded_scope.forbidden_paths", bs.get("forbidden_paths"), errs)

        cb = (
            plan_contract.get("change_boundaries")
            if isinstance(plan_contract, dict) and isinstance(plan_contract.get("change_boundaries"), dict)
            else {}
        )
        try:
            plan_max_files = int(cb.get("max_files_touched", 0))
            plan_max_lines = int(cb.get("max_diff_lines_hint", 0))
        except (TypeError, ValueError):
            plan_max_files = 0
            plan_max_lines = 0
        if max_files > plan_max_files:
            errs.append("patch_proposal.bounded_scope.max_files_touched exceeds plan_contract boundary")
        if max_lines > plan_max_lines:
            errs.append("patch_proposal.bounded_scope.max_diff_lines exceeds plan_contract boundary")

    edits = proposal.get("proposed_edits")
    if not isinstance(edits, list):
        errs.append("patch_proposal.proposed_edits must be an array")
    else:
        if isinstance(bs, dict):
            try:
                max_files = int(bs.get("max_files_touched", 0))
            except (TypeError, ValueError):
                max_files = 0
            if len(edits) > max_files:
                errs.append("patch_proposal.proposed_edits exceeds bounded_scope.max_files_touched")
        for i, row in enumerate(edits):
            if not isinstance(row, dict):
                errs.append(f"patch_proposal.proposed_edits[{i}] must be an object")
                continue
            if not _is_non_empty_str(row.get("path")):
                errs.append(f"patch_proposal.proposed_edits[{i}].path must be a non-empty string")
            kind = row.get("intent")
            if kind not in EDIT_INTENT_KINDS:
                errs.append(
                    f"patch_proposal.proposed_edits[{i}].intent must be one of {sorted(EDIT_INTENT_KINDS)} got {kind!r}"
                )
            if not _is_non_empty_str(row.get("rationale")):
                errs.append(f"patch_proposal.proposed_edits[{i}].rationale must be a non-empty string")

    vr = proposal.get("validation_and_risk")
    if not isinstance(vr, dict):
        errs.append("patch_proposal.validation_and_risk must be an object")
    else:
        for key in ("risk_class", "key_risks", "assumptions"):
            if key not in vr:
                errs.append(f"patch_proposal.validation_and_risk.{key} is required")
        if not _is_non_empty_str(vr.get("risk_class")):
            errs.append("patch_proposal.validation_and_risk.risk_class must be a non-empty string")
        _check_string_list("patch_proposal.validation_and_risk.key_risks", vr.get("key_risks"), errs)
        _check_string_list("patch_proposal.validation_and_risk.assumptions", vr.get("assumptions"), errs)

    tpr = proposal.get("test_plan_required")
    if not isinstance(tpr, dict):
        errs.append("patch_proposal.test_plan_required must be an object")
    else:
        _check_string_list("patch_proposal.test_plan_required.required_checks", tpr.get("required_checks"), errs)
        if not _is_non_empty_str(tpr.get("pass_fail_criteria")):
            errs.append("patch_proposal.test_plan_required.pass_fail_criteria must be a non-empty string")

    rpr = proposal.get("rollback_plan_required")
    if not isinstance(rpr, dict):
        errs.append("patch_proposal.rollback_plan_required must be an object")
    else:
        if not _is_non_empty_str(rpr.get("strategy")):
            errs.append("patch_proposal.rollback_plan_required.strategy must be a non-empty string")
        _check_string_list("patch_proposal.rollback_plan_required.safety_checks", rpr.get("safety_checks"), errs)

    rr = proposal.get("review_requirements")
    if not isinstance(rr, dict):
        errs.append("patch_proposal.review_requirements must be an object")
    else:
        if rr.get("human_review_required") is not True:
            errs.append("patch_proposal.review_requirements.human_review_required must be true")
        _check_string_list("patch_proposal.review_requirements.checklist", rr.get("checklist"), errs)

    return errs


def validate_patch_proposal_quality_category(
    proposal: dict[str, Any],
    plan_contract: dict[str, Any],
    code_reasoning_trace: dict[str, Any],
    category: str,
) -> list[str]:
    errs: list[str] = []
    if category not in PATCH_PROPOSAL_QUALITY_CATEGORIES:
        return [f"unknown patch_proposal_quality_category: {category!r}"]

    structural = validate_patch_proposal_v1(proposal, plan_contract, code_reasoning_trace)
    rr = proposal.get("review_requirements") if isinstance(proposal.get("review_requirements"), dict) else {}
    edits = proposal.get("proposed_edits") if isinstance(proposal.get("proposed_edits"), list) else []
    rollback = (
        proposal.get("rollback_plan_required")
        if isinstance(proposal.get("rollback_plan_required"), dict)
        else {}
    )
    test_plan = (
        proposal.get("test_plan_required")
        if isinstance(proposal.get("test_plan_required"), dict)
        else {}
    )

    if category == "overbound":
        if not structural:
            errs.append("overbound: expected structural bound violations")
        elif not any("exceeds" in e.lower() or "over" in e.lower() for e in structural):
            errs.append("overbound: expected bound-related structural errors")
        return errs

    if category == "missing_rollback":
        if not structural:
            errs.append("missing_rollback: expected rollback structural errors")
        elif not any("rollback_plan_required" in e for e in structural):
            errs.append("missing_rollback: expected rollback_plan_required error")
        return errs

    if category == "weak_test_plan":
        if not structural:
            # Structural schema can still pass while quality is weak; enforce content checks here.
            checks = test_plan.get("required_checks")
            criteria = str(test_plan.get("pass_fail_criteria") or "")
            if not isinstance(checks, list) or len(checks) < 2:
                return []
            if "all tests pass" in criteria.lower() and len(criteria.split()) <= 4:
                return []
            errs.append("weak_test_plan: expected weak/non-specific test plan signal")
            return errs
        # If structural failed, allow only test-plan related failures.
        if not any("test_plan_required" in e for e in structural):
            errs.append("weak_test_plan: structural errors are not test-plan related")
        return errs

    if structural:
        errs.extend(structural)
        return errs

    # Positive-quality categories
    if category == "clear_and_bounded":
        if not edits:
            errs.append("clear_and_bounded: expected at least one proposed edit")
        for i, row in enumerate(edits):
            if not isinstance(row, dict):
                continue
            rationale = str(row.get("rationale") or "").strip()
            if len(rationale.split()) < 4:
                errs.append(f"clear_and_bounded: proposed_edits[{i}].rationale too terse")

    if category == "good_reviewer_structure":
        if rr.get("human_review_required") is not True:
            errs.append("good_reviewer_structure: human_review_required must be true")
        checklist = rr.get("checklist")
        if not isinstance(checklist, list) or len(checklist) < 2:
            errs.append("good_reviewer_structure: checklist must have at least 2 actionable entries")
        if not str(rollback.get("strategy") or "").strip():
            errs.append("good_reviewer_structure: rollback strategy must be non-empty")
        checks = test_plan.get("required_checks")
        if not isinstance(checks, list) or len(checks) < 2:
            errs.append("good_reviewer_structure: required_checks must include at least 2 checks")

    return errs


def score_patch_proposal_quality(
    proposal: dict[str, Any],
    plan_contract: dict[str, Any],
    code_reasoning_trace: dict[str, Any],
) -> dict[str, Any]:
    """
    Non-authoritative quality scoring for reviewer usefulness.

    This does not change structural validity semantics; it complements
    validate_patch_proposal_v1 with measurable rubric signals.
    """
    criteria: dict[str, bool] = {}
    structural_errors = validate_patch_proposal_v1(proposal, plan_contract, code_reasoning_trace)

    rr = proposal.get("review_requirements") if isinstance(proposal.get("review_requirements"), dict) else {}
    edits = proposal.get("proposed_edits") if isinstance(proposal.get("proposed_edits"), list) else []
    rollback = (
        proposal.get("rollback_plan_required")
        if isinstance(proposal.get("rollback_plan_required"), dict)
        else {}
    )
    test_plan = (
        proposal.get("test_plan_required")
        if isinstance(proposal.get("test_plan_required"), dict)
        else {}
    )
    bounded_scope = proposal.get("bounded_scope") if isinstance(proposal.get("bounded_scope"), dict) else {}
    plan_cb = (
        plan_contract.get("change_boundaries")
        if isinstance(plan_contract.get("change_boundaries"), dict)
        else {}
    )

    # A: clarity
    criteria["clarity_has_edits"] = len(edits) > 0
    criteria["clarity_rationales_specific"] = all(
        isinstance(row, dict)
        and isinstance(row.get("rationale"), str)
        and len(str(row.get("rationale") or "").strip().split()) >= 4
        for row in edits
    ) if edits else False
    criteria["clarity_paths_deduped"] = len(
        {
            str(row.get("path")).strip()
            for row in edits
            if isinstance(row, dict) and isinstance(row.get("path"), str)
        }
    ) == len(edits) if edits else False

    # B: bounds realism
    try:
        max_files = int(bounded_scope.get("max_files_touched", -1))
        max_lines = int(bounded_scope.get("max_diff_lines", -1))
        plan_max_files = int(plan_cb.get("max_files_touched", -1))
        plan_max_lines = int(plan_cb.get("max_diff_lines_hint", -1))
    except (TypeError, ValueError):
        max_files = max_lines = plan_max_files = plan_max_lines = -1
    criteria["bounds_edit_count_within_scope"] = max_files >= 0 and len(edits) <= max_files
    criteria["bounds_max_files_within_plan"] = max_files >= 0 and plan_max_files >= 0 and max_files <= plan_max_files
    criteria["bounds_max_lines_within_plan"] = max_lines >= 0 and plan_max_lines >= 0 and max_lines <= plan_max_lines

    # C: rollback quality
    criteria["rollback_strategy_present"] = isinstance(rollback.get("strategy"), str) and bool(
        str(rollback.get("strategy") or "").strip()
    )
    criteria["rollback_safety_checks_present"] = isinstance(rollback.get("safety_checks"), list) and len(
        rollback.get("safety_checks") or []
    ) >= 1
    criteria["rollback_not_placeholder"] = criteria["rollback_strategy_present"] and str(
        rollback.get("strategy") or ""
    ).strip().lower() not in {"rollback", "revert", "undo"}

    # D: test usefulness
    required_checks = test_plan.get("required_checks") if isinstance(test_plan.get("required_checks"), list) else []
    criteria["tests_required_checks_count"] = len(required_checks) >= 2
    criteria["tests_criteria_present"] = isinstance(test_plan.get("pass_fail_criteria"), str) and bool(
        str(test_plan.get("pass_fail_criteria") or "").strip()
    )
    criteria["tests_not_generic_only"] = criteria["tests_criteria_present"] and "all tests pass" not in str(
        test_plan.get("pass_fail_criteria") or ""
    ).strip().lower()

    # E/F: omission/reviewer UX-like checks on emitted proposals
    criteria["review_human_required_true"] = rr.get("human_review_required") is True
    checklist = rr.get("checklist") if isinstance(rr.get("checklist"), list) else []
    criteria["review_checklist_min_two"] = len(checklist) >= 2
    criteria["review_checklist_non_empty"] = all(isinstance(x, str) and bool(x.strip()) for x in checklist)

    total = len(criteria)
    passed = sum(1 for ok in criteria.values() if ok)
    score_percent = float((passed / total) * 100.0) if total else 0.0

    return {
        "structural_valid": len(structural_errors) == 0,
        "structural_error_count": len(structural_errors),
        "score_percent": round(score_percent, 2),
        "passed_criteria": passed,
        "total_criteria": total,
        "criteria": criteria,
    }


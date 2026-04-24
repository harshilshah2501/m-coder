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


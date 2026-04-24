from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from runtime.code_reasoning.v1_validate import validate_code_reasoning_trace_v1
from runtime.patch_proposal.v1_validate import validate_patch_proposal_v1
from runtime.plan_contract.v1_validate import validate_plan_contract_v1


@dataclass(frozen=True)
class PatchProposalBuildResult:
    patch_proposal: dict[str, Any] | None
    omission_reason: str | None = None


def _hash_ref(prefix: str, payload: dict[str, Any]) -> str:
    material = repr(sorted(payload.items())).encode("utf-8")
    return f"{prefix}:{sha256(material).hexdigest()}"


def _truthy_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(x).strip() for x in value if isinstance(x, str) and str(x).strip()]


def _edit_intent_for_path(path: str) -> str:
    p = path.lower()
    if p.endswith((".md", ".rst", ".txt")):
        return "verify"
    return "edit"


def _build_edit_rationale(
    *,
    path: str,
    query: str,
    plan_steps: list[str],
    max_files: int,
    max_lines: int,
) -> str:
    step_hint = plan_steps[0] if plan_steps else f"Address query intent: {query[:100]}"
    return (
        f"Update `{path}` to {step_hint.lower()}, keeping scope within "
        f"plan bounds (max_files={max_files}, max_diff_lines={max_lines})."
    )


def build_patch_proposal_v1(
    *,
    request_id: str,
    query: str,
    plan_steps: list[str] | None,
    metadata: dict[str, Any] | None,
    plan_contract: dict[str, Any] | None,
    code_reasoning_trace: dict[str, Any] | None,
) -> PatchProposalBuildResult:
    """
    Deterministic patch_proposal.v1 builder skeleton.

    This builder does not wire /v1/ask emission. It only creates proposal
    artifacts for later opt-in use when dependencies are valid and bounded.
    """
    if not isinstance(plan_contract, dict):
        return PatchProposalBuildResult(None, "missing_plan_contract")
    if not isinstance(code_reasoning_trace, dict):
        return PatchProposalBuildResult(None, "missing_code_reasoning_trace")

    if validate_plan_contract_v1(plan_contract):
        return PatchProposalBuildResult(None, "invalid_plan_contract")
    if validate_code_reasoning_trace_v1(code_reasoning_trace, plan_contract):
        return PatchProposalBuildResult(None, "invalid_code_reasoning_trace")

    posture = str(plan_contract.get("approval_posture") or "")
    risk_class = str(plan_contract.get("risk_class") or "")
    if posture in {"refuse", "defer"} or risk_class == "insufficient_evidence":
        return PatchProposalBuildResult(None, "forbidden_or_refusal_posture")

    md = metadata if isinstance(metadata, dict) else {}
    quality = str(md.get("evidence_quality") or "").strip()
    reasons = _truthy_str_list(md.get("quality_reasons"))
    req_id = str(request_id or "").strip()
    if not req_id or not quality:
        return PatchProposalBuildResult(None, "insufficient_metadata")

    cb = plan_contract.get("change_boundaries") if isinstance(plan_contract.get("change_boundaries"), dict) else {}
    try:
        max_files = int(cb.get("max_files_touched", 0))
        max_lines = int(cb.get("max_diff_lines_hint", 0))
    except (TypeError, ValueError):
        return PatchProposalBuildResult(None, "invalid_plan_contract")

    affected = plan_contract.get("affected_files") if isinstance(plan_contract.get("affected_files"), list) else []
    paths = [
        str(row.get("path")).strip()
        for row in affected
        if isinstance(row, dict) and isinstance(row.get("path"), str) and str(row.get("path")).strip()
    ][: max(0, max_files)]
    if not paths and max_files > 0:
        return PatchProposalBuildResult(None, "insufficient_metadata")

    steps = [s.strip() for s in (plan_steps or []) if isinstance(s, str) and s.strip()]
    q = str(query or "").strip()
    if not q:
        return PatchProposalBuildResult(None, "insufficient_metadata")

    proposal: dict[str, Any] = {
        "schema_version": "patch_proposal.v1",
        "proposal_ref": f"patch_proposal:{req_id}",
        "plan_contract_ref": _hash_ref("plan_contract_sha256", plan_contract),
        "code_reasoning_trace_ref": _hash_ref("code_reasoning_trace_sha256", code_reasoning_trace),
        "bounded_scope": {
            "max_files_touched": max_files,
            "max_diff_lines": max_lines,
            "allowed_paths": paths or ["<none>"],
            "forbidden_paths": [".git/", "runtime/.secrets/", "/etc/"],
        },
        "proposed_edits": [
            {
                "path": p,
                "intent": _edit_intent_for_path(p),
                "rationale": _build_edit_rationale(
                    path=p,
                    query=q,
                    plan_steps=steps,
                    max_files=max_files,
                    max_lines=max_lines,
                ),
            }
            for p in paths
        ],
        "validation_and_risk": {
            "risk_class": risk_class,
            "key_risks": [
                "Behavioral regression if assumptions are wrong",
                "Scope drift beyond plan boundaries",
            ],
            "assumptions": reasons or [f"evidence_quality={quality}"],
        },
        "test_plan_required": {
            "required_checks": [
                (
                    f"Run targeted unit tests covering {paths[0]}"
                    if paths
                    else "Run targeted unit tests for touched module"
                ),
                "Run targeted regression scenario for the affected behavior path",
                "Run linter/static checks for touched files only",
            ],
            "pass_fail_criteria": "All required checks pass with no new critical regressions.",
        },
        "rollback_plan_required": {
            "strategy": "Revert touched files and re-run targeted tests if regression is detected.",
            "safety_checks": [
                "Capture pre-change diff for all touched files",
                "Confirm rollback restores prior test pass state",
            ],
        },
        "review_requirements": {
            "human_review_required": True,
            "checklist": [
                "Verify proposed file paths are inside plan_contract bounded scope",
                "Verify rollback steps are actionable and reference touched files",
                "Verify test plan covers changed behavior and touched modules",
            ],
        },
    }

    errs = validate_patch_proposal_v1(proposal, plan_contract, code_reasoning_trace)
    if errs:
        return PatchProposalBuildResult(None, "generated_patch_proposal_invalid")
    return PatchProposalBuildResult(proposal, None)


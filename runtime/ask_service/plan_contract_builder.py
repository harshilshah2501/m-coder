from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.plan_contract.v1_validate import validate_plan_contract_v1


@dataclass(frozen=True)
class PlanContractBuildResult:
    plan_contract: dict[str, Any] | None
    omission_reason: str | None = None


_DESTRUCTIVE_TOKENS = (
    "rm -rf",
    "drop table",
    "truncate",
    "shutdown",
    "systemctl",
    "sudo",
    "privileged",
    "delete all",
)


def _truthy_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for x in value:
        if isinstance(x, str) and x.strip():
            out.append(x.strip())
    return out


def _intent_kind_from_metadata(intent_type: str) -> str:
    t = (intent_type or "").upper()
    if t == "DEBUG_INTENT":
        return "fix"
    if t in {"CONFIG_INTENT", "INFRA_INTENT"}:
        return "config"
    if t in {"DOC_INTENT", "DOCUMENT_INTENT"}:
        return "document"
    return "explore"


def _collect_candidate_paths(evidence_bundle: dict[str, Any] | None) -> list[str]:
    paths: list[str] = []
    if isinstance(evidence_bundle, dict):
        entries = evidence_bundle.get("entries")
        if isinstance(entries, list):
            for ent in entries:
                if not isinstance(ent, dict):
                    continue
                p = str(ent.get("relative_path") or "").strip()
                if p:
                    paths.append(p)
        ar = evidence_bundle.get("authority_resolution")
        if isinstance(ar, dict):
            po = ar.get("primary_owner")
            if isinstance(po, dict):
                owner_file = str(po.get("file") or "").strip()
                if owner_file:
                    paths.append(owner_file)
    # keep deterministic order while deduplicating
    seen: set[str] = set()
    deduped: list[str] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            deduped.append(p)
    return deduped


def build_plan_contract_v1(
    *,
    query: str,
    plan_steps: list[str] | None,
    metadata: dict[str, Any] | None,
    evidence_bundle: dict[str, Any] | None,
) -> PlanContractBuildResult:
    """
    Deterministic plan_contract.v1 builder skeleton for /v1/ask.

    This module intentionally does not wire runtime emission; it only builds
    from existing Ask metadata/evidence and can refuse with omission_reason.
    """
    md = metadata if isinstance(metadata, dict) else {}
    eq = str(md.get("evidence_quality") or "").strip()
    reasons = _truthy_str_list(md.get("quality_reasons"))
    intent = str(md.get("intent_type") or "").strip()
    q = str(query or "").strip()
    steps = [s for s in (plan_steps or []) if isinstance(s, str) and s.strip()]
    if not q:
        return PlanContractBuildResult(None, "missing_query")
    if not eq:
        return PlanContractBuildResult(None, "missing_metadata:evidence_quality")
    if not intent:
        return PlanContractBuildResult(None, "missing_metadata:intent_type")
    if not reasons:
        return PlanContractBuildResult(None, "missing_metadata:quality_reasons")

    q_low = q.lower()
    destructive = any(tok in q_low for tok in _DESTRUCTIVE_TOKENS)
    candidate_paths = _collect_candidate_paths(evidence_bundle)

    insufficient = eq in {"INSUFFICIENT", "NO_MATCH", "WEAK"}
    if destructive:
        risk_class = "critical"
        approval_posture = "refuse"
        allowed_actions: list[str] = []
        forbidden_actions = [
            "execute_shell",
            "privileged_write",
            "propose_patch_text",
            "run_tests_local",
        ]
        max_files_touched = 0
        max_diff_lines = 0
        affected_files: list[dict[str, str]] = []
        requires_resolution = [
            "request_is_privileged_or_destructive",
            "human_policy_override_required",
        ]
    elif insufficient:
        risk_class = "insufficient_evidence"
        approval_posture = "defer"
        allowed_actions = ["read_repo"]
        forbidden_actions = [
            "execute_shell",
            "privileged_write",
            "propose_patch_text",
        ]
        max_files_touched = 0
        max_diff_lines = 0
        affected_files = []
        requires_resolution = reasons or ["insufficient_grounded_evidence"]
    else:
        risk_class = "medium"
        approval_posture = "advisory_only"
        allowed_actions = ["read_repo", "run_linter", "run_tests_local", "propose_patch_text"]
        forbidden_actions = ["execute_shell", "privileged_write"]
        # keep scope narrow and deterministic; this is a planning cap, not execution authority
        max_files_touched = max(1, min(len(candidate_paths), 5))
        max_diff_lines = 120
        affected_files = [
            {"path": p, "role": ("primary" if idx == 0 else "secondary")}
            for idx, p in enumerate(candidate_paths[:max_files_touched])
        ]
        requires_resolution = []

    plan_contract: dict[str, Any] = {
        "schema_version": "plan_contract.v1",
        "task_intent": {
            "summary": (steps[0] if steps else f"Plan work for query: {q[:180]}"),
            "kind": _intent_kind_from_metadata(intent),
        },
        "affected_files": affected_files,
        "evidence_requirements": {
            "must_have": ["grounded_context_bundle"],
            "nice_to_have": ["owner_method_visible", "call_site_resolution_state"],
            "insufficient_without": ["grounded_context_bundle"] if insufficient else [],
        },
        "change_boundaries": {
            "in_scope": (steps[:3] or [f"Address query intent: {q[:120]}"]),
            "out_of_scope": [
                "No direct execution from /v1/ask",
                "No Stage 3 loop integration in this slice",
            ],
            "max_files_touched": max_files_touched,
            "max_diff_lines_hint": max_diff_lines,
        },
        "risk_class": risk_class,
        "allowed_actions": allowed_actions,
        "forbidden_actions": forbidden_actions,
        "approval_posture": approval_posture,
        "confidence_limits": {
            "known": [f"evidence_quality={eq}", f"intent_type={intent}"],
            "unknown": reasons,
            "requires_resolution": requires_resolution,
        },
    }

    errs = validate_plan_contract_v1(plan_contract)
    if errs:
        return PlanContractBuildResult(None, f"generated_contract_invalid:{'; '.join(errs[:3])}")
    return PlanContractBuildResult(plan_contract=plan_contract, omission_reason=None)

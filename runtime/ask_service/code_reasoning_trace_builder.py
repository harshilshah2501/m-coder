from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from runtime.code_reasoning.v1_validate import validate_code_reasoning_trace_v1
from runtime.plan_contract.v1_validate import validate_plan_contract_v1


@dataclass(frozen=True)
class CodeReasoningTraceBuildResult:
    code_reasoning_trace: dict[str, Any] | None
    omission_reason: str | None = None


def _plan_contract_ref(plan_contract: dict[str, Any]) -> str:
    material = repr(sorted(plan_contract.items())).encode("utf-8")
    return f"plan_contract_sha256:{sha256(material).hexdigest()}"


def build_code_reasoning_trace_v1(
    *,
    request_id: str,
    query: str,
    plan_steps: list[str] | None,
    metadata: dict[str, Any] | None,
    plan_contract: dict[str, Any] | None,
) -> CodeReasoningTraceBuildResult:
    """
    Deterministic code_reasoning_trace.v1 builder skeleton.

    This builder is intentionally standalone and not wired into /v1/ask emission yet.
    """
    if not isinstance(plan_contract, dict):
        return CodeReasoningTraceBuildResult(None, "missing_plan_contract")

    plan_errs = validate_plan_contract_v1(plan_contract)
    if plan_errs:
        return CodeReasoningTraceBuildResult(None, "invalid_plan_contract")

    posture = str(plan_contract.get("approval_posture") or "")
    risk_class = str(plan_contract.get("risk_class") or "")
    if posture in {"refuse", "defer"} or risk_class == "insufficient_evidence":
        return CodeReasoningTraceBuildResult(None, "forbidden_or_refusal_posture")

    md = metadata if isinstance(metadata, dict) else {}
    intent = str(md.get("intent_type") or "").strip()
    quality = str(md.get("evidence_quality") or "").strip()
    reasons = md.get("quality_reasons")
    if not intent or not quality or not isinstance(reasons, list):
        return CodeReasoningTraceBuildResult(None, "insufficient_metadata")

    req_id = str(request_id or "").strip()
    if not req_id:
        return CodeReasoningTraceBuildResult(None, "insufficient_metadata")

    steps_text = [s.strip() for s in (plan_steps or []) if isinstance(s, str) and s.strip()]
    q = str(query or "").strip()

    cb = plan_contract.get("change_boundaries") if isinstance(plan_contract.get("change_boundaries"), dict) else {}
    max_files = int(cb.get("max_files_touched", 0) or 0)
    max_lines = int(cb.get("max_diff_lines_hint", 0) or 0)

    trace: dict[str, Any] = {
        "schema_version": "code_reasoning_trace.v1",
        "request_id": req_id,
        "plan_contract_ref": _plan_contract_ref(plan_contract),
        "bounds": {
            "max_iterations": 5,
            "max_tool_calls": 0,
            "max_evidence_refs_per_step": 8,
            "max_step_text_chars": 4096,
            "max_patch_intent_files": max_files,
            "max_patch_intent_lines_total": max_lines,
            "summarize_between_steps": True,
        },
        "steps": [
            {
                "step_index": 0,
                "step_kind": "LOCATE_TARGET",
                "status": "complete",
                "evidence_requirements": {
                    "must_have": ["grounded_context_bundle"],
                    "nice_to_have": [],
                    "insufficient_without": [],
                },
                "evidence_refs_used": ["ask.evidence_bundle"],
                "rationale": f"Use grounded evidence for query intent: {q[:120]}",
                "summary": (steps_text[0] if steps_text else "Locate grounded owner/context for requested task."),
            },
            {
                "step_index": 1,
                "step_kind": "INSPECT_CONTEXT",
                "status": "complete",
                "evidence_requirements": {
                    "must_have": ["grounded_context_bundle"],
                    "nice_to_have": ["owner_method_visible"],
                    "insufficient_without": [],
                },
                "evidence_refs_used": ["ask.metadata"],
                "rationale": "Inspect quality metrics and authority context before proposing changes.",
                "summary": "Inspect context and confidence limits from current Ask metadata.",
            },
            {
                "step_index": 2,
                "step_kind": "CHANGE_STRATEGY",
                "status": "complete",
                "evidence_requirements": {
                    "must_have": ["plan_contract"],
                    "nice_to_have": [],
                    "insufficient_without": [],
                },
                "evidence_refs_used": ["plan_contract"],
                "rationale": "Derive bounded strategy from plan contract limits and forbidden actions.",
                "summary": "Construct bounded strategy consistent with plan constraints.",
            },
            {
                "step_index": 3,
                "step_kind": "FINAL_PROPOSAL",
                "status": "complete",
                "evidence_requirements": {
                    "must_have": ["plan_contract"],
                    "nice_to_have": [],
                    "insufficient_without": [],
                },
                "evidence_refs_used": ["plan_contract", "ask.metadata"],
                "rationale": "Finalize planning-only trace without execution request.",
                "summary": "Final proposal prepared under PLAN_ONLY constraints.",
            },
        ],
        "terminal": {
            "outcome": "completed",
            "reason_code": "trace_ready_plan_only",
            "human_message": "Bounded code reasoning trace prepared; no execution requested.",
            "execution_requested": False,
        },
        "ledger_preview": [
            {"event_type": "code_reasoning_session_start"},
            {"event_type": "code_reasoning_terminal"},
        ],
    }

    trace_errs = validate_code_reasoning_trace_v1(trace, plan_contract)
    if trace_errs:
        return CodeReasoningTraceBuildResult(None, "generated_trace_invalid")

    return CodeReasoningTraceBuildResult(code_reasoning_trace=trace, omission_reason=None)

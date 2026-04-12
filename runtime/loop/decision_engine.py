"""Stage 3 deterministic decision engine."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from runtime.state.validators import validate_loop_decision


def _stable_ref(prefix: str, payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


class DecisionEngine:
    """Builds LoopDecision.v1 from proposal/tool/policy outcomes."""

    def decide(
        self,
        *,
        proposal_ref: str,
        remaining_budget: int,
        proposal: dict[str, Any] | None = None,
        tool_result: dict[str, Any] | None = None,
        failure_class: str | None = None,
    ) -> dict[str, Any]:
        if failure_class == "insufficient_evidence":
            decision = "TERMINATE_INSUFFICIENT"
            reason_code = "insufficient_evidence"
        elif failure_class == "plan_gate_refused":
            decision = "TERMINATE_REFUSED"
            reason_code = "plan_gate_refused"
        elif failure_class in {"schema_version_mismatch", "policy_violation", "tool_failure_terminal"}:
            decision = "TERMINATE_FAILED"
            reason_code = failure_class
        elif failure_class in {"invalid_proposal", "tool_failure_retryable"}:
            if remaining_budget > 0:
                decision = "REVISE_PROPOSAL"
            else:
                decision = "TERMINATE_FAILED"
            reason_code = failure_class
        elif failure_class == "tool_denied":
            decision = "TERMINATE_FAILED"
            reason_code = "tool_denied"
        elif tool_result is not None:
            status = tool_result["status"]
            output_data = tool_result.get("output", {}).get("data", {})
            if (
                status == "partial"
                and bool(output_data.get("evidence_inadequate", False))
            ):
                decision = "TERMINATE_INSUFFICIENT"
                reason_code = "insufficient_evidence"
            elif status in {"failed_retryable"} and remaining_budget > 0:
                decision = "REVISE_PROPOSAL"
                reason_code = "tool_failure_retryable"
            elif status in {"denied"}:
                # Controller translates this deterministic terminal-failed decision
                # into BLOCKED terminal semantics for non-executed denied actions.
                decision = "TERMINATE_FAILED"
                reason_code = "tool_denied"
            elif status in {"failed_terminal", "timeout"}:
                decision = "TERMINATE_FAILED"
                reason_code = "tool_failure_terminal" if status == "failed_terminal" else "tool_timeout"
            elif status in {"success", "partial"}:
                decision = "TERMINATE_SUCCESS"
                reason_code = "tool_success"
            else:
                decision = "TERMINATE_FAILED"
                reason_code = "tool_unknown_status"
        elif proposal is not None:
            intent = proposal["intent_type"]
            if intent in {"answer_only", "plan_only"}:
                decision = "TERMINATE_SUCCESS"
                reason_code = "proposal_complete"
            elif intent == "refuse":
                decision = "TERMINATE_REFUSED"
                reason_code = "proposal_refuse"
            else:
                decision = "PROCEED_TO_TOOL"
                reason_code = "tool_required"
        else:
            decision = "TERMINATE_FAILED"
            reason_code = "decision_input_missing"

        payload = {
            "proposal_ref": proposal_ref,
            "decision": decision,
            "reason_code": reason_code,
            "remaining_budget": remaining_budget,
        }
        loop_decision = {
            "schema_version": "loop_decision.v1",
            "proposal_ref": proposal_ref,
            "decision_ref": _stable_ref("decision", payload),
            "decision": decision,
            "reason_code": reason_code,
            "remaining_budget": remaining_budget,
        }
        validate_loop_decision(loop_decision)
        return loop_decision

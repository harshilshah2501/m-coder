"""Stage 3 controlled runtime loop controller."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from runtime.adapters.model_adapter import ModelAdapter
from runtime.loop.decision_engine import DecisionEngine
from runtime.loop.state_machine import IllegalTransitionError, Stage3StateMachine
from runtime.obs.ledger import LedgerEvent, Stage3Ledger
from runtime.state.validators import (
    EvidenceIntegrityError,
    Stage3ValidationError,
    SchemaValidationError,
    validate_final_response,
    validate_frame_evidence_integrity,
    validate_loop_context_frame,
    validate_task_envelope,
)
from runtime.tools.executor import ToolExecutor


@dataclass
class LoopResult:
    terminal_state: str
    final_response: dict[str, Any]
    trace: dict[str, Any]


class Stage3LoopController:
    """Runtime-owned Stage 3 loop implementation."""

    def __init__(
        self,
        *,
        model_adapter: ModelAdapter,
        tool_executor: ToolExecutor,
        plan_gate_service: Any,
        ledger: Stage3Ledger,
        state_machine: Stage3StateMachine | None = None,
        decision_engine: DecisionEngine | None = None,
    ) -> None:
        self._model_adapter = model_adapter
        self._tool_executor = tool_executor
        self._plan_gate_service = plan_gate_service
        self._ledger = ledger
        self._sm = state_machine or Stage3StateMachine()
        self._de = decision_engine or DecisionEngine()

    def run(self, task_envelope: dict[str, Any], *, working_dir: str) -> LoopResult:
        self._last_internal_failure_reason: str | None = None
        try:
            validate_task_envelope(task_envelope)
        except Stage3ValidationError:
            return self._preloop_fail_closed(
                reason_code="invalid_task_envelope",
                task_envelope=task_envelope,
            )
        except Exception:
            return self._preloop_fail_closed(
                reason_code="preloop_validation_failed",
                task_envelope=task_envelope,
            )

        request_id = task_envelope["request_id"]
        task_type = task_envelope["task_type"]
        allowed_evidence_refs = set(task_envelope["evidence_bundle"]["evidence_refs"])
        current_state = "CONTEXT_READY"
        remaining_budget = int(task_envelope["attempt_budget"]["remaining_attempts"])
        iteration_index = 0
        rejection_reasons: list[str] = []
        previous_proposal_ref: str | None = None
        last_tool_result_ref: str | None = None
        last_tool_status: str | None = None
        proposal_refs: list[str] = []
        tool_result_refs: list[str] = []
        execution_artifact_refs: list[str] = []
        previous_action_class: str | None = None

        try:
            pre_gate = self._invoke_plan_gate(request_id=request_id, task_type=task_type, intent_type=None)
        except Exception:
            return self._preloop_fail_closed(
                reason_code="preloop_plan_gate_failed",
                task_envelope=task_envelope,
                request_id=request_id,
            )
        if pre_gate == "refuse":
            current_state = self._transition(current_state, "plan_gate_pre_refuse", request_id, iteration_index)
            return self._terminal_response(
                request_id=request_id,
                outcome="refused",
                terminal_state=current_state,
                task_envelope=task_envelope,
                reason_code="plan_gate_refused",
                proposal_refs=proposal_refs,
                tool_result_refs=tool_result_refs,
            )
        if pre_gate in {"defer", "bounded_allow"}:
            current_state = self._transition(current_state, "plan_gate_pre_block", request_id, iteration_index)
            return self._terminal_response(
                request_id=request_id,
                outcome="blocked",
                terminal_state=current_state,
                task_envelope=task_envelope,
                reason_code="plan_gate_blocked",
                proposal_refs=proposal_refs,
                tool_result_refs=tool_result_refs,
            )

        current_state = self._transition(
            current_state,
            "plan_gate_pre_pass",
            request_id,
            iteration_index,
            guard_context={"evidence_valid": True},
        )

        while True:
            if current_state == "FAILED" and self._last_internal_failure_reason:
                return self._terminal_response(
                    request_id=request_id,
                    outcome="failed",
                    terminal_state="FAILED",
                    task_envelope=task_envelope,
                    reason_code=self._last_internal_failure_reason,
                    proposal_refs=proposal_refs,
                    tool_result_refs=tool_result_refs,
                    last_tool_status=last_tool_status,
                    execution_artifact_refs=execution_artifact_refs,
                )
            if remaining_budget <= 0:
                if current_state == "MODEL_REVISED":
                    current_state = self._transition(current_state, "budget_exhausted", request_id, iteration_index)
                return self._terminal_response(
                    request_id=request_id,
                    outcome="failed",
                    terminal_state=current_state if current_state in {"FAILED"} else "FAILED",
                    task_envelope=task_envelope,
                    reason_code="budget_exhausted",
                    proposal_refs=proposal_refs,
                    tool_result_refs=tool_result_refs,
                )
            frame = {
                "schema_version": "loop_context_frame.v1",
                "request_id": request_id,
                "iteration_index": iteration_index,
                "remaining_budget": remaining_budget,
                "current_state": current_state,
                "evidence_refs": sorted(allowed_evidence_refs),
                "previous_proposal_ref": previous_proposal_ref,
                "last_tool_result_ref": last_tool_result_ref,
                "rejection_reasons": rejection_reasons,
                "policy_snapshot": {
                    "tool_mode": task_envelope["tool_policy"]["mode"],
                    "allowed_tools": task_envelope["tool_policy"]["allowed"],
                    "plan_gate_recheck_required": True,
                },
                "task_type": task_type,
            }
            try:
                validate_loop_context_frame(frame)
                validate_frame_evidence_integrity(frame=frame, task_envelope=task_envelope)
            except Stage3ValidationError:
                return self._terminal_response(
                    request_id=request_id,
                    outcome="failed",
                    terminal_state="FAILED",
                    task_envelope=task_envelope,
                    reason_code="loop_context_frame_validation_failed",
                    proposal_refs=proposal_refs,
                    tool_result_refs=tool_result_refs,
                    last_tool_status=last_tool_status,
                    execution_artifact_refs=execution_artifact_refs,
                )

            current_state = self._transition(
                current_state,
                "request_proposal",
                request_id,
                iteration_index,
                guard_context={"remaining_budget": remaining_budget},
            )

            try:
                proposal = self._model_adapter.propose(
                    loop_context_frame=frame,
                    evidence_refs=sorted(allowed_evidence_refs),
                )
            except (SchemaValidationError, EvidenceIntegrityError) as exc:
                rejection_reasons.append(str(exc))
                if remaining_budget > 0:
                    current_state = self._transition(
                        current_state,
                        "proposal_invalid_recoverable",
                        request_id,
                        iteration_index,
                        guard_context={"remaining_budget": remaining_budget},
                        reason_code="invalid_proposal",
                    )
                    remaining_budget -= 1
                    if remaining_budget <= 0:
                        current_state = self._transition(
                            current_state,
                            "budget_exhausted",
                            request_id,
                            iteration_index,
                        )
                        return self._terminal_response(
                            request_id=request_id,
                            outcome="failed",
                            terminal_state=current_state,
                            task_envelope=task_envelope,
                            reason_code="budget_exhausted",
                            proposal_refs=proposal_refs,
                            tool_result_refs=tool_result_refs,
                        )
                    current_state = self._transition(
                        current_state,
                        "repropose",
                        request_id,
                        iteration_index,
                        guard_context={"remaining_budget": remaining_budget},
                    )
                    iteration_index += 1
                    continue
                current_state = self._transition(
                    current_state,
                    "proposal_invalid_terminal",
                    request_id,
                    iteration_index,
                    reason_code="invalid_proposal",
                )
                return self._terminal_response(
                    request_id=request_id,
                    outcome="failed",
                    terminal_state=current_state,
                    task_envelope=task_envelope,
                    reason_code="invalid_proposal",
                    proposal_refs=proposal_refs,
                    tool_result_refs=tool_result_refs,
                )

            proposal_ref = self._stable_ref("proposal", proposal)
            previous_proposal_ref = proposal_ref
            proposal_refs.append(proposal_ref)
            current_state = self._transition(current_state, "proposal_schema_policy_valid", request_id, iteration_index)

            decision = self._de.decide(
                proposal_ref=proposal_ref,
                remaining_budget=remaining_budget,
                proposal=proposal,
            )
            self._ledger.emit(
                LedgerEvent(
                    request_id=request_id,
                    iteration_index=iteration_index,
                    event_type="loop_decision",
                    proposal_ref=proposal_ref,
                    decision_ref=decision["decision_ref"],
                    reason_code=decision["reason_code"],
                )
            )

            if decision["decision"] == "TERMINATE_SUCCESS":
                current_state = self._transition(current_state, "decision_terminate_success", request_id, iteration_index)
                return self._terminal_response(
                    request_id=request_id,
                    outcome="completed",
                    terminal_state=current_state,
                    task_envelope=task_envelope,
                    reason_code=decision["reason_code"],
                    proposal_refs=proposal_refs,
                    tool_result_refs=tool_result_refs,
                )
            if decision["decision"] == "TERMINATE_REFUSED":
                current_state = self._transition(current_state, "decision_terminate_refused", request_id, iteration_index)
                return self._terminal_response(
                    request_id=request_id,
                    outcome="refused",
                    terminal_state=current_state,
                    task_envelope=task_envelope,
                    reason_code=decision["reason_code"],
                    proposal_refs=proposal_refs,
                    tool_result_refs=tool_result_refs,
                )

            if decision["decision"] == "PROCEED_TO_TOOL":
                tool_call = proposal.get("tool_call", {})
                current_action_class = proposal["intent_type"]
                requires_gate = (
                    task_type in {"CODE", "EXECUTE"}
                    or current_action_class != previous_action_class
                    or task_envelope["tool_policy"]["mode"] == "sandboxed"
                )
                previous_action_class = current_action_class

                current_state = self._transition(
                    current_state,
                    "decision_proceed_to_tool",
                    request_id,
                    iteration_index,
                    guard_context={"tool_calls_requested": 1},
                )

                if requires_gate:
                    try:
                        gate = self._invoke_plan_gate(
                            request_id=request_id,
                            task_type=task_type,
                            intent_type=current_action_class,
                        )
                    except Exception:
                        current_state = self._transition(
                            current_state,
                            "tool_terminal_failure",
                            request_id,
                            iteration_index,
                            reason_code="inloop_plan_gate_failed",
                        )
                        return self._terminal_response(
                            request_id=request_id,
                            outcome="failed",
                            terminal_state=current_state,
                            task_envelope=task_envelope,
                            reason_code="inloop_plan_gate_failed",
                            proposal_refs=proposal_refs,
                            tool_result_refs=tool_result_refs,
                            last_tool_status=last_tool_status,
                            execution_artifact_refs=execution_artifact_refs,
                        )
                    if gate != "safe_execute":
                        # Centralized mapping: non-refusal recheck blocks are surfaced as BLOCKED.
                        failure_class = "plan_gate_refused" if gate == "refuse" else "policy_violation"
                        failure_decision = self._de.decide(
                            proposal_ref=proposal_ref,
                            remaining_budget=remaining_budget,
                            failure_class=failure_class,
                        )
                        current_state = self._transition(
                            current_state,
                            "gate_blocked",
                            request_id,
                            iteration_index,
                            reason_code=failure_decision["reason_code"],
                        )
                        self._ledger.emit(
                            LedgerEvent(
                                request_id=request_id,
                                iteration_index=iteration_index,
                                event_type="terminal_decision",
                                proposal_ref=proposal_ref,
                                decision_ref=failure_decision["decision_ref"],
                                reason_code=failure_decision["reason_code"],
                            )
                        )
                        outcome = "refused" if gate == "refuse" else "blocked"
                        return self._terminal_response(
                            request_id=request_id,
                            outcome=outcome,
                            terminal_state=current_state,
                            task_envelope=task_envelope,
                            reason_code=failure_decision["reason_code"],
                            proposal_refs=proposal_refs,
                            tool_result_refs=tool_result_refs,
                            last_tool_status=last_tool_status,
                            execution_artifact_refs=execution_artifact_refs,
                        )

                self._ledger.emit(
                    LedgerEvent(
                        request_id=request_id,
                        iteration_index=iteration_index,
                        event_type="tool_dispatch",
                        proposal_ref=proposal_ref,
                    )
                )
                tool_request = {
                    "schema_version": "tool_execution_request.v1",
                    "tool_name": tool_call["tool_name"],
                    "args": tool_call["args"],
                    "constraints": {
                        "timeout_ms": 30000,
                        "sandbox_required": True,
                        "read_only": task_envelope["tool_policy"]["mode"] == "read_only",
                    },
                }
                try:
                    tool_result = self._tool_executor.execute(tool_request, request_id=request_id, working_dir=working_dir)
                except Stage3ValidationError:
                    current_state = self._transition(
                        current_state,
                        "tool_terminal_failure",
                        request_id,
                        iteration_index,
                        reason_code="internal_schema_validation_failed",
                    )
                    return self._terminal_response(
                        request_id=request_id,
                        outcome="failed",
                        terminal_state=current_state,
                        task_envelope=task_envelope,
                        reason_code="internal_schema_validation_failed",
                        proposal_refs=proposal_refs,
                        tool_result_refs=tool_result_refs,
                        last_tool_status="failed_terminal",
                        execution_artifact_refs=execution_artifact_refs,
                    )
                tool_result_ref = self._stable_ref("tool_result", tool_result)
                last_tool_result_ref = tool_result_ref
                last_tool_status = tool_result.get("status")
                tool_result_refs.append(tool_result_ref)
                execution_artifact_refs.extend(
                    [a.get("artifact_ref") for a in tool_result.get("artifacts", []) if a.get("artifact_ref")]
                )
                self._ledger.emit(
                    LedgerEvent(
                        request_id=request_id,
                        iteration_index=iteration_index,
                        event_type="tool_result_normalized",
                        proposal_ref=proposal_ref,
                        tool_result_ref=tool_result_ref,
                        reason_code=last_tool_status,
                    )
                )
                current_state = self._transition(current_state, "tool_result_ready", request_id, iteration_index)

                tool_decision = self._de.decide(
                    proposal_ref=proposal_ref,
                    remaining_budget=remaining_budget,
                    tool_result=tool_result,
                )
                self._ledger.emit(
                    LedgerEvent(
                        request_id=request_id,
                        iteration_index=iteration_index,
                        event_type="loop_decision",
                        proposal_ref=proposal_ref,
                        decision_ref=tool_decision["decision_ref"],
                        tool_result_ref=tool_result_ref,
                        reason_code=tool_decision["reason_code"],
                    )
                )

                if tool_decision["decision"] == "REVISE_PROPOSAL":
                    if remaining_budget > 0:
                        current_state = self._transition(
                            current_state,
                            "runtime_decide_revise",
                            request_id,
                            iteration_index,
                            guard_context={"remaining_budget": remaining_budget},
                            reason_code=tool_decision["reason_code"],
                        )
                        remaining_budget -= 1
                        if remaining_budget <= 0:
                            current_state = self._transition(
                                current_state,
                                "budget_exhausted",
                                request_id,
                                iteration_index,
                            )
                            return self._terminal_response(
                                request_id=request_id,
                                outcome="failed",
                                terminal_state=current_state,
                                task_envelope=task_envelope,
                                reason_code="budget_exhausted",
                                proposal_refs=proposal_refs,
                                tool_result_refs=tool_result_refs,
                                last_tool_status=last_tool_status,
                                execution_artifact_refs=execution_artifact_refs,
                            )
                        current_state = self._transition(
                            current_state,
                            "repropose",
                            request_id,
                            iteration_index,
                            guard_context={"remaining_budget": remaining_budget},
                        )
                        iteration_index += 1
                        continue
                    current_state = self._transition(current_state, "budget_exhausted", request_id, iteration_index)
                    return self._terminal_response(
                        request_id=request_id,
                        outcome="failed",
                        terminal_state=current_state,
                        task_envelope=task_envelope,
                        reason_code="budget_exhausted",
                        proposal_refs=proposal_refs,
                        tool_result_refs=tool_result_refs,
                        last_tool_status=last_tool_status,
                        execution_artifact_refs=execution_artifact_refs,
                    )

                if tool_decision["decision"] == "TERMINATE_SUCCESS":
                    current_state = self._transition(current_state, "runtime_decide_success", request_id, iteration_index)
                    return self._terminal_response(
                        request_id=request_id,
                        outcome="completed",
                        terminal_state=current_state,
                        task_envelope=task_envelope,
                        reason_code=tool_decision["reason_code"],
                        proposal_refs=proposal_refs,
                        tool_result_refs=tool_result_refs,
                        last_tool_status=last_tool_status,
                        execution_artifact_refs=execution_artifact_refs,
                    )

                if tool_decision["decision"] == "TERMINATE_INSUFFICIENT":
                    current_state = self._transition(current_state, "runtime_decide_insufficient", request_id, iteration_index)
                    return self._terminal_response(
                        request_id=request_id,
                        outcome="insufficient",
                        terminal_state=current_state,
                        task_envelope=task_envelope,
                        reason_code=tool_decision["reason_code"],
                        proposal_refs=proposal_refs,
                        tool_result_refs=tool_result_refs,
                        last_tool_status=last_tool_status,
                        execution_artifact_refs=execution_artifact_refs,
                    )

                if tool_decision["reason_code"] == "tool_denied":
                    current_state = self._transition(
                        current_state,
                        "runtime_decide_blocked",
                        request_id,
                        iteration_index,
                        reason_code=tool_decision["reason_code"],
                    )
                    return self._terminal_response(
                        request_id=request_id,
                        outcome="blocked",
                        terminal_state=current_state,
                        task_envelope=task_envelope,
                        reason_code=tool_decision["reason_code"],
                        proposal_refs=proposal_refs,
                        tool_result_refs=tool_result_refs,
                        last_tool_status=last_tool_status,
                        execution_artifact_refs=execution_artifact_refs,
                    )

                current_state = self._transition(
                    current_state,
                    "runtime_decide_failed",
                    request_id,
                    iteration_index,
                    reason_code=tool_decision["reason_code"],
                )
                return self._terminal_response(
                    request_id=request_id,
                    outcome="failed",
                    terminal_state=current_state,
                    task_envelope=task_envelope,
                    reason_code=tool_decision["reason_code"],
                    proposal_refs=proposal_refs,
                    tool_result_refs=tool_result_refs,
                    last_tool_status=last_tool_status,
                    execution_artifact_refs=execution_artifact_refs,
                )

            if decision["decision"] == "REVISE_PROPOSAL":
                if remaining_budget > 0:
                    current_state = self._transition(
                        current_state,
                        "decision_revise",
                        request_id,
                        iteration_index,
                        guard_context={"remaining_budget": remaining_budget},
                        reason_code=decision["reason_code"],
                    )
                    remaining_budget -= 1
                    if remaining_budget <= 0:
                        current_state = self._transition(
                            current_state,
                            "budget_exhausted",
                            request_id,
                            iteration_index,
                        )
                        return self._terminal_response(
                            request_id=request_id,
                            outcome="failed",
                            terminal_state=current_state,
                            task_envelope=task_envelope,
                            reason_code="budget_exhausted",
                            proposal_refs=proposal_refs,
                            tool_result_refs=tool_result_refs,
                        )
                    current_state = self._transition(
                        current_state,
                        "repropose",
                        request_id,
                        iteration_index,
                        guard_context={"remaining_budget": remaining_budget},
                    )
                    iteration_index += 1
                    continue
                current_state = self._transition(current_state, "budget_exhausted", request_id, iteration_index)
                return self._terminal_response(
                    request_id=request_id,
                    outcome="failed",
                    terminal_state=current_state,
                    task_envelope=task_envelope,
                    reason_code="budget_exhausted",
                    proposal_refs=proposal_refs,
                    tool_result_refs=tool_result_refs,
                )

    def _invoke_plan_gate(self, *, request_id: str, task_type: str, intent_type: str | None) -> str:
        pg_request = {
            "request_id": request_id,
            "command": [task_type.lower(), intent_type or "pre_loop"],
        }
        decision = self._plan_gate_service.evaluate(pg_request)
        return str(decision.posture)

    def _transition(
        self,
        current_state: str,
        event: str,
        request_id: str,
        iteration_index: int,
        *,
        guard_context: dict[str, Any] | None = None,
        reason_code: str | None = None,
    ) -> str:
        guard_context = guard_context or {}
        try:
            next_state = self._sm.next_state(current_state, event, guard_context)
        except IllegalTransitionError:
            next_state = "FAILED"
            reason_code = reason_code or "illegal_transition"
            self._last_internal_failure_reason = reason_code
        self._ledger.emit(
            LedgerEvent(
                request_id=request_id,
                iteration_index=iteration_index,
                event_type="state_transition",
                state_from=current_state,
                state_to=next_state,
                reason_code=reason_code,
            )
        )
        return next_state

    def _terminal_response(
        self,
        *,
        request_id: str,
        outcome: str,
        terminal_state: str,
        task_envelope: dict[str, Any],
        reason_code: str,
        proposal_refs: list[str],
        tool_result_refs: list[str],
        last_tool_status: str | None = None,
        execution_artifact_refs: list[str] | None = None,
    ) -> LoopResult:
        execution_status = "not_run"
        if last_tool_status in {"success", "partial"}:
            execution_status = "executed"
        elif last_tool_status == "denied":
            execution_status = "blocked"
        elif last_tool_status in {"failed_retryable", "failed_terminal", "timeout"}:
            execution_status = "failed"
        elif outcome == "blocked":
            execution_status = "blocked"

        final_response = {
            "schema_version": "final_response.v1",
            "outcome": outcome,
            "evidence_used": {
                "bundle_id": task_envelope["evidence_bundle"]["bundle_id"],
                "item_count": len(task_envelope["evidence_bundle"]["evidence_refs"]),
            },
            "evidence_refs": list(task_envelope["evidence_bundle"]["evidence_refs"]),
            "proposal_refs": proposal_refs,
            "tool_result_refs": tool_result_refs,
            "reasoning_summary": f"terminal={terminal_state}; reason={reason_code}",
            "execution_result": {
                "status": execution_status,
                "artifact_refs": execution_artifact_refs or [],
            },
        }
        try:
            validate_final_response(
                final_response,
                allowed_evidence_refs=set(task_envelope["evidence_bundle"]["evidence_refs"]),
            )
        except Stage3ValidationError:
            outcome = "failed"
            terminal_state = "FAILED"
            reason_code = "final_response_validation_failed"
            execution_status = "failed"
            final_response = {
                "schema_version": "final_response.v1",
                "outcome": "failed",
                "evidence_used": {
                    "bundle_id": task_envelope["evidence_bundle"]["bundle_id"],
                    "item_count": len(task_envelope["evidence_bundle"]["evidence_refs"]),
                },
                "evidence_refs": list(task_envelope["evidence_bundle"]["evidence_refs"]),
                "proposal_refs": proposal_refs,
                "tool_result_refs": tool_result_refs,
                "reasoning_summary": "terminal=FAILED; reason=final_response_validation_failed",
                "execution_result": {
                    "status": "failed",
                    "artifact_refs": execution_artifact_refs or [],
                },
            }
        self._ledger.emit(
            LedgerEvent(
                request_id=request_id,
                iteration_index=-1,
                event_type="terminal_decision",
                state_to=terminal_state,
                reason_code=reason_code,
                proposal_ref=proposal_refs[-1] if proposal_refs else None,
                tool_result_ref=tool_result_refs[-1] if tool_result_refs else None,
                payload={"outcome": outcome, "execution_status": execution_status},
            )
        )
        return LoopResult(
            terminal_state=terminal_state,
            final_response=final_response,
            trace=self._ledger.reconstruct_trace(request_id),
        )

    @staticmethod
    def _stable_ref(prefix: str, payload: dict[str, Any]) -> str:
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
        return f"{prefix}:{digest}"

    def _preloop_fail_closed(
        self,
        *,
        reason_code: str,
        task_envelope: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> LoopResult:
        req_id = request_id or str((task_envelope or {}).get("request_id", "unknown_request"))
        evidence_bundle = (task_envelope or {}).get("evidence_bundle", {}) if isinstance(task_envelope, dict) else {}
        evidence_refs = list(evidence_bundle.get("evidence_refs", [])) if isinstance(evidence_bundle, dict) else []
        bundle_id = evidence_bundle.get("bundle_id", "unknown_bundle") if isinstance(evidence_bundle, dict) else "unknown_bundle"
        final_response = {
            "schema_version": "final_response.v1",
            "outcome": "failed",
            "evidence_used": {"bundle_id": bundle_id, "item_count": len(evidence_refs)},
            "evidence_refs": evidence_refs,
            "proposal_refs": [],
            "tool_result_refs": [],
            "reasoning_summary": f"terminal=FAILED; reason={reason_code}",
            "execution_result": {"status": "not_run", "artifact_refs": []},
        }
        self._ledger.emit(
            LedgerEvent(
                request_id=req_id,
                iteration_index=-1,
                event_type="terminal_decision",
                state_to="FAILED",
                reason_code=reason_code,
                payload={"outcome": "failed", "execution_status": "not_run"},
            )
        )
        return LoopResult(
            terminal_state="FAILED",
            final_response=final_response,
            trace=self._ledger.reconstruct_trace(req_id),
        )


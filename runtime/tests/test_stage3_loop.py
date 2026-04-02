from __future__ import annotations

from dataclasses import dataclass

import pytest

from runtime.adapters.model_adapter import ModelAdapter
import runtime.loop.loop_controller as loop_controller_module
from runtime.loop.loop_controller import Stage3LoopController
from runtime.loop.state_machine import IllegalTransitionError
from runtime.obs.ledger import Stage3Ledger
from runtime.tools.executor import ToolExecutor
from runtime.state.validators import Stage3ValidationError


def _base_task_envelope(remaining_attempts: int = 2, task_type: str = "ASK") -> dict:
    return {
        "schema_version": "task_envelope.v1",
        "request_id": "req-1",
        "task_type": task_type,
        "constraints": {
            "no_repo_access_from_gpu": True,
            "no_silent_fallback": True,
            "runtime_controls_loop": True,
            "no_reretrieval_inside_loop": True,
        },
        "evidence_bundle": {
            "schema_version": "layer5.evidence_bundle.v1",
            "bundle_id": "bundle-1",
            "workspace_identity_hash": "whash",
            "evidence_refs": ["ev1", "ev2"],
        },
        "attempt_budget": {"max_attempts": 3, "remaining_attempts": remaining_attempts},
        "tool_policy": {
            "allowed": ["echo", "ls", "rm"],
            "mode": "sandboxed",
            "plan_gate_recheck_required": True,
        },
    }


@dataclass
class _PGDecision:
    posture: str


class _PlanGate:
    def __init__(self, postures: list[str]) -> None:
        self._postures = list(postures)

    def evaluate(self, _: dict) -> _PGDecision:
        if self._postures:
            return _PGDecision(self._postures.pop(0))
        return _PGDecision("safe_execute")


class _FakeSandboxExecutor:
    def __init__(self, outcome_type: str = "executed", final_status: str = "executed_ok", blocked_reason: str = "") -> None:
        self.outcome_type = outcome_type
        self.final_status = final_status
        self.blocked_reason = blocked_reason
        self.calls = 0
        self.last_action = None

    def execute_sandbox_action(self, _action):  # noqa: ANN001
        self.calls += 1
        self.last_action = _action
        if self.outcome_type == "blocked":
            return type(
                "BlockedResult",
                (),
                {
                    "outcome_type": "blocked",
                    "blocked_reason": self.blocked_reason or "blocked",
                    "commands_blocked": ["tool"],
                    "ledger_row_id": f"lr-{self.calls}",
                },
            )()
        return type(
            "ExecResult",
            (),
            {
                "outcome_type": "executed",
                "final_status": self.final_status,
                "commands_executed": ["tool"],
                "commands_blocked": [],
                "stderr_summary": (
                    "timeout"
                    if self.final_status == "executed_failed_timeout"
                    else ("terminal failure" if self.final_status == "executed_failed_terminal" else "")
                ),
                "ledger_row_id": f"lr-{self.calls}",
            },
        )()


def _controller(model_callable, *, plan_gate: _PlanGate, sandbox: _FakeSandboxExecutor) -> Stage3LoopController:
    return Stage3LoopController(
        model_adapter=ModelAdapter(model_callable),
        tool_executor=ToolExecutor(sandbox),
        plan_gate_service=plan_gate,
        ledger=Stage3Ledger(),
    )


def test_invalid_proposal_schema() -> None:
    def bad_model(_payload: dict) -> dict:
        return {"schema_version": "model_proposal.v1", "intent_type": "answer_only"}

    controller = _controller(bad_model, plan_gate=_PlanGate(["safe_execute"]), sandbox=_FakeSandboxExecutor())
    result = controller.run(_base_task_envelope(remaining_attempts=1), working_dir=".")
    assert result.terminal_state == "FAILED"
    assert result.final_response["outcome"] == "failed"
    assert result.final_response["execution_result"]["status"] == "not_run"


def test_fake_evidence_refs_rejected() -> None:
    def fake_ref_model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "answer_only",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "observe", "content": "x", "evidence_refs": ["fake_ev"]}
            ],
            "confidence": 0.5,
            "requires_revision": False,
        }

    controller = _controller(fake_ref_model, plan_gate=_PlanGate(["safe_execute"]), sandbox=_FakeSandboxExecutor())
    result = controller.run(_base_task_envelope(remaining_attempts=1), working_dir=".")
    assert result.terminal_state == "FAILED"
    assert "budget_exhausted" in result.final_response["reasoning_summary"]
    assert result.final_response["execution_result"]["status"] == "not_run"


def test_tool_denied_path_is_blocked_execution_truth() -> None:
    def model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "tool_needed",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "tool_rationale", "content": "run tool", "evidence_refs": ["ev1"]}
            ],
            "tool_call": {"tool_name": "rm", "args": {"path": "/tmp/x"}},
            "confidence": 0.8,
            "requires_revision": False,
        }

    controller = _controller(
        model,
        plan_gate=_PlanGate(["safe_execute", "safe_execute"]),
        sandbox=_FakeSandboxExecutor(outcome_type="blocked", blocked_reason="policy deny"),
    )
    result = controller.run(_base_task_envelope(remaining_attempts=1, task_type="CODE"), working_dir=".")
    assert result.terminal_state == "BLOCKED"
    assert result.final_response["outcome"] == "blocked"
    assert result.final_response["execution_result"]["status"] == "blocked"


def test_retry_loop_exhaustion() -> None:
    def invalid_model(_payload: dict) -> dict:
        return {"schema_version": "model_proposal.v1", "intent_type": "answer_only"}

    controller = _controller(invalid_model, plan_gate=_PlanGate(["safe_execute"]), sandbox=_FakeSandboxExecutor())
    result = controller.run(_base_task_envelope(remaining_attempts=1), working_dir=".")
    assert result.terminal_state == "FAILED"
    assert any("invalid_proposal" in r for r in result.trace["reason_code_chain"])
    assert result.final_response["execution_result"]["status"] == "not_run"


def test_plan_gate_refusal() -> None:
    def model(_payload: dict) -> dict:
        raise AssertionError("model should not be called when pre-loop gate refuses")

    controller = _controller(model, plan_gate=_PlanGate(["refuse"]), sandbox=_FakeSandboxExecutor())
    result = controller.run(_base_task_envelope(), working_dir=".")
    assert result.terminal_state == "REFUSED"
    assert result.final_response["outcome"] == "refused"
    assert result.final_response["execution_result"]["status"] == "not_run"


def test_terminal_correctness_success_no_tool_not_run() -> None:
    def answer_model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "answer_only",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "observe", "content": "grounded", "evidence_refs": ["ev1"]}
            ],
            "confidence": 0.9,
            "requires_revision": False,
        }

    controller = _controller(answer_model, plan_gate=_PlanGate(["safe_execute"]), sandbox=_FakeSandboxExecutor())
    result = controller.run(_base_task_envelope(), working_dir=".")
    assert result.terminal_state == "COMPLETED"
    assert result.final_response["outcome"] == "completed"
    assert result.final_response["execution_result"]["status"] == "not_run"


def test_no_silent_fallback() -> None:
    def model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "tool_needed",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "tool_rationale", "content": "needs execute", "evidence_refs": ["ev1"]}
            ],
            "tool_call": {"tool_name": "echo", "args": {"msg": "hi"}},
            "confidence": 0.6,
            "requires_revision": False,
        }

    controller = _controller(
        model,
        plan_gate=_PlanGate(["safe_execute", "defer"]),
        sandbox=_FakeSandboxExecutor(outcome_type="executed"),
    )
    result = controller.run(_base_task_envelope(task_type="EXECUTE", remaining_attempts=1), working_dir=".")
    # no silent fallback: gate defer on risk recheck must terminate, not execute.
    assert result.final_response["outcome"] in {"blocked", "refused"}
    assert "plan_gate" in result.final_response["reasoning_summary"] or "policy_violation" in result.final_response["reasoning_summary"]
    if result.final_response["outcome"] == "blocked":
        assert result.final_response["execution_result"]["status"] == "blocked"
    else:
        assert result.final_response["execution_result"]["status"] == "not_run"


def test_terminal_tool_failure_after_tool_result_ready_regression() -> None:
    def model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "tool_needed",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "tool_rationale", "content": "execute", "evidence_refs": ["ev1"]}
            ],
            "tool_call": {"tool_name": "echo", "args": {"msg": "x"}},
            "confidence": 0.7,
            "requires_revision": False,
        }

    controller = _controller(
        model,
        plan_gate=_PlanGate(["safe_execute", "safe_execute"]),
        sandbox=_FakeSandboxExecutor(outcome_type="executed", final_status="executed_failed_terminal"),
    )
    result = controller.run(_base_task_envelope(task_type="CODE", remaining_attempts=1), working_dir=".")
    assert result.terminal_state == "FAILED"
    assert result.final_response["execution_result"]["status"] == "failed"
    assert any(e["state_from"] == "TOOL_RESULT_READY" and e["state_to"] == "FAILED" for e in result.trace["events"])


def test_tool_success_execution_truth_executed() -> None:
    def model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "tool_needed",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "tool_rationale", "content": "execute", "evidence_refs": ["ev1"]}
            ],
            "tool_call": {"tool_name": "echo", "args": {"msg": "ok"}},
            "confidence": 0.8,
            "requires_revision": False,
        }

    controller = _controller(
        model,
        plan_gate=_PlanGate(["safe_execute", "safe_execute"]),
        sandbox=_FakeSandboxExecutor(outcome_type="executed", final_status="executed_ok"),
    )
    result = controller.run(_base_task_envelope(task_type="EXECUTE", remaining_attempts=1), working_dir=".")
    assert result.terminal_state == "COMPLETED"
    assert result.final_response["execution_result"]["status"] == "executed"
    assert result.final_response["execution_result"]["artifact_refs"] == ["tool_result:lr-1"]


def test_timeout_normalization_and_failed_truth() -> None:
    def model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "tool_needed",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "tool_rationale", "content": "execute", "evidence_refs": ["ev1"]}
            ],
            "tool_call": {"tool_name": "echo", "args": {"msg": "ok"}},
            "confidence": 0.8,
            "requires_revision": False,
        }

    controller = _controller(
        model,
        plan_gate=_PlanGate(["safe_execute", "safe_execute"]),
        sandbox=_FakeSandboxExecutor(outcome_type="executed", final_status="executed_failed_timeout"),
    )
    result = controller.run(_base_task_envelope(task_type="EXECUTE", remaining_attempts=1), working_dir=".")
    assert result.terminal_state == "FAILED"
    assert result.final_response["execution_result"]["status"] == "failed"
    assert "tool_timeout" in result.trace["reason_code_chain"]


def test_explicit_failed_terminal_normalization() -> None:
    fake = _FakeSandboxExecutor(outcome_type="executed", final_status="executed_failed_terminal")
    executor = ToolExecutor(fake)
    request = {
        "schema_version": "tool_execution_request.v1",
        "tool_name": "echo",
        "args": {"msg": "x"},
        "constraints": {"timeout_ms": 30000, "sandbox_required": True, "read_only": False},
    }
    result = executor.execute(request, request_id="rid", working_dir=".")
    assert result["status"] == "failed_terminal"
    assert result["error_class"] == "tool_internal_error"


def test_insufficiency_after_tool_result() -> None:
    def model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "tool_needed",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "tool_rationale", "content": "execute", "evidence_refs": ["ev1"]}
            ],
            "tool_call": {"tool_name": "echo", "args": {"msg": "x"}},
            "confidence": 0.7,
            "requires_revision": False,
        }

    class _InsufficientSandbox(_FakeSandboxExecutor):
        def execute_sandbox_action(self, _action):  # noqa: ANN001
            self.calls += 1
            self.last_action = _action
            return type(
                "ExecResult",
                (),
                {
                    "outcome_type": "executed",
                        "final_status": "executed_partial_insufficient",
                    "commands_executed": ["tool"],
                    "commands_blocked": [],
                        "stderr_summary": "",
                    "ledger_row_id": f"lr-{self.calls}",
                },
            )()

    controller = _controller(
        model,
        plan_gate=_PlanGate(["safe_execute", "safe_execute"]),
        sandbox=_InsufficientSandbox(),
    )
    result = controller.run(_base_task_envelope(task_type="DEBUG", remaining_attempts=1), working_dir=".")
    assert result.terminal_state == "INSUFFICIENT"
    assert result.final_response["outcome"] == "insufficient"


def test_canonical_execution_identity_changes_with_args() -> None:
    fake = _FakeSandboxExecutor(outcome_type="executed", final_status="executed_ok")
    executor = ToolExecutor(fake)
    req1 = {
        "schema_version": "tool_execution_request.v1",
        "tool_name": "echo",
        "args": {"msg": "a"},
        "constraints": {"timeout_ms": 30000, "sandbox_required": True, "read_only": False},
    }
    req2 = {
        "schema_version": "tool_execution_request.v1",
        "tool_name": "echo",
        "args": {"msg": "b"},
        "constraints": {"timeout_ms": 30000, "sandbox_required": True, "read_only": False},
    }
    executor.execute(req1, request_id="r1", working_dir=".")
    hash1 = fake.last_action.metadata["canonical_hash"]
    executor.execute(req2, request_id="r1", working_dir=".")
    hash2 = fake.last_action.metadata["canonical_hash"]
    assert hash1 != hash2


def test_ledger_trace_linkage_contains_refs() -> None:
    def model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "tool_needed",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "tool_rationale", "content": "execute", "evidence_refs": ["ev1"]}
            ],
            "tool_call": {"tool_name": "echo", "args": {"msg": "ok"}},
            "confidence": 0.8,
            "requires_revision": False,
        }

    controller = _controller(
        model,
        plan_gate=_PlanGate(["safe_execute", "safe_execute"]),
        sandbox=_FakeSandboxExecutor(outcome_type="executed", final_status="executed_ok"),
    )
    result = controller.run(_base_task_envelope(task_type="EXECUTE", remaining_attempts=1), working_dir=".")
    linkage = result.trace["iteration_linkage"]
    assert linkage
    first = linkage[min(linkage.keys())]
    assert first["proposal_ref"]
    assert first["decision_ref"]
    assert first["tool_result_ref"]
    assert result.trace["terminal_decision_summary"]["state"] == "COMPLETED"
    assert result.trace["execution_truth_summary"] == "executed"


def test_recheck_gate_blocked_path_semantics() -> None:
    def model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "tool_needed",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "tool_rationale", "content": "execute", "evidence_refs": ["ev1"]}
            ],
            "tool_call": {"tool_name": "echo", "args": {"msg": "x"}},
            "confidence": 0.8,
            "requires_revision": False,
        }

    controller = _controller(
        model,
        plan_gate=_PlanGate(["safe_execute", "bounded_allow"]),
        sandbox=_FakeSandboxExecutor(outcome_type="executed", final_status="executed_ok"),
    )
    result = controller.run(_base_task_envelope(task_type="CODE", remaining_attempts=1), working_dir=".")
    assert result.terminal_state == "BLOCKED"
    assert result.final_response["outcome"] == "blocked"
    assert result.final_response["execution_result"]["status"] == "blocked"


def test_fail_closed_illegal_transition_path() -> None:
    class _BrokenStateMachine:
        def next_state(self, *_args, **_kwargs):  # noqa: ANN002, ANN003
            raise IllegalTransitionError("forced illegal transition")

    def model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "answer_only",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "observe", "content": "x", "evidence_refs": ["ev1"]}
            ],
            "confidence": 0.8,
            "requires_revision": False,
        }

    controller = Stage3LoopController(
        model_adapter=ModelAdapter(model),
        tool_executor=ToolExecutor(_FakeSandboxExecutor()),
        plan_gate_service=_PlanGate(["safe_execute"]),
        ledger=Stage3Ledger(),
        state_machine=_BrokenStateMachine(),  # type: ignore[arg-type]
    )
    result = controller.run(_base_task_envelope(remaining_attempts=1), working_dir=".")
    assert result.terminal_state == "FAILED"
    assert result.final_response["outcome"] == "failed"
    assert "illegal_transition" in result.trace["reason_code_chain"]


def test_tool_result_validation_failure_fail_closed_no_nameerror(monkeypatch: pytest.MonkeyPatch) -> None:
    def model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "tool_needed",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "tool_rationale", "content": "execute", "evidence_refs": ["ev1"]}
            ],
            "tool_call": {"tool_name": "echo", "args": {"msg": "ok"}},
            "confidence": 0.8,
            "requires_revision": False,
        }

    controller = _controller(
        model,
        plan_gate=_PlanGate(["safe_execute", "safe_execute"]),
        sandbox=_FakeSandboxExecutor(outcome_type="executed", final_status="executed_ok"),
    )

    def _raise_validation(*_args, **_kwargs):  # noqa: ANN002, ANN003
        raise Stage3ValidationError("forced validation failure")

    monkeypatch.setattr(controller._tool_executor, "execute", _raise_validation)
    result = controller.run(_base_task_envelope(task_type="EXECUTE", remaining_attempts=1), working_dir=".")
    assert result.terminal_state == "FAILED"
    assert result.final_response["outcome"] == "failed"
    assert "internal_schema_validation_failed" in result.trace["reason_code_chain"]


def test_final_response_validation_failure_consistency(monkeypatch: pytest.MonkeyPatch) -> None:
    def answer_model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "answer_only",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "observe", "content": "grounded", "evidence_refs": ["ev1"]}
            ],
            "confidence": 0.9,
            "requires_revision": False,
        }

    controller = _controller(answer_model, plan_gate=_PlanGate(["safe_execute"]), sandbox=_FakeSandboxExecutor())

    def _raise_final_response_validation(*_args, **_kwargs):  # noqa: ANN002, ANN003
        raise Stage3ValidationError("forced final_response validation fail")

    monkeypatch.setattr(loop_controller_module, "validate_final_response", _raise_final_response_validation)
    result = controller.run(_base_task_envelope(remaining_attempts=1), working_dir=".")
    assert result.final_response["outcome"] == "failed"
    assert result.terminal_state == "FAILED"
    assert result.trace["terminal_decision_summary"]["outcome"] == "failed"
    assert result.trace["execution_truth_summary"] == "failed"


def test_preloop_invalid_task_envelope_fail_closed() -> None:
    def model(_payload: dict) -> dict:
        return {}

    controller = _controller(model, plan_gate=_PlanGate(["safe_execute"]), sandbox=_FakeSandboxExecutor())
    invalid = _base_task_envelope()
    invalid.pop("schema_version")
    result = controller.run(invalid, working_dir=".")
    assert result.terminal_state == "FAILED"
    assert result.final_response["outcome"] == "failed"
    assert "invalid_task_envelope" in result.trace["reason_code_chain"]


def test_preloop_plan_gate_error_fail_closed() -> None:
    class _ErrorPlanGate:
        def evaluate(self, _req):  # noqa: ANN001
            raise RuntimeError("plan gate down")

    def model(_payload: dict) -> dict:
        return {}

    controller = Stage3LoopController(
        model_adapter=ModelAdapter(model),
        tool_executor=ToolExecutor(_FakeSandboxExecutor()),
        plan_gate_service=_ErrorPlanGate(),
        ledger=Stage3Ledger(),
    )
    result = controller.run(_base_task_envelope(), working_dir=".")
    assert result.terminal_state == "FAILED"
    assert result.final_response["outcome"] == "failed"
    assert "preloop_plan_gate_failed" in result.trace["reason_code_chain"]


def test_loop_context_frame_validation_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def answer_model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "answer_only",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "observe", "content": "grounded", "evidence_refs": ["ev1"]}
            ],
            "confidence": 0.9,
            "requires_revision": False,
        }

    controller = _controller(answer_model, plan_gate=_PlanGate(["safe_execute"]), sandbox=_FakeSandboxExecutor())

    def _raise_frame_validation(*_args, **_kwargs):  # noqa: ANN002, ANN003
        raise Stage3ValidationError("forced frame invalid")

    monkeypatch.setattr(loop_controller_module, "validate_loop_context_frame", _raise_frame_validation)
    result = controller.run(_base_task_envelope(remaining_attempts=1), working_dir=".")
    assert result.terminal_state == "FAILED"
    assert result.final_response["outcome"] == "failed"
    assert "loop_context_frame_validation_failed" in result.trace["reason_code_chain"]


def test_inloop_plan_gate_recheck_exception_fail_closed() -> None:
    class _FlakyPlanGate:
        def __init__(self) -> None:
            self.calls = 0

        def evaluate(self, _req):  # noqa: ANN001
            self.calls += 1
            if self.calls == 1:
                return _PGDecision("safe_execute")
            raise RuntimeError("recheck failed")

    def model(_payload: dict) -> dict:
        return {
            "schema_version": "model_proposal.v1",
            "intent_type": "tool_needed",
            "reasoning_trace": [
                {"step_id": "s1", "kind": "tool_rationale", "content": "execute", "evidence_refs": ["ev1"]}
            ],
            "tool_call": {"tool_name": "echo", "args": {"msg": "ok"}},
            "confidence": 0.8,
            "requires_revision": False,
        }

    sandbox = _FakeSandboxExecutor(outcome_type="executed", final_status="executed_ok")
    controller = Stage3LoopController(
        model_adapter=ModelAdapter(model),
        tool_executor=ToolExecutor(sandbox),
        plan_gate_service=_FlakyPlanGate(),
        ledger=Stage3Ledger(),
    )
    result = controller.run(_base_task_envelope(task_type="EXECUTE", remaining_attempts=1), working_dir=".")
    assert sandbox.calls == 0
    assert result.terminal_state == "FAILED"
    assert result.final_response["outcome"] == "failed"
    assert result.final_response["execution_result"]["status"] == "not_run"
    assert "inloop_plan_gate_failed" in result.trace["reason_code_chain"]
    assert result.trace["terminal_decision_summary"]["outcome"] == result.final_response["outcome"]
    assert result.trace["execution_truth_summary"] == result.final_response["execution_result"]["status"]

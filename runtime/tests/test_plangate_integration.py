"""
M3.3 Plan-Gate integration tests.

Verify: refusal prevents sandbox; defer prevents sandbox; safe_execute allows sandbox;
Plan-Gate decisions are persisted to ledger. Deterministic behavior.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from runtime.plangate.plangate_decision import PlanGateDecision
from runtime.plangate.plangate_service import PlanGateService
from runtime.sandbox.sandbox_ledger_store import (
    EVENT_PLANGATE_DEFERRED,
    EVENT_PLANGATE_REFUSED,
    EVENT_PLANGATE_SAFE_EXECUTE,
    SandboxLedgerStore,
)
from runtime.sandbox.sandbox_executor import SandboxExecutor
from runtime.state.store import TaskStateStore
from runtime.state.transitions import TransitionValidator
from runtime.orchestrator.loop_controller import LoopController


class TestPlanGateDecision:
    """PlanGateDecision model."""

    def test_may_execute_only_safe_execute(self) -> None:
        assert PlanGateDecision("safe_execute", True, False, False, "ok").may_execute is True
        assert PlanGateDecision("refuse", False, True, True, "no").may_execute is False
        assert PlanGateDecision("defer", True, False, False, "later").may_execute is False
        assert PlanGateDecision("bounded_allow", True, False, False, "bounded").may_execute is False

    def test_to_dict_roundtrip(self) -> None:
        d = PlanGateDecision("safe_execute", True, False, False, "reason")
        assert PlanGateDecision.from_dict(d.to_dict()).posture == d.posture


class TestPlanGateService:
    """PlanGateService deterministic evaluation."""

    def test_curl_refused(self) -> None:
        svc = PlanGateService()
        d = svc.evaluate({"request_id": "r1", "command": ["curl", "http://x.com"]})
        assert d.posture == "refuse"
        assert not d.may_execute

    def test_echo_safe_execute(self) -> None:
        svc = PlanGateService()
        d = svc.evaluate({"request_id": "r2", "command": ["echo", "hi"]})
        assert d.posture == "safe_execute"
        assert d.may_execute

    def test_force_defer(self) -> None:
        svc = PlanGateService()
        d = svc.evaluate({"request_id": "r3", "command": ["echo", "x"], "plan_gate_defer": True})
        assert d.posture == "defer"
        assert not d.may_execute

    def test_force_refuse(self) -> None:
        svc = PlanGateService()
        d = svc.evaluate({"request_id": "r4", "command": ["echo", "x"], "plan_gate_refuse": True})
        assert d.posture == "refuse"
        assert not d.may_execute

    def test_force_bounded_allow(self) -> None:
        svc = PlanGateService()
        d = svc.evaluate({"request_id": "r5", "command": ["echo", "x"], "plan_gate_bounded_allow": True})
        assert d.posture == "bounded_allow"
        assert not d.may_execute
        assert "bounded_allow" in (d.reason or "").lower()

    def test_bounded_allow_does_not_override_refuse(self) -> None:
        """force_refuse must dominate over bounded_allow."""
        svc = PlanGateService()
        d = svc.evaluate({"request_id": "r6", "plan_gate_refuse": True, "plan_gate_bounded_allow": True})
        assert d.posture == "refuse"

    def test_bounded_allow_does_not_override_defer(self) -> None:
        """force_defer must dominate over bounded_allow."""
        svc = PlanGateService()
        d = svc.evaluate({"request_id": "r7", "plan_gate_defer": True, "plan_gate_bounded_allow": True})
        assert d.posture == "defer"


class TestPlanGateLoopControllerIntegration:
    """Plan-Gate + LoopController: refusal/defer prevent sandbox; safe_execute allows."""

    def test_plangate_refusal_prevents_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(ledger)
            executor = SandboxExecutor(ledger_store=store)
            controller = LoopController(
                store=TaskStateStore(),
                validator=TransitionValidator(),
                sandbox_executor=executor,
                ledger_store=store,
                plan_gate_service=PlanGateService(),
            )
            controller.create_task("t1", metadata={"plan_hash": "ph", "working_dir": tmp})
            state = controller.store.load("t1")
            assert state is not None
            state.current_state = "PROPOSAL_VALIDATED"
            controller.store.save(state)
            r = controller.apply_transition(
                "t1",
                transition_id="validated_to_sandbox",
                guard_inputs={"command": ["curl", "http://evil.com"], "working_dir": tmp},
            )
            assert r.valid is False
            # Reason may be from DeterministicGuard (pre-gate), AuthorityValidator, or old format
            assert any(
                phrase in r.reason.lower()
                for phrase in (
                    "not permitted",
                    "refused",
                    "authority denied",
                    "not authorized",
                    "not allowed",
                    "pre-gate",
                )
            )
            state2 = controller.store.load("t1")
            assert state2 is not None
            assert state2.current_state == "PROPOSAL_VALIDATED"
            all_rows = store.list_all()
            # Plan-Gate refusal path persists plangate_refused; sandbox refusal row also written
            assert any(
                row.event_type in ("plangate_refused", "sandbox_refused") for row in all_rows
            )

    def test_plangate_defer_prevents_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(ledger)
            executor = SandboxExecutor(ledger_store=store)
            controller = LoopController(
                store=TaskStateStore(),
                validator=TransitionValidator(),
                sandbox_executor=executor,
                ledger_store=store,
                plan_gate_service=PlanGateService(),
            )
            controller.create_task("t2", metadata={"plan_hash": "ph", "working_dir": tmp})
            state = controller.store.load("t2")
            assert state is not None
            state.current_state = "PROPOSAL_VALIDATED"
            controller.store.save(state)
            r = controller.apply_transition(
                "t2",
                transition_id="validated_to_sandbox",
                guard_inputs={"command": ["echo", "x"], "working_dir": tmp, "plan_gate_defer": True},
            )
            assert r.valid is False
            assert r.stop_reason == "deferred" or "defer" in (r.reason or "").lower()
            state2 = controller.store.load("t2")
            assert state2 is not None
            assert state2.current_state == "PROPOSAL_VALIDATED"
            all_rows = store.list_all()
            assert any(
                row.event_type == "plangate_deferred" for row in all_rows
            ), f"expected plangate_deferred in {[r.event_type for r in all_rows]}"
            assert r.stop_reason == "deferred"

    def test_plangate_bounded_allow_prevents_sandbox(self) -> None:
        """bounded_allow must not launch sandbox; distinct stop_reason and ledger event from defer."""
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(ledger)
            executor = SandboxExecutor(ledger_store=store)
            controller = LoopController(
                store=TaskStateStore(),
                validator=TransitionValidator(),
                sandbox_executor=executor,
                ledger_store=store,
                plan_gate_service=PlanGateService(),
            )
            controller.create_task("tb", metadata={"plan_hash": "ph", "working_dir": tmp})
            state = controller.store.load("tb")
            assert state is not None
            state.current_state = "PROPOSAL_VALIDATED"
            controller.store.save(state)
            r = controller.apply_transition(
                "tb",
                transition_id="validated_to_sandbox",
                guard_inputs={"command": ["echo", "x"], "working_dir": tmp, "plan_gate_bounded_allow": True},
            )
            assert r.valid is False
            assert r.stop_reason == "bounded_allow"
            assert "bounded_allow" in (r.reason or "").lower()
            state2 = controller.store.load("tb")
            assert state2 is not None
            assert state2.current_state == "PROPOSAL_VALIDATED"
            all_rows = store.list_all()
            assert any(
                row.event_type == "plangate_bounded_allow" for row in all_rows
            ), f"expected plangate_bounded_allow in {[x.event_type for x in all_rows]}"
            assert r.ledger_row_id

    def test_plangate_safe_execute_allows_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(ledger)
            executor = SandboxExecutor(ledger_store=store)
            controller = LoopController(
                store=TaskStateStore(),
                validator=TransitionValidator(),
                sandbox_executor=executor,
                ledger_store=store,
                plan_gate_service=PlanGateService(),
            )
            controller.create_task("t3", metadata={"plan_hash": "ph", "working_dir": tmp})
            state = controller.store.load("t3")
            assert state is not None
            state.current_state = "PROPOSAL_VALIDATED"
            controller.store.save(state)
            r = controller.apply_transition(
                "t3",
                transition_id="validated_to_sandbox",
                guard_inputs={"command": ["echo", "ok"], "working_dir": tmp},
            )
            assert r.valid is True
            state2 = controller.store.load("t3")
            assert state2 is not None
            assert state2.current_state == "SANDBOX_EXECUTED"
            assert state2.metadata.get("last_sandbox_success") is True
            all_rows = store.list_all()
            assert any(
                row.event_type == "plangate_safe_execute" for row in all_rows
            ), f"expected plangate_safe_execute in {[r.event_type for r in all_rows]}"
            assert any(row.event_type == "sandbox_executed" for row in all_rows)

    def test_plangate_decision_persists_ledger_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.db"
            store = SandboxLedgerStore(ledger)
            executor = SandboxExecutor(ledger_store=store)
            controller = LoopController(
                store=TaskStateStore(),
                validator=TransitionValidator(),
                sandbox_executor=executor,
                ledger_store=store,
                plan_gate_service=PlanGateService(),
            )
            controller.create_task("t4", metadata={"plan_hash": "ph", "working_dir": tmp})
            state = controller.store.load("t4")
            assert state is not None
            state.current_state = "PROPOSAL_VALIDATED"
            controller.store.save(state)
            controller.apply_transition(
                "t4",
                transition_id="validated_to_sandbox",
                guard_inputs={"command": ["echo", "y"], "working_dir": tmp},
            )
            rows = store.get_by_request_id("t4")
            plangate_rows = [r for r in rows if r.event_type.startswith("plangate_")]
            assert len(plangate_rows) >= 1
            assert plangate_rows[0].payload.get("decision_posture") == "safe_execute"
            assert plangate_rows[0].payload.get("request_id") == "t4"

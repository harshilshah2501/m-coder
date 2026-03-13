#!/usr/bin/env python3
"""
Canonical M3.2/M3.3 governed execution demo — runtime CLI / test harness entry.

Flow: request → Plan-Gate → LoopController → (sandbox if safe_execute) → ledger.

  CASE A — SAFE_EXECUTE → EXECUTED: Plan-Gate allows; sandbox runs; execution row persisted.
  CASE B — REFUSE: Plan-Gate refuses (e.g. curl); refusal + plangate_refused persisted.
  CASE C — REFUSED (no gate): controller has no Plan-Gate → refuse; refusal row persisted.
  CASE D — DEFER: Plan-Gate defers; plangate_deferred persisted; sandbox does not run.
  CASE E — BOUNDED_ALLOW: Plan-Gate bounded_allow; plangate_bounded_allow persisted; sandbox does not run.

Run: python3 -m runtime.sandbox.demo_governed_execution
Or:  pytest runtime/tests/test_sandbox_demo_e2e.py -v
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from runtime.sandbox.sandbox_executor import SandboxExecutor
from runtime.sandbox.sandbox_ledger_store import SandboxLedgerStore
from runtime.state.store import TaskStateStore
from runtime.state.transitions import TransitionValidator
from runtime.orchestrator.loop_controller import LoopController
from runtime.plangate.plangate_service import PlanGateService


def _controller_for_executed_blocked(ledger_path: Path, work_dir: Path) -> LoopController:
    """Controller with Plan-Gate, executor, and ledger_store (same spine)."""
    store = SandboxLedgerStore(ledger_path)
    executor = SandboxExecutor(ledger_store=store)
    task_store = TaskStateStore()
    return LoopController(
        store=task_store,
        validator=TransitionValidator(),
        sandbox_executor=executor,
        ledger_store=store,
        plan_gate_service=PlanGateService(),
    )


def run_case_executed(ledger_path: Path, work_dir: Path) -> dict:
    """CASE A — EXECUTED: controller → validated_to_sandbox → executor runs allowed command; execution row persisted."""
    controller = _controller_for_executed_blocked(ledger_path, work_dir)
    controller.create_task("demo-executed", metadata={"plan_hash": "plan-demo", "working_dir": str(work_dir)})
    state = controller.store.load("demo-executed")
    assert state is not None
    state.current_state = "PROPOSAL_VALIDATED"
    controller.store.save(state)

    r = controller.apply_transition(
        "demo-executed",
        transition_id="validated_to_sandbox",
        guard_inputs={"command": ["echo", "hello"], "working_dir": str(work_dir)},
    )
    assert r.valid, r.reason
    state = controller.store.load("demo-executed")
    assert state is not None
    assert state.current_state == "SANDBOX_EXECUTED"
    assert state.metadata.get("last_sandbox_success") is True
    lid = state.metadata.get("last_sandbox_ledger_id", "")
    assert lid
    return {"outcome_type": "executed", "success": True, "ledger_row_id": lid, "request_id": "demo-executed"}


def run_case_blocked(ledger_path: Path, work_dir: Path) -> dict:
    """CASE B — REFUSE: Plan-Gate refuses curl; sandbox does not run; plangate_refused + refusal persisted."""
    controller = _controller_for_executed_blocked(ledger_path, work_dir)
    controller.create_task("demo-blocked", metadata={"plan_hash": "plan-demo", "working_dir": str(work_dir)})
    state = controller.store.load("demo-blocked")
    assert state is not None
    state.current_state = "PROPOSAL_VALIDATED"
    controller.store.save(state)

    r = controller.apply_transition(
        "demo-blocked",
        transition_id="validated_to_sandbox",
        guard_inputs={"command": ["curl", "http://example.com"], "working_dir": str(work_dir)},
    )
    assert not r.valid, "Plan-Gate must refuse curl"
    assert r.ledger_row_id
    return {"outcome_type": "refused", "success": False, "ledger_row_id": r.ledger_row_id, "request_id": "demo-blocked", "reason": r.reason}


def run_case_refused(ledger_path: Path, work_dir: Path) -> tuple[bool, str, str | None]:
    """
    CASE C — REFUSED: controller has no Plan-Gate; validated_to_sandbox refused; refusal row persisted.
    Returns (valid, reason, ledger_row_id).
    """
    store = SandboxLedgerStore(ledger_path)
    controller = LoopController(sandbox_executor=None, ledger_store=store)
    controller.create_task("demo-refused", metadata={"plan_hash": "plan-demo"})
    state = controller.store.load("demo-refused")
    assert state is not None
    state.current_state = "PROPOSAL_VALIDATED"
    controller.store.save(state)
    r = controller.apply_transition(
        "demo-refused",
        transition_id="validated_to_sandbox",
        guard_inputs={"command": ["echo", "x"], "working_dir": str(work_dir)},
    )
    assert not r.valid
    assert r.ledger_row_id, "Refusal must produce a ledger row"
    return (r.valid, r.reason, r.ledger_row_id)


def run_case_deferred(ledger_path: Path, work_dir: Path) -> dict:
    """CASE D — DEFER: Plan-Gate defers; sandbox does not run; plangate_deferred persisted."""
    controller = _controller_for_executed_blocked(ledger_path, work_dir)
    controller.create_task("demo-deferred", metadata={"plan_hash": "plan-demo", "working_dir": str(work_dir)})
    state = controller.store.load("demo-deferred")
    assert state is not None
    state.current_state = "PROPOSAL_VALIDATED"
    controller.store.save(state)
    r = controller.apply_transition(
        "demo-deferred",
        transition_id="validated_to_sandbox",
        guard_inputs={"command": ["echo", "ok"], "working_dir": str(work_dir), "plan_gate_defer": True},
    )
    assert not r.valid
    assert "defer" in (r.reason or "").lower() or r.stop_reason == "deferred"
    return {"outcome_type": "deferred", "valid": False, "ledger_row_id": r.ledger_row_id, "reason": r.reason}


def run_case_bounded_allow(ledger_path: Path, work_dir: Path) -> dict:
    """CASE E — BOUNDED_ALLOW: Plan-Gate bounded_allow; sandbox does not run; plangate_bounded_allow persisted."""
    controller = _controller_for_executed_blocked(ledger_path, work_dir)
    controller.create_task("demo-bounded", metadata={"plan_hash": "plan-demo", "working_dir": str(work_dir)})
    state = controller.store.load("demo-bounded")
    assert state is not None
    state.current_state = "PROPOSAL_VALIDATED"
    controller.store.save(state)
    r = controller.apply_transition(
        "demo-bounded",
        transition_id="validated_to_sandbox",
        guard_inputs={"command": ["echo", "ok"], "working_dir": str(work_dir), "plan_gate_bounded_allow": True},
    )
    assert not r.valid
    assert r.stop_reason == "bounded_allow"
    assert r.ledger_row_id
    return {"outcome_type": "bounded_allow", "valid": False, "ledger_row_id": r.ledger_row_id, "reason": r.reason}


def run_all_cases(ledger_path: Path | None = None, work_dir: Path | None = None) -> dict:
    """Run all cases (executed, refused-by-gate, refused-no-gate, deferred, bounded_allow) through controller + Plan-Gate."""
    if work_dir is None:
        work_dir = Path(tempfile.mkdtemp())
    if ledger_path is None:
        fd, path = tempfile.mkstemp(suffix=".db")
        import os
        os.close(fd)
        ledger_path = Path(path)
    ledger_path = Path(ledger_path)
    work_dir = Path(work_dir)

    executed = run_case_executed(ledger_path, work_dir)
    blocked = run_case_blocked(ledger_path, work_dir)
    valid, reason, refusal_ledger_id = run_case_refused(ledger_path, work_dir)
    deferred = run_case_deferred(ledger_path, work_dir)
    bounded_allow = run_case_bounded_allow(ledger_path, work_dir)

    store = SandboxLedgerStore(ledger_path)
    rows = store.list_all()

    return {
        "executed": executed,
        "blocked": blocked,
        "refused": {"valid": valid, "reason": reason, "ledger_row_id": refusal_ledger_id},
        "deferred": deferred,
        "bounded_allow": bounded_allow,
        "ledger_path": str(ledger_path),
        "ledger_row_count": len(rows),
        "ledger_rows": [r.to_dict() for r in rows],
    }


def main() -> None:
    import json
    summary = run_all_cases()
    print("M3.2/M3.3 Governed Execution Demo — Plan-Gate + Controller spine")
    print("=" * 60)
    print("SAFE_EXECUTE → EXECUTED:", summary["executed"].get("ledger_row_id"))
    print("REFUSE (curl):", summary["blocked"].get("ledger_row_id"), summary["blocked"].get("reason", "")[:50])
    print("REFUSED (no gate): valid=", summary["refused"]["valid"], "ledger_row_id:", summary["refused"].get("ledger_row_id"))
    print("DEFER:", summary["deferred"].get("ledger_row_id"), summary["deferred"].get("reason", "")[:50])
    print("BOUNDED_ALLOW:", summary["bounded_allow"].get("ledger_row_id"), summary["bounded_allow"].get("reason", "")[:50])
    print("Ledger path:", summary["ledger_path"], "rows:", summary["ledger_row_count"])
    print()
    print("Full summary (JSON):")
    print(json.dumps({k: v for k, v in summary.items() if k != "ledger_rows"}, indent=2))


if __name__ == "__main__":
    main()

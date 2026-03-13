#!/usr/bin/env python3
"""
Shadow Runner Demo — Deterministic Runtime Emulator (M3.E0).

Simulates three IDE-like events:
1. merge_without_approval → REF → refuse
2. commit_prod_change → CONF → bounded_allow
3. safe_commit → DES → safe_execute

Run: python -m runtime.shadow_runner.run_demo
"""

from __future__ import annotations

import json
import sys
from typing import Any

from runtime.plan_gate_stub.plan_gate import Decision, PlanGate, PlanDecision, Phase
from runtime.emulator.ledger import LedgerRow


def create_event(
    action_type: str,
    user_context: dict[str, Any],
    boundary_phrase: str = "",
    request_id: str = "req-001",
    session_id: str = "sess-001",
) -> dict[str, Any]:
    """Create a simulated IDE event."""
    return {
        "action_type": action_type,
        "user_context": user_context,
        "boundary_phrase": boundary_phrase,
        "request_id": request_id,
        "session_id": session_id,
        "mode": "shadow",
    }


def print_separator() -> None:
    print("=" * 70)


def print_decision(scenario: str, decision: PlanDecision, ledger: LedgerRow) -> None:
    """Print decision details."""
    print(f"\nScenario: {scenario}")
    print("-" * 40)
    print(f"  Phase:            {decision.phase.value}")
    print(f"  Decision:         {decision.decision.value}")
    print(f"  Authority:        {decision.authority_verdict.value}")
    print(f"  Boundary:         {decision.boundary_verdict.value}")
    print(f"  Plan Hash:        {decision.plan_hash[:16]}...")
    print(f"  Boundary Hash:    {decision.boundary_phrase_hash[:16] if decision.boundary_phrase_hash else 'N/A'}...")
    print(f"  Reason Codes:     {', '.join(decision.reason_codes)}")
    print(f"  Ledger Event ID:  {ledger.event_id[:16]}...")
    print(f"  Terminal Posture: {ledger.terminal_posture}")


def scenario_merge_without_approval(gate: PlanGate) -> tuple[PlanDecision, LedgerRow]:
    """
    Scenario 1: merge_without_approval
    
    Expected: REF → refuse
    - No approval chain
    - No approval token
    - Risky action type
    """
    event = create_event(
        action_type="merge_without_approval",
        user_context={
            "user_id": "user-123",
            "role": "developer",
        },
        boundary_phrase="merge to production branch",
        request_id="req-merge-001",
    )
    decision, ledger, _ = gate.evaluate_plan(event)
    return decision, ledger


def scenario_commit_prod_change(gate: PlanGate) -> tuple[PlanDecision, LedgerRow]:
    """
    Scenario 2: commit_prod_change
    
    Expected: CONF → bounded_allow
    - Has approval token
    - Has approval chain
    - Boundary present (production)
    """
    event = create_event(
        action_type="commit_prod_change",
        user_context={
            "user_id": "user-456",
            "role": "admin",
            "approval_token": "tok-abc123",
            "approval_chain": ["approver-1", "approver-2"],
        },
        boundary_phrase="commit changes to production config",
        request_id="req-commit-001",
    )
    decision, ledger, _ = gate.evaluate_plan(event)
    return decision, ledger


def scenario_safe_commit(gate: PlanGate) -> tuple[PlanDecision, LedgerRow]:
    """
    Scenario 3: safe_commit
    
    Expected: DES → safe_execute
    - Safe action type
    - Authority passes
    - No boundary detected
    """
    event = create_event(
        action_type="safe_commit",
        user_context={
            "user_id": "user-789",
            "role": "developer",
        },
        boundary_phrase="",
        request_id="req-safe-001",
    )
    decision, ledger, _ = gate.evaluate_plan(event)
    return decision, ledger


def validate_invariants(
    results: list[tuple[str, PlanDecision, LedgerRow]],
) -> tuple[bool, list[str]]:
    """
    Validate constitutional invariants.
    
    Invariants:
    1. authority_fail never produces safe_execute
    2. boundary_present never produces defer
    3. shadow mode never emits boundary_verdict=crossed
    """
    violations: list[str] = []
    
    for scenario, decision, ledger in results:
        if decision.authority_verdict.value == "fail":
            if decision.decision == Decision.SAFE_EXECUTE:
                violations.append(
                    f"{scenario}: authority_fail produced safe_execute (INVARIANT VIOLATION)"
                )
        
        if decision.boundary_verdict.value in ("present", "detected"):
            if ledger.terminal_posture == "defer":
                violations.append(
                    f"{scenario}: boundary_present produced defer (INVARIANT VIOLATION)"
                )
        
        if ledger.mode == "shadow":
            if ledger.boundary_verdict == "crossed":
                violations.append(
                    f"{scenario}: shadow mode emitted boundary_verdict=crossed (INVARIANT VIOLATION)"
                )
    
    return len(violations) == 0, violations


def main() -> int:
    """Run the shadow demo."""
    print_separator()
    print("Deterministic Runtime Emulator — Shadow Runner Demo (M3.E0)")
    print_separator()
    
    gate = PlanGate(mode="shadow")
    results: list[tuple[str, PlanDecision, LedgerRow]] = []
    
    print("\n[1/3] Running scenario: merge_without_approval")
    decision1, ledger1 = scenario_merge_without_approval(gate)
    print_decision("merge_without_approval", decision1, ledger1)
    results.append(("merge_without_approval", decision1, ledger1))
    
    print("\n[2/3] Running scenario: commit_prod_change")
    decision2, ledger2 = scenario_commit_prod_change(gate)
    print_decision("commit_prod_change", decision2, ledger2)
    results.append(("commit_prod_change", decision2, ledger2))
    
    print("\n[3/3] Running scenario: safe_commit")
    decision3, ledger3 = scenario_safe_commit(gate)
    print_decision("safe_commit", decision3, ledger3)
    results.append(("safe_commit", decision3, ledger3))
    
    print_separator()
    print("\nExpected vs Actual Results:")
    print("-" * 40)
    
    expected = [
        ("merge_without_approval", Phase.REF, Decision.REFUSAL, "refuse"),
        ("commit_prod_change", Phase.CONF, Decision.BOUNDED_ALLOW, "bounded_allow"),
        ("safe_commit", Phase.DES, Decision.SAFE_EXECUTE, "safe_execute"),
    ]
    
    all_match = True
    for (scenario, exp_phase, exp_decision, exp_posture), (_, decision, ledger) in zip(expected, results):
        phase_ok = decision.phase == exp_phase
        decision_ok = decision.decision == exp_decision
        posture_ok = ledger.terminal_posture == exp_posture
        
        status = "PASS" if (phase_ok and decision_ok and posture_ok) else "FAIL"
        if status == "FAIL":
            all_match = False
        
        print(f"  {scenario}:")
        print(f"    Phase:    {decision.phase.value} (expected: {exp_phase.value}) [{status if phase_ok else 'FAIL'}]")
        print(f"    Decision: {decision.decision.value} (expected: {exp_decision.value}) [{status if decision_ok else 'FAIL'}]")
        print(f"    Posture:  {ledger.terminal_posture} (expected: {exp_posture}) [{status if posture_ok else 'FAIL'}]")
    
    print_separator()
    print("\nInvariant Validation:")
    print("-" * 40)
    
    invariants_ok, violations = validate_invariants(results)
    
    if invariants_ok:
        print("  [PASS] authority_fail never produces safe_execute")
        print("  [PASS] boundary_present never produces defer")
        print("  [PASS] shadow mode never emits boundary_verdict=crossed")
    else:
        for v in violations:
            print(f"  [FAIL] {v}")
    
    print_separator()
    print("\nLedger Records (JSON):")
    print("-" * 40)
    
    for scenario, decision, ledger in results:
        print(f"\n{scenario}:")
        print(json.dumps(ledger.to_dict(), indent=2))
    
    print_separator()
    
    if all_match and invariants_ok:
        print("\n✓ DEMO COMPLETE — All scenarios passed, all invariants held.")
        return 0
    else:
        print("\n✗ DEMO FAILED — Some checks did not pass.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

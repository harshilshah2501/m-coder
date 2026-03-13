"""
Invariant Tests — Deterministic Runtime Emulator (M3.E0).

Tests verify constitutional invariants:
1. authority_fail never produces safe_execute
2. boundary_present never produces defer
3. shadow mode never emits boundary_verdict=crossed

No LLM. No inference. Deterministic evaluation only.
"""

from __future__ import annotations

import unittest
from typing import Any

from runtime.plan_gate_stub.plan_gate import Decision, Phase, PlanDecision, PlanGate
from runtime.emulator.authority import AuthorityChecker, AuthorityVerdict
from runtime.emulator.boundary import BoundaryDetector, BoundaryVerdict
from runtime.emulator.ledger import LedgerEmitter, LedgerRow


def make_event(
    action_type: str = "safe_commit",
    user_context: dict[str, Any] | None = None,
    boundary_phrase: str = "",
    request_id: str = "req-test",
    session_id: str = "sess-test",
    mode: str = "shadow",
) -> dict[str, Any]:
    """Create a test event."""
    return {
        "action_type": action_type,
        "user_context": user_context or {"user_id": "u1", "role": "admin"},
        "boundary_phrase": boundary_phrase,
        "request_id": request_id,
        "session_id": session_id,
        "mode": mode,
    }


class TestAuthorityChecker(unittest.TestCase):
    """Unit tests for AuthorityChecker."""
    
    def setUp(self) -> None:
        self.checker = AuthorityChecker()
    
    def test_missing_user_id_fails(self) -> None:
        result = self.checker.check({}, "safe_commit")
        self.assertEqual(result, AuthorityVerdict.FAIL)
    
    def test_missing_role_fails(self) -> None:
        result = self.checker.check({"user_id": "u1"}, "safe_commit")
        self.assertEqual(result, AuthorityVerdict.FAIL)
    
    def test_risky_action_without_token_fails(self) -> None:
        ctx = {"user_id": "u1", "role": "admin"}
        result = self.checker.check(ctx, "merge_without_approval")
        self.assertEqual(result, AuthorityVerdict.FAIL)
    
    def test_risky_action_with_token_passes(self) -> None:
        ctx = {"user_id": "u1", "role": "admin", "approval_token": "tok-123"}
        result = self.checker.check(ctx, "commit_prod_change")
        self.assertEqual(result, AuthorityVerdict.PASS)
    
    def test_required_approval_without_chain_fails(self) -> None:
        ctx = {"user_id": "u1", "role": "admin", "approval_token": "tok-123"}
        result = self.checker.check(ctx, "merge_without_approval")
        self.assertEqual(result, AuthorityVerdict.FAIL)
    
    def test_required_approval_with_chain_passes(self) -> None:
        ctx = {
            "user_id": "u1",
            "role": "admin",
            "approval_token": "tok-123",
            "approval_chain": ["approver-1"],
        }
        result = self.checker.check(ctx, "merge_without_approval")
        self.assertEqual(result, AuthorityVerdict.PASS)
    
    def test_safe_action_passes(self) -> None:
        ctx = {"user_id": "u1", "role": "developer"}
        result = self.checker.check(ctx, "safe_commit")
        self.assertEqual(result, AuthorityVerdict.PASS)


class TestBoundaryDetector(unittest.TestCase):
    """Unit tests for BoundaryDetector."""
    
    def setUp(self) -> None:
        self.detector = BoundaryDetector()
    
    def test_no_boundary_returns_none(self) -> None:
        result = self.detector.detect("safe_commit", "")
        self.assertEqual(result, BoundaryVerdict.NONE)
    
    def test_boundary_action_returns_present(self) -> None:
        result = self.detector.detect("commit_prod_change", "")
        self.assertEqual(result, BoundaryVerdict.PRESENT)
    
    def test_irreversible_phrase_returns_detected(self) -> None:
        result = self.detector.detect("safe_commit", "merge to main branch")
        self.assertEqual(result, BoundaryVerdict.DETECTED)
    
    def test_boundary_action_with_phrase_returns_detected(self) -> None:
        result = self.detector.detect("commit_prod_change", "deploy to production")
        self.assertEqual(result, BoundaryVerdict.DETECTED)
    
    def test_shadow_mode_never_crossed(self) -> None:
        """Invariant: shadow mode never emits crossed."""
        result = self.detector.detect("commit_prod_change", "deploy to production", mode="shadow")
        self.assertNotEqual(result, BoundaryVerdict.CROSSED)


class TestPlanGateInvariants(unittest.TestCase):
    """Integration tests for PlanGate constitutional invariants."""
    
    def setUp(self) -> None:
        self.gate = PlanGate(mode="shadow")
    
    def test_authority_fail_never_safe_execute(self) -> None:
        """Invariant: authority_fail never produces safe_execute."""
        event = make_event(
            action_type="merge_without_approval",
            user_context={"user_id": "u1", "role": "developer"},
            boundary_phrase="merge to main",
        )
        decision, ledger, _ = self.gate.evaluate_plan(event)
        
        self.assertEqual(decision.authority_verdict, AuthorityVerdict.FAIL)
        self.assertNotEqual(decision.decision, Decision.SAFE_EXECUTE)
        self.assertNotEqual(ledger.terminal_posture, "safe_execute")
    
    def test_authority_fail_no_token_never_safe_execute(self) -> None:
        """Invariant: authority_fail (no token) never produces safe_execute."""
        event = make_event(
            action_type="commit_prod_change",
            user_context={"user_id": "u1", "role": "admin"},
            boundary_phrase="production",
        )
        decision, ledger, _ = self.gate.evaluate_plan(event)
        
        self.assertEqual(decision.authority_verdict, AuthorityVerdict.FAIL)
        self.assertNotEqual(decision.decision, Decision.SAFE_EXECUTE)
    
    def test_authority_fail_missing_role_never_safe_execute(self) -> None:
        """Invariant: authority_fail (no role) never produces safe_execute."""
        event = make_event(
            action_type="safe_commit",
            user_context={"user_id": "u1"},
        )
        decision, _, _ = self.gate.evaluate_plan(event)
        
        self.assertEqual(decision.authority_verdict, AuthorityVerdict.FAIL)
        self.assertNotEqual(decision.decision, Decision.SAFE_EXECUTE)
    
    def test_boundary_present_never_defer(self) -> None:
        """Invariant: boundary_present never produces defer."""
        event = make_event(
            action_type="commit_prod_change",
            user_context={
                "user_id": "u1",
                "role": "admin",
                "approval_token": "tok-123",
            },
            boundary_phrase="production config change",
        )
        decision, ledger, _ = self.gate.evaluate_plan(event)
        
        self.assertIn(decision.boundary_verdict, [BoundaryVerdict.PRESENT, BoundaryVerdict.DETECTED])
        self.assertNotEqual(ledger.terminal_posture, "defer")
        self.assertEqual(ledger.terminal_posture, "bounded_allow")
    
    def test_boundary_detected_never_defer(self) -> None:
        """Invariant: boundary_detected never produces defer."""
        event = make_event(
            action_type="safe_commit",
            user_context={"user_id": "u1", "role": "admin"},
            boundary_phrase="merge changes to production",
        )
        decision, ledger, _ = self.gate.evaluate_plan(event)
        
        self.assertEqual(decision.boundary_verdict, BoundaryVerdict.DETECTED)
        self.assertNotEqual(ledger.terminal_posture, "defer")
    
    def test_shadow_mode_never_crossed(self) -> None:
        """Invariant: shadow mode never emits boundary_verdict=crossed."""
        event = make_event(
            action_type="deploy_production",
            user_context={
                "user_id": "u1",
                "role": "admin",
                "approval_token": "tok-123",
                "approval_chain": ["approver-1"],
            },
            boundary_phrase="deploy to production",
            mode="shadow",
        )
        decision, ledger, _ = self.gate.evaluate_plan(event)
        
        self.assertNotEqual(decision.boundary_verdict, BoundaryVerdict.CROSSED)
        self.assertNotEqual(ledger.boundary_verdict, "crossed")
        self.assertFalse(ledger.boundary_crossed)


class TestExpectedScenarios(unittest.TestCase):
    """Test the three expected demo scenarios."""
    
    def setUp(self) -> None:
        self.gate = PlanGate(mode="shadow")
    
    def test_merge_without_approval_ref_refuse(self) -> None:
        """merge_without_approval → REF → refuse"""
        event = make_event(
            action_type="merge_without_approval",
            user_context={"user_id": "u1", "role": "developer"},
            boundary_phrase="merge to production branch",
        )
        decision, ledger, _ = self.gate.evaluate_plan(event)
        
        self.assertEqual(decision.phase, Phase.REF)
        self.assertEqual(decision.decision, Decision.REFUSAL)
        self.assertEqual(ledger.terminal_posture, "refuse")
    
    def test_commit_prod_change_conf_bounded_allow(self) -> None:
        """commit_prod_change → CONF → bounded_allow"""
        event = make_event(
            action_type="commit_prod_change",
            user_context={
                "user_id": "u1",
                "role": "admin",
                "approval_token": "tok-123",
                "approval_chain": ["approver-1"],
            },
            boundary_phrase="commit changes to production config",
        )
        decision, ledger, _ = self.gate.evaluate_plan(event)
        
        self.assertEqual(decision.phase, Phase.CONF)
        self.assertEqual(decision.decision, Decision.BOUNDED_ALLOW)
        self.assertEqual(ledger.terminal_posture, "bounded_allow")
    
    def test_safe_commit_des_safe_execute(self) -> None:
        """safe_commit → DES → safe_execute"""
        event = make_event(
            action_type="safe_commit",
            user_context={"user_id": "u1", "role": "developer"},
            boundary_phrase="",
        )
        decision, ledger, _ = self.gate.evaluate_plan(event)
        
        self.assertEqual(decision.phase, Phase.DES)
        self.assertEqual(decision.decision, Decision.SAFE_EXECUTE)
        self.assertEqual(ledger.terminal_posture, "safe_execute")


class TestLedgerEmitter(unittest.TestCase):
    """Unit tests for LedgerEmitter."""
    
    def test_ledger_fields_populated(self) -> None:
        """Test that all required ledger fields are populated."""
        gate = PlanGate(mode="shadow")
        event = make_event(request_id="req-123", session_id="sess-456")
        decision, ledger, _ = gate.evaluate_plan(event)
        
        self.assertTrue(ledger.event_id.startswith("evt-"))
        self.assertEqual(ledger.request_id, "req-123")
        self.assertEqual(ledger.session_id, "sess-456")
        self.assertEqual(ledger.mode, "shadow")
        self.assertTrue(len(ledger.plan_hash) == 64)
        self.assertIn(ledger.phase_emitted, ["REF", "CONF", "DES"])
        self.assertIn(ledger.terminal_posture, ["refuse", "bounded_allow", "safe_execute"])
        self.assertIn(ledger.authority_verdict, ["pass", "fail"])
        self.assertIn(ledger.boundary_verdict, ["none", "present", "detected", "crossed"])
    
    def test_ledger_to_dict(self) -> None:
        """Test ledger to_dict produces valid schema."""
        gate = PlanGate(mode="shadow")
        event = make_event()
        _, ledger, _ = gate.evaluate_plan(event)
        
        d = ledger.to_dict()
        
        self.assertEqual(d["schema_version"], "ledger_row.v0.1")
        self.assertIn("event", d)
        self.assertIn("plan_link", d)
        self.assertIn("verdicts", d)
        self.assertIn("boundary", d)
        self.assertIn("reason_codes", d)


class TestDeterministicHashing(unittest.TestCase):
    """Test that hashing is deterministic."""
    
    def test_same_event_same_hashes(self) -> None:
        """Same event should produce same plan_hash."""
        gate = PlanGate(mode="shadow")
        event = make_event(
            action_type="safe_commit",
            user_context={"user_id": "u1", "role": "admin"},
            boundary_phrase="",
            request_id="req-deterministic",
        )
        
        decision1, _, _ = gate.evaluate_plan(event)
        decision2, _, _ = gate.evaluate_plan(event)
        
        self.assertEqual(decision1.plan_hash, decision2.plan_hash)
        self.assertEqual(decision1.boundary_phrase_hash, decision2.boundary_phrase_hash)
    
    def test_different_events_different_hashes(self) -> None:
        """Different events should produce different plan_hash."""
        gate = PlanGate(mode="shadow")
        
        event1 = make_event(request_id="req-001")
        event2 = make_event(request_id="req-002")
        
        decision1, _, _ = gate.evaluate_plan(event1)
        decision2, _, _ = gate.evaluate_plan(event2)
        
        self.assertNotEqual(decision1.plan_hash, decision2.plan_hash)


class TestReasonCodes(unittest.TestCase):
    """Test reason codes are properly populated."""
    
    def test_authority_fail_reason_code(self) -> None:
        gate = PlanGate(mode="shadow")
        event = make_event(
            action_type="merge_without_approval",
            user_context={"user_id": "u1", "role": "dev"},
        )
        decision, _, _ = gate.evaluate_plan(event)
        
        self.assertIn("AUTHORITY_FAIL", decision.reason_codes)
    
    def test_boundary_detected_reason_code(self) -> None:
        gate = PlanGate(mode="shadow")
        event = make_event(
            action_type="commit_prod_change",
            user_context={
                "user_id": "u1",
                "role": "admin",
                "approval_token": "tok-123",
            },
            boundary_phrase="production",
        )
        decision, _, _ = gate.evaluate_plan(event)
        
        self.assertIn("BOUNDARY_DETECTED", decision.reason_codes)
    
    def test_no_boundary_reason_code(self) -> None:
        gate = PlanGate(mode="shadow")
        event = make_event(
            action_type="safe_commit",
            user_context={"user_id": "u1", "role": "admin"},
            boundary_phrase="",
        )
        decision, _, _ = gate.evaluate_plan(event)
        
        self.assertIn("NO_BOUNDARY", decision.reason_codes)


if __name__ == "__main__":
    unittest.main()

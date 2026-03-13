"""
Deterministic Runtime Emulator — Plan-Gate Core (M3.E0).

Evaluates IDE-like events through Plan-Gate governance logic.
Produces governed decisions + ledger records.

Rules:
1. Runtime must own decision logic.
2. No LLM or agent autonomy.
3. Deterministic evaluation only.
4. REF, CONF decisions must follow constitutional invariants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from runtime.emulator.authority import AuthorityChecker, AuthorityVerdict
from runtime.emulator.boundary import BoundaryDetector, BoundaryVerdict
from runtime.emulator.ledger import LedgerEmitter, LedgerRow

from .canonicalize import boundary_phrase_hash, plan_hash


class Phase(str, Enum):
    """Constitutional phases. REF > CONF > DES dominance hierarchy."""
    REF = "REF"
    CONF = "CONF"
    DES = "DES"


class Decision(str, Enum):
    """Terminal decisions produced by the runtime."""
    REFUSAL = "REFUSAL"
    BOUNDED_ALLOW = "BOUNDED_ALLOW"
    SAFE_EXECUTE = "SAFE_EXECUTE"


@dataclass
class PlanDecision:
    """
    Decision output from PlanGate.evaluate_plan().
    
    Fields:
        decision: Terminal decision (REFUSAL, BOUNDED_ALLOW, SAFE_EXECUTE)
        phase: Constitutional phase (REF, CONF, DES)
        authority_verdict: Result of authority check
        boundary_verdict: Result of boundary detection
        plan_hash: SHA-256 hash of the plan
        boundary_phrase_hash: SHA-256 hash of the boundary phrase
    """
    decision: Decision
    phase: Phase
    authority_verdict: AuthorityVerdict
    boundary_verdict: BoundaryVerdict
    plan_hash: str
    boundary_phrase_hash: str
    reason_codes: list[str] = field(default_factory=list)


class PlanGate:
    """
    Deterministic Plan-Gate runtime emulator.
    
    Evaluates IDE events through governance logic:
    1. Authority check (who can do this?)
    2. Boundary detection (what is at risk?)
    3. Phase routing (REF, CONF, DES)
    4. Decision emission (REFUSAL, BOUNDED_ALLOW, SAFE_EXECUTE)
    5. Ledger record emission
    
    Constitutional invariants:
    - authority_fail → never produces safe_execute
    - boundary_present → never produces defer
    - shadow_mode → never emits boundary_verdict=crossed
    """
    
    def __init__(self, mode: str = "shadow"):
        """
        Initialize PlanGate.
        
        Args:
            mode: Execution mode ("shadow" or "live")
        """
        self.mode = mode
        self.authority_checker = AuthorityChecker()
        self.boundary_detector = BoundaryDetector()
        self.ledger_emitter = LedgerEmitter()
    
    def evaluate_plan(self, event: dict[str, Any]) -> tuple[PlanDecision, LedgerRow, dict[str, Any]]:
        """
        Evaluate an IDE event and produce a governed decision.
        
        Args:
            event: IDE event dict with action_type, user context, etc.
        
        Returns:
            Tuple of (PlanDecision, LedgerRow, plan_dict) for shadow artifact plumbing.
        
        Invariants enforced:
        - REF phase always produces REFUSAL
        - CONF phase produces BOUNDED_ALLOW (never defer on boundary)
        - DES stub produces SAFE_EXECUTE only if authority passes
        - Shadow mode never emits boundary_verdict=crossed
        """
        action_type = event.get("action_type", "unknown")
        user_context = event.get("user_context", {})
        boundary_phrase = event.get("boundary_phrase", "")
        
        authority_verdict = self.authority_checker.check(
            user_context=user_context,
            action_type=action_type,
        )
        
        boundary_verdict = self.boundary_detector.detect(
            action_type=action_type,
            boundary_phrase=boundary_phrase,
            mode=self.mode,
        )
        
        phase, decision, reason_codes = self._route_decision(
            authority_verdict=authority_verdict,
            boundary_verdict=boundary_verdict,
            action_type=action_type,
        )
        
        plan = self._build_plan(event, phase, authority_verdict, boundary_verdict)
        p_hash = plan_hash(plan)
        bp_hash = boundary_phrase_hash(boundary_phrase) if boundary_phrase else ""
        
        plan_decision = PlanDecision(
            decision=decision,
            phase=phase,
            authority_verdict=authority_verdict,
            boundary_verdict=boundary_verdict,
            plan_hash=p_hash,
            boundary_phrase_hash=bp_hash,
            reason_codes=reason_codes,
        )
        
        ledger_row = self.ledger_emitter.emit(
            event=event,
            decision=plan_decision,
            plan=plan,
        )
        
        return plan_decision, ledger_row, plan
    
    def _route_decision(
        self,
        authority_verdict: AuthorityVerdict,
        boundary_verdict: BoundaryVerdict,
        action_type: str,
    ) -> tuple[Phase, Decision, list[str]]:
        """
        Route to phase and decision based on verdicts.
        
        Constitutional routing rules:
        1. Authority fail + boundary present → REF → REFUSAL
        2. Authority pass + boundary present → CONF → BOUNDED_ALLOW
        3. Authority pass + no boundary → DES → SAFE_EXECUTE
        4. Authority fail + no boundary → still REF → REFUSAL (fail-closed)
        
        Invariants:
        - authority_fail NEVER produces safe_execute
        - boundary_present NEVER produces defer (we use bounded_allow)
        """
        reason_codes: list[str] = []
        
        if authority_verdict == AuthorityVerdict.FAIL:
            reason_codes.append("AUTHORITY_FAIL")
            if boundary_verdict in (BoundaryVerdict.PRESENT, BoundaryVerdict.DETECTED):
                reason_codes.append("BOUNDARY_DETECTED")
            return Phase.REF, Decision.REFUSAL, reason_codes
        
        if boundary_verdict in (BoundaryVerdict.PRESENT, BoundaryVerdict.DETECTED):
            reason_codes.append("BOUNDARY_DETECTED")
            reason_codes.append("AUTHORITY_PASS")
            return Phase.CONF, Decision.BOUNDED_ALLOW, reason_codes
        
        reason_codes.append("AUTHORITY_PASS")
        reason_codes.append("NO_BOUNDARY")
        return Phase.DES, Decision.SAFE_EXECUTE, reason_codes
    
    def _build_plan(
        self,
        event: dict[str, Any],
        phase: Phase,
        authority_verdict: AuthorityVerdict,
        boundary_verdict: BoundaryVerdict,
    ) -> dict[str, Any]:
        """Build the plan object for hashing and ledger linkage."""
        return {
            "schema_version": "plan.v0.1",
            "event": event,
            "constitutional_phase": phase.value,
            "authority": {
                "verdict": authority_verdict.value,
            },
            "boundary": {
                "verdict": boundary_verdict.value,
                "phrase": event.get("boundary_phrase", ""),
            },
            "mode": self.mode,
        }

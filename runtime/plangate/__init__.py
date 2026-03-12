"""
Plan-Gate — M3.3 mandatory pre-sandbox decision gate.

All execution paths must flow through Plan-Gate before sandbox.
Postures: refuse, defer, bounded_allow, safe_execute.
Only safe_execute may reach sandbox.
"""

from runtime.plangate.plangate_decision import PlanGateDecision, Posture
from runtime.plangate.plangate_service import PlanGateService

__all__ = ["PlanGateDecision", "PlanGateService", "Posture"]

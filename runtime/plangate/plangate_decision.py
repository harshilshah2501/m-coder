"""
Plan-Gate Decision — M3.3 runtime posture for execution gating.

Deterministic decision model: refuse, defer, bounded_allow, safe_execute.
Only safe_execute may reach sandbox execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Posture = Literal["refuse", "defer", "bounded_allow", "safe_execute"]


@dataclass
class PlanGateDecision:
    """
    Result of Plan-Gate evaluation. Determines whether a request may proceed to sandbox.

    Attributes:
        posture: Runtime posture (refuse | defer | bounded_allow | safe_execute).
        authority_ok: Whether authority check passed.
        boundary_detected: Whether an irreversible boundary was detected.
        irreversible: Whether the requested action is considered irreversible.
        reason: Human-readable reason for the decision.
    """

    posture: Posture
    authority_ok: bool
    boundary_detected: bool
    irreversible: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "posture": self.posture,
            "authority_ok": self.authority_ok,
            "boundary_detected": self.boundary_detected,
            "irreversible": self.irreversible,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PlanGateDecision:
        return cls(
            posture=d["posture"],
            authority_ok=d.get("authority_ok", False),
            boundary_detected=d.get("boundary_detected", False),
            irreversible=d.get("irreversible", False),
            reason=d.get("reason", ""),
        )

    @property
    def may_execute(self) -> bool:
        """Only safe_execute may reach sandbox."""
        return self.posture == "safe_execute"

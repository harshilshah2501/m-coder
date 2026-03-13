"""
Plan-Gate internal contracts — M3.3B decomposition.

First-class result models for AuthorityValidator, IrreversibilityDetector, and JudgeGate.
These contracts enable explicit, machine-readable outputs from each Plan-Gate subcomponent.

External contract (PlanGateService.evaluate() -> PlanGateDecision) remains unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuthorityResult:
    """
    Result from AuthorityValidator.

    Determines whether the requester has sufficient authority for the requested action.
    This is an explicit, machine-readable output — not a hidden boolean.

    Attributes:
        authority_ok: Whether authority check passed (True = authorized).
        authority_reason: Human-readable reason for the authority decision.
        authority_source: Source of authority decision (e.g., "request_hint", "default", "rule").
    """

    authority_ok: bool
    authority_reason: str
    authority_source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_ok": self.authority_ok,
            "authority_reason": self.authority_reason,
            "authority_source": self.authority_source,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AuthorityResult:
        return cls(
            authority_ok=d.get("authority_ok", True),
            authority_reason=d.get("authority_reason", ""),
            authority_source=d.get("authority_source"),
        )


@dataclass(frozen=True)
class IrreversibilityResult:
    """
    Result from IrreversibilityDetector.

    Classifies whether the request involves a boundary or irreversible action.
    This is an explicit, machine-readable output — not a hidden boolean.

    Attributes:
        boundary_detected: Whether a governance boundary was detected.
        irreversible: Whether the action is classified as irreversible.
        boundary_reason: Human-readable reason for the boundary/irreversibility decision.
        boundary_class: Classification of the boundary (e.g., "dangerous_command", "request_hint").
    """

    boundary_detected: bool
    irreversible: bool
    boundary_reason: str
    boundary_class: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_detected": self.boundary_detected,
            "irreversible": self.irreversible,
            "boundary_reason": self.boundary_reason,
            "boundary_class": self.boundary_class,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> IrreversibilityResult:
        return cls(
            boundary_detected=d.get("boundary_detected", False),
            irreversible=d.get("irreversible", False),
            boundary_reason=d.get("boundary_reason", ""),
            boundary_class=d.get("boundary_class"),
        )


@dataclass(frozen=True)
class JudgeInput:
    """
    Input to JudgeGate.

    Combines the original request with authority and irreversibility results
    for the final posture decision.

    Attributes:
        request: Original request dict (includes command, hints, etc.).
        authority_result: Result from AuthorityValidator.
        irreversibility_result: Result from IrreversibilityDetector.
    """

    request: dict[str, Any]
    authority_result: AuthorityResult
    irreversibility_result: IrreversibilityResult

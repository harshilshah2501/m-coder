"""
Authority Drift / Freshness Utility.

Determines authority state based on confidence and staleness.

Phase 1: Simple deterministic logic only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class AuthorityState(Enum):
    """Authority validation state."""

    VALIDATED = "validated"
    STALE_CANDIDATE = "stale_candidate"
    STALE = "stale"
    UNVERIFIED = "unverified"


@dataclass(frozen=True)
class FreshnessResult:
    """Result of freshness check."""

    state: AuthorityState
    is_stale: bool
    days_since_verification: int
    threshold_days: int
    confidence: str


def is_stale(
    last_verified_at: datetime,
    threshold_days: int = 90,
    *,
    reference_time: Optional[datetime] = None,
) -> bool:
    """
    Check if authority verification is stale.

    Args:
        last_verified_at: Timestamp of last verification.
        threshold_days: Days after which authority is considered stale.
        reference_time: Optional reference time (default: now).

    Returns:
        True if stale, False otherwise.
    """
    if reference_time is None:
        reference_time = datetime.now()

    age = reference_time - last_verified_at
    return age > timedelta(days=threshold_days)


def days_since_verification(
    last_verified_at: datetime,
    *,
    reference_time: Optional[datetime] = None,
) -> int:
    """
    Calculate days since last verification.

    Args:
        last_verified_at: Timestamp of last verification.
        reference_time: Optional reference time (default: now).

    Returns:
        Number of days since verification.
    """
    if reference_time is None:
        reference_time = datetime.now()

    age = reference_time - last_verified_at
    return max(0, age.days)


def compute_authority_state(
    confidence: str,
    stale: bool,
    *,
    structural_validation_passed: Optional[bool] = None,
) -> AuthorityState:
    """
    Compute authority state based on confidence and staleness.

    Decision matrix:
    - confidence=high, not stale, structural=pass → VALIDATED
    - confidence=high, not stale, structural=None → VALIDATED (assume pass)
    - confidence=high, stale, structural=pass → STALE_CANDIDATE
    - confidence=high, stale, structural=fail/None → UNVERIFIED
    - confidence=medium, not stale → STALE_CANDIDATE
    - confidence=medium, stale → UNVERIFIED
    - confidence=low → STALE
    - Any case where structural fails hard → STALE

    Args:
        confidence: Authority confidence level (high/medium/low).
        stale: Whether verification is beyond staleness threshold.
        structural_validation_passed: Result of structural validation (None if not run).

    Returns:
        AuthorityState enum value.
    """
    if structural_validation_passed is False:
        return AuthorityState.STALE

    confidence_lower = confidence.lower() if confidence else "low"

    if confidence_lower == "low":
        return AuthorityState.STALE

    if confidence_lower == "high":
        if not stale:
            return AuthorityState.VALIDATED
        else:
            if structural_validation_passed is True:
                return AuthorityState.STALE_CANDIDATE
            else:
                return AuthorityState.UNVERIFIED

    if confidence_lower == "medium":
        if not stale:
            return AuthorityState.STALE_CANDIDATE
        else:
            return AuthorityState.UNVERIFIED

    return AuthorityState.UNVERIFIED


def compute_freshness_result(
    confidence: str,
    last_verified_at: datetime,
    threshold_days: int = 90,
    *,
    structural_validation_passed: Optional[bool] = None,
    reference_time: Optional[datetime] = None,
) -> FreshnessResult:
    """
    Compute complete freshness result.

    Args:
        confidence: Authority confidence level.
        last_verified_at: Timestamp of last verification.
        threshold_days: Staleness threshold in days.
        structural_validation_passed: Result of structural validation.
        reference_time: Optional reference time (default: now).

    Returns:
        FreshnessResult with state and metrics.
    """
    stale = is_stale(last_verified_at, threshold_days, reference_time=reference_time)
    days = days_since_verification(last_verified_at, reference_time=reference_time)
    state = compute_authority_state(
        confidence, stale, structural_validation_passed=structural_validation_passed
    )

    return FreshnessResult(
        state=state,
        is_stale=stale,
        days_since_verification=days,
        threshold_days=threshold_days,
        confidence=confidence,
    )

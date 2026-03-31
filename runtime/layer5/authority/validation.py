"""
Pre-Boost Structural Validation Utility.

Validates authority records against code index before boost is applied.
Returns validation status and check details.

Phase 1: Validation only, no ranking decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from runtime.layer5.authority.code_index_adapter import CodeIndexProtocol
from runtime.layer5.authority.freshness import (
    AuthorityState,
    compute_authority_state,
    days_since_verification,
    is_stale,
)
from runtime.layer5.authority.registry_loader import Concept, PrimaryOwner, Verification


@dataclass(frozen=True)
class ValidationChecks:
    """Individual validation check results."""

    file_exists: bool
    class_exists: bool
    method_exists: Optional[bool]  # None if method not specified
    is_referenced: Optional[bool]  # None if not available
    freshness_ok: bool
    days_since_verification: int


@dataclass(frozen=True)
class ValidationResult:
    """Complete validation result."""

    status: AuthorityState
    checks: ValidationChecks
    all_critical_passed: bool
    requires_verification: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status.value,
            "checks": {
                "file_exists": self.checks.file_exists,
                "class_exists": self.checks.class_exists,
                "method_exists": self.checks.method_exists,
                "is_referenced": self.checks.is_referenced,
                "freshness_ok": self.checks.freshness_ok,
                "days_since_verification": self.checks.days_since_verification,
            },
            "all_critical_passed": self.all_critical_passed,
            "requires_verification": self.requires_verification,
        }


def validate_authority(
    primary_owner: PrimaryOwner,
    verification: Verification,
    code_index: CodeIndexProtocol,
    *,
    reference_time: Optional[datetime] = None,
) -> ValidationResult:
    """
    Validate authority record against code index.

    Checks:
    1. file_exists (CRITICAL)
    2. class_exists (CRITICAL)
    3. method_exists (optional, downgrades if fails)
    4. is_referenced (optional, downgrades if fails)
    5. freshness_ok (requires structural validation if fails)

    Args:
        primary_owner: Authority owner record.
        verification: Drift control metadata.
        code_index: Code index adapter for checks.
        reference_time: Optional reference time for freshness (default: now).

    Returns:
        ValidationResult with status and check details.
    """
    file_exists = code_index.file_exists(primary_owner.file)

    class_exists = False
    if file_exists:
        class_exists = code_index.class_exists(
            primary_owner.file, primary_owner.class_name
        )

    method_exists: Optional[bool] = None
    if primary_owner.method and file_exists and class_exists:
        method_exists = code_index.method_exists(
            primary_owner.file, primary_owner.class_name, primary_owner.method
        )

    is_ref = code_index.is_referenced(primary_owner.file) if file_exists else None

    stale = is_stale(
        verification.last_verified_at,
        verification.staleness_threshold_days,
        reference_time=reference_time,
    )
    freshness_ok = not stale

    days = days_since_verification(
        verification.last_verified_at, reference_time=reference_time
    )

    checks = ValidationChecks(
        file_exists=file_exists,
        class_exists=class_exists,
        method_exists=method_exists,
        is_referenced=is_ref,
        freshness_ok=freshness_ok,
        days_since_verification=days,
    )

    all_critical_passed = file_exists and class_exists

    if not file_exists or not class_exists:
        status = AuthorityState.STALE
        structural_passed = False
    elif method_exists is False or is_ref is False:
        status = compute_authority_state(
            primary_owner.confidence,
            stale,
            structural_validation_passed=None,
        )
        if status == AuthorityState.VALIDATED:
            status = AuthorityState.STALE_CANDIDATE
        structural_passed = None
    else:
        structural_passed = True
        status = compute_authority_state(
            primary_owner.confidence,
            stale,
            structural_validation_passed=structural_passed,
        )

    requires_verification = status in (
        AuthorityState.STALE,
        AuthorityState.STALE_CANDIDATE,
        AuthorityState.UNVERIFIED,
    )

    return ValidationResult(
        status=status,
        checks=checks,
        all_critical_passed=all_critical_passed,
        requires_verification=requires_verification,
    )


def validate_concept(
    concept: Concept,
    code_index: CodeIndexProtocol,
    *,
    reference_time: Optional[datetime] = None,
) -> ValidationResult:
    """
    Validate a concept's primary owner.

    Convenience wrapper around validate_authority.

    Args:
        concept: Concept to validate.
        code_index: Code index adapter.
        reference_time: Optional reference time.

    Returns:
        ValidationResult for the concept's primary owner.
    """
    return validate_authority(
        concept.primary_owner,
        concept.verification,
        code_index,
        reference_time=reference_time,
    )

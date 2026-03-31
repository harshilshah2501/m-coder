"""
Product Authority Layer — Foundation Module.

Provides:
- Authority registry loading and validation
- Drift/freshness classification
- Pre-boost structural validation

Phase 1: Data + validation only. No ranking integration.
"""

from runtime.layer5.authority.registry_loader import (
    AuthorityRegistry,
    load_registry,
    AuthorityRegistryError,
)
from runtime.layer5.authority.freshness import (
    is_stale,
    compute_authority_state,
    AuthorityState,
)
from runtime.layer5.authority.validation import (
    validate_authority,
    ValidationResult,
)

__all__ = [
    "AuthorityRegistry",
    "load_registry",
    "AuthorityRegistryError",
    "is_stale",
    "compute_authority_state",
    "AuthorityState",
    "validate_authority",
    "ValidationResult",
]

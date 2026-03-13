"""
Runtime integrity — M4.1 Canonical execution artifact and normalization.

Provides CanonicalExecutionIntent as the single semantic source of truth for
execution identity, and CommandNormalizer to build it from request once.
No downstream re-parsing of command text after normalization.
"""

from runtime.integrity.canonical_intent import (
    CanonicalExecutionIntent,
    compute_canonical_hash,
    serialize_for_hash,
)
from runtime.integrity.command_normalizer import (
    CommandNormalizer,
    NormalizationError,
)

__all__ = [
    "CanonicalExecutionIntent",
    "CommandNormalizer",
    "NormalizationError",
    "compute_canonical_hash",
    "serialize_for_hash",
]

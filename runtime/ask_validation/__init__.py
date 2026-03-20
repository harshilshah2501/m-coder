"""
Layer-5 Grounded Ask Validation Harness.

Provides measurable gates for grounded Ask progress:
- Empty bundle rate
- Relevant file presence rate  
- Retrieval latency
- End-to-end ask latency
- No-match justification validation

This harness prevents subjective "it seems better" claims by enforcing
concrete, repeatable metric thresholds.
"""

from runtime.ask_validation.harness import (
    AskValidationHarness,
    HarnessResult,
    ValidationMetrics,
)
from runtime.ask_validation.golden_queries import (
    GoldenQuery,
    GOLDEN_QUERY_SUITE,
)

__all__ = [
    "AskValidationHarness",
    "HarnessResult",
    "ValidationMetrics",
    "GoldenQuery",
    "GOLDEN_QUERY_SUITE",
]

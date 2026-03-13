"""
Shadow Mode Validation (M3.6).

Log-only enforcement: full governed pipeline without crossing irreversible boundaries.
Emits plan, decision, ledger, shadow run record, and ingestion batch.
"""

from runtime.shadow.runner import ShadowRunner, ShadowRunResult
from runtime.shadow.harness import ShadowValidationHarness
from runtime.shadow.baseline_scenarios import BASELINE_SCENARIOS, ScenarioDef

__all__ = [
    "ShadowRunner",
    "ShadowRunResult",
    "ShadowValidationHarness",
    "BASELINE_SCENARIOS",
    "ScenarioDef",
]

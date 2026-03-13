"""
Observation module — M4.6 runtime performance metrics.

Provides deterministic operational visibility into runtime health and invariance behavior.
Read-only over ledger evidence. No external telemetry pipelines.
"""

from runtime.observation.metrics_models import (
    BackendDistribution,
    CanonicalHashReuse,
    CollapseSummary,
    LatencySummary,
    PostureCounts,
    RuntimeMetricsReport,
)
from runtime.observation.runtime_metrics import RuntimeMetricsService

__all__ = [
    "RuntimeMetricsService",
    "RuntimeMetricsReport",
    "PostureCounts",
    "BackendDistribution",
    "CanonicalHashReuse",
    "LatencySummary",
    "CollapseSummary",
]

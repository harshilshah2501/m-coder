"""
Runtime Observation — M4.3 Collapse Vector Tracking.

Provides deterministic detection and classification of governance/runtime
collapse vectors from runtime evidence. Operates on existing evidence
artifacts (ledger rows, trace summaries, baseline comparisons).

Collapse classes:
- identity_propagation_missing
- decision_execution_mismatch
- replay_mismatch
- missing_trace_linkage
- unexpected_refusal_distribution_drift
- missing_evidence_join
"""

from runtime.observation.collapse_models import (
    CollapseClass,
    CollapseEvent,
    CollapseEvidence,
    CollapseSeverity,
    CollapseSummary,
)
from runtime.observation.collapse_vectors import (
    CollapseClassifier,
    ClassificationResult,
)
from runtime.observation.collapse_queries import (
    CollapseQueryService,
    CollapseFilter,
)

__all__ = [
    "CollapseClass",
    "CollapseEvent",
    "CollapseEvidence",
    "CollapseSeverity",
    "CollapseSummary",
    "CollapseClassifier",
    "ClassificationResult",
    "CollapseQueryService",
    "CollapseFilter",
]

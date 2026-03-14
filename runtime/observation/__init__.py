"""
Runtime Observation — M4.1 Observability Closure + M4.2 Drift Baseline + M4.3 Collapse Tracking + M4.4 Ledger Reconciliation.

This package provides:

M4.1 Observability Closure:
- TraceBuilder: Build execution traces by request_id or canonical_hash
- RuntimeSummaryQueries: Aggregate statistics for observability dashboards
- ExplanationBuilder: Human-readable explanation payloads for plugin
- Models: TraceEvent, ExecutionTrace, PostureDistribution, RefusalSummary,
          BackendDistribution, RuntimeSummary, ExplanationPayload

M4.2 Drift Baseline:
- BaselineBuilder: Build deterministic baselines from ledger evidence
- BaselineStore: Persistence for baseline artifacts
- Models: BaselineDimension, DimensionDistribution, BaselineSnapshot, BaselineMetadata

M4.3 Collapse Vector Tracking:
- CollapseClassifier: Deterministic detection of collapse vectors
- CollapseQueryService: Query and filter collapse events
- Models: CollapseClass, CollapseEvent, CollapseEvidence, CollapseSeverity, CollapseSummary
- ClassificationResult, CollapseFilter

M4.4 Ledger Reconciliation:
- LedgerReconciliationService: Reconcile plan, decision, execution evidence
- ReconciliationConfig: Configuration for reconciliation behavior
- MismatchClassification, MismatchSeverity: Mismatch types and severity
- ReconciliationMismatch, ReconciliationResult, ReconciliationStatus: Results
- RowLinkage: Ledger row linkage evidence

Rules:
- Deterministic only (no LLMs, no randomness)
- Read-only over ledger evidence
- No mutation of runtime behavior
"""

# =============================================================================
# M4.1 Observability Closure exports
# =============================================================================

from runtime.observation.models import (
    TraceEvent,
    ExecutionTrace,
    PostureDistribution,
    RefusalSummary,
    BackendDistribution,
    RuntimeSummary,
    ExplanationPayload,
)
from runtime.observation.trace_builder import TraceBuilder
from runtime.observation.summary_queries import RuntimeSummaryQueries
from runtime.observation.explanation_builder import ExplanationBuilder

# =============================================================================
# M4.2 Drift Baseline exports
# =============================================================================

from runtime.observation.baseline_models import (
    BaselineDimension,
    DimensionDistribution,
    BaselineSnapshot,
    BaselineMetadata,
)
from runtime.observation.drift_baseline import (
    BaselineBuilder,
    BaselineBuildError,
)
from runtime.observation.baseline_store import (
    BaselineStore,
    BaselineStoreError,
)

# =============================================================================
# M4.3 Collapse Vector Tracking exports
# =============================================================================

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

# =============================================================================
# M4.4 Ledger Reconciliation exports
# =============================================================================

from runtime.observation.reconciliation_models import (
    MismatchClassification,
    MismatchSeverity,
    ReconciliationMismatch,
    ReconciliationResult,
    ReconciliationStatus,
    RowLinkage,
)
from runtime.observation.reconciliation import (
    LedgerReconciliationService,
    ReconciliationConfig,
)

__all__ = [
    # M4.1 Models
    "TraceEvent",
    "ExecutionTrace",
    "PostureDistribution",
    "RefusalSummary",
    "BackendDistribution",
    "RuntimeSummary",
    "ExplanationPayload",
    # M4.1 TraceBuilder
    "TraceBuilder",
    # M4.1 Summary queries
    "RuntimeSummaryQueries",
    # M4.1 Explanation
    "ExplanationBuilder",
    # M4.2 Baseline models
    "BaselineDimension",
    "DimensionDistribution",
    "BaselineSnapshot",
    "BaselineMetadata",
    # M4.2 BaselineBuilder
    "BaselineBuilder",
    "BaselineBuildError",
    # M4.2 BaselineStore
    "BaselineStore",
    "BaselineStoreError",
    # M4.3 Collapse models
    "CollapseClass",
    "CollapseEvent",
    "CollapseEvidence",
    "CollapseSeverity",
    "CollapseSummary",
    # M4.3 CollapseClassifier
    "CollapseClassifier",
    "ClassificationResult",
    # M4.3 CollapseQueryService
    "CollapseQueryService",
    "CollapseFilter",
    # M4.4 Reconciliation service
    "LedgerReconciliationService",
    "ReconciliationConfig",
    # M4.4 Mismatch types
    "MismatchClassification",
    "MismatchSeverity",
    # M4.4 Results
    "ReconciliationMismatch",
    "ReconciliationResult",
    "ReconciliationStatus",
    # M4.4 Linkage evidence
    "RowLinkage",
]

"""
Runtime Observation — M4.1 Observability Closure + M4.2 Drift Baseline + M4.3 Collapse Tracking + M4.4 Ledger Reconciliation + M4.5 GREG Escalation + M4.6 Runtime Metrics.

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

M4.5 GREG Governance Escalation:
- EscalationPolicy: Threshold-based escalation decision logic
- EscalationThresholds: Configurable thresholds for escalation triggers
- EscalationDecision: Result of escalation evaluation
- EscalationType, EscalationSeverity: Escalation classification
- GREGBundle: Evidence bundle for governance escalation
- EscalationEvidence: Aggregated evidence structures
- BundleBuilder: Constructs bundles from observation data
- EscalationMismatchType: Mismatch types for escalation (distinct from M4.4)
- CollapseClassification: Collapse vector classification for escalation

M4.6 Runtime Performance Metrics:
- RuntimeMetricsService: Deterministic metrics query layer over ledger evidence
- RuntimeMetricsReport: Complete runtime performance metrics report
- PostureCounts, ExecutionCounts: Plan-Gate and sandbox outcome counts
- MetricsBackendDistribution: Backend execution distribution (distinct from M4.1)
- CanonicalHashReuse: Hash reuse metrics for replay validation
- LatencySummary, ReplayCounts: Latency and replay statistics
- MetricsCollapseSummary: Collapse metrics aggregation (distinct from M4.3)
- InvariantHealth: Runtime invariant health metrics

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

# =============================================================================
# M4.5 GREG Governance Escalation exports
# =============================================================================

from runtime.observation.greg_escalation import (
    EscalationPolicy,
    EscalationThresholds,
    EscalationDecision,
    EscalationType,
    EscalationSeverity,
)
from runtime.observation.greg_bundle import (
    GREGBundle,
    EscalationEvidence,
    EscalationMismatchType,
    CollapseClassification,
    MismatchEvidence,
    CollapseEvidence as GREGCollapseEvidence,
    DriftEvidence,
    IntegrityEvidence,
    LedgerReference,
    BundleSummary,
)
from runtime.observation.bundle_builder import BundleBuilder

# =============================================================================
# M4.6 Runtime Performance Metrics exports
# =============================================================================

from runtime.observation.metrics_models import (
    PostureCounts,
    ExecutionCounts,
    MetricsBackendDistribution,
    CanonicalHashReuse,
    LatencySummary,
    ReplayCounts,
    MetricsCollapseSummary,
    InvariantHealth,
    RuntimeMetricsReport,
)
from runtime.observation.runtime_metrics import RuntimeMetricsService

__all__ = [
    # =========================================================================
    # M4.1 Observability Closure
    # =========================================================================
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
    # =========================================================================
    # M4.2 Drift Baseline
    # =========================================================================
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
    # =========================================================================
    # M4.3 Collapse Vector Tracking
    # =========================================================================
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
    # =========================================================================
    # M4.4 Ledger Reconciliation
    # =========================================================================
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
    # =========================================================================
    # M4.5 GREG Governance Escalation
    # =========================================================================
    # M4.5 Escalation policy
    "EscalationPolicy",
    "EscalationThresholds",
    "EscalationDecision",
    "EscalationType",
    "EscalationSeverity",
    # M4.5 GREG bundle
    "GREGBundle",
    "EscalationEvidence",
    "EscalationMismatchType",
    "CollapseClassification",
    "MismatchEvidence",
    "GREGCollapseEvidence",
    "DriftEvidence",
    "IntegrityEvidence",
    "LedgerReference",
    "BundleSummary",
    # M4.5 Bundle builder
    "BundleBuilder",
    # =========================================================================
    # M4.6 Runtime Performance Metrics
    # =========================================================================
    # M4.6 Metrics models
    "PostureCounts",
    "ExecutionCounts",
    "MetricsBackendDistribution",
    "CanonicalHashReuse",
    "LatencySummary",
    "ReplayCounts",
    "MetricsCollapseSummary",
    "InvariantHealth",
    "RuntimeMetricsReport",
    # M4.6 Metrics service
    "RuntimeMetricsService",
]

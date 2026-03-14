"""
Runtime Observation — M4.1 Observability Closure + M4.4 Ledger Reconciliation.

This package provides:

M4.1 Observability Closure:
- TraceBuilder: Build execution traces by request_id or canonical_hash
- RuntimeSummaryQueries: Aggregate statistics for observability dashboards
- ExplanationBuilder: Human-readable explanation payloads for plugin
- Models: TraceEvent, ExecutionTrace, PostureDistribution, RefusalSummary,
          BackendDistribution, RuntimeSummary, ExplanationPayload

M4.4 Ledger Reconciliation:
- LedgerReconciliationService: Reconcile plan, decision, execution evidence
- ReconciliationConfig: Configuration for reconciliation behavior
- MismatchClassification, MismatchSeverity: Mismatch types and severity
- ReconciliationMismatch, ReconciliationResult, ReconciliationStatus: Results
- RowLinkage: Ledger row linkage evidence
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

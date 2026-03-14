"""
Observation module — Runtime observation and ledger reconciliation.

This module provides:
- M4.1: Execution tracing, posture distribution, and runtime summaries
- M4.4: Ledger reconciliation for verifying consistency between
        plan, decision, execution, and replay evidence

M4.1 Observability Closure exports (when available):
- TraceEvent, ExecutionTrace: Execution event tracing
- PostureDistribution, RefusalSummary, BackendDistribution: Posture analytics
- RuntimeSummary, RuntimeSummaryQueries: Runtime statistics
- ExplanationPayload, ExplanationBuilder: Explanation generation
- TraceBuilder: Trace construction utilities

M4.4 Ledger Reconciliation exports:
- LedgerReconciliationService, ReconciliationConfig: Reconciliation service
- MismatchClassification, MismatchSeverity: Mismatch types
- ReconciliationMismatch, ReconciliationResult, ReconciliationStatus: Results
- RowLinkage: Ledger row linkage evidence
"""

__all__: list[str] = []

# =============================================================================
# M4.1 Observability Closure exports (conditional import)
# =============================================================================
# These symbols will be available when M4.1 observability closure is integrated.
# Import conditionally to maintain backward and forward compatibility.

try:
    from runtime.observation.trace import TraceEvent, ExecutionTrace, TraceBuilder
    __all__.extend(["TraceEvent", "ExecutionTrace", "TraceBuilder"])
except ImportError:
    TraceEvent = None  # type: ignore[misc, assignment]
    ExecutionTrace = None  # type: ignore[misc, assignment]
    TraceBuilder = None  # type: ignore[misc, assignment]

try:
    from runtime.observation.posture import (
        PostureDistribution,
        RefusalSummary,
        BackendDistribution,
    )
    __all__.extend(["PostureDistribution", "RefusalSummary", "BackendDistribution"])
except ImportError:
    PostureDistribution = None  # type: ignore[misc, assignment]
    RefusalSummary = None  # type: ignore[misc, assignment]
    BackendDistribution = None  # type: ignore[misc, assignment]

try:
    from runtime.observation.summary import RuntimeSummary, RuntimeSummaryQueries
    __all__.extend(["RuntimeSummary", "RuntimeSummaryQueries"])
except ImportError:
    RuntimeSummary = None  # type: ignore[misc, assignment]
    RuntimeSummaryQueries = None  # type: ignore[misc, assignment]

try:
    from runtime.observation.explanation import ExplanationPayload, ExplanationBuilder
    __all__.extend(["ExplanationPayload", "ExplanationBuilder"])
except ImportError:
    ExplanationPayload = None  # type: ignore[misc, assignment]
    ExplanationBuilder = None  # type: ignore[misc, assignment]

# =============================================================================
# M4.4 Ledger Reconciliation exports (always available)
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

__all__.extend([
    # Reconciliation service
    "LedgerReconciliationService",
    "ReconciliationConfig",
    # Mismatch types
    "MismatchClassification",
    "MismatchSeverity",
    # Results
    "ReconciliationMismatch",
    "ReconciliationResult",
    "ReconciliationStatus",
    # Linkage evidence
    "RowLinkage",
])

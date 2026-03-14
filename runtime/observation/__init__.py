"""
M4.1 Observability Closure — Runtime evidence reconstruction and explanation.

This package provides:
- TraceBuilder: Build execution traces by request_id or canonical_hash
- RuntimeSummaryQueries: Aggregate statistics for observability dashboards
- RuntimeReportCLI: CLI for generating runtime reports
- ExplanationBuilder: Human-readable explanation payloads for plugin
"""

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

__all__ = [
    # Models
    "TraceEvent",
    "ExecutionTrace",
    "PostureDistribution",
    "RefusalSummary",
    "BackendDistribution",
    "RuntimeSummary",
    "ExplanationPayload",
    # TraceBuilder
    "TraceBuilder",
    # Summary queries
    "RuntimeSummaryQueries",
    # Explanation
    "ExplanationBuilder",
]

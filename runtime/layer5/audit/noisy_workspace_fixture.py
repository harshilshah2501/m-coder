"""
Deterministic noisy AIOps-style workspace for PR-6 evaluation.

Uses a ``motadata/`` module prefix so relative paths match real-checkout layouts.

PR-6 closure fixture generator — DO NOT MODIFY without version bump and
PR-6 audit re-validation.
"""

from __future__ import annotations

import os
from pathlib import Path

# Paths mirror typical Motadata monorepo layout (see PR-6 fixtures).
_M = "motadata"


def write_noisy_aiops_workspace(root: Path) -> None:
    """Create a tree under ``root`` covering mandatory + ambiguous PR-6 fixture anchors."""

    def _touch(rel: str, text: str) -> None:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        os.utime(p, ns=(1_000_000_000, 1_000_000_000))

    p = f"{_M}/src/main/java/com/mindarray"

    # --- Repo-confirmed-style anchors (see ``pr6_*_debug_queries.v1.json``)
    _touch(
        f"{p}/aiops/AvailabilityCorrelationEngine.java",
        """package com.mindarray.aiops;
public class AvailabilityCorrelationEngine {
  // alerts correlation issue handling for duplicate incidents
  // metrics ingestion intermittent availability correlation
  public void correlateDuplicateIncidents() {}
  public void correlateAlerts() {}
}
""",
    )
    _touch(
        f"{p}/aiops/DependencyManager.java",
        """package com.mindarray.aiops;
public class DependencyManager {
  // trace topology anomaly detector false positives in node graph
  // topology anomaly detector false positives node graph trace
  public void traceTopologyDependencies() {}
}
""",
    )
    _touch(
        f"{p}/aiops/DependencyQueryProcessor.java",
        """package com.mindarray.aiops;
public class DependencyQueryProcessor {
  // topology graph inconsistency dependency queries
  // investigate ingestion pipeline parser timeout metrics collector
  public void processDuplicateIncidents() {}
  public void orchestrateCollectorPipeline() {}
}
""",
    )
    _touch(
        f"{p}/nms/ObjectManager.java",
        """package com.mindarray.nms;
public class ObjectManager {
  // debug alert correlation engine failing duplicate incidents
  public void manageAlerts() {}
}
""",
    )
    _touch(
        f"{p}/nms/TopologyEngine.java",
        """package com.mindarray.nms;
public class TopologyEngine {
  // topology graph inconsistency cache refresh
  // alert correlation duplicate incidents engine debug
  public void refreshTopologyGraph() {}
}
""",
    )
    _touch(
        f"{p}/nms/MetricEnricher.java",
        """package com.mindarray.nms;
public class MetricEnricher {
  // metrics ingestion failing intermittently enrich pipeline
  public void enrichIngestionMetrics() {}
}
""",
    )
    _touch(
        f"{p}/nms/MetricPoller.java",
        """package com.mindarray.nms;
public class MetricPoller {
  // intermittent metrics ingestion collector failure
  public void pollIntermittentMetrics() {}
}
""",
    )
    _touch(
        f"{p}/eventbus/UIActionEventHandler.java",
        """package com.mindarray.eventbus;
public class UIActionEventHandler {
  // trace topology anomaly detector false positives in node graph
  // ingestion pipeline parser timeout metrics collector handling
  public void handleCorrelationAlerts() {}
}
""",
    )
    _touch(
        f"{p}/eventbus/EventEngine.java",
        """package com.mindarray.eventbus;
public class EventEngine {
  public void correlationHelperUtilities() {}
}
""",
    )
    _touch(
        f"{p}/eventbus/LocalEventChangeNotificationHandler.java",
        """package com.mindarray.eventbus;
public class LocalEventChangeNotificationHandler {
  public void notifyCollectorPipeline() {}
}
""",
    )
    _touch(
        f"{p}/util/MotadataConfigUtil.java",
        """package com.mindarray.util;
public class MotadataConfigUtil {
  // trace topology anomaly detector false positives in node graph
  public void loadAlertConfig() {}
}
""",
    )
    _touch(
        f"{p}/store/TopologyCacheStore.java",
        """package com.mindarray.store;
public class TopologyCacheStore {
  // topology graph inconsistency persistence
  public void persistTopologyGraphInconsistency() {}
}
""",
    )
    _touch(
        f"{p}/trace/TraceProcessor.java",
        """package com.mindarray.trace;
public class TraceProcessor {
  public void processServiceFacadeDelegation() {}
}
""",
    )
    _touch(
        f"{p}/trace/TraceStatCalculator.java",
        """package com.mindarray.trace;
public class TraceStatCalculator {
  public void correlateTraceStats() {}
}
""",
    )

    # --- Soft noise / siblings (ambiguous fixture distractors).
    # Note: no synthetic ``aiops/topology/*`` classes here — those masked real-style
    # anchors (nms/store) in PR-6 Slice 3 tests and do not appear in repo candidates.
    _touch(
        f"{p}/aiops/correlation/AlertCorrelationEngine.java",
        """package com.mindarray.aiops.correlation;
public class AlertCorrelationEngine {
  public void correlateDuplicateIncidents() {}
}
""",
    )
    _touch(
        f"{p}/aiops/correlation/CorrelationService.java",
        """package com.mindarray.aiops.correlation;
public class CorrelationService {
  public void correlateAlerts() {}
}
""",
    )
    _touch(
        f"{p}/aiops/correlation/CorrelationUtils.java",
        """package com.mindarray.aiops.correlation;
public class CorrelationUtils {
  void helper() {}
}
""",
    )
    _touch(
        f"{p}/aiops/correlation/internal/EventDeduper.java",
        """package com.mindarray.aiops.correlation.internal;
public class EventDeduper {
  void dedupeStreams() {}
}
""",
    )
    _touch(
        f"{p}/aiops/ingestion/IngestionPipeline.java",
        """package com.mindarray.aiops.ingestion;
public class IngestionPipeline {
  public void runCollectorPipeline() {}
  void orchestrateEndToEnd() {}
}
""",
    )
    _touch(
        f"{p}/aiops/ingestion/MetricsParser.java",
        """package com.mindarray.aiops.ingestion;
public class MetricsParser {
  public void parseCollectorMetrics() {}
  void intermittentFailureHook() {}
}
""",
    )
    _touch(
        f"{p}/aiops/ingestion/CollectorRegistry.java",
        """package com.mindarray.aiops.ingestion;
public class CollectorRegistry {
  void registerCollector() {}
}
""",
    )
    _touch(
        f"{p}/aiops/metrics/MetricsAggregator.java",
        """package com.mindarray.aiops.metrics;
public class MetricsAggregator {
  void rollup() {}
}
""",
    )
    _touch(
        f"{p}/aiops/shared/ServiceFacade.java",
        """package com.mindarray.aiops.shared;
public class ServiceFacade {
  void delegateToCorrelation() {}
}
""",
    )

    # --- Noise (same classification rules as production trees)
    _touch(
        f"{_M}/tests/correlation/alert_correlation_test.py",
        "alert correlation engine duplicate incidents topology metrics",
    )
    _touch(
        f"{_M}/logs/correlation.log",
        "correlate duplicate incidents engine failed intermittently",
    )
    _touch(f"{_M}/vendor/topology.js", "topology anomaly detector graph node ingestion")
    _touch(
        f"{_M}/test-plugin-metrics/collector_snapshot.json",
        '{"collector":"timeout","metrics":"ingestion"}',
    )

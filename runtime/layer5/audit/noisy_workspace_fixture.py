"""
Deterministic noisy AIOps-style workspace for PR-6 Slice 2 evaluation.

Not a real Motadata checkout — simulates soft noise, helpers, and multi-module layout.
"""

from __future__ import annotations

import os
from pathlib import Path


def write_noisy_aiops_workspace(root: Path) -> None:
    """Create a large-enough tree under ``root`` for ambiguous + mandatory PR-6 fixtures."""

    def _touch(rel: str, text: str) -> None:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        os.utime(p, ns=(1_000_000_000, 1_000_000_000))

    # --- Core correlation (mandatory + ambiguous)
    _touch(
        "src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java",
        """package com.mindarray.aiops.correlation;
public class AlertCorrelationEngine {
  public void correlateDuplicateIncidents() {}
  void mergeAlertStreams() {}
  // duplicate incident handling path
}
""",
    )
    _touch(
        "src/main/java/com/mindarray/aiops/correlation/CorrelationService.java",
        """package com.mindarray.aiops.correlation;
public class CorrelationService {
  public void correlateAlerts() {}
  void routeIncidentDedup() {}
}
""",
    )
    _touch(
        "src/main/java/com/mindarray/aiops/correlation/CorrelationUtils.java",
        """package com.mindarray.aiops.correlation;
public class CorrelationUtils {
  void helper() {}
  // correlation helper utilities noise
}
""",
    )
    _touch(
        "src/main/java/com/mindarray/aiops/correlation/internal/EventDeduper.java",
        """package com.mindarray.aiops.correlation.internal;
public class EventDeduper {
  void dedupeStreams() {}
}
""",
    )

    # --- Topology
    _touch(
        "src/main/java/com/mindarray/aiops/topology/TopologyAnomalyDetector.java",
        """package com.mindarray.aiops.topology;
public class TopologyAnomalyDetector {
  public void detectNodeGraphAnomaly() {}
}
""",
    )
    _touch(
        "src/main/java/com/mindarray/aiops/topology/NodeGraphAnalyzer.java",
        """package com.mindarray.aiops.topology;
public class NodeGraphAnalyzer {
  public void analyzeGraphNodes() {}
}
""",
    )
    _touch(
        "src/main/java/com/mindarray/aiops/topology/GraphConsistencyChecker.java",
        """package com.mindarray.aiops.topology;
public class GraphConsistencyChecker {
  void checkTopologyGraphInconsistency() {}
}
""",
    )

    # --- Ingestion / metrics
    _touch(
        "src/main/java/com/mindarray/aiops/ingestion/IngestionPipeline.java",
        """package com.mindarray.aiops.ingestion;
public class IngestionPipeline {
  public void runCollectorPipeline() {}
  void orchestrateEndToEnd() {}
}
""",
    )
    _touch(
        "src/main/java/com/mindarray/aiops/ingestion/MetricsParser.java",
        """package com.mindarray.aiops.ingestion;
public class MetricsParser {
  public void parseCollectorMetrics() {}
  void intermittentFailureHook() {}
}
""",
    )
    _touch(
        "src/main/java/com/mindarray/aiops/ingestion/CollectorRegistry.java",
        """package com.mindarray.aiops.ingestion;
public class CollectorRegistry {
  void registerCollector() {}
}
""",
    )
    _touch(
        "src/main/java/com/mindarray/aiops/metrics/MetricsAggregator.java",
        """package com.mindarray.aiops.metrics;
public class MetricsAggregator {
  void rollup() {}
}
""",
    )

    # --- Shared facade (soft collision)
    _touch(
        "src/main/java/com/mindarray/aiops/shared/ServiceFacade.java",
        """package com.mindarray.aiops.shared;
public class ServiceFacade {
  void delegateToCorrelation() {}
}
""",
    )

    # --- Noise
    _touch(
        "tests/correlation/alert_correlation_test.py",
        "alert correlation engine duplicate incidents topology metrics",
    )
    _touch("logs/correlation.log", "correlate duplicate incidents engine failed intermittently")
    _touch("vendor/topology.js", "topology anomaly detector graph node ingestion")
    _touch("test-plugin-metrics/collector_snapshot.json", '{"collector":"timeout","metrics":"ingestion"}')

# PR-6 real-repo (or bundled) retrieval audit
## Workspace source
- bundled noisy fixture (no real AIOps checkout found): `/home/harshil/Harshil-PoCs/m-coder/runtime/layer5/audit/fixture_noisy_aiops_workspace` (set `PR6_AIOPS_ROOT` to evaluate a real tree)
- **Indexed files:** 16
- **Queries run:** 10

## Per-query results
### `alert_correlation_engine_debug` (mandatory)
- **query:** Debug alert correlation engine failing to correlate duplicate incidents
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java` — 57 ✓
  - **diagnostics (top-1):** {'path_lexical': 4, 'basename_lexical': 6, 'content': 9, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 15, 'module_bias': 4, 'noise_penalty': 0, 'total': 57}
  - **note:** top-1 is an expected anchor.
  2. `src/main/java/com/mindarray/aiops/correlation/CorrelationService.java` — 43 ✓
  3. `src/main/java/com/mindarray/aiops/correlation/CorrelationUtils.java` — 39
  4. `src/main/java/com/mindarray/aiops/shared/ServiceFacade.java` — 27
  5. `src/main/java/com/mindarray/aiops/correlation/internal/EventDeduper.java` — 25

### `topology_anomaly_detector_debug` (mandatory)
- **query:** Trace topology anomaly detector false positives in node graph
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `src/main/java/com/mindarray/aiops/topology/TopologyAnomalyDetector.java` — 58 ✓
  - **diagnostics (top-1):** {'path_lexical': 6, 'basename_lexical': 6, 'content': 8, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 15, 'module_bias': 4, 'noise_penalty': 0, 'total': 58}
  - **note:** top-1 is an expected anchor.
  2. `src/main/java/com/mindarray/aiops/topology/NodeGraphAnalyzer.java` — 50 ✓
  3. `src/main/java/com/mindarray/aiops/topology/GraphConsistencyChecker.java` — 47
  4. `src/main/java/com/mindarray/aiops/ingestion/IngestionPipeline.java` — 27
  5. `src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java` — 23

### `ingestion_pipeline_parser_debug` (mandatory)
- **query:** Investigate ingestion pipeline parser timeout for metrics collector
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `src/main/java/com/mindarray/aiops/ingestion/IngestionPipeline.java` — 50 ✓
  - **diagnostics (top-1):** {'path_lexical': 3, 'basename_lexical': 4, 'content': 5, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 15, 'module_bias': 4, 'noise_penalty': 0, 'total': 50}
  - **note:** top-1 is an expected anchor.
  2. `src/main/java/com/mindarray/aiops/ingestion/MetricsParser.java` — 50 ✓
  3. `src/main/java/com/mindarray/aiops/ingestion/CollectorRegistry.java` — 39
  4. `src/main/java/com/mindarray/aiops/metrics/MetricsAggregator.java` — 38
  5. `src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java` — 13

### `ambiguous_correlation_alerts` (ambiguous)
- **query:** Correlation issue in alerts
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java` — 49 ✓
  - **diagnostics (top-1):** {'path_lexical': 5, 'basename_lexical': 4, 'content': 8, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 9, 'module_bias': 4, 'noise_penalty': 0, 'total': 49}
  - **note:** top-1 is an expected anchor.
  2. `src/main/java/com/mindarray/aiops/correlation/CorrelationService.java` — 46 ✓
  3. `src/main/java/com/mindarray/aiops/correlation/CorrelationUtils.java` — 42
  4. `src/main/java/com/mindarray/aiops/correlation/internal/EventDeduper.java` — 30 ✓
  5. `src/main/java/com/mindarray/aiops/ingestion/IngestionPipeline.java` — 27

### `ambiguous_topology_graph` (ambiguous)
- **query:** Topology graph inconsistency
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `src/main/java/com/mindarray/aiops/topology/GraphConsistencyChecker.java` — 47 ✓
  - **diagnostics (top-1):** {'path_lexical': 2, 'basename_lexical': 2, 'content': 5, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 15, 'module_bias': 4, 'noise_penalty': 0, 'total': 47}
  - **note:** top-1 is an expected anchor.
  2. `src/main/java/com/mindarray/aiops/topology/TopologyAnomalyDetector.java` — 42 ✓
  3. `src/main/java/com/mindarray/aiops/topology/NodeGraphAnalyzer.java` — 39 ✓
  4. `src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java` — 13
  5. `src/main/java/com/mindarray/aiops/correlation/CorrelationService.java` — 13

### `ambiguous_metrics_ingestion_intermittent` (ambiguous)
- **query:** Metrics ingestion failing intermittently
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `src/main/java/com/mindarray/aiops/ingestion/MetricsParser.java` — 39 ✓
  - **diagnostics (top-1):** {'path_lexical': 2, 'basename_lexical': 2, 'content': 3, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 9, 'module_bias': 4, 'noise_penalty': 0, 'total': 39}
  - **note:** top-1 is an expected anchor.
  2. `src/main/java/com/mindarray/aiops/ingestion/IngestionPipeline.java` — 38 ✓
  3. `src/main/java/com/mindarray/aiops/metrics/MetricsAggregator.java` — 38 ✓
  4. `src/main/java/com/mindarray/aiops/ingestion/CollectorRegistry.java` — 25
  5. `src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java` — 13

### `indirect_duplicate_incidents` (ambiguous)
- **query:** duplicate incident handling
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java` — 33 ✓
  - **diagnostics (top-1):** {'path_lexical': 0, 'basename_lexical': 0, 'content': 5, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 9, 'module_bias': 0, 'noise_penalty': 0, 'total': 33}
  - **note:** top-1 is an expected anchor.
  2. `src/main/java/com/mindarray/aiops/correlation/CorrelationService.java` — 29 ✓
  3. `src/main/java/com/mindarray/aiops/correlation/CorrelationUtils.java` — 19
  4. `src/main/java/com/mindarray/aiops/correlation/internal/EventDeduper.java` — 19
  5. `src/main/java/com/mindarray/aiops/ingestion/CollectorRegistry.java` — 13

### `soft_noise_helper_utils` (ambiguous)
- **query:** correlation helper utilities
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `src/main/java/com/mindarray/aiops/correlation/CorrelationUtils.java` — 45 ✓
  - **diagnostics (top-1):** {'path_lexical': 2, 'basename_lexical': 2, 'content': 6, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 12, 'module_bias': 4, 'noise_penalty': 0, 'total': 45}
  - **note:** top-1 is an expected anchor.
  2. `src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java` — 38
  3. `src/main/java/com/mindarray/aiops/correlation/CorrelationService.java` — 38 ✓
  4. `src/main/java/com/mindarray/aiops/correlation/internal/EventDeduper.java` — 25
  5. `src/main/java/com/mindarray/aiops/shared/ServiceFacade.java` — 23 ✓

### `multi_file_pipeline_orchestration` (ambiguous)
- **query:** orchestrate collector pipeline end to end
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `src/main/java/com/mindarray/aiops/ingestion/IngestionPipeline.java` — 47 ✓
  - **diagnostics (top-1):** {'path_lexical': 1, 'basename_lexical': 2, 'content': 10, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 15, 'module_bias': 0, 'noise_penalty': 0, 'total': 47}
  - **note:** top-1 is an expected anchor.
  2. `src/main/java/com/mindarray/aiops/ingestion/CollectorRegistry.java` — 38 ✓
  3. `src/main/java/com/mindarray/aiops/ingestion/MetricsParser.java` — 30 ✓
  4. `src/main/java/com/mindarray/aiops/shared/ServiceFacade.java` — 23
  5. `src/main/java/com/mindarray/aiops/topology/TopologyAnomalyDetector.java` — 23

### `soft_collision_shared_facade` (ambiguous)
- **query:** service facade delegation correlation
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `src/main/java/com/mindarray/aiops/correlation/CorrelationService.java` — 45 ✓
  - **diagnostics (top-1):** {'path_lexical': 3, 'basename_lexical': 4, 'content': 3, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 12, 'module_bias': 4, 'noise_penalty': 0, 'total': 45}
  - **note:** top-1 is an expected anchor.
  2. `src/main/java/com/mindarray/aiops/correlation/CorrelationUtils.java` — 39
  3. `src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java` — 38
  4. `src/main/java/com/mindarray/aiops/shared/ServiceFacade.java` — 37 ✓
  5. `src/main/java/com/mindarray/aiops/correlation/internal/EventDeduper.java` — 25

## Aggregate metrics
- **top-1 accuracy:** 10/10 = 1.00
- **top-3 anchor hit rate:** 10/10 = 1.00
- **mean first relevant rank:** 1.00
- **mean noise dominance ratio (top-5):** 0.00

## Failure analysis
- No queries missed all anchors in top-k (first relevant rank defined for all).

## Caveat validation
- **Package-private methods:** extractor extended (regex); see unit test `test_package_private_methods_in_symbol_inventory`.
- **Module/path bias:** `RetrievalHit.diagnostics` exposes `module_bias` vs `symbol_inventory_boost` vs `content` for top-1 rows above.

## Adjustments made in this slice
- Diagnostics-only (`include_score_diagnostics`) + package-private regex extension; **no retrieval weight tuning** in this pass (failures classified first).

## Verdict
**READY** for next slice (subject to real-checkout confirmation).

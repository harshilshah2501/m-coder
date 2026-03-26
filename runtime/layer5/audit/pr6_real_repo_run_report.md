# PR-6 real-repo (or bundled) retrieval audit
## Workspace source
- environment `PR6_AIOPS_ROOT` / `MOTADATA_AIOPS_REPO_ROOT` → `/home/harshil/Projects/Motadata`
- **Indexed files:** 2432
- **Queries run:** 10

## Per-query results
### `alert_correlation_engine_debug` (mandatory)
- **query:** Debug alert correlation engine failing to correlate duplicate incidents
- **first relevant rank:** 3
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/visualization/VisualizationConstants.java` — 1470
  - **diagnostics (top-1):** {'path_lexical': 0, 'basename_lexical': 0, 'content': 1458, 'path_prior': 5, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 0, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'code_intent': 1, 'total': 1470}
  - **note:** path_prior exceeds symbol_inventory on this file — class policy prior strong
  2. `motadata/src/main/java/com/mindarray/nms/NMSConstants.java` — 936
  3. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 824 ✓
  4. `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java` — 802
  5. `motadata/src/main/java/com/mindarray/nms/ObjectManager.java` — 765 ✓

### `topology_anomaly_detector_debug` (mandatory)
- **query:** Trace topology anomaly detector false positives in node graph
- **first relevant rank:** 3
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/visualization/VisualizationConstants.java` — 2967
  - **diagnostics (top-1):** {'path_lexical': 2, 'basename_lexical': 0, 'content': 2953, 'path_prior': 5, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 0, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'code_intent': 1, 'total': 2967}
  - **note:** path_prior exceeds symbol_inventory on this file — class policy prior strong
  2. `motadata/src/main/java/com/mindarray/nms/NMSConstants.java` — 2253
  3. `motadata/src/main/java/com/mindarray/aiops/DependencyManager.java` — 1154 ✓
  4. `motadata/src/main/java/com/mindarray/util/MotadataConfigUtil.java` — 1961
  5. `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` — 1759

### `ingestion_pipeline_parser_debug` (mandatory)
- **query:** Investigate ingestion pipeline parser timeout for metrics collector
- **first relevant rank:** 3
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java` — 422
  - **diagnostics (top-1):** {'path_lexical': 0, 'basename_lexical': 0, 'content': 410, 'path_prior': 5, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 0, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'code_intent': 1, 'total': 422}
  - **note:** path_prior exceeds symbol_inventory on this file — class policy prior strong
  2. `motadata/src/main/java/com/mindarray/integration/LAMAIntegration.java` — 386
  3. `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` — 286 ✓
  4. `motadata/src/main/java/com/mindarray/nms/MetricPoller.java` — 349
  5. `motadata/src/main/java/com/mindarray/log/LogParser.java` — 338

### `ambiguous_correlation_alerts` (ambiguous)
- **query:** Correlation issue in alerts
- **first relevant rank:** 3
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/visualization/VisualizationConstants.java` — 2875
  - **diagnostics (top-1):** {'path_lexical': 2, 'basename_lexical': 0, 'content': 2861, 'path_prior': 5, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 0, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'code_intent': 1, 'total': 2875}
  - **note:** path_prior exceeds symbol_inventory on this file — class policy prior strong
  2. `motadata/src/main/java/com/mindarray/nms/NMSConstants.java` — 2165
  3. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 1300 ✓
  4. `motadata/src/main/java/com/mindarray/util/MotadataConfigUtil.java` — 1830 ✓
  5. `motadata/src/main/java/com/mindarray/policy/PolicyEngineConstants.java` — 1716

### `ambiguous_topology_graph` (ambiguous)
- **query:** Topology graph inconsistency
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/nms/TopologyEngine.java` — 273 ✓
  - **diagnostics (top-1):** {'path_lexical': 1, 'basename_lexical': 2, 'content': 258, 'path_prior': 5, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 0, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'code_intent': 1, 'total': 273}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/api/TopologyPlugin.java` — 93
  3. `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` — 44 ✓
  4. `motadata/src/main/java/com/mindarray/nms/NMSConstants.java` — 69
  5. `motadata/src/main/java/com/mindarray/store/TopologyCacheStore.java` — 47 ✓

### `ambiguous_metrics_ingestion_intermittent` (ambiguous)
- **query:** Metrics ingestion failing intermittently
- **first relevant rank:** None
- **top-3 anchor hit:** no
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/nms/MetricEnricher.java` — 240
  - **diagnostics (top-1):** {'path_lexical': 0, 'basename_lexical': 0, 'content': 228, 'path_prior': 5, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 0, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'code_intent': 1, 'total': 240}
  - **note:** path_prior exceeds symbol_inventory on this file — class policy prior strong
  2. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 28
  3. `motadata/src/main/java/com/mindarray/nms/MetricPoller.java` — 176
  4. `motadata/src/main/java/com/mindarray/netroute/NetRouteResponseProcessor.java` — 65
  5. `motadata/src/main/java/com/mindarray/nms/ResponseProcessor.java` — 61

### `indirect_duplicate_incidents` (ambiguous)
- **query:** duplicate incident handling
- **first relevant rank:** 3
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/integration/ServiceNowIntegration.java` — 75
  - **diagnostics (top-1):** {'path_lexical': 0, 'basename_lexical': 0, 'content': 63, 'path_prior': 5, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 0, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'code_intent': 1, 'total': 75}
  - **note:** path_prior exceeds symbol_inventory on this file — class policy prior strong
  2. `motadata/src/main/java/com/mindarray/nms/MetricPoller.java` — 36
  3. `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` — 32 ✓
  4. `motadata/src/main/java/com/mindarray/manager/MotadataAppManager.java` — 29
  5. `motadata/src/main/java/com/mindarray/slo/SLOConstants.java` — 29

### `soft_noise_helper_utils` (ambiguous)
- **query:** correlation helper utilities
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 322 ✓
  - **diagnostics (top-1):** {'path_lexical': 1, 'basename_lexical': 2, 'content': 290, 'path_prior': 13, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 9, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'code_intent': 1, 'total': 322}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/aiops/AIOpsConstants.java` — 87
  3. `motadata/src/main/java/com/mindarray/policy/MetricPolicyInspector.java` — 62
  4. `motadata/src/main/java/com/mindarray/eventbus/EventEngine.java` — 55
  5. `motadata/src/main/java/com/mindarray/datastore/DatastoreEngine.java` — 30

### `multi_file_pipeline_orchestration` (ambiguous)
- **query:** orchestrate collector pipeline end to end
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` — 2117 ✓
  - **diagnostics (top-1):** {'path_lexical': 2, 'basename_lexical': 4, 'content': 2082, 'path_prior': 13, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 9, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'code_intent': 1, 'total': 2117}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/aiops/DependencyManager.java` — 2010 ✓
  3. `motadata/src/main/java/com/mindarray/visualization/VisualizationConstants.java` — 1548
  4. `motadata/src/main/java/com/mindarray/nms/TopologyEngine.java` — 1347
  5. `motadata/src/main/java/com/mindarray/nms/ObjectManager.java` — 1141

### `soft_collision_shared_facade` (ambiguous)
- **query:** service facade delegation correlation
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 325 ✓
  - **diagnostics (top-1):** {'path_lexical': 1, 'basename_lexical': 2, 'content': 293, 'path_prior': 13, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 9, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'code_intent': 1, 'total': 325}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/trace/TraceProcessor.java` — 255
  3. `motadata/src/main/java/com/mindarray/trace/TraceConstants.java` — 191
  4. `motadata/src/main/java/com/mindarray/integration/ServiceNowIntegration.java` — 179
  5. `motadata/src/main/java/com/mindarray/nms/NMSConstants.java` — 165

## Aggregate metrics
- **top-1 accuracy:** 4/10 = 0.40
- **top-3 anchor hit rate:** 9/10 = 0.90
- **mean first relevant rank:** 2.11
- **mean noise dominance ratio (top-5):** 0.00

## Failure analysis
- **ambiguous_metrics_ingestion_intermittent:** no anchor in top-k (inspect diagnostics on top rows).

## Caveat validation
- **Package-private methods:** extractor extended (regex); see unit test `test_package_private_methods_in_symbol_inventory`.
- **Module/path bias:** `RetrievalHit.diagnostics` exposes `module_bias` vs `symbol_inventory_boost` vs `content` for top-1 rows above.

## Adjustments made in this slice
- **Slice 3:** code/debug intent content gating on noise file classes, optional ``config`` content cap, ``retrieval_policy.v3`` main-Java lane bonus, ``db-files`` → ``generated_metrics_data`` classification, expanded diagnostics.

## Verdict
**NOT READY** — review failure analysis and real `PR6_AIOPS_ROOT` run.
- **Caveat:** top-3 anchor hit rate is 0.90; treat as **NOT READY** for closure until all fixtures recover anchors in top-3 on the target checkout.

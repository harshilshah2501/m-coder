# PR-6 real-repo (or bundled) retrieval audit
## Workspace source
- environment `PR6_AIOPS_ROOT` / `MOTADATA_AIOPS_REPO_ROOT` → `/home/harshil/Projects/Motadata`
- **Indexed files:** 2432
- **Queries run:** 10

## Per-query results
### `alert_correlation_engine_debug` (mandatory)
- **query:** Debug alert correlation engine failing to correlate duplicate incidents
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 832 ✓
  - **diagnostics (top-1):** {'path_lexical': 2, 'basename_lexical': 4, 'content': 786, 'path_prior': 13, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 12, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 8, 'support_file_demotion': 0, 'total': 832}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java` — 802
  3. `motadata/src/main/java/com/mindarray/nms/ObjectManager.java` — 765 ✓
  4. `motadata/src/main/java/com/mindarray/nms/TopologyEngine.java` — 737 ✓
  5. `motadata/src/main/java/com/mindarray/api/APIServer.java` — 654

### `topology_anomaly_detector_debug` (mandatory)
- **query:** Trace topology anomaly detector false positives in node graph
- **first relevant rank:** 3
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java` — 2027
  - **diagnostics (top-1):** {'path_lexical': 2, 'basename_lexical': 0, 'content': 2013, 'path_prior': 5, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 0, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 0, 'support_file_demotion': 0, 'total': 2027}
  - **note:** path_prior exceeds symbol_inventory on this file — class policy prior strong
  2. `motadata/src/main/java/com/mindarray/util/MotadataConfigUtil.java` — 1961
  3. `motadata/src/main/java/com/mindarray/aiops/DependencyManager.java` — 1154 ✓
  4. `motadata/src/main/java/com/mindarray/nms/ObjectManager.java` — 1429
  5. `motadata/src/main/java/com/mindarray/nms/TopologyEngine.java` — 1426 ✓

### `ingestion_pipeline_parser_debug` (mandatory)
- **query:** Investigate ingestion pipeline parser timeout for metrics collector
- **first relevant rank:** 3
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java` — 422
  - **diagnostics (top-1):** {'path_lexical': 0, 'basename_lexical': 0, 'content': 410, 'path_prior': 5, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 0, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 0, 'support_file_demotion': 0, 'total': 422}
  - **note:** path_prior exceeds symbol_inventory on this file — class policy prior strong
  2. `motadata/src/main/java/com/mindarray/integration/LAMAIntegration.java` — 386
  3. `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` — 286 ✓
  4. `motadata/src/main/java/com/mindarray/nms/MetricPoller.java` — 349
  5. `motadata/src/main/java/com/mindarray/log/LogParser.java` — 342

### `ambiguous_correlation_alerts` (ambiguous)
- **query:** Correlation issue in alerts
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java` — 1857 ✓
  - **diagnostics (top-1):** {'path_lexical': 2, 'basename_lexical': 0, 'content': 1843, 'path_prior': 5, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 0, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 0, 'support_file_demotion': 0, 'total': 1857}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/util/MotadataConfigUtil.java` — 1830 ✓
  3. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 1304 ✓
  4. `motadata/src/main/java/com/mindarray/nms/ObjectManager.java` — 1388
  5. `motadata/src/main/java/com/mindarray/api/APIServer.java` — 1469

### `ambiguous_topology_graph` (ambiguous)
- **query:** Topology graph inconsistency
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/nms/TopologyEngine.java` — 277 ✓
  - **diagnostics (top-1):** {'path_lexical': 1, 'basename_lexical': 2, 'content': 258, 'path_prior': 5, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 0, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 4, 'support_file_demotion': 0, 'total': 277}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/api/TopologyPlugin.java` — 97
  3. `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` — 44 ✓
  4. `motadata/src/main/java/com/mindarray/store/TopologyCacheStore.java` — 51 ✓
  5. `motadata/src/main/java/com/mindarray/eventbus/UIActionEventHandler.java` — 45

### `ambiguous_metrics_ingestion_intermittent` (ambiguous)
- **query:** Metrics ingestion failing intermittently
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/nms/MetricEnricher.java` — 240 ✓
  - **diagnostics (top-1):** {'path_lexical': 0, 'basename_lexical': 0, 'content': 228, 'path_prior': 5, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 0, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 0, 'support_file_demotion': 0, 'total': 240}
  - **note:** top-1 is an expected anchor.
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
  - **diagnostics (top-1):** {'path_lexical': 0, 'basename_lexical': 0, 'content': 63, 'path_prior': 5, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 0, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 0, 'support_file_demotion': 0, 'total': 75}
  - **note:** path_prior exceeds symbol_inventory on this file — class policy prior strong
  2. `motadata/src/main/java/com/mindarray/nms/MetricPoller.java` — 36
  3. `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` — 32 ✓
  4. `motadata/src/main/java/com/mindarray/manager/MotadataAppManager.java` — 29
  5. `motadata/src/main/java/com/mindarray/integration/ServiceOpsIntegration.java` — 26

### `soft_noise_helper_utils` (ambiguous)
- **query:** correlation helper utilities
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 326 ✓
  - **diagnostics (top-1):** {'path_lexical': 1, 'basename_lexical': 2, 'content': 290, 'path_prior': 13, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 9, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 4, 'support_file_demotion': 0, 'total': 326}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/policy/MetricPolicyInspector.java` — 62
  3. `motadata/src/main/java/com/mindarray/eventbus/EventEngine.java` — 55
  4. `motadata/src/main/java/com/mindarray/aiops/AIOpsConstants.java` — 43
  5. `motadata/src/main/java/com/mindarray/datastore/DatastoreEngine.java` — 30

### `multi_file_pipeline_orchestration` (ambiguous)
- **query:** orchestrate collector pipeline end to end
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` — 2117 ✓
  - **diagnostics (top-1):** {'path_lexical': 2, 'basename_lexical': 4, 'content': 2082, 'path_prior': 13, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 9, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 0, 'support_file_demotion': 0, 'total': 2117}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/aiops/DependencyManager.java` — 2010 ✓
  3. `motadata/src/main/java/com/mindarray/nms/TopologyEngine.java` — 1347
  4. `motadata/src/main/java/com/mindarray/nms/ObjectManager.java` — 1141
  5. `motadata/src/main/java/com/mindarray/eventbus/LocalEventChangeNotificationHandler.java` — 1091 ✓

### `soft_collision_shared_facade` (ambiguous)
- **query:** service facade delegation correlation
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 329 ✓
  - **diagnostics (top-1):** {'path_lexical': 1, 'basename_lexical': 2, 'content': 293, 'path_prior': 13, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 9, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 4, 'support_file_demotion': 0, 'total': 329}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/trace/TraceProcessor.java` — 255
  3. `motadata/src/main/java/com/mindarray/integration/ServiceNowIntegration.java` — 183
  4. `motadata/src/main/java/com/mindarray/rum/RUMEventProcessor.java` — 125
  5. `motadata/src/main/java/com/mindarray/trace/TraceStatCalculator.java` — 124

## Aggregate metrics
- **top-1 accuracy:** 7/10 = 0.70
- **top-3 anchor hit rate:** 10/10 = 1.00
- **mean first relevant rank:** 1.60
- **mean noise dominance ratio (top-5):** 0.00

## Failure analysis
- No queries missed all anchors in top-k (first relevant rank defined for all).

## Caveat validation
- **Package-private methods:** extractor extended (regex); see unit test `test_package_private_methods_in_symbol_inventory`.
- **Module/path bias:** `RetrievalHit.diagnostics` exposes `module_bias` vs `symbol_inventory_boost` vs `content` for top-1 rows above.

## Adjustments made in this slice
- **Slice 3:** code/debug intent content gating on noise file classes, optional ``config`` content cap, ``retrieval_policy.v3`` main-Java lane bonus, ``db-files`` → ``generated_metrics_data`` classification, expanded diagnostics.
- **Slice 4:** ``retrieval_policy.v4`` — support-style Java basename content cap + demotion, basename/query CamelCase token overlap (specificity), diagnostics (``basename_specificity``, ``support_file_demotion``, ``support_style_content_trimmed``).

## Verdict
**READY** for next slice (subject to real-checkout confirmation).

# PR-6 Closure Validation Report — Canonical
## PR-6 real-repo (or bundled) retrieval audit
## Workspace source
- **audit mode:** `PR6_CLOSURE_AUDIT`
- **context mode:** `fixture_diagnostic`
- environment root classified as fixture_diagnostic: `/home/harshil/Harshil-PoCs/m-coder/runtime/layer5/audit/fixture_noisy_aiops_workspace` (Root is bundled PR-6 fixture workspace; diagnostic-only context.)
- **Indexed files:** 27
- **Queries run:** 10

## Per-query results
### `alert_correlation_engine_debug` (mandatory)
- **query:** Debug alert correlation engine failing to correlate duplicate incidents
- **first relevant rank:** 2
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java` — 110
  - **diagnostics (top-1):** {'path_lexical': 4, 'basename_lexical': 6, 'content': 7, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 15, 'module_bias': 4, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'generic_facade_content_trimmed': 0, 'topic_focus_supporting_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 12, 'support_file_demotion': 0, 'owner_evidence_score': 27, 'direct_owner_alignment': 1, 'generic_integration_demotion': 0, 'ingestion_log_parser_demotion': 0, 'duplicate_incident_core_boost': 36, 'facade_cap_basename_or_symbol_owner_signal': 1, 'total': 110}
  - **note:** inspect content vs symbol_inventory vs lexical path overlap
  2. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 97 ✓
  3. `motadata/src/main/java/com/mindarray/aiops/correlation/CorrelationService.java` — 90
  4. `motadata/src/main/java/com/mindarray/aiops/correlation/CorrelationUtils.java` — 75
  5. `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` — 73

### `topology_anomaly_detector_debug` (mandatory)
- **query:** Trace topology anomaly detector false positives in node graph
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/DependencyManager.java` — 54 ✓
  - **diagnostics (top-1):** {'path_lexical': 2, 'basename_lexical': 0, 'content': 20, 'path_prior': 13, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 12, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'generic_facade_content_trimmed': 0, 'topic_focus_supporting_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 0, 'support_file_demotion': 0, 'owner_evidence_score': 12, 'direct_owner_alignment': 1, 'generic_integration_demotion': 0, 'ingestion_log_parser_demotion': 0, 'duplicate_incident_core_boost': 0, 'facade_cap_basename_or_symbol_owner_signal': 0, 'total': 54}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/aiops/ingestion/IngestionPipeline.java` — 34
  3. `motadata/src/main/java/com/mindarray/nms/TopologyEngine.java` — 34 ✓
  4. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 32
  5. `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` — 31

### `ingestion_pipeline_parser_debug` (mandatory)
- **query:** Investigate ingestion pipeline parser timeout for metrics collector
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/ingestion/IngestionPipeline.java` — 65 ✓
  - **diagnostics (top-1):** {'path_lexical': 3, 'basename_lexical': 4, 'content': 5, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 15, 'module_bias': 4, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'generic_facade_content_trimmed': 0, 'topic_focus_supporting_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 8, 'support_file_demotion': 0, 'owner_evidence_score': 23, 'direct_owner_alignment': 1, 'generic_integration_demotion': 0, 'ingestion_log_parser_demotion': 0, 'duplicate_incident_core_boost': 0, 'facade_cap_basename_or_symbol_owner_signal': 1, 'total': 65}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/aiops/ingestion/MetricsParser.java` — 65 ✓
  3. `motadata/src/main/java/com/mindarray/aiops/ingestion/CollectorRegistry.java` — 50
  4. `motadata/src/main/java/com/mindarray/aiops/metrics/MetricsAggregator.java` — 49
  5. `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` — 41 ✓

### `ambiguous_correlation_alerts` (ambiguous)
- **query:** Correlation issue in alerts
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 57 ✓
  - **diagnostics (top-1):** {'path_lexical': 4, 'basename_lexical': 4, 'content': 13, 'path_prior': 13, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 12, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'generic_facade_content_trimmed': 0, 'topic_focus_supporting_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 4, 'support_file_demotion': 0, 'owner_evidence_score': 16, 'direct_owner_alignment': 1, 'generic_integration_demotion': 0, 'ingestion_log_parser_demotion': 0, 'duplicate_incident_core_boost': 0, 'facade_cap_basename_or_symbol_owner_signal': 1, 'total': 57}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java` — 57
  3. `motadata/src/main/java/com/mindarray/aiops/correlation/CorrelationService.java` — 56
  4. `motadata/src/main/java/com/mindarray/aiops/correlation/CorrelationUtils.java` — 42
  5. `motadata/src/main/java/com/mindarray/aiops/correlation/internal/EventDeduper.java` — 37

### `ambiguous_topology_graph` (ambiguous)
- **query:** Topology graph inconsistency
- **first relevant rank:** 2
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/DependencyManager.java` — 34
  - **diagnostics (top-1):** {'path_lexical': 0, 'basename_lexical': 0, 'content': 5, 'path_prior': 13, 'subsystem_boost': 0, 'symbol_boost': 0, 'symbol_inventory_boost': 9, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'generic_facade_content_trimmed': 0, 'topic_focus_supporting_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 0, 'support_file_demotion': 0, 'owner_evidence_score': 9, 'direct_owner_alignment': 1, 'generic_integration_demotion': 0, 'ingestion_log_parser_demotion': 0, 'duplicate_incident_core_boost': 0, 'facade_cap_basename_or_symbol_owner_signal': 0, 'total': 34}
  - **note:** path_prior exceeds symbol_inventory on this file — class policy prior strong
  2. `motadata/src/main/java/com/mindarray/store/TopologyCacheStore.java` — 26 ✓
  3. `motadata/src/main/java/com/mindarray/nms/TopologyEngine.java` — 25 ✓
  4. `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` — 23 ✓
  5. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 20

### `ambiguous_metrics_ingestion_intermittent` (ambiguous)
- **query:** Metrics ingestion failing intermittently
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/ingestion/MetricsParser.java` — 50 ✓
  - **diagnostics (top-1):** {'path_lexical': 2, 'basename_lexical': 2, 'content': 3, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 9, 'module_bias': 4, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'generic_facade_content_trimmed': 0, 'topic_focus_supporting_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 4, 'support_file_demotion': 0, 'owner_evidence_score': 13, 'direct_owner_alignment': 1, 'generic_integration_demotion': 0, 'ingestion_log_parser_demotion': 0, 'duplicate_incident_core_boost': 0, 'facade_cap_basename_or_symbol_owner_signal': 1, 'total': 50}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/aiops/ingestion/IngestionPipeline.java` — 49 ✓
  3. `motadata/src/main/java/com/mindarray/aiops/metrics/MetricsAggregator.java` — 49
  4. `motadata/src/main/java/com/mindarray/aiops/ingestion/CollectorRegistry.java` — 32
  5. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 22

### `indirect_duplicate_incidents` (ambiguous)
- **query:** duplicate incident handling
- **first relevant rank:** 2
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java` — 73
  - **diagnostics (top-1):** {'path_lexical': 0, 'basename_lexical': 0, 'content': 2, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 9, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'generic_facade_content_trimmed': 0, 'topic_focus_supporting_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 0, 'support_file_demotion': 0, 'owner_evidence_score': 9, 'direct_owner_alignment': 1, 'generic_integration_demotion': 0, 'ingestion_log_parser_demotion': 0, 'duplicate_incident_core_boost': 36, 'facade_cap_basename_or_symbol_owner_signal': 0, 'total': 73}
  - **note:** path_prior exceeds symbol_inventory on this file — class policy prior strong
  2. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 70 ✓
  3. `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` — 67 ✓
  4. `motadata/src/main/java/com/mindarray/aiops/correlation/CorrelationService.java` — 62
  5. `motadata/src/main/java/com/mindarray/aiops/DependencyManager.java` — 56 ✓

### `soft_noise_helper_utils` (ambiguous)
- **query:** correlation helper utilities
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java` — 49 ✓
  - **diagnostics (top-1):** {'path_lexical': 2, 'basename_lexical': 2, 'content': 2, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 9, 'module_bias': 4, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'generic_facade_content_trimmed': 0, 'topic_focus_supporting_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 4, 'support_file_demotion': 0, 'owner_evidence_score': 13, 'direct_owner_alignment': 1, 'generic_integration_demotion': 0, 'ingestion_log_parser_demotion': 0, 'duplicate_incident_core_boost': 0, 'facade_cap_basename_or_symbol_owner_signal': 1, 'total': 49}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/aiops/correlation/CorrelationService.java` — 49
  3. `motadata/src/main/java/com/mindarray/aiops/correlation/CorrelationUtils.java` — 43 ✓
  4. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 39 ✓
  5. `motadata/src/main/java/com/mindarray/aiops/correlation/internal/EventDeduper.java` — 32

### `multi_file_pipeline_orchestration` (ambiguous)
- **query:** orchestrate collector pipeline end to end
- **first relevant rank:** 2
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/ingestion/IngestionPipeline.java` — 58
  - **diagnostics (top-1):** {'path_lexical': 1, 'basename_lexical': 2, 'content': 10, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 15, 'module_bias': 0, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'generic_facade_content_trimmed': 0, 'topic_focus_supporting_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 4, 'support_file_demotion': 0, 'owner_evidence_score': 19, 'direct_owner_alignment': 1, 'generic_integration_demotion': 0, 'ingestion_log_parser_demotion': 0, 'duplicate_incident_core_boost': 0, 'facade_cap_basename_or_symbol_owner_signal': 1, 'total': 58}
  - **note:** inspect content vs symbol_inventory vs lexical path overlap
  2. `motadata/src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java` — 53 ✓
  3. `motadata/src/main/java/com/mindarray/aiops/ingestion/CollectorRegistry.java` — 49
  4. `motadata/src/main/java/com/mindarray/aiops/ingestion/MetricsParser.java` — 37
  5. `motadata/src/main/java/com/mindarray/aiops/DependencyManager.java` — 35 ✓

### `soft_collision_shared_facade` (ambiguous)
- **query:** service facade delegation correlation
- **first relevant rank:** 1
- **top-3 anchor hit:** yes
- **noise dominance ratio (top-5):** 0.00
- **top-5 (path | score):**
  1. `motadata/src/main/java/com/mindarray/aiops/correlation/CorrelationService.java` — 60 ✓
  - **diagnostics (top-1):** {'path_lexical': 3, 'basename_lexical': 4, 'content': 3, 'path_prior': 13, 'subsystem_boost': 6, 'symbol_boost': 0, 'symbol_inventory_boost': 12, 'module_bias': 4, 'noise_penalty': 0, 'main_java_bonus': 7, 'noise_content_suppressed': 0, 'config_content_trimmed': 0, 'support_style_content_trimmed': 0, 'generic_facade_content_trimmed': 0, 'topic_focus_supporting_content_trimmed': 0, 'code_intent': 1, 'basename_specificity': 8, 'support_file_demotion': 0, 'owner_evidence_score': 20, 'direct_owner_alignment': 1, 'generic_integration_demotion': 0, 'ingestion_log_parser_demotion': 0, 'duplicate_incident_core_boost': 0, 'facade_cap_basename_or_symbol_owner_signal': 1, 'total': 60}
  - **note:** top-1 is an expected anchor.
  2. `motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java` — 49
  3. `motadata/src/main/java/com/mindarray/aiops/shared/ServiceFacade.java` — 42 ✓
  4. `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` — 39 ✓
  5. `motadata/src/main/java/com/mindarray/aiops/correlation/CorrelationUtils.java` — 39

## Aggregate metrics
- **top-1 accuracy:** 6/10 = 0.60
- **top-3 anchor hit rate:** 10/10 = 1.00
- **mean first relevant rank:** 1.40
- **mean noise dominance ratio (top-5):** 0.00

## Failure analysis
- No queries missed all anchors in top-k (first relevant rank defined for all).

## Caveat validation
- **Package-private methods:** extractor extended (regex); see unit test `test_package_private_methods_in_symbol_inventory`.
- **Module/path bias:** `RetrievalHit.diagnostics` exposes `module_bias` vs `symbol_inventory_boost` vs `content` for top-1 rows above.

## Adjustments made in this slice
- **Slice 3:** code/debug intent content gating on noise file classes, optional ``config`` content cap, ``retrieval_policy.v3`` main-Java lane bonus, ``db-files`` → ``generated_metrics_data`` classification, expanded diagnostics.
- **Slice 4:** ``retrieval_policy.v4`` — support-style Java basename content cap + demotion, basename/query CamelCase token overlap (specificity), diagnostics (``basename_specificity``, ``support_file_demotion``, ``support_style_content_trimmed``).
- **Slice 5:** ``retrieval_policy.v5`` — topic-gated generic eventbus handler content cap, supporting-class content cap when path lacks topic hints, ``*Util.java`` support suffix, duplicate-incident integration demotion + core AIOps boost, ingestion ``log/*Parser`` demotion; diagnostics (``owner_evidence_score``, ``facade_cap_basename_or_symbol_owner_signal``, ``topic_focus_supporting_content_trimmed``, ``ingestion_log_parser_demotion``, …).

## Verdict
**READY** for next slice (subject to real-checkout confirmation).

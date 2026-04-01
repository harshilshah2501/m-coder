# Product Authority + Code Understanding Layer (v1)

**Document Type:** Architecture Design Specification  
**Status:** Planning Phase — READY FOR IMPLEMENTATION  
**Version:** 1.1  
**Date:** 2026-03-31  
**Revision:** 2026-03-31 — Hardening pass complete (drift control, structural validation, multi-hop, entry points, guarded ranking, answer anchoring)

---

## Table of Contents

1. [Architecture](#1-architecture)
2. [Data Structures](#2-data-structures)
3. [Retrieval & Ranking Logic](#3-retrieval--ranking-logic)
4. [Integration Points](#4-integration-points)
5. [Execution Flow](#5-execution-flow)
6. [Evaluation Design](#6-evaluation-design)
7. [Implementation Plan](#7-implementation-plan)
8. [Example Outputs](#8-example-outputs)

---

## 1. Architecture

### 1.1 Design Philosophy

This system is NOT a semantic retrieval improvement. It is a **product-to-code ownership resolution layer** that behaves like a senior engineer who knows the codebase.

**Core Principle:** If the system returns semantically related files but misses the true owner, the system is **incorrect**. Ownership accuracy > recall.

### 1.2 Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONTEXT LAYER (WSL)                                  │
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────────┐│
│  │  LAYER 1            │  │  LAYER 2            │  │  LAYER 3             ││
│  │  Product Authority  │  │  Code Understanding │  │  Verification        ││
│  │  Registry           │  │  Index              │  │  Layer               ││
│  │                     │  │                     │  │                      ││
│  │  • Curated          │  │  • Derived          │  │  • Golden tests      ││
│  │  • Concept→Owner    │  │  • File→Symbols     │  │  • Expected owners   ││
│  │  • Aliases          │  │  • Call edges       │  │  • Forbidden dists.  ││
│  │  • Distractors      │  │  • Package groups   │  │  • Failure conditions││
│  └─────────┬───────────┘  └──────────┬──────────┘  └──────────┬───────────┘│
│            │                         │                        │            │
│            └─────────────┬───────────┴────────────────────────┘            │
│                          │                                                  │
│                          ▼                                                  │
│              ┌───────────────────────────────────────┐                     │
│              │       AUTHORITY RESOLVER               │                     │
│              │  • Concept extraction                  │                     │
│              │  • Registry lookup                     │                     │
│              │  • Structural expansion                │                     │
│              │  • Ranking fusion                      │                     │
│              └───────────────────┬───────────────────┘                     │
│                                  │                                          │
│                                  ▼                                          │
│              ┌───────────────────────────────────────┐                     │
│              │    EVIDENCE BUNDLE v1 (extended)      │                     │
│              │  + authority_resolution               │                     │
│              │  + owner_evidence                     │                     │
│              │  + structural_context                 │                     │
│              └───────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼ POST /v1/ask
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PLAN-GATE (GPU)                                    │
│                                                                             │
│  • Consumes extended evidence bundle                                        │
│  • Uses authority_resolution for answer generation                          │
│  • Generates answer-first responses (not exploration steps)                 │
│  • Falls back to plan-only when authority is weak                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Layer Responsibilities

| Layer | Role | Artifact | Ownership |
|-------|------|----------|-----------|
| **Product Authority** | Curated mapping of product concepts to code owners | `product_authority_registry.yaml` | Manual + validation |
| **Code Understanding** | Lightweight structural index derived from codebase | In-memory / file-based index | Automated extraction |
| **Verification** | Golden test suite for ownership accuracy | `product_goldens.yaml` | Manual + CI validation |

### 1.4 No Heavy Infrastructure

This design explicitly **avoids**:
- Neo4j / graph database
- ChromaDB / vector DB / embeddings
- Semantic similarity pipelines
- Model retraining / fine-tuning
- New services beyond existing Context Layer

---

## 2. Data Structures

### 2.1 Product Authority Registry Schema

**File:** `product_authority_registry.yaml`

```yaml
# Schema: product_authority_registry.v1.1
schema_version: "product_authority_registry.v1.1"
last_updated: "2026-03-31"
maintainer: "harshil@motadata.com"

# Concept definitions
concepts:

  incident_deduplication:
    # Primary owner - the single source of truth for this concept
    primary_owner:
      file: "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentDeduplicationProcessor.java"
      class: "IncidentDeduplicationProcessor"
      method: "processDeduplication"  # Optional: entry point method
      confidence: "high"  # high | medium | low
    
    # DRIFT CONTROL (v1.1): Verification metadata to prevent stale authority
    verification:
      last_verified_at: "2026-03-31T10:00:00Z"
      verification_source: "code_trace"  # code_trace | human | test
      verification_notes: "Verified via call graph trace from IncidentEventHandler"
      staleness_threshold_days: 90  # Authority requires re-verification after this
    
    # Alternative names users might use for this concept
    aliases:
      - "duplicate incident"
      - "incident dedup"
      - "dedup"
      - "duplicate detection"
      - "incident matching"
    
    # Secondary files that participate but are not the owner
    collaborators:
      - file: "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentCorrelationEngine.java"
        role: "orchestrator"
        relationship: "calls_primary"
      - file: "motadata/src/main/java/com/mindarray/aiops/query/IncidentQueryProcessor.java"
        role: "query_support"
        relationship: "data_provider"
    
    # Files that match keywords but are NOT the owner (false anchors)
    forbidden_distractors:
      - file: "motadata/src/main/java/com/mindarray/aiops/integration/ServiceNowIntegration.java"
        reason: "Uses incident term but handles external sync, not deduplication logic"
      - file: "motadata/src/main/java/com/mindarray/aiops/eventbus/handlers/IncidentEventHandler.java"
        reason: "Generic event routing, not deduplication implementation"
    
    # Domain knowledge notes for Plan-Gate
    notes:
      - "Deduplication uses similarity scoring with configurable thresholds"
      - "Primary algorithm is in processDeduplication() method"
      - "Uses DependencyManager for topology-aware grouping"
    
    # Control flow from entry to implementation
    control_flow:
      entry: "REST API or EventBus"
      path:
        - "IncidentEventHandler.handle()"
        - "IncidentCorrelationEngine.correlate()"
        - "IncidentDeduplicationProcessor.processDeduplication()"
      exit: "IncidentStore.persist()"
    
    # ENTRY POINTS (v1.1): Known system entry points that invoke this concept
    entry_points:
      - type: "eventbus_handler"
        file: "motadata/src/main/java/com/mindarray/aiops/eventbus/handlers/IncidentEventHandler.java"
        method: "handle"
        event_type: "INCIDENT_CREATED"
      - type: "rest_api"
        file: "motadata/src/main/java/com/mindarray/aiops/api/IncidentController.java"
        method: "createIncident"
        endpoint: "POST /api/v1/incidents"

  alert_correlation:
    primary_owner:
      file: "motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java"
      class: "AlertCorrelationEngine"
      confidence: "high"
    
    # DRIFT CONTROL (v1.1)
    verification:
      last_verified_at: "2026-03-31T10:00:00Z"
      verification_source: "code_trace"
      staleness_threshold_days: 90
    
    aliases:
      - "alert grouping"
      - "alert clustering"
      - "related alerts"
      - "correlation engine"
    
    collaborators:
      - file: "motadata/src/main/java/com/mindarray/aiops/correlation/CorrelationManager.java"
        role: "manager"
        relationship: "lifecycle_management"
      - file: "motadata/src/main/java/com/mindarray/aiops/topology/TopologyCache.java"
        role: "topology_provider"
        relationship: "context_enrichment"
    
    forbidden_distractors:
      - file: "motadata/src/main/java/com/mindarray/aiops/correlation/AvailabilityCorrelationEngine.java"
        reason: "Different correlation domain - availability, not alerts"
    
    notes:
      - "Uses topology graph for dependency-aware correlation"
      - "Supports both time-based and topology-based correlation"
    
    # ENTRY POINTS (v1.1)
    entry_points:
      - type: "eventbus_handler"
        file: "motadata/src/main/java/com/mindarray/aiops/eventbus/handlers/AlertEventHandler.java"
        method: "handle"
        event_type: "ALERT_CREATED"

  alert_escalation:
    primary_owner:
      file: "motadata/src/main/java/com/mindarray/aiops/alerting/AlertEscalationHandler.java"
      class: "AlertEscalationHandler"
      confidence: "high"
    
    # DRIFT CONTROL (v1.1)
    verification:
      last_verified_at: "2026-03-31T10:00:00Z"
      verification_source: "human"
      staleness_threshold_days: 90
    
    aliases:
      - "escalation"
      - "alert escalation"
      - "severity escalation"
      - "escalate alert"
    
    collaborators:
      - file: "motadata/src/main/java/com/mindarray/aiops/alerting/AlertNotificationService.java"
        role: "notification"
        relationship: "downstream_action"
    
    forbidden_distractors: []
    
    notes:
      - "Escalation rules are policy-driven from AlertPolicyEngine"

# Subsystem boundaries for structural expansion
subsystems:
  correlation:
    root_package: "com.mindarray.aiops.correlation"
    description: "All correlation-related logic including incidents, alerts, dependencies"
    
  alerting:
    root_package: "com.mindarray.aiops.alerting"
    description: "Alert lifecycle management, escalation, notification"
    
  topology:
    root_package: "com.mindarray.aiops.topology"
    description: "Topology graph, dependency tracking, anomaly detection"
    
  ingestion:
    root_package: "com.mindarray.aiops.ingestion"
    description: "Data ingestion pipelines, parsers, collectors"

# ENTRY POINTS REGISTRY (v1.1): System-wide entry point catalog
entry_points_catalog:
  eventbus_handlers:
    description: "EventBus message handlers - primary async entry points"
    pattern: "**/eventbus/handlers/*Handler.java"
    role: "entry"
    examples:
      - "IncidentEventHandler"
      - "AlertEventHandler"
      - "MetricEventHandler"
  
  rest_controllers:
    description: "REST API controllers - HTTP entry points"
    pattern: "**/api/*Controller.java"
    role: "entry"
    examples:
      - "IncidentController"
      - "AlertController"
  
  schedulers:
    description: "Scheduled/cron jobs - time-triggered entry points"
    pattern: "**/scheduler/*Scheduler.java"
    role: "entry"
    examples:
      - "AlertCleanupScheduler"
      - "MetricAggregationScheduler"
  
  message_consumers:
    description: "Kafka/queue consumers - external message entry points"
    pattern: "**/consumer/*Consumer.java"
    role: "entry"
    examples:
      - "MetricConsumer"
      - "EventConsumer"
```

### 2.2 Code Understanding Index Schema

**File:** In-memory structure (extends existing `WorkspaceFileIndex`)

```yaml
# Schema: code_understanding_index.v1.1 (upgraded for multi-hop and entry points)
schema_version: "code_understanding_index.v1.1"
workspace_identity_hash: "sha256:..."
canonical_root: "/path/to/workspace"

# File-level records (extends existing FileIndexEntry)
files:
  - relative_path: "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentDeduplicationProcessor.java"
    size_bytes: 15234
    mtime_ns: 1711929600000000000
    
    # Symbol-level detail (extends existing symbol_inventory)
    symbols:
      classes:
        - name: "IncidentDeduplicationProcessor"
          visibility: "public"
          extends: "AbstractProcessor"
          implements: ["DeduplicationStrategy"]
          line_start: 45
          line_end: 312
      
      methods:
        - name: "processDeduplication"
          visibility: "public"
          return_type: "DeduplicationResult"
          parameters: ["Incident", "List<Incident>"]
          line_start: 78
          line_end: 145
        - name: "calculateSimilarity"
          visibility: "private"
          return_type: "double"
          parameters: ["Incident", "Incident"]
          line_start: 150
          line_end: 180
    
    # Import relationships (lightweight)
    imports:
      - "com.mindarray.aiops.model.Incident"
      - "com.mindarray.aiops.query.IncidentQueryProcessor"
      - "com.mindarray.aiops.topology.DependencyManager"
    
    # MULTI-HOP CALL GRAPH (v1.1): Controlled 2-hop expansion with pruning
    calls:
      # Hop 1: Direct calls from this file
      hop_1:
        - target_class: "IncidentQueryProcessor"
          target_method: "findPotentialDuplicates"
          call_site_line: 95
          confidence: "high"
        - target_class: "DependencyManager"
          target_method: "getDependencies"
          call_site_line: 102
          confidence: "high"
      
      # Hop 2: Calls from hop_1 targets (pruned, same-package priority)
      hop_2:
        - source: "IncidentQueryProcessor.findPotentialDuplicates"
          target_class: "IncidentStore"
          target_method: "queryByTimeWindow"
          pruning_reason: "same_subsystem"
          included: true
        - source: "DependencyManager.getDependencies"
          target_class: "TopologyCache"
          target_method: "getGraph"
          pruning_reason: "authority_linked"
          included: true
        - source: "DependencyManager.getDependencies"
          target_class: "MetricsCollector"
          target_method: "recordLatency"
          pruning_reason: "utility_fanout"
          included: false  # Pruned: utility/observability, not domain logic
    
    # Package/module classification
    package: "com.mindarray.aiops.correlation"
    module: "correlation"
    subsystem: "correlation"

# Symbol → File reverse index (for fast lookup)
symbol_index:
  "IncidentDeduplicationProcessor":
    file: "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentDeduplicationProcessor.java"
    type: "class"
  "processDeduplication":
    file: "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentDeduplicationProcessor.java"
    type: "method"
    parent_class: "IncidentDeduplicationProcessor"

# Caller → Callee edges (bidirectional for navigation)
# MULTI-HOP (v1.1): Now supports 2-hop with pruning rules
call_graph:
  # Forward edges: who does X call? (2-hop with pruning)
  forward:
    "IncidentCorrelationEngine.correlate":
      hop_1:
        - "IncidentDeduplicationProcessor.processDeduplication"
        - "IncidentStore.save"
      hop_2:
        - source: "IncidentDeduplicationProcessor.processDeduplication"
          targets:
            - "IncidentQueryProcessor.findPotentialDuplicates"
            - "DependencyManager.getDependencies"
  
  # Reverse edges: who calls X? (2-hop with pruning)
  reverse:
    "IncidentDeduplicationProcessor.processDeduplication":
      hop_1:
        - "IncidentCorrelationEngine.correlate"
      hop_2:
        - source: "IncidentCorrelationEngine.correlate"
          targets:
            - "IncidentEventHandler.handle"  # Entry point!
  
  # PRUNING RULES (v1.1): Control fan-out explosion
  pruning_rules:
    max_hop_2_targets_per_source: 5
    priority_order:
      - "same_package"           # Highest: same package as primary owner
      - "known_collaborator"     # High: listed in registry collaborators
      - "authority_linked"       # High: linked to another authority concept
      - "same_subsystem"         # Medium: same subsystem
      - "entry_point"            # Medium: known entry point
      - "different_subsystem"    # Low: cross-subsystem (often pruned)
      - "utility_fanout"         # Lowest: utils, logging, metrics (excluded)
    excluded_patterns:
      - "*Logger*"
      - "*Metrics*"
      - "*Utils*"
      - "*Constants*"

# ENTRY POINTS INDEX (v1.1): Catalog of system entry points
entry_points_index:
  eventbus_handlers:
    - file: "motadata/src/main/java/com/mindarray/aiops/eventbus/handlers/IncidentEventHandler.java"
      class: "IncidentEventHandler"
      method: "handle"
      event_types: ["INCIDENT_CREATED", "INCIDENT_UPDATED"]
      invokes: ["IncidentCorrelationEngine.correlate"]
    - file: "motadata/src/main/java/com/mindarray/aiops/eventbus/handlers/AlertEventHandler.java"
      class: "AlertEventHandler"
      method: "handle"
      event_types: ["ALERT_CREATED"]
      invokes: ["AlertCorrelationEngine.correlate"]
  
  rest_controllers:
    - file: "motadata/src/main/java/com/mindarray/aiops/api/IncidentController.java"
      class: "IncidentController"
      endpoints:
        - method: "POST"
          path: "/api/v1/incidents"
          handler: "createIncident"
          invokes: ["IncidentService.create"]
  
  schedulers:
    - file: "motadata/src/main/java/com/mindarray/aiops/scheduler/AlertCleanupScheduler.java"
      class: "AlertCleanupScheduler"
      cron: "0 0 * * *"
      invokes: ["AlertStore.deleteOld"]

# Package grouping for structural expansion
package_groups:
  "com.mindarray.aiops.correlation":
    files:
      - "IncidentDeduplicationProcessor.java"
      - "IncidentCorrelationEngine.java"
      - "AlertCorrelationEngine.java"
      - "CorrelationManager.java"
    subsystem: "correlation"
```

### 2.3 Product Goldens Schema

**File:** `product_goldens.yaml`

```yaml
# Schema: product_goldens.v1.1 (extended with structural and drift failure modes)
schema_version: "product_goldens.v1.1"
last_updated: "2026-03-31"
policy_version: "retrieval_policy.v5"

goldens:
  - id: "GOLDEN-001"
    query: "Where is incident deduplication implemented?"
    intent: "code_location"
    
    # Expected primary owner - MUST be rank 1
    expected_primary_owner:
      file: "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentDeduplicationProcessor.java"
      class: "IncidentDeduplicationProcessor"
      confidence_required: "high"
    
    # Acceptable supporting files (may appear in top-k)
    acceptable_supporting:
      - file: "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentCorrelationEngine.java"
        max_rank: 3
        role: "orchestrator"
      - file: "motadata/src/main/java/com/mindarray/aiops/query/IncidentQueryProcessor.java"
        max_rank: 5
        role: "query_support"
    
    # Files that MUST NOT rank in top-3
    forbidden_distractors:
      - file: "motadata/src/main/java/com/mindarray/aiops/integration/ServiceNowIntegration.java"
        reason: "External integration, not dedup logic"
      - file: "motadata/src/main/java/com/mindarray/aiops/eventbus/handlers/IncidentEventHandler.java"
        reason: "Generic routing"
      - file: "motadata/src/main/java/com/mindarray/aiops/correlation/AvailabilityCorrelationEngine.java"
        reason: "Different correlation domain"
    
    # Failure conditions
    failure_conditions:
      - condition: "primary_owner_not_rank_1"
        severity: "critical"
        description: "Primary owner must be rank 1"
      - condition: "distractor_in_top_3"
        severity: "critical"
        description: "Forbidden distractor appeared in top 3"
      - condition: "no_authority_match"
        severity: "warning"
        description: "Query could not be resolved to any authority concept"
    
    # Expected evidence structure
    expected_evidence:
      control_flow_present: true
      notes_present: true
      collaborators_identified: true

  - id: "GOLDEN-002"
    query: "How are alerts correlated or escalated?"
    intent: "code_understanding"
    
    # Multiple owners expected (compound query)
    expected_primary_owners:
      - file: "motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java"
        class: "AlertCorrelationEngine"
        concept: "alert_correlation"
      - file: "motadata/src/main/java/com/mindarray/aiops/alerting/AlertEscalationHandler.java"
        class: "AlertEscalationHandler"
        concept: "alert_escalation"
    
    acceptable_supporting:
      - file: "motadata/src/main/java/com/mindarray/aiops/topology/TopologyCache.java"
        max_rank: 5
        role: "context_provider"
    
    forbidden_distractors:
      - file: "motadata/src/main/java/com/mindarray/aiops/correlation/AvailabilityCorrelationEngine.java"
        reason: "Different correlation domain"
    
    failure_conditions:
      - condition: "both_owners_not_in_top_3"
        severity: "critical"
        description: "At least one owner for each concept must be in top 3"

  - id: "GOLDEN-003"
    query: "Debug: duplicate incidents are being created"
    intent: "debug"
    
    expected_primary_owner:
      file: "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentDeduplicationProcessor.java"
      class: "IncidentDeduplicationProcessor"
      confidence_required: "high"
    
    # Debug queries should include method-level detail
    expected_evidence:
      method_entry_point: "processDeduplication"
      control_flow_present: true
      caller_callee_present: true
    
    failure_conditions:
      - condition: "no_method_level_detail"
        severity: "warning"
        description: "Debug intent should include method-level resolution"
    
    # ENTRY POINT TRACING (v1.1): Debug queries should trace from entry
    expected_evidence:
      entry_point_traced: true
      entry_to_owner_path_present: true

  # GOLDEN-004 (v1.1): Stale authority detection test
  - id: "GOLDEN-004"
    query: "Where is metric aggregation implemented?"
    intent: "code_location"
    
    # Intentionally stale authority for testing
    expected_primary_owner:
      file: "motadata/src/main/java/com/mindarray/aiops/metrics/MetricAggregator.java"
      class: "MetricAggregator"
      confidence_required: "high"
    
    # Test expects structural validation to catch staleness
    expected_behavior:
      authority_is_stale: true
      structural_validation_should_fail: true
      expected_fallback: "reduced_boost"
    
    failure_conditions:
      - condition: "stale_authority_error"
        severity: "critical"
        description: "Authority file no longer exists or class renamed"
      - condition: "full_boost_applied_to_stale"
        severity: "critical"
        description: "Full +100 boost applied without structural validation"

  # GOLDEN-005 (v1.1): Entry point tracing test
  - id: "GOLDEN-005"
    query: "Trace: how does an incident get created?"
    intent: "trace"
    
    expected_trace:
      entry_point:
        type: "rest_api"
        file: "motadata/src/main/java/com/mindarray/aiops/api/IncidentController.java"
      path:
        - "IncidentController.createIncident()"
        - "IncidentService.create()"
        - "IncidentCorrelationEngine.correlate()"
        - "IncidentDeduplicationProcessor.processDeduplication()"
    
    failure_conditions:
      - condition: "missing_entry_point_trace"
        severity: "critical"
        description: "Trace query did not identify entry point"
      - condition: "incomplete_path"
        severity: "warning"
        description: "Path from entry to owner is incomplete"

  # GOLDEN-006 (v1.1): Shallow path error test
  - id: "GOLDEN-006"
    query: "How does topology affect correlation?"
    intent: "code_understanding"
    
    expected_primary_owner:
      file: "motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java"
      class: "AlertCorrelationEngine"
    
    # Test expects structural context, not just lexical matches
    expected_evidence:
      structural_context_required: true
      must_include_callee: "TopologyCache"
      must_show_relationship: "AlertCorrelationEngine → TopologyCache.getGraph()"
    
    failure_conditions:
      - condition: "shallow_path_error"
        severity: "warning"
        description: "Only lexical matches found, no structural relationships"

# Aggregate metrics requirements
metrics_requirements:
  owner_at_1:
    minimum: 0.90
    target: 0.95
    description: "Primary owner ranked #1"
  
  owner_at_3:
    minimum: 0.95
    target: 1.00
    description: "Primary owner in top 3"
  
  distractor_error_rate:
    maximum: 0.05
    target: 0.00
    description: "Forbidden distractor in top 3"
  
  authority_hit_rate:
    minimum: 0.80
    target: 0.90
    description: "Query resolved to authority concept"
  
  # NEW METRICS (v1.1): Structural and drift metrics
  authority_freshness_score:
    minimum: 0.85
    target: 0.95
    description: "Percentage of authority entries verified within staleness threshold"
  
  structural_validation_pass_rate:
    minimum: 0.90
    target: 0.98
    description: "Percentage of authority lookups that pass pre-boost validation"
  
  multi_hop_trace_accuracy:
    minimum: 0.80
    target: 0.90
    description: "Accuracy of 2-hop call graph traces (validated against known paths)"
  
  entry_point_identification_rate:
    minimum: 0.75
    target: 0.85
    description: "Percentage of queries where entry point was correctly identified"
```

---

## 3. Retrieval & Ranking Logic

### 3.1 Scoring Formula

The ranking score combines existing lexical scoring with authority-aware components:

```
total_score = lexical_score + authority_score + structural_score - distractor_penalty

where:
  lexical_score = existing L5 retrieval score (path + basename + content + policy)
  
  authority_score = 
    owner_boost          (if file is primary_owner for matched concept)
    + collaborator_boost (if file is collaborator for matched concept)
    + alias_match_boost  (if query matches concept aliases)
  
  structural_score =
    caller_boost         (if file is caller of primary_owner)
    + callee_boost       (if file is callee of primary_owner)
    + package_affinity   (if file is in same package as primary_owner)
  
  distractor_penalty =
    distractor_penalty   (if file is in forbidden_distractors list)
```

### 3.2 Authority Sanity Check (Pre-Boost Validation) — v1.1

**Critical Addition:** Before applying any authority boost, the system MUST validate that the authority is not stale.

```yaml
# AUTHORITY SANITY CHECK (v1.1)
# Runs BEFORE authority_score is computed
pre_boost_validation:
  description: "Structural validation to prevent boosting stale/invalid authority"
  
  checks:
    - id: "file_exists"
      description: "Primary owner file must exist in workspace"
      action: "Check index for primary_owner.file"
      on_failure: "mark_stale"
    
    - id: "class_exists"
      description: "Primary owner class must exist in file"
      action: "Check symbol_index for primary_owner.class"
      on_failure: "mark_stale"
    
    - id: "method_exists"
      description: "Primary owner method must exist (if specified)"
      action: "Check symbol_index for primary_owner.method"
      on_failure: "downgrade_confidence"
    
    - id: "is_referenced"
      description: "File must be imported or called by at least one other file"
      action: "Check call_graph.reverse for any caller"
      on_failure: "mark_stale_candidate"
    
    - id: "freshness_check"
      description: "Authority verification must be within staleness threshold"
      action: "Compare last_verified_at to current date"
      on_failure: "require_structural_validation"
  
  outcomes:
    all_pass:
      authority_status: "validated"
      boost_allowed: "full"  # +100
    
    file_or_class_missing:
      authority_status: "stale"
      boost_allowed: "none"  # 0
      action: "Log stale_authority_error, fall back to lexical"
    
    method_missing_or_not_referenced:
      authority_status: "stale_candidate"
      boost_allowed: "partial"  # +40
      action: "Proceed with reduced confidence"
    
    freshness_failed:
      authority_status: "unverified"
      boost_allowed: "conditional"  # +100 only if structural checks pass
      action: "Require structural validation before full boost"
```

### 3.3 Authority Boost Values

```yaml
# Authority scoring weights (scaled to existing policy_score_scale = 2)
authority_weights:
  # Primary owner boost - CONDITIONAL on validation (v1.1)
  owner_boost_full: 100      # Only when authority_status == "validated"
  owner_boost_partial: 40    # When authority_status == "stale_candidate" or "unverified"
  owner_boost_none: 0        # When authority_status == "stale"
  
  # Concept match boosters
  exact_concept_match: 40      # Query maps directly to concept
  alias_concept_match: 30      # Query matches alias
  partial_concept_match: 15    # Partial token overlap with concept
  
  # Collaborator boosts (supporting but not primary)
  collaborator_direct: 25      # Listed as collaborator
  collaborator_same_package: 10 # Same package as primary owner
  
  # Structural proximity
  caller_of_owner: 15          # Calls primary owner method
  callee_of_owner: 12          # Called by primary owner method
  same_module: 8               # Same module directory
  
  # Distractor penalties (negative, must suppress)
  distractor_explicit: -80     # Explicitly listed as forbidden
  distractor_eventbus_generic: -40  # Generic eventbus handlers
  distractor_integration: -30  # Integration files when query is not integration-focused

# Hard rules
hard_rules:
  owner_must_rank_1: true
  owner_must_in_top_3: true
  distractor_max_rank: 4  # Distractors cannot be higher than rank 4
  weak_authority_signal_threshold: 0.6  # Below this, add uncertainty flag

# AUTHORITY OVERCONFIDENCE GUARD (v1.1)
# Prevents full boost without structural backing
overconfidence_guard:
  description: "Safety mechanism to prevent blind authority trust"
  
  full_boost_requires:
    - "authority.confidence == 'high'"
    - "OR pre_boost_validation.all_checks_pass == true"
  
  when_not_met:
    boost_applied: "partial"  # +40 instead of +100
    ranking_behavior: "allow_lexical_competition"
    explanation: "Authority exists but not structurally validated; lexical signals may compete"
  
  logging:
    event: "authority_overconfidence_guard_triggered"
    fields:
      - "concept_id"
      - "primary_owner.file"
      - "failed_checks"
      - "applied_boost"
```

### 3.3.1 Authority Trust Policy (v1.1)

**Explicit Policy:** Full authority boost (+100) is ONLY allowed when ALL of the following conditions are met:

```yaml
# AUTHORITY TRUST POLICY (v1.1)
# Defines when authority can be fully trusted
authority_trust_policy:
  full_boost_conditions:
    all_required:
      - "confidence == 'high'"
      - "authority_status == 'validated'"
      - "NOT stale (freshness check passed)"
      - "structural_validation.all_critical_checks_pass == true"
    
    critical_checks:
      - "file_exists"      # Primary owner file must exist
      - "class_exists"     # Primary owner class must exist in file
    
    optional_checks:
      - "method_exists"    # Downgrades to partial on failure
      - "is_referenced"    # Downgrades to stale_candidate on failure
  
  partial_boost_conditions:
    any_of:
      - "confidence == 'medium'"
      - "authority_status == 'stale_candidate'"
      - "authority_status == 'unverified'"
      - "freshness check failed but structural checks passed"
    
    boost_value: 40
    ranking_behavior: "allow_lexical_competition"
  
  no_boost_conditions:
    any_of:
      - "confidence == 'low'"
      - "authority_status == 'stale'"
      - "file_exists check failed"
      - "class_exists check failed"
    
    boost_value: 0
    ranking_behavior: "lexical_only"
    logging: "stale_authority_error"
  
  # Explicit prohibition
  prohibited:
    - "Full boost (+100) when authority_status != 'validated'"
    - "Full boost (+100) when freshness check failed AND no structural validation"
    - "Forced rank-1 when authority_status == 'stale_candidate'"
    - "Suppressing lexical competition when confidence < 'high'"
```

### 3.5 Distractor Penalty Rules

```yaml
distractor_rules:
  # Explicit forbidden list (from registry)
  - condition: "file in concept.forbidden_distractors"
    penalty: distractor_explicit
    reason: "Explicitly marked as distractor for matched concept"
  
  # Generic patterns (structural detection)
  - condition: "basename matches '*EventHandler.java' AND path contains '/eventbus/'"
    penalty: distractor_eventbus_generic
    applies_when: "query does not contain 'eventbus' or 'handler'"
    reason: "Generic event routing, not implementation"
  
  - condition: "basename matches '*Integration.java' AND path contains '/integration/'"
    penalty: distractor_integration
    applies_when: "query does not contain 'integration' or 'sync'"
    reason: "External integration, not core logic"
  
  - condition: "basename matches '*Constants.java' OR '*Utils.java'"
    penalty: -20
    applies_when: "query is code_location or debug intent"
    reason: "Support file, not behavioral owner"
```

### 3.6 Structural Proximity Scoring

```yaml
structural_proximity:
  # MULTI-HOP RELATIONSHIPS (v1.1): Upgraded from 1-hop to controlled 2-hop
  caller_relationship:
    description: "File A calls methods in primary_owner"
    hop_1:
      boost: 15  # Direct caller
    hop_2:
      boost: 8   # Caller of caller (reduced)
      pruning: "apply_pruning_rules"
  
  callee_relationship:
    description: "Primary owner calls methods in file B"
    hop_1:
      boost: 12  # Direct callee
    hop_2:
      boost: 6   # Callee of callee (reduced)
      pruning: "apply_pruning_rules"
  
  # Package affinity
  package_affinity:
    same_package: 10
    same_subsystem: 5
    different_subsystem: 0
  
  # Import relationship
  import_relationship:
    direct_import: 5
    transitive_import: 3  # Now tracked in v1.1 (1-hop transitive)
  
  # ENTRY POINT PROXIMITY (v1.1)
  entry_point_relationship:
    description: "File is a known entry point that leads to primary_owner"
    direct_entry: 20      # Entry point directly invokes owner
    indirect_entry: 10    # Entry point → orchestrator → owner
    max_hops_from_entry: 2

# MULTI-HOP EXPANSION RULES (v1.1)
multi_hop_expansion:
  enabled: true
  max_hops: 2
  
  pruning_rules:
    # Avoid fan-out explosion
    max_targets_per_hop: 5
    
    # Priority ordering for which hop-2 targets to include
    include_priority:
      - same_package_as_owner     # Highest priority
      - known_collaborator        # Listed in registry
      - authority_linked          # Linked to another concept
      - entry_point              # Known system entry
    
    exclude_always:
      - "*Logger*"
      - "*Metrics*"
      - "*Utils*"
      - "*Constants*"
      - "*Exception*"
    
    # Stop expansion if target is in different subsystem AND not authority-linked
    cross_subsystem_policy: "exclude_unless_authority_linked"
  
  # Boost decay per hop
  decay_factor: 0.5  # hop_2 boost = hop_1 boost * 0.5
```

---

## 4. Integration Points

### 4.1 Context Layer Integration

**Location:** `runtime/layer5/` - new module `runtime/layer5/authority/`

```
runtime/layer5/authority/
├── __init__.py
├── registry.py          # Load and parse product_authority_registry.yaml
├── resolver.py          # Concept extraction and authority lookup
├── code_index.py        # Extended code understanding index
├── ranking.py           # Authority-aware ranking fusion
└── config.py            # Authority layer configuration
```

#### 4.1.1 Integration with Existing Retrieval

**File:** `runtime/layer5/retrieval/lexical.py` - minimal modification

```python
# At the end of retrieve_lexical(), before returning:

def retrieve_lexical(...) -> RetrievalResult:
    # ... existing lexical retrieval logic ...
    
    # NEW: Authority resolution pass (optional, controlled by config)
    if cfg.enable_authority_resolution:
        from runtime.layer5.authority.resolver import resolve_authority
        from runtime.layer5.authority.ranking import apply_authority_ranking
        
        # Step 1: Extract concepts from query
        authority_resolution = resolve_authority(query, tokens, index)
        
        # Step 2: Re-rank with authority signals
        if authority_resolution.matched_concepts:
            scored = apply_authority_ranking(
                scored,
                authority_resolution,
                code_index,  # Extended index with symbols/calls
                cfg,
            )
            scored.sort(key=lambda h: (-h.score, h.relative_path))
    
    # Continue with existing core correction, symbol correction, etc.
    ...
```

#### 4.1.2 Evidence Bundle Extension

**File:** `runtime/layer5/evidence/evidence_bundle.v1.schema.json` - additive extension

```json
{
  "properties": {
    "authority_resolution": {
      "type": "object",
      "description": "Optional authority layer resolution",
      "properties": {
        "matched_concepts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "concept_id": { "type": "string" },
              "match_type": { "enum": ["exact", "alias", "partial"] },
              "confidence": { "type": "number" }
            }
          }
        },
        "primary_owner": {
          "type": "object",
          "properties": {
            "file": { "type": "string" },
            "class": { "type": "string" },
            "method": { "type": "string" },
            "confidence": { "enum": ["high", "medium", "weak"] }
          }
        },
        "control_flow": {
          "type": "array",
          "items": { "type": "string" }
        },
        "notes": {
          "type": "array",
          "items": { "type": "string" }
        },
        "authority_confidence": {
          "type": "string",
          "enum": ["high", "medium", "weak", "none"]
        },
        "authority_status": {
          "type": "string",
          "enum": ["validated", "stale", "stale_candidate", "unverified"],
          "description": "v1.1: Result of pre-boost validation"
        },
        "validation_details": {
          "type": "object",
          "description": "v1.1: Details of pre-boost validation checks",
          "properties": {
            "file_exists": { "type": "boolean" },
            "class_exists": { "type": "boolean" },
            "method_exists": { "type": "boolean" },
            "is_referenced": { "type": "boolean" },
            "freshness_ok": { "type": "boolean" },
            "days_since_verification": { "type": "integer" }
          }
        },
        "entry_trace": {
          "type": "object",
          "description": "v1.1: Entry point to owner trace",
          "properties": {
            "entry_point": {
              "type": "object",
              "properties": {
                "type": { "type": "string" },
                "file": { "type": "string" },
                "method": { "type": "string" }
              }
            },
            "path": {
              "type": "array",
              "items": { "type": "string" }
            }
          }
        }
      }
    },
    "owner_evidence": {
      "type": "array",
      "description": "Evidence entries marked as owner candidates",
      "items": {
        "$ref": "#/definitions/evidence_entry"
      }
    },
    "structural_context": {
      "type": "object",
      "description": "v1.1: Multi-hop structural context",
      "properties": {
        "callers_hop_1": { "type": "array", "items": { "type": "string" } },
        "callers_hop_2": { "type": "array", "items": { "type": "string" } },
        "callees_hop_1": { "type": "array", "items": { "type": "string" } },
        "callees_hop_2": { "type": "array", "items": { "type": "string" } },
        "entry_points": { "type": "array", "items": { "type": "string" } },
        "hop_2_pruned_count": { "type": "integer" }
      }
    }
  }
}
```

### 4.2 Plan-Gate Consumption

**File:** `runtime/ask_service/v1_ingest.py` - minimal modification

```python
def handle_ask_v1_request(ask_request: dict) -> dict:
    # ... existing validation and evidence extraction ...
    
    # NEW: Extract authority resolution if present
    authority_resolution = evidence_bundle.get("authority_resolution")
    
    if authority_resolution:
        # Use authority signals for answer-first behavior
        primary_owner = authority_resolution.get("primary_owner")
        control_flow = authority_resolution.get("control_flow", [])
        notes = authority_resolution.get("notes", [])
        authority_confidence = authority_resolution.get("authority_confidence", "none")
        authority_status = authority_resolution.get("authority_status", "unknown")  # v1.1
        
        # Pass to planner for answer-first generation
        planner_context = {
            "primary_owner": primary_owner,
            "control_flow": control_flow,
            "notes": notes,
            "authority_confidence": authority_confidence,
            "authority_status": authority_status,  # v1.1: validated/stale/stale_candidate
        }
    else:
        planner_context = {}
    
    # ... continue with existing plan/explain_debug logic ...
    # Planner receives authority context for answer-first behavior
    plan_summary = planner.plan(
        query=query,
        bundle=bundle,
        authority_context=planner_context,  # NEW parameter
    )
```

### 4.2.1 Answer Synthesis Guardrail (v1.1)

**Critical Rule:** When authority resolution provides a primary owner, the final answer MUST anchor to it.

```yaml
# ANSWER SYNTHESIS GUARDRAIL (v1.1)
# Enforced in Plan-Gate response generation
answer_guardrail:
  description: "Ensures answer anchors to authority when available"
  
  when_primary_owner_exists:
    required:
      - "Answer MUST reference primary_owner.file"
      - "Answer MUST reference primary_owner.class"
      - "If method specified, answer SHOULD reference primary_owner.method"
      - "Answer MUST explain role of primary owner in system"
    
    disallowed:
      - "Generic exploration steps without anchoring to owner"
      - "Alternative candidates presented as equal options"
      - "Hedge language like 'might be in' when confidence is high"
    
    alternative_candidates:
      allowed_when: "Explicitly marked as collaborators or secondary"
      presentation: "After primary owner, clearly labeled as supporting"
  
  when_authority_status_is_stale:
    required:
      - "Explicitly state uncertainty: 'Authority may be outdated'"
      - "Include structural evidence for why file was selected"
      - "Recommend verification"
    
    example: |
      "Based on registry, this was implemented in `{class}`, but the authority 
      has not been recently verified. The file still exists and is referenced 
      by `{caller}`. Recommend confirming this is still the current implementation."
  
  when_authority_confidence_is_weak:
    required:
      - "Use uncertainty language: 'Likely in' not 'Is in'"
      - "Present lexical evidence alongside authority"
      - "Do not suppress alternative candidates"
  
  validation:
    check: "Response must contain primary_owner.class if authority_confidence >= medium"
    on_violation: "Log answer_anchor_violation, escalate for review"
```

### 4.3 New Fields Added to Evidence Bundle

| Field | Type | Location | Description |
|-------|------|----------|-------------|
| `authority_resolution` | object | Evidence bundle top-level | Authority resolution result |
| `authority_resolution.matched_concepts` | array | Inside authority_resolution | Concepts matched from query |
| `authority_resolution.primary_owner` | object | Inside authority_resolution | Primary owner file/class/method |
| `authority_resolution.control_flow` | array | Inside authority_resolution | Entry → implementation path |
| `authority_resolution.notes` | array | Inside authority_resolution | Domain knowledge notes |
| `authority_resolution.authority_confidence` | string | Inside authority_resolution | high/medium/weak/none |
| `owner_evidence` | array | Evidence bundle top-level | Subset of entries marked as owners |

**New Fields (v1.1):**

| Field | Type | Location | Description |
|-------|------|----------|-------------|
| `authority_resolution.authority_status` | string | Inside authority_resolution | validated/stale/stale_candidate/unverified |
| `authority_resolution.validation_details` | object | Inside authority_resolution | Pre-boost validation check results |
| `authority_resolution.entry_trace` | object | Inside authority_resolution | Entry point → owner trace path |
| `structural_context` | object | Evidence bundle top-level | Multi-hop callers, callees, entry points |
| `structural_context.callers_hop_1` | array | Inside structural_context | Direct callers of owner |
| `structural_context.callers_hop_2` | array | Inside structural_context | Callers of callers (pruned) |
| `structural_context.entry_points` | array | Inside structural_context | Known entry points leading to owner |
| `structural_context.hop_2_pruned_count` | integer | Inside structural_context | Number of hop-2 targets pruned |

### 4.4 Ask / Debug / Plan Behavior Changes

| Mode | Current Behavior | With Authority Layer |
|------|------------------|---------------------|
| **Ask** | Returns top-k files with snippets | Returns primary owner + control flow + notes |
| **Debug** | Generic exploration steps | Points to specific method entry point |
| **Plan** | List files to explore | Answer-first: "Implementation is in X.method()" |

---

## 5. Execution Flow

### 5.1 Step-by-Step Pipeline

```
QUERY INPUT
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: QUERY CLASSIFICATION                                                │
│                                                                             │
│ Input:  Raw query string                                                    │
│ Output: intent_type, normalized_tokens, code_debug_intent                   │
│                                                                             │
│ Actions:                                                                    │
│   1. Normalize query → tokens (existing normalize_query)                    │
│   2. Classify intent: code_location | code_understanding | debug | general │
│   3. Extract symbol tokens (existing classify_intent)                       │
│   4. Detect code/debug intent (existing infer_code_debug_intent)            │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: AUTHORITY RESOLUTION                                                │
│                                                                             │
│ Input:  Query tokens, intent_type                                           │
│ Output: AuthorityResolution (matched_concepts, primary_owner, confidence)   │
│                                                                             │
│ Actions:                                                                    │
│   1. Load product_authority_registry.yaml (cached)                          │
│   2. Match query tokens against concept names and aliases                   │
│   3. Score matches: exact > alias > partial                                 │
│   4. Select best matching concept(s)                                        │
│   5. Extract primary_owner, collaborators, forbidden_distractors            │
│   6. Compute authority_confidence based on match quality                    │
│                                                                             │
│ Match Algorithm:                                                            │
│   - Exact: query contains concept_id verbatim → confidence = high           │
│   - Alias: query matches any alias → confidence = high                      │
│   - Partial: ≥50% token overlap with concept_id → confidence = medium       │
│   - None: no overlap → confidence = none                                    │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2.5: AUTHORITY SANITY CHECK (v1.1 — Pre-Boost Validation)              │
│                                                                             │
│ Input:  AuthorityResolution, CodeUnderstandingIndex                         │
│ Output: AuthorityResolution with authority_status field                     │
│                                                                             │
│ Actions:                                                                    │
│   1. Check file_exists: primary_owner.file in index?                        │
│   2. Check class_exists: primary_owner.class in symbol_index?               │
│   3. Check method_exists: primary_owner.method in symbol_index? (if set)    │
│   4. Check is_referenced: file has callers in call_graph.reverse?           │
│   5. Check freshness: last_verified_at within staleness_threshold?          │
│                                                                             │
│ Outcomes:                                                                   │
│   - All pass → authority_status = "validated", boost = full (+100)          │
│   - File/class missing → authority_status = "stale", boost = none (0)       │
│   - Method missing or not ref'd → authority_status = "stale_candidate",     │
│                                    boost = partial (+40)                    │
│   - Freshness failed → require structural validation for full boost         │
│                                                                             │
│ On Stale:                                                                   │
│   - Log stale_authority_error                                               │
│   - Continue with lexical-only ranking                                      │
│   - Mark authority_resolution.requires_verification = true                  │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: STRUCTURAL EXPANSION (v1.1 — Multi-Hop with Entry Points)           │
│                                                                             │
│ Input:  AuthorityResolution (validated), CodeUnderstandingIndex             │
│ Output: StructuralContext (callers, callees, package_peers, entry_points)   │
│                                                                             │
│ Actions (only if authority_status != "stale"):                              │
│   1. Look up primary_owner file in code_understanding_index                 │
│   2. Extract HOP 1 callers (direct callers from call_graph.reverse)         │
│   3. Extract HOP 1 callees (direct callees from call_graph.forward)         │
│   4. Apply pruning rules for HOP 2 expansion:                               │
│      - Include: same_package, known_collaborator, authority_linked          │
│      - Exclude: utility_fanout, different_subsystem (unless authority link) │
│      - Max 5 targets per source                                             │
│   5. Extract HOP 2 callers/callees with decay factor (0.5x boost)           │
│   6. Identify entry points that lead to primary_owner:                      │
│      - Check entry_points_index for paths to owner                          │
│      - Include entry → orchestrator → owner traces                          │
│   7. Identify package peers (same package, exclude noise)                   │
│   8. Mark all with appropriate boosts and hop distance                      │
│                                                                             │
│ Skip conditions:                                                            │
│   - authority_status == "stale" → skip structural expansion                 │
│   - authority_confidence == "none" → skip structural expansion              │
│   - primary_owner file not in index → skip (already caught in Step 2.5)     │
│                                                                             │
│ Entry Point Tracing (v1.1):                                                 │
│   - If query intent is "trace" or "debug":                                  │
│     → Prioritize finding entry point that leads to owner                    │
│     → Build entry → orchestrator → owner path                               │
│     → Include in structural_context.entry_trace                             │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: LEXICAL RETRIEVAL (Existing)                                        │
│                                                                             │
│ Input:  WorkspaceFileIndex, query tokens, config                            │
│ Output: List[RetrievalHit] with lexical scores                              │
│                                                                             │
│ Actions:                                                                    │
│   - Run existing retrieve_lexical() unchanged                               │
│   - Apply existing policy biases (path_prior, symbol_boost, etc.)           │
│   - Apply existing code_intent content gating                               │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: AUTHORITY-AWARE RANKING FUSION                                      │
│                                                                             │
│ Input:  List[RetrievalHit], AuthorityResolution, StructuralContext          │
│ Output: Re-ranked List[RetrievalHit] with authority signals                 │
│                                                                             │
│ Actions:                                                                    │
│   1. For each hit, compute authority_score (v1.1 — conditional boost):      │
│      - If hit.file == primary_owner.file:                                   │
│        → If authority_status == "validated": +owner_boost_full (100)        │
│        → If authority_status == "stale_candidate": +owner_boost_partial (40)│
│        → If authority_status == "stale": +0 (no boost)                      │
│      - If hit.file in collaborators: +collaborator_boost (25)               │
│      - If hit.file in callers (hop 1): +caller_boost (15)                   │
│      - If hit.file in callers (hop 2): +caller_boost * 0.5 (8)              │
│      - If hit.file in callees (hop 1): +callee_boost (12)                   │
│      - If hit.file in callees (hop 2): +callee_boost * 0.5 (6)              │
│      - If hit.file is entry_point leading to owner: +entry_point_boost (20) │
│      - If hit.file in forbidden_distractors: +distractor_penalty (-80)      │
│   2. Update hit.score = lexical_score + authority_score                     │
│   3. Re-sort by new score (descending)                                      │
│   4. Apply hard rules (with overconfidence guard):                          │
│      - If authority_status == "validated" AND not rank 1 → swap to rank 1   │
│      - If authority_status != "validated" → allow lexical competition       │
│      - If distractor in top 3 → demote below rank 3                         │
│                                                                             │
│ Hard Rule Enforcement (v1.1):                                               │
│   - Primary owner MUST be rank 1 ONLY if authority_status == "validated"    │
│   - If authority_status == "stale_candidate": owner SHOULD be in top 3      │
│   - Distractors MUST NOT be in top 3 regardless of score                    │
│   - Overconfidence guard: no forced rank 1 without structural validation    │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: EVIDENCE BUNDLE CONSTRUCTION                                        │
│                                                                             │
│ Input:  Re-ranked hits, AuthorityResolution, StructuralContext              │
│ Output: EvidenceBundle v1 (extended with authority fields)                  │
│                                                                             │
│ Actions:                                                                    │
│   1. Run existing build_evidence_bundle() for entries                       │
│   2. Add authority_resolution object:                                       │
│      - matched_concepts                                                     │
│      - primary_owner (file, class, method, confidence)                      │
│      - control_flow from registry                                           │
│      - notes from registry                                                  │
│      - authority_confidence                                                 │
│   3. Mark owner entries in owner_evidence array                             │
│   4. Include structural_context in diagnostics (if enabled)                 │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 7: PLAN-GATE CONSUMPTION                                               │
│                                                                             │
│ Input:  EvidenceBundle v1 (extended)                                        │
│ Output: Plan-only response with answer-first behavior                       │
│                                                                             │
│ Actions:                                                                    │
│   1. Validate evidence bundle (existing)                                    │
│   2. Extract authority_resolution                                           │
│   3. Generate response:                                                     │
│      - If authority_confidence == high/medium:                              │
│        → Answer-first: "Implemented in {class}.{method}"                    │
│        → Include control_flow path                                          │
│        → Include notes                                                      │
│      - If authority_confidence == weak:                                     │
│        → Include uncertainty: "Likely in {file}, but verify"                │
│      - If authority_confidence == none:                                     │
│        → Fall back to exploration steps (existing behavior)                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Decision Tree

```
Query received
    │
    ├── Normalize and classify intent
    │       │
    │       ├── code_location / code_understanding / debug
    │       │       │
    │       │       └── Attempt authority resolution
    │       │               │
    │       │               ├── Match found (high/medium confidence)
    │       │               │       │
    │       │               │       ├── Expand structural context
    │       │               │       │
    │       │               │       ├── Apply authority ranking
    │       │               │       │
    │       │               │       └── Generate answer-first response
    │       │               │
    │       │               └── No match (weak/none confidence)
    │       │                       │
    │       │                       └── Fall back to lexical-only ranking
    │       │
    │       └── general intent
    │               │
    │               └── Skip authority resolution
    │                       │
    │                       └── Use lexical-only ranking (existing)
    │
    └── Build evidence bundle
            │
            └── Send to Plan-Gate
```

---

## 6. Evaluation Design

### 6.1 Metrics Definitions

| Metric | Formula | Target | Minimum |
|--------|---------|--------|---------|
| **owner@1** | (# queries where primary owner is rank 1) / (total queries with validated authority) | 0.95 | 0.90 |
| **owner@3** | (# queries where primary owner is in top 3) / (total queries with known owner) | 1.00 | 0.95 |
| **distractor_error_rate** | (# queries where distractor in top 3) / (total queries with forbidden distractors) | 0.00 | 0.05 |
| **authority_hit_rate** | (# queries resolved to authority concept) / (total queries) | 0.90 | 0.80 |
| **mean_owner_rank** | average rank of primary owner across all queries | 1.05 | 1.50 |
| **weak_authority_rate** | (# queries with weak/none confidence) / (total queries) | 0.10 | 0.20 |

**New Metrics (v1.1):**

| Metric | Formula | Target | Minimum |
|--------|---------|--------|---------|
| **authority_freshness_score** | (# concepts verified within staleness_threshold) / (total concepts) | 0.95 | 0.85 |
| **structural_validation_pass_rate** | (# authority lookups passing pre-boost validation) / (total authority lookups) | 0.98 | 0.90 |
| **multi_hop_trace_accuracy** | (# correct 2-hop paths) / (total 2-hop traces attempted) | 0.90 | 0.80 |
| **entry_point_identification_rate** | (# queries where entry point correctly identified) / (total trace/debug queries) | 0.85 | 0.75 |
| **stale_authority_detection_rate** | (# stale authorities correctly detected) / (total stale authorities in test set) | 0.95 | 0.90 |
| **overconfidence_guard_trigger_rate** | (# times guard triggered) / (total high-confidence lookups) | < 0.10 | < 0.15 |

### 6.2 Failure Conditions

```yaml
failure_conditions:
  critical:
    - id: "OWNER_NOT_RANK_1"
      condition: "primary_owner exists AND authority_status == 'validated' AND primary_owner.rank > 1"
      description: "Primary owner must be rank 1 when authority is validated"
      action: "Test fails, requires investigation"
    
    - id: "DISTRACTOR_IN_TOP_3"
      condition: "any forbidden_distractor in top 3 entries"
      description: "Forbidden distractors must never rank in top 3"
      action: "Test fails, requires investigation"
    
    - id: "OWNER_MISSING"
      condition: "primary_owner not in top 10 AND authority_confidence >= medium"
      description: "Primary owner completely missing from results"
      action: "Test fails, requires registry or index fix"
    
    # NEW CRITICAL FAILURES (v1.1)
    - id: "STALE_AUTHORITY_ERROR"
      condition: "authority_status == 'stale' AND (file missing OR class missing)"
      description: "Authority file or class no longer exists in codebase"
      action: "Registry requires update; mark concept as stale"
    
    - id: "FULL_BOOST_WITHOUT_VALIDATION"
      condition: "owner_boost == 100 AND authority_status != 'validated'"
      description: "Full boost applied without passing structural validation"
      action: "Overconfidence guard failure; review ranking logic"

  warning:
    - id: "NO_AUTHORITY_MATCH"
      condition: "authority_confidence == none AND intent is code_location/debug"
      description: "Query could not be resolved to any authority concept"
      action: "Consider adding concept to registry"
    
    - id: "WEAK_CONFIDENCE"
      condition: "authority_confidence == weak"
      description: "Authority match is uncertain"
      action: "Response should include uncertainty flag"
    
    - id: "COLLABORATOR_OUTRANKS_OWNER"
      condition: "collaborator.rank < primary_owner.rank"
      description: "Collaborator ranked higher than owner"
      action: "Review scoring weights"
    
    # NEW WARNING FAILURES (v1.1)
    - id: "MISSING_ENTRY_POINT_TRACE"
      condition: "intent == 'trace' AND entry_trace not present"
      description: "Trace query did not identify entry point leading to owner"
      action: "Review entry_points_index coverage"
    
    - id: "SHALLOW_PATH_ERROR"
      condition: "structural_context is empty AND authority_confidence >= medium"
      description: "Only lexical matches found; no structural relationships identified"
      action: "Code understanding index may be incomplete"
    
    - id: "AUTHORITY_FRESHNESS_WARNING"
      condition: "days_since_verification > staleness_threshold"
      description: "Authority has not been verified recently"
      action: "Schedule re-verification via code_trace or human review"

  info:
    - id: "MULTIPLE_CONCEPTS_MATCHED"
      condition: "len(matched_concepts) > 1"
      description: "Multiple concepts matched - compound query"
      action: "Ensure all owners are in top results"
    
    # NEW INFO EVENTS (v1.1)
    - id: "OVERCONFIDENCE_GUARD_TRIGGERED"
      condition: "authority_confidence == high AND structural_validation failed"
      description: "High-confidence authority did not pass structural validation"
      action: "Partial boost applied; lexical signals may compete"
    
    - id: "HOP_2_PRUNING_APPLIED"
      condition: "hop_2_targets_pruned > 0"
      description: "Multi-hop expansion was pruned to avoid fan-out"
      action: "Normal behavior; log for debugging"
```

### 6.3 L5.8 Validation Integration

The authority layer evaluation integrates into existing L5.8 validation framework:

```yaml
# Addition to L5.8 validation config
l5_8_validation:
  existing_suites:
    - pr6_baseline_invariants
    - symbol_owner_correction
    - core_aiops_correction
  
  new_suite: authority_golden_validation
  
  authority_golden_validation:
    input: "product_goldens.yaml"
    runner: "runtime/layer5/authority/eval/golden_runner.py"
    
    assertions:
      - name: "owner_at_1"
        check: "assert metrics.owner_at_1 >= 0.90"
        severity: "critical"
      
      - name: "owner_at_3"
        check: "assert metrics.owner_at_3 >= 0.95"
        severity: "critical"
      
      - name: "distractor_error_rate"
        check: "assert metrics.distractor_error_rate <= 0.05"
        severity: "critical"
      
      - name: "authority_hit_rate"
        check: "assert metrics.authority_hit_rate >= 0.80"
        severity: "warning"
      
      # NEW ASSERTIONS (v1.1)
      - name: "authority_freshness_score"
        check: "assert metrics.authority_freshness_score >= 0.85"
        severity: "warning"
      
      - name: "structural_validation_pass_rate"
        check: "assert metrics.structural_validation_pass_rate >= 0.90"
        severity: "critical"
      
      - name: "multi_hop_trace_accuracy"
        check: "assert metrics.multi_hop_trace_accuracy >= 0.80"
        severity: "warning"
      
      - name: "stale_authority_detection"
        check: "assert metrics.stale_authority_detection_rate >= 0.90"
        severity: "critical"
      
      - name: "no_full_boost_without_validation"
        check: "assert metrics.full_boost_without_validation_count == 0"
        severity: "critical"
    
    output:
      report_file: "authority_validation_report.json"
      include_in_ci: true
      
    # NEW VALIDATION SUITES (v1.1)
    structural_validation_suite:
      description: "Tests for pre-boost validation and staleness detection"
      tests:
        - "test_stale_file_detection"
        - "test_stale_class_detection"
        - "test_freshness_threshold_enforcement"
        - "test_overconfidence_guard"
      
    multi_hop_suite:
      description: "Tests for 2-hop call graph accuracy"
      tests:
        - "test_hop_2_expansion"
        - "test_pruning_rules"
        - "test_entry_point_tracing"
```

---

## 7. Implementation Plan

### Phase 1: Authority Registry (Foundation)

**Deliverables:**
- [ ] `product_authority_registry.yaml` with initial 10 concepts
- [ ] `runtime/layer5/authority/registry.py` - YAML loader and validator
- [ ] Unit tests for registry loading and validation
- [ ] Schema definition and validation

**Success Criteria:**
- Registry loads without errors
- Schema validates all required fields
- At least 10 product concepts defined with primary owners
- Forbidden distractors identified for each concept

**Risks:**
- Risk: Manual curation is time-consuming
- Mitigation: Start with most frequently queried concepts
- Risk: Concept definitions become stale
- Mitigation: Include `last_validated` timestamp and validation job

### Phase 2: Code Structure Index (Augmentation)

**Deliverables:**
- [ ] Extended `symbol_inventory.py` with method-level extraction
- [ ] `runtime/layer5/authority/code_index.py` - call graph extraction
- [ ] Import relationship tracking
- [ ] Package grouping and subsystem classification

**Success Criteria:**
- Java files parsed for class/method symbols
- 1-hop call graph edges extracted
- Import relationships tracked
- Index builds in < 5s for standard Motadata repo

**Risks:**
- Risk: Regex-based parsing is fragile
- Mitigation: Use existing proven patterns from symbol_inventory.py
- Risk: Call graph may have false positives
- Mitigation: Conservative extraction (high-confidence only)

### Phase 3: Ranking Fusion (Core Logic)

**Deliverables:**
- [ ] `runtime/layer5/authority/resolver.py` - concept matching
- [ ] `runtime/layer5/authority/ranking.py` - authority-aware scoring
- [ ] Integration with existing `retrieve_lexical()`
- [ ] Hard rule enforcement (owner@1, distractor suppression)

**Success Criteria:**
- Authority resolver correctly matches concepts
- Scoring formula produces correct rankings
- Hard rules enforced (owner at rank 1, distractors demoted)
- No regression on existing PR-6 baseline

**Risks:**
- Risk: Scoring weights need tuning
- Mitigation: Golden tests drive weight optimization
- Risk: Breaking existing retrieval behavior
- Mitigation: Feature flag for authority resolution

### Phase 4: Goldens + Evaluation (Validation)

**Deliverables:**
- [ ] `product_goldens.yaml` with 20+ golden test cases
- [ ] `runtime/layer5/authority/eval/golden_runner.py` - test harness
- [ ] CI integration for golden validation
- [ ] Metrics dashboard for tracking

**Success Criteria:**
- All critical golden tests pass
- owner@1 >= 0.90, owner@3 >= 0.95
- distractor_error_rate <= 0.05
- authority_hit_rate >= 0.80

**Risks:**
- Risk: Goldens may not cover edge cases
- Mitigation: Iteratively expand goldens based on failures
- Risk: Metrics may be gamed by overfitting
- Mitigation: Separate validation vs test sets

### Phase 5: Hardening (v1.1 Delta Tasks)

**Deliverables:**
- [ ] Registry freshness metadata: Add `verification` block to all concepts
- [ ] `runtime/layer5/authority/validation.py` - Pre-boost structural validation
- [ ] `runtime/layer5/authority/entry_points.py` - Entry point extraction/indexing
- [ ] 2-hop trace logic in `code_index.py` with pruning rules
- [ ] Stale authority evaluation tests in `eval/structural_validator.py`
- [ ] Overconfidence guard implementation in `ranking.py`

**Success Criteria:**
- authority_freshness_score >= 0.85
- structural_validation_pass_rate >= 0.90
- multi_hop_trace_accuracy >= 0.80
- entry_point_identification_rate >= 0.75
- stale_authority_detection_rate >= 0.90
- No full boost applied without validation (0 violations)

**Risks:**
- Risk: Freshness thresholds too strict, causing false staleness
- Mitigation: Configurable thresholds per concept; start lenient (90 days)
- Risk: 2-hop expansion creates noise
- Mitigation: Strict pruning rules; cap at 5 targets per hop
- Risk: Entry point detection misses custom patterns
- Mitigation: Extensible pattern registry; manual overrides in concept definitions

---

## 8. Example Outputs

### 8.1 Example: "Where is incident deduplication implemented?"

**Query Classification:**
```yaml
query_raw: "Where is incident deduplication implemented?"
query_tokens: ["incident", "deduplication", "implemented"]
intent_type: "code_location"
code_debug_intent: true
```

**Authority Resolution:**
```yaml
matched_concepts:
  - concept_id: "incident_deduplication"
    match_type: "exact"
    confidence: 1.0
    match_reason: "Query contains 'incident' and 'deduplication'"

primary_owner:
  file: "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentDeduplicationProcessor.java"
  class: "IncidentDeduplicationProcessor"
  method: "processDeduplication"
  confidence: "high"

collaborators:
  - file: "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentCorrelationEngine.java"
    role: "orchestrator"
  - file: "motadata/src/main/java/com/mindarray/aiops/query/IncidentQueryProcessor.java"
    role: "query_support"

forbidden_distractors:
  - "motadata/src/main/java/com/mindarray/aiops/integration/ServiceNowIntegration.java"
  - "motadata/src/main/java/com/mindarray/aiops/eventbus/handlers/IncidentEventHandler.java"

authority_confidence: "high"
```

**Evidence Bundle (top 5 entries):**
```yaml
entries:
  - rank: 0
    relative_path: "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentDeduplicationProcessor.java"
    retrieval_score: 245  # lexical (45) + owner_boost (100) + concept_match (40) + ...
    authority_role: "primary_owner"
    
  - rank: 1
    relative_path: "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentCorrelationEngine.java"
    retrieval_score: 112
    authority_role: "collaborator"
    
  - rank: 2
    relative_path: "motadata/src/main/java/com/mindarray/aiops/query/IncidentQueryProcessor.java"
    retrieval_score: 98
    authority_role: "collaborator"
    
  - rank: 3
    relative_path: "motadata/src/main/java/com/mindarray/aiops/model/Incident.java"
    retrieval_score: 72
    authority_role: "structural_context"
    
  - rank: 4
    relative_path: "motadata/src/main/java/com/mindarray/aiops/topology/DependencyManager.java"
    retrieval_score: 65
    authority_role: "callee"

authority_resolution:
  matched_concepts:
    - concept_id: "incident_deduplication"
      match_type: "exact"
      confidence: 1.0
  primary_owner:
    file: "motadata/src/main/java/com/mindarray/aiops/correlation/IncidentDeduplicationProcessor.java"
    class: "IncidentDeduplicationProcessor"
    method: "processDeduplication"
    confidence: "high"
  control_flow:
    - "IncidentEventHandler.handle()"
    - "IncidentCorrelationEngine.correlate()"
    - "IncidentDeduplicationProcessor.processDeduplication()"
  notes:
    - "Deduplication uses similarity scoring with configurable thresholds"
    - "Primary algorithm is in processDeduplication() method"
    - "Uses DependencyManager for topology-aware grouping"
  authority_confidence: "high"
```

**Plan-Gate Response (Answer-First):**
```
Incident deduplication is implemented in:

**Primary Implementation:**
`IncidentDeduplicationProcessor.java` → `processDeduplication()` method

**Control Flow:**
1. `IncidentEventHandler.handle()` - receives incident event
2. `IncidentCorrelationEngine.correlate()` - orchestrates processing
3. `IncidentDeduplicationProcessor.processDeduplication()` - performs deduplication

**Key Details:**
- Uses similarity scoring with configurable thresholds
- Leverages DependencyManager for topology-aware grouping

**Supporting Files:**
- `IncidentQueryProcessor.java` - query support for finding potential duplicates
- `IncidentCorrelationEngine.java` - correlation orchestration
```

### 8.2 Example: "How are alerts correlated or escalated?"

**Query Classification:**
```yaml
query_raw: "How are alerts correlated or escalated?"
query_tokens: ["alerts", "correlated", "escalated"]
intent_type: "code_understanding"
code_debug_intent: true
```

**Authority Resolution:**
```yaml
matched_concepts:
  - concept_id: "alert_correlation"
    match_type: "alias"
    confidence: 0.9
    match_reason: "Query matches alias 'related alerts'"
  - concept_id: "alert_escalation"
    match_type: "alias"
    confidence: 0.9
    match_reason: "Query matches alias 'escalate alert'"

primary_owners:  # Multiple owners for compound query
  - file: "motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java"
    class: "AlertCorrelationEngine"
    confidence: "high"
    concept: "alert_correlation"
  - file: "motadata/src/main/java/com/mindarray/aiops/alerting/AlertEscalationHandler.java"
    class: "AlertEscalationHandler"
    confidence: "high"
    concept: "alert_escalation"

authority_confidence: "high"
```

**Evidence Bundle (top 5 entries):**
```yaml
entries:
  - rank: 0
    relative_path: "motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java"
    retrieval_score: 230
    authority_role: "primary_owner"
    concept: "alert_correlation"
    
  - rank: 1
    relative_path: "motadata/src/main/java/com/mindarray/aiops/alerting/AlertEscalationHandler.java"
    retrieval_score: 225
    authority_role: "primary_owner"
    concept: "alert_escalation"
    
  - rank: 2
    relative_path: "motadata/src/main/java/com/mindarray/aiops/correlation/CorrelationManager.java"
    retrieval_score: 95
    authority_role: "collaborator"
    
  - rank: 3
    relative_path: "motadata/src/main/java/com/mindarray/aiops/topology/TopologyCache.java"
    retrieval_score: 85
    authority_role: "collaborator"
    
  - rank: 4
    relative_path: "motadata/src/main/java/com/mindarray/aiops/alerting/AlertNotificationService.java"
    retrieval_score: 78
    authority_role: "collaborator"

# AvailabilityCorrelationEngine is NOT in top 5 despite keyword match
# It would have scored ~45 (lexical) - 80 (distractor_penalty) = -35 (negative)
```

**Plan-Gate Response (Answer-First):**
```
Alerts are correlated and escalated through two main components:

**Alert Correlation:**
`AlertCorrelationEngine.java`
- Uses topology graph for dependency-aware correlation
- Supports both time-based and topology-based correlation
- Collaborates with TopologyCache for context enrichment

**Alert Escalation:**
`AlertEscalationHandler.java`
- Handles severity escalation based on policy rules
- Works with AlertNotificationService for downstream actions
- Escalation rules are policy-driven from AlertPolicyEngine

**Note:** AvailabilityCorrelationEngine handles a different domain (availability metrics) and is not involved in alert correlation.
```

---

## Appendix A: File Locations

```
docs/design/
└── PRODUCT_AUTHORITY_CODE_UNDERSTANDING_LAYER_v1.md  (this document, v1.1)

runtime/layer5/
├── authority/                          (NEW)
│   ├── __init__.py
│   ├── registry.py                     # Load product_authority_registry.yaml
│   ├── resolver.py                     # Concept extraction and matching
│   ├── code_index.py                   # Extended code understanding index (multi-hop v1.1)
│   ├── ranking.py                      # Authority-aware ranking fusion
│   ├── config.py                       # Authority layer configuration
│   ├── validation.py                   # (v1.1) Pre-boost sanity checks
│   ├── entry_points.py                 # (v1.1) Entry point detection and tracing
│   └── eval/
│       ├── __init__.py
│       ├── golden_runner.py            # Golden test harness
│       └── structural_validator.py     # (v1.1) Structural validation tests
├── retrieval/
│   └── lexical.py                      # MODIFIED: authority integration point
└── evidence/
    └── evidence_bundle.v1.schema.json  # MODIFIED: authority_resolution + structural_context

runtime/data/authority/                 (NEW)
├── product_authority_registry.yaml     # Product concept registry (v1.1 schema)
└── product_goldens.yaml                # Golden test cases (v1.1 schema)
```

---

## Appendix B: Contract Compatibility

This design maintains full backward compatibility with existing contracts:

| Contract | Status | Notes |
|----------|--------|-------|
| `layer5.evidence_bundle.v1` | **Extended** | New optional fields added; existing fields unchanged |
| `ask_request.v1.0` | **Unchanged** | No modifications to request schema |
| `POST /v1/ask` | **Unchanged** | Same endpoint, enhanced evidence |
| `POST /v1/export_evidence` | **Extended** | Returns enhanced evidence bundle |
| `/healthz`, `/version` | **Unchanged** | No modifications |

**Backward Compatibility Guarantees:**
- Evidence bundles without `authority_resolution` are valid
- Plan-Gate handles missing authority fields gracefully
- Existing retrieval behavior preserved when authority disabled
- No breaking changes to existing APIs

---

## Appendix C: Configuration

```yaml
# Authority layer configuration (runtime/layer5/authority/config.py)
# Schema version: authority_config.v1.1

authority_config:
  enabled: true
  
  # Registry location
  registry_path: "runtime/data/authority/product_authority_registry.yaml"
  
  # Matching thresholds
  exact_match_threshold: 1.0
  alias_match_threshold: 0.9
  partial_match_min_overlap: 0.5
  
  # Confidence mapping
  confidence_thresholds:
    high: 0.9
    medium: 0.6
    weak: 0.3
    none: 0.0
  
  # Scoring weights (scaled to policy_score_scale = 2)
  weights:
    # CONDITIONAL OWNER BOOST (v1.1)
    owner_boost_full: 100       # Only when authority_status == "validated"
    owner_boost_partial: 40     # When authority_status == "stale_candidate"
    owner_boost_none: 0         # When authority_status == "stale"
    
    exact_concept_match: 40
    alias_concept_match: 30
    partial_concept_match: 15
    collaborator_direct: 25
    collaborator_same_package: 10
    
    # MULTI-HOP CALLER/CALLEE (v1.1)
    caller_of_owner_hop_1: 15
    caller_of_owner_hop_2: 8    # hop_1 * decay_factor
    callee_of_owner_hop_1: 12
    callee_of_owner_hop_2: 6    # hop_1 * decay_factor
    
    # ENTRY POINT BOOST (v1.1)
    entry_point_direct: 20      # Entry point directly invokes owner
    entry_point_indirect: 10    # Entry → orchestrator → owner
    
    same_module: 8
    distractor_explicit: -80
    distractor_eventbus_generic: -40
    distractor_integration: -30
  
  # Hard rules (cannot be disabled)
  hard_rules:
    enforce_owner_rank_1: true
    enforce_distractor_demotion: true
    weak_authority_uncertainty_flag: true
    # OVERCONFIDENCE GUARD (v1.1)
    require_validation_for_full_boost: true
  
  # PRE-BOOST VALIDATION (v1.1)
  pre_boost_validation:
    enabled: true
    checks:
      - "file_exists"
      - "class_exists"
      - "method_exists"       # Optional, downgrades on failure
      - "is_referenced"       # File has at least one caller
      - "freshness_check"
    on_stale:
      log_event: true
      fallback_to_lexical: true
      mark_requires_verification: true
  
  # DRIFT CONTROL (v1.1)
  drift_control:
    default_staleness_threshold_days: 90
    freshness_check_enabled: true
    on_stale_authority:
      boost_allowed: "partial"
      log_stale_authority_error: true
  
  # Code index configuration (v1.1 — multi-hop)
  code_index:
    extract_methods: true
    extract_imports: true
    extract_calls: true
    max_call_hops: 2           # Upgraded from 1 to 2
    hop_decay_factor: 0.5      # hop_2 boost = hop_1 * 0.5
    cache_ttl_seconds: 300
    
    # MULTI-HOP PRUNING (v1.1)
    pruning:
      max_hop_2_targets_per_source: 5
      priority_order:
        - "same_package"
        - "known_collaborator"
        - "authority_linked"
        - "entry_point"
      exclude_patterns:
        - "*Logger*"
        - "*Metrics*"
        - "*Utils*"
        - "*Constants*"
    
    # ENTRY POINTS (v1.1)
    entry_points:
      enabled: true
      patterns:
        eventbus_handlers: "**/eventbus/handlers/*Handler.java"
        rest_controllers: "**/api/*Controller.java"
        schedulers: "**/scheduler/*Scheduler.java"
        consumers: "**/consumer/*Consumer.java"
```

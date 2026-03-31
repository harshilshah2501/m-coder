# Product Authority + Code Understanding Layer (v1)

**Document Type:** Architecture Design Specification  
**Status:** Planning Phase  
**Version:** 1.0  
**Date:** 2026-03-31

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
# Schema: product_authority_registry.v1
schema_version: "product_authority_registry.v1"
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
      confidence: "high"  # high | medium | weak
    
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

  alert_correlation:
    primary_owner:
      file: "motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java"
      class: "AlertCorrelationEngine"
      confidence: "high"
    
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

  alert_escalation:
    primary_owner:
      file: "motadata/src/main/java/com/mindarray/aiops/alerting/AlertEscalationHandler.java"
      class: "AlertEscalationHandler"
      confidence: "high"
    
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
```

### 2.2 Code Understanding Index Schema

**File:** In-memory structure (extends existing `WorkspaceFileIndex`)

```yaml
# Schema: code_understanding_index.v1
schema_version: "code_understanding_index.v1"
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
    
    # Import relationships (lightweight, 1-hop)
    imports:
      - "com.mindarray.aiops.model.Incident"
      - "com.mindarray.aiops.query.IncidentQueryProcessor"
      - "com.mindarray.aiops.topology.DependencyManager"
    
    # Outbound method calls (1-hop, high-confidence only)
    calls:
      - target_class: "IncidentQueryProcessor"
        target_method: "findPotentialDuplicates"
        call_site_line: 95
      - target_class: "DependencyManager"
        target_method: "getDependencies"
        call_site_line: 102
    
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
call_graph:
  # Forward edges: who does X call?
  forward:
    "IncidentCorrelationEngine.correlate":
      - "IncidentDeduplicationProcessor.processDeduplication"
      - "IncidentStore.save"
  
  # Reverse edges: who calls X?
  reverse:
    "IncidentDeduplicationProcessor.processDeduplication":
      - "IncidentCorrelationEngine.correlate"
      - "IncidentEventHandler.handle"

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
# Schema: product_goldens.v1
schema_version: "product_goldens.v1"
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

### 3.2 Authority Boost Values

```yaml
# Authority scoring weights (scaled to existing policy_score_scale = 2)
authority_weights:
  # Primary owner boost - overwhelming to ensure rank #1
  owner_boost: 100  # Must dominate all other signals
  
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
```

### 3.3 Distractor Penalty Rules

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

### 3.4 Structural Proximity Scoring

```yaml
structural_proximity:
  # 1-hop caller/callee relationships
  caller_relationship:
    description: "File A calls methods in primary_owner"
    boost: caller_of_owner
    max_hops: 1
  
  callee_relationship:
    description: "Primary owner calls methods in file B"
    boost: callee_of_owner
    max_hops: 1
  
  # Package affinity
  package_affinity:
    same_package: 10
    same_subsystem: 5
    different_subsystem: 0
  
  # Import relationship
  import_relationship:
    direct_import: 5
    transitive_import: 0  # Not tracked in v1
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
        }
      }
    },
    "owner_evidence": {
      "type": "array",
      "description": "Evidence entries marked as owner candidates",
      "items": {
        "$ref": "#/definitions/evidence_entry"
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
        
        # Pass to planner for answer-first generation
        planner_context = {
            "primary_owner": primary_owner,
            "control_flow": control_flow,
            "notes": notes,
            "authority_confidence": authority_confidence,
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
│ STEP 3: STRUCTURAL EXPANSION                                                │
│                                                                             │
│ Input:  AuthorityResolution, CodeUnderstandingIndex                         │
│ Output: StructuralContext (callers, callees, package_peers)                 │
│                                                                             │
│ Actions (only if authority match found):                                    │
│   1. Look up primary_owner file in code_understanding_index                 │
│   2. Extract direct callers (1-hop reverse call graph)                      │
│   3. Extract direct callees (1-hop forward call graph)                      │
│   4. Identify package peers (same package, exclude noise)                   │
│   5. Mark all as "structural context" with appropriate boosts               │
│                                                                             │
│ Skip conditions:                                                            │
│   - authority_confidence == "none" → skip structural expansion              │
│   - primary_owner file not in index → skip                                  │
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
│   1. For each hit, compute authority_score:                                 │
│      - If hit.file == primary_owner.file: +owner_boost (100)                │
│      - If hit.file in collaborators: +collaborator_boost (25)               │
│      - If hit.file in callers: +caller_boost (15)                           │
│      - If hit.file in callees: +callee_boost (12)                           │
│      - If hit.file in forbidden_distractors: +distractor_penalty (-80)      │
│   2. Update hit.score = lexical_score + authority_score                     │
│   3. Re-sort by new score (descending)                                      │
│   4. Apply hard rules:                                                      │
│      - If primary_owner exists and not rank 1 → swap to rank 1              │
│      - If distractor in top 3 → demote below rank 3                         │
│                                                                             │
│ Hard Rule Enforcement:                                                      │
│   - Primary owner MUST be rank 1 if authority_confidence >= medium          │
│   - Distractors MUST NOT be in top 3 regardless of score                    │
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
| **owner@1** | (# queries where primary owner is rank 1) / (total queries with known owner) | 0.95 | 0.90 |
| **owner@3** | (# queries where primary owner is in top 3) / (total queries with known owner) | 1.00 | 0.95 |
| **distractor_error_rate** | (# queries where distractor in top 3) / (total queries with forbidden distractors) | 0.00 | 0.05 |
| **authority_hit_rate** | (# queries resolved to authority concept) / (total queries) | 0.90 | 0.80 |
| **mean_owner_rank** | average rank of primary owner across all queries | 1.05 | 1.50 |
| **weak_authority_rate** | (# queries with weak/none confidence) / (total queries) | 0.10 | 0.20 |

### 6.2 Failure Conditions

```yaml
failure_conditions:
  critical:
    - id: "OWNER_NOT_RANK_1"
      condition: "primary_owner exists AND primary_owner.rank > 1"
      description: "Primary owner must be rank 1 when authority confidence >= medium"
      action: "Test fails, requires investigation"
    
    - id: "DISTRACTOR_IN_TOP_3"
      condition: "any forbidden_distractor in top 3 entries"
      description: "Forbidden distractors must never rank in top 3"
      action: "Test fails, requires investigation"
    
    - id: "OWNER_MISSING"
      condition: "primary_owner not in top 10 AND authority_confidence >= medium"
      description: "Primary owner completely missing from results"
      action: "Test fails, requires registry or index fix"

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

  info:
    - id: "MULTIPLE_CONCEPTS_MATCHED"
      condition: "len(matched_concepts) > 1"
      description: "Multiple concepts matched - compound query"
      action: "Ensure all owners are in top results"
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
    
    output:
      report_file: "authority_validation_report.json"
      include_in_ci: true
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
└── PRODUCT_AUTHORITY_CODE_UNDERSTANDING_LAYER_v1.md  (this document)

runtime/layer5/
├── authority/                          (NEW)
│   ├── __init__.py
│   ├── registry.py                     # Load product_authority_registry.yaml
│   ├── resolver.py                     # Concept extraction and matching
│   ├── code_index.py                   # Extended code understanding index
│   ├── ranking.py                      # Authority-aware ranking fusion
│   ├── config.py                       # Authority layer configuration
│   └── eval/
│       ├── __init__.py
│       └── golden_runner.py            # Golden test harness
├── retrieval/
│   └── lexical.py                      # MODIFIED: authority integration point
└── evidence/
    └── evidence_bundle.v1.schema.json  # MODIFIED: authority_resolution field

runtime/data/authority/                 (NEW)
├── product_authority_registry.yaml     # Product concept registry
└── product_goldens.yaml                # Golden test cases
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
    owner_boost: 100
    exact_concept_match: 40
    alias_concept_match: 30
    partial_concept_match: 15
    collaborator_direct: 25
    collaborator_same_package: 10
    caller_of_owner: 15
    callee_of_owner: 12
    same_module: 8
    distractor_explicit: -80
    distractor_eventbus_generic: -40
    distractor_integration: -30
  
  # Hard rules (cannot be disabled)
  hard_rules:
    enforce_owner_rank_1: true
    enforce_distractor_demotion: true
    weak_authority_uncertainty_flag: true
  
  # Code index configuration
  code_index:
    extract_methods: true
    extract_imports: true
    extract_calls: true
    max_call_hops: 1
    cache_ttl_seconds: 300
```

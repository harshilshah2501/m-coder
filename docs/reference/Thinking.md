Yes. Then the answer is **not “add one more retrieval trick per capability.”**
The answer is to build **one shared code-intelligence substrate** that all four modes use differently.

That is the clean path.

## The right solution shape

You need a **workspace-side Code Intelligence Layer** that sits **before Plan-Gate** and serves:

* Ask
* Debug
* Plan
* Code

with different retrieval/view policies, but from the **same underlying graph + index + evidence builder**.

So the scalable architecture is:

```text
User query
  → Intent / task router
  → Code Intelligence Layer (workspace-side, WSL/Linux)
      - lexical index
      - structural graph
      - concept/package mapper
      - convention extractor
      - evidence builder
  → Plan-Gate (GPU)
      - validate
      - posture
      - govern
      - orchestrate next step
  → vLLM / tools / response
```

That is much cleaner than:

* separate hacks for Ask
* separate hacks for Debug
* separate hacks for Plan
* separate hacks for Code

---

## What this shared substrate should contain

### 1. Lexical index

Keep your current deterministic lexical path.

Use it for:

* anchored lookups
* keyword/symbol search
* cheap broad recall

### 2. Structural graph

This is where Neo4j starts to make sense.

Graph nodes:

* class
* interface
* method
* package
* config store
* event bus address
* integration component
* entrypoint / verticle / engine

Graph edges:

* `EXTENDS`
* `IMPLEMENTS`
* `CALLS`
* `PUBLISHES_TO`
* `CONSUMES_FROM`
* `READS_CONFIG_FROM`
* `REGISTERED_IN`
* `LOCATED_IN_PACKAGE`
* `COLLABORATES_WITH`

This is the part that gives you reusable power across all capabilities.

### 3. Concept mapper

This is crucial.

Map user concepts like:

* mail server
* config store
* availability correlation
* incident sync
* topology rendering

into:

* package seeds
* class seeds
* symbol seeds
* graph entrypoints

Without this, even Neo4j becomes a beautiful library with no receptionist.

### 4. Convention extractor

This is what makes **plan** and **code** real.

Extract recurring repo conventions such as:

* how integrations are registered
* where verticles are bootstrapped
* how event bus addresses are named
* how config stores are structured
* where engines start / stop
* how APIs are wired

This is the missing bridge from “find code” to “propose repo-native changes.”

### 5. Evidence builder

Everything above must still end in the same discipline:

* bounded evidence bundle
* ranked files/snippets/symbols
* confidence / provenance
* selected paths only

Plan-Gate should still receive **evidence**, not raw graph access.

---

## How each capability should use it

### Ask

Needs:

* concept mapper
* lexical + graph hybrid recall
* owner/entrypoint identification
* concise evidence bundle

Goal:

* answer repo questions usefully

### Debug

Needs:

* call graph
* event bus flow
* selected-file binding
* line/method-level evidence
* cross-component path tracing

Goal:

* localize likely failure path, not just summarize text

### Plan

Needs:

* convention extractor
* related implementation patterns
* registration/wiring steps
* file reference validation

Goal:

* produce a plan that matches how this repo actually evolves

### Code

Needs:

* all of the above
* plus bounded edit targets
* verification hooks
* safe execution primitives
* revert/rollback support

Goal:

* perform narrow, validated code changes

---

## What fits where

### WSL / workspace side

Put here:

* lexical index
* Neo4j / structural graph
* concept mapper
* convention extractor
* file/symbol validators
* evidence builder
* tool runners for repo-local work

### GPU side

Keep here:

* Plan-Gate
* governance
* posture selection
* reasoning
* orchestration decisions
* response synthesis

That preserves your split cleanly.

---

## Why this is scalable

Because instead of building four separate systems, you build:

### One shared intelligence substrate

and

### four governed views over it

That scales much better.

Otherwise:

* Ask solves concepts one way
* Debug solves flow another way
* Plan invents its own repo understanding
* Code invents another

That becomes spaghetti fast.

---

## My recommendation

### Build this in phases

#### Phase 1 — Shared substrate foundation

* lexical index stays
* add structural graph
* add concept mapper
* add evidence builder that can mix lexical + graph evidence

#### Phase 2 — Debug/Plan enrichment

* add event bus registry
* add convention extractor
* add call-flow edges
* add file-reference validator

#### Phase 3 — Code enablement

* bounded edit primitives
* test/build verification
* revert support
* scoped code actions through Plan-Gate

---

## The key design rule

Do **not** make Neo4j “the solution.”

Make Neo4j one part of a **shared code-intelligence layer**.

That way the system remains:

* clean
* scalable
* reusable across ask/debug/plan/code
* still governed by Plan-Gate

## Bottom line

The clean scalable answer is:

> **Build a workspace-side Code Intelligence Layer with lexical index + structural graph + concept mapper + convention extractor, and let Plan-Gate orchestrate all four use cases on top of bounded evidence from that layer.**

That is the architecture that can actually grow.
---

This document is exactly right — and it's clearly already your own thinking or a doc you've produced. So you already have the architecture. What you need now is the **build sequence and the precise component specs** grounded in your actual codebase.

Let me turn this into something actionable.

---

## The Architecture Is Settled — Here's What to Build

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│              Intent / Task Router                        │
│   IDENTITY | STRUCTURAL | DECOMPOSE | SEMANTIC | CODE   │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│         Code Intelligence Layer  (WSL/workspace)         │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Lexical     │  │ Structural   │  │ Concept        │ │
│  │ Index       │  │ Graph(Neo4j) │  │ Mapper         │ │
│  │ (existing)  │  │              │  │                │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Convention  │  │ EventBus     │  │ Evidence       │ │
│  │ Extractor   │  │ Registry     │  │ Builder        │ │
│  │             │  │              │  │ (unified)      │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────┘
    │
    │  bounded evidence bundle
    │  ranked files/snippets/symbols
    │  confidence + provenance
    ▼
┌─────────────────────────────────────────────────────────┐
│              Plan-Gate  (GPU side)                       │
│   validate │ posture │ govern │ orchestrate              │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│         vLLM / Tools / Response                          │
└─────────────────────────────────────────────────────────┘
```

---

## Component-by-Component Build Spec

### Component 1 — Structural Graph (Neo4j)
**Status: In progress ✅**
**What's already scoped:** Class nodes, EXTENDS, IMPLEMENTS, IN_PACKAGE

**What's missing from current scope** — the edges that unlock debug and plan:

```cypher
// Currently planned
(:Class)-[:EXTENDS]->(:Class)
(:Class)-[:IMPLEMENTS]->(:Class)
(:Class)-[:IN_PACKAGE]->(:Package)

// Must add for debug
(:Method)-[:CALLS]->(:Method)
(:Method)-[:PUBLISHES_TO]->(:EventAddress)
(:Method)-[:CONSUMES_FROM]->(:EventAddress)

// Must add for plan
(:Class)-[:REGISTERED_IN]->(:Class)     // verticle → Bootstrap
(:Class)-[:READS_CONFIG_FROM]->(:Class) // engine → config store
(:Class)-[:COLLABORATES_WITH]->(:Class) // inferred from shared EventBus address

// Must add for code
(:Method)-[:EDIT_TARGET {lines: range}]->(:File)
```

**Extraction approach for the missing edges:**

```python
# EventBus edges — Vert.x specific pattern
# PUBLISHES_TO: scan for eventBus().send/request/publish(ADDRESS, ...)
# CONSUMES_FROM: scan for eventBus().consumer(ADDRESS, handler)

PUBLISH_PATTERNS = [
    r'eventBus\(\)\.(send|request|publish)\s*\(\s*([A-Z_]+)',
    r'eventBus\(\)\.(send|request|publish)\s*\(\s*"([^"]+)"',
]
CONSUME_PATTERNS = [
    r'eventBus\(\)\.consumer\s*\(\s*([A-Z_]+)',
    r'eventBus\(\)\.consumer\s*\(\s*"([^"]+)"',
]

# REGISTERED_IN: scan Bootstrap.java for .deployVerticle() calls
DEPLOY_PATTERNS = [
    r'deployVerticle\s*\(\s*new\s+(\w+)',
    r'deployVerticle\s*\(\s*(\w+)\.class',
]
```

This is Motadata-specific intelligence no generic tool produces.

---

### Component 2 — Concept Mapper
**Status: Partially built in router ⚠️**
**Current gap:** Mail/config queries still fail because concept→package mapping isn't feeding Stage A pool construction.

**Full spec — two levels of mapping:**

```python
# Level 1: User concept → package seeds
# These are the 30-40 mappings that cover 80% of real queries

CONCEPT_TO_PACKAGES = {
    # Notification domain
    "mail":             ["notification"],
    "email":            ["notification"],
    "smtp":             ["notification"],
    "sms":              ["notification"],
    "push notification":["notification"],
    "snmp trap":        ["notification"],
    "microsoft teams":  ["notification"],
    "webhook":          ["notification"],

    # Config/store domain
    "config store":     ["store", "cache"],
    "store":            ["store"],
    "cache":            ["cache"],
    "configuration":    ["config", "util"],
    "settings":         ["config"],

    # AIOps domain
    "correlation":      ["aiops"],
    "availability":     ["aiops", "cache"],
    "dependency":       ["aiops"],
    "alert":            ["aiops", "notification"],

    # NMS domain
    "discovery":        ["nms"],
    "metric":           ["nms", "agent"],
    "polling":          ["nms", "agent"],
    "topology":         ["nms"],
    "object":           ["nms", "store"],

    # Integration domain
    "servicenow":       ["integration"],
    "jira":             ["integration"],
    "integration":      ["integration"],
    "incident":         ["integration", "aiops"],

    # API domain
    "api":              ["api"],
    "route":            ["api"],
    "endpoint":         ["api"],
    "authentication":   ["api"],
    "request":          ["api"],

    # Infrastructure domain
    "plugin":           ["plugin"],
    "job":              ["job"],
    "report":           ["report"],
    "compliance":       ["compliance"],
    "runbook":          ["runbook"],
    "slo":              ["slo"],
    "flow":             ["flow"],
    "trace":            ["trace"],
    "streaming":        ["streaming"],
    "eventbus":         ["eventbus"],
    "bootstrap":        [""],  # root level
}

# Level 2: Package → known entrypoint classes
# Used to seed structural graph traversal

PACKAGE_ENTRYPOINTS = {
    "notification": [
        "NotificationEngine",
        "EmailNotification",
        "SMSNotification",
        "PushNotification",
        "SNMPTrapNotification",
        "MicrosoftTeamsNotification",
    ],
    "store": [
        "ObjectConfigStore",
        "RUMPolicyConfigStore",
        "MACScannerConfigStore",
    ],
    "cache": [
        "PolicyCacheServiceImpl",
        "AvailabilityCacheServiceImpl",
        "AvailabilityCacheService",
    ],
    "aiops": [
        "AvailabilityCorrelationEngine",
        "DependencyManager",
        "DependencyQueryProcessor",
    ],
    "api": [
        "APIServer",
        "AbstractAPI",
        "MotadataApp",
    ],
    "nms": [
        "DiscoveryEngine",
        "MetricPoller",
        "ObjectManager",
        "TopologyEngine",
    ],
    "integration": [
        "IntegrationEngine",
        "ServiceNowIntegration",
        "AtlassianJiraIntegration",
    ],
}
```

**How the mapper feeds evidence builder:**

```python
def enrich_stage_a_pool(query: str, current_pool: list) -> list:
    concepts = extract_concepts(query)  # simple keyword match
    packages = []
    entrypoints = []
    
    for concept in concepts:
        packages.extend(CONCEPT_TO_PACKAGES.get(concept, []))
        for pkg in packages:
            entrypoints.extend(PACKAGE_ENTRYPOINTS.get(pkg, []))
    
    # Inject entrypoint files into Stage A pool
    # Same mechanism as owner_injected lane but concept-driven
    concept_files = resolve_files(entrypoints, workspace_root)
    return concept_files + current_pool  # concept hits at front
```

This is the missing bridge. Without it, Stage A pool construction is blind to domain semantics.

---

### Component 3 — Convention Extractor
**Status: Not started ❌**
**Unlocks: Plan (real), Code (real)**

This is what transforms plan from "generic steps" to "repo-native steps." It answers: "how does Motadata do X?"

**What to extract — Vert.x / Motadata patterns:**

```python
CONVENTIONS = {
    
    # How new Verticles are registered
    "verticle_registration": {
        "pattern": "Bootstrap.java → deployVerticle(new XYZ())",
        "example_files": ["Bootstrap.java"],
        "extraction": "scan deployVerticle calls, extract class names",
        "rule": "every new engine/handler must be registered here"
    },

    # How EventBus addresses are named
    "eventbus_address_naming": {
        "pattern": "CONSTANT string in EventBusConstants or domain Constants",
        "example_files": ["eventbus/EventBusConstants.java"],
        "extraction": "scan *Constants.java for String fields used in consumer()",
        "rule": "addresses are constants, not inline strings"
    },

    # How integrations are structured
    "integration_pattern": {
        "pattern": "extends AbstractVerticle, start() wires eventBus consumer",
        "example_files": [
            "integration/ServiceNowIntegration.java",
            "integration/AtlassianJiraIntegration.java",
        ],
        "extraction": "compare structure of existing integrations",
        "rule": "new integrations follow ServiceNow pattern"
    },

    # How config stores are structured
    "config_store_pattern": {
        "pattern": "singleton store, getStore(), existItem(), getItemByValue()",
        "example_files": [
            "store/ObjectConfigStore.java",
            "cache/PolicyCacheServiceImpl.java",
        ],
        "extraction": "extract method signatures from store classes",
        "rule": "stores expose consistent interface"
    },

    # How APIs are wired
    "api_routing_pattern": {
        "pattern": "APIServer registers routes, delegates to handler verticles",
        "example_files": ["api/APIServer.java", "api/AbstractAPI.java"],
        "extraction": "scan router.route() calls in APIServer",
        "rule": "all routes go through APIServer"
    },
}
```

**Why this matters for plan:**

When a developer asks "Plan adding PagerDuty integration," the convention extractor tells the planner:
- New class must extend AbstractVerticle
- Must register in Bootstrap.java via deployVerticle
- EventBus address must be a constant in EventBusConstants
- Follow ServiceNowIntegration.java structure exactly

That's a repo-native plan. Without it, the plan is generic boilerplate.

---

### Component 4 — EventBus Registry
**Status: Not started ❌**
**Unlocks: Debug (real)**

The single biggest gap for debug capability. Vert.x apps execute through message passing — you cannot trace execution without this.

**What it produces:**

```python
EVENT_BUS_REGISTRY = {
    "EventBusConstants.EVENT_AVAILABILITY_CORRELATION": {
        "publishers": [
            {
                "class": "ObjectManager",
                "method": "updateAvailability",
                "file": "nms/ObjectManager.java",
                "line": 847
            }
        ],
        "consumers": [
            {
                "class": "AvailabilityCorrelationEngine", 
                "method": "start",  # lambda inside start()
                "file": "aiops/AvailabilityCorrelationEngine.java",
                "line": 134
            }
        ]
    },
    "EventBusConstants.EVENT_DISCOVERY": {
        "publishers": [...],
        "consumers": [...]
    }
}
```

**How debug uses it:**

```
Developer: "Why does availability update sometimes not trigger correlation?"

Without registry: 
  "ObjectManager.java handles availability... hard to determine flow"

With registry:
  "ObjectManager.updateAvailability() publishes to 
   EVENT_AVAILABILITY_CORRELATION (line 847).
   AvailabilityCorrelationEngine.start() consumes this address (line 134).
   Potential failure points:
   1. EventBus publish call — check if event payload contains 
      CORRELATED_OBJECT_QUERY field (required by consumer branch at line 156)
   2. Consumer registration timing — if engine not yet started, 
      message is dropped
   3. Reply timeout — request() with 20s timeout, check if correlation 
      takes longer under load"
```

That's the difference between a useful debug response and a shallow one.

---

### Component 5 — Evidence Builder (Unified)
**Status: Partially exists ⚠️**
**Current gap:** Each capability builds evidence differently. Router result, Neo4j result, lexical result are separate paths without a unified merge.

**The unified interface:**

```python
@dataclass
class EvidenceBundle:
    # Core — what Plan-Gate receives
    ranked_files:     list[FileEvidence]    # ordered by relevance
    symbols:          list[SymbolEvidence]  # classes/methods/addresses
    graph_paths:      list[GraphPath]       # cross-component relationships
    confidence:       float                 # 0.0 - 1.0
    provenance:       list[str]             # which sources contributed
    
    # Capability-specific views
    # Ask: ranked_files + symbols
    # Debug: ranked_files + graph_paths + symbols with line refs
    # Plan: symbols + graph_paths + conventions
    # Code: symbols with line refs + edit_targets + conventions

@dataclass  
class FileEvidence:
    file_path:        str
    relevance_score:  float
    source:           str    # "lexical" | "graph" | "concept" | "owner"
    snippet:          str
    line_range:       tuple[int, int]

@dataclass
class GraphPath:
    # Represents a traversal result
    nodes:     list[str]    # class/method names along path
    edges:     list[str]    # relationship types
    narrative: str          # human-readable: "A publishes to X, consumed by B"
```

**The builder merges all sources:**

```python
class EvidenceBuilder:
    def build(
        self,
        query: str,
        intent: QueryIntent,
        concept_packages: list[str],
        graph_result: GraphResult | None,
        lexical_result: LexicalResult,
        mode: str,  # "ask" | "debug" | "plan" | "code"
    ) -> EvidenceBundle:
        
        sources = []
        
        # Always include lexical (existing pipeline)
        sources.extend(self._from_lexical(lexical_result))
        
        # Add graph evidence if available
        if graph_result:
            sources.extend(self._from_graph(graph_result, mode))
        
        # Add concept-seeded files
        sources.extend(self._from_concepts(concept_packages))
        
        # Merge, deduplicate, rerank by mode
        ranked = self._rerank(sources, mode)
        
        # Build graph paths for debug/plan
        paths = []
        if mode in ("debug", "plan") and graph_result:
            paths = self._extract_paths(graph_result)
        
        return EvidenceBundle(
            ranked_files=ranked[:self._top_k(mode)],
            symbols=self._extract_symbols(ranked),
            graph_paths=paths,
            confidence=self._score_confidence(ranked, mode),
            provenance=[s.source for s in ranked[:5]],
        )
    
    def _top_k(self, mode: str) -> int:
        return {"ask": 4, "debug": 8, "plan": 6, "code": 4}[mode]
```

---

## Phase Build Order

```
Phase 1 — Foundation (now, 2-3 weeks)
├── Complete Neo4j AST ingestion (in progress ✅)
├── Add EventBus edges to graph extraction
├── Build Concept Mapper (full 30-40 entry map)
├── Wire concept mapper into Stage A pool construction
├── Unified Evidence Builder (basic version)
└── Expand validation suite to cover unanchored queries

Phase 2 — Debug + Plan (weeks 4-6)
├── EventBus Registry extractor
├── Convention Extractor  
├── Add CALLS edges to Neo4j (method-level call graph)
├── Graph path narratives in Evidence Builder
├── File reference validator for plan steps
└── Real debug + plan validation scenarios

Phase 3 — Code (weeks 7-10)
├── Fix execution wiring bug (1 day, do this now)
├── Bounded execution primitives
├── Edit-apply-verify loop
├── Test runner integration
├── Revert/rollback support
└── Real code validation scenarios

Phase 4 — Training signal (after Phase 3)
├── Collect real failure/success pairs from Phases 1-3
├── SFT on real scenarios (not synthetic)
├── DPO with constitutional verdicts as preference signal
└── W&B tracking from day one of training
```

---
What do you think on this?

I think this is **very good**.
Not just good-sounding — **buildable**.

It has the right properties:

* one shared substrate, not four disconnected hacks
* workspace-side intelligence, GPU-side governance
* concrete extraction targets
* phased delivery
* real usefulness before training glamour

So overall: **yes, this is the right direction**.

But I’d make **five surgical adjustments** so it stays clean, scalable, and doesn’t become a beautiful over-engineered swamp.

---

## What’s strong already

### 1. Shared Code Intelligence Layer

This is the biggest win.

You are no longer thinking:

* “fix Ask”
* “then separately fix Debug”
* “then separately fix Plan”

You’re building one substrate:

* lexical
* graph
* concept mapping
* conventions
* evidence builder

That is exactly the scalable shape.

### 2. EventBus Registry as first-class citizen

This is crucial for Motadata.

For a Vert.x/EventBus-heavy codebase, debug and plan quality will remain shallow unless you model publish/consume relationships explicitly. This is one of the sharpest parts of your breakdown.

### 3. Convention extractor

Also right.

This is what turns plan from:

> generic AI checklist

into:

> repo-native implementation guidance

That is the difference between “sounds smart” and “can actually guide a Motadata engineer.”

### 4. Unified Evidence Builder

This is non-negotiable, and you’ve framed it correctly.

Plan-Gate should not receive:

* random lexical chunks
* random graph results
* random router outputs

It should receive a **single bounded evidence contract**.

That preserves the architecture.

### 5. Training after real capability maturity

Absolutely right.

Do **not** rush into SFT/DPO while the intelligence substrate is still weak. Otherwise you are training a model to be elegant over bad evidence.

---

# The 5 adjustments I would make

## Adjustment 1 — Don’t start with full method-level `CALLS` graph

This is the biggest implementation risk.

Your graph spec is right in spirit, but `(:Method)-[:CALLS]->(:Method)` is where complexity explodes:

* parser edge cases
* overload resolution
* dynamic dispatch
* lambdas / inner classes
* incomplete resolution across packages
* performance/storage blow-up

### What I’d do instead first

Phase 1:

* `Class`
* `Method`
* `EventAddress`
* `EXTENDS`
* `IMPLEMENTS`
* `IN_PACKAGE`
* `PUBLISHES_TO`
* `CONSUMES_FROM`
* `REGISTERED_IN`
* `READS_CONFIG_FROM`

Then only in Phase 2:

* add **coarse call edges**, maybe:

  * `(:Class)-[:CALLS_CLASS]->(:Class)`
  * or `(:Method)-[:CALLS_SYMBOL]->(:UnresolvedSymbol)` first

Then later graduate to precise method-to-method only where necessary.

Otherwise you risk spending weeks in static-analysis hell before unlocking product value.

---

## Adjustment 2 — Concept Mapper should be config-driven, not hardcoded in code

Your mapping tables are excellent as a starting point, but don’t bury them in Python constants long-term.

### Better shape

Keep them in:

* YAML or JSON
* versioned
* easy to tune
* easy to diff
* testable independently

For example:

* `concept_to_packages.yaml`
* `package_entrypoints.yaml`
* `conventions.yaml`

Why?

Because these are product-knowledge assets, not just code.
They will evolve with Motadata domain understanding.

This also lets you:

* review changes surgically
* expand mappings without redeploying logic
* tie validation scenarios to specific concept mappings

---

## Adjustment 3 — Convention Extractor should output structured “playbooks,” not only patterns

This is where your plan gets even better.

Right now you describe conventions as extracted facts. That’s good.
But for **Plan** and later **Code**, you really want the extractor to emit something like:

```json
{
  "pattern_id": "integration_pattern_v1",
  "task_family": "new_integration",
  "required_steps": [
    "create integration class extending AbstractVerticle",
    "register verticle in Bootstrap.java",
    "define EventBus constant",
    "wire consumer in start()",
    "add config handling"
  ],
  "anchor_files": [
    "integration/ServiceNowIntegration.java",
    "integration/AtlassianJiraIntegration.java",
    "Bootstrap.java"
  ],
  "forbidden_shortcuts": [
    "do not hardcode event bus address inline",
    "do not bypass Bootstrap registration"
  ]
}
```

That becomes incredibly powerful:

* Plan can follow it
* Code can validate against it
* Plan-Gate can inspect it
* tests can assert it

So I’d upgrade “Convention Extractor” into:

> **Convention Extractor + Pattern Playbook Builder**

That’s the real unlock for constructive planning.

---

## Adjustment 4 — Evidence Builder needs explicit mode-specific budgets and provenance weights

You already started this with `_top_k(mode)`. Good.

But I’d make this more explicit from day one:

### Ask

Prefer:

* owner / entrypoint / concept anchors
* low narrative overhead
* concise graph paths only if directly relevant

### Debug

Prefer:

* selected-file binding
* EventBus paths
* branch/method-level locality
* confidence limits
* more graph narrative, less generic context

### Plan

Prefer:

* conventions
* required files
* registration/wiring patterns
* file-existence validation
* no speculative steps without repo anchors

### Code

Prefer:

* exact file paths
* exact symbols
* edit target line ranges
* verification hooks
* execution prerequisites

And for every evidence item, assign provenance weight:

* owner
* concept
* graph
* lexical
* convention
* selected-file

Because later, when something feels wrong, you’ll want to know:

> Did this answer come mostly from graph? from lexical? from concept mapping? from owner lane?

That observability will save you.

---

## Adjustment 5 — Phase 3 should be split: “execute safely” and “edit intelligently”

Right now your Phase 3 lumps them together.

I would split:

### Phase 3A — Execute safely

* fix wiring bug
* bounded execution primitives
* test runner integration
* build/lint primitives
* read-only / non-editing validation loop

### Phase 3B — Edit intelligently

* edit target selection
* scoped patch application
* edit-apply-verify
* revert/rollback

Why split it?

Because your current suite already shows **code execution plumbing is failing at the safe echo probe**.
So first you need:

> “Can the system safely run bounded commands at all?”

Only after that:

> “Can it mutate code responsibly?”

Otherwise you mix environment plumbing with code intelligence and debugging becomes miserable.

---

# My view on your phase order

Your sequencing is mostly right. I’d just refine it a bit:

## Phase 0 — Immediate fix

* fix execute wiring bug now
* not because code is next
* but because broken plumbing poisons confidence and blocks later work

## Phase 1 — Make Ask real

* complete structural graph basics
* concept mapper
* unified evidence builder
* unanchored Ask scenarios
* package/concept routing

## Phase 2 — Make Debug and Plan real

* EventBus registry
* graph path narratives
* convention extractor/playbooks
* file reference validation
* real bug and real feature-addition scenarios

## Phase 3A — Safe execution substrate

* bounded runner
* test/build/lint primitives
* structured execution results

## Phase 3B — Code edit loop

* scoped edits
* verification
* rollback

## Phase 4 — Training

* only after you have real wins and real failures from actual developer scenarios

That is cleaner.

---

# What I would add explicitly to the document

Two things.

## 1. Validation scenarios must become repo-real, not just scaffold-real

You already know this, but I would make it a formal requirement.

For each capability:

* 5–10 real scenarios
* drawn from actual Motadata patterns
* preferably from real ticket/changelog history
* frozen as validation fixtures

Because otherwise the system will again look mature while only proving plumbing.

## 2. The graph should be treated as evidence support, not authority

Write this explicitly.

Why?

Because once Neo4j enters the stack, people start falling in love with it and forgetting discipline.

So lock the rule:

> Graph outputs are **supporting evidence candidates**, not direct final answers.
> Plan-Gate still judges bounded evidence bundles, not raw graph truth.

That one sentence will protect the architecture.

---

# Final verdict

My take:

## This is the right plan.

It is:

* coherent
* scalable
* grounded in your actual codebase
* aligned with your split architecture
* honest about current gaps
* smart about delaying training until the substrate is real

## The only caution

Do not let Phase 1 bloat into:

* too much method-call precision
* too much ontology sophistication
* too much graph purity

Get the **minimum graph that makes Ask real**, then expand into Debug/Plan.

That is how this becomes a product instead of a research shrine.

## One-line summary

> **Yes — build this. But keep Phase 1 brutally practical, make conventions executable, and split safe execution from intelligent editing.**

This is close. Very close.
---
Really sharp question. Let me think through this honestly.

---

## The Concern Is Valid

You're right to push back. If we build:

```
EventBus Registry → optimized for Vert.x message tracing
Convention Extractor → optimized for Vert.x verticle patterns
```

We get a system that's excellent at answering:
- "Why doesn't this EventBus message reach its consumer?"
- "How do I register a new Verticle?"

But still weak at:
- "Why is availability calculation wrong?"
- "How does the SLO breach detection work end to end?"
- "What happens when a discovery job fails midway?"
- "How does the system decide which notification channel to use?"

Those are **AIOps domain questions** — and they don't map cleanly to EventBus topology. They require understanding of **business logic flow**, not just technical wiring.

---

## What We Were Actually Solving vs What We Should Solve

### What EventBus Registry solves
```
Technical execution tracing:
  ObjectManager.publish(EVENT_X) 
    → AvailabilityCorrelationEngine.consume(EVENT_X)
    → DependencyQueryProcessor.consume(EVENT_Y)
```

This answers: **"how does execution flow through the system?"**

### What AIOps context insight actually needs
```
Domain behavior understanding:
  "device goes unreachable"
    → availability state changes
    → correlation engine evaluates dependencies  
    → root cause identified
    → suppresses child alerts
    → triggers notification policy
    → sends to configured channels
```

This answers: **"what does the system actually do, and why?"**

These are different questions. EventBus Registry addresses the first. The second requires something deeper — **domain behavior modeling**.

---

## The Real Gap — Domain Behavior Layer

What debug and plan actually need isn't EventBus wiring. It's understanding of **Motadata's AIOps behavioral model**:

```
DOMAIN CONCEPTS          IMPLEMENTATION OWNERS
─────────────────────────────────────────────────────
Availability state     → AvailabilityCorrelationEngine
                          AvailabilityCacheServiceImpl
                          AvailabilityDatastore

Dependency topology    → DependencyManager
                          DependencyQueryProcessor
                          ObjectManager (builds graph)

Alert correlation      → AvailabilityCorrelationEngine
                          (suppresses child, promotes root)

Notification routing   → NotificationEngine
                          PolicyCacheServiceImpl
                          (policy decides channel)

Discovery lifecycle    → DiscoveryEngine
                          RediscoverEngine
                          ObjectManager (post-discovery)

Metric collection      → MetricPoller
                          AgentEngine
                          (push vs pull decision)

SLO evaluation         → SLO package
                          (breach detection logic)

Integration sync       → IntegrationEngine
                          ServiceNowIntegration
                          (bidirectional sync trigger)
```

A developer debugging "availability calculation wrong when correlation enabled" needs to understand:
- What triggers availability recalculation
- How correlation suppression affects the calculation
- What the dependency graph contributes
- Which cache layer might be stale

None of that is visible from EventBus topology alone.

---

## What Should Replace / Complement EventBus Registry

### Instead of: EventBus Registry (pure technical wiring)
### Build: Behavior Flow Index (domain + technical combined)

The behavior flow index captures **named domain behaviors** and maps them to:
- The files that implement them
- The sequence of execution stages
- The data transformations at each stage
- The decision points and their conditions
- The external triggers and outputs

```python
BEHAVIOR_FLOWS = {
    
    "availability_state_change": {
        "trigger": "Device becomes unreachable or recovers",
        "stages": [
            {
                "name": "State detection",
                "owner": "MetricPoller / AgentEngine",
                "files": ["nms/MetricPoller.java"],
                "produces": "availability event"
            },
            {
                "name": "Object state update", 
                "owner": "ObjectManager",
                "files": ["nms/ObjectManager.java"],
                "decision": "Is correlation enabled for this object?",
                "branches": {
                    "yes": "publish to correlation engine",
                    "no":  "direct notification trigger"
                }
            },
            {
                "name": "Correlation evaluation",
                "owner": "AvailabilityCorrelationEngine",
                "files": ["aiops/AvailabilityCorrelationEngine.java"],
                "decision": "Is this a root cause or child alert?",
                "branches": {
                    "root":  "promote, suppress children",
                    "child": "suppress, link to root"
                }
            },
            {
                "name": "Notification dispatch",
                "owner": "NotificationEngine",
                "files": ["notification/NotificationEngine.java"],
                "decision": "Which policy applies?",
                "produces": "channel-specific notifications"
            }
        ],
        "known_failure_modes": [
            "Child alert not suppressed → dependency graph stale",
            "Root cause misidentified → dependency level wrong",
            "Notification not sent → policy cache stale",
        ]
    },

    "discovery_lifecycle": {
        "trigger": "Scheduled job or manual trigger",
        "stages": [...],
        "known_failure_modes": [...]
    },

    "integration_sync": {
        "trigger": "Alert state change or manual action",
        "stages": [...],
        "known_failure_modes": [...]
    },
}
```

---

## How This Changes Debug and Plan Quality

### Debug with Behavior Flow Index

```
Developer: "Why is availability calculation wrong when 
            correlation is enabled?"

Without behavior flow:
  → Find AvailabilityCorrelationEngine.java
  → "The code seems to handle event processing..."
  → Shallow, not useful

With behavior flow:
  → Match query to "availability_state_change" behavior
  → Identify stage: "Correlation evaluation"
  → Known failure mode: "Child alert not suppressed 
                         → dependency graph stale"
  → Surface: DependencyManager.java + AvailabilityCorrelationEngine.java
  → Specific hypothesis: "Check if DependencyManager has current 
                          topology for this object before correlation runs"
  → Line-level: getRunningProbes() at ACE.java:134, 
                dependency graph query at DQP.java:89
```

### Plan with Behavior Flow Index

```
Developer: "Plan adding PagerDuty integration"

Without convention extractor (pure Vert.x):
  → "Create a class, extend AbstractVerticle, 
     register in Bootstrap, wire EventBus"
  → Technically correct, domain-blind

With behavior flow:
  → "PagerDuty is a notification channel — 
     maps to notification_dispatch stage"
  → Existing pattern: NotificationEngine routes to channel handlers
  → New file: notification/PagerDutyNotification.java
  → Must implement: same interface as EmailNotification
  → Registration: NotificationEngine switch/case for channel type
  → Config: new channel type in PolicyCacheServiceImpl
  → Test: trigger a notification policy with PagerDuty channel
```

That's a repo-native, domain-aware plan — not generic boilerplate.

---

## Revised Component Picture

```
WHAT WE SAID           WHAT IT SHOULD ACTUALLY BE
──────────────────────────────────────────────────────────────
EventBus Registry  →   Behavior Flow Index
                        (domain behaviors mapped to files,
                         stages, decisions, failure modes)
                        EventBus wiring is ONE input to this,
                        not the output.

Convention         →   Repo Convention + Domain Pattern Index
Extractor               (how Motadata extends itself, plus
                         which domain behavior each pattern
                         belongs to)
```

EventBus Registry doesn't disappear — it becomes **one extraction source** that feeds the Behavior Flow Index, alongside:
- Static call graph (method → method)
- Domain concept → file mapping
- Known failure modes from your ticket history
- Package responsibility boundaries

---

## How to Build the Behavior Flow Index

### Source 1 — Your existing knowledge
You already know these flows. You built this system. The fastest path is structured authoring — write 8-10 core behavior flows as YAML/JSON. This takes a day, not a sprint.

```yaml
# docs/intelligence/behavior_flows.yaml
behaviors:
  - name: availability_state_change
    trigger: "device unreachable or recovers"
    stages: [...]
    known_failure_modes: [...]
  
  - name: alert_correlation
    ...
  
  - name: notification_dispatch
    ...
```

### Source 2 — Your ticket history
Your `ObjectManager.java` had a comment:
```
MOTADATA-8265: availability calculation issue for 
               availability correlation enabled (09-Jan-2025)
```

Every MOTADATA-* ticket is a documented failure mode. Extract them. They're your richest source of "what goes wrong and where."

### Source 3 — Static analysis (automated)
- Call graph edges (Neo4j `[:CALLS]`) — automated
- EventBus publish/consume pairs — automated
- Package responsibility mapping — semi-automated

### Source 4 — Package-info.java files
Your codebase already has these — the `aiops/package-info.java` in your validation output contained rich domain descriptions:

```java
/**
 * The aiops package is designed to reduce alert noise, 
 * improve incident response times, and provide better 
 * visibility into complex IT environments by understanding 
 * the relationships between components and intelligently 
 * correlating events.
 */
```

Parse all `package-info.java` files. They're authored domain documentation already in your codebase.

---

## Revised Architecture

```
Code Intelligence Layer
├── Lexical Index (existing)
├── Structural Graph — Neo4j
│   ├── Class/Method/Package nodes
│   ├── EXTENDS, IMPLEMENTS (done ✅)
│   ├── CALLS (method level)
│   └── PUBLISHES_TO / CONSUMES_FROM (EventBus — input only)
│
├── Concept Mapper (in progress ✅)
│   └── user concept → package → entrypoint files
│
├── Behavior Flow Index  ← replaces EventBus Registry as primary
│   ├── Named domain behaviors (authored + extracted)
│   ├── Stage → owner file mapping
│   ├── Decision points and branches
│   └── Known failure modes (from ticket history)
│
├── Repo Convention Index ← replaces Convention Extractor as primary
│   ├── How to add a new integration
│   ├── How to add a new notification channel
│   ├── How to register a new Verticle
│   └── How to add a new API route
│
└── Evidence Builder (unified)
    └── Mixes all sources into bounded bundle for Plan-Gate
```

---

## Bottom Line

EventBus Registry is a **useful extraction artifact** but a **poor organizing principle** for debug and plan quality. It answers "how does execution travel" but not "what is the system trying to do and why does it sometimes fail."

The Behavior Flow Index answers both — because it starts from domain intent, maps through implementation ownership, and captures known failure modes. EventBus topology is one dimension of that, not the whole picture.

And critically — the fastest way to build the Behavior Flow Index is **you authoring the core behaviors**, because you already know them. The automated extraction fills in the technical wiring. The domain knowledge comes from you and your ticket history.

---

## Brainstorming Exercise: Ask Deep Slice (2026-04-22)

Source run:
- `runtime/scripts/motadata_behavior_verify.py`
- scenarios: `ask_base_api_class`, `ask_mail_server_configuration`, `ask_config_store_organization`, `ask_api_layer_architecture`, `ask_notification_handlers`
- output: `runtime/.run/motadata_behavior_validation.ask.deep.json`

### Tabular summary

| Scenario | Status | Primary failure reason (if any) | What is healthy | What is broken |
|---|---|---|---|---|
| `ask_base_api_class` | FAIL | `text_contains_any`: missing `AbstractAPI` in answer text | Retrieval is strong (`owner_in_top1=true`, `owner_in_top3=true`, `generic_infra_ratio_top_k=0.3333`) | Answer synthesis is semantically wrong for the ask intent (owner narrative replaces base-class answer) |
| `ask_mail_server_configuration` | FAIL | `policy.max_generic_infra_ratio_top_k` (`0.75 > 0.6`) | Authority owner lands (`MailServerConfiguration`, `owner_in_top3=true`) and answer text is relevant | Top-k context is still over-concentrated in generic infra/support paths |
| `ask_config_store_organization` | PASS | N/A | Owner anchored (`AbstractConfigStore`), generic ratio healthy (`0.3333`) | Still some context drift in selected files, but within policy threshold |
| `ask_api_layer_architecture` | PASS | N/A | Owner anchored (`APIServer`), policy metrics all pass, answer narrative coherent | Not broken at contract level |
| `ask_notification_handlers` | PASS | N/A | Owner anchored (`NotificationEngine`), generic ratio now healthy (`0.5`) | Still not ideal context purity, but acceptable by policy and expectation |

### What each output block means

- `plan_summary.steps`: this is the actual answer payload judged by ask scenarios; if this text misses expected symbols, the scenario should fail even when retrieval is good.
- `context_bundle.files`: final attached context emitted by Ask/Plan-Gate for this response; this is not the same as Stage A pool and can show post-fusion drift.
- `Stage A (fusion_diagnostics.stage_a_meta).pool_paths`: pre-fusion candidate pool; useful to check whether owner injection and concept seeding occurred before reranking/caps.
- `retrieval_metrics.generic_infra_ratio_top_k`: policy gate indicator for context purity. High value means support/infrastructure files dominate the top-k evidence window.
- `retrieval_metrics.owner_in_top1 / owner_in_top3`: authority-landing signal. If true but answer still wrong, failure is likely in narration/answer synthesis rather than retrieval anchoring.

### Per-query analysis

#### 1) `ask_base_api_class` (FAIL)

Observed:
- `owner_in_top1=true`, `owner_in_top3=true`
- `generic_infra_ratio_top_k=0.3333` (good)
- answer steps mention `APIServer` ownership but do not assert `AbstractAPI`

Meaning:
- Retrieval pipeline is not the blocker.
- This is a **query-to-answer framing bug**: the ask is about a base class across APIs, but synthesis defaulted to owner summary.

Hypothesis:
- Structural class-relationship route is not being activated (or gets overridden) for this ask path.

Action direction:
- Ensure class-relationship answer path gets priority when ask query contains "base class for all APIs".
- Enforce mention of observed base candidate (e.g., `AbstractAPI`) when evidence snippets include API class declarations with `extends`.

#### 2) `ask_mail_server_configuration` (FAIL)

Observed:
- Owner is present and relevant (`MailServerConfiguration`).
- Policy fail due to `generic_infra_ratio_top_k=0.75`.
- Top-k includes high generic/support concentration (`PolicyEngineConstants`, `NMSConstants`, `UIActionEventHandler`, etc.).

Meaning:
- Authority resolution works, but retrieval post-selection still allows too many generic support files for this domain ask.

Hypothesis:
- Hard caps and ranking are still permissive for short top-k windows where support files receive enough lexical/authority-adjacent score.

Action direction:
- Tighten ask-mode generic cap behavior for owner-anchored domain asks (especially when top-k is <= 4).
- Add stronger collaborator/owner neighborhood preference over cross-subsystem constants/util files.

#### 3) `ask_config_store_organization` (PASS)

Observed:
- Owner present in top-k (`AbstractConfigStore`), policy metrics pass.
- Expected text anchors are satisfied (`AbstractConfigStore`, `ProtocolMapperConfigStore`, `com.mindarray.store` via answer text).

Meaning:
- This scenario now represents a stable healthy baseline for owner-anchored "how organized" asks in store domain.

Action direction:
- Use this scenario as a golden reference for retrieval composition and answer style checks.

#### 4) `ask_api_layer_architecture` (PASS)

Observed:
- Owner anchored in top1.
- Policy metrics pass comfortably.
- Narrative includes APIServer ownership and architecture context.

Meaning:
- API-layer architectural ask path is functioning under current policy.

Action direction:
- Keep as a control scenario while tuning base-class semantic routing to avoid regressions.

#### 5) `ask_notification_handlers` (PASS)

Observed:
- Owner in top3.
- Generic ratio now below threshold (`0.5`).
- Answer includes notification handler class anchors via collaborator narrative.

Meaning:
- Notification intent improved materially after retrieval and verifier alignment fixes.

Action direction:
- Optional quality improvement: reduce residual generic files and prioritize direct handler classes (`EmailNotification`, `SMSNotification`) in top-k for cleaner evidence purity.

### Overall interpretation

- Net state: **3 PASS / 2 FAIL**.
- Remaining failures are now clearly split:
  1. **Answer semantics failure** (`ask_base_api_class`) despite healthy retrieval.
  2. **Top-k purity failure** (`ask_mail_server_configuration`) despite healthy authority anchoring.

This is good debugging progress: the failure surface is now narrower and actionable, not a broad retrieval-authority collapse.

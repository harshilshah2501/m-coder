# MOTADATA Wiring Maps v1 Plan

## Objective
Design a repo-wide, evidence-first wiring-map system for Motadata that is:
- additive and fail-safe,
- grounded in source edges only,
- explicit about unknowns,
- consumable by Ask/Debug/Plan/Code without changing runtime behavior.

This is design/documentation only. No extraction implementation in this phase.

## Scope and Guardrails
- Do not modify runtime behavior.
- Do not change retrieval, Plan-Gate, CIG, schemas, or composer.
- Repo is truth; graph is map; LLM is narrator; runtime is judge.
- Every edge must include file/class/method/line evidence.
- No co-occurrence chains.
- No `A -> B -> C` unless every edge is proven in source.
- Maps are additive and fail-safe (absent map must not break current flow).

## Phase 0: Subsystem Discovery (Discover First, Slice Second)

### Discovery Inputs
- Package topology under `motadata/src/main/java/com/mindarray/**`
- Startup/deployment loci: `Bootstrap*`, `MotadataAppManager`, verticle deployment
- API loci: `APIServer`, `APIRouter`, `AbstractAPI`
- Event loci: `EventBusConstants`, `eventBus().consumer/localConsumer/send/publish/request`
- Store loci: `AbstractConfigStore`, `AbstractCacheStore`, concrete `*ConfigStore/*CacheStore`

### Discovered Taxonomy Hierarchy (v1, evidence-backed)

1. Runtime and Platform Core
   - Bootstrap and runtime lifecycle
   - Event transport/routing control plane
   - Persistence/state infrastructure (db/cache/store)
2. API and Interaction Layer
   - HTTP/API ingress and route registration
   - API module registration and lifecycle hooks
3. Domain Control Layer
   - Policy evaluation and alerting
   - Notification orchestration
   - AIOps correlation/dependency
4. Observability Domain
   - NMS/discovery/metric polling
   - Flow telemetry
   - Log pipeline
   - NetRoute monitoring
   - RUM
   - Trace
5. User-Facing Query and Presentation
   - Visualization/query processing
   - Streaming/live delivery
6. Edge and Integration Runtime
   - Agent lifecycle and ingestion

## Subsystem Evidence Table

| Subsystem | Evidence paths / symbols | Confidence | Ambiguity / unresolved boundary | Candidate map artifact |
|---|---|---|---|---|
| API/HTTP ingress | `com/mindarray/api/APIServer.java` (`APIServer.start`), `com/mindarray/api/APIRouter.java` (`APIRouter.init`), `com/mindarray/api/AbstractAPI.java` (`init`) | high | Exact per-endpoint override behavior varies by concrete API class and must be extracted class-by-class. | `api_route_mapping.v1` |
| Bootstrap/runtime | `com/mindarray/Bootstrap.java`, `BootstrapStandalone.java`, `BootstrapPrimary.java`, `BootstrapSecondary.java`, `BootstrapCollector.java` | high | Startup topology differs by deployment mode (standalone/primary/secondary/collector), so mode-conditional edges are required. | `bootstrap_runtime_mapping.v1` |
| EventBus topology | `com/mindarray/eventbus/EventBusConstants.java`, `LocalEventRouter.java`, `RemoteEventRouter.java`, `EventReceiver.java`, `RemoteEventReceiver.java` | high | Dynamic address routing from payload fields cannot always be statically resolved; unresolved targets must remain unknown. | `eventbus_topology_mapping.v1` |
| Config/store/cache | `com/mindarray/store/AbstractConfigStore.java`, `AbstractCacheStore.java`, `ObjectConfigStore.java`, `RemoteEventProcessorConfigStore.java`, `MetricConfigStore.java` | high | Ownership is cross-cutting (`db`/`cache`/`store`) and some mutation side-effects fan out via EventBus handlers. | `store_ownership_mapping.v1` |
| Policy/notification | `com/mindarray/policy/PolicyEngine.java`, `MetricPolicyInspector.java`, `com/mindarray/eventbus/UIActionEventHandler.java`, API classes like `MailServerConfiguration` | medium | Policy evaluators and notification dispatchers are intertwined across event and domain packages; exact authority split needs extraction rules. | `policy_notification_mapping.v1` |
| AIOps/dependency | `com/mindarray/aiops/AvailabilityCorrelationEngine.java`, `DependencyManager.java`, dependency-related API/event query handlers | high | Boundaries with policy and visualization query flows are cross-subsystem and require explicit interaction edges, not inferred sequence. | `aiops_dependency_mapping.v1` |
| Observability domain | `com/mindarray/nms/**`, `flow/**`, `log/**`, `netroute/**`, `rum/**`, `trace/**` plus corresponding stores and routers | medium | Domain packages are clear, but inter-domain handoffs (for enrichment/correlation/notification) must be proven through event or API/store edges. | `observability_domain_mapping.v1` |
| Visualization/query | `com/mindarray/visualization/VisualizationManager.java`, `VisualizationMetricManager.java`, `com/mindarray/api/Query.java` | high | Ownership boundary between query execution and domain engines is shared; avoid asserting execution order unless edge-proven. | `visualization_query_mapping.v1` |
| Agent/streaming | `com/mindarray/agent/AgentManager.java`, `MetricAgentEventProcessor.java`, `com/mindarray/streaming/StreamingEngine.java` | medium | Streaming transport and agent lifecycle interact through EventBus and mode-specific runtime paths; some edges are conditional at runtime. | `agent_streaming_mapping.v1` |
| Cross-subsystem interaction | Derived only from proven primitive maps (`api_route`, `bootstrap_runtime`, `eventbus_topology`, `store_ownership`, domain maps) | high | Must not be sourced from raw co-occurrence scans; only compositional edges from already-proven map artifacts are allowed. | `interaction_mapping.v1` |

### Subsystem Confidence and Ambiguity Policy
- High: clear package ownership + direct wiring points.
- Medium: cross-cutting ownership or conditional startup mode.
- Low: naming-only signals without direct wiring proof.
- Ambiguous boundaries are documented as unresolved and carried into `unknowns[]`.

## Wiring Map Candidate Set (v1)

### Core maps
1. API Route/Handler Wiring Map
2. Bootstrap/Runtime Deployment Map
3. EventBus Topology Map
4. Config/Store Ownership Map

### Domain maps
5. Policy/Notification Control Map
6. AIOps/Dependency Topology Map
7. Observability Domain Maps (NMS, Flow, Log, NetRoute, RUM, Trace)
8. Visualization/Query Wiring Map
9. Agent/Streaming Runtime Map

### New required conceptual layer
10. Cross-Subsystem Interaction Map v1 (design-first)

## Cross-Subsystem Interaction Map v1 (Design)
Purpose: capture evidence-backed subsystem-to-subsystem handoff edges.

Examples (design targets only):
- API -> EventBus -> Notification
- API -> Store -> AIOps
- Bootstrap -> Verticle -> EventBus

Rules:
- Each interaction edge must reference concrete source edges from underlying maps.
- If a bridge cannot be proven, emit unknown instead of inferred interaction.
- Interaction map never invents new primitive edges; it composes proven ones.

## Per-Map Design Contract
For each map in the set above, define:
- purpose,
- source files and search patterns,
- extraction rules and allowed edge types,
- artifact schema,
- unknown handling,
- validation gates,
- acceptance tests,
- integration slot in `reasoning_context`,
- Ask/Debug/Plan/Code consumption behavior.

## Shared Edge Contract (All Maps)
Each extracted edge must carry:
- `edge_type`
- `source` (file/class/method/symbol/address/route/store key)
- `target` (file/class/method/symbol/address/route/store key)
- `evidence` (path + line range + extraction rule id)
- `confidence` (`high|medium|low`)
- optional `mode` (standalone/primary/secondary/collector/etc.)
- optional `unknown_reason` when unresolved

## Artifact Schema (Sample Layout)
```json
{
  "schema_version": "motadata_wiring_map.v1",
  "map_type": "eventbus_topology",
  "subsystem": "runtime_platform_core",
  "generated_at_utc": "2026-04-30T00:00:00Z",
  "nodes": [],
  "edges": [],
  "unknowns": [],
  "validation_summary": {
    "edge_count": 0,
    "unknown_count": 0,
    "confidence_distribution": {
      "high": 0,
      "medium": 0,
      "low": 0
    }
  }
}
```

## Reasoning Context Integration (Additive)
Add map payloads under dedicated keys, for example:
- `api_route_mapping`
- `bootstrap_runtime_mapping`
- `eventbus_topology_mapping`
- `store_ownership_mapping`
- `interaction_mapping`

Behavior:
- If map exists, use map edges as first evidence source.
- If map missing, degrade safely to existing reasoning behavior.
- Unknowns are surfaced as one bounded, natural sentence.

## Map Precedence Rules (Mandatory)
When multiple maps apply to a query, use this order:
1. Direct wiring maps (API route, Bootstrap runtime, EventBus topology)
2. Store/ownership maps
3. Domain control maps (Policy/Notification, AIOps)
4. Observability domain maps
5. Interaction map composition (built from proven primitives)
6. Fallback collaborator heuristics (last resort only)

This precedence prevents regression into co-occurrence narration.

## Scale and Context-Budget Guardrails
- Configurable max nodes/edges per map artifact.
- Configurable max map payload injected into `reasoning_context` per query.
- Lazy map loading by query intent/subsystem match.
- Truncation policy must preserve:
  - high-confidence edges first,
  - then medium confidence,
  - unknowns summary always retained.
- If budget exceeded, summarize lower-priority maps rather than dropping direct wiring edges.

## Validation and Acceptance Strategy

### Static extraction validation
- Edge has complete evidence tuple.
- Constant and symbol reference resolution passes.
- No edge without source anchor.

### Anti-hallucination validation
- Reject co-occurrence-only adjacency.
- Force unknown emission for dynamic/unresolvable targets.
- Disallow unproven multi-hop chain rendering.

### Consumption validation
- Ask/Debug/Plan/Code can cite map edges directly.
- Unknowns appear explicitly and bounded.
- Missing map data does not break existing responses.

### Acceptance tests (design targets)
- API architecture answers include `APIServer.start`, `/api/v1/*`, `APIRouter.init`, `AbstractAPI.init` when map present.
- HTTP flow answers avoid fabricated domain chains unless map proves them.
- EventBus map proves producer/consumer/address edges or emits unknowns.
- Interaction map only composes already-proven primitive edges.

## Risk Register
- Dynamic dispatch may hide concrete targets.
- Startup mode branching creates conditional topology.
- Large handlers can inflate unknowns and extraction complexity.
- Cross-cutting packages can blur subsystem boundaries.
- Context overload risk from too many map slices.

Mitigations:
- confidence tiers,
- mode-tagged edges,
- explicit unknowns,
- map precedence,
- context-budget guardrails,
- fixture-based validation and drift checks.

## Phased Rollout (Design Sequence)
1. Finalize taxonomy hierarchy and ambiguity ledger.
2. Define Interaction Map v1 contract (design-only).
3. Define map precedence and context-budget guardrails.
4. Finalize per-map schemas/rules for core maps.
5. Finalize per-map schemas/rules for domain maps.
6. Finalize validation gates and acceptance matrix.
7. Finalize CIG v2 merge contract.
8. Start implementation with EventBus Topology Map v1 as first slice.

## CIG v2 Merge Plan
- Wiring Maps v1 become an authoritative, provenance-carrying edge layer.
- Node identity is canonicalized across maps before merge.
- Direct wiring edges are ranked above inferred graph neighbors.
- Unknowns are retained as explicit unresolved entries.

Non-override rule (mandatory):
- Once an edge is proven by wiring-map evidence, inferred graph edges cannot override or downgrade it.

## Immediate Next Step
Design Interaction Map first; implement EventBus Topology first.

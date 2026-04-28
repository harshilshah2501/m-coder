# Deterministic Code Intelligence Graph v1

**Document Type:** Architecture Design Specification  
**Status:** Pass B Design Only (No Implementation in this pass)  
**Version:** 1.0  
**Date:** 2026-04-28  
**Scope:** Documentation only; no code or runtime behavior changes

---

## 1) Charter and Invariant

This document defines Pass B design for a deterministic Code Intelligence Graph (CIG) that is derived from repository state and consumed as evidence support.

Core invariant:

`Repo is truth. Graph is map. LLM is narrator. Runtime is judge.`

Interpretation:
- **Repo is truth:** The checked-out repository is the canonical source of facts.
- **Graph is map:** The graph is a deterministic projection of repo facts, never an authority replacement.
- **LLM is narrator:** The LLM explains and synthesizes evidence; it does not create ground truth.
- **Runtime is judge:** Existing runtime and policy gates decide what is accepted.

Hard boundaries for this pass:
- No code changes.
- No Pass A implementation changes.
- No runtime behavior changes.

---

## 2) Goals and Non-Goals

### Goals
- Define deterministic extraction modules for graph construction.
- Define CIG v1 schema contracts.
- Define portable storage format and versioning.
- Define incremental rebuild strategy based on repo deltas.
- Define validation gates for quality and safety.
- Define clean integration points with Pass A outputs/consumers.

### Non-Goals
- No execution engine changes in retrieval, ranking, ask, or plan paths.
- No replacement of existing authority contracts.
- No graph database dependency introduction.
- No probabilistic/embedding-derived edge creation in v1.

---

## 3) System Model

### 3.1 Position in Stack

CIG v1 is a read-only, derivable artifact that sits between:
- **Input:** Repository file system + existing deterministic index outputs.
- **Output:** Versioned graph artifact consumable by evidence assembly and diagnostics.

It augments understanding but does not alter current ranking or response logic in this pass.

### 3.2 Determinism Contract

Given:
- same repo commit/tree,
- same extractor version,
- same config,

the generated graph artifact must be byte-stable except for explicitly allowed metadata fields (for example generation timestamp).

---

## 4) Extraction Modules

Each module is deterministic, side-effect free (except artifact write), and independently testable.

### 4.1 `workspace_snapshot_extractor`
- Captures repo identity (`commit_sha`, tree hash where available, root path fingerprint).
- Enumerates tracked files eligible for graph extraction.
- Produces canonical file list ordering (lexicographic normalized path order).

### 4.2 `symbol_extractor`
- Extracts file-level and symbol-level entities from existing parser/index outputs.
- Entity kinds (v1 minimum): `file`, `class`, `interface`, `method`, `function`, `module`.
- Emits stable symbol IDs using normalized path + symbol signature.

### 4.3 `import_dependency_extractor`
- Produces deterministic import/include edges:
  - `IMPORTS`
  - `REFERENCES_MODULE`
- Strictly syntactic in v1 (no heuristic semantic inference).

### 4.4 `call_edge_extractor`
- Produces call relationships where existing deterministic call data exists:
  - `CALLS`
  - reverse view materialized as adjacency index only (not separate truth edge).
- Marks edge confidence class (`high`, `bounded`, `unknown`) from extraction provenance; no model confidence.

### 4.5 `ownership_overlay_extractor`
- Projects existing authority/ownership artifacts into graph overlay nodes/edges:
  - `CONCEPT_OWNS`
  - `CONCEPT_COLLABORATES_WITH`
  - `CONCEPT_FORBIDS`
- Does not author new ownership; only mirrors curated source contracts.

### 4.6 `entrypoint_extractor`
- Extracts known entrypoint entities from deterministic patterns/config:
  - REST handlers, event handlers, schedulers, consumers (as configured).
- Produces `ENTRYPOINT_INVOKES` edges where statically resolvable.

### 4.7 `graph_assembler`
- Merges module outputs into canonical node/edge sets.
- Deduplicates by stable IDs.
- Sorts deterministically and computes integrity hashes.

### 4.8 `artifact_writer`
- Writes graph artifact and manifest atomically.
- Stores schema version, extractor version, and build diagnostics.

### 4.9 Motadata-Specific Required Edge Families (v1)

These edge families are mandatory in Motadata-targeted Pass B implementation and remain deterministic/repo-derived.

1) API inheritance
- `API_CLASS -> EXTENDS -> AbstractAPI`

2) API route registration
- `APIServer.start -> REGISTERS_ROUTE -> handler/API class`

3) API lifecycle methods
- `API_CLASS -> OVERRIDES -> beforeAdd|beforeUpdate|beforeDelete|getItem|...`

4) Config-store relation
- `API/service class -> READS_FROM -> AbstractConfigStore|concrete store`
- `API/service class -> WRITES_TO -> AbstractConfigStore|concrete store`

5) EventBus flow
- `publisher method -> PUBLISHES_TO -> eventbus address`
- `consumer method -> CONSUMES_FROM -> eventbus address`

6) Notification/mail domain flow
- `MailServerConfiguration -> AFFECTS -> notification/mail delivery concept`
- `NotificationEngine -> HANDLES -> notification dispatch/reply concepts`

7) Ownership concept overlay
- `concept:mail_config -> OWNS -> MailServerConfiguration`
- `concept:api_layer -> OWNS -> APIServer, AbstractAPI`
- `concept:notification -> OWNS -> NotificationEngine + related handlers`

---

## 5) CIG v1 Schema

### 5.1 Top-Level Envelope

```yaml
schema_version: "code_intelligence_graph.v1"
graph_version: "1.0.0"
generated_at: "ISO-8601"
repo_identity:
  commit_sha: "..."
  workspace_fingerprint: "sha256:..."
extractor_identity:
  extractor_version: "..."
  config_hash: "sha256:..."
stats:
  node_count: 0
  edge_count: 0
  file_count: 0
nodes: []
edges: []
adjacency: {}
diagnostics: {}
```

### 5.2 Node Schema

Required fields:
- `id`: stable deterministic identifier
- `kind`: enum (`file`, `symbol`, `concept`, `entrypoint`, `module`)
- `label`: human-readable stable label
- `attrs`: key/value map (primitive values only in v1)

Node ID strategy:
- `file`: `file::<normalized_relative_path>`
- `symbol`: `symbol::<normalized_relative_path>::<signature>`
- `concept`: `concept::<concept_id>`
- `entrypoint`: `entry::<type>::<normalized_relative_path>::<handler>`

### 5.3 Edge Schema

Required fields:
- `id`: deterministic hash of (`src`, `type`, `dst`, optional qualifier)
- `src`: source node ID
- `type`: enum
- `dst`: destination node ID
- `attrs`: map (for provenance/path metadata)

Edge types (v1):
- Structural: `IMPORTS`, `CALLS`, `DECLARES`, `CONTAINS`, `ENTRYPOINT_INVOKES`
- Ownership overlay: `CONCEPT_OWNS`, `CONCEPT_COLLABORATES_WITH`, `CONCEPT_FORBIDS`

### 5.4 Provenance and Trust Fields

Every edge may include:
- `provenance.source`: extractor module name
- `provenance.mode`: `deterministic_static`
- `provenance.input_ref`: source artifact hash or file

Trust posture is inherited from source artifacts:
- Graph never elevates trust beyond source contract.

---

## 6) Storage Format

### 6.1 Artifact Files (v1)

Recommended deterministic file set:
- `code_intelligence_graph.v1.jsonl`  
  - line-delimited records for nodes and edges
- `code_intelligence_graph.v1.manifest.json`  
  - schema/extractor identity, counts, hash totals, diagnostics summary
- `code_intelligence_graph.v1.adjacency.json`  
  - compact forward/reverse adjacency maps for fast lookup

Why JSON/JSONL in v1:
- deterministic serialization control,
- easy diffability in CI,
- no extra service/database dependency.

### 6.2 Canonical Serialization Rules

- UTF-8, LF newlines.
- Sorted record order:
  1. nodes by `id`,
  2. edges by (`src`, `type`, `dst`, `id`).
- Canonical key order within JSON objects.
- No nondeterministic maps in output.

### 6.3 Compatibility Policy

- `schema_version` is mandatory and semver-governed.
- Minor changes: additive fields only.
- Major changes: new schema namespace (`v2`) with migration notes.

---

## 7) Incremental Rebuild Strategy

### 7.1 Change Detection Inputs

Incremental rebuild is keyed by:
- repo identity delta (commit/tree),
- changed file paths,
- extractor/config hash changes.

### 7.2 Rebuild Units

Three deterministic unit scopes:
- **File unit:** re-extract changed files and directly dependent symbol records.
- **Edge unit:** recompute edges touching changed nodes.
- **Overlay unit:** recompute concept/entrypoint overlays when their source artifacts change.

### 7.3 Dependency Propagation

For changed file `F`:
- recompute `file::<F>` node and declared symbols,
- recompute outbound structural edges from `F`,
- recompute inbound adjacency indexes where `dst` impacted,
- keep untouched records byte-identical.

### 7.4 Rebuild Modes

- `full_rebuild`: cold start or schema/extractor major change.
- `incremental_rebuild`: default for repo deltas.
- `overlay_only_rebuild`: authority/entrypoint contract updates without structural change.

### 7.5 Determinism Safeguards

- Stable ordering at every stage.
- Hash-based content equality checks before write.
- Atomic swap of artifact files (`tmp` -> final) after manifest verification.

---

## 8) Validation Gates

Validation gates are design contracts to be enforced by CI/runtime wrappers in future implementation, without changing runtime behavior in this pass.

### 8.1 Gate A: Schema Integrity
- Validate all artifacts against `code_intelligence_graph.v1` schema.
- Fail on missing required fields, unknown enum values, malformed IDs.

### 8.2 Gate B: Determinism
- Re-run extraction twice on same repo snapshot.
- Expect identical manifest content hashes (excluding allowed timestamp fields).
- Fail on nondeterministic drift.

### 8.3 Gate C: Referential Integrity
- Every edge `src`/`dst` must resolve to an existing node.
- No dangling ownership/entrypoint references.

### 8.4 Gate D: Overlay Contract Integrity
- `CONCEPT_*` edges must map to existing curated concept IDs.
- Graph cannot invent concept ownership not present in source authority artifacts.

### 8.5 Gate E: Delta Safety (Incremental vs Full)
- Incremental rebuild output must match full rebuild output for same final repo state.
- Fail on divergence; full rebuild becomes fallback truth.

### 8.6 Gate F: Size and Performance Budgets
- Enforce configurable upper bounds for build time and artifact size growth.
- Warn on trend breaches; fail on hard limits.

### 8.7 Gate G: Answer-Quality Acceptance (Post-Graph Enrichment)

These are scenario-level acceptance gates for future enriched answer composition across Motadata AIOps intents (`ask`, `debug`, `plan`). They are quality targets and do not change runtime behavior in this design pass.

Scope policy:
- Applies to any Motadata AIOps query where deterministic graph evidence is available.
- Includes, but is not limited to, architecture, ownership, tracing, debugging, dependency, and discovery questions.

Intent-wide quality requirements:
- **Grounding:** Answers must anchor claims to deterministic graph/repo evidence, not generic single-anchor phrasing.
- **Structure-aware completeness:** Answers should include primary owner, collaborating components, and relevant flow/dependency path when evidence supports it.
- **Role separation:** Must distinguish primary owner vs collaborator/supporting classes.
- **Confidence honesty:** Must include bounded language whenever evidence coverage is partial/weak.
- **Non-collapse rule:** Must not reduce multi-component behavior to one method/class when graph resolves broader responsibility.

Mandatory seed scenarios (examples, not exhaustive):

Query: `Explain the API layer architecture.`
- Must mention `APIServer` route/server responsibility.
- Must mention `AbstractAPI` as base/lifecycle abstraction.
- Must mention concrete API classes as handlers/extensions.
- Must not collapse answer to only `APIServer.start` as sole anchor.

Query: `How does mail server configuration work?`
- Must mention `MailServerConfiguration.beforeUpdate`.
- Must explain update/validation/persistence path.
- Must identify store/config collaborators when graph evidence resolves them.
- Must include confidence-bounded phrasing when evidence is partial.

Query: `Find all classes that handle notifications.`
- Must return multiple classes when graph/domain ownership evidence resolves them.
- Must separate primary owner from collaborators.

### 8.8 Gate H: Regression vs Pass A Baseline

- Graph-enriched scenarios must strictly improve answer completeness over Pass A anchor-only phrasing across Motadata AIOps ask/debug/plan intents.
- Any regression to single-anchor output in presence of richer deterministic graph evidence is a gate failure.

---

## 9) Integration Points with Pass A

Pass B integration is additive and read-only in this design.

### 9.1 Inbound from Pass A
- Existing deterministic file/symbol/call/index artifacts (as currently produced).
- Existing authority and concept contracts (curated source of ownership truth).
- Existing entrypoint registries/patterns where available.

### 9.2 Outbound to Pass A Consumers
- Graph artifact path and manifest metadata for optional evidence enrichment.
- Adjacency lookup for diagnostics and explainability surfaces.
- No mandatory consumer contract changes in this pass.

### 9.3 Integration Guardrails
- If graph artifact is unavailable or invalid, consumers continue with current Pass A behavior.
- No hard dependency injection into current ranking/response path for Pass B design.
- Feature integration (future pass) must be behind explicit flags and compatibility checks.

---

## 10) Failure Modes and Recovery

Expected failure classes:
- extractor parser mismatch on language edge cases,
- stale overlay references,
- incremental divergence from full rebuild,
- artifact corruption/partial write.

Recovery posture:
- fail closed on invalid graph artifact,
- preserve current runtime behavior,
- surface diagnostics in manifest,
- require explicit rebuild or fallback to full rebuild.

---

## 11) Rollout and Governance (Design Only)

### 11.1 Phased Rollout Plan
- **Phase 0:** generate artifact in shadow mode (no consumers depend on it).
- **Phase 1:** enable read-only diagnostics consumers.
- **Phase 2:** propose optional ranking/evidence integrations under feature flags (outside this pass).

### 11.2 Ownership and Review
- Schema changes require design review.
- Extractor logic changes require determinism gate pass.
- Overlay changes remain governed by authority contract maintainers.

---

## 12) Acceptance Criteria for This Document

This Pass B design is complete when:
- extraction modules are explicitly defined,
- schema and storage contracts are versioned,
- incremental rebuild algorithm is deterministic and testable,
- validation gates are enumerated with pass/fail semantics,
- Pass A integration boundaries are explicit and non-invasive,
- invariant is preserved end-to-end.

Invariant check:

`Repo is truth. Graph is map. LLM is narrator. Runtime is judge.`

---

## 13) Graph-to-Answer Composition Rules

This section defines how deterministic graph evidence is transformed into user-facing answers. Without these rules, graph construction alone does not improve perceived intelligence.

### 13.1 Composition Contract

Inputs:
- normalized query + inferred intent (`ask` / `debug` / `plan`),
- deterministic CIG v1 nodes/edges + adjacency,
- existing quality metadata and policy posture.

Outputs:
- answer blocks shaped from traversal evidence,
- explicit role separation (primary owner vs collaborators),
- confidence-bounded phrasing tied to edge coverage.

Hard rule:
- Do not select a single anchor if traversal path contains more than one meaningful node.

Meaningful node (v1):
- participates in ownership, inheritance, control flow, config-store interaction, or event flow for the resolved intent.

### 13.2 Intent-to-Traversal Mapping

`STRUCTURAL`
- Traverse inheritance and declaration edges:
  - `EXTENDS`, `IMPLEMENTS`, `DECLARES`, `CONTAINS`.
- Return base abstraction plus inheritance chain.
- Expected shape:
  - `AbstractAPI -> concrete API classes` (when present).

`EXPLAIN / ARCHITECTURE`
- Traverse entry-to-flow-to-abstraction path:
  - `REGISTERS_ROUTE` / `ENTRYPOINT_INVOKES` -> `CALLS` -> `EXTENDS`/`OVERRIDES`.
- Return:
  - entrypoint -> flow -> abstraction -> concrete implementation.

`DEBUG / WHY`
- Traverse execution path and side-effect edges:
  - entrypoint -> handler -> called methods -> store/eventbus interaction.
- Include:
  - likely hypothesis,
  - supporting traversal edges,
  - candidate missing edge or branch-not-taken point when path breaks.

`DISCOVERY`
- Traverse concept ownership overlay:
  - `CONCEPT_OWNS`, `CONCEPT_COLLABORATES_WITH`, `CONCEPT_FORBIDS`.
- Return:
  - primary owner(s) + collaborators, clearly separated.
- Example:
  - `NotificationEngine` (primary) + related handlers (collaborators).

### 13.3 Anti-Collapse and Answer Assembly Rules

- If graph resolves a multi-node path, answer must include the path summary (not only first hop).
- If graph resolves owner + collaborators, answer must include both sections.
- If graph lacks required edges for a complete claim, answer must downgrade confidence and state missing evidence.
- If conflicting paths exist, answer must present the dominant path and list alternatives as secondary candidates.

### 13.4 Traversal API (Read-Only, Phase 1)

Before composer integration, expose deterministic read-only traversal helpers over CIG v1 artifacts:

```python
get_inheritance_chain(class_name)
get_call_chain(method_id)
get_entrypoint_flow(route_or_handler)
get_concept_owners(concept_id)
```

Rules:
- read-only over derived graph artifacts,
- deterministic outputs for same artifact version,
- no mutation of repo truth or curated authority contracts.

### 13.5 Integration Strategy

Phase 0 (already defined):
- generate graph artifacts,
- validate determinism and integrity.

Phase 1:
- implement read-only traversal API over file-backed CIG artifacts.

Phase 2:
- integrate traversal outputs into answer composer (not retrieval scoring in this phase).

### 13.6 Neo4j Projection Policy (Optional Backend)

Neo4j may be used as an optional query backend, but only as a derived projection of deterministic CIG v1 artifacts.

Source-of-truth order:
1. repository state,
2. deterministic CIG v1 JSON/JSONL artifacts,
3. Neo4j projection generated from those artifacts.

Mandatory rules:
- No direct Neo4j-authored facts.
- No manual graph edits as source truth.
- Rebuild Neo4j from CIG artifacts whenever required.
- Neo4j schema must mirror CIG v1 node/edge model.
- If Neo4j query path fails, fallback to file-backed CIG traversal; if that also fails, fallback to current Pass A behavior.


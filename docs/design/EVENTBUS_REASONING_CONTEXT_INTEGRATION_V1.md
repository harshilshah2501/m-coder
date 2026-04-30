# EventBus Topology Map v1 -> reasoning_context Integration (Design)

## Scope
Design only.

- Do not implement code.
- Do not modify Ask/Debug/Plan/Code behavior in this phase.
- Do not change extractor contracts.

## Goal
Integrate EventBus topology as a safe reasoning signal without:
- introducing noise,
- inflating context,
- enabling fake chains.

## Preconditions
- EventBus extractor v1 is frozen and trusted.
- Artifact is available at build/runtime boundary:
  - `eventbus_topology_mapping.v1.json`
- Unknown handling remains explicit:
  - `DYNAMIC_ADDRESS`
  - `UNRESOLVED_ADDRESS`
  - `__unresolved_static_or_lambda_context__`

## 1) Injection Rules
Include EventBus context only when query intent indicates event-driven reasoning.

### Include for query intents containing signals like
- `event`
- `notification`
- `async`
- `trigger`
- `correlation`
- `streaming`
- `consumer`
- `producer`
- `message bus`

### Exclude by default for non-event intents
- generic architecture questions (for example API layer overview)
- storage-only questions
- inheritance/base-class questions
- unrelated refactor planning prompts

If intent is ambiguous, default to no EventBus injection.

## 2) Selection Strategy
Never inject full EventBus artifact.

### Default selection caps
- max relevant addresses: `3`
- max producers: `3`
- max consumers: `3`

### Address-kind policy
- default include: `runtime`
- default exclude: `test`, `control`
- `websocket` include only if query mentions websocket/streaming
- `unknown` include only in debug-mode contexts or explicit unknown-focused queries

### Relevance ordering (design)
1. exact query token overlap with address
2. exact symbol overlap with producer/consumer class/method
3. higher-confidence edges first
4. recent/primary evidence anchors when ties occur

## 3) reasoning_context Representation
Use a compact structured block, not raw edge dumps:

```json
{
  "eventbus_context": {
    "addresses": [],
    "producers": [],
    "consumers": [],
    "unknowns": [],
    "confidence": {}
  }
}
```

### Required field guidance
- `addresses`: selected address objects (`address`, `address_kind`, `evidence`)
- `producers`: selected producer entries (`class`, `method`, `address`, `evidence`)
- `consumers`: selected consumer entries (`class`, `method`, `address`, `evidence`)
- `unknowns`: selected unresolved entries with reason/type
- `confidence`: aggregate summary (`resolved_count`, `unknown_count`, confidence distribution)

No full artifact embedding.

## 4) Narration Rules

### Ask mode
- Use EventBus context for “who triggers what” explanations.
- Describe roles only:
  - producer
  - consumer
  - event/address
- Do not emit multi-hop chains beyond proven direct address joins.

### Debug mode
- Primary EventBus consumption mode.
- Use map to reason about:
  - missing consumer,
  - unresolved/dynamic address source,
  - producer/consumer mismatch on exact address.
- Unknowns remain unknown; never patched with inferred links.

### Plan/Code modes
- EventBus context may inform diagnostics/plans, but must remain evidence-bounded.
- No expansion into speculative orchestration flow.

## 5) Safety Rules (Hard)
- Never infer producer -> consumer unless exact address match exists in artifact.
- Never connect through dynamic addresses.
- Never let EventBus context override higher-confidence proven wiring from direct-map precedence.
- Never mix EventBus edges with generic collaborator heuristics in a way that creates synthetic chains.
- Never suppress unknowns to “improve fluency.”

## 6) Context Budget

### Caps
- max injected EventBus nodes: `10`
- max addresses: `3`
- max producers: `3`
- max consumers: `3`

### Truncation policy
Drop in this order:
1. lowest-confidence edges
2. non-runtime address kinds (unless debug intent)
3. least query-relevant symbols

Always preserve at least one explicit unknown when unknowns are central to query/debug intent.

## 7) Test Design
Define integration-contract tests (design targets):

1. event-focused question -> EventBus context injected
2. non-event question -> no EventBus context injected
3. debug scenario -> producer/consumer mismatch identified via exact address
4. dynamic address case -> remains unknown, not inferred
5. test/control address suppression in Ask path by default
6. websocket address included only when websocket/streaming intent is present
7. context cap enforcement does not exceed node/address limits

## Acceptance Criteria
- No increased hallucination risk from EventBus injection.
- No context explosion.
- No fake chains introduced.
- EventBus context appears only when meaningful to intent.
- Unknown handling remains explicit and preserved.

## Non-Goals
- No direct code integration in this phase.
- No schema changes outside this design contract.
- No cross-subsystem interaction composition implementation yet.
